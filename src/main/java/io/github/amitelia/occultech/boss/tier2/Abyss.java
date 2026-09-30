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
final class Abyss {

    private Abyss() {}

    /**
     * Turns a mob into a puppet the boss script moves: no goals (so vanilla AI never steers it, and guardians never
     * flop), no gravity, but still normal physics so velocity carries it.
     */
    static void puppet(org.bukkit.entity.Mob mob) {
        org.bukkit.Bukkit.getMobGoals().removeAllGoals(mob);
        mob.setGravity(false);
        mob.setTarget(null);
    }

    /**
     * Moves a gravity-less, AI-less creature toward {@code toward}, hovering {@code hover} blocks above the ground and
     * stopping {@code keepDistance} short of it. Called once per boss step; the velocity carries it between steps.
     */
    static void glide(LivingEntity mob, Location toward, double speed, double hover, double keepDistance) {
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
    static void face(LivingEntity mob, Location toward) {
        Vector look = toward.toVector().subtract(mob.getEyeLocation().toVector());
        if (look.lengthSquared() < 0.01) {
            return;
        }
        Location facing = mob.getLocation().setDirection(look);
        mob.setRotation(facing.getYaw(), facing.getPitch());
    }

    /** Top of the first solid block at or below {@code at} (up to 8 down), or the location's own height. */
    static double groundY(Location at) {
        Block block = at.getBlock();
        for (int i = 0; i < 8; i++) {
            if (!block.isPassable()) {
                return block.getY() + 1;
            }
            block = block.getRelative(0, -1, 0);
        }
        return at.getY();
    }

    static void line(Location from, Location to, Particle.DustOptions dust, double step) {
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
    static List<Player> alongBeam(List<Player> players, Location from, Vector direction, double length, double width) {
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
     * Magic damage from a fight creature: ignores armor like the vanilla guardian laser (Protection still counts).
     * Used for beams, whose raw numbers would otherwise vanish into max-enchanted netherite.
     */
    static void magic(Player player, double amount, LivingEntity source) {
        player.damage(amount, org.bukkit.damage.DamageSource.builder(org.bukkit.damage.DamageType.INDIRECT_MAGIC)
            .withCausingEntity(source).withDirectEntity(source).build());
    }

    /**
     * A beam that tracks a player while it charges and turns white for its last 0.75s. Its aim follows the player until
     * the step before it fires (0.25s), so standing still or walking gets you hit and a sideways sprint dodges it.
     * Draw it every step with {@link #step}; it fires once.
     */
    static final class Beam {
        /** Ticks before firing the beam turns white (warning). */
        private static final int WARN_BEFORE = 15;
        /** Ticks before firing the aim stops following (one boss step). */
        private static final int LOCK_BEFORE = 5;
        private static final double WIDTH = 1.3;

        private final LivingEntity source;
        private final Player target;
        private final int fireAt;
        private final double damage;
        private final Color color;
        private Vector aim;
        private boolean done;

        Beam(LivingEntity source, Player target, int now, int chargeTicks, double damage, Color color) {
            this.source = source;
            this.target = target;
            this.fireAt = now + chargeTicks;
            this.damage = damage;
            this.color = color;
            source.getWorld().playSound(source.getLocation(), Sound.ENTITY_GUARDIAN_ATTACK, 1.5F, 0.6F);
        }

        boolean done() {
            return done;
        }

        /** Draws the charging beam; fires when due. Returns the players hit on the firing step, else an empty list. */
        List<Player> step(BossFight fight, int now) {
            if (done) {
                return List.of();
            }
            if (!source.isValid() || !target.isValid() || target.getWorld() != source.getWorld()) {
                done = true;
                return List.of();
            }
            Location eye = source.getEyeLocation();
            if (now <= fireAt - LOCK_BEFORE || aim == null) {
                aim = target.getLocation().add(0, 1, 0).toVector().subtract(eye.toVector());
            }
            Location end = eye.clone().add(aim.clone().normalize().multiply(Math.max(aim.length(), 4) + 4));
            if (now < fireAt) {
                boolean warning = now >= fireAt - WARN_BEFORE;
                line(eye, end, new Particle.DustOptions(warning ? Color.WHITE : color, warning ? 1.2F : 0.6F), 0.6);
                return List.of();
            }
            done = true;
            line(eye, end, new Particle.DustOptions(color, 2F), 0.3);
            eye.getWorld().playSound(eye, Sound.ENTITY_ELDER_GUARDIAN_HURT, 1.5F, 0.6F);
            List<Player> hit = alongBeam(fight.players(), eye, aim, eye.distance(end), WIDTH);
            for (Player player : hit) {
                magic(player, damage, source);
            }
            return hit;
        }

        @Nullable
        Player target() {
            return target;
        }
    }
}
