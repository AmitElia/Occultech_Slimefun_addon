package io.github.amitelia.occultech.boss.tier2;

import java.util.ArrayList;
import java.util.List;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;

/**
 * Shared tier-2 mechanics: land "gliding" for sea creatures (they hover over the ground instead of flopping) and
 * dodgeable charged beams.
 */
public final class Abyss {

    private Abyss() {}

    /**
     * Turns a mob into a puppet the boss script moves: no goals (so vanilla AI never steers it, and guardians never
     * flop), no gravity, but still normal physics so velocity carries it.
     */
    public static void puppet(org.bukkit.entity.Mob mob) {
        org.bukkit.Bukkit.getMobGoals().removeAllGoals(mob);
        // unaware: no goals, look or body-turn controls (they would spin the body against our facing), physics still on
        mob.setAware(false);
        mob.setGravity(false);
        mob.setTarget(null);
    }

    /**
     * Moves a walking creature (gravity on) toward {@code toward}: sets the horizontal velocity and keeps the vertical one,
     * so it still falls and lands. Stops {@code keepDistance} short. Call every tick.
     */
    public static void walk(LivingEntity mob, Location toward, double speed, double keepDistance) {
        Location at = mob.getLocation();
        Vector flat = toward.toVector().subtract(at.toVector()).setY(0);
        double distance = flat.length();
        Vector velocity = new Vector();
        if (distance > keepDistance + 0.3) {
            velocity = flat.normalize().multiply(Math.min(speed, (distance - keepDistance) * 0.25));
        } else if (distance < keepDistance - 1.5 && distance > 0.01) {
            velocity = flat.normalize().multiply(-speed * 0.5);
        }
        velocity.setY(mob.getVelocity().getY());
        // step up single blocks in the way
        Block ahead = at.clone().add(velocity.clone().setY(0).normalize().multiply(0.9)).getBlock();
        if (velocity.lengthSquared() > 0.001 && !ahead.isPassable() && ahead.getRelative(0, 1, 0).isPassable() && mob.isOnGround()) {
            velocity.setY(0.42);
        }
        mob.setVelocity(velocity);
        face(mob, toward);
    }

    /**
     * Moves a gravity-less, AI-less creature toward {@code toward}, hovering {@code hover} blocks above the ground and
     * stopping {@code keepDistance} short of it. Called once per boss step; the velocity carries it between steps.
     */
    public static void glide(LivingEntity mob, Location toward, double speed, double hover, double keepDistance) {
        Location at = mob.getLocation();
        Vector flat = toward.toVector().subtract(at.toVector()).setY(0);
        double distance = flat.length();
        Vector velocity = new Vector();
        if (distance > keepDistance + 0.3) {
            velocity = flat.normalize().multiply(Math.min(speed, (distance - keepDistance) * 0.25));
        } else if (distance < keepDistance - 1.5 && distance > 0.01) {
            velocity = flat.normalize().multiply(-speed * 0.5);
        }
        double wantY = groundY(at) + hover;
        velocity.setY(Math.max(-0.4, Math.min(0.4, (wantY - at.getY()) * 0.3)));
        mob.setVelocity(velocity);
        face(mob, toward);
    }

    /** Turns a creature (body and head) to look at a point. */
    /**
     * Like {@link #glide} but calm, for big slow creatures (Session R2): its speed eases in and out instead of snapping,
     * it turns at most {@code maxTurn} degrees a tick, and it holds still anywhere from {@code keepDistance - 4} to
     * {@code keepDistance + 1} - no flipping between closing in and backing off as its target moves around it.
     */
    public static void glideSmooth(LivingEntity mob, Location toward, double speed, double hover, double keepDistance, float maxTurn) {
        Location at = mob.getLocation();
        Vector flat = toward.toVector().subtract(at.toVector()).setY(0);
        double distance = flat.length();
        Vector want = new Vector();
        if (distance > keepDistance + 1) {
            want = flat.normalize().multiply(Math.min(speed, (distance - keepDistance) * 0.2));
        } else if (distance < keepDistance - 4 && distance > 0.01) {
            want = flat.normalize().multiply(-speed * 0.5);
        }
        Vector old = mob.getVelocity();
        Vector velocity = old.clone().setY(0).multiply(0.8).add(want.multiply(0.2));
        double wantY = groundY(at) + hover;
        velocity.setY(Math.max(-0.3, Math.min(0.3, (wantY - at.getY()) * 0.2)));
        mob.setVelocity(velocity);
        turnToward(mob, toward, maxTurn);
    }

    /** Turns {@code mob} toward a point, at most {@code maxTurn} degrees this tick. */
    public static void turnToward(LivingEntity mob, Location toward, float maxTurn) {
        Vector look = toward.toVector().subtract(mob.getEyeLocation().toVector());
        if (look.lengthSquared() < 0.01) {
            return;
        }
        Location facing = mob.getLocation().setDirection(look);
        float yaw = mob.getLocation().getYaw();
        float delta = ((facing.getYaw() - yaw) % 360 + 540) % 360 - 180;
        float turned = yaw + Math.max(-maxTurn, Math.min(maxTurn, delta));
        mob.setRotation(turned, facing.getPitch());
        mob.setBodyYaw(turned);
    }

    public static void face(LivingEntity mob, Location toward) {
        Vector look = toward.toVector().subtract(mob.getEyeLocation().toVector());
        if (look.lengthSquared() < 0.01) {
            return;
        }
        Location facing = mob.getLocation().setDirection(look);
        mob.setRotation(facing.getYaw(), facing.getPitch());
        mob.setBodyYaw(facing.getYaw());
    }

    /** Top of the first solid block at or below {@code at} (up to 8 down), or the location's own height. */
    public static double groundY(Location at) {
        Block block = at.getBlock();
        for (int i = 0; i < 8; i++) {
            if (!block.isPassable()) {
                return block.getY() + 1;
            }
            block = block.getRelative(0, -1, 0);
        }
        return at.getY();
    }

    public static void line(Location from, Location to, Particle.DustOptions dust, double step) {
        Vector direction = to.toVector().subtract(from.toVector());
        double length = direction.length();
        if (length < 0.01) {
            return;
        }
        direction.normalize().multiply(step);
        Location point = from.clone();
        for (double d = 0; d < length; d += step) {
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0, 0, 0, 0, dust);
            point.add(direction);
        }
    }

    /** Players within {@code width} of the segment from {@code from} along {@code direction} for {@code length}. */
    public static List<Player> alongBeam(List<Player> players, Location from, Vector direction, double length, double width) {
        List<Player> hit = new ArrayList<>();
        Vector origin = from.toVector();
        Vector unit = direction.clone().normalize();
        for (Player player : players) {
            for (double h : new double[] { 0.3, 1.0, 1.6 }) {
                Vector point = player.getLocation().toVector().add(new Vector(0, h, 0)).subtract(origin);
                double along = point.dot(unit);
                if (along >= 0 && along <= length && point.clone().subtract(unit.clone().multiply(along)).length() <= width) {
                    hit.add(player);
                    break;
                }
            }
        }
        return hit;
    }

    /**
     * A beam that tracks a player while it charges and turns white for its last 0.75s. Its aim follows the player until
     * the step before it fires (0.25s), so standing still or walking gets you hit and a sideways sprint dodges it.
     * Draw it every step with {@link #step}; it fires once.
     */
    public static final class Beam {
        /** Ticks before firing the beam turns white (warning). */
        private static final int WARN_BEFORE = 15;
        /** Ticks before firing the aim stops following (one boss step). */
        private static final int LOCK_BEFORE = 5;
        private static final double WIDTH = 1.3;

        private final LivingEntity source;
        private final Player target;
        private final int fireAt;
        private final io.github.amitelia.occultech.boss.Mechanic mechanic;
        private final Color color;
        private Vector aim;
        private boolean done;
        /** The beam drawn in the air (Session O5), with the resource pack; else particles. */
        @Nullable private io.github.amitelia.occultech.boss.AirEffects.Streak fx;
        private final int startedAt;
        private boolean warned;
        @Nullable private final java.util.function.Supplier<Location> origin;

        public Beam(LivingEntity source, Player target, int now, int chargeTicks, io.github.amitelia.occultech.boss.Mechanic mechanic, Color color) {
            this(source, null, target, now, chargeTicks, mechanic, color);
        }

        /**
         * A beam fired from {@code origin} (e.g. a pylon's tip) for {@code source}; it fizzles if {@code origin} gives null
         * (the pylon broke). Null origin: from the source's eyes.
         */
        public Beam(LivingEntity source, @Nullable java.util.function.Supplier<Location> origin, Player target, int now, int chargeTicks,
            io.github.amitelia.occultech.boss.Mechanic mechanic, Color color) {
            this.origin = origin;
            this.source = source;
            this.target = target;
            this.fireAt = now + chargeTicks;
            this.mechanic = mechanic;
            this.color = color;
            this.startedAt = now;
            source.getWorld().playSound(source.getLocation(), Sound.ENTITY_GUARDIAN_ATTACK, 1.5F, 0.6F);
        }

        public boolean done() {
            return done;
        }

        /** Draws the charging beam; fires when due. Returns the players hit on the firing step, else an empty list. */
        public List<Player> step(BossFight fight, int now) {
            if (done) {
                return List.of();
            }
            if (!source.isValid() || !target.isValid() || target.getWorld() != source.getWorld()) {
                done = true;
                if (fx != null) {
                    fx.snap();
                }
                return List.of();
            }
            Location eye = origin == null ? source.getEyeLocation() : origin.get();
            if (eye == null) {
                done = true;
                if (fx != null) {
                    fx.snap();
                }
                return List.of();
            }
            if (now <= fireAt - LOCK_BEFORE || aim == null) {
                aim = target.getLocation().add(0, 1, 0).toVector().subtract(eye.toVector());
            }
            Location end = eye.clone().add(aim.clone().normalize().multiply(Math.max(aim.length(), 4) + 4));
            if (now < fireAt) {
                boolean warning = now >= fireAt - WARN_BEFORE;
                if (io.github.amitelia.occultech.boss.AirEffects.enabled()) {
                    // a beam that thickens as it charges, turning white for its warning
                    float charge = (now - startedAt) / (float) Math.max(1, fireAt - startedAt);
                    if (fx == null) {
                        fx = io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "air_beam", eye, end, color, 0.25F);
                    } else {
                        fx.aim(eye, end, 0.25F + 0.45F * charge, io.github.amitelia.occultech.boss.BossService.STEP);
                    }
                    if (warning && !warned) {
                        warned = true;
                        fx.tint(Color.fromRGB(235, 245, 255));
                    }
                } else {
                    line(eye, end, new Particle.DustOptions(warning ? Color.WHITE : color, warning ? 1.2F : 0.6F), 0.6);
                }
                return List.of();
            }
            done = true;
            if (fx != null) {
                fx.fire(eye, end);
            } else {
                line(eye, end, new Particle.DustOptions(color, 2F), 0.3);
            }
            eye.getWorld().playSound(eye, Sound.ENTITY_ELDER_GUARDIAN_HURT, 1.5F, 0.6F);
            List<Player> hit = alongBeam(fight.players(), eye, aim, eye.distance(end), WIDTH);
            for (Player player : hit) {
                fight.hit(player, mechanic, source);
                io.github.amitelia.occultech.boss.AirEffects.burst(fight, player.getLocation().add(0, 1.1, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.CRACKLE, color, 1.8F);
            }
            return hit;
        }

        @Nullable
        Player target() {
            return target;
        }
    }
}
