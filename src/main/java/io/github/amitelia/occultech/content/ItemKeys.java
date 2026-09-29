package io.github.amitelia.occultech.content;

import javax.annotation.Nonnull;

/**
 * One string identity for "what item is this", shared by recipes and ritual matching.
 * <ul>
 * <li>vanilla item: {@code mc:MATERIAL}</li>
 * <li>base Slimefun or other addon item: its Slimefun id, e.g. {@code MAGIC_LUMP_1}</li>
 * <li>Occultech item: {@code OCCULTECH_<ID>}</li>
 * </ul>
 */
public final class ItemKeys {

    public static final String PREFIX = "OCCULTECH_";
    public static final String VANILLA = "mc:";
    private static final String SLIMEFUN = "sf:";

    private ItemKeys() {}

    /** Converts a key as written in recipes.yml to its runtime form. */
    @Nonnull
    public static String fromCatalog(@Nonnull String catalogKey) {
        if (catalogKey.startsWith(VANILLA)) {
            return catalogKey;
        }
        if (catalogKey.startsWith(SLIMEFUN)) {
            return catalogKey.substring(SLIMEFUN.length());
        }
        return slimefunId(catalogKey);
    }

    /** Slimefun id of an Occultech catalog id. */
    @Nonnull
    public static String slimefunId(@Nonnull String occultechId) {
        return PREFIX + occultechId;
    }

    @Nonnull
    public static String vanilla(@Nonnull String materialName) {
        return VANILLA + materialName;
    }

    public static boolean isVanilla(@Nonnull String key) {
        return key.startsWith(VANILLA);
    }
}
