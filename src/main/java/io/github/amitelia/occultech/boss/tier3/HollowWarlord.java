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
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.WitherSkeleton;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Tier-3 mini-boss (Infinity gear). A giant wither skeleton in netherite with its own warband.
 * <ul>
 * <li>Wither sweep: a ring warns for 1s, then its blade sweeps everyone close - heavy damage and Wither.</li>
 * <li>Warband: three guards join at the start and every 25s (capped). While two or more stand, the Warlord takes half
 * damage - shown by soul chains to each guard. Kill the guards, then the Warlord.</li>
 * <li>It grows faster as it weakens.</li>
 * </ul>
 * Health attributes cap at 1024, so it takes about a fifth of the damage dealt (~2200 effective health solo).
 */
public final class HollowWarlord extends BossBehavior {

    /** The soul chains to the guards shielding it, drawn in the air (Session O5). */
    private final java.util.Map<WitherSkeleton, io.github.amitelia.occultech.boss.AirEffects.Streak> chains = new java.util.HashMap<>();

    private static final double HEALTH = 400;
    private static final double ARMOR = 0.18;
    private static final double GUARDED = 0.6;
    private static final double MELEE = 45;
    private static final double SWEEP_DAMAGE = 55;
    private static final double SWEEP_RADIUS = 4.5;
    private static final int SWEEP_INTERVAL = 120;
    private static final int GUARD_INTERVAL = 500;
    private static final Color SOUL = Color.fromRGB(60, 200, 220);

    private WitherSkeleton warlord;
    private final List<WitherSkeleton> guards = new ArrayList<>();
    private int sweepAt = -1;
    private boolean enraged;

    public HollowWarlord(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        warlord = fight.spawnBoss(WitherSkeleton.class, at.clone().add(0, 1, 0), w -> {
            w.setCustomName(ChatColor.DARK_GRAY + "Hollow Warlord");
            w.setCustomNameVisible(true);
            w.getEquipment().setItemInMainHand(new ItemStack(Material.NETHERITE_SWORD));
            w.getEquipment().setHelmet(new ItemStack(Material.NETHERITE_HELMET));
            w.getEquipment().setChestplate(new ItemStack(Material.NETHERITE_CHESTPLATE));
            w.getEquipment().setLeggings(new ItemStack(Material.NETHERITE_LEGGINGS));
            w.getEquipment().setBoots(new ItemStack(Material.NETHERITE_BOOTS));
            BossFight.setAttribute(w, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(w, Attribute.ATTACK_DAMAGE, MELEE);
            BossFight.setAttribute(w, Attribute.SCALE, 1.8);
            BossFight.setAttribute(w, Attribute.FOLLOW_RANGE, 48);
            BossFight.setAttribute(w, Attribute.KNOCKBACK_RESISTANCE, 1);
        });
        callWarband();
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR * (liveGuards() >= 2 ? GUARDED : 1);
    }

    @Override
    public void tick() {
        if (!warlord.isValid()) {
            return;
        }
        int now = fight.elapsed();
        guards.removeIf(g -> !g.isValid() || g.isDead());
        if (warlord.getTarget() == null) {
            warlord.setTarget(fight.nearestPlayer(warlord.getLocation()));
        }

        // faster as it weakens: up to +50% speed
        double speed = 0.25 * (1 + 0.5 * (1 - fight.healthFraction()));
        BossFight.setAttribute(warlord, Attribute.MOVEMENT_SPEED, speed);
        if (!enraged && fight.healthFraction() < 0.35) {
            enraged = true;
            fight.broadcast("&8The Warlord's blade drinks the dark - &fit hunts faster!");
        }

        if (every(GUARD_INTERVAL)) {
            callWarband();
        }
        boolean bound = liveGuards() >= 2;
        if (io.github.amitelia.occultech.boss.AirEffects.enabled()) {
            // soul chains to each living guard while they shield it (Session O5); a chain snaps when its guard dies
            chains.entrySet().removeIf(entry -> {
                boolean keep = bound && entry.getKey().isValid() && !entry.getKey().isDead() && entry.getValue().valid();
                if (!keep) {
                    entry.getValue().snap();
                }
                return !keep;
            });
            if (bound) {
                for (WitherSkeleton guard : guards) {
                    if (!guard.isValid() || guard.isDead()) {
                        continue;
                    }
                    Location from = warlord.getLocation().add(0, 2, 0);
                    Location to = guard.getLocation().add(0, 1.2, 0);
                    io.github.amitelia.occultech.boss.AirEffects.Streak chain = chains.get(guard);
                    if (chain == null) {
                        chains.put(guard, io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "air_chain", from, to, SOUL, 0.45F));
                    } else {
                        chain.aim(from, to, 0.45F, io.github.amitelia.occultech.boss.BossService.STEP);
                    }
                }
            }
        } else if (bound && every(10)) {
            for (WitherSkeleton guard : guards) {
                Abyss.line(warlord.getLocation().add(0, 2, 0), guard.getLocation().add(0, 1.2, 0), new Particle.DustOptions(SOUL, 0.6F), 0.7);
            }
        }

        if (every(enraged ? 80 : SWEEP_INTERVAL) && sweepAt < 0) {
            sweepAt = now + 20;
            Location ground = warlord.getLocation();
            ground.setY(Abyss.groundY(ground));
            fight.telegraph(ground, SWEEP_RADIUS, 25, Color.fromRGB(40, 40, 40), FloorDecals.Mark.SWEEP);
            warlord.getWorld().playSound(warlord.getLocation(), Sound.ENTITY_WITHER_SKELETON_AMBIENT, 2F, 0.5F);
        }
        if (sweepAt >= 0 && now >= sweepAt) {
            sweepAt = -1;
            sweep();
        }
    }

    private void sweep() {
        Location at = warlord.getLocation();
        warlord.swingMainHand();
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, at.clone().add(0, 1.3, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.SLASH, SOUL, (float) (SWEEP_RADIUS * 2));
        at.getWorld().playSound(at, Sound.ENTITY_PLAYER_ATTACK_SWEEP, 2F, 0.6F);
        for (int i = 0; i < 24; i++) {
            double angle = Math.PI * 2 * i / 24;
            at.getWorld().spawnParticle(Particle.SWEEP_ATTACK, at.clone().add(Math.cos(angle) * 3, 1, Math.sin(angle) * 3), 1);
        }
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= SWEEP_RADIUS * SWEEP_RADIUS) {
                player.damage(SWEEP_DAMAGE, warlord);
                player.addPotionEffect(new PotionEffect(PotionEffectType.WITHER, 100, 1));
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.8).setY(0.3));
                }
            }
        }
    }

    private void callWarband() {
        for (int i = 0; i < 3 && liveGuards() < 3; i++) {
            WitherSkeleton guard = fight.spawnAdd(WitherSkeleton.class, fight.randomPoint(3, 8).add(0, 1, 0), g -> {
                g.getEquipment().setItemInMainHand(new ItemStack(Material.STONE_SWORD));
                g.getEquipment().setHelmet(new ItemStack(Material.CHAINMAIL_HELMET));
                BossFight.setAttribute(g, Attribute.MAX_HEALTH, 60);
                g.setHealth(60);
                BossFight.setAttribute(g, Attribute.ATTACK_DAMAGE, 25);
            });
            if (guard != null) {
                guards.add(guard);
                guard.setTarget(fight.randomPlayer());
            }
        }
        fight.broadcast("&8The warband answers its Warlord - &fcut them down to break its guard.");
    }

    private int liveGuards() {
        int count = 0;
        for (WitherSkeleton guard : guards) {
            if (guard.isValid() && !guard.isDead()) {
                count++;
            }
        }
        return count;
    }
}
