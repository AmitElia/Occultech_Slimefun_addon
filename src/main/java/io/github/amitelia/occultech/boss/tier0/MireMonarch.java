package io.github.amitelia.occultech.boss.tier0;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.block.Block;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Frog;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.MagmaCube;
import org.bukkit.entity.Player;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.AirEffects;
import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Tier-0 gate boss (iron gear, 4-6 minutes): the Elder of Ash, an elder toad sage with a volcano growing out of its back
 * (the id stays MIRE_MONARCH; until 2026-10-11 it was the Gelatinous Sovereign, a slime, and
 * {@link io.github.amitelia.occultech.core.BossIds} maps that old id). Its carrier is a magma cube that the script moves:
 * no vanilla AI, so no bouncing; he crawls after the nearest fighter and always turns to face whoever he is after.
 * <ul>
 * <li>The leap: every 8s marks a player's spot with an ember ring (1.5s) while he sinks onto his haunches facing it, then
 * leaps onto it in a high arc and sends out a shockwave that only hurts players standing on the ground - jump to dodge.
 * The landing splashes lava.</li>
 * <li>Tongue (every 10s, 8s from 66%): picks a player 5-14 blocks away it can see and tracks them for 1s, turning with
 * them; then he locks on (the lane shows, his mouth hangs open, 0.75s) and the tongue shoots straight down the lane: the
 * first player in it is hit and yanked to his mouth (a capped pull, never a teleport) - step out of the lane to dodge.</li>
 * <li>Volcanic rocks: the volcano lobs magma blocks in high arcs at the fighters (each landing spot is marked for the
 * whole flight); they burst on landing and leave a pool of lava. More of them, more often, from 66%.</li>
 * <li>The eruption (66%): the volcano throws 3 Ash Frogs (tanky frogs, three times a frog's size) to the arena's edge;
 * they hop back to the altar, and each one that arrives heals him by 6%. The lava turns from orange to deep red: from
 * here he crawls faster, throws more rocks, strikes with the tongue more often and leaves lava pools behind him.</li>
 * <li>Below 33%: the volcano's top blows off; faster still, the rocks and the pools come quicker.</li>
 * </ul>
 * The look comes from the Mythic body (Mobs/Skills MireMonarch.yml, model occultech_mire_monarch): the leap's coil, the
 * tongue's lash (1.75s in) and the blast are timed to the server's moments, the volcano's stages are tints on its lava,
 * and its smoke, flares and the pipe's smoke come from their places on the model. Without Mythic the fight plays the
 * same on a bare magma cube.
 */
public final class MireMonarch extends BossBehavior {

    private static final Mechanic CRUSH = Mechanic.of("MIRE_MONARCH", "Crush", 7, Mechanic.Kind.MELEE, false);
    private static final Mechanic SHOCKWAVE = Mechanic.of("MIRE_MONARCH", "Shockwave", 11, Mechanic.Kind.AREA, true);
    private static final Mechanic MAGMA = Mechanic.of("MIRE_MONARCH", "Magma", 2, Mechanic.Kind.ZONE, false);
    private static final Mechanic TONGUE = Mechanic.of("MIRE_MONARCH", "Tongue", 8, Mechanic.Kind.MELEE, true);
    private static final Mechanic ROCK = Mechanic.of("MIRE_MONARCH", "Volcanic rock", 7, Mechanic.Kind.AREA, true);

    /** Stage one's lava: orange. */
    private static final Color ORANGE = Color.fromRGB(255, 140, 30);
    /** From the eruption on: deep red. */
    private static final Color DEEP_RED = Color.fromRGB(190, 25, 10);
    private static final Color TONGUE_PINK = Color.fromRGB(196, 92, 84);
    private static final Color TONGUE_TIP = Color.fromRGB(255, 150, 60);
    private static final int SLAM_INTERVAL = 160;
    private static final int SLAM_WARNING = 30;
    private static final int PUDDLE_INTERVAL = 100;
    private static final int PUDDLE_INTERVAL_BLOWN = 60;
    private static final int TONGUE_INTERVAL = 200;
    private static final int TONGUE_INTERVAL_AWAKE = 160;
    /** He tracks his target this long (ticks), turning with them, ... */
    private static final int TONGUE_AIM = 20;
    /** ... then locks on: the lane shows and his mouth hangs open this long before the lash (the clip's 1.75 s). */
    private static final int TONGUE_LOCK = 15;
    /** The tongue stays out this long, then snaps back over {@link #TONGUE_BACK}. */
    private static final int TONGUE_OUT = 12;
    private static final int TONGUE_BACK = 5;
    private static final double TONGUE_MIN = 5;
    private static final double TONGUE_RANGE = 14;
    /** Half the lane's width plus a player's half width. */
    private static final double TONGUE_REACH_SIDE = 1.3;
    /** The model's tongue reaches about this far from his middle; the plugin draws it on beyond, straight down the lane. */
    private static final double MODEL_TONGUE = 8.5;
    /** The tongue's height over his feet (the model's tongue, level, in the open mouth). */
    private static final double TONGUE_HEIGHT = 1.25;
    private static final double BASE_HEALTH = 600;
    private static final double BASE_SPEED = 0.3;
    /** His crawl (blocks a tick) per stage: dormant, awake, blown. */
    private static final double[] CRAWL = {0.075, 0.095, 0.12};
    /** He stops this far (from his middle) short of his target: his head reaches about 5 blocks forward. */
    private static final double KEEP = 5;
    private static final int FROGS = 3;
    private static final double FROG_HEALTH = 60;
    private static final double FROG_HEAL = 0.06;
    /** Volcanic rocks: the volley interval per stage (ticks), the rocks per volley, the burst radius. */
    private static final int[] ROCK_INTERVAL = {50, 30, 25};
    private static final int[] ROCKS = {2, 3, 4};
    private static final double ROCK_RADIUS = 1.8;
    private static final int MAX_POOLS = 14;
    /** The blast clip blows the top off 0.9s in. */
    private static final int BLAST_AT = 18;
    /** The eruption clip throws the frogs as his head goes back (0.9s in). */
    private static final int ERUPT_THROW_AT = 18;

    /** The volcano's stages: above 2/3 health, below 2/3 (after the eruption), below 1/3 (the top blown off). */
    private enum Stage { DORMANT, AWAKE, BLOWN }

    /** A magma block lobbed from the crater: it flies a high arc to {@code to} over {@code flight} ticks. */
    private record Rock(BlockDisplay block, Location from, Location to, int start, int flight, double height, float size,
                        Vector3f axis, @Nullable Consumer<Location> landed) {}

    private record Pool(Location at, double radius, int until) {}

    private final List<Frog> frogs = new ArrayList<>();
    private final List<Rock> rocks = new ArrayList<>();
    private final List<Pool> pools = new ArrayList<>();
    private MagmaCube elder;
    /** Server ticks this fight has moved (move() runs every tick; the fight's clock steps by 5). */
    private int ticks;
    /** He holds still until then: the spawn, the eruption and the blast clips. */
    private int busyUntil = 52;
    @Nullable private Player focus;
    private Location slamTarget;
    private int leapAt = -1;
    private int leapStart = -1;
    private int leapFlight;
    private Location leapFrom;
    private Location leapTo;
    private int nextTongue = TONGUE_INTERVAL / 2;
    @Nullable private Player aimTarget;
    private int lockAt = -1;
    private int lashAt = -1;
    private int tongueShot = -1;
    private double tongueReach;
    @Nullable private Player caught;
    private Location tongueFrom;
    private Vector tongueDir;
    private boolean split;
    private boolean enraged;
    private int blastAt = -1;
    private int eruptAt = -1;
    private int flinchReady;
    private Stage stage = Stage.DORMANT;
    private boolean settled;
    /** The eruption keeps boiling for 2s after it bursts (fight clock). */
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
        // the script moves him (a magma cube's AI only bounces, and turns its body against his facing); unaware mobs
        // still have physics and still hurt players they touch
        org.bukkit.Bukkit.getMobGoals().removeAllGoals(elder);
        elder.setAware(false);
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

    /** The lava's colour: orange in stage one, deep red from the eruption on. */
    private Color lava() {
        return stage == Stage.DORMANT ? ORANGE : DEEP_RED;
    }

    private boolean coiling() {
        return slamTarget != null && leapStart < 0 && leapAt >= 0;
    }

    private boolean flying() {
        return leapStart >= 0;
    }

    private boolean tongueBusy() {
        return lockAt >= 0 || lashAt >= 0 || tongueShot >= 0;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (ticks >= flinchReady && !coiling() && !flying() && !tongueBusy() && ticks >= busyUntil) {
            flinchReady = ticks + 20;
            act("FLINCH", null);
        }
    }

    // ---- every tick: movement, facing and the timed strikes -----------------------------------------------------

    /**
     * Every tick: he crawls after his target and turns to face it; through the leap's coil and the tongue he holds still
     * and faces where he will strike; the leap flies its arc; the rocks fly theirs; the tongue is drawn.
     */
    @Override
    public void move() {
        if (elder == null || !elder.isValid()) {
            return;
        }
        ticks++;
        if (blastAt >= 0 && ticks >= blastAt) {
            blastAt = -1;
            blast();
        }
        if (eruptAt >= 0 && ticks >= eruptAt) {
            eruptAt = -1;
            throwFrogs();
        }
        flyRocks();

        if (flying()) {
            flyLeap();
        } else if (coiling()) {
            hold();
            Abyss.turnToward(elder, slamTarget, 12);
            if (ticks >= leapAt) {
                leap();
            }
        } else if (lockAt >= 0) {                                // tracking: he turns with his target
            hold();
            if (aimTarget != null && aimTarget.isValid()) {
                Abyss.turnToward(elder, aimTarget.getLocation(), 9);
            }
            if (ticks >= lockAt) {
                lock();
            }
        } else if (lashAt >= 0 || tongueShot >= 0) {             // locked on: facing down the lane
            hold();
            face(tongueDir);
            if (lashAt >= 0 && ticks >= lashAt) {
                lashAt = -1;
                lash();
            }
            if (tongueShot >= 0) {
                drawTongue();
            }
        } else if (ticks < busyUntil) {                          // a clip that plays on the spot
            hold();
            if (focus != null && focus.isValid()) {
                Abyss.turnToward(elder, focus.getLocation(), 3);
            }
        } else if (focus != null && focus.isValid()) {
            crawl(focus.getLocation());
        } else {
            hold();
        }
    }

    /** Stands still (keeps falling if he's in the air). */
    private void hold() {
        Vector v = elder.getVelocity();
        elder.setVelocity(new Vector(0, Math.min(0, v.getY()), 0));
    }

    private void face(Vector direction) {
        if (direction == null || direction.clone().setY(0).lengthSquared() < 0.01) {
            return;
        }
        float yaw = (float) Math.toDegrees(Math.atan2(-direction.getX(), direction.getZ()));
        elder.setRotation(yaw, 0);
        elder.setBodyYaw(yaw);
    }

    /**
     * A heavy crawl towards {@code toward}, stopping {@link #KEEP} short: he eases into his speed and turns at most a few
     * degrees a tick, so the 9-block toad never spins; single blocks in his way are stepped up.
     */
    private void crawl(Location toward) {
        Location at = elder.getLocation();
        Abyss.turnToward(elder, toward, 6);
        Vector flat = toward.toVector().subtract(at.toVector()).setY(0);
        double distance = flat.length();
        Vector want = new Vector();
        if (distance > KEEP + 0.5) {
            // he crawls the way he faces, so he turns before he walks off sideways
            double yaw = Math.toRadians(elder.getLocation().getYaw());
            Vector facing = new Vector(-Math.sin(yaw), 0, Math.cos(yaw));
            double ahead = Math.max(0, facing.dot(flat.clone().normalize()));
            want = facing.multiply(CRAWL[stage.ordinal()] * ahead * Math.min(1, (distance - KEEP) * 0.4));
        }
        Vector old = elder.getVelocity();
        Vector velocity = old.clone().setY(0).multiply(0.6).add(want.multiply(0.4)).setY(old.getY());
        if (want.lengthSquared() > 1e-4 && elder.isOnGround()) {
            Block ahead = at.clone().add(want.clone().normalize().multiply(2.2)).getBlock();
            if (!ahead.isPassable() && ahead.getRelative(0, 1, 0).isPassable()) {
                velocity.setY(0.42);
            }
        }
        elder.setVelocity(velocity);
    }

    // ---- every 5 ticks: the fight's decisions --------------------------------------------------------------------

    @Override
    public void tick() {
        if (!elder.isValid()) {
            return;
        }
        if (!settled) {
            settle();
        }
        double health = fight.healthFraction();
        focus = fight.nearestPlayer(elder.getLocation());

        if (!split && health <= 0.66) {
            split = true;
            erupt();
        }
        if (!enraged && health <= 0.33) {
            enraged = true;
            enrage();
        }

        slam();
        tongue();
        volley();
        tendFrogs();
        ground();
        if (mythic()) {
            smoke();
        }

        int puddles = stage == Stage.BLOWN ? PUDDLE_INTERVAL_BLOWN : PUDDLE_INTERVAL;
        if (stage != Stage.DORMANT && every(puddles) && !flying()) {
            pool(elder.getLocation(), 2.5, 200);
            elder.getWorld().playSound(elder.getLocation(), Sound.BLOCK_LAVA_POP, 1.4F, 0.6F);
        }
    }

    /** A pool of lava that hurts anyone standing in it, bubbling while it lasts (at most {@link #MAX_POOLS} at once). */
    private void pool(Location at, double radius, int duration) {
        pools.removeIf(p -> p.until() <= fight.elapsed());
        if (pools.size() >= MAX_POOLS) {
            return;
        }
        Location floor = at.clone();
        floor.setY(Abyss.groundY(at));
        fight.addHazard(floor, radius, duration, lava(), FloorDecals.Zone.FIRE, player -> fight.hit(player, MAGMA, elder));
        pools.add(new Pool(floor, radius, fight.elapsed() + duration));
    }

    /**
     * The ground round him and his pools, every step: the pools bubble and spit, embers pop from the ground at his feet;
     * from the eruption on the ground round him glows, flames lick up off his flanks and lava drips everywhere.
     */
    private void ground() {
        ThreadLocalRandom r = ThreadLocalRandom.current();
        for (Pool p : pools) {
            Location at = p.at().clone().add(r.nextGaussian() * p.radius() * 0.4, 0.1, r.nextGaussian() * p.radius() * 0.4);
            fx(Particle.LAVA, at, 1, 0.1, 0, 0.1, 0);
            if (r.nextBoolean()) {
                fx(Particle.FLAME, at, 2, p.radius() * 0.3, 0.05, p.radius() * 0.3, 0.01);
            }
            if (stage != Stage.DORMANT) {
                fx(Particle.DUST, at, 2, p.radius() * 0.3, 0.05, p.radius() * 0.3, 0);
            }
        }
        if (flying()) {
            return;
        }
        Location feet = elder.getLocation();
        if (stage == Stage.DORMANT) {
            if (r.nextInt(3) == 0) {
                double a = r.nextDouble() * Math.PI * 2;
                fx(Particle.LAVA, feet.clone().add(Math.cos(a) * 3.5, 0.2, Math.sin(a) * 3.5), 1, 0.2, 0, 0.2, 0);
            }
            return;
        }
        for (int i = 0; i < 3; i++) {                             // the scorched ring round him
            double a = r.nextDouble() * Math.PI * 2;
            double d = 3 + r.nextDouble() * 2.5;
            Location at = feet.clone().add(Math.cos(a) * d, 0.15, Math.sin(a) * d);
            fx(Particle.LAVA, at, 1, 0.1, 0, 0.1, 0);
            fx(Particle.FLAME, at, 2, 0.3, 0.05, 0.3, 0.01);
        }
        fx(Particle.FLAME, modelPoint(3.2, 1.5, 0), 3, 0.3, 0.6, 1.2, 0.02);       // flames off his flanks
        fx(Particle.FLAME, modelPoint(-3.2, 1.5, 0), 3, 0.3, 0.6, 1.2, 0.02);
        fx(Particle.DRIPPING_LAVA, modelPoint(0, 3.5, -0.4), 4, 2.5, 1.2, 2.5, 0);
        if (stage == Stage.BLOWN) {
            fx(Particle.LARGE_SMOKE, feet.clone().add(0, 0.3, 0), 3, 3.5, 0.1, 3.5, 0.01);
        }
        if (every(20)) {
            double a = r.nextDouble() * Math.PI * 2;
            FloorDecals.splash(fight, feet.clone().add(Math.cos(a) * 4, 0, Math.sin(a) * 4), 1.4, lava());
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
        return mythic() ? modelPoint(0, stage == Stage.BLOWN ? 5.9 : 6.6, -0.4) : elder.getLocation().add(0, 3, 0);
    }

    /** A particle burst that players see from far away (a 9-block volcano is seen across the arena and beyond). */
    private static void fx(Particle particle, Location at, int count, double dx, double dy, double dz, double speed) {
        if (count <= 0) {
            return;
        }
        Object data = particle == Particle.DUST ? new Particle.DustOptions(Color.fromRGB(190, 25, 10), 1.6F) : null;
        at.getWorld().spawnParticle(particle, at, count, dx, dy, dz, speed, data, true);
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
     * thick dark smoke, fireballs at the rim and lava spray while he coils or erupts; from the eruption on a fountain of
     * flame and lava, and once the top is blown a roaring one. The pipe smokes too.
     */
    private void smoke() {
        ThreadLocalRandom r = ThreadLocalRandom.current();
        Location top = crater();
        boolean boiling = coiling() || fight.elapsed() < eruptingUntil;
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
                fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 3, 0.4, 0.1, 0.4, 0.02);
                fx(Particle.LARGE_SMOKE, top, 2, 0.3, 0.2, 0.3, 0.03);
                spray(Particle.FLAME, top, 4, 0.05, 0.4);
                fx(Particle.LAVA, top, 2, 0.4, 0.1, 0.4, 0);
                fx(Particle.DUST, top, 4, 0.5, 0.4, 0.5, 0);
                fx(Particle.ASH, cone, 12, 3.5, 2.5, 3.5, 0);
            }
            case BLOWN -> {
                fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top.clone().add(0, 1.5, 0), 4, 0.6, 0.2, 0.6, 0.025);
                fx(Particle.LARGE_SMOKE, top.clone().add(0, 1, 0), 3, 0.5, 0.3, 0.5, 0.04);
                spray(Particle.FLAME, top, 8, 0.06, 0.55);              // the fountain welling up out of the crater
                fx(Particle.LAVA, top, 4, 0.6, 0.2, 0.6, 0);
                fx(Particle.DRIPPING_LAVA, top, 3, 0.9, 0.1, 0.9, 0);
                fx(Particle.DUST, top, 6, 0.7, 0.6, 0.7, 0);
                fx(Particle.ASH, cone, 14, 3.5, 2.5, 3.5, 0);
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

    // ---- the leap -------------------------------------------------------------------------------------------------

    private void slam() {
        if (every(SLAM_INTERVAL) && !tongueBusy() && !flying() && ticks >= busyUntil) {
            Player target = fight.randomPlayer();
            if (target != null) {
                slamTarget = target.getLocation();
                slamTarget.setY(Abyss.groundY(slamTarget));
                leapAt = ticks + SLAM_WARNING;
                fight.telegraph(slamTarget, 3.5, SLAM_WARNING + 30, lava(), FloorDecals.Mark.SLAM);
                elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_FROG_AMBIENT, 2F, 0.5F);
                act("COIL", target);                          // he sinks, facing the ring, and the volcano boils (1.5s)
            }
        }
    }

    /** Off the ground in a high arc that comes down on the marked spot. */
    private void leap() {
        leapFrom = elder.getLocation();
        leapTo = slamTarget.clone();
        double distance = leapFrom.toVector().setY(0).distance(leapTo.toVector().setY(0));
        leapFlight = 16 + (int) Math.min(12, distance * 0.7);
        leapStart = ticks;
        leapAt = -1;
        elder.setGravity(false);
        act("LEAP", null);
    }

    private void flyLeap() {
        double t = Math.min(1, (ticks - leapStart + 1) / (double) leapFlight);
        double distance = leapFrom.toVector().setY(0).distance(leapTo.toVector().setY(0));
        double height = 4 + distance * 0.25;
        Vector want = leapFrom.toVector().multiply(1 - t).add(leapTo.toVector().multiply(t)).add(new Vector(0, 4 * height * t * (1 - t), 0));
        elder.setVelocity(want.subtract(elder.getLocation().toVector()));
        face(leapTo.toVector().subtract(leapFrom.toVector()));
        if (t >= 1) {
            leapStart = -1;
            slamTarget = null;
            elder.setGravity(true);
            elder.setVelocity(new Vector(0, -0.3, 0));
            act("LAND", null);
            shockwave();
        }
    }

    private void shockwave() {
        Location at = elder.getLocation();
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 1.2F, 0.6F);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 80, 2.5, 0.2, 2.5, Material.BASALT.createBlockData());
        at.getWorld().spawnParticle(Particle.BLOCK, at, 40, 2.5, 0.2, 2.5, Material.MAGMA_BLOCK.createBlockData());
        fx(Particle.LARGE_SMOKE, at, 30, 2.5, 0.3, 2.5, 0.02);
        fx(Particle.LAVA, at, 30, 3, 0.2, 3, 0);
        spray(Particle.FLAME, at, 25, 0.25, 0.25);
        FloorDecals.wave(fight, at, 0.5, 4, 8, lava());
        FloorDecals.splash(fight, at, 4, lava());
        AirEffects.burst(fight, at.clone().add(0, 0.8, 0), AirEffects.Burst.IMPACT, lava(), 4F);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 16 && player.isOnGround()) {
                fight.hit(player, SHOCKWAVE, elder);
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.9).setY(0.4));
                }
            }
        }
        ThreadLocalRandom r = ThreadLocalRandom.current();       // the landing splashes lava round him
        int splashes = stage == Stage.DORMANT ? 2 : 4;
        for (int i = 0; i < splashes; i++) {
            double a = Math.PI * 2 * i / splashes + r.nextDouble();
            pool(at.clone().add(Math.cos(a) * 5, 0, Math.sin(a) * 5), 1.4, 100);
        }
    }

    // ---- the tongue -----------------------------------------------------------------------------------------------

    private void tongue() {
        int now = fight.elapsed();
        if (tongueBusy() || now < nextTongue || flying() || coiling() || ticks < busyUntil) {
            return;
        }
        nextTongue = now + (stage == Stage.DORMANT ? TONGUE_INTERVAL : TONGUE_INTERVAL_AWAKE);
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
        aimTarget = inReach.get(ThreadLocalRandom.current().nextInt(inReach.size()));
        lockAt = ticks + TONGUE_AIM;
        elder.getWorld().playSound(from, Sound.ENTITY_FROG_AMBIENT, 2F, 0.5F);
        act("TONGUE", aimTarget);                      // the glare while he tracks; the mouth opens at the lock
    }

    /** The lock: the lane's direction is fixed now (the lash uses this same geometry); the lane shows, the mouth hangs open. */
    private void lock() {
        lockAt = -1;
        Location from = elder.getLocation();
        Vector dir = aimTarget != null && aimTarget.isValid()
            ? aimTarget.getLocation().toVector().subtract(from.toVector()).setY(0) : null;
        if (dir == null || dir.lengthSquared() < 0.01) {
            double yaw = Math.toRadians(from.getYaw());
            dir = new Vector(-Math.sin(yaw), 0, Math.cos(yaw));
        }
        tongueFrom = from.clone();
        tongueDir = dir.normalize();
        lashAt = ticks + TONGUE_LOCK;
        FloorDecals.lane(fight, tongueFrom, tongueDir, TONGUE_RANGE, 2 * (TONGUE_REACH_SIDE - 0.3), TONGUE_LOCK + 4, lava());
        elder.getWorld().playSound(from, Sound.BLOCK_LAVA_AMBIENT, 1.6F, 0.8F);
    }

    /** The tongue shoots straight down the locked lane: the first player in it is hit and pulled to the Elder's mouth. */
    private void lash() {
        Location mouth = elder.getLocation();
        caught = null;
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
        tongueReach = caught == null ? TONGUE_RANGE : nearest;
        tongueShot = ticks;
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

    /**
     * The tongue beyond the model's own, every tick: it shoots out in 3 ticks, stays out (its tip on the caught player as
     * they are reeled in), then snaps back - one straight line at mouth height, a glowing tip at its end.
     */
    private void drawTongue() {
        int age = ticks - tongueShot;
        double out;
        if (age < 3) {
            out = (age + 1) / 3.0;
        } else if (age < TONGUE_OUT) {
            out = 1;
        } else {
            out = 1 - (age - TONGUE_OUT + 1) / (double) TONGUE_BACK;
        }
        if (out <= 0) {
            tongueShot = -1;
            caught = null;
            return;
        }
        double reach = tongueReach;
        if (caught != null && caught.isValid() && age >= 3) {
            Vector rel = caught.getLocation().toVector().subtract(tongueFrom.toVector());
            reach = Math.max(MODEL_TONGUE, Math.min(reach, rel.getX() * tongueDir.getX() + rel.getZ() * tongueDir.getZ()));
        }
        double start = mythic() ? MODEL_TONGUE - 0.5 : 1.5;
        double end = start + (reach - start) * out;
        Particle.DustOptions pink = new Particle.DustOptions(TONGUE_PINK, 1.5F);
        for (double t = start; t <= end; t += 0.25) {
            Location p = tongueFrom.clone().add(tongueDir.clone().multiply(t)).add(0, TONGUE_HEIGHT, 0);
            p.getWorld().spawnParticle(Particle.DUST, p, 1, 0.02, 0.02, 0.02, 0, pink, true);
        }
        Location tip = tongueFrom.clone().add(tongueDir.clone().multiply(end)).add(0, TONGUE_HEIGHT, 0);
        tip.getWorld().spawnParticle(Particle.DUST, tip, 4, 0.12, 0.12, 0.12, 0, new Particle.DustOptions(TONGUE_TIP, 2.2F), true);
        if (age < 3) {
            fx(Particle.FLAME, tip, 2, 0.1, 0.1, 0.1, 0.02);
        }
    }

    // ---- volcanic rocks -------------------------------------------------------------------------------------------

    /** Every volley interval: magma blocks lobbed at the fighters (one at each, the rest round them). */
    private void volley() {
        int i = stage.ordinal();
        if (fight.elapsed() < 60 || !every(ROCK_INTERVAL[i]) || fight.players().isEmpty()) {
            return;
        }
        ThreadLocalRandom r = ThreadLocalRandom.current();
        List<Player> players = fight.players();
        for (int n = 0; n < ROCKS[i]; n++) {
            Player target = players.get(n < players.size() ? n : r.nextInt(players.size()));
            Location to = target.getLocation();
            if (n >= players.size()) {                              // the extra rocks land round them
                double a = r.nextDouble() * Math.PI * 2;
                double d = 2.5 + r.nextDouble() * 3;
                to.add(Math.cos(a) * d, 0, Math.sin(a) * d);
            }
            to.setY(Abyss.groundY(to));
            if (to.toVector().setY(0).distance(fight.center().toVector().setY(0)) > fight.radius()) {
                continue;
            }
            int flight = 26 + r.nextInt(10);
            throwRock(to, 0.9F, flight, at -> rockLands(at));
        }
        Location top = crater();
        fx(Particle.LAVA, top, 10, 0.5, 0.3, 0.5, 0);
        spray(Particle.FLAME, top, 10, 0.12, 0.5);
        top.getWorld().playSound(top, Sound.ENTITY_BLAZE_SHOOT, 1.6F, 0.5F);
    }

    private void throwRock(Location to, float size, int flight, @Nullable Consumer<Location> landed) {
        Location from = crater();
        ThreadLocalRandom r = ThreadLocalRandom.current();
        Vector3f axis = new Vector3f((float) r.nextGaussian(), (float) r.nextGaussian(), (float) r.nextGaussian());
        if (axis.lengthSquared() < 1e-4) {
            axis.set(1, 0, 0);
        }
        axis.normalize();
        BlockDisplay block = fight.spawnExtra(BlockDisplay.class, from, d -> {
            d.setBlock(Material.MAGMA_BLOCK.createBlockData());
            d.setBrightness(new Display.Brightness(15, 15));
            d.setTeleportDuration(1);
            d.setTransformation(spin(size, new Quaternionf()));
        });
        double distance = from.toVector().setY(0).distance(to.toVector().setY(0));
        if (landed != null) {
            fight.telegraph(to, ROCK_RADIUS, flight, lava());
        }
        rocks.add(new Rock(block, from, to, ticks, flight, 3 + distance * 0.25, size, axis, landed));
    }

    private static Transformation spin(float size, Quaternionf rotation) {
        Vector3f corner = rotation.transform(new Vector3f(-size / 2, -size / 2, -size / 2));
        return new Transformation(corner, rotation, new Vector3f(size, size, size), new Quaternionf());
    }

    /** Every tick: each rock along its arc, tumbling and trailing fire; on landing it bursts. */
    private void flyRocks() {
        rocks.removeIf(rock -> {
            double t = Math.min(1, (ticks - rock.start()) / (double) rock.flight());
            Vector p = rock.from().toVector().multiply(1 - t).add(rock.to().toVector().multiply(t))
                .add(new Vector(0, 4 * rock.height() * t * (1 - t), 0));
            Location at = p.toLocation(rock.to().getWorld());
            if (rock.block().isValid()) {
                rock.block().teleport(at);
                if ((ticks - rock.start()) % 2 == 0) {
                    float angle = (ticks - rock.start()) * 0.35F;
                    rock.block().setInterpolationDelay(0);
                    rock.block().setInterpolationDuration(2);
                    rock.block().setTransformation(spin(rock.size(), new Quaternionf().rotateAxis(angle, rock.axis())));
                }
            }
            fx(Particle.FLAME, at, 2, 0.15, 0.15, 0.15, 0.01);
            fx(Particle.LARGE_SMOKE, at, 1, 0.1, 0.1, 0.1, 0.01);
            if (stage != Stage.DORMANT) {
                fx(Particle.DUST, at, 2, 0.2, 0.2, 0.2, 0);
            }
            if (t < 1) {
                return false;
            }
            rock.block().remove();
            if (rock.landed() != null) {
                rock.landed().accept(rock.to());
            }
            return true;
        });
    }

    /** A rock bursts: it hurts anyone in the marked ring and leaves a pool of lava. */
    private void rockLands(Location at) {
        fx(Particle.EXPLOSION, at.clone().add(0, 0.5, 0), 1, 0, 0, 0, 0);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 30, 0.8, 0.3, 0.8, Material.MAGMA_BLOCK.createBlockData());
        fx(Particle.LAVA, at, 8, 0.6, 0.2, 0.6, 0);
        spray(Particle.FLAME, at, 8, 0.15, 0.25);
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 0.8F, 1.1F);
        for (Player player : fight.players()) {
            Location p = player.getLocation();
            double dx = p.getX() - at.getX();
            double dz = p.getZ() - at.getZ();
            if (dx * dx + dz * dz <= ROCK_RADIUS * ROCK_RADIUS && Math.abs(p.getY() - at.getY()) < 2.5) {
                fight.hit(player, ROCK, elder);
            }
        }
        FloorDecals.splash(fight, at, ROCK_RADIUS, lava());
        pool(at, stage == Stage.DORMANT ? 1.2 : 1.6, stage == Stage.DORMANT ? 80 : 120);
    }

    // ---- the eruption and the frogs -------------------------------------------------------------------------------

    /** At 66%: the volcano erupts (the lava turns deep red) and throws 3 Ash Frogs to the arena's edge. */
    private void erupt() {
        stage = Stage.AWAKE;
        act("ERUPT", null);
        Location top = crater();
        eruptingUntil = fight.elapsed() + 40;
        busyUntil = Math.max(busyUntil, ticks + 44);
        eruptAt = ticks + ERUPT_THROW_AT;
        fx(Particle.EXPLOSION_EMITTER, top, 1, 0, 0, 0, 0);
        fx(Particle.CAMPFIRE_SIGNAL_SMOKE, top, 20, 0.8, 0.4, 0.8, 0.05);
        fx(Particle.LARGE_SMOKE, top, 50, 0.8, 1.0, 0.8, 0.08);
        fx(Particle.LAVA, top, 40, 0.6, 0.4, 0.6, 0);
        fx(Particle.DUST, top, 40, 1.0, 1.0, 1.0, 0);
        spray(Particle.FLAME, top, 30, 0.15, 0.6);
        top.getWorld().playSound(top, Sound.ENTITY_GENERIC_EXPLODE, 2F, 0.5F);
        fight.broadcast("&4The Elder of Ash erupts! &fHis lava runs deep red - and Ash Frogs hop back to heal him. Stop them!");
    }

    /** The frogs fly out of the crater in big magma clods that burst at the arena's edge. */
    private void throwFrogs() {
        Location top = crater();
        fx(Particle.EXPLOSION_EMITTER, top.clone().add(0, 0.5, 0), 1, 0, 0, 0, 0);
        top.getWorld().playSound(top, Sound.ENTITY_GENERIC_EXPLODE, 1.6F, 0.7F);
        double offset = ThreadLocalRandom.current().nextDouble() * Math.PI;
        for (int i = 0; i < FROGS; i++) {
            double angle = offset + Math.PI * 2 * i / FROGS;
            Location at = fight.center().add(Math.cos(angle) * (fight.radius() - 3), 0, Math.sin(angle) * (fight.radius() - 3));
            at.setY(Abyss.groundY(at));
            throwRock(at, 1.4F, 34, this::hatchFrog);
        }
    }

    private void hatchFrog(Location at) {
        fx(Particle.EXPLOSION, at.clone().add(0, 0.5, 0), 1, 0, 0, 0, 0);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 30, 0.8, 0.3, 0.8, Material.MAGMA_BLOCK.createBlockData());
        fx(Particle.LAVA, at, 12, 0.5, 0.3, 0.5, 0);
        at.getWorld().playSound(at, Sound.ENTITY_FROG_LONG_JUMP, 2F, 0.5F);
        Frog frog = fight.spawnAdd(Frog.class, at.clone().add(0, 0.2, 0), f -> {
            f.setVariant(Frog.Variant.WARM);
            f.setCustomName(ChatColor.GOLD + "Ash Frog");
            BossFight.setAttribute(f, Attribute.SCALE, 3);
            BossFight.setAttribute(f, Attribute.MAX_HEALTH, FROG_HEALTH);
            BossFight.setAttribute(f, Attribute.ARMOR, 6);
            BossFight.setAttribute(f, Attribute.KNOCKBACK_RESISTANCE, 1);
            f.setHealth(FROG_HEALTH);
        });
        if (frog != null) {
            frogs.add(frog);
        }
    }

    /** The frogs hop back to the altar; each one that reaches it heals the Elder. */
    private void tendFrogs() {
        Location altar = fight.center();
        frogs.removeIf(frog -> {
            if (frog.isDead() || !frog.isValid()) {
                return true;
            }
            Vector toAltar = altar.toVector().subtract(frog.getLocation().toVector()).setY(0);
            if (toAltar.lengthSquared() < 9) {
                fight.healBoss(elder, FROG_HEAL);
                fx(Particle.LAVA, frog.getLocation(), 20, 0.6, 0.6, 0.6, 0);
                frog.getWorld().playSound(frog.getLocation(), Sound.BLOCK_LAVA_EXTINGUISH, 1.5F, 0.8F);
                fight.broadcast("&6An Ash Frog reaches the altar and the Elder drinks it in.");
                frog.remove();
                return true;
            }
            if (!frog.getPathfinder().moveTo(altar, 1.2) && frog.isOnGround()) {
                frog.setVelocity(toAltar.normalize().multiply(0.35).setY(0.35));
            }
            if (every(10)) {
                fx(Particle.FLAME, frog.getLocation().add(0, 0.6, 0), 2, 0.4, 0.3, 0.4, 0.01);
            }
            return false;
        });
    }

    // ---- the blast ------------------------------------------------------------------------------------------------

    /** At 33%: the volcano's top blows off (the blast lands 0.9s into the clip); he speeds up and sheds lava pools. */
    private void enrage() {
        fight.broadcast("&4The Elder of Ash's peak blows apart! &fLava pours from him now.");
        busyUntil = Math.max(busyUntil, ticks + 40);
        if (mythic()) {
            act("BLOW", null);
            blastAt = ticks + BLAST_AT;
        } else {
            blast();
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
        fx(Particle.DUST, top, 50, 1.2, 1.2, 1.2, 0);
        spray(Particle.FLAME, top, 40, 0.2, 0.7);
        top.getWorld().spawnParticle(Particle.BLOCK, top, 60, 1.2, 0.6, 1.2, 0.2, Material.BASALT.createBlockData(), true);
        top.getWorld().playSound(top, Sound.ENTITY_GENERIC_EXPLODE, 2.5F, 0.4F);
        ThreadLocalRandom r = ThreadLocalRandom.current();      // the cap's chunks rain down round him
        for (int i = 0; i < 6; i++) {
            double a = r.nextDouble() * Math.PI * 2;
            double d = 6 + r.nextDouble() * 6;
            Location to = elder.getLocation().add(Math.cos(a) * d, 0, Math.sin(a) * d);
            to.setY(Abyss.groundY(to));
            throwRock(to, 1.1F, 24 + r.nextInt(12), this::rockLands);
        }
    }
}
