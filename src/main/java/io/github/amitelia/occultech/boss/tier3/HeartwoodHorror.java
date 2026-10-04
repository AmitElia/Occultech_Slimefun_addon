package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Creaking;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-3 mini-boss (Infinity gear). A giant creaking that, like every creaking, only moves while nobody looks at it.
 * <ul>
 * <li>Heart markers: four creaking-heart markers stand around the circle (display entities, not real blocks). While
 * any stands, the Horror can't be hurt. Breaking all four opens a 20s window, then the hearts regrow. Someone has to
 * look away from it to go break them - and then it moves.</li>
 * <li>Root snare: a circle of roots under a player, then they're held and hurt.</li>
 * </ul>
 * It is not tied to a real creaking heart, so its health is ours to manage; it takes an eighth of the damage dealt.
 */
public final class HeartwoodHorror extends BossBehavior {

    private static final double HEALTH = 320;
    private static final double ARMOR = 0.125;
    private static final double MELEE = 50;
    private static final int HEARTS = 4;
    private static final int HEART_HITS = 12;
    /** Staring at it this long (ticks) makes it snap and lunge at the starer. */
    private static final int STARE_LIMIT = 60;
    private static final int CREAK_INTERVAL = 240;
    private static final double LUNGE_DAMAGE = 50;
    private static final int VULNERABLE_TICKS = 400;
    private static final int SNARE_INTERVAL = 160;
    private static final double SNARE_DAMAGE = 30;
    private static final Color ROOTS = Color.fromRGB(90, 70, 50);

    private Creaking horror;
    private final List<BossFight.FightObject> hearts = new ArrayList<>();
    /** Roots and sap round it while its hearts make it invulnerable. */
    @javax.annotation.Nullable private io.github.amitelia.occultech.boss.AirEffects.Aura roots;
    private int vulnerableUntil = -1;
    private int heartsLeft;
    private int snareAt = -1;
    private final java.util.Map<java.util.UUID, Integer> stares = new java.util.HashMap<>();
    private int lungeReady;
    private int creakAt = -1;
    private Player creakTarget;
    private Location snareSpot;

    public HeartwoodHorror(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        horror = fight.spawnBoss(Creaking.class, at.clone().add(0, 1, 0), c -> {
            c.setCustomName(ChatColor.GOLD + "Heartwood Horror");
            c.setCustomNameVisible(true);
            BossFight.setAttribute(c, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(c, Attribute.ATTACK_DAMAGE, MELEE);
            BossFight.setAttribute(c, Attribute.SCALE, 1.6);
            BossFight.setAttribute(c, Attribute.FOLLOW_RANGE, 48);
            BossFight.setAttribute(c, Attribute.KNOCKBACK_RESISTANCE, 1);
        });
        growHearts();
    }

    /** Invulnerable while any heart stands. */
    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        if (fight.elapsed() >= vulnerableUntil) {
            boss.getWorld().spawnParticle(Particle.BLOCK, boss.getLocation().add(0, 2, 0), 12, 0.4, 0.6, 0.4, Material.PALE_OAK_LOG.createBlockData());
            boss.getWorld().playSound(boss.getLocation(), Sound.BLOCK_CREAKING_HEART_HURT, 1F, 0.6F);
            return 0;
        }
        return damage * ARMOR;
    }

    @Override
    public void tick() {
        if (!horror.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (horror.getTarget() == null) {
            horror.setTarget(fight.nearestPlayer(horror.getLocation()));
        }

        hearts.removeIf(heart -> !heart.isAlive());
        if (!hearts.isEmpty() && roots == null) {
            roots = io.github.amitelia.occultech.boss.AirEffects.Aura.create(fight, horror, "aura_roots", 0.02, 2.4);
        } else if (hearts.isEmpty() && roots != null) {
            roots.end();
            roots = null;
        }
        boolean vulnerable = now < vulnerableUntil;
        if (hearts.isEmpty() && !vulnerable && vulnerableUntil >= 0 && now >= vulnerableUntil) {
            // the window closed: the hearts regrow
            vulnerableUntil = -1;
            horror.setGlowing(false);
            growHearts();
        }
        if (vulnerable && every(10)) {
            horror.getWorld().spawnParticle(Particle.TRIAL_SPAWNER_DETECTION, horror.getLocation().add(0, 2, 0), 6, 0.5, 0.8, 0.5, 0.02);
        }
        // the hearts pulse toward the Horror so players can find them
        if (every(20)) {
            for (BossFight.FightObject heart : hearts) {
                heart.location().getWorld().spawnParticle(Particle.DUST, heart.location().clone().add(0, 1.2, 0), 6, 0.2, 0.4, 0.2, 0,
                    new Particle.DustOptions(Color.fromRGB(255, 140, 40), 1.2F));
            }
        }

        stareCheck(now);
        if (every(CREAK_INTERVAL) && creakAt < 0) {
            creakTarget = fight.randomPlayer();
            if (creakTarget != null) {
                creakAt = now + 20;
                horror.getWorld().playSound(creakTarget.getLocation(), Sound.ENTITY_CREAKING_AMBIENT, 2F, 0.5F);
                creakTarget.sendActionBar(ChatColor.GOLD + "Something creaks behind you...");
            }
        }
        if (creakAt >= 0 && now >= creakAt) {
            creakAt = -1;
            if (creakTarget != null && creakTarget.isValid()) {
                lunge(creakTarget, true);
            }
        }

        if (every(SNARE_INTERVAL) && snareAt < 0) {
            Player victim = fight.randomPlayer();
            if (victim != null) {
                snareSpot = victim.getLocation();
                snareAt = now + 30;
                fight.telegraph(snareSpot, 2.5, 35, ROOTS, FloorDecals.Mark.ROOTS);
            }
        }
        if (snareAt >= 0 && now >= snareAt) {
            snareAt = -1;
            snareSpot.getWorld().spawnParticle(Particle.BLOCK, snareSpot.clone().add(0, 0.5, 0), 40, 1.2, 0.5, 1.2, Material.PALE_OAK_LOG.createBlockData());
            snareSpot.getWorld().playSound(snareSpot, Sound.BLOCK_ROOTS_BREAK, 2F, 0.6F);
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(snareSpot) <= 6.25) {
                    player.damage(SNARE_DAMAGE, horror);
                    player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 60, 4));
                }
            }
        }
    }

    /** Staring keeps it still, but not forever: 3s of staring makes it snap at the starer. */
    private void stareCheck(int now) {
        Location center = horror.getLocation().add(0, horror.getHeight() / 2, 0);
        for (Player player : fight.players()) {
            org.bukkit.util.Vector to = center.toVector().subtract(player.getEyeLocation().toVector());
            boolean staring = to.length() < 30 && Math.toDegrees(to.angle(player.getEyeLocation().getDirection())) < 15;
            int stared = staring ? stares.merge(player.getUniqueId(), 5, Integer::sum) : 0;
            if (!staring) {
                stares.remove(player.getUniqueId());
            }
            if (stared >= STARE_LIMIT && now >= lungeReady) {
                stares.clear();
                fight.broadcast("&6The Horror won't be watched forever!");
                lunge(player, false);
                return;
            }
        }
    }

    /** Appears right next to a player (in front of them, or behind for the creak) and strikes. */
    private void lunge(Player player, boolean behind) {
        lungeReady = fight.elapsed() + 100;
        org.bukkit.util.Vector facing = player.getLocation().getDirection().setY(0);
        if (facing.lengthSquared() < 0.01) {
            facing = new org.bukkit.util.Vector(1, 0, 0);
        }
        facing.normalize().multiply(behind ? -1.8 : 1.8);
        Location spot = player.getLocation().add(facing);
        spot.setY(io.github.amitelia.occultech.boss.tier2.Abyss.groundY(spot));
        spot.setDirection(player.getLocation().toVector().subtract(spot.toVector()));
        horror.getWorld().spawnParticle(Particle.BLOCK, horror.getLocation().add(0, 1.5, 0), 25, 0.5, 1, 0.5, Material.PALE_OAK_LOG.createBlockData());
        horror.teleport(spot);
        horror.swingMainHand();
        horror.getWorld().playSound(spot, Sound.ENTITY_CREAKING_ATTACK, 2F, 0.6F);
        player.damage(LUNGE_DAMAGE, horror);
        horror.setTarget(player);
    }

    private void growHearts() {
        heartsLeft = HEARTS;
        double offset = Math.random() * Math.PI;
        for (int i = 0; i < HEARTS; i++) {
            double angle = offset + Math.PI * 2 * i / HEARTS;
            double radius = Math.min(fight.radius() - 3, 15);
            Location at = fight.center().clone().add(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
            hearts.add(fight.spawnObject(at, Material.CREAKING_HEART, 1.2F, HEART_HITS, this::heartBroken));
        }
        fight.broadcast("&6Its hearts take root around the circle - &fbreak all four to make it bleed.");
        horror.getWorld().playSound(horror.getLocation(), Sound.BLOCK_CREAKING_HEART_SPAWN, 2F, 0.7F);
    }

    private void heartBroken() {
        int left = --heartsLeft;
        horror.getWorld().playSound(horror.getLocation(), Sound.ENTITY_CREAKING_TWITCH, 2F, 0.7F);
        if (left <= 0) {
            vulnerableUntil = fight.elapsed() + VULNERABLE_TICKS;
            horror.setGlowing(true);
            fight.broadcast("&6The last heart breaks - &fthe Horror can be hurt for 20 seconds!");
        }
    }
}
