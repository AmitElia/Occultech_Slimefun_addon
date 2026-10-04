package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.GameMode;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockUseHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * Trophy Board: shows a small, slowly turning model of one boss you have defeated, with how many times you won.
 * Sneak + right-click cycles through the bosses the clicking player has beaten (creative players may pick any boss).
 * Drawn by {@link DecorationService}; the choice is stored in the block ({@value #TROPHY_KEY}: "BOSS;wins;player").
 */
public class TrophyBoard extends SlimefunItem {

    public static final String TROPHY_KEY = "occultech_trophy";

    public TrophyBoard(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, Occultech plugin,
        DecorationService decorations) {
        super(group, item, type, recipe, output);

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                decorations.register(block, DecorationService.Kind.TROPHY_BOARD);
            }
        });

        addItemHandler((BlockUseHandler) e -> {
            if (!e.getPlayer().isSneaking()) {
                return; // a plain right-click places blocks against it; sneak + right-click picks the boss
            }
            e.cancel();
            Player player = e.getPlayer();
            e.getClickedBlock().ifPresent(block -> {
                List<String> choices = new ArrayList<>();
                for (ItemCatalog.BossDef boss : plugin.catalog().bosses()) {
                    boolean summonable = plugin.rituals().spec(boss.id()).isPresent();
                    if (summonable && (player.getGameMode() == GameMode.CREATIVE || Keys.winsOf(player, boss.id()) > 0)) {
                        choices.add(boss.id());
                    }
                }
                if (choices.isEmpty()) {
                    player.sendActionBar(MenuUtils.color("&7Defeat a boss first - its trophy will be yours to show."));
                    return;
                }
                String current = BlockStorage.getLocationInfo(block.getLocation(), TROPHY_KEY);
                String currentId = current == null ? null : current.split(";", 2)[0];
                String next = choices.get((choices.indexOf(currentId) + 1) % choices.size());
                int wins = Keys.winsOf(player, next);
                BlockStorage.addBlockInfo(block, TROPHY_KEY, next + ";" + wins + ";" + player.getName());
                player.sendActionBar(MenuUtils.color("&6Trophy: &f" + ContentRegistrar.title(next) + " &7(" + wins + " wins)"));
                player.playSound(block.getLocation(), Sound.ENTITY_ITEM_FRAME_ROTATE_ITEM, 1F, 0.8F);
            });
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                decorations.remove(e.getBlock());
            }
        });
    }
}
