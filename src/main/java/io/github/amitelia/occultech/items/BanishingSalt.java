package io.github.amitelia.occultech.items;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;
import org.bukkit.GameMode;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

/**
 * Banishing Salt (Session P2): thrown toward a boss fight that has gone wrong - the circle is too dangerous to walk up
 * to - it ends the nearest fight within {@value #RANGE} blocks of its arena. Asks first (use it again within 5 s); one
 * salt is used up and the catalyst is lost, as with every early end. Only the summoner or someone who fought the boss
 * may banish it.
 */
public class BanishingSalt extends SlimefunItem {

    public static final double RANGE = 48;

    public BanishingSalt(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals) {
        super(group, item, type, recipe, output);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            BossFight fight = rituals.bosses().nearestFight(player.getLocation(), RANGE);
            if (fight == null) {
                player.sendActionBar(MenuUtils.color("&7No summoned creature walks a circle nearby."));
                return;
            }
            if (rituals.bosses().requestBanish(player, fight)) {
                if (player.getGameMode() != GameMode.CREATIVE) {
                    e.getItem().subtract();
                }
                player.getWorld().spawnParticle(Particle.WHITE_ASH, player.getEyeLocation(), 40, 0.4, 0.3, 0.4, 0.02);
                player.getWorld().playSound(player.getLocation(), Sound.BLOCK_SAND_BREAK, 1F, 1.6F);
            }
        });
    }
}
