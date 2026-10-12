package io.github.amitelia.occultech.boss;

import java.util.function.Consumer;
import java.util.List;
import org.bukkit.Location;
import org.bukkit.entity.LivingEntity;

/** Optional carrier and presentation layer. Fight rules always remain in {@link BossFight}. */
public interface BossBody {
    <T extends LivingEntity> T spawn(String id, Class<T> type, Location at, Consumer<T> setup);

    default void playAction(LivingEntity entity, String bossId, String action) {}

    /** The action with the target it locked: Mythic skills reach it as {@code @trigger}. */
    default void playAction(LivingEntity entity, String bossId, String action, org.bukkit.entity.Entity target) {
        playAction(entity, bossId, action);
    }

    default void stop(LivingEntity entity) {}

    default boolean isMythic(String id) { return false; }

    default boolean isCarrier(LivingEntity entity) { return true; }

    default List<String> extraRewards(String id) { return List.of(); }

    /** A model at {@code at} (its feet on that spot) for a fight object, or null to keep the vanilla look. */
    default Prop prop(String modelId, Location at) { return null; }

    /**
     * Keeps a dying boss's model for its whole {@code death} clip: the game removes a dead mob after a second, and its
     * model goes with it. Hides the carrier's model and plays the clip on a stand-in at the same spot, which goes
     * by itself once the clip has played. Null when the boss has no model.
     */
    default Prop corpse(LivingEntity dead) { return null; }
}
