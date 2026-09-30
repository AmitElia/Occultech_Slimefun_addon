package io.github.amitelia.occultech.ritual;

import java.util.List;
import java.util.Map;
import java.util.OptionalInt;

import javax.annotation.Nonnull;

/**
 * Circle layouts per tier. Every piece sits on the same layer as the altar. Higher tiers will contain the lower
 * circles (Occultism-style), so a tier-N altar can also run lower-tier rituals.
 */
public final class Circles {

    public static final String CHALK_GLYPH = "OCCULTECH_CHALK_GLYPH";
    public static final String TALLOW_CANDLE = "OCCULTECH_TALLOW_CANDLE";
    public static final String OFFERING_BOWL = "OCCULTECH_OFFERING_BOWL";
    public static final String INITIATE_ALTAR = "OCCULTECH_INITIATE_ALTAR";
    public static final String BOUND_GLYPH = "OCCULTECH_BOUND_GLYPH";
    public static final String BOUND_ALTAR = "OCCULTECH_BOUND_ALTAR";

    /**
     * Tier 0 (5x5): altar in the middle, bowls on its four sides, candles on the diagonals, chalk ring outside.
     */
    private static final CirclePattern INITIATE = new CirclePattern(
        List.of(
            "ccccc",
            "cKBKc",
            "cBABc",
            "cKBKc",
            "ccccc"
        ),
        Map.of('c', CHALK_GLYPH, 'K', TALLOW_CANDLE, 'B', OFFERING_BOWL, 'A', INITIATE_ALTAR)
    );

    /**
     * Tier 1 (7x7): the Initiate's circle with a Bound Altar in the middle, wrapped in a ring of Bound Glyphs with a
     * candle on each corner and a bowl in the middle of each side.
     */
    private static final CirclePattern BOUND = new CirclePattern(
        List.of(
            "KbbBbbK",
            "bcccccb",
            "bcKBKcb",
            "BcBABcB",
            "bcKBKcb",
            "bcccccb",
            "KbbBbbK"
        ),
        Map.of('c', CHALK_GLYPH, 'b', BOUND_GLYPH, 'K', TALLOW_CANDLE, 'B', OFFERING_BOWL, 'A', BOUND_ALTAR)
    );

    private static final Map<String, Integer> ALTAR_TIERS = Map.of(INITIATE_ALTAR, 0, BOUND_ALTAR, 1);
    private static final List<String> NAMES = List.of("Initiate's Circle", "Bound Circle");

    public static int highestTier() {
        return NAMES.size() - 1;
    }

    @Nonnull
    public static String name(int tier) {
        return tier < NAMES.size() ? NAMES.get(tier) : "Tier " + tier + " circle";
    }

    private Circles() {}

    @Nonnull
    public static CirclePattern forTier(int tier) {
        if (tier == 0) {
            return INITIATE;
        }
        if (tier == 1) {
            return BOUND;
        }
        throw new IllegalArgumentException("No circle defined for tier " + tier);
    }

    @Nonnull
    public static OptionalInt tierOfAltar(@Nonnull String altarId) {
        Integer tier = ALTAR_TIERS.get(altarId);
        return tier == null ? OptionalInt.empty() : OptionalInt.of(tier);
    }
}
