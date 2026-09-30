package io.github.amitelia.occultech.boss;

import java.util.Map;

import javax.annotation.Nonnull;

/**
 * Data about a boss that comes from recipes.yml (name, tier, loot) rather than from its behavior class.
 *
 * @param dropId     Slimefun id of the boss's drop
 * @param drops      guaranteed drops per win per contributor
 * @param arenaRadius fight radius around the altar
 * @param bonusDrops  extra drops (Slimefun id -> chance) rolled per contributor per win
 * @param mobDrops    vanilla material name -> {min, max}, rolled per contributor per win
 * @param xp          experience per contributor per win
 */
public record BossSpec(@Nonnull String id, @Nonnull String name, int tier, boolean major, @Nonnull String dropId, int drops,
    double arenaRadius, int timeLimitSeconds, @Nonnull Map<String, Double> bonusDrops, @Nonnull Map<String, int[]> mobDrops, int xp) {}
