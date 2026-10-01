package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.ChatColor;
import org.bukkit.Sound;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.Damageable;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/**
 * Necromancy item: right-click to raise minions for 30 seconds. Bone Scepter (tier 1): 2 skeleton archers; Grave
 * Lantern (tier 2): 3 wither knights. Uses 1 durability per summon (Unbreaking applies) and stops working at 1
 * durability instead of breaking.
 */
public class BoneScepter extends OccultItem {

    private static final int LIFETIME_SECONDS = 30;

    private final Map<UUID, Long> cooldowns = new HashMap<>();

    public BoneScepter(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, MinionService minions,
        MinionService.Kind kind, int count, long cooldownMs) {
        this(group, item, type, recipe, output, minions, kind, count, cooldownMs, LIFETIME_SECONDS, 0);
    }

    /**
     * @param lifetimeSeconds how long raised minions stay
     * @param cap             most minions an owner may have at once (0 = no cap): the item tops up to the cap
     */
    public BoneScepter(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, MinionService minions,
        MinionService.Kind kind, int count, long cooldownMs, int lifetimeSeconds, int cap) {
        super(group, item, type, recipe, output);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            ItemStack scepter = e.getItem();
            if (cap > 0 && minions.count(player) > 0) {
                // a capped escort toggles: use it again to send the knights back
                minions.dismissAll(player.getUniqueId());
                player.sendMessage(ChatColor.GRAY + "Your knights return to the dark.");
                player.playSound(player.getLocation(), Sound.ENTITY_WITHER_SKELETON_DEATH, 0.6F, 1.4F);
                return;
            }
            long now = System.currentTimeMillis();
            long ready = cooldowns.getOrDefault(player.getUniqueId(), 0L);
            if (now < ready) {
                player.sendMessage(ChatColor.GRAY + "The bones need " + ((ready - now) / 1000 + 1) + "s more to settle.");
                return;
            }
            int raise = cap > 0 ? Math.min(count, cap) : count;
            if (!useDurability(scepter)) {
                player.sendMessage(ChatColor.RED + "The scepter is spent. Repair it before calling the dead again.");
                player.playSound(player.getLocation(), Sound.BLOCK_BONE_BLOCK_BREAK, 1F, 0.6F);
                return;
            }
            cooldowns.put(player.getUniqueId(), now + cooldownMs);
            minions.raise(player, kind, raise, lifetimeSeconds);
        });
    }

    /** Takes one point of durability (Unbreaking can save it). False if the item is already at its last point. */
    static boolean useDurability(ItemStack item) {
        if (!(item.getItemMeta() instanceof Damageable meta) || !meta.hasMaxDamage()) {
            return true;
        }
        if (meta.getDamage() >= meta.getMaxDamage() - 1) {
            return false;
        }
        int unbreaking = item.getEnchantmentLevel(Enchantment.UNBREAKING);
        if (unbreaking == 0 || ThreadLocalRandom.current().nextInt(unbreaking + 1) == 0) {
            meta.setDamage(meta.getDamage() + 1);
            item.setItemMeta(meta);
        }
        return true;
    }
}
