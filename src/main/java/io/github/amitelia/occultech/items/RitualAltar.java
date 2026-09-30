package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.Occultech;
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
 * Center of a summoning circle. Its menu holds the ritual's center item and has a "Begin Ritual" button;
 * the circle check, matching and the ritual itself are handled by {@link RitualService}.
 */
public class RitualAltar extends SlimefunItem {

    public static final int CENTER_SLOT = 13;
    private static final int INFO_SLOT = 4;
    private static final int BUTTON_SLOT = 22;

    public RitualAltar(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals) {
        super(group, item, type, recipe, output);

        new BlockMenuPreset(getId(), getItemName()) {

            @Override
            public void init() {
                for (int slot = 0; slot < 27; slot++) {
                    if (slot != CENTER_SLOT && slot != INFO_SLOT && slot != BUTTON_SLOT) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO_SLOT, MenuUtils.icon(Material.LODESTONE, "&5Summoning Circle",
                    "&7Put the ritual's center item", "&7in the slot below and its", "&7offerings in the Offering Bowls.",
                    "", "&7Right-click this altar with an", "&7&dOccult Codex &7to check the circle."), (p, slot, stack, action) -> false);
                addItem(BUTTON_SLOT, MenuUtils.icon(Material.SOUL_CAMPFIRE, "&dBegin Ritual",
                    "&7Checks the circle and offerings,", "&7then performs the ritual."), (p, slot, stack, action) -> false);
            }

            @Override
            public boolean canOpen(Block block, Player player) {
                return MenuUtils.canOpen(block, player);
            }

            @Override
            public int[] getSlotsAccessedByItemTransport(ItemTransportFlow flow) {
                return new int[0];
            }

            @Override
            public void newInstance(BlockMenu menu, Block block) {
                menu.addMenuClickHandler(BUTTON_SLOT, (p, slot, stack, action) -> {
                    p.closeInventory();
                    rituals.begin(p, block);
                    return false;
                });
                menu.addMenuClickHandler(CENTER_SLOT, (p, slot, stack, action) -> !rituals.isLocked(block.getLocation()));
                menu.addPlayerInventoryClickHandler((p, slot, stack, action) -> !rituals.isLocked(block.getLocation()));
                // a fight interrupted by a crash leaves a marker on the altar: return its catalyst
                Bukkit.getScheduler().runTask(Occultech.instance(), () -> rituals.recoverAltar(block));
            }
        };

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(e.getBlock().getLocation(), CENTER_SLOT);
                }
            }
        });
    }
}
