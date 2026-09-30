package io.github.amitelia.occultech.boss;

import javax.annotation.Nonnull;

/**
 * Data about a boss that comes from recipes.yml (name, tier, loot) rather than from its behavior class.
 *
 * @param dropId     Slimefun id of the boss's drop
 * @param drops      guaranteed drops per win per contributor
 * @param arenaRadius fight radius around the altar
 */
public record BossSpec(@Nonnull String id, @Nonnull String name, int tier, boolean major, @Nonnull String dropId, int drops,
    double arenaRadius, int timeLimitSeconds) {}
