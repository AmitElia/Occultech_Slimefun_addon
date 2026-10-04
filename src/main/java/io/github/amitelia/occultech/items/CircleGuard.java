package io.github.amitelia.occultech.items;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.thebusybiscuit.slimefun4.api.events.ExplosiveToolBreakBlocksEvent;
import java.util.List;
import java.util.OptionalInt;
import org.bukkit.Location;
import org.bukkit.block.Block;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockBurnEvent;
import org.bukkit.event.block.BlockExplodeEvent;
import org.bukkit.event.block.BlockFromToEvent;
import org.bukkit.event.block.BlockPistonExtendEvent;
import org.bukkit.event.block.BlockPistonRetractEvent;
import org.bukkit.event.entity.EntityExplodeEvent;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * While a ritual runs or a boss walks a circle, the circle is bound (Session P4): its altar, bowls, glyphs and candles -
 * every Occultech block on the altar's level within the circle, and the blocks holding them up - can't be broken,
 * blown up, burnt, washed away or pushed. Breaking a bowl mid-ritual used to fail the ritual a second later, or never
 * be noticed; now it simply can't happen. Runs before Slimefun's own break handling, so nothing drops.
 */
public final class CircleGuard implements Listener {

    private final RitualService rituals;

    public CircleGuard(RitualService rituals) {
        this.rituals = rituals;
    }

    /** Whether {@code block} belongs to (or holds up) a circle that is in use right now. */
    public boolean isBound(Block block) {
        for (Location at : rituals.activeAltars()) {
            if (at.getWorld() != block.getWorld()) {
                continue;
            }
            Block altar = at.getBlock();
            int dx = block.getX() - altar.getX();
            int dz = block.getZ() - altar.getZ();
            if (dx == 0 && dz == 0 && block.getY() == altar.getY()) {
                return true;
            }
            OptionalInt tier = Circles.tierOfAltar(String.valueOf(BlockStorage.checkID(altar)));
            int radius = tier.isPresent() ? Circles.forTier(tier.getAsInt()).radius() : 0;
            if (Math.abs(dx) > radius || Math.abs(dz) > radius) {
                continue;
            }
            if (block.getY() == altar.getY() && ours(block)) {
                return true;
            }
            if (block.getY() == altar.getY() - 1 && ours(block.getRelative(0, 1, 0))) {
                return true;   // what a carpet glyph or a candle stands on
            }
        }
        return false;
    }

    private static boolean ours(Block block) {
        String id = BlockStorage.checkID(block);
        return id != null && id.startsWith(ItemKeys.slimefunId(""));
    }

    @EventHandler(priority = EventPriority.LOWEST, ignoreCancelled = true)
    public void onBreak(BlockBreakEvent e) {
        if (isBound(e.getBlock())) {
            e.setCancelled(true);
            e.getPlayer().sendActionBar(MenuUtils.color("&5The circle is bound while its ritual or summons lasts."));
        }
    }

    @EventHandler(priority = EventPriority.LOWEST, ignoreCancelled = true)
    public void onExplosiveTool(ExplosiveToolBreakBlocksEvent e) {
        if (isBound(e.getPrimaryBlock()) || e.getAdditionalBlocks().stream().anyMatch(this::isBound)) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onEntityExplode(EntityExplodeEvent e) {
        e.blockList().removeIf(this::isBound);
    }

    @EventHandler(ignoreCancelled = true)
    public void onBlockExplode(BlockExplodeEvent e) {
        e.blockList().removeIf(this::isBound);
    }

    @EventHandler(ignoreCancelled = true)
    public void onPistonExtend(BlockPistonExtendEvent e) {
        if (anyBound(e.getBlocks())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onPistonRetract(BlockPistonRetractEvent e) {
        if (anyBound(e.getBlocks())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onBurn(BlockBurnEvent e) {
        if (isBound(e.getBlock())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onFlow(BlockFromToEvent e) {
        if (isBound(e.getToBlock())) {
            e.setCancelled(true);
        }
    }

    private boolean anyBound(List<Block> blocks) {
        for (Block block : blocks) {
            if (isBound(block)) {
                return true;
            }
        }
        return false;
    }
}
