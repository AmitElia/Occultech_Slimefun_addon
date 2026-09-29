package io.github.amitelia.occultech.core;

import javax.annotation.Nullable;

import org.bukkit.NamespacedKey;
import org.bukkit.entity.Entity;
import org.bukkit.persistence.PersistentDataType;

/**
 * Persistent-data keys shared across systems.
 */
public final class Keys {

    /** Marks every entity Occultech summons (bosses, their extra mobs, mounts, minions, decoys). */
    public static final NamespacedKey SUMMONED = new NamespacedKey("occultech", "summoned");

    private Keys() {}

    public static boolean isSummoned(@Nullable Entity entity) {
        return entity != null && entity.getPersistentDataContainer().has(SUMMONED, PersistentDataType.BYTE);
    }
}
