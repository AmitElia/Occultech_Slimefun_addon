package io.github.amitelia.occultech.setup;

import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import io.github.amitelia.occultech.Occultech;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;

/**
 * Slimefun guide categories. Add new groups here as content tiers grow.
 */
public final class OccultechGroups {

    public static final ItemGroup MATERIALS = new ItemGroup(Occultech.key("materials"), icon(Material.BONE_MEAL, "&5Occultech &8- &dMaterials"));

    private OccultechGroups() {}

    private static ItemStack icon(Material material, String name) {
        ItemStack item = new ItemStack(material);
        ItemMeta meta = item.getItemMeta();
        meta.setDisplayName(ChatColor.translateAlternateColorCodes('&', name));
        item.setItemMeta(meta);
        return item;
    }
}
