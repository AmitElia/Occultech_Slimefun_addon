package io.github.amitelia.occultech.items;

import java.util.List;
import java.util.Optional;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitRunnable;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.attributes.NotPlaceable;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/**
 * Right-click anywhere: opens the codex (circles, crafting rituals, summoning rituals).
 * Right-click an altar: opens the circle page with that altar's circle checked, and marks missing pieces in the world
 * with red particles that only you see.
 */
public class OccultCodex extends SlimefunItem implements NotPlaceable {

    private static final int HIGHLIGHT_SECONDS = 10;
    private static final Particle.DustOptions MISSING = new Particle.DustOptions(Color.fromRGB(230, 40, 40), 1.6F);
    private static final Particle.DustOptions COMPLETE = new Particle.DustOptions(Color.fromRGB(80, 220, 120), 1.2F);

    public OccultCodex(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals, Plugin plugin) {
        super(group, item, type, recipe, output);
        CodexMenu pages = new CodexMenu(rituals);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            Optional<Block> clicked = e.getClickedBlock();
            Optional<RitualService.CircleCheck> check = clicked.flatMap(rituals::checkCircle);
            if (check.isPresent()) {
                highlight(plugin, player, clicked.get(), check.get());
                pages.openCircle(player, check.get().tier(), check.get());
            } else {
                pages.openHome(player);
            }
            player.playSound(player.getLocation(), Sound.ITEM_BOOK_PAGE_TURN, 1F, 1F);
        });
    }

    private static void highlight(Plugin plugin, Player player, Block altar, RitualService.CircleCheck check) {
        if (check.complete()) {
            player.playSound(player.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 1F, 1.2F);
            player.spawnParticle(Particle.DUST, altar.getLocation().add(0.5, 1.2, 0.5), 30, 1.2, 0.2, 1.2, 0, COMPLETE);
            return;
        }
        List<int[]> missing = check.missing();
        new BukkitRunnable() {
            private int runs;

            @Override
            public void run() {
                if (!player.isOnline() || runs++ >= HIGHLIGHT_SECONDS * 2) {
                    cancel();
                    return;
                }
                for (int[] offset : missing) {
                    Location at = altar.getRelative(offset[0], 0, offset[1]).getLocation().add(0.5, 0.4, 0.5);
                    player.spawnParticle(Particle.DUST, at, 3, 0.15, 0.15, 0.15, 0, MISSING);
                }
            }
        }.runTaskTimer(plugin, 0L, 10L);
    }
}
