package io.github.amitelia.occultech.setup;

import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.Occultech;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.implementation.SlimefunItems;

/**
 * Registers every Occultech item with Slimefun.
 * This package is the only place that should touch Slimefun's item/recipe API,
 * so porting to a different Slimefun build stays contained here.
 */
public final class OccultechItems {

    private OccultechItems() {}

    public static void setup(Occultech plugin) {
        new SlimefunItem(OccultechGroups.MATERIALS, OccultechStacks.RITUAL_CHALK, RecipeType.ENHANCED_CRAFTING_TABLE, new ItemStack[] {
            null, new ItemStack(Material.BONE_MEAL), null,
            new ItemStack(Material.CLAY_BALL), SlimefunItems.MAGIC_LUMP_1.item(), new ItemStack(Material.CLAY_BALL),
            null, new ItemStack(Material.BONE_MEAL), null
        }, OccultechStacks.RITUAL_CHALK.item().asQuantity(4)).register(plugin);
    }
}
