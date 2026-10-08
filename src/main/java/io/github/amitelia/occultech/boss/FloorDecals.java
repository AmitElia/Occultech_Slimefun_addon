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
import org.bukkit.util.Vector;
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
    public enum Mark { SLAM, DIVE, WEB, FLAME, STORM, SPIKES, WIND, ROOTS, SWEEP, CURSE, DANGER, SOAK, TARGET }

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

    /**
     * An attack warning at {@code at} (on the floor under the hit), {@code radius} blocks, landing in {@code ticks}:
     * the ring, the fill growing to it, and the {@code mark} in the middle (none: a small warning, e.g. one fang).
     */
    static void warning(@Nonnull BossFight fight, @Nonnull Location at, double radius, int ticks, @Nonnull Color color, @Nullable Mark mark) {
        Color tint = visible(color);
        float across = (float) (radius * 2);
        Location floor = floor(at);
        ItemDisplay fill = decal(fight, floor.clone().add(0, WARNING_HEIGHT, 0), "floor_warning_fill", tint, true, 0.01F);
        ItemDisplay ring = decal(fight, floor.clone().add(0, WARNING_HEIGHT + 0.01, 0), "floor_warning_ring", tint, true, across * 0.6F);
        ItemDisplay symbol = mark == null ? null : decal(fight, floor.clone().add(0, WARNING_HEIGHT + 0.02, 0),
            "floor_mark_" + mark.name().toLowerCase(Locale.ROOT), tint, true, 0.01F);
        float symbolSize = (float) Math.min(1.8, Math.max(0.9, radius * 0.7));
        later(2, () -> {
            grow(ring, across, UNFOLD);                       // the ring snaps out to the hit's edge
            if (symbol != null) {
                grow(symbol, symbolSize, UNFOLD);
            }
            grow(fill, across, Math.max(1, ticks - 2));       // the fill reaches the edge as the hit lands
        });
        later(ticks + 2, () -> remove(fill, ring, symbol));
    }

    /** A wedge from {@code origin} along {@code direction}, {@code range} long and 90 degrees wide (a cleave). */
    public static void wedge(@Nonnull BossFight fight, @Nonnull Location origin, @Nonnull Vector direction, double range, int ticks,
        @Nonnull Color color) {
        aimed(fight, origin, direction, range, range, ticks, color, "floor_warning_wedge");
    }

    /** The sector warnings the pack has (degrees): a fan uses the smallest that covers it. */
    private static final int[] SECTOR_ARCS = { 60, 70, 90, 120, 150, 180 };

    /**
     * A fan-shaped warning that traces a hit exactly: centred on {@code origin}, {@code reach} blocks out, {@code arc}
     * degrees wide, centred on {@code direction}. Its outline snaps out, its fill grows from the centre to the rim as the
     * hit lands. (A {@link #wedge} is a fixed 90-degree cleave from a point; this is the true sector.)
     */
    public static void sector(@Nonnull BossFight fight, @Nonnull Location origin, @Nonnull Vector direction, double reach, double arc,
        int ticks, @Nonnull Color color) {
        if (!enabled()) {
            return;
        }
        Vector dir = direction.clone().setY(0);
        if (dir.lengthSquared() < 1e-6) {
            return;
        }
        dir.normalize();
        int model = SECTOR_ARCS[SECTOR_ARCS.length - 1];
        for (int candidate : SECTOR_ARCS) {
            if (candidate >= arc - 0.5) {
                model = candidate;
                break;
            }
        }
        float yaw = (float) Math.atan2(-dir.getX(), -dir.getZ());   // the models open toward north
        float across = (float) (reach * 2);
        Color tint = visible(color);
        Location floor = floor(origin);
        ItemDisplay outline = decal(fight, floor.clone().add(0, WARNING_HEIGHT + 0.01, 0), "floor_warning_sector" + model, tint, true, 0.01F);
        ItemDisplay fill = decal(fight, floor.clone().add(0, WARNING_HEIGHT, 0), "floor_warning_sector" + model + "_fill", tint, true, 0.01F);
        outline.setTransformation(turned(yaw, 0.01F));
        fill.setTransformation(turned(yaw, 0.01F));
        later(2, () -> {
            animate(outline, turned(yaw, across), UNFOLD);
            animate(fill, turned(yaw, across), Math.max(1, ticks - 2));
        });
        later(ticks + 2, () -> remove(outline, fill));
    }

    private static Transformation turned(float yaw, float size) {
        return new Transformation(new Vector3f(), new AxisAngle4f(yaw, 0F, 1F, 0F), new Vector3f(size, 1F, size), new AxisAngle4f());
    }

    /** A lane from {@code origin} along {@code direction}, {@code length} long and {@code width} wide (a charge). */
    public static void lane(@Nonnull BossFight fight, @Nonnull Location origin, @Nonnull Vector direction, double length, double width,
        int ticks, @Nonnull Color color) {
        aimed(fight, origin, direction, length, width, ticks, color, "floor_warning_lane");
    }

    /**
     * An outline and a fill that grows from {@code origin} outward to {@code length} (it's full as the hit lands), turned
     * to point along {@code direction}. The models point north from the middle of their south edge.
     */
    private static void aimed(BossFight fight, Location origin, Vector direction, double length, double width, int ticks, Color color,
        String model) {
        if (!enabled()) {
            return;
        }
        Vector dir = direction.clone().setY(0);
        if (dir.lengthSquared() < 1e-6) {
            return;
        }
        dir.normalize();
        float yaw = (float) Math.atan2(-dir.getX(), -dir.getZ());
        Color tint = visible(color);
        Location floor = floor(origin);
        ItemDisplay outline = decal(fight, floor.clone().add(0, WARNING_HEIGHT + 0.01, 0), model, tint, true, 0.01F);
        ItemDisplay fill = decal(fight, floor.clone().add(0, WARNING_HEIGHT, 0), model + "_fill", tint, true, 0.01F);
        outline.setTransformation(aim(dir, yaw, (float) width, 0.01F));
        fill.setTransformation(aim(dir, yaw, (float) width, 0.01F));
        later(2, () -> {
            animate(outline, aim(dir, yaw, (float) width, (float) length), UNFOLD);
            animate(fill, aim(dir, yaw, (float) width, (float) length), Math.max(1, ticks - 2));
        });
        later(ticks + 2, () -> remove(outline, fill));
    }

    /** Turned to {@code yaw}, {@code width} across and {@code length} long, its south edge's middle at the entity. */
    private static Transformation aim(Vector dir, float yaw, float width, float length) {
        Vector3f shift = new Vector3f((float) dir.getX() * length / 2, 0F, (float) dir.getZ() * length / 2);
        return new Transformation(shift, new AxisAngle4f(yaw, 0F, 1F, 0F), new Vector3f(width, 1F, length), new AxisAngle4f());
    }

    /**
     * A wave travelling over the floor from {@code fromRadius} to {@code toRadius} (outward, or closing in) over
     * {@code ticks} - a shockwave, a tidal wave, a squall. It goes when it arrives.
     */
    public static void wave(@Nonnull BossFight fight, @Nonnull Location center, double fromRadius, double toRadius, int ticks,
        @Nonnull Color color) {
        wave(fight, center, fromRadius, toRadius, ticks, color, 0);
    }

    /** As {@link #wave}, then staying where it arrived for {@code hold} more ticks (a squall that closed in). */
    public static void wave(@Nonnull BossFight fight, @Nonnull Location center, double fromRadius, double toRadius, int ticks,
        @Nonnull Color color, int hold) {
        if (!enabled()) {
            return;
        }
        ItemDisplay wave = decal(fight, floor(center).add(0, WARNING_HEIGHT, 0), "floor_wave", visible(color), true,
            (float) Math.max(0.01, fromRadius * 2));
        later(2, () -> grow(wave, (float) (toRadius * 2), Math.max(1, ticks - 2)));
        later(ticks + 2L + hold, wave::remove);
    }

    /**
     * A glowing display of the pack's {@code model} at {@code at}, tinted (or not), at its model's own size: the caller
     * shapes and moves it (the Staff Raid's walls, a marker that follows a player). Removed with the fight.
     */
    @Nonnull
    public static ItemDisplay model(@Nonnull BossFight fight, @Nonnull Location at, @Nonnull String model, @Nullable Color tint) {
        return decal(fight, at, model, tint == null ? null : visible(tint), true, 1F);
    }

    /** A floor decal of {@code model} at {@code at}, {@code size} across, glowing and tinted (a marker's ring). */
    @Nonnull
    public static ItemDisplay flat(@Nonnull BossFight fight, @Nonnull Location at, @Nonnull String model, @Nonnull Color tint, double size) {
        return decal(fight, floor(at).add(0, WARNING_HEIGHT, 0), model, visible(tint), true, (float) size);
    }

    /** Shows {@code model} on a display made here instead of its current one, keeping its tint. */
    public static void remodel(@Nonnull ItemDisplay display, @Nonnull String model) {
        if (display.isValid()) {
            ItemStack stack = display.getItemStack();
            ItemMeta meta = stack.getItemMeta();
            meta.setItemModel(new NamespacedKey("occultech", model));
            stack.setItemMeta(meta);
            display.setItemStack(stack);
        }
    }

    /** Re-tints a display made here (a marker that locks turns red). */
    public static void tint(@Nonnull ItemDisplay display, @Nonnull Color tint) {
        if (display.isValid()) {
            ItemStack stack = display.getItemStack();
            stack.setData(DataComponentTypes.DYED_COLOR, DyedItemColor.dyedItemColor(visible(tint)));
            display.setItemStack(stack);
        }
    }

    /** A splat where something burst ({@code radius} blocks): it pops out and fades away within a second. */
    public static void splash(@Nonnull BossFight fight, @Nonnull Location at, double radius, @Nonnull Color color) {
        if (!enabled()) {
            return;
        }
        ItemDisplay splat = decal(fight, floor(at).add(0, WARNING_HEIGHT, 0), "floor_splash", visible(color), true, 0.01F);
        later(1, () -> grow(splat, (float) (radius * 2), 3));
        later(10, () -> grow(splat, 0.01F, 8));
        later(20, splat::remove);
    }

    /** A patch of a zone's surface that does nothing itself (the boss's own code hurts) - e.g. the echo's path. */
    public static void patch(@Nonnull BossFight fight, @Nonnull Location at, double radius, int ticks, @Nonnull Zone zone) {
        if (!enabled()) {
            return;
        }
        ItemDisplay surface = zone(fight, at, radius, ticks, zone);
        later(ticks + 2, surface::remove);
    }

    /** A ground zone at {@code at}, {@code radius} blocks, lasting {@code ticks}; returns its display (the fight removes it). */
    static ItemDisplay zone(@Nonnull BossFight fight, @Nonnull Location at, double radius, int ticks, @Nonnull Zone zone) {
        float across = (float) (radius * 2);
        ItemDisplay surface = decal(fight, floor(at).add(0, ZONE_HEIGHT, 0), "floor_zone_" + zone.name().toLowerCase(Locale.ROOT),
            null, zone.glows, 0.01F);
        later(2, () -> grow(surface, across, UNFOLD));
        later(Math.max(3, ticks - UNFOLD), () -> grow(surface, 0.01F, UNFOLD));   // it shrinks away as it ends
        return surface;
    }

    /**
     * The top of the floor under {@code at}, facing nowhere: a marking lies flat on the surface. (Spots taken from a
     * player carry where they look - a marking spawned there was tilted, half under the floor - and their feet can be
     * a little in the air or in a slab.)
     */
    static Location floor(Location at) {
        Location out = at.clone();
        out.setYaw(0F);
        out.setPitch(0F);
        org.bukkit.block.Block block = out.getBlock();
        for (int i = 0; i < 3 && !block.isPassable(); i++) {
            block = block.getRelative(org.bukkit.block.BlockFace.UP);      // inside something solid: climb out
        }
        for (int i = 0; i < 6 && block.isPassable() && block.getRelative(org.bukkit.block.BlockFace.DOWN).isPassable(); i++) {
            block = block.getRelative(org.bukkit.block.BlockFace.DOWN);    // in the air: drop to the floor
        }
        org.bukkit.block.Block below = block.getRelative(org.bukkit.block.BlockFace.DOWN);
        double top = !block.isPassable() ? block.getBoundingBox().getMaxY()
            : !below.isPassable() ? below.getBoundingBox().getMaxY() : out.getY();
        out.setY(top);
        return out;
    }

    private static void remove(ItemDisplay... displays) {
        for (ItemDisplay display : displays) {
            if (display != null) {
                display.remove();
            }
        }
    }

    private static void animate(ItemDisplay display, Transformation to, int ticks) {
        if (display.isValid()) {
            display.setInterpolationDelay(0);
            display.setInterpolationDuration(ticks);
            display.setTransformation(to);
        }
    }

    private static ItemDisplay decal(BossFight fight, Location at, String model, @Nullable Color tint, boolean glows, float size) {
        at = at.clone();
        at.setYaw(0F);
        at.setPitch(0F);
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
