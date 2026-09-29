package io.github.amitelia.occultech.items;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
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

import io.github.amitelia.occultech.ritual.CirclePattern;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.attributes.NotPlaceable;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/**
 * Right-click an altar: highlights missing or wrong circle pieces with particles (only you see them).
 * Right-click anywhere else: prints the Initiate's circle layout in chat.
 */
public class OccultCodex extends SlimefunItem implements NotPlaceable {

    private static final int HIGHLIGHT_SECONDS = 10;
    private static final Particle.DustOptions MISSING = new Particle.DustOptions(Color.fromRGB(230, 40, 40), 1.6F);
    private static final Particle.DustOptions COMPLETE = new Particle.DustOptions(Color.fromRGB(80, 220, 120), 1.2F);
    private static final Map<Character, String> SYMBOL_COLORS = Map.of('c', "&f", 'K', "&e", 'B', "&8", 'A', "&5");

    public OccultCodex(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals, Plugin plugin) {
        super(group, item, type, recipe, output);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            Optional<RitualService.CircleCheck> check = e.getClickedBlock().flatMap(rituals::checkCircle);
            if (check.isPresent()) {
                highlight(plugin, player, e.getClickedBlock().get(), check.get());
            } else {
                explain(player, Circles.forTier(0));
            }
        });
    }

    private static void highlight(Plugin plugin, Player player, Block altar, RitualService.CircleCheck check) {
        if (check.complete()) {
            player.sendMessage(MenuUtils.color("&aThe circle is complete."));
            player.playSound(player.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 1F, 1.2F);
            Location center = altar.getLocation().add(0.5, 1.2, 0.5);
            player.spawnParticle(Particle.DUST, center, 30, 1.2, 0.2, 1.2, 0, COMPLETE);
            return;
        }

        Map<String, Integer> missingByGlyph = new LinkedHashMap<>();
        for (int[] offset : check.missing()) {
            String expected = expectedGlyph(check.pattern(), offset, check.rotation());
            missingByGlyph.merge(expected, 1, Integer::sum);
        }
        StringBuilder summary = new StringBuilder("&cMissing or wrong: ");
        missingByGlyph.forEach((id, count) -> {
            SlimefunItem item = SlimefunItem.getById(id);
            summary.append("&f").append(count).append("x ").append(item == null ? id : item.getItemName()).append("&7, ");
        });
        player.sendMessage(MenuUtils.color(summary.substring(0, summary.length() - 4)));
        player.sendMessage(MenuUtils.color("&7The red markers show where for " + HIGHLIGHT_SECONDS + " seconds."));

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

    /** Which glyph belongs at a world offset, undoing the rotation. */
    private static String expectedGlyph(CirclePattern pattern, int[] offset, int rotation) {
        int dx = offset[0];
        int dz = offset[1];
        for (int i = 0; i < rotation; i++) {
            // inverse of a clockwise quarter turn
            int tmp = dx;
            dx = dz;
            dz = -tmp;
        }
        String glyph = pattern.glyphAt(dx, dz);
        return glyph == null ? "?" : glyph;
    }

    private static void explain(Player player, CirclePattern pattern) {
        player.sendMessage(MenuUtils.color("&5&lInitiate's Circle &7(5x5, everything on the altar's layer)"));
        for (String row : pattern.rows()) {
            StringBuilder line = new StringBuilder("  ");
            for (char symbol : row.toCharArray()) {
                line.append(SYMBOL_COLORS.getOrDefault(symbol, "&7")).append(symbol).append(' ');
            }
            player.sendMessage(MenuUtils.color(line.toString()));
        }
        pattern.legend().forEach((symbol, id) -> {
            SlimefunItem item = SlimefunItem.getById(id);
            player.sendMessage(MenuUtils.color("  " + SYMBOL_COLORS.getOrDefault(symbol, "&7") + symbol + " &7= " + (item == null ? id : item.getItemName())));
        });
        player.sendMessage(MenuUtils.color("&7Right-click an altar with this codex to check your circle."));
    }
}
