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

    /** Whether the model's ob_/b_ hitbox bone has its hitbox entity, which passes hits on to the carrier. */
    public static boolean hasHitbox(Entity entity, String modelId) {
        return BetterModel.registry(entity.getUniqueId())
            .map(registry -> registry.trackers().stream().filter(tracker -> tracker.renderer().name().equals(modelId))
                .anyMatch(tracker -> tracker.bones().stream().anyMatch(bone -> bone.getHitBox() != null)))
            .orElse(false);
    }

    /** Debug: each model on the entity, the lowest and highest bone and the head, relative to the entity's feet. */
    public static java.util.List<String> describe(Entity entity) {
        java.util.List<String> out = new java.util.ArrayList<>();
        BetterModel.registry(entity.getUniqueId()).ifPresent(registry -> registry.trackers().forEach(tracker -> {
            float low = Float.MAX_VALUE;
            float high = -Float.MAX_VALUE;
            StringBuilder named = new StringBuilder();
            for (var bone : tracker.bones()) {
                org.joml.Vector3f at = bone.worldPosition();
                low = Math.min(low, at.y);
                high = Math.max(high, at.y);
                String name = bone.name().toString();
                if (name.contains("head") || name.contains("foot") || name.contains("root")) {
                    named.append(String.format(" %s=(%.2f, %.2f, %.2f)", bone.name().name(), at.x, at.y, at.z));
                }
            }
            String boxes = tracker.bones().stream().filter(bone -> bone.getHitBox() != null)
                .map(bone -> bone.name().name()).toList().toString();
            out.add(String.format("%s: bone pivots y %.2f..%.2f;%s; hitboxes %s", tracker.renderer().name(), low, high, named, boxes));
        }));
        return out;
    }

    public static String trackerNames(Entity entity) {
        return BetterModel.registry(entity.getUniqueId())
            .map(registry -> registry.trackers().stream().map(tracker -> tracker.renderer().name()).toList().toString())
            .orElse("no registry");
    }
}
