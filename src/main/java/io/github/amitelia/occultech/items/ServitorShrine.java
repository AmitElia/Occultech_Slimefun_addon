package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockPlaceHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ChestMenu.AdvancedMenuClickHandler;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ClickAction;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset;
import me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow;

/**
 * Servitor Shrine: houses a bound spirit that works the area around it according to the contract in its slot.
 * No fuel. Output goes into a 27-slot store that cargo and Networks can pull from. See {@link ServitorService}.
 */
public class ServitorShrine extends SlimefunItem {

    public static final int CONTRACT_SLOT = 4;
    public static final int[] STORE = range(18, 45);
    private static final int INFO_SLOT = 13;

    public ServitorShrine(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        ServitorService servitors) {
        super(group, item, type, recipe, output);

        new BlockMenuPreset(getId(), MenuUtils.color("&5Servitor Shrine")) {

            @Override
            public void init() {
                for (int slot = 0; slot < 18; slot++) {
                    if (slot != CONTRACT_SLOT && slot != INFO_SLOT) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO_SLOT, MenuUtils.icon(Material.HEART_OF_THE_SEA, "&5Servitor Shrine",
                    "&7Put a &fContract &7in the slot above.", "&7Harvest / Gather: works 9x9 around the shrine",
                    "&7Ward: no hostile spawns within 8 blocks", "", "&7No fuel. Output lands in the store below;",
                    "&7cargo and Networks can pull from it."), (p, s, i, a) -> false);
            }

            @Override
            public boolean canOpen(Block block, Player player) {
                return MenuUtils.canOpen(block, player);
            }

            @Override
            public int[] getSlotsAccessedByItemTransport(ItemTransportFlow flow) {
                return flow == ItemTransportFlow.WITHDRAW ? STORE : new int[0];
            }

            @Override
            public void newInstance(BlockMenu menu, Block block) {
                // the store is output only
                for (int slot : STORE) {
                    menu.addMenuClickHandler(slot, new AdvancedMenuClickHandler() {
                        @Override
                        public boolean onClick(Player p, int s, ItemStack cursor, ClickAction action) {
                            return false;
                        }

                        @Override
                        public boolean onClick(InventoryClickEvent e, Player p, int s, ItemStack cursor, ClickAction action) {
                            return cursor == null || cursor.getType().isAir();
                        }
                    });
                }
            }
        };

        addItemHandler(new BlockPlaceHandler(false) {
            @Override
            public void onPlayerPlace(BlockPlaceEvent e) {
                if (servitors.countInChunk(e.getBlock()) >= ServitorService.MAX_PER_CHUNK) {
                    e.setCancelled(true);
                    e.getPlayer().sendMessage(ChatColor.RED + "Too many spirits bound in this chunk (max " + ServitorService.MAX_PER_CHUNK + ").");
                    return;
                }
                BlockStorage.addBlockInfo(e.getBlock(), ServitorService.OWNER_KEY, e.getPlayer().getUniqueId().toString());
            }
        });

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                BlockMenu menu = BlockStorage.getInventory(block);
                if (menu != null) {
                    String status = servitors.tick(block, menu, STORE, CONTRACT_SLOT);
                    rituals.holograms().show(block, null, "&5Servitor Shrine &8| " + status);
                }
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                servitors.removeShrine(e.getBlock().getLocation());
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(e.getBlock().getLocation(), CONTRACT_SLOT);
                    menu.dropItems(e.getBlock().getLocation(), STORE);
                }
            }
        });
    }

    private static int[] range(int from, int to) {
        int[] slots = new int[to - from];
        for (int i = 0; i < slots.length; i++) {
            slots[i] = from + i;
        }
        return slots;
    }
}
