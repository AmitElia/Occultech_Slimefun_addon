package io.github.amitelia.occultech.boss;

import io.papermc.paper.datacomponent.DataComponentTypes;
import io.papermc.paper.datacomponent.item.DyedItemColor;
import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.util.Locale;

/**
 * Floor markings for boss fights (Session O4): flat floor holograms like the ritual sigils - item displays with flat
 * models from the resource pack, scaled to the effect's radius, animated by the client (interpolated transformations),
 * never saved, removed with the fight.
 *
 * <ul>
 * <li>{@link #warning}: where an attack will land - a ring at the exact hit radius, a fill growing from the centre to
 * the edge over the warning (when it's full, the hit lands), the attack's {@link Mark} in the middle; tinted to the
 * attack's colour.</li>
 * <li>{@link #zone}: a ground zone that hurts while you stand in it - an animated surface of its {@link Zone}.</li>
 * </ul>
 * Without the pack (see {@link #enable}) fights keep their particle clouds.
 */
public final class FloorDecals {

    /** The symbol in the middle of an attack warning. */
    public enum Mark { SLAM, DIVE, WEB, FLAME, STORM, SPIKES, WIND, ROOTS, SWEEP, DANGER }

    /** A ground zone's surface. Acid and fire glow. */
    public enum Zone {
        ACID(true), WEB(false), YOLK(false), FIRE(true), POISON(false), FROST(false), SHADOW(false);

        final boolean glows;

        Zone(boolean glows) {
            this.glows = glows;
        }
    }

    private static final double WARNING_HEIGHT = 0.03;
    private static final double ZONE_HEIGHT = 0.02;
    private static final int UNFOLD = 6;
    @Nullable private static Plugin plugin;
    private static boolean enabled;

    private FloorDecals() {}

    /** Called at startup: markings are drawn when the resource pack (with their models) is in use. */
    public static void enable(@Nonnull Plugin owner, boolean on) {
        plugin = owner;
        enabled = on;
    }

    public static boolean enabled() {
        return enabled && plugin != null;
    }

    /** An attack warning at {@code at} (the floor under the hit), {@code radius} blocks, landing in {@code ticks}. */
    static void warning(@Nonnull BossFight fight, @Nonnull Location at, double radius, int ticks, @Nonnull Color color, @Nonnull Mark mark) {
        Color tint = visible(color);
        float across = (float) (radius * 2);
        ItemDisplay fill = decal(fight, at.clone().add(0, WARNING_HEIGHT, 0), "floor_warning_fill", tint, true, 0.01F);
        ItemDisplay ring = decal(fight, at.clone().add(0, WARNING_HEIGHT + 0.01, 0), "floor_warning_ring", tint, true, across * 0.6F);
        ItemDisplay symbol = decal(fight, at.clone().add(0, WARNING_HEIGHT + 0.02, 0),
            "floor_mark_" + mark.name().toLowerCase(Locale.ROOT), tint, true, 0.01F);
        float symbolSize = (float) Math.min(1.8, Math.max(0.9, radius * 0.7));
        later(2, () -> {
            grow(ring, across, UNFOLD);                       // the ring snaps out to the hit's edge
            grow(symbol, symbolSize, UNFOLD);
            grow(fill, across, Math.max(1, ticks - 2));       // the fill reaches the edge as the hit lands
        });
        later(ticks + 2, () -> {
            fill.remove();
            ring.remove();
            symbol.remove();
        });
    }

    /** A ground zone at {@code at}, {@code radius} blocks, lasting {@code ticks}; returns its display (the fight removes it). */
    static ItemDisplay zone(@Nonnull BossFight fight, @Nonnull Location at, double radius, int ticks, @Nonnull Zone zone) {
        float across = (float) (radius * 2);
        ItemDisplay surface = decal(fight, at.clone().add(0, ZONE_HEIGHT, 0), "floor_zone_" + zone.name().toLowerCase(Locale.ROOT),
            null, zone.glows, 0.01F);
        later(2, () -> grow(surface, across, UNFOLD));
        later(Math.max(3, ticks - UNFOLD), () -> grow(surface, 0.01F, UNFOLD));   // it shrinks away as it ends
        return surface;
    }

    private static ItemDisplay decal(BossFight fight, Location at, String model, @Nullable Color tint, boolean glows, float size) {
        ItemStack stack = new ItemStack(Material.PAPER);
        ItemMeta meta = stack.getItemMeta();
        meta.setItemModel(new NamespacedKey("occultech", model));
        stack.setItemMeta(meta);
        if (tint != null) {
            stack.setData(DataComponentTypes.DYED_COLOR, DyedItemColor.dyedItemColor(tint));
        }
        return fight.spawnExtra(ItemDisplay.class, at, d -> {
            d.setItemStack(stack);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setShadowRadius(0F);
            d.setViewRange(2F);
            if (glows) {
                d.setBrightness(new Display.Brightness(15, 15));
            }
            d.setTransformation(scaled(size));
        });
    }

    private static void grow(ItemDisplay display, float size, int ticks) {
        if (!display.isValid()) {
            return;
        }
        display.setInterpolationDelay(0);
        display.setInterpolationDuration(ticks);
        display.setTransformation(scaled(size));
    }

    private static Transformation scaled(float size) {
        return new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(size, 1F, size), new AxisAngle4f());
    }

    /** Very dark attack colours (the Hollow Warlord's near-black sweep) are lifted so the tinted warning still shows. */
    static Color visible(Color color) {
        int max = Math.max(color.getRed(), Math.max(color.getGreen(), color.getBlue()));
        if (max >= 140) {
            return color;
        }
        double k = 140.0 / Math.max(1, max);
        return Color.fromRGB(Math.min(255, (int) (Math.max(30, color.getRed()) * k)), Math.min(255, (int) (Math.max(30, color.getGreen()) * k)),
            Math.min(255, (int) (Math.max(30, color.getBlue()) * k)));
    }

    private static void later(long ticks, Runnable task) {
        if (plugin != null) {
            Bukkit.getScheduler().runTaskLater(plugin, task, ticks);
        }
    }
}
