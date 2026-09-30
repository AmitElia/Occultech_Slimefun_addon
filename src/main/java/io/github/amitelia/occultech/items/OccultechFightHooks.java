package io.github.amitelia.occultech.items;

import java.util.Map;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.block.Block;
import org.bukkit.entity.Item;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.boss.FightHooks;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * Slimefun side of the boss engine: loot items, catalyst refunds and the crash marker on the altar.
 * <p>
 * While a fight runs, the altar's block data holds {@value #ACTIVE_KEY} = the catalyst's id (or "none"). If the server
 * crashes mid-fight, the marker survives and the catalyst is returned the next time the altar loads.
 */
public final class OccultechFightHooks implements FightHooks {

    static final String ACTIVE_KEY = "occultech_active_fight";
    static final String NO_REFUND = "none";

    @Override
    public void giveLoot(Player player, String itemId, int amount) {
        SlimefunItem item = SlimefunItem.getById(itemId);
        if (item == null) {
            return;
        }
        ItemStack loot = item.getItem().clone();
        loot.setAmount(amount);
        Map<Integer, ItemStack> leftover = player.getInventory().addItem(loot);
        for (ItemStack rest : leftover.values()) {
            Item dropped = player.getWorld().dropItem(player.getLocation(), rest);
            dropped.setOwner(player.getUniqueId());
        }
        player.sendMessage(ChatColor.LIGHT_PURPLE + "You earned " + amount + "x " + item.getItemName() + ChatColor.LIGHT_PURPLE + ".");
    }

    @Override
    public void refund(Block altar, ItemStack item) {
        BlockMenu menu = BlockStorage.getInventory(altar);
        if (menu != null && MenuUtils.isEmpty(menu.getItemInSlot(RitualAltar.CENTER_SLOT))) {
            menu.replaceExistingItem(RitualAltar.CENTER_SLOT, item);
        } else {
            altar.getWorld().dropItemNaturally(altar.getLocation().add(0.5, 1.2, 0.5), item);
        }
    }

    @Override
    public void markActive(Block altar, @Nullable ItemStack refund) {
        SlimefunItem catalyst = refund == null ? null : SlimefunItem.getByItem(refund);
        BlockStorage.addBlockInfo(altar, ACTIVE_KEY, catalyst == null ? NO_REFUND : catalyst.getId());
    }

    @Override
    public void clearActive(Block altar) {
        if (BlockStorage.hasBlockInfo(altar)) {
            BlockStorage.addBlockInfo(altar, ACTIVE_KEY, null);
        }
    }

    /** After a crash: return the catalyst of a fight that no longer exists. */
    void recover(Block altar) {
        String marker = BlockStorage.getLocationInfo(altar.getLocation(), ACTIVE_KEY);
        if (marker == null) {
            return;
        }
        clearActive(altar);
        SlimefunItem catalyst = NO_REFUND.equals(marker) ? null : SlimefunItem.getById(marker);
        if (catalyst != null) {
            refund(altar, catalyst.getItem().clone());
        }
    }
}
