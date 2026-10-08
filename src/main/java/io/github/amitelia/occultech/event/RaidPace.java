package io.github.amitelia.occultech.event;

import javax.annotation.Nonnull;

/**
 * How hard Act 2 pushes right now (docs/staff-raid.md, "Pace"). The pace rises with the Council's shared bar, not with
 * separate phases: three bands, then a soft enrage once the fight runs long. Pure Java, unit tested.
 *
 * @param band           0 (100-66%), 1 (66-33%) or 2 (33-0% or enraged)
 * @param cooldownFactor multiply every cooldown by this
 * @param overlap        how many raid mechanics may run at once
 * @param beams          beams on a spinning laser
 * @param reverse        whether lasers may change direction
 * @param ringWaves      rings per stomp
 * @param damageFactor   multiply every hit by this (only above 1 once enraged)
 */
public record RaidPace(int band, double cooldownFactor, int overlap, int beams, boolean reverse, int ringWaves, double damageFactor) {

    /** The soft enrage starts after this long (ticks): 15 minutes. */
    public static final int ENRAGE_TICKS = 15 * 60 * 20;
    /** Once enraged, damage grows by this share... */
    public static final double ENRAGE_STEP = 0.05;
    /** ...every this many ticks (30 s). */
    public static final int ENRAGE_EVERY = 30 * 20;

    /** The pace for the Council at {@code healthFraction} of its bar, {@code elapsed} ticks into Act 2. */
    @Nonnull
    public static RaidPace of(double healthFraction, int elapsed) {
        return of(healthFraction, elapsed, ENRAGE_TICKS);
    }

    @Nonnull
    public static RaidPace of(double healthFraction, int elapsed, int enrageTicks) {
        boolean enraged = elapsed >= enrageTicks;
        int band = enraged || healthFraction <= 1 / 3.0 ? 2 : healthFraction <= 2 / 3.0 ? 1 : 0;
        double damage = enraged ? 1 + ENRAGE_STEP * (1 + (elapsed - enrageTicks) / ENRAGE_EVERY) : 1;
        return switch (band) {
            case 0 -> new RaidPace(0, 1, 1, 2, false, 1, damage);
            case 1 -> new RaidPace(1, 0.8, 2, 3, false, 2, damage);
            default -> new RaidPace(2, 0.65, 3, 4, true, 2, damage);
        };
    }

    /** A cooldown of {@code ticks} at this pace (whole boss steps). */
    public int cooldown(int ticks) {
        return Math.max(5, (int) Math.round(ticks * cooldownFactor / 5.0) * 5);
    }
}
