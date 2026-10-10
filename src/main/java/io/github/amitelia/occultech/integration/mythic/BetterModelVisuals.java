package io.github.amitelia.occultech.integration.mythic;

import org.bukkit.entity.Entity;

import kr.toxicity.model.api.BetterModel;

/** Read-only probe of the pinned BetterModel 3.5.0 tracker API. */
public final class BetterModelVisuals {
    private BetterModelVisuals() {}

    public static boolean available(String modelId) {
        return BetterModel.model(modelId).isPresent();
    }

    public static boolean attached(Entity entity, String modelId) {
        return BetterModel.registry(entity.getUniqueId())
            .map(registry -> registry.trackers().stream().anyMatch(tracker -> tracker.renderer().name().equals(modelId)))
            .orElse(false);
    }

    public static long count(Entity entity, String modelId) {
        return BetterModel.registry(entity.getUniqueId())
            .map(registry -> registry.trackers().stream().filter(tracker -> tracker.renderer().name().equals(modelId)).count())
            .orElse(0L);
    }

    public static String trackerNames(Entity entity) {
        return BetterModel.registry(entity.getUniqueId())
            .map(registry -> registry.trackers().stream().map(tracker -> tracker.renderer().name()).toList().toString())
            .orElse("no registry");
    }
}
