package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.block.Block;
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
 * A block that slowly produces items (cycling through its product list) into a 9-slot store (Brood Egg: string, Phantom Roost: membranes).
 * Right-click to collect; Slimefun cargo and Networks can pull from the store but not insert.
 * Production only happens while the chunk is loaded and never catches up on time spent unloaded.
 */
public class ProducerBlock extends SlimefunItem {

    public static final int[] OUTPUT_SLOTS = { 9, 10, 11, 12, 13, 14, 15, 16, 17 };
    private static final int INFO_SLOT = 4;

    private static final String MADE_KEY = "occultech_made";

    private final Map<Location, Long> lastMade = new HashMap<>();

    public ProducerBlock(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        List<Material> products, String productName, int seconds, Material particleBlock) {
        super(group, item, type, recipe, output);
        Material product = products.get(0);
        long interval = Math.max(1, seconds) * 1000L;
        String title = item.item().getItemMeta().getDisplayName();

        new BlockMenuPreset(getId(), title) {

            @Override
            public void init() {
                for (int slot = 0; slot < 27; slot++) {
                    if ((slot < 9 || slot > 17) && slot != INFO_SLOT) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO_SLOT, MenuUtils.icon(product, title,
                    "&7Makes &f1 " + productName + " &7every &f" + seconds + "s", "&7while this area is loaded.",
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
                beforeTick(block);
                BlockMenu menu = BlockStorage.getInventory(block);
                if (menu == null) {
                    return;
                }

                long now = System.currentTimeMillis();
                Long last = lastMade.putIfAbsent(block.getLocation(), now);
                if (last != null && now - last >= interval) {
                    lastMade.put(block.getLocation(), now);
                    // several products cycle in order (e.g. shard, shard, crystal)
                    int made = made(block) + 1;
                    BlockStorage.addBlockInfo(block, MADE_KEY, String.valueOf(made % products.size()));
                    if (menu.pushItem(new ItemStack(products.get((made - 1) % products.size())), OUTPUT_SLOTS) == null) {
                        block.getWorld().spawnParticle(Particle.BLOCK, block.getLocation().add(0.5, 0.6, 0.5), 6, 0.2, 0.2, 0.2,
                            particleBlock.createBlockData());
                    }
                }

                int stored = 0;
                for (int slot : OUTPUT_SLOTS) {
                    ItemStack content = menu.getItemInSlot(slot);
                    stored += MenuUtils.isEmpty(content) ? 0 : content.getAmount();
                }
                String status = stored >= OUTPUT_SLOTS.length * product.getMaxStackSize() ? "&cFull" : "&7" + stored + " " + productName;
                rituals.holograms().show(block, null, title + " &8| " + status);
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                lastMade.remove(e.getBlock().getLocation());
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(e.getBlock().getLocation(), OUTPUT_SLOTS);
                }
            }
        });
    }

    private static int made(Block block) {
        try {
            String value = BlockStorage.getLocationInfo(block.getLocation(), MADE_KEY);
            return value == null ? 0 : Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    /** Hook for block-specific upkeep each tick (e.g. keeping an egg from hatching). */
    protected void beforeTick(Block block) {}
}
