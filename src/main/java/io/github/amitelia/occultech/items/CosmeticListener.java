package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Color;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.Tag;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockFadeEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * World behavior of the cosmetic blocks:
 * <ul>
 * <li>Step tiles: a chime (amethyst) or a splash (coral) when walked on; nothing while sneaking. Only checked when a
 * player moves onto a new block, with a cheap material filter before any Slimefun lookup, and a short cooldown.</li>
 * <li>Everliving coral, Tidal Tiles and Pearl Beds never dry out of water.</li>
 * <li>Decorative flowers: breaking the block under one pops the Occultech item, never a plain vanilla flower.</li>
 * <li>Prismatic Netherrack burns with its own coloured fire: lighting it (flint and steel, a fire charge, spreading
 * fire, lava) lights that instead of vanilla fire, and a left-click on its top puts it out.</li>
 * </ul>
 */
public final class CosmeticListener implements Listener {

    private static final String CHIMING = ItemKeys.slimefunId("CHIMING_TILE");
    private static final String TIDAL = ItemKeys.slimefunId("TIDAL_TILE");
    private static final String RESIN = ItemKeys.slimefunId("RESIN_TILE");
    private static final String PRISMATIC = ItemKeys.slimefunId("PRISMATIC_NETHERRACK");
    private static final Set<String> NEVER_DRY = Set.of(TIDAL, ItemKeys.slimefunId("EVERLIVING_CORAL"),
        ItemKeys.slimefunId("PEARL_BED"));
    private static final Set<String> FLOWERS = Set.of(ItemKeys.slimefunId("MOONLIT_LILY"), ItemKeys.slimefunId("WITCHCAP"),
        ItemKeys.slimefunId("EVERLIVING_CORAL"), ItemKeys.slimefunId("WATCHFUL_EYEBLOSSOM"));
    private static final long STEP_COOLDOWN_MS = 250;
    /** A pentatonic scale, so any run of steps sounds pleasant. */
    private static final float[] PENTATONIC = { 0.749F, 0.841F, 1.0F, 1.122F, 1.26F, 1.498F, 1.682F };

    private final DecorationService decorations;
    private final Map<UUID, Long> lastStep = new HashMap<>();

    public CosmeticListener(DecorationService decorations) {
        this.decorations = decorations;
    }

    public static final Set<Material> CORAL_BLOCKS = Set.of(Material.TUBE_CORAL_BLOCK, Material.BRAIN_CORAL_BLOCK, Material.BUBBLE_CORAL_BLOCK,
        Material.FIRE_CORAL_BLOCK, Material.HORN_CORAL_BLOCK);

    @EventHandler(ignoreCancelled = true)
    public void onStep(PlayerMoveEvent e) {
        if (e.getFrom().getBlockX() == e.getTo().getBlockX() && e.getFrom().getBlockY() == e.getTo().getBlockY()
            && e.getFrom().getBlockZ() == e.getTo().getBlockZ()) {
            return;
        }
        Player player = e.getPlayer();
        if (player.isSneaking() || !player.isOnGround()) {
            return;
        }
        Block under = e.getTo().getBlock().getRelative(BlockFace.DOWN);
        Material type = under.getType();
        if (type != Material.NOTE_BLOCK && type != Material.AMETHYST_BLOCK && type != Material.RESIN_BRICKS && !CORAL_BLOCKS.contains(type)) {
            return;
        }
        long now = System.currentTimeMillis();
        if (now - lastStep.getOrDefault(player.getUniqueId(), 0L) < STEP_COOLDOWN_MS) {
            return;
        }
        String id = BlockStorage.checkID(under);
        if (CHIMING.equals(id)) {
            lastStep.put(player.getUniqueId(), now);
            chime(under);
        } else if (TIDAL.equals(id)) {
            lastStep.put(player.getUniqueId(), now);
            splash(under);
        } else if (RESIN.equals(id)) {
            lastStep.put(player.getUniqueId(), now);
            amber(under);
        }
    }

    private static void chime(Block tile) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        var top = tile.getLocation().add(0.5, 1.05, 0.5);
        tile.getWorld().playSound(top, Sound.BLOCK_AMETHYST_BLOCK_CHIME, 0.6F, PENTATONIC[random.nextInt(PENTATONIC.length)]);
        tile.getWorld().spawnParticle(Particle.DUST, top, 4, 0.3, 0.05, 0.3, 0, new Particle.DustOptions(Color.fromRGB(200, 140, 255), 0.7F));
        tile.getWorld().spawnParticle(Particle.END_ROD, top, 1, 0.2, 0.1, 0.2, 0.01);
    }

    private static void splash(Block tile) {
        var top = tile.getLocation().add(0.5, 1.05, 0.5);
        tile.getWorld().playSound(top, Sound.BLOCK_BUBBLE_COLUMN_BUBBLE_POP, 0.7F, 1.2F);
        tile.getWorld().spawnParticle(Particle.SPLASH, top, 8, 0.3, 0.05, 0.3, 0.1);
        tile.getWorld().spawnParticle(Particle.BUBBLE_POP, top, 3, 0.3, 0.1, 0.3, 0.02);
    }

    private static void amber(Block tile) {
        var top = tile.getLocation().add(0.5, 1.05, 0.5);
        tile.getWorld().playSound(top, Sound.BLOCK_HONEY_BLOCK_STEP, 0.6F, 0.8F);
        tile.getWorld().spawnParticle(Particle.DUST, top, 4, 0.3, 0.05, 0.3, 0, new Particle.DustOptions(Color.fromRGB(230, 130, 30), 0.8F));
        tile.getWorld().spawnParticle(Particle.FALLING_HONEY, top.clone().add(0, 0.6, 0), 2, 0.3, 0.1, 0.3, 0);
    }

    /** Coral dries out when no water touches it; ours never does. */
    @EventHandler(ignoreCancelled = true)
    public void onDry(BlockFadeEvent e) {
        Material type = e.getBlock().getType();
        if ((Tag.CORALS.isTagged(type) || CORAL_BLOCKS.contains(type)) && NEVER_DRY.contains(BlockStorage.checkID(e.getBlock()))) {
            e.setCancelled(true);
        }
    }

    /** Breaking the block under a decorative flower: drop the Occultech item and clear the flower cleanly. */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onSupportBroken(BlockBreakEvent e) {
        Block above = e.getBlock().getRelative(BlockFace.UP);
        String id = BlockStorage.checkID(above);
        if (id == null || !FLOWERS.contains(id)) {
            return;
        }
        SlimefunItem item = SlimefunItem.getById(id);
        decorations.remove(above);
        BlockStorage.clearBlockInfo(above);
        above.setType(Material.AIR, false);
        if (item != null) {
            ItemStack drop = item.getItem().clone();
            drop.setAmount(1);
            above.getWorld().dropItemNaturally(above.getLocation().add(0.5, 0.3, 0.5), drop);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onIgnite(org.bukkit.event.block.BlockIgniteEvent e) {
        Block below = e.getBlock().getRelative(BlockFace.DOWN);
        if (!PRISMATIC.equals(BlockStorage.checkID(below)) || !decorations.coloredFire()) {
            return;
        }
        e.setCancelled(true);
        if (decorations.lightPrismatic(below)) {
            below.getWorld().playSound(e.getBlock().getLocation().add(0.5, 0.5, 0.5), Sound.ITEM_FLINTANDSTEEL_USE, 1F, 1F);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onPunchFire(org.bukkit.event.player.PlayerInteractEvent e) {
        Block block = e.getClickedBlock();
        if (e.getAction() != org.bukkit.event.block.Action.LEFT_CLICK_BLOCK || block == null || e.getBlockFace() != BlockFace.UP
            || !DecorationService.prismaticLit(block) || !PRISMATIC.equals(BlockStorage.checkID(block))) {
            return;
        }
        e.setCancelled(true);
        decorations.extinguishPrismatic(block);
        block.getWorld().playSound(block.getLocation().add(0.5, 1.2, 0.5), Sound.BLOCK_FIRE_EXTINGUISH, 0.7F, 1.2F);
    }

    /** Trophy models are real (tiny, frozen) mobs: they must never burn in daylight. */
    @EventHandler(ignoreCancelled = true)
    public void onCombust(org.bukkit.event.entity.EntityCombustEvent e) {
        if (e.getEntity().getPersistentDataContainer().has(io.github.amitelia.occultech.core.Keys.HOLOGRAM)) {
            e.setCancelled(true);
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        lastStep.remove(e.getPlayer().getUniqueId());
    }
}
