package io.github.amitelia.occultech.items;

import io.github.amitelia.occultech.pack.ResourcePackService;
import io.github.thebusybiscuit.slimefun4.api.events.SlimefunBlockPlaceEvent;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import org.bukkit.Bukkit;
import org.bukkit.Chunk;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.data.Directional;
import org.bukkit.Axis;
import org.bukkit.block.data.BlockData;
import org.bukkit.block.data.Orientable;
import org.bukkit.block.data.type.Lantern;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockBurnEvent;
import org.bukkit.event.block.BlockExplodeEvent;
import org.bukkit.event.block.BlockFormEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.EntityExplodeEvent;
import org.bukkit.event.world.EntitiesLoadEvent;
import org.bukkit.event.world.EntitiesUnloadEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Block skins: a placed Occultech block keeps its vanilla block (Slimefun's), and an item display shows Occultech's own
 * model over it - a hair larger, so the vanilla block is hidden and nothing vanilla is ever retextured. Displays have no
 * hitbox, so clicks and breaking still reach the real block.
 *
 * <p>The display stands on top of the block (so it is lit by the air above, not darkened inside the block) and its
 * model is shifted down into the block. It is tagged with {@link #SKIN} ({@code "x,y,z|ITEM_ID"}) and saved with the
 * chunk; on load it is tracked again. A skin comes and goes in the same tick as its block: it is put on when the
 * block is placed (from the placed item, without waiting for Slimefun's storage) and taken off when the block is
 * broken, burnt or blown up. A sweep every second catches anything else (a block replaced by a plugin): a skin is
 * removed when its block's type no longer matches the item's - never merely because Slimefun's data for the chunk
 * isn't loaded yet.
 *
 * <p>A block with a front (a horizontal {@link Directional}, like the Occult Forge's blast furnace) turns its skin so
 * the model's north face is its front. A tile that swaps its vanilla block ({@link StepTile} looks) shows the skin
 * variant for its current block.
 *
 * <p><b>Custom blocks (Session N).</b> When {@link CustomBlockService} is on, blocks are real custom blocks and this
 * service only bridges: {@link #ensure} and {@link #ensureIfMissing} make the block its custom block, and a skin left in
 * the world from before is converted - its block becomes the custom block (keeping its look) and the display goes.
 */
public final class BlockSkinService implements Listener {

    public static final NamespacedKey SKIN = new NamespacedKey("occultech", "skin");
    private static final float SCALE = 1.004F;

    private final JavaPlugin plugin;
    private final ResourcePackService pack;
    private final Map<String, UUID> tracked = new HashMap<>();   // "world|x,y,z" -> display
    private final CustomBlockService blocks;

    public BlockSkinService(@Nonnull JavaPlugin plugin, @Nonnull ResourcePackService pack, @Nonnull CustomBlockService blocks) {
        this.plugin = plugin;
        this.pack = pack;
        this.blocks = blocks;
    }

    /** The custom blocks (Session N); when they're on, skins only remain to be converted. */
    @Nonnull
    public CustomBlockService blocks() {
        return blocks;
    }

    public void start() {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        for (World world : Bukkit.getWorlds()) {
            world.getEntitiesByClass(ItemDisplay.class).forEach(this::adopt);
        }
        Bukkit.getScheduler().runTaskTimer(plugin, this::validate, 20L, 20L);
    }

    /** Whether Occultech has a skin for this Slimefun item id. */
    public boolean isSkinned(@Nullable String slimefunId) {
        return slimefunId != null && (blocks.enabled() ? blocks.isCustom(slimefunId) : pack.skinVariants(stripPrefix(slimefunId)) > 0);
    }

    /** Puts the skin on a placed Occultech block if it should have one and doesn't yet. Returns the display, or null. */
    @Nullable
    public ItemDisplay ensure(@Nonnull Block block) {
        return ensure(block, BlockStorage.checkID(block));
    }

    /** As {@link #ensure(Block)}, for a block known to be {@code id} (just placed: Slimefun may not have stored it yet). */
    @Nullable
    public ItemDisplay ensure(@Nonnull Block block, @Nullable String id) {
        if (blocks.enabled()) {
            blocks.ensure(block, id);   // a custom block: nothing to display
            return null;
        }
        if (!isSkinned(id)) {
            return null;
        }
        NamespacedKey model = modelFor(block, id);
        if (model == null) {
            return null;
        }
        ItemStack stack = new ItemStack(Material.PAPER);
        ItemMeta meta = stack.getItemMeta();
        meta.setItemModel(model);
        stack.setItemMeta(meta);
        // A display is lit by the light where it stands. Inside a block that lets light through (a chain, a pot, a lantern,
        // a carpet) that's the block itself; inside a solid cube it's dark, so a solid block's skin stands just above it.
        // (Standing above put a Wind Chime hung under a ceiling inside the ceiling - pitch black.)
        boolean solid = block.getType().isOccluding();
        Location at = block.getLocation().add(0.5, solid ? 1.0 : 0.5, 0.5);
        Transformation transformation = new Transformation(new Vector3f(0F, solid ? -0.5F : 0F, 0F), new AxisAngle4f(yaw(block), 0F, 1F, 0F),
            new Vector3f(SCALE, SCALE, SCALE), new AxisAngle4f());
        String key = key(block);
        UUID existing = tracked.get(key);
        if (existing != null && Bukkit.getEntity(existing) instanceof ItemDisplay display && display.isValid()) {
            if (id.equals(skinOf(display))) {
                ItemStack shown = display.getItemStack();
                if (shown.getItemMeta() == null || !model.equals(shown.getItemMeta().getItemModel())) {
                    display.setItemStack(stack);   // a tile changed its look
                }
                display.setTransformation(transformation);
                if (Math.abs(display.getLocation().getY() - at.getY()) > 1e-3) {
                    display.teleport(at);   // skins made before they were anchored by their block's light
                }
                return display;
            }
            display.remove();   // the block changed into another Occultech block (an altar upgrade)
        }
        ItemDisplay display = block.getWorld().spawn(at, ItemDisplay.class, d -> {
            d.setItemStack(stack);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setTransformation(transformation);
            d.setShadowRadius(0F);
            d.setPersistent(true);
            d.getPersistentDataContainer().set(SKIN, PersistentDataType.STRING,
                block.getX() + "," + block.getY() + "," + block.getZ() + "|" + id);
        });
        tracked.put(key, display.getUniqueId());
        return display;
    }

    /** Skins every skinnable Occultech block within {@code radius} of a location (for blocks placed before skins existed). */
    public int ensureAround(@Nonnull Location center, int radius) {
        int made = 0;
        World world = center.getWorld();
        for (int x = -radius; x <= radius; x++) {
            for (int z = -radius; z <= radius; z++) {
                for (int y = -radius / 2; y <= radius / 2; y++) {
                    Block block = world.getBlockAt(center.getBlockX() + x, center.getBlockY() + y, center.getBlockZ() + z);
                    if (block.getType().isAir() || !world.isChunkLoaded(block.getX() >> 4, block.getZ() >> 4)) {
                        continue;
                    }
                    String id = BlockStorage.checkID(block);
                    if (blocks.enabled()) {
                        if (blocks.isCustom(id) && !blocks.isCustomState(block)) {
                            blocks.ensure(block, id);
                            made++;
                        }
                    } else if (isSkinned(id) && !tracked.containsKey(key(block)) && ensure(block) != null) {
                        made++;
                    }
                }
            }
        }
        return made;
    }

    /** A player placed a block: skin it now, from the item in hand (the same tick the block appears). */
    /** A skinned decoration on a soul lantern (the Soulfire Brazier) must stand: its skin has no hanging version. */
    @EventHandler(priority = EventPriority.LOW, ignoreCancelled = true)
    public void onPlaceHanging(BlockPlaceEvent event) {
        if (blocks.enabled() || event.getBlockPlaced().getType() != Material.SOUL_LANTERN
            || !(event.getBlockPlaced().getBlockData() instanceof Lantern lantern) || !lantern.isHanging()) {
            return;
        }
        SlimefunItem item = SlimefunItem.getByItem(event.getItemInHand());
        if (item != null && isSkinned(item.getId())) {
            event.setCancelled(true);
            event.getPlayer().sendActionBar(Component.text(item.getItemName().replaceAll("§.", "") + " must stand on a block",
                NamedTextColor.GRAY));
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPlace(BlockPlaceEvent event) {
        SlimefunItem item = SlimefunItem.getByItem(event.getItemInHand());
        if (!blocks.enabled() && item != null && isSkinned(item.getId())) {
            upright(event.getBlockPlaced());
            ensure(event.getBlockPlaced(), item.getId());
        }
    }

    /**
     * Stands a skinned block's interim vanilla block upright when it was placed sideways: a chain (Wind Chime) along y,
     * a lightning rod (Occult Orrery) facing up - their skins are upright objects. Neither needs support, so nothing
     * pops off. Other blocks are left as placed.
     */
    public static void upright(@Nonnull Block block) {
        BlockData data = block.getBlockData();
        if (block.getType() == Material.IRON_CHAIN && data instanceof Orientable chain && chain.getAxis() != Axis.Y) {
            chain.setAxis(Axis.Y);
            block.setBlockData(chain, false);
        } else if (block.getType() == Material.LIGHTNING_ROD && data instanceof Directional rod && rod.getFacing() != BlockFace.UP) {
            rod.setFacing(BlockFace.UP);
            block.setBlockData(rod, false);
        }
    }

    /** Slimefun placed one (a Block Placer, or after a player's placement): same, idempotent. */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onSlimefunPlace(SlimefunBlockPlaceEvent event) {
        if (!blocks.enabled() && isSkinned(event.getSlimefunItem().getId())) {
            ensure(event.getBlockPlaced(), event.getSlimefunItem().getId());
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onBreak(BlockBreakEvent event) {
        remove(event.getBlock());
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onBurn(BlockBurnEvent event) {
        remove(event.getBlock());
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onExplode(BlockExplodeEvent event) {
        event.blockList().forEach(this::remove);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onExplode(EntityExplodeEvent event) {
        event.blockList().forEach(this::remove);
    }

    /** Takes a block's skin off now (its block is going). */
    public void remove(@Nonnull Block block) {
        if (tracked.isEmpty()) {
            return;
        }
        UUID id = tracked.remove(key(block));
        Entity display = id == null ? null : Bukkit.getEntity(id);
        if (display != null) {
            display.remove();
        }
    }

    @EventHandler
    public void onEntitiesLoad(EntitiesLoadEvent event) {
        event.getEntities().forEach(this::adopt);
    }

    @EventHandler
    public void onEntitiesUnload(EntitiesUnloadEvent event) {
        for (Entity entity : event.getEntities()) {
            String data = entity.getPersistentDataContainer().get(SKIN, PersistentDataType.STRING);
            if (data != null) {
                tracked.values().remove(entity.getUniqueId());
            }
        }
    }

    /** Tracks a skin display found in the world - or, with custom blocks on, converts its block and removes it. */
    public void adopt(Entity entity) {
        String data = entity.getPersistentDataContainer().get(SKIN, PersistentDataType.STRING);
        if (data == null || !(entity instanceof ItemDisplay)) {
            return;
        }
        Block block = blockOf(entity.getWorld(), data);
        if (block == null) {
            entity.remove();
            return;
        }
        if (blocks.enabled()) {
            // a skin from before custom blocks: its block becomes the custom block, keeping the look it showed
            String id = data.substring(data.indexOf('|') + 1);
            Runnable convert = () -> {
                SlimefunItem item = SlimefunItem.getById(id);
                if (id.equals(BlockStorage.checkID(block)) && item != null && (item instanceof StepTile || restoreWeathered(block, item))) {
                    blocks.ensure(block, id);
                }
                entity.remove();
            };
            if (BlockStorage.hasBlockInfo(block)) {
                convert.run();
            } else {
                Bukkit.getScheduler().runTask(plugin, convert);   // Slimefun's data for a freshly loaded chunk may lag a tick
            }
            return;
        }
        UUID previous = tracked.put(key(block), entity.getUniqueId());
        if (previous != null && !previous.equals(entity.getUniqueId()) && Bukkit.getEntity(previous) != null) {
            entity.remove();   // a duplicate: keep the one we had
            tracked.put(key(block), previous);
        }
    }

    /**
     * Copper weathering (a lightning rod turning exposed, weathered, oxidized) would change an Occultech block's type
     * and so cost it its skin: Occultech blocks don't weather.
     */
    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onWeather(BlockFormEvent event) {
        if (event.getBlock().getType() != event.getNewState().getType() && isSkinned(BlockStorage.checkID(event.getBlock()))) {
            event.setCancelled(true);
        }
    }

    /**
     * Puts a skinned block back to its item's own block when it became a weathered or waxed variant of it (an Occult
     * Orrery's lightning rod that oxidized before weathering was stopped), keeping its state (facing, water).
     * Returns whether the block is (now) the item's own type.
     */
    public static boolean restoreWeathered(@Nonnull Block block, @Nonnull SlimefunItem item) {
        Material own = item.getItem().getType();
        Material now = block.getType();
        if (now == own) {
            return true;
        }
        String ownName = own.name();
        if (!now.name().endsWith(ownName) || !(now.name().startsWith("WAXED_") || now.name().startsWith("EXPOSED_")
            || now.name().startsWith("WEATHERED_") || now.name().startsWith("OXIDIZED_"))) {
            return false;
        }
        String state = block.getBlockData().getAsString();
        block.setBlockData(Bukkit.createBlockData(state.replace(now.getKey().toString(), own.getKey().toString())), false);
        return block.getType() == own;
    }

    /** Cheap per-tick check for a block's ticker: re-skins it only if its skin is missing (a block placed before
     * skins, a skin lost to a type change). */
    public void ensureIfMissing(@Nonnull Block block, @Nonnull SlimefunItem item) {
        if (blocks.enabled()) {
            blocks.ensure(block, item.getId());   // also restores a block whose state was changed
            return;
        }
        if (!isSkinned(item.getId()) || !restoreWeathered(block, item)) {
            return;   // the rod goes back first, whether or not the skin is still there
        }
        UUID existing = tracked.get(key(block));
        if (existing != null && Bukkit.getEntity(existing) instanceof ItemDisplay display && display.isValid()
            && Math.abs(display.getLocation().getY() - block.getY() - (block.getType().isOccluding() ? 1.0 : 0.5)) < 1e-3) {
            return;
        }
        ensure(block, item.getId());   // missing, or standing where its block's light doesn't reach
    }

    /** Removes skins whose block is really gone (its type no longer the item's). */
    public void validate() {
        tracked.entrySet().removeIf(entry -> {
            Entity entity = Bukkit.getEntity(entry.getValue());
            if (entity == null) {
                return false;   // its chunk isn't loaded; checked again when it is
            }
            String data = entity.getPersistentDataContainer().get(SKIN, PersistentDataType.STRING);
            Block block = data == null ? null : blockOf(entity.getWorld(), data);
            String id = data == null ? null : data.substring(data.indexOf('|') + 1);
            SlimefunItem item = id == null ? null : SlimefunItem.getById(id);
            if (block != null && item != null && !(item instanceof StepTile) && BlockStorage.hasBlockInfo(block)
                && id.equals(BlockStorage.checkID(block))) {
                restoreWeathered(block, item);   // a weathered rod is still the orrery
            }
            boolean gone = block == null || item == null || !isLook(item, block.getType())
                || (BlockStorage.hasBlockInfo(block) && !id.equals(BlockStorage.checkID(block)));
            if (gone) {
                entity.remove();
            }
            return gone;
        });
    }

    /** The model for this block: its look's variant (tiles), else a variant picked by position. Null: no skin. */
    @Nullable
    private NamespacedKey modelFor(Block block, String id) {
        String item = stripPrefix(id);
        int variants = pack.skinVariants(item);
        int variant;
        if (SlimefunItem.getById(id) instanceof StepTile tile) {
            variant = tile.lookVariant(block.getType());
            if (variant < 0 || variant >= variants) {
                return null;
            }
        } else {
            variant = variants <= 1 ? 0 : Math.floorMod(block.getX() * 31 + block.getZ() * 17 + block.getY() * 7, variants);
        }
        return new NamespacedKey(ResourcePackService.NAMESPACE, item.toLowerCase(java.util.Locale.ROOT) + (variant == 0 ? "" : "_v" + variant));
    }

    /** Whether a block of this type can still be this item (a tile may have swapped to another of its looks). */
    private static boolean isLook(SlimefunItem item, Material type) {
        return item instanceof StepTile tile ? tile.lookVariant(type) >= 0 : type == item.getItem().getType();
    }

    /**
     * The skin's turn about the vertical axis so the model's north face is the block's front. Item displays draw a
     * model turned half a turn from a placed block, which the base angle undoes.
     */
    static float yaw(Block block) {
        if (!(block.getBlockData() instanceof Directional directional)) {
            return 0F;
        }
        float half = (float) Math.PI;
        return switch (directional.getFacing()) {
            case EAST -> half - half / 2;
            case SOUTH -> 0F;
            case WEST -> half + half / 2;
            default -> directional.getFacing() == BlockFace.NORTH ? half : 0F;
        };
    }

    public int count() {
        return tracked.size();
    }

    @Nullable
    private static String skinOf(Entity display) {
        String data = display.getPersistentDataContainer().get(SKIN, PersistentDataType.STRING);
        return data == null ? null : data.substring(data.indexOf('|') + 1);
    }

    @Nullable
    private static Block blockOf(World world, String data) {
        try {
            String[] xyz = data.substring(0, data.indexOf('|')).split(",");
            return world.getBlockAt(Integer.parseInt(xyz[0]), Integer.parseInt(xyz[1]), Integer.parseInt(xyz[2]));
        } catch (RuntimeException e) {
            return null;
        }
    }

    private static String key(Block block) {
        return block.getWorld().getName() + "|" + block.getX() + "," + block.getY() + "," + block.getZ();
    }

    static String stripPrefix(String slimefunId) {
        return slimefunId.startsWith("OCCULTECH_") ? slimefunId.substring("OCCULTECH_".length()) : slimefunId;
    }

    /** Chunk helper for callers that rebuild an area (the showcase). */
    public static boolean loaded(Chunk chunk) {
        return chunk.isLoaded();
    }
}
