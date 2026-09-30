package io.github.amitelia.occultech.core;

import javax.annotation.Nullable;

import org.bukkit.NamespacedKey;
import org.bukkit.entity.Entity;
import org.bukkit.persistence.PersistentDataType;

/**
 * Persistent-data keys shared across systems.
 */
public final class Keys {

    /** Marks every entity Occultech summons (bosses, their extra mobs, mounts, minions, decoys, fight objects). */
    public static final NamespacedKey SUMMONED = new NamespacedKey("occultech", "summoned");

    /** The fight (UUID string) a summoned entity belongs to. */
    public static final NamespacedKey FIGHT = new NamespacedKey("occultech", "fight");

    /** Marks hologram displays above bowls, altars and other blocks (never saved with the world). */
    public static final NamespacedKey HOLOGRAM = new NamespacedKey("occultech", "hologram");

    /** Marks entities placed by /occultech showcase so it can clean up after itself. */
    public static final NamespacedKey SHOWCASE = new NamespacedKey("occultech", "showcase");

    private Keys() {}

    public static boolean isSummoned(@Nullable Entity entity) {
        return entity != null && entity.getPersistentDataContainer().has(SUMMONED, PersistentDataType.BYTE);
    }

    @Nullable
    public static String fightOf(@Nullable Entity entity) {
        return entity == null ? null : entity.getPersistentDataContainer().get(FIGHT, PersistentDataType.STRING);
    }
}
