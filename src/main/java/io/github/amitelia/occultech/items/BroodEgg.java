package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.block.Block;
import org.bukkit.block.data.BlockData;
import org.bukkit.block.data.Hatchable;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ChestMenu.AdvancedMenuClickHandler;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ClickAction;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset;
import me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow;

/**
 * Brood Egg: a rare Brood Mother drop. Placed, it looks like a sniffer egg but never hatches, and slowly spins String
 * into a 9-slot store. Right-click to collect; Slimefun cargo and Networks can pull from the store (they can't insert).
 * <p>
 * Production only happens while the chunk is loaded and never catches up on time spent unloaded.
 */
public class BroodEgg extends SlimefunItem {

    public static final int[] OUTPUT_SLOTS = { 9, 10, 11, 12, 13, 14, 15, 16, 17 };
    private static final int INFO_SLOT = 4;

    private final Map<Location, Long> lastSpin = new HashMap<>();

    public BroodEgg(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        int secondsPerString) {
        super(group, item, type, recipe, output);
        long interval = Math.max(1, secondsPerString) * 1000L;

        new BlockMenuPreset(getId(), MenuUtils.color("&fBrood Egg")) {

            @Override
            public void init() {
                for (int slot = 0; slot < 27; slot++) {
                    if ((slot < 9 || slot > 17) && slot != INFO_SLOT) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO_SLOT, MenuUtils.icon(Material.COBWEB, "&fBrood Egg",
                    "&7Spins &f1 String &7every &f" + secondsPerString + "s", "&7while this area is loaded.",
                    "", "&7Cargo and Networks can pull", "&7from the store below."), (p, s, i, a) -> false);
            }

            @Override
            public boolean canOpen(Block block, Player player) {
                return MenuUtils.canOpen(block, player);
            }

            @Override
            public int[] getSlotsAccessedByItemTransport(ItemTransportFlow flow) {
                return flow == ItemTransportFlow.WITHDRAW ? OUTPUT_SLOTS : new int[0];
            }

            @Override
            public void newInstance(BlockMenu menu, Block block) {
                // output only: players can take items out but not put items in
                for (int slot : OUTPUT_SLOTS) {
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

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                keepUnhatched(block);
                BlockMenu menu = BlockStorage.getInventory(block);
                if (menu == null) {
                    return;
                }

                long now = System.currentTimeMillis();
                Long last = lastSpin.putIfAbsent(block.getLocation(), now);
                if (last != null && now - last >= interval) {
                    lastSpin.put(block.getLocation(), now);
                    ItemStack rest = menu.pushItem(new ItemStack(Material.STRING), OUTPUT_SLOTS);
                    if (rest == null) {
                        block.getWorld().spawnParticle(Particle.BLOCK, block.getLocation().add(0.5, 0.6, 0.5), 6, 0.2, 0.2, 0.2,
                            Material.COBWEB.createBlockData());
                    }
                }

                int stored = 0;
                for (int slot : OUTPUT_SLOTS) {
                    ItemStack content = menu.getItemInSlot(slot);
                    stored += MenuUtils.isEmpty(content) ? 0 : content.getAmount();
                }
                String status = stored >= OUTPUT_SLOTS.length * 64 ? "&cFull" : "&7" + stored + " string";
                rituals.holograms().show(block, null, "&fBrood Egg &8| " + status);
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                lastSpin.remove(e.getBlock().getLocation());
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(e.getBlock().getLocation(), OUTPUT_SLOTS);
                }
            }
        });
    }

    /** Sniffer eggs crack over time and hatch at full crack; keep it at zero so it never hatches. */
    private static void keepUnhatched(Block block) {
        BlockData data = block.getBlockData();
        if (data instanceof Hatchable hatchable && hatchable.getHatch() > 0) {
            hatchable.setHatch(0);
            block.setBlockData(hatchable, false);
        }
    }
}
