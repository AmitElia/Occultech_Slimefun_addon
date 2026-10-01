package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.block.Block;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockUseHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;

/**
 * A decoration block. Its visuals are drawn by {@link DecorationService}; right-click cycles its palette.
 */
public class DecorationBlock extends SlimefunItem {

    public DecorationBlock(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output,
        DecorationService decorations, DecorationService.Kind kind) {
        super(group, item, type, recipe, output);

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                decorations.register(block, kind);
            }
        });

        addItemHandler((BlockUseHandler) e -> {
            org.bukkit.Material held = e.getItem() == null ? org.bukkit.Material.AIR : e.getItem().getType();
            if (held == org.bukkit.Material.FLINT_AND_STEEL || held == org.bukkit.Material.FIRE_CHARGE) {
                return; // lighting it (Prismatic Netherrack), not changing its look
            }
            e.cancel();
            e.getClickedBlock().ifPresent(block -> {
                String palette = decorations.cyclePalette(block, kind);
                e.getPlayer().sendActionBar(MenuUtils.color("&d" + getItemName() + "&7: " + palette));
            });
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                decorations.remove(e.getBlock());
            }
        });
    }
}
