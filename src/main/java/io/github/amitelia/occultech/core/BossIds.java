package io.github.amitelia.occultech.core;

import java.util.List;
import java.util.Map;

/**
 * Boss ids that were renamed. Old ids still live in saved data: a fight saved on an altar, a player's win count (which
 * unlocks that boss's halo), restock buttons in built showcases. Everything that reads a boss id from saved data or a
 * command passes it through {@link #current}; win counts add up every id the boss has had.
 */
public final class BossIds {

    /** old id -> current id */
    private static final Map<String, String> RENAMED = Map.of(
        "GELATINOUS_SOVEREIGN", "MIRE_MONARCH"   // 2026-10-11: the slime became a toad
    );

    private BossIds() {}

    /** The current id for {@code id} (itself unless it was renamed). */
    public static String current(String id) {
        return RENAMED.getOrDefault(id, id);
    }

    /** Every earlier id of the boss now called {@code id}. */
    public static List<String> previous(String id) {
        return RENAMED.entrySet().stream().filter(e -> e.getValue().equals(id)).map(Map.Entry::getKey).toList();
    }
}
