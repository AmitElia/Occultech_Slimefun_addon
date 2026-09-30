package io.github.amitelia.occultech.items;

import org.bukkit.block.Block;

/**
 * Read access to the Scrying Mirror's status line (used by the self-test).
 */
public final class ScryingMirrorAccess {

    private ScryingMirrorAccess() {}

    public static String status(RitualService rituals, Block mirror) {
        return ScryingMirror.status(rituals, mirror);
    }
}
