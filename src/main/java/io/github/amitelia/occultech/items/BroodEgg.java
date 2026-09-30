package io.github.amitelia.occultech.items;

import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.block.data.BlockData;
import org.bukkit.block.data.Hatchable;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;

/**
 * Brood Egg: a rare Brood Mother drop. Looks like a sniffer egg but never hatches, and slowly spins String.
 */
public class BroodEgg extends ProducerBlock {

    public BroodEgg(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        int secondsPerString) {
        super(group, item, type, recipe, output, rituals, Material.STRING, "string", secondsPerString, Material.COBWEB);
    }

    /** Sniffer eggs crack over time and hatch at full crack; keep it at zero so it never hatches. */
    @Override
    protected void beforeTick(Block block) {
        BlockData data = block.getBlockData();
        if (data instanceof Hatchable hatchable && hatchable.getHatch() > 0) {
            hatchable.setHatch(0);
            block.setBlockData(hatchable, false);
        }
    }
}
