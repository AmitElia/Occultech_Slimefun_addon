package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.Particle;
import org.bukkit.block.Block;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;

/**
 * Frenzy Idol: a rare drop from The Unbound. Placed, Servitor Shrines within 8 blocks work 50% faster.
 */
public class FrenzyIdol extends SlimefunItem {

    public FrenzyIdol(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        ServitorService servitors) {
        super(group, item, type, recipe, output);

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                servitors.registerIdol(block.getLocation());
                rituals.holograms().show(block, null, "&6Frenzy Idol &8| &7shrines within 8 work faster");
                block.getWorld().spawnParticle(Particle.ANGRY_VILLAGER, block.getLocation().add(0.5, 1.2, 0.5), 1, 0.2, 0.1, 0.2, 0);
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                servitors.removeIdol(e.getBlock().getLocation());
            }
        });
    }
}
