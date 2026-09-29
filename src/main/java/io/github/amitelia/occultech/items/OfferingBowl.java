package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset;
import me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow;

/**
 * Holds one stack of offerings for a ritual. Contents are a Slimefun block menu, so Slimefun persists them;
 * the slot is locked while a ritual that uses this bowl is running.
 */
public class OfferingBowl extends SlimefunItem {

    public static final int SLOT = 4;
    private static final int[] BACKGROUND = { 0, 1, 2, 3, 5, 6, 7, 8 };

    public OfferingBowl(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals) {
        super(group, item, type, recipe, output);

        new BlockMenuPreset(getId(), MenuUtils.color("&8Offering Bowl")) {

            @Override
            public void init() {
                drawBackground(BACKGROUND);
            }

            @Override
            public boolean canOpen(Block block, Player player) {
                return MenuUtils.canOpen(block, player);
            }

            @Override
            public int[] getSlotsAccessedByItemTransport(ItemTransportFlow flow) {
                // no cargo: offerings are placed by hand
                return new int[0];
            }

            @Override
            public void newInstance(BlockMenu menu, Block block) {
                menu.addMenuClickHandler(SLOT, (p, slot, stack, action) -> !rituals.isLocked(block.getLocation()));
                menu.addPlayerInventoryClickHandler((p, slot, stack, action) -> !rituals.isLocked(block.getLocation()));
            }
        };

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(e.getBlock().getLocation(), SLOT);
                }
            }
        });
    }
}
