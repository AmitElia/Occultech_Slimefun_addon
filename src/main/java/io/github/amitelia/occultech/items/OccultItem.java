package io.github.amitelia.occultech.items;

import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.attributes.NotPlaceable;

/**
 * A plain Occultech item (materials, drops, catalysts). Never placeable, even when its look is a block.
 */
public class OccultItem extends SlimefunItem implements NotPlaceable {

    public OccultItem(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output) {
        super(group, item, type, recipe, output);
    }
}
