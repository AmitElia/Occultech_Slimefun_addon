package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ChestMenu;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset;
import me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow;

/**
 * Servitor Nexus (tier 3): links up to {@value ServitorService#NEXUS_LINKS} Servitor Shrines within
 * {@value ServitorService#NEXUS_RANGE} blocks.
 * <ul>
 * <li>Shared store: linked shrines deliver into the Nexus's 45-slot store first (cargo and Networks can use it), and
 * their Brewer's Aid / Acolyte supplies are taken from it too.</li>
 * <li>Empower all: one Spirit Essence empowers every linked shrine for an hour.</li>
 * <li>Overview: a menu listing every linked shrine with its contract, area and status; click one to open that shrine
 * (and swap its contract) from here.</li>
 * </ul>
 */
public class ServitorNexus extends SlimefunItem {

    public static final int[] STORE = range(9, 54);
    private static final int OVERVIEW_SLOT = 2;
    private static final int INFO_SLOT = 4;
    private static final int EMPOWER_SLOT = 6;

    public ServitorNexus(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        ServitorService servitors) {
        super(group, item, type, recipe, output);

        new BlockMenuPreset(getId(), MenuUtils.color("&3Servitor Nexus")) {

            @Override
            public void init() {
                // the store holds no preset items, so the size must be explicit or it would never be saved
                setSize(54);
                for (int slot = 0; slot < 9; slot++) {
                    if (slot != OVERVIEW_SLOT && slot != INFO_SLOT && slot != EMPOWER_SLOT) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO_SLOT, MenuUtils.icon(Material.CONDUIT, "&3Servitor Nexus",
                    "&7Links up to " + ServitorService.NEXUS_LINKS + " Servitor Shrines", "&7within " + ServitorService.NEXUS_RANGE + " blocks.",
                    "", "&7Linked shrines deliver here and take", "&7their supplies from here.", "&7Cargo and Networks can use the store."),
                    (p, s, i, a) -> false);
                addItem(OVERVIEW_SLOT, MenuUtils.icon(Material.SPYGLASS, "&bOverview", "&7See every linked shrine;", "&7click one to open it."),
                    (p, s, i, a) -> false);
                addItem(EMPOWER_SLOT, MenuUtils.icon(Material.POPPED_CHORUS_FRUIT, "&dEmpower all",
                    "&7Click with a &fSpirit Essence &7in your", "&7inventory: every linked shrine works", "&7at double speed for &f1 hour&7."),
                    (p, s, i, a) -> false);
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
                menu.addMenuClickHandler(OVERVIEW_SLOT, (p, slot, stack, action) -> {
                    openOverview(p, block, servitors);
                    return false;
                });
                menu.addMenuClickHandler(EMPOWER_SLOT, (p, slot, stack, action) -> {
                    List<Location> linked = servitors.linkedTo(block.getLocation());
                    if (linked.isEmpty()) {
                        p.sendMessage(ChatColor.GRAY + "No shrines are linked to this Nexus yet.");
                    } else if (ServitorShrine.takeEssence(p)) {
                        linked.forEach(at -> servitors.empower(at.getBlock()));
                        p.playSound(block.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 1F, 1.2F);
                        p.sendMessage(ChatColor.LIGHT_PURPLE + "All " + linked.size() + " linked spirits are empowered for an hour.");
                    } else {
                        p.sendMessage(ChatColor.GRAY + "You need a Spirit Essence in your inventory.");
                    }
                    return false;
                });
            }
        };

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                servitors.registerNexus(block.getLocation());
                int linked = servitors.linkedTo(block.getLocation()).size();
                rituals.holograms().show(block, null, "&3Servitor Nexus &8| &7" + linked + "/" + ServitorService.NEXUS_LINKS + " shrines linked");
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                servitors.removeNexus(e.getBlock().getLocation());
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(e.getBlock().getLocation(), STORE);
                }
            }
        });
    }

    /** Every linked shrine at a glance; clicking one opens it (contracts can be swapped there). */
    private static void openOverview(Player player, Block nexus, ServitorService servitors) {
        ChestMenu menu = new ChestMenu(MenuUtils.color("&3Linked shrines"));
        menu.setEmptySlotsClickable(false);
        menu.setPlayerInventoryClickable(true);
        for (int slot = 0; slot < 18; slot++) {
            menu.addItem(slot, MenuUtils.icon(Material.GRAY_STAINED_GLASS_PANE, " "), (p, s, i, a) -> false);
        }
        List<Location> linked = new ArrayList<>(servitors.linkedTo(nexus.getLocation()));
        for (int i = 0; i < linked.size() && i < 18; i++) {
            Location at = linked.get(i);
            ServitorService.Contract contract = servitors.contractAt(at);
            boolean tethered = servitors.tetheredAt(at);
            int radius = contract == null ? 0 : contract.radius(tethered);
            long empowered = servitors.empoweredFor(at.getBlock());
            ItemStack icon = MenuUtils.icon(contract == null ? Material.PURPUR_PILLAR : Material.PAPER,
                "&5Shrine at &f" + at.getBlockX() + " " + at.getBlockY() + " " + at.getBlockZ(),
                "&7Contract: &f" + (contract == null ? "none" : contract.label),
                "&7Area: &f" + (contract == null ? "-" : (radius * 2 + 1) + "x" + (radius * 2 + 1)) + (tethered ? " &3(tethered)" : ""),
                "&7Status: " + servitors.statusAt(at),
                empowered > 0 ? "&dEmpowered: " + (empowered / 60000 + 1) + " min" : "&8Not empowered",
                "", "&eClick to open this shrine");
            menu.addItem(i, icon, (p, s, item, action) -> {
                BlockMenu shrine = BlockStorage.getInventory(at.getBlock());
                if (shrine != null && MenuUtils.canOpen(at.getBlock(), p)) {
                    shrine.open(p);
                } else {
                    p.sendMessage(ChatColor.GRAY + "That shrine can't be opened from here.");
                }
                return false;
            });
        }
        menu.open(player);
    }

    private static int[] range(int from, int to) {
        int[] slots = new int[to - from];
        for (int i = 0; i < slots.length; i++) {
            slots[i] = from + i;
        }
        return slots;
    }
}
