package io.github.amitelia.occultech.items;

import java.util.List;

import org.bukkit.Color;
import org.bukkit.Particle;
import org.bukkit.block.Block;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;

/**
 * Frenzy Idol: a rare drop from The Unbound. Placed, Servitor Shrines within 8 blocks work 50% faster.
 */
public class FrenzyIdol extends SlimefunItem {

    /** Bound-tier violet motes that warm to ember orange as they rise (matches the idol's skin). */
    private static final Particle.DustTransition MOTE = new Particle.DustTransition(Color.fromRGB(150, 110, 255), Color.fromRGB(240, 138, 30), 0.9F);

    public FrenzyIdol(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        ServitorService servitors) {
        super(group, item, type, recipe, output);

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                servitors.registerIdol(block.getLocation());
                rituals.holograms().show(block, null, "&6Frenzy Idol &8| &7shrines within 8 work faster");
                block.getWorld().spawnParticle(Particle.DUST_COLOR_TRANSITION, block.getLocation().add(0.5, 1.15, 0.5), 2, 0.3, 0.1, 0.3, 0, MOTE);
                if (Math.random() < 0.25) {
                    block.getWorld().spawnParticle(Particle.SMALL_FLAME, block.getLocation().add(0.5, 1.05, 0.5), 1, 0.08, 0, 0.08, 0.005);
                }
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                servitors.removeIdol(e.getBlock().getLocation());
            }
        });
    }
}
