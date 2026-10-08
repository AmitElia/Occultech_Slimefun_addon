package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;

import javax.annotation.Nonnull;

/**
 * Staff Raid numbers (docs/staff-raid.md). The engine's group scaling stops at 5 players (x2.27), far too low for 25, so
 * the raid has its own curve: health x {@code players^exponent} for the group a boss faces. Pure Java, unit tested.
 *
 * @param playersPerTarget Act 1 aims for groups this size
 * @param maxTargets       Act 1 never has more targets than this
 * @param exponent         health grows with group size to this power (just under linear: crowds get in each other's way)
 */
public record RaidScaling(double playersPerTarget, int maxTargets, double exponent) {

    public static final RaidScaling DEFAULT = new RaidScaling(2.5, 10, 0.9);
    /** Most health a body may have: the health attribute stops at 1024. */
    public static final double MAX_BODY_HEALTH = 1000;
    public static final int MIN_TARGETS = 2;

    public RaidScaling {
        playersPerTarget = Math.max(0.5, playersPerTarget);
        maxTargets = Math.max(MIN_TARGETS, maxTargets);
        exponent = Math.max(0.1, Math.min(1, exponent));
    }

    /** How many staff are on the floor at once in Act 1 for {@code players}. */
    public int targets(int players) {
        return (int) Math.max(MIN_TARGETS, Math.min(maxTargets, Math.round(players / playersPerTarget)));
    }

    /** Health factor for a group of {@code players} (at least 1). */
    public double factor(double players) {
        return Math.pow(Math.max(1, players), exponent);
    }

    /**
     * A body's real health and the share of each hit it takes: up to {@link #MAX_BODY_HEALTH} the body simply has
     * {@code effective} health; beyond it, it takes a share of each hit instead (the bosses' usual way past the cap).
     */
    @Nonnull
    public static Body body(double effective) {
        double health = Math.max(1, Math.min(MAX_BODY_HEALTH, effective));
        return new Body(health, health / Math.max(1, effective));
    }

    /** A body's health attribute and the share of incoming damage it takes. */
    public record Body(double maxHealth, double damageTaken) {}

    /**
     * Where Act 1's {@code count} targets stand, as {x, z} offsets from the arena center: one ring for up to 6, an inner
     * and an outer ring beyond that, so the crowd spreads over the whole arena.
     */
    @Nonnull
    public static List<double[]> spots(int count, double radius) {
        List<double[]> out = new ArrayList<>();
        if (count <= 6) {
            ring(out, count, radius * 0.5, 0);
        } else {
            int inner = count / 3;
            ring(out, inner, radius * 0.3, 0);
            ring(out, count - inner, radius * 0.68, Math.PI / (count - inner));
        }
        return out;
    }

    private static void ring(List<double[]> out, int count, double distance, double turn) {
        for (int i = 0; i < count; i++) {
            double angle = turn + Math.PI * 2 * i / count;
            out.add(new double[] { Math.cos(angle) * distance, Math.sin(angle) * distance });
        }
    }
}
