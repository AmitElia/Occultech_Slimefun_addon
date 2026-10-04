package io.github.amitelia.occultech.core;

import org.bukkit.NamespacedKey;
import org.bukkit.entity.Entity;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntitySpawnEvent;
import org.bukkit.event.world.EntitiesLoadEvent;

/**
 * Keeps entity-clearing plugins off Occultech's entities. ClearLaggEnhanced (DJtmk) clears and spawn-limits by entity
 * type: it spares displays, but not the {@code Interaction} hitboxes of fight objects (a cleared pylon or heart makes a
 * fight unwinnable), adds, unnamed bosses or minions, and its mob limiter can cancel a boss's spawn in a crowded chunk.
 * It always spares entities with the scoreboard tag {@value #PROTECTED}, so every entity carrying Occultech data gets it:
 * on spawn (after our own spawn handlers tag it, before the clearer's HIGHEST handlers) and when old ones load.
 */
public final class ClearLagGuard implements Listener {

    public static final String PROTECTED = "CLE_PROTECTED";

    @EventHandler(priority = EventPriority.HIGH)
    public void onSpawn(EntitySpawnEvent event) {
        protect(event.getEntity());
    }

    @EventHandler
    public void onLoad(EntitiesLoadEvent event) {
        for (Entity entity : event.getEntities()) {
            protect(entity);
        }
    }

    private static void protect(Entity entity) {
        if (isOurs(entity)) {
            entity.addScoreboardTag(PROTECTED);
        }
    }

    public static boolean isOurs(Entity entity) {
        for (NamespacedKey key : entity.getPersistentDataContainer().getKeys()) {
            if ("occultech".equals(key.getNamespace())) {
                return true;
            }
        }
        return false;
    }
}
