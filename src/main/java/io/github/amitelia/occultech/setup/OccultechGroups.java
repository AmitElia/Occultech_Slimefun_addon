package io.github.amitelia.occultech.setup;

import java.util.HashMap;
import java.util.Map;

import javax.annotation.Nonnull;

import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;

/**
 * One Slimefun guide category per tier.
 */
public final class OccultechGroups {

    private static final Material[] ICONS = { Material.LODESTONE, Material.AMETHYST_CLUSTER, Material.PRISMARINE_CRYSTALS, Material.WITHER_ROSE };
    private static final Map<Integer, ItemGroup> GROUPS = new HashMap<>();

    private OccultechGroups() {}

    @Nonnull
    public static ItemGroup forTier(@Nonnull ItemCatalog catalog, int tier) {
        return GROUPS.computeIfAbsent(tier, t -> new ItemGroup(Occultech.key("tier_" + t),
            icon(ICONS[Math.min(t, ICONS.length - 1)], "&5Occultech &8- &d" + catalog.tier(t).name())));
    }

    private static ItemStack icon(Material material, String name) {
        ItemStack item = new ItemStack(material);
        ItemMeta meta = item.getItemMeta();
        meta.setDisplayName(ChatColor.translateAlternateColorCodes('&', name));
        item.setItemMeta(meta);
        return item;
    }
}
