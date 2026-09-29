package io.github.amitelia.occultech.ritual;

import java.util.Map;

import javax.annotation.Nonnull;

/**
 * A crafting ritual: one item on the altar plus offerings in bowls (one bowl per offering, a bowl holds a stack).
 * All keys use the {@code ItemKeys} runtime format.
 */
public record RitualRecipe(@Nonnull String outputId, int outputAmount, @Nonnull String center, @Nonnull Map<String, Integer> offerings, int circle) {}
