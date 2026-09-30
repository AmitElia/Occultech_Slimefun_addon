package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.content.ItemKeys;
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
 * <ul>
 * <li>Contract slot: only contract items; swap them any time to change the job.</li>
 * <li>Store (27 slots): output of producing contracts, and the supply for Brewer's Aid / Acolyte. Players, cargo and
 * Networks can put items in and take them out.</li>
 * <li>Empower: feed one Spirit Essence from your inventory for an hour of double speed (up to 24h banked).</li>
 * </ul>
 * No fuel otherwise. At most {@value ServitorService#MAX_NEARBY} shrines within {@value ServitorService#CAP_RADIUS}
 * blocks. See {@link ServitorService}.
 */
public class ServitorShrine extends SlimefunItem {

    public static final int CONTRACT_SLOT = 4;
    /** Takes an Abyssal Tether (tier 2), which widens the contract's radius. */
    public static final int UPGRADE_SLOT = 13;
    public static final int[] STORE = range(18, 45);
    private static final int INFO_SLOT = 11;
    private static final int EMPOWER_SLOT = 15;
    private static final String SPIRIT_ESSENCE = ItemKeys.slimefunId("SPIRIT_ESSENCE");

    public ServitorShrine(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        ServitorService servitors) {
        super(group, item, type, recipe, output);

        new BlockMenuPreset(getId(), MenuUtils.color("&5Servitor Shrine")) {

            @Override
            public void init() {
                // the store (18-44) holds no preset items, so the size must be explicit: an inferred size would stop at
                // slot 17 and Slimefun would never save the store (losing it, and the contract with it, on reload)
                setSize(45);
                for (int slot = 0; slot < 18; slot++) {
                    if (slot != CONTRACT_SLOT && slot != UPGRADE_SLOT && slot != INFO_SLOT && slot != EMPOWER_SLOT) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO_SLOT, MenuUtils.icon(Material.HEART_OF_THE_SEA, "&5Servitor Shrine",
                    "&7Put a &fContract &7in the top slot;", "&7swap it any time to change the job.",
                    "", "&7Harvest, Gather, Shepherd, Beekeeper,", "&7Brewer's Aid: 9x9 around the shrine",
                    "&7Ward, Acolyte: 17x17", "", "&7Middle slot: &3Abyssal Tether &7widens",
                    "&7these to 15x15 and 25x25.", "", "&7The store below holds output and supplies;",
                    "&7cargo and Networks can use it."), (p, s, i, a) -> false);
                addItem(EMPOWER_SLOT, empowerIcon(), (p, s, i, a) -> false);
            }

            @Override
            public boolean canOpen(Block block, Player player) {
                return MenuUtils.canOpen(block, player);
            }

            @Override
            public int[] getSlotsAccessedByItemTransport(ItemTransportFlow flow) {
                return STORE;
            }

            @Override
            public void newInstance(BlockMenu menu, Block block) {
                // only contracts go in the contract slot
                menu.addMenuClickHandler(CONTRACT_SLOT, new AdvancedMenuClickHandler() {
                    @Override
                    public boolean onClick(Player p, int s, ItemStack cursor, ClickAction action) {
                        return false;
                    }

                    @Override
                    public boolean onClick(InventoryClickEvent e, Player p, int s, ItemStack cursor, ClickAction action) {
                        return MenuUtils.isEmpty(cursor) || ServitorService.Contract.of(MenuUtils.keyOf(cursor)) != null;
                    }
                });
                // only an Abyssal Tether goes in the upgrade slot
                menu.addMenuClickHandler(UPGRADE_SLOT, new AdvancedMenuClickHandler() {
                    @Override
                    public boolean onClick(Player p, int s, ItemStack cursor, ClickAction action) {
                        return false;
                    }

                    @Override
                    public boolean onClick(InventoryClickEvent e, Player p, int s, ItemStack cursor, ClickAction action) {
                        return MenuUtils.isEmpty(cursor) || (ServitorService.TETHER_ID.equals(MenuUtils.keyOf(cursor)) && cursor.getAmount() == 1);
                    }
                });
                menu.addMenuClickHandler(EMPOWER_SLOT, (p, slot, stack, action) -> {
                    if (takeEssence(p)) {
                        servitors.empower(block);
                        p.playSound(block.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 1F, 1.4F);
                        p.sendMessage(ChatColor.LIGHT_PURPLE + "The spirit is empowered: double speed for "
                            + (servitors.empoweredFor(block) / 60000 + 1) + " minutes.");
                    } else {
                        p.sendMessage(ChatColor.GRAY + "You need a Spirit Essence in your inventory to empower the shrine.");
                    }
                    return false;
                });
            }
        };

        addItemHandler(new BlockPlaceHandler(false) {
            @Override
            public void onPlayerPlace(BlockPlaceEvent e) {
                if (!servitors.canPlace(e.getBlock().getLocation())) {
                    e.setCancelled(true);
                    e.getPlayer().sendMessage(ChatColor.RED + "Too many spirits bound nearby (max " + ServitorService.MAX_NEARBY
                        + " shrines within " + ServitorService.CAP_RADIUS + " blocks).");
                    return;
                }
                BlockStorage.addBlockInfo(e.getBlock(), ServitorService.OWNER_KEY, e.getPlayer().getUniqueId().toString());
                servitors.onPlaced(e.getBlock());
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
                    String status = servitors.tick(block, menu, STORE, CONTRACT_SLOT, UPGRADE_SLOT);
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
                    menu.dropItems(e.getBlock().getLocation(), CONTRACT_SLOT, UPGRADE_SLOT);
                    menu.dropItems(e.getBlock().getLocation(), STORE);
                }
            }
        });
    }

    private static ItemStack empowerIcon() {
        return MenuUtils.icon(Material.POPPED_CHORUS_FRUIT, "&dEmpower",
            "&7Click with a &fSpirit Essence &7in your", "&7inventory: double speed for &f1 hour&7.",
            "&7Banks up to 24 hours. Stacks with a", "&7Frenzy Idol (x1.5) for x3.");
    }

    private static boolean takeEssence(Player player) {
        for (ItemStack item : player.getInventory().getContents()) {
            SlimefunItem sfItem = item == null || item.getType().isAir() ? null : SlimefunItem.getByItem(item);
            if (sfItem != null && sfItem.getId().equals(SPIRIT_ESSENCE)) {
                item.setAmount(item.getAmount() - 1);
                return true;
            }
        }
        return false;
    }

    private static int[] range(int from, int to) {
        int[] slots = new int[to - from];
        for (int i = 0; i < slots.length; i++) {
            slots[i] = from + i;
        }
        return slots;
    }
}
