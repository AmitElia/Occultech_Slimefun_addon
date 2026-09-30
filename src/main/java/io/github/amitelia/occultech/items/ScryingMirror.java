package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockPlaceHandler;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockUseHandler;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * Scrying Mirror: a rare drop from the Mirrored Magus. Right-click an altar while holding it to link it; placed, its
 * hologram shows that circle's state from afar (circle complete?, ritual running, boss and its health).
 */
public class ScryingMirror extends SlimefunItem {

    static final String LINK_KEY = "occultech_link";
    private static final org.bukkit.NamespacedKey ITEM_LINK = new org.bukkit.NamespacedKey("occultech", "mirror_link");

    public ScryingMirror(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals) {
        super(group, item, type, recipe, output);

        // link: right-click an altar with the mirror in hand
        addItemHandler((ItemUseHandler) e -> {
            Optional<Block> clicked = e.getClickedBlock();
            String id = clicked.map(BlockStorage::checkID).orElse(null);
            if (id == null || Circles.tierOfAltar(id).isEmpty()) {
                return;
            }
            e.cancel();
            ItemStack hand = e.getItem();
            ItemMeta meta = hand.getItemMeta();
            meta.getPersistentDataContainer().set(ITEM_LINK, PersistentDataType.STRING, serialize(clicked.get().getLocation()));
            List<String> lore = meta.hasLore() ? new ArrayList<>(meta.getLore()) : new ArrayList<>();
            lore.removeIf(line -> ChatColor.stripColor(line).startsWith("Linked to"));
            lore.add(ChatColor.LIGHT_PURPLE + "Linked to " + clicked.get().getX() + " " + clicked.get().getY() + " " + clicked.get().getZ());
            meta.setLore(lore);
            hand.setItemMeta(meta);
            e.getPlayer().sendMessage(ChatColor.LIGHT_PURPLE + "The mirror now watches this circle. Place it anywhere.");
        });

        addItemHandler(new BlockPlaceHandler(false) {
            @Override
            public void onPlayerPlace(BlockPlaceEvent e) {
                String link = e.getItemInHand().getItemMeta().getPersistentDataContainer().get(ITEM_LINK, PersistentDataType.STRING);
                if (link != null) {
                    BlockStorage.addBlockInfo(e.getBlock(), LINK_KEY, link);
                }
            }
        });

        addItemHandler((BlockUseHandler) e -> {
            e.cancel();
            e.getClickedBlock().ifPresent(block -> e.getPlayer().sendMessage(MenuUtils.color("&dScrying Mirror: &f" + status(rituals, block))));
        });

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                rituals.holograms().show(block, null, "&dScrying Mirror\n&f" + status(rituals, block));
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
            }
        });
    }

    /** What the linked circle is doing right now, in one line. */
    static String status(RitualService rituals, Block mirror) {
        Block altar = linked(mirror);
        if (altar == null) {
            return "&7Not linked. Right-click an altar with the mirror item.";
        }
        if (!altar.getChunk().isLoaded()) {
            return "&7The circle is out of reach (unloaded).";
        }
        Optional<BossFight> fight = rituals.bosses().fightAt(altar);
        if (fight.isPresent()) {
            return "&c" + fight.get().spec().name() + " &7- &f" + Math.round(fight.get().healthFraction() * 100) + "% &7health";
        }
        String busy = rituals.altarStatus(altar);
        if (busy != null) {
            return busy;
        }
        return rituals.checkCircle(altar)
            .map(check -> check.complete() ? "&aCircle complete and quiet" : "&c" + check.missing().size() + " circle pieces missing")
            .orElse("&7The linked altar is gone.");
    }

    @Nullable
    private static Block linked(Block mirror) {
        String link = BlockStorage.getLocationInfo(mirror.getLocation(), LINK_KEY);
        if (link == null) {
            return null;
        }
        String[] parts = link.split(";");
        World world = Bukkit.getWorld(parts[0]);
        return world == null ? null : world.getBlockAt(Integer.parseInt(parts[1]), Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
    }

    static String serialize(Location at) {
        return at.getWorld().getName() + ";" + at.getBlockX() + ";" + at.getBlockY() + ";" + at.getBlockZ();
    }
}
