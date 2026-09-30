package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockUseHandler;

/**
 * A floor tile with an effect when walked on (see {@link CosmeticListener}). Tiles are meant to be laid in numbers, so
 * they have no ticker: nothing runs until someone steps on one. With more than one look, right-click cycles it.
 */
public class StepTile extends SlimefunItem {

    public StepTile(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, List<Material> looks) {
        super(group, item, type, recipe, output);

        if (looks.size() > 1) {
            addItemHandler((BlockUseHandler) e -> e.getClickedBlock().ifPresent(block -> {
                if (e.getPlayer().isSneaking()) {
                    return; // let players place blocks against tiles while sneaking
                }
                e.cancel();
                int current = looks.indexOf(block.getType());
                Material next = looks.get((current + 1) % looks.size());
                // no physics: coral out of water must not be updated into dead coral
                block.setType(next, false);
                e.getPlayer().sendActionBar(MenuUtils.color("&d" + getItemName() + "&7: " + MenuUtils.pretty(next)));
            }));
        }
    }
}
