package io.github.amitelia.occultech.boss;

import java.util.function.Function;

import javax.annotation.Nonnull;

/**
 * Registers a boss's behavior under its recipes.yml id.
 */
public record BossBlueprint(@Nonnull String id, @Nonnull Function<BossFight, BossBehavior> factory) {}
