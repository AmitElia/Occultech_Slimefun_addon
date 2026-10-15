package io.github.amitelia.occultech.boss.tier0;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.MagmaCube;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-0 gate boss (iron gear, 4-6 minutes): the Elder of Ash, an elder toad sage with a volcano growing out of its back
 * (the id stays MIRE_MONARCH; until 2026-10-11 it was the Gelatinous Sovereign, a slime, and
 * {@link io.github.amitelia.occultech.core.BossIds} maps that old id). Its carrier is a magma cube.
 * <ul>
 * <li>The leap: every 8s marks a player's spot with an ember ring (1.5s) while he sinks onto his haunches and the volcano
 * flares, leaps onto it and sends out a shockwave that only hurts players standing on the ground - jump to dodge.</li>
 * <li>Tongue (every 10s, 8s from 33%): picks a player 5-14 blocks away it can see, marks a lane towards them (1.25s,
 * its direction locked; he turns to it), then lashes its tongue down it: the first player in the lane is hit and yanked
 * to its mouth (a capped pull, never a teleport) - step out of the lane to dodge.</li>
 * <li>The eruption (66%): the volcano throws up 3 magma cubes that land at the arena's edge and crawl back to the altar;
 * each one that arrives heals him by 6%.</li>
 * <li>Below 33%: the volcano's top blows off; he moves faster and leaves pools of lava that hurt anyone standing in
 * them.</li>
 * </ul>
 * The look comes from the Mythic body (Mobs/Skills MireMonarch.yml, model occultech_mire_monarch): the leap's coil, the
 * tongue's lash (1.25s in) and the blast are timed to the server's moments, the volcano's stages are tints on its lava,
 * and its smoke, flares and the pipe's smoke come from their places on the model. Without Mythic the fight plays as
 * before, on a bare magma cube.
 */
public final class MireMonarch extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic CRUSH = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Crush", 7, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic SHOCKWAVE = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Shockwave", 11, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic MAGMA = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Magma", 2, io.github.amitelia.occultech.boss.Mechanic.Kind.ZONE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic TONGUE = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Tongue", 8, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, true);
    private static final io.github.amitelia.occultech.boss.Mechanic SHARD = io.github.amitelia.occultech.boss.Mechanic.of("MIRE_MONARCH", "Magma spawn", 4, io.github.amitelia.occultech.boss.Mechanic.Kind.ADD, false);

    private static final Color EMBER = Color.fromRGB(255, 120, 30);
    private static final Color LAVA = Color.fromRGB(255, 90, 20);
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
    /** The model's tongue reaches about this far from his middle; the plugin draws the lash on beyond it. */
    private static final double MODEL_TONGUE = 8.5;
    private static final double BASE_HEALTH = 600;
    private static final double BASE_SPEED = 0.3;
    private static final int SHARDS = 3;
    private static final double SHARD_HEAL = 0.06;
    /** The blast clip blows the top off 0.9s in. */
    private static final int BLAST_AT = 18;

    /** The volcano's stages: above 2/3 health, below 2/3 (after the eruption), below 1/3 (the top blown off). */
    private enum Stage { DORMANT, AWAKE, BLOWN }

    private final List<MagmaCube> shards = new ArrayList<>();
    private MagmaCube elder;
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
    private int blastAt = -1;
    private int flinchReady;
    private Stage stage = Stage.DORMANT;
    private boolean settled;
    /** The eruption keeps boiling for 2s after it bursts. */
    private int eruptingUntil = -1;

    public MireMonarch(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        elder = fight.spawnBoss(MagmaCube.class, at, s -> {
            s.setSize(7);
            s.setCustomName(ChatColor.GOLD + "The Elder of Ash");
            s.setCustomNameVisible(true);
            BossFight.setAttribute(s, Attribute.MAX_HEALTH, BASE_HEALTH);
            fight.label(s, CRUSH);
            BossFight.setAttribute(s, Attribute.KNOCKBACK_RESISTANCE, 0.8);
            BossFight.setAttribute(s, Attribute.FOLLOW_RANGE, 32);
            BossFight.setAttribute(s, Attribute.MOVEMENT_SPEED, BASE_SPEED);
            s.setHealth(BASE_HEALTH);
        });
        act("STAGE_DORMANT", null);                      // the lava is painted white: it needs its tint at once
    }

    /**
     * On the first tick (a resumed fight has its saved health by then): a fight that comes back below 2/3 or 1/3 takes up
     * its stage without replaying the eruption or the blast.
     */
    private void settle() {
        settled = true;
        double health = fight.healthFraction();
        if (health <= 0.33) {
            split = enraged = true;
            stage = Stage.BLOWN;
            BossFight.setAttribute(elder, Attribute.MOVEMENT_SPEED, BASE_SPEED * 1.6);
        } else if (health <= 0.66) {
            split = true;
            stage = Stage.AWAKE;
        }
        if (stage != Stage.DORMANT) {
            act("STAGE_" + stage.name(), null);
        }
    }

    private boolean mythic() {
        return fight.usesMythicBody();
    }

    private void act(String action, @Nullable Entity target) {
        if (mythic() && elder != null) {
            fight.playAction(elder, action, target);
        }
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        int now = fight.elapsed();
        if (now >= flinchReady && leapAt < now && lashAt < 0 && !airborne) {
            flinchReady = now + 20;
            act("FLINCH", null);
        }
    }

    /**
     * Every tick (Mythic body): the carrier is a magma cube, which moves in bounces; under a 9-block toad those read as
     * hops of the whole mountain, so outside the leap he keeps to the ground and crawls. Through the leap's and the
     * tongue's warnings he holds still and faces where he will strike, and the blast lands on its frame.
     */
    @Override
    public void move() {
        if (elder == null || !elder.isValid() || !mythic()) {
            return;
        }
        int now = fight.elapsed();
        if (blastAt >= 0 && now >= blastAt) {
            blastAt = -1;
            blast();
        }
        Vector v = elder.getVelocity();
        boolean coiling = slamTarget != null && leapAt >= now;
        if (coiling || lashAt >= 0) {
            elder.setVelocity(new Vector(0, Math.min(0, v.getY()), 0));
            Vector look = coiling ? slamTarget.toVector().subtract(elder.getLocation().toVector()) : tongueDir;
            if (look != null && look.clone().setY(0).lengthSquared() > 0.01) {
                elder.setRotation((float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ())), 0);
            }
        } else if (!airborne && v.getY() > 0.08) {
            elder.setVelocity(v.setY(0.08));
        }
    }

    @Override
    public void tick() {
        if (!elder.isValid()) {
            return;
        }
        if (!settled) {
            settle();
        }
        int now = fight.elapsed();
        double health = fight.healthFraction();

        if (!split && health <= 0.66) {
            split = true;
            erupt();
        }
        if (!enraged && health <= 0.33) {
            enraged = true;
            enrage();
        }

        slam(now);
        tongue(now);
        tendShards();
        if (mythic()) {
            smoke(now);
        }

        if (enraged && every(PUDDLE_INTERVAL)) {
            Location at = elder.getLocation();
            fight.addHazard(at, 2.5, 200, LAVA, FloorDecals.Zone.FIRE, player -> fight.hit(player, MAGMA, elder));
            at.getWorld().playSound(at, Sound.BLOCK_LAVA_POP, 1.4F, 0.6F);
        }
    }

    /** A point on the model, standing where the carrier stands and turned the way it faces (blocks from its feet). */
    private Location modelPoint(double right, double up, double forward) {
        Location feet = elder.getLocation();
        double yaw = Math.toRadians(feet.getYaw());
        Vector facing = new Vector(-Math.sin(yaw), 0, Math.cos(yaw));
        Vector toRight = new Vector(-Math.cos(yaw), 0, -Math.sin(yaw));
        return feet.clone().add(toRight.multiply(right)).add(facing.multiply(forward)).add(0, up, 0);
    }

    /** The crater: the top of the cone, or the blown-open crater lower down once the top is gone. */
    private Location crater() {
        return modelPoint(0, stage == Stage.BLOWN ? 5.9 : 6.6, -0.4);
    }

    /** A particle burst that players see from far away (a 9-block volcano is seen across the arena and beyond). */
    private static void fx(Particle particle, Location at, int count, double dx, double dy, double dz, double speed) {
        at.getWorld().spawnParticle(particle, at, count, dx, dy, dz, speed, null, true);
    }

    /** Particles thrown along a direction (count 0: the offsets are the velocity). */
    private static void spray(Particle particle, Location at, int count, double spread, double up) {
        ThreadLocalRandom r = ThreadLocalRandom.current();
        for (int i = 0; i < count; i++) {
            at.getWorld().spawnParticle(particle, at.clone().add(r.nextGaussian() * 0.3, 0, r.nextGaussian() * 0.3), 0,
                r.nextGaussian() * spread, up * (0.7 + r.nextDouble() * 0.6), r.nextGaussian() * spread, 1, null, true);
        }
    }

    /**
     * The volcano, every behavior step: a plume rising from the crater that grows at each stage (signal-fire smoke, which
     * climbs high and is seen from far off), embers and ash drifting round the cone, lava dripping off the streams' ends;
     * thick dark smoke, fireballs at the rim and lava spray while he coils or erupts; a lava fountain once the top is
     * blown. The pipe smokes too. (docs/art/bosses/elder_of_ash/overhaul/s8_ship/hero_poses.png shows each stage.)
     */
    private void smoke(int now) {
        ThreadLocalRandom r = ThreadLocalRandom.current();
        Location top = crater();
        boolean coiling = slamTarget != null && leapAt >= now;
        boolean boiling = coiling || now < eruptingUntil;
        Location cone = modelPoint(0, 4.5, -0.4);
        switch (stage) {
            case DORMANT -> {
                fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 1, 0.3, 0.1, 0.3, 0.01);
                fx(Particle.CAMPFIRE_COSY_SMOKE, top, 1, 0.25, 0.1, 0.25, 0.01);
                if (r.nextInt(3) == 0) {
                    fx(Particle.SMALL_FLAME, top, 2, 0.3, 0.2, 0.3, 0.01);
                }
                fx(Particle.WHITE_ASH, cone, 8, 3, 2, 3, 0);
            }
            case AWAKE -> {
                fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 2, 0.35, 0.1, 0.35, 0.015);
                fx(Particle.LARGE_SMOKE, top, 1, 0.3, 0.2, 0.3, 0.02);
                if (r.nextBoolean()) {
                    fx(Particle.LAVA, top, 1, 0.3, 0.1, 0.3, 0);
                }
                fx(Particle.WHITE_ASH, cone, 12, 3.5, 2.5, 3.5, 0);
                fx(Particle.ASH, cone, 4, 3, 2, 3, 0);
            }
            case BLOWN -> {
                fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top.clone().add(0, 1.5, 0), 3, 0.5, 0.2, 0.5, 0.02);
                fx(Particle.LARGE_SMOKE, top.clone().add(0, 1, 0), 2, 0.5, 0.3, 0.5, 0.03);
                spray(Particle.FLAME, top, 5, 0.04, 0.45);              // the fountain welling up out of the crater
                fx(Particle.LAVA, top, 2, 0.5, 0.2, 0.5, 0);
                fx(Particle.DRIPPING_LAVA, top, 2, 0.9, 0.1, 0.9, 0);
                fx(Particle.ASH, cone, 10, 3.5, 2.5, 3.5, 0);
            }
        }
        if (boiling) {                                                  // thick dark smoke, fireballs, lava spray
            fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 3, 0.5, 0.2, 0.5, 0.02);
            fx(Particle.LARGE_SMOKE, top, 3, 0.5, 0.3, 0.5, 0.04);
            spray(Particle.FLAME, top, 3, 0.08, 0.3);
            fx(Particle.LAVA, top, 3, 0.4, 0.2, 0.4, 0);
            if (r.nextInt(3) == 0) {
                double a = r.nextDouble() * Math.PI * 2;
                Location rim = top.clone().add(Math.cos(a) * 0.7, 0.3, Math.sin(a) * 0.7);
                fx(Particle.EXPLOSION, rim, 1, 0.1, 0.1, 0.1, 0);
                top.getWorld().playSound(rim, Sound.BLOCK_LAVA_POP, 1.4F, 0.5F + r.nextFloat() * 0.3F);
            }
        }
        if (every(10)) {                                                // lava dripping off the streams' ends
            fx(Particle.FALLING_LAVA, modelPoint(2.95, 0.9, 0.2), 1, 0.05, 0.05, 0.1, 0);
            fx(Particle.FALLING_LAVA, modelPoint(-2.95, 1.2, -0.6), 1, 0.05, 0.05, 0.1, 0);
            if (stage != Stage.DORMANT) {
                fx(Particle.FALLING_LAVA, modelPoint(0.3, 0.9, -2.95), 1, 0.1, 0.05, 0.05, 0);
            }
        }
        if (every(20)) {                                                // the pipe
            Location bowl = modelPoint(2.9, 1.3, 5.0);
            fx(Particle.SMOKE, bowl, 3, 0.05, 0.08, 0.05, 0.01);
        }
    }

    private void slam(int now) {
        if (every(SLAM_INTERVAL)) {
            Player target = fight.randomPlayer();
            if (target != null) {
                slamTarget = target.getLocation();
                leapAt = now + SLAM_WARNING;
                fight.telegraph(slamTarget, 3.5, SLAM_WARNING + 10, EMBER, FloorDecals.Mark.SLAM);
                elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_FROG_AMBIENT, 2F, 0.5F);
                act("COIL", target);                          // he sinks and the volcano flares (1.5s, the warning)
            }
        }
        if (now == leapAt && slamTarget != null) {
            Vector jump = slamTarget.toVector().subtract(elder.getLocation().toVector()).setY(0).multiply(0.12);
            elder.setVelocity(jump.setY(0.95));
            airborne = true;
            landingCheckUntil = now + 60;
            act("LEAP", null);
        }
        if (airborne && now > leapAt + 5 && (elder.isOnGround() || now >= landingCheckUntil)) {
            airborne = false;
            slamTarget = null;
            act("LAND", null);
            act("STAGE_" + stage.name(), null);              // the coil's white flare settles back to the stage
            shockwave();
        }
    }

    private void tongue(int now) {
        if (lashAt < 0 && now >= nextTongue && !airborne && (leapAt < now || leapAt - now > TONGUE_WARNING + 15)) {
            nextTongue = now + (enraged ? TONGUE_INTERVAL_ENRAGED : TONGUE_INTERVAL);
            Location from = elder.getLocation();
            List<Player> inReach = new ArrayList<>();
            for (Player player : fight.players()) {
                double d = player.getLocation().distance(from);
                if (d >= TONGUE_MIN && d <= TONGUE_RANGE && elder.hasLineOfSight(player)) {
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
            FloorDecals.lane(fight, tongueFrom, tongueDir, TONGUE_RANGE, 2 * (TONGUE_REACH_SIDE - 0.3), TONGUE_WARNING, EMBER);
            elder.getWorld().playSound(from, Sound.ENTITY_FROG_AMBIENT, 2F, 0.5F);
            act("TONGUE", target);                            // his glare down the lane; the lash 1.25s in
        }
        if (lashAt >= 0 && now >= lashAt) {
            lashAt = -1;
            lash();
        }
    }

    /** The tongue shoots down the locked lane: the first player in it is hit and pulled to the Elder's mouth. */
    private void lash() {
        Location mouth = elder.getLocation();
        Player caught = null;
        double nearest = Double.MAX_VALUE;
        for (Player player : fight.players()) {
            Vector rel = player.getLocation().toVector().subtract(tongueFrom.toVector());
            double along = rel.getX() * tongueDir.getX() + rel.getZ() * tongueDir.getZ();
            double side = Math.abs(rel.getX() * tongueDir.getZ() - rel.getZ() * tongueDir.getX());
            if (along >= 0 && along <= TONGUE_RANGE && side <= TONGUE_REACH_SIDE && Math.abs(rel.getY()) <= 2.5
                && along < nearest && elder.hasLineOfSight(player)) {
                caught = player;
                nearest = along;
            }
        }
        double reach = caught == null ? TONGUE_RANGE : nearest;
        // the model's tongue covers the first stretch; the plugin draws it on to wherever it reaches
        for (double t = mythic() ? MODEL_TONGUE : 0.5; t <= reach; t += 0.5) {
            Location p = tongueFrom.clone().add(tongueDir.clone().multiply(t)).add(0, 1.0, 0);
            p.getWorld().spawnParticle(Particle.DUST, p, 2, 0.08, 0.08, 0.08, 0, new Particle.DustOptions(EMBER, 1.4F));
        }
        mouth.getWorld().playSound(mouth, Sound.ENTITY_FROG_TONGUE, 2F, 0.6F);
        if (caught == null) {
            return;
        }
        fight.hit(caught, TONGUE, elder);
        // a capped yank towards the mouth, landing about two blocks in front of it (knockback, never a teleport)
        Vector pull = mouth.toVector().subtract(caught.getLocation().toVector()).setY(0);
        double distance = pull.length();
        if (distance > 2.5) {
            caught.setVelocity(pull.normalize().multiply(Math.min(1.6, 0.15 + (distance - 2) * 0.1)).setY(0.42));
        }
        caught.getWorld().playSound(caught.getLocation(), Sound.ENTITY_SLIME_ATTACK, 1.2F, 0.7F);
    }

    private void shockwave() {
        Location at = elder.getLocation();
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 0.8F, 0.6F);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 60, 2.5, 0.2, 2.5, Material.BASALT.createBlockData());
        at.getWorld().spawnParticle(Particle.LARGE_SMOKE, at, 30, 2.5, 0.3, 2.5, 0.02);
        FloorDecals.wave(fight, at, 0.5, 4, 8, EMBER);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, at.clone().add(0, 0.8, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, EMBER, 4F);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 16 && player.isOnGround()) {
                fight.hit(player, SHOCKWAVE, elder);
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.9).setY(0.4));
                }
            }
        }
    }

    /** At 66%: the volcano erupts and throws 3 magma cubes to the arena's edge, which crawl back to heal him. */
    private void erupt() {
        stage = Stage.AWAKE;
        act("ERUPT", null);
        Location top = mythic() ? crater() : elder.getLocation().add(0, 2, 0);
        eruptingUntil = fight.elapsed() + 40;
        fx(Particle.EXPLOSION_EMITTER, top, 1, 0, 0, 0, 0);
        fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 20, 0.8, 0.4, 0.8, 0.05);
        fx(Particle.LARGE_SMOKE, top, 50, 0.8, 1.0, 0.8, 0.08);
        fx(Particle.LAVA, top, 40, 0.6, 0.4, 0.6, 0);
        spray(Particle.FLAME, top, 30, 0.15, 0.6);
        top.getWorld().playSound(top, Sound.ENTITY_GENERIC_EXPLODE, 2F, 0.5F);
        int count = SHARDS;
        for (int i = 0; i < count; i++) {
            double angle = Math.PI * 2 * i / count;
            Location at = fight.center().add(Math.cos(angle) * (fight.radius() - 3), 0.5, Math.sin(angle) * (fight.radius() - 3));
            MagmaCube shard = fight.spawnAdd(MagmaCube.class, at, s -> {
                s.setSize(3);
                s.setCustomName(ChatColor.GOLD + "Magma Spawn");
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 40);
                s.setHealth(40);
                fight.label(s, SHARD);
            });
            if (shard != null) {
                shards.add(shard);
                at.getWorld().spawnParticle(Particle.LAVA, at, 12, 0.4, 0.3, 0.4, 0);
            }
        }
        fight.broadcast("&6The Elder of Ash erupts, hurling magma! &fStop the magma spawn before they crawl back to the altar!");
    }

    private void tendShards() {
        Location altar = fight.center();
        shards.removeIf(shard -> {
            if (shard.isDead() || !shard.isValid()) {
                return true;
            }
            Vector toAltar = altar.toVector().subtract(shard.getLocation().toVector()).setY(0);
            if (toAltar.lengthSquared() < 4) {
                fight.healBoss(elder, SHARD_HEAL);
                shard.getWorld().spawnParticle(Particle.LAVA, shard.getLocation(), 20, 0.5, 0.5, 0.5, 0);
                shard.getWorld().playSound(shard.getLocation(), Sound.BLOCK_LAVA_EXTINGUISH, 1.5F, 0.8F);
                fight.broadcast("&6A magma spawn flows back into the Elder.");
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

    /** At 33%: the volcano's top blows off (the blast lands 0.9s into the clip); he speeds up and sheds lava pools. */
    private void enrage() {
        BossFight.setAttribute(elder, Attribute.MOVEMENT_SPEED, BASE_SPEED * 1.6);
        fight.broadcast("&6The Elder of Ash's peak blows apart! &fLava pours from him now.");
        if (mythic()) {
            act("BLOW", null);
            blastAt = fight.elapsed() + BLAST_AT;
        } else {
            stage = Stage.BLOWN;
            elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_GENERIC_EXPLODE, 2F, 0.4F);
        }
    }

    private void blast() {
        stage = Stage.BLOWN;
        Location top = crater();
        eruptingUntil = fight.elapsed() + 40;
        fx(Particle.EXPLOSION_EMITTER, top.clone().add(0, 0.8, 0), 2, 0.4, 0.4, 0.4, 0);
        fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 30, 1.0, 0.4, 1.0, 0.06);
        fx(Particle.LARGE_SMOKE, top, 60, 1.0, 1.2, 1.0, 0.1);
        fx(Particle.LAVA, top, 50, 1.0, 0.6, 1.0, 0);
        spray(Particle.FLAME, top, 40, 0.2, 0.7);
        top.getWorld().spawnParticle(Particle.BLOCK, top, 60, 1.2, 0.6, 1.2, 0.2, Material.BASALT.createBlockData(), true);
        top.getWorld().playSound(top, Sound.ENTITY_GENERIC_EXPLODE, 2.5F, 0.4F);
    }
}
