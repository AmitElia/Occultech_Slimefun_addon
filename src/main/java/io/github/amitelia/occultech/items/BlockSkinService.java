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
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockBurnEvent;
import org.bukkit.event.block.BlockExplodeEvent;
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
 */
public final class BlockSkinService implements Listener {

    public static final NamespacedKey SKIN = new NamespacedKey("occultech", "skin");
    private static final float SCALE = 1.004F;

    private final JavaPlugin plugin;
    private final ResourcePackService pack;
    private final Map<String, UUID> tracked = new HashMap<>();   // "world|x,y,z" -> display

    public BlockSkinService(@Nonnull JavaPlugin plugin, @Nonnull ResourcePackService pack) {
        this.plugin = plugin;
        this.pack = pack;
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
        return slimefunId != null && pack.skinVariants(stripPrefix(slimefunId)) > 0;
    }

    /** Puts the skin on a placed Occultech block if it should have one and doesn't yet. Returns the display, or null. */
    @Nullable
    public ItemDisplay ensure(@Nonnull Block block) {
        return ensure(block, BlockStorage.checkID(block));
    }

    /** As {@link #ensure(Block)}, for a block known to be {@code id} (just placed: Slimefun may not have stored it yet). */
    @Nullable
    public ItemDisplay ensure(@Nonnull Block block, @Nullable String id) {
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
        Transformation transformation = new Transformation(new Vector3f(0F, -0.5F, 0F), new AxisAngle4f(yaw(block), 0F, 1F, 0F),
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
                return display;
            }
            display.remove();   // the block changed into another Occultech block (an altar upgrade)
        }
        Location at = block.getLocation().add(0.5, 1.0, 0.5);
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
                    if (isSkinned(BlockStorage.checkID(block)) && !tracked.containsKey(key(block)) && ensure(block) != null) {
                        made++;
                    }
                }
            }
        }
        return made;
    }

    /** A player placed a block: skin it now, from the item in hand (the same tick the block appears). */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPlace(BlockPlaceEvent event) {
        SlimefunItem item = SlimefunItem.getByItem(event.getItemInHand());
        if (item != null && isSkinned(item.getId())) {
            ensure(event.getBlockPlaced(), item.getId());
        }
    }

    /** Slimefun placed one (a Block Placer, or after a player's placement): same, idempotent. */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onSlimefunPlace(SlimefunBlockPlaceEvent event) {
        if (isSkinned(event.getSlimefunItem().getId())) {
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

    private void adopt(Entity entity) {
        String data = entity.getPersistentDataContainer().get(SKIN, PersistentDataType.STRING);
        if (data == null || !(entity instanceof ItemDisplay)) {
            return;
        }
        Block block = blockOf(entity.getWorld(), data);
        if (block == null) {
            entity.remove();
            return;
        }
        UUID previous = tracked.put(key(block), entity.getUniqueId());
        if (previous != null && !previous.equals(entity.getUniqueId()) && Bukkit.getEntity(previous) != null) {
            entity.remove();   // a duplicate: keep the one we had
            tracked.put(key(block), previous);
        }
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

    private static String stripPrefix(String slimefunId) {
        return slimefunId.startsWith("OCCULTECH_") ? slimefunId.substring("OCCULTECH_".length()) : slimefunId;
    }

    /** Chunk helper for callers that rebuild an area (the showcase). */
    public static boolean loaded(Chunk chunk) {
        return chunk.isLoaded();
    }
}
