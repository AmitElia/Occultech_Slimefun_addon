package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.TextDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.core.Keys;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * Floating item + label above a block (offering bowls, altars, the Brood Egg).
 * <p>
 * The displays are not saved with the world: they are recreated by the block's ticker, and a sweep removes any whose
 * block is gone. So a restart or chunk unload never leaves stray holograms behind.
 */
public final class Holograms {

    private static final float ITEM_SCALE = 0.55F;
    private static final float SPIN_STEP = 0.4F;
    private static final int SPIN_TICKS = 12;

    private record Hologram(ItemDisplay item, TextDisplay text) {

        boolean isValid() {
            return item.isValid() && text.isValid();
        }

        void remove() {
            item.remove();
            text.remove();
        }
    }

    private final Map<Location, Hologram> holograms = new HashMap<>();
    private float angle;

    public Holograms(Plugin plugin) {
        Bukkit.getScheduler().runTaskTimer(plugin, this::sweep, 100L, 100L);
        Bukkit.getScheduler().runTaskTimer(plugin, () -> angle += SPIN_STEP, SPIN_TICKS, SPIN_TICKS);
    }

    /**
     * Shows (or updates) the hologram above a block.
     *
     * @param item shown spinning above the block, or null for none
     * @param text label above the item (color codes allowed), or null for none
     */
    public void show(Block block, @Nullable ItemStack item, @Nullable String text) {
        Location key = block.getLocation();
        Hologram hologram = holograms.get(key);
        if (hologram == null || !hologram.isValid()) {
            if (hologram != null) {
                hologram.remove();
            }
            hologram = create(block);
            holograms.put(key, hologram);
        }

        ItemStack shown = item == null || item.getType().isAir() ? new ItemStack(Material.AIR) : single(item);
        if (!shown.equals(hologram.item().getItemStack())) {
            hologram.item().setItemStack(shown);
        }
        hologram.item().setInterpolationDelay(0);
        hologram.item().setInterpolationDuration(SPIN_TICKS);
        hologram.item().setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(angle, 0, 1, 0),
            new Vector3f(ITEM_SCALE, ITEM_SCALE, ITEM_SCALE), new AxisAngle4f()));

        String label = text == null ? "" : MenuUtils.color(text);
        if (!label.equals(hologram.text().getText())) {
            hologram.text().setText(label);
        }
    }

    public void clear(Block block) {
        Hologram hologram = holograms.remove(block.getLocation());
        if (hologram != null) {
            hologram.remove();
        }
    }

    public void clearAll() {
        holograms.values().forEach(Hologram::remove);
        holograms.clear();
    }

    /** A readable name for an item: its display name, or the material name. */
    public static String nameOf(ItemStack item) {
        ItemMeta meta = item.getItemMeta();
        if (meta != null && meta.hasDisplayName()) {
            return meta.getDisplayName();
        }
        String name = item.getType().name().toLowerCase().replace('_', ' ');
        return Character.toUpperCase(name.charAt(0)) + name.substring(1);
    }

    private Hologram create(Block block) {
        // float just above what is there: a full block (an altar) or a low bowl (a carpet under its skin)
        double top = org.bukkit.Tag.WOOL_CARPETS.isTagged(block.getType()) ? 0.35 : 1.0;
        Location base = block.getLocation().add(0.5, top - 1.0, 0.5);
        ItemDisplay item = block.getWorld().spawn(base.clone().add(0, 1.35, 0), ItemDisplay.class, d -> {
            d.setPersistent(false);
            d.setBillboard(Display.Billboard.FIXED);
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
        TextDisplay text = block.getWorld().spawn(base.clone().add(0, 1.85, 0), TextDisplay.class, d -> {
            d.setPersistent(false);
            d.setBillboard(Display.Billboard.CENTER);
            d.setShadowed(true);
            d.setBackgroundColor(Color.fromARGB(90, 0, 0, 0));
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
        return new Hologram(item, text);
    }

    private void sweep() {
        Iterator<Map.Entry<Location, Hologram>> it = holograms.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<Location, Hologram> entry = it.next();
            Location at = entry.getKey();
            boolean blockGone = !at.isChunkLoaded() || BlockStorage.checkID(at) == null;
            if (blockGone || !entry.getValue().isValid()) {
                entry.getValue().remove();
                it.remove();
            }
        }
    }

    private static ItemStack single(ItemStack item) {
        ItemStack copy = item.clone();
        copy.setAmount(1);
        return copy;
    }
}
