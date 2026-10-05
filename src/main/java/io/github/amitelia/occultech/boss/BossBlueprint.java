package io.github.amitelia.occultech.boss;

import java.util.function.Function;

import javax.annotation.Nonnull;

/**
 * Registers a boss's behavior under its recipes.yml id. {@code type} is the behavior class: loading it declares the
 * boss's {@link Mechanic}s (for the balance report) without starting a fight.
 */
public record BossBlueprint(@Nonnull String id, @Nonnull Class<? extends BossBehavior> type, @Nonnull Function<BossFight, BossBehavior> factory) {

    /** Loads the behavior class, so its mechanics are declared. */
    public void load() {
        try {
            Class.forName(type.getName(), true, type.getClassLoader());
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException(e);
        }
    }
}
