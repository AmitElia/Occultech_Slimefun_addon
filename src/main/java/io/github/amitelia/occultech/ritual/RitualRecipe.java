package io.github.amitelia.occultech.ritual;

import java.util.Map;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * A ritual: an item on the altar (or nothing) plus offerings in bowls (one bowl per offering, a bowl holds a stack).
 * All keys use the {@code ItemKeys} runtime format.
 *
 * @param outputId the crafted item, or null for a summoning ritual
 * @param center   the item that must be on the altar, or null if the altar must be empty
 * @param bossId   the boss this ritual summons, or null for a crafting ritual
 */
public record RitualRecipe(@Nullable String outputId, int outputAmount, @Nullable String center, @Nonnull Map<String, Integer> offerings,
    int circle, @Nullable String bossId) {

    public static RitualRecipe crafting(String outputId, int amount, String center, Map<String, Integer> offerings, int circle) {
        return new RitualRecipe(outputId, amount, center, offerings, circle, null);
    }

    public static RitualRecipe summoning(String bossId, @Nullable String center, Map<String, Integer> offerings, int circle) {
        return new RitualRecipe(null, 0, center, offerings, circle, bossId);
    }

    public boolean isSummon() {
        return bossId != null;
    }
}
