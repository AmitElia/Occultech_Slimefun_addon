package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.logging.Logger;
import javax.annotation.Nonnull;
import org.bukkit.Location;
import org.bukkit.block.Block;
import org.bukkit.inventory.ItemStack;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * A record, in a block's Slimefun data, of what a running ritual or infusion took out of which menus - so a server
 * crash mid-way gives the inputs back instead of swallowing them (Sessions P3/P4). Written when the inputs are taken,
 * cleared when the work finishes or is handed back normally; read when the block loads again.
 * <p>
 * Never twice: an input is only returned if its slot holds no more than was left right after the take. If the take
 * itself never reached the disk (the crash came first), the items are still in their slot and nothing is added.
 */
final class CrashLedger {

    /** One taken stack: from {@code slot} of the menu at {@code block}, leaving {@code left} behind. */
    record Entry(Location block, int slot, ItemStack item, int left) {}

    private CrashLedger() {}

    /** An entry for {@code item} just taken from {@code slot} of {@code menu} (call after the take). */
    static Entry taken(@Nonnull BlockMenu menu, int slot, @Nonnull ItemStack item) {
        ItemStack left = menu.getItemInSlot(slot);
        return new Entry(menu.getLocation(), slot, item.clone(), MenuUtils.isEmpty(left) ? 0 : left.getAmount());
    }

    static void save(@Nonnull Block holder, @Nonnull String key, @Nonnull List<Entry> entries) {
        StringBuilder out = new StringBuilder();
        for (Entry e : entries) {
            out.append(out.isEmpty() ? "" : ";").append(e.block().getBlockX()).append(',').append(e.block().getBlockY()).append(',')
                .append(e.block().getBlockZ()).append(',').append(e.slot()).append(',').append(e.left()).append(',')
                .append(Base64.getEncoder().encodeToString(e.item().serializeAsBytes()));
        }
        BlockStorage.addBlockInfo(holder, key, out.toString());
    }

    static void clear(@Nonnull Block holder, @Nonnull String key) {
        if (BlockStorage.hasBlockInfo(holder)) {
            BlockStorage.addBlockInfo(holder, key, null);
        }
    }

    /** Gives back what a crash cut short (once): into the slot it came from, or dropped at {@code holder}. */
    static void restore(@Nonnull Block holder, @Nonnull String key, @Nonnull Logger log) {
        String saved = BlockStorage.getLocationInfo(holder.getLocation(), key);
        if (saved == null || saved.isEmpty()) {
            return;
        }
        clear(holder, key);
        List<String> failed = new ArrayList<>();
        for (String entry : saved.split(";")) {
            try {
                String[] f = entry.split(",", 6);
                Block block = holder.getWorld().getBlockAt(Integer.parseInt(f[0]), Integer.parseInt(f[1]), Integer.parseInt(f[2]));
                int slot = Integer.parseInt(f[3]);
                int left = Integer.parseInt(f[4]);
                ItemStack item = ItemStack.deserializeBytes(Base64.getDecoder().decode(f[5]));
                BlockMenu menu = BlockStorage.getInventory(block);
                ItemStack now = menu == null ? null : menu.getItemInSlot(slot);
                if (!MenuUtils.isEmpty(now) && now.isSimilar(item) && now.getAmount() > left) {
                    continue;   // the take never reached the disk: the input is still in its slot
                }
                if (menu != null && MenuUtils.isEmpty(now)) {
                    menu.replaceExistingItem(slot, item);
                } else {
                    ItemStack rest = menu == null ? item : menu.pushItem(item, slot);
                    if (rest != null) {
                        holder.getWorld().dropItemNaturally(holder.getLocation().add(0.5, 1.2, 0.5), rest);
                    }
                }
            } catch (RuntimeException e) {
                failed.add(e.toString());
            }
        }
        if (!failed.isEmpty()) {
            log.warning("Could not give back " + failed.size() + " input(s) at " + holder.getLocation() + ": " + failed);
        }
    }
}
