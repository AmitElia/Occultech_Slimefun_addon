package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

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
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Tier-3 mini-boss (Infinity gear). A giant creaking that - unlike every other creaking - never freezes when looked at
 * (Session R4: our own movement and attacks replace vanilla's AI). It stalks its target and fills the circle with area
 * attacks:
 * <ul>
 * <li>Heart markers: four creaking-heart markers stand around the circle (display entities, not real blocks). While
 * any stands, the Horror can't be hurt. Breaking all four opens a 20s window, then the hearts regrow. The hearts pulse
 * with thorns now and then, so breaking them is a fight of its own.</li>
 * <li>Swipe: a heavy blow at close range, at most every 2s.</li>
 * <li>Root eruptions: three lanes of roots burst from it, toward its target and to either side.</li>
 * <li>Sap rain: amber sap falls on marked spots - under every player and around the circle.</li>
 * <li>Ground slam: it stamps, and a ring of roots erupts around it.</li>
 * <li>Creak: it vanishes and strikes from behind a player.</li>
 * </ul>
 * Its hits are few and heavy. It is not tied to a real creaking heart, so its health is ours to manage; it takes an
 * eighth of the damage dealt.
 */
public final class HeartwoodHorror extends BossBehavior {

    private static final Mechanic SWIPE = Mechanic.of("HEARTWOOD_HORROR", "Swipe", 47, Mechanic.Kind.MELEE, false);
    private static final Mechanic LUNGE_DAMAGE = Mechanic.of("HEARTWOOD_HORROR", "Lunge", 59, Mechanic.Kind.AREA, true);
    private static final Mechanic ERUPTION = Mechanic.of("HEARTWOOD_HORROR", "Root eruption", 55, Mechanic.Kind.AREA, true);
    private static final Mechanic SAP = Mechanic.of("HEARTWOOD_HORROR", "Sap rain", 45, Mechanic.Kind.AREA, true);
    private static final Mechanic SLAM = Mechanic.of("HEARTWOOD_HORROR", "Ground slam", 57, Mechanic.Kind.AREA, true);
    private static final Mechanic THORNS = Mechanic.of("HEARTWOOD_HORROR", "Heart thorns", 42, Mechanic.Kind.AREA, true);

    private static final double HEALTH = 320;
    private static final double ARMOR = 0.125;
    private static final int HEARTS = 4;
    private static final int HEART_HITS = 12;
    private static final int VULNERABLE_TICKS = 400;
    private static final double SPEED = 0.2;
    private static final double REACH = 3.2;
    private static final int SWIPE_COOLDOWN = 40;
    private static final int ERUPTION_INTERVAL = 140;
    private static final int SAP_INTERVAL = 180;
    private static final int SLAM_INTERVAL = 220;
    private static final int THORN_INTERVAL = 120;
    private static final int CREAK_INTERVAL = 260;
    private static final int WARNING = 30;
    private static final double LANE_LENGTH = 14;
    private static final double LANE_WIDTH = 2.2;
    private static final double SAP_RADIUS = 2.2;
    private static final double SLAM_RADIUS = 6;
    private static final double THORN_RADIUS = 3.5;
    private static final Color ROOTS = Color.fromRGB(90, 70, 50);
    private static final Color AMBER = Color.fromRGB(230, 140, 40);

    /** A delayed area hit: when it lands, where, and what decides who's caught. */
    private record Pending(int at, Mechanic mechanic, java.util.function.Predicate<Location> caught, Runnable effect) {}

    private Creaking horror;
    private final List<BossFight.FightObject> hearts = new ArrayList<>();
    private final List<Pending> pending = new ArrayList<>();
    /** Roots and sap round it while its hearts make it invulnerable. */
    @javax.annotation.Nullable private io.github.amitelia.occultech.boss.AirEffects.Aura roots;
    private int vulnerableUntil = -1;
    private int heartsLeft;
    private int nextSwipe;
    private int creakAt = -1;
    private Player creakTarget;
    private Player target;

    public HeartwoodHorror(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        horror = fight.spawnBoss(Creaking.class, at.clone().add(0, 1, 0), c -> {
            c.setCustomName(ChatColor.GOLD + "Heartwood Horror");
            c.setCustomNameVisible(true);
            BossFight.setAttribute(c, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(c, Attribute.SCALE, 1.6);
            BossFight.setAttribute(c, Attribute.FOLLOW_RANGE, 48);
            BossFight.setAttribute(c, Attribute.KNOCKBACK_RESISTANCE, 1);
            // no vanilla AI: a creaking freezes while watched; ours walks and strikes whether you look or not
            Abyss.puppet(c);
            c.setGravity(true);
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

    /** Every tick: it stalks its target. */
    @Override
    public void move() {
        if (!horror.isValid() || target == null || !target.isValid()) {
            return;
        }
        Abyss.walk(horror, target.getLocation(), SPEED, REACH - 1);
    }

    @Override
    public void tick() {
        if (!horror.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (target == null || !fight.players().contains(target) || every(160)) {
            target = fight.nearestPlayer(horror.getLocation());
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
        if (every(20)) {   // the hearts pulse so players can find them
            for (BossFight.FightObject heart : hearts) {
                heart.location().getWorld().spawnParticle(Particle.DUST, heart.location().clone().add(0, 1.2, 0), 6, 0.2, 0.4, 0.2, 0,
                    new Particle.DustOptions(Color.fromRGB(255, 140, 40), 1.2F));
            }
        }

        swipe(now);
        if (every(ERUPTION_INTERVAL)) {
            eruption(now);
        }
        if (every(SAP_INTERVAL)) {
            sapRain(now);
        }
        if (every(SLAM_INTERVAL)) {
            slam(now);
        }
        if (every(THORN_INTERVAL) && !hearts.isEmpty()) {
            thorns(now);
        }
        creak(now);
        land(now);
    }

    // ------------------------------------------------------------------ attacks

    private void swipe(int now) {
        if (target == null || now < nextSwipe) {
            return;
        }
        if (target.getLocation().distanceSquared(horror.getLocation()) <= REACH * REACH) {
            nextSwipe = now + SWIPE_COOLDOWN;
            Abyss.face(horror, target.getEyeLocation());
            horror.swingMainHand();
            horror.getWorld().playSound(horror.getLocation(), Sound.ENTITY_CREAKING_ATTACK, 1.5F, 0.7F);
            fight.hit(target, SWIPE, horror);
        }
    }

    /** Three lanes of roots burst from it: toward its target and 35 degrees to either side. */
    private void eruption(int now) {
        Player aim = target != null ? target : fight.randomPlayer();
        if (aim == null) {
            return;
        }
        Location origin = ground(horror.getLocation());
        Vector toward = aim.getLocation().toVector().subtract(origin.toVector()).setY(0);
        if (toward.lengthSquared() < 0.01) {
            toward = new Vector(1, 0, 0);
        }
        toward.normalize();
        horror.getWorld().playSound(origin, Sound.BLOCK_ROOTS_PLACE, 2F, 0.5F);
        for (double turn : new double[] { -35, 0, 35 }) {
            Vector dir = toward.clone().rotateAroundY(Math.toRadians(turn));
            FloorDecals.lane(fight, origin, dir, LANE_LENGTH, LANE_WIDTH, WARNING, ROOTS);
            pending.add(new Pending(now + WARNING, ERUPTION, at -> inLane(at, origin, dir), () -> {
                for (double t = 1; t <= LANE_LENGTH; t += 1.5) {
                    Location spot = origin.clone().add(dir.clone().multiply(t));
                    spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.4, 0), 8, 0.4, 0.4, 0.4, Material.PALE_OAK_LOG.createBlockData());
                }
                origin.getWorld().playSound(origin, Sound.BLOCK_ROOTS_BREAK, 2F, 0.6F);
            }));
        }
    }

    private static boolean inLane(Location at, Location origin, Vector dir) {
        Vector offset = at.toVector().subtract(origin.toVector()).setY(0);
        double along = offset.dot(dir);
        double across = offset.clone().subtract(dir.clone().multiply(along)).length();
        return along >= 0 && along <= LANE_LENGTH && across <= LANE_WIDTH / 2 + 0.3;
    }

    /** Sap falls on marked spots: under every player, and a few more around the circle. */
    private void sapRain(int now) {
        List<Location> spots = new ArrayList<>();
        for (Player player : fight.players()) {
            spots.add(ground(player.getLocation()));
        }
        for (int i = 0; i < 3; i++) {
            spots.add(ground(fight.randomPoint(2, fight.radius() - 2)));
        }
        fight.broadcast("&6Amber sap gathers overhead - &fmove!");
        for (Location spot : spots) {
            fight.telegraph(spot, SAP_RADIUS, WARNING + 5, AMBER);
            pending.add(new Pending(now + WARNING + 5, SAP, at -> at.distanceSquared(spot) <= SAP_RADIUS * SAP_RADIUS, () -> {
                spot.getWorld().spawnParticle(Particle.FALLING_HONEY, spot.clone().add(0, 3, 0), 30, SAP_RADIUS / 2, 0.5, SAP_RADIUS / 2, 0);
                spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.3, 0), 20, SAP_RADIUS / 2, 0.1, SAP_RADIUS / 2,
                    Material.RESIN_BLOCK.createBlockData());
                spot.getWorld().playSound(spot, Sound.BLOCK_HONEY_BLOCK_FALL, 1.5F, 0.6F);
            }));
        }
    }

    /** It stamps: a ring of roots erupts around it. */
    private void slam(int now) {
        Location center = ground(horror.getLocation());
        fight.telegraph(center, SLAM_RADIUS, WARNING, ROOTS, FloorDecals.Mark.ROOTS);
        horror.getWorld().playSound(center, Sound.ENTITY_CREAKING_ACTIVATE, 2F, 0.5F);
        pending.add(new Pending(now + WARNING, SLAM, at -> at.distanceSquared(center) <= SLAM_RADIUS * SLAM_RADIUS, () -> {
            FloorDecals.wave(fight, center, 0.5, SLAM_RADIUS, 10, ROOTS);
            io.github.amitelia.occultech.boss.AirEffects.burst(fight, center.clone().add(0, 0.8, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT,
                ROOTS, 5F);
            center.getWorld().spawnParticle(Particle.BLOCK, center.clone().add(0, 0.3, 0), 80, SLAM_RADIUS / 2, 0.2, SLAM_RADIUS / 2,
                Material.PALE_OAK_LOG.createBlockData());
            center.getWorld().playSound(center, Sound.ENTITY_GENERIC_EXPLODE, 1.2F, 0.5F);
        }));
    }

    /** Each standing heart pulses with thorns: breaking them is a fight of its own. */
    private void thorns(int now) {
        for (BossFight.FightObject heart : hearts) {
            Location center = ground(heart.location());
            fight.telegraph(center, THORN_RADIUS, WARNING - 5, AMBER, FloorDecals.Mark.SPIKES);
            pending.add(new Pending(now + WARNING - 5, THORNS, at -> at.distanceSquared(center) <= THORN_RADIUS * THORN_RADIUS, () -> {
                center.getWorld().spawnParticle(Particle.CRIT, center.clone().add(0, 0.8, 0), 40, THORN_RADIUS / 2, 0.5, THORN_RADIUS / 2, 0.2);
                center.getWorld().playSound(center, Sound.ENCHANT_THORNS_HIT, 1.5F, 0.6F);
            }));
        }
    }

    /** Lands every pending area hit whose time has come. */
    private void land(int now) {
        pending.removeIf(hit -> {
            if (now < hit.at()) {
                return false;
            }
            hit.effect().run();
            for (Player player : fight.players()) {
                if (hit.caught().test(player.getLocation())) {
                    fight.hit(player, hit.mechanic(), horror);
                    if (hit.mechanic() == ERUPTION || hit.mechanic() == SLAM) {
                        player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 2));
                    }
                }
            }
            return true;
        });
    }

    /** It creaks behind a player, then vanishes from where it stood and strikes from behind them. */
    private void creak(int now) {
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
            if (creakTarget != null && creakTarget.isValid() && fight.players().contains(creakTarget)) {
                lunge(creakTarget);
            }
        }
    }

    private void lunge(Player player) {
        Vector facing = player.getLocation().getDirection().setY(0);
        if (facing.lengthSquared() < 0.01) {
            facing = new Vector(1, 0, 0);
        }
        facing.normalize().multiply(-1.8);
        Location spot = player.getLocation().add(facing);
        spot.setY(Abyss.groundY(spot));
        spot.setDirection(player.getLocation().toVector().subtract(spot.toVector()));
        horror.getWorld().spawnParticle(Particle.BLOCK, horror.getLocation().add(0, 1.5, 0), 25, 0.5, 1, 0.5, Material.PALE_OAK_LOG.createBlockData());
        horror.teleport(spot);
        horror.swingMainHand();
        horror.getWorld().playSound(spot, Sound.ENTITY_CREAKING_ATTACK, 2F, 0.6F);
        fight.hit(player, LUNGE_DAMAGE, horror);
        target = player;
        nextSwipe = fight.elapsed() + SWIPE_COOLDOWN;
    }

    private static Location ground(Location at) {
        Location spot = at.clone();
        spot.setY(Abyss.groundY(at));
        return spot;
    }

    // ------------------------------------------------------------------ hearts

    private void growHearts() {
        heartsLeft = HEARTS;
        double offset = ThreadLocalRandom.current().nextDouble() * Math.PI;
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
