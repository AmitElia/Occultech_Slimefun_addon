package io.github.amitelia.occultech.setup;

import org.bukkit.Material;

import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;

/**
 * Item stack definitions (id, look, name, lore). Registration happens in {@link OccultechItems}.
 * All ids are prefixed with {@code OCCULTECH_} to avoid clashing with other addons.
 */
public final class OccultechStacks {

    public static final SlimefunItemStack RITUAL_CHALK = new SlimefunItemStack(
        "OCCULTECH_RITUAL_CHALK",
        Material.BONE_MEAL,
        "&fRitual Chalk",
        "",
        "&7Used to draw glyphs of",
        "&7a summoning circle"
    );

    private OccultechStacks() {}
}
