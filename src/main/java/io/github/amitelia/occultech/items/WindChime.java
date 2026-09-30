package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;

/**
 * Wind Chime: players within 32 blocks get Speed II and Jump Boost II. It chimes softly now and then - one random
 * note from a pentatonic scale every 10-25 seconds - never constantly.
 */
public class WindChime extends SlimefunItem {

    public static final double RADIUS = 32;
    /** A pentatonic scale (note block pitches), so any two random notes sound pleasant together. */
    private static final float[] PENTATONIC = { 0.5F, 0.561F, 0.63F, 0.749F, 0.841F, 1.0F, 1.122F, 1.26F, 1.498F, 1.682F };

    private final Map<Location, Long> nextChime = new HashMap<>();

    public WindChime(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals) {
        super(group, item, type, recipe, output);

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                Location center = block.getLocation().add(0.5, 0.5, 0.5);
                for (Player player : block.getWorld().getNearbyPlayers(center, RADIUS)) {
                    refresh(player, PotionEffectType.SPEED);
                    refresh(player, PotionEffectType.JUMP_BOOST);
                }

                long now = System.currentTimeMillis();
                Long next = nextChime.get(block.getLocation());
                if (next == null) {
                    nextChime.put(block.getLocation(), now + randomDelay());
                } else if (now >= next) {
                    nextChime.put(block.getLocation(), now + randomDelay());
                    float pitch = PENTATONIC[ThreadLocalRandom.current().nextInt(PENTATONIC.length)];
                    block.getWorld().playSound(center, Sound.BLOCK_NOTE_BLOCK_CHIME, 0.7F, pitch);
                    block.getWorld().spawnParticle(Particle.NOTE, center.clone().add(0, 0.9, 0), 1, 0.2, 0.1, 0.2, pitch / 2);
                }
                rituals.holograms().show(block, null, "&bWind Chime &8| &7Speed II, Jump Boost II within 32");
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                nextChime.remove(e.getBlock().getLocation());
            }
        });
    }

    /** Keeps the effect topped up without flicker, and never replaces a stronger one. */
    private static void refresh(Player player, PotionEffectType type) {
        PotionEffect current = player.getPotionEffect(type);
        if (current == null || (current.getAmplifier() <= 1 && current.getDuration() < 60)) {
            player.addPotionEffect(new PotionEffect(type, 100, 1, true, false, true));
        }
    }

    private static long randomDelay() {
        return 10_000 + ThreadLocalRandom.current().nextLong(15_000);
    }
}
