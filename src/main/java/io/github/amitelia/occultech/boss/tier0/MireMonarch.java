package io.github.amitelia.occultech.boss.tier0;

import io.github.amitelia.occultech.boss.FloorDecals;

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
import org.bukkit.entity.Player;
import org.bukkit.entity.Slime;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-0 gate boss (iron gear, 4-6 minutes): the Mire Monarch, a giant crowned cellar toad (until 2026-10-11 the
 * Gelatinous Sovereign, a slime; its old id is mapped by {@link io.github.amitelia.occultech.core.BossIds}).
 * Its body is still a slime until the new model ships.
 * <ul>
 * <li>Phase 1: every 8s marks a player's spot with a lime ring (1.5s), leaps onto it and sends out a shockwave that
 * only hurts players standing on the ground - jump to dodge.</li>
 * <li>Tongue (every 10s, 8s from 33%): picks a player 5-14 blocks away it can see, marks a lane towards them (1.25s,
 * its direction locked), then lashes its tongue down it: the first player in the lane is hit and yanked to its mouth
 * (a capped pull, never a teleport) - step out of the lane to dodge.</li>
 * <li>Phase 2 (66%): splits off 3 shards that crawl back to the altar; each one that arrives heals the Monarch by 6%.</li>
 * <li>Phase 3 (33%): shrinks and speeds up, leaving acid puddles that hurt anyone standing in them.</li>
 * </ul>
 */
public final class MireMonarch extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic CRUSH = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Crush", 7, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic SHOCKWAVE = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Shockwave", 11, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic ACID_BURN = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Acid", 2, io.github.amitelia.occultech.boss.Mechanic.Kind.ZONE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic TONGUE = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Tongue", 8, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, true);
    private static final io.github.amitelia.occultech.boss.Mechanic SHARD = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Shard", 4, io.github.amitelia.occultech.boss.Mechanic.Kind.ADD, false);

    private static final Color LIME = Color.fromRGB(120, 230, 60);
    private static final Color ACID = Color.fromRGB(160, 255, 40);
    private static final int SLAM_INTERVAL = 160;
    private static final int SLAM_WARNING = 30;
    private static final int PUDDLE_INTERVAL = 100;
    private static final int TONGUE_INTERVAL = 200;
    private static final int TONGUE_INTERVAL_ENRAGED = 160;
    private static final int TONGUE_WARNING = 25;
    private static final double TONGUE_MIN = 5;
    private static final double TONGUE_RANGE = 14;
    /** Half the lane's width plus a player's half width. */
    private static final double TONGUE_REACH_SIDE = 1.3;
    private static final double BASE_HEALTH = 600;
    private static final int SHARDS = 3;
    private static final double SHARD_HEAL = 0.06;

    private final List<Slime> shards = new ArrayList<>();
    private Slime sovereign;
    private Location slamTarget;
    private int leapAt = -1;
    private int landingCheckUntil = -1;
    private boolean airborne;
    private int nextTongue = TONGUE_INTERVAL / 2;
    private int lashAt = -1;
    private Location tongueFrom;
    private Vector tongueDir;
    private boolean split;
    private boolean enraged;

    public MireMonarch(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        sovereign = fight.spawnBoss(Slime.class, at, s -> {
            s.setSize(7);
            s.setCustomName(ChatColor.GREEN + "Mire Monarch");
            s.setCustomNameVisible(true);
            BossFight.setAttribute(s, Attribute.MAX_HEALTH, BASE_HEALTH);
            fight.label(s, CRUSH);
            BossFight.setAttribute(s, Attribute.KNOCKBACK_RESISTANCE, 0.8);
            BossFight.setAttribute(s, Attribute.FOLLOW_RANGE, 32);
            s.setHealth(BASE_HEALTH);
        });
    }

    @Override
    public void tick() {
        if (!sovereign.isValid()) {
            return;
        }
        int now = fight.elapsed();
        double health = fight.healthFraction();

        if (!split && health <= 0.66) {
            split = true;
            splitShards();
        }
        if (!enraged && health <= 0.33) {
            enraged = true;
            enrage();
        }

        slam(now);
        tongue(now);
        tendShards();

        if (enraged && every(PUDDLE_INTERVAL)) {
            Location at = sovereign.getLocation();
            fight.addHazard(at, 2.5, 200, ACID, FloorDecals.Zone.ACID, player -> fight.hit(player, ACID_BURN, sovereign));
            at.getWorld().playSound(at, Sound.BLOCK_SLIME_BLOCK_FALL, 1F, 0.6F);
        }
    }

    private void slam(int now) {
        if (every(SLAM_INTERVAL)) {
            Player target = fight.randomPlayer();
            if (target != null) {
                slamTarget = target.getLocation();
                leapAt = now + SLAM_WARNING;
                fight.telegraph(slamTarget, 3.5, SLAM_WARNING + 10, LIME, FloorDecals.Mark.SLAM);
                sovereign.getWorld().playSound(sovereign.getLocation(), Sound.ENTITY_SLIME_SQUISH, 2F, 0.5F);
            }
        }
        if (now == leapAt && slamTarget != null) {
            Vector jump = slamTarget.toVector().subtract(sovereign.getLocation().toVector()).setY(0).multiply(0.12);
            sovereign.setVelocity(jump.setY(0.95));
            airborne = true;
            landingCheckUntil = now + 60;
        }
        if (airborne && now > leapAt + 5 && (sovereign.isOnGround() || now >= landingCheckUntil)) {
            airborne = false;
            shockwave();
        }
    }

    private void tongue(int now) {
        if (lashAt < 0 && now >= nextTongue && !airborne && (leapAt < now || leapAt - now > TONGUE_WARNING + 15)) {
            nextTongue = now + (enraged ? TONGUE_INTERVAL_ENRAGED : TONGUE_INTERVAL);
            Location from = sovereign.getLocation();
            List<Player> inReach = new ArrayList<>();
            for (Player player : fight.players()) {
                double d = player.getLocation().distance(from);
                if (d >= TONGUE_MIN && d <= TONGUE_RANGE && sovereign.hasLineOfSight(player)) {
                    inReach.add(player);
                }
            }
            if (inReach.isEmpty()) {
                return;
            }
            Player target = inReach.get(ThreadLocalRandom.current().nextInt(inReach.size()));
            Vector dir = target.getLocation().toVector().subtract(from.toVector()).setY(0);
            if (dir.lengthSquared() < 0.01) {
                return;
            }
            // the lane's direction is locked now; the lash uses this same geometry
            tongueFrom = from.clone();
            tongueDir = dir.normalize();
            lashAt = now + TONGUE_WARNING;
            FloorDecals.lane(fight, tongueFrom, tongueDir, TONGUE_RANGE, 2 * (TONGUE_REACH_SIDE - 0.3), TONGUE_WARNING, LIME);
            sovereign.getWorld().playSound(from, Sound.ENTITY_FROG_AMBIENT, 2F, 0.5F);
        }
        if (lashAt >= 0 && now >= lashAt) {
            lashAt = -1;
            lash();
        }
    }

    /** The tongue shoots down the locked lane: the first player in it is hit and pulled to the Monarch's mouth. */
    private void lash() {
        Location mouth = sovereign.getLocation();
        Player caught = null;
        double nearest = Double.MAX_VALUE;
        for (Player player : fight.players()) {
            Vector rel = player.getLocation().toVector().subtract(tongueFrom.toVector());
            double along = rel.getX() * tongueDir.getX() + rel.getZ() * tongueDir.getZ();
            double side = Math.abs(rel.getX() * tongueDir.getZ() - rel.getZ() * tongueDir.getX());
            if (along >= 0 && along <= TONGUE_RANGE && side <= TONGUE_REACH_SIDE && Math.abs(rel.getY()) <= 2.5
                && along < nearest && sovereign.hasLineOfSight(player)) {
                caught = player;
                nearest = along;
            }
        }
        double reach = caught == null ? TONGUE_RANGE : nearest;
        for (double t = 0.5; t <= reach; t += 0.5) {
            Location p = tongueFrom.clone().add(tongueDir.clone().multiply(t)).add(0, 1.0, 0);
            p.getWorld().spawnParticle(Particle.DUST, p, 2, 0.08, 0.08, 0.08, 0, new Particle.DustOptions(ACID, 1.4F));
        }
        mouth.getWorld().playSound(mouth, Sound.ENTITY_FROG_TONGUE, 2F, 0.6F);
        if (caught == null) {
            return;
        }
        fight.hit(caught, TONGUE, sovereign);
        // a capped yank towards the mouth, landing about two blocks in front of it (knockback, never a teleport)
        Vector pull = mouth.toVector().subtract(caught.getLocation().toVector()).setY(0);
        double distance = pull.length();
        if (distance > 2.5) {
            caught.setVelocity(pull.normalize().multiply(Math.min(1.6, 0.15 + (distance - 2) * 0.1)).setY(0.42));
        }
        caught.getWorld().playSound(caught.getLocation(), Sound.ENTITY_SLIME_ATTACK, 1.2F, 0.7F);
    }

    private void shockwave() {
        Location at = sovereign.getLocation();
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 0.8F, 0.6F);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 60, 2.5, 0.2, 2.5, Material.SLIME_BLOCK.createBlockData());
        FloorDecals.wave(fight, at, 0.5, 4, 8, LIME);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, at.clone().add(0, 0.8, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, LIME, 4F);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 16 && player.isOnGround()) {
                fight.hit(player, SHOCKWAVE, sovereign);
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.9).setY(0.4));
                }
            }
        }
    }

    private void splitShards() {
        int count = SHARDS;
        for (int i = 0; i < count; i++) {
            double angle = Math.PI * 2 * i / count;
            Location at = fight.center().add(Math.cos(angle) * (fight.radius() - 3), 0.5, Math.sin(angle) * (fight.radius() - 3));
            Slime shard = fight.spawnAdd(Slime.class, at, s -> {
                s.setSize(3);
                s.setCustomName(ChatColor.GREEN + "Mire Spawn");
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 40);
                s.setHealth(40);
                fight.label(s, SHARD);
            });
            if (shard != null) {
                shards.add(shard);
            }
        }
        fight.broadcast("&aThe Mire Monarch retches up its spawn! &fStop them before they crawl back to the altar!");
        sovereign.getWorld().playSound(sovereign.getLocation(), Sound.ENTITY_SLIME_DEATH, 2F, 0.5F);
    }

    private void tendShards() {
        Location altar = fight.center();
        shards.removeIf(shard -> {
            if (shard.isDead() || !shard.isValid()) {
                return true;
            }
            Vector toAltar = altar.toVector().subtract(shard.getLocation().toVector()).setY(0);
            if (toAltar.lengthSquared() < 4) {
                fight.healBoss(sovereign, SHARD_HEAL);
                shard.getWorld().spawnParticle(Particle.ITEM_SLIME, shard.getLocation(), 30, 0.5, 0.5, 0.5, 0);
                shard.getWorld().playSound(shard.getLocation(), Sound.ENTITY_SLIME_SQUISH, 1.5F, 1.5F);
                fight.broadcast("&aA spawn crawls back into the Monarch.");
                shard.remove();
                return true;
            }
            shard.setTarget(null);
            if (shard.isOnGround()) {
                shard.setVelocity(toAltar.normalize().multiply(0.35).setY(0.3));
            }
            return false;
        });
    }

    private void enrage() {
        double fraction = sovereign.getHealth() / sovereign.getAttribute(Attribute.MAX_HEALTH).getValue();
        double max = sovereign.getAttribute(Attribute.MAX_HEALTH).getValue();
        // setSize resets size-based attributes, so re-apply ours afterwards and keep the health fraction
        sovereign.setSize(4);
        BossFight.setAttribute(sovereign, Attribute.MAX_HEALTH, max);
        fight.label(sovereign, CRUSH);
        BossFight.setAttribute(sovereign, Attribute.KNOCKBACK_RESISTANCE, 0.8);
        BossFight.setAttribute(sovereign, Attribute.MOVEMENT_SPEED, 0.5);
        sovereign.setHealth(Math.max(1, max * fraction));
        fight.broadcast("&aThe Mire Monarch dries and splits, sweating acid!");
        sovereign.getWorld().playSound(sovereign.getLocation(), Sound.ENTITY_SLIME_ATTACK, 2F, 0.4F);
    }
}
