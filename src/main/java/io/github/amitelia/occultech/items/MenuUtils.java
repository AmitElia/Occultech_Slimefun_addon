package io.github.amitelia.occultech.items;

import java.util.Arrays;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.implementation.Slimefun;
import io.github.thebusybiscuit.slimefun4.libraries.dough.protection.Interaction;

import io.github.amitelia.occultech.content.ItemKeys;

/**
 * Small helpers for block menus and item identity.
 */
final class MenuUtils {

    private MenuUtils() {}

    static boolean canOpen(Block block, Player player) {
        return player.hasPermission("slimefun.inventory.bypass")
            || Slimefun.getProtectionManager().hasPermission(player, block.getLocation(), Interaction.INTERACT_BLOCK);
    }

    static ItemStack icon(Material material, String name, String... lore) {
        ItemStack item = new ItemStack(material);
        ItemMeta meta = item.getItemMeta();
        meta.setDisplayName(color(name));
        meta.setLore(Arrays.stream(lore).map(MenuUtils::color).toList());
        item.setItemMeta(meta);
        return item;
    }

    static boolean isEmpty(@Nullable ItemStack item) {
        return item == null || item.getType().isAir() || item.getAmount() <= 0;
    }

    /** The {@link ItemKeys} identity of a stack: its Slimefun id, or {@code mc:MATERIAL} for vanilla items. */
    @Nullable
    static String keyOf(@Nullable ItemStack item) {
        if (isEmpty(item)) {
            return null;
        }
        SlimefunItem sfItem = SlimefunItem.getByItem(item);
        return sfItem != null ? sfItem.getId() : ItemKeys.vanilla(item.getType().name());
    }

    static String color(String text) {
        return ChatColor.translateAlternateColorCodes('&', text);
    }
}
