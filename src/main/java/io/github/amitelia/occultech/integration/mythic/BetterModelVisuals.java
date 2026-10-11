package io.github.amitelia.occultech.integration.mythic;

import org.bukkit.entity.Entity;

import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.bukkit.platform.BukkitAdapter;
import kr.toxicity.model.api.tracker.DummyTracker;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;

/** The pinned BetterModel 3.5.0 API: tracker probes, and models placed at a location for fight objects. */
public final class BetterModelVisuals {
    private BetterModelVisuals() {}

    /** How near a player must be to be shown a prop (blocks). */
    private static final double PROP_VIEW = 48;

    /**
     * A model standing on {@code at}, or null if BetterModel has no such model. Packets only: nothing is saved. A
     * model at a location is shown to no one by itself, so it is spawned for the players near it, and for anyone who
     * comes near later on each refresh.
     */
    public static io.github.amitelia.occultech.boss.Prop prop(String modelId, org.bukkit.Location at) {
        var renderer = BetterModel.model(modelId).orElse(null);
        if (renderer == null) {
            return null;
        }
        DummyTracker tracker = renderer.create(BukkitAdapter.adapt(at));
        Runnable show = () -> {
            for (org.bukkit.entity.Player player : at.getWorld().getPlayers()) {
                if (player.getLocation().distanceSquared(at) < PROP_VIEW * PROP_VIEW && !tracker.isSpawned(player.getUniqueId())) {
                    tracker.spawn(BukkitAdapter.adapt(player));
                }
            }
        };
        show.run();
        return new io.github.amitelia.occultech.boss.Prop() {
            @Override
            public void refresh() {
                if (!tracker.isClosed()) {
                    show.run();
                }
            }

            @Override
            public void animate(String clip) {
                if (!tracker.isClosed()) {
                    tracker.animate(clip);
                }
            }

            @Override
            public void hidePart(String part) {
                if (!tracker.isClosed()) {
                    tracker.update(TrackerUpdateAction.togglePart(false), bone -> bone.name().name().equals(part));
                }
            }

            @Override
            public void remove() {
                if (!tracker.isClosed()) {
                    tracker.close();
                }
            }
        };
    }

    public static boolean available(String modelId) {
        return BetterModel.model(modelId).isPresent();
    }

    public static boolean attached(Entity entity, String modelId) {
        return BetterModel.registry(entity.getUniqueId())
            .map(registry -> registry.trackers().stream().anyMatch(tracker -> tracker.renderer().name().equals(modelId)))
            .orElse(false);
    }

    /** Puts {@code modelId} on {@code entity} (after a Mythic reload lost it). */
    public static void attach(Entity entity, String modelId) {
        BetterModel.model(modelId).ifPresent(renderer -> renderer.create(BukkitAdapter.adapt(entity)));
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
