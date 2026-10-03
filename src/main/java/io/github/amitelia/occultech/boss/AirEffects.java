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
import org.joml.Quaternionf;
import org.joml.Vector3f;

import javax.annotation.Nonnull;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Effects in the air for boss fights (Session O5, phase 1): beams, chains and plasma bolts - item displays with
 * crossed-plane models from the resource pack, stretched between two points and turned to face along them.
 *
 * <p>Minecraft runs animated textures on one global clock, so these textures are seamless loops that scroll along the
 * effect (any frame works as a start). What marks a start - a beam shooting out, a bolt dropping, a flash, a collapse - is
 * the display's own interpolated movement, done by each player's client; a tracking beam is re-aimed once a boss step.
 * Like the floor markings, they're spawned through the fight (gone with it), never saved, and only drawn with the pack
 * ({@link FloorDecals#enabled()}); without it fights keep their particles.
 */
public final class AirEffects {

    private static final int BOLT_LENGTH = 14;

    private AirEffects() {}

    public static boolean enabled() {
        return FloorDecals.enabled();
    }

    /**
     * A beam or chain between two points: a display at {@code from}, its model stretched to {@code to}. Re-aim it with
     * {@link #aim}; end it with {@link #fire} (a flash, then it collapses) or {@link #snap} (it just collapses).
     */
    public static final class Streak {
        private final ItemDisplay display;
        private float width;

        private Streak(ItemDisplay display, float width) {
            this.display = display;
            this.width = width;
        }

        /** A new streak of {@code model} ({@code air_beam}, {@code air_chain}) from {@code from} to {@code to}, tinted. */
        public static Streak create(@Nonnull BossFight fight, @Nonnull String model, @Nonnull Location from, @Nonnull Location to,
            @Nonnull Color tint, float width) {
            ItemDisplay display = spawn(fight, from, model, tint);
            display.setTeleportDuration(BossService.STEP);
            display.setTransformation(along(to.toVector().subtract(flat(from).toVector()), 0.01F));
            Streak streak = new Streak(display, width);
            later(2, () -> streak.aim(from, to, width, 4));     // it shoots out to its target
            return streak;
        }

        /** Points it from {@code from} to {@code to}, {@code width} across, getting there in {@code ticks}. */
        public void aim(@Nonnull Location from, @Nonnull Location to, float width, int ticks) {
            if (!display.isValid()) {
                return;
            }
            this.width = width;
            Location anchor = flat(from);
            if (anchor.distanceSquared(display.getLocation()) > 1e-4) {
                display.teleport(anchor);                          // its source moved (smoothed over a step)
            }
            animate(display, along(to.toVector().subtract(anchor.toVector()), width), ticks);
        }

        /** Its colour (a beam turning white as it's about to fire). */
        public void tint(@Nonnull Color tint) {
            if (display.isValid()) {
                ItemStack stack = display.getItemStack();
                stack.setData(DataComponentTypes.DYED_COLOR, DyedItemColor.dyedItemColor(tint));
                display.setItemStack(stack);
            }
        }

        /** Fires: flashes white and wide for a moment along its last aim, then collapses and goes. */
        public void fire(@Nonnull Location from, @Nonnull Location to) {
            tint(Color.WHITE);
            aim(from, to, Math.max(width * 2.2F, 0.9F), 2);
            Location f = from.clone();
            Location t = to.clone();
            later(4, () -> aim(f, t, 0.01F, 5));
            later(10, display::remove);
        }

        /** Collapses (to nothing across) and goes - a chain whose guard died, a beam that was cancelled. */
        public void snap() {
            if (!display.isValid()) {
                return;
            }
            Transformation now = display.getTransformation();
            animate(display, new Transformation(now.getTranslation(), now.getLeftRotation(),
                new Vector3f(0.01F, now.getScale().y(), 0.01F), now.getRightRotation()), 4);
            later(6, display::remove);
        }

        public boolean valid() {
            return display.isValid();
        }
    }

    /**
     * A plasma bolt striking {@code ground} from the sky: it drops in a few ticks, flashes, thins and goes. One of three
     * shapes at random, so repeated strikes don't look alike.
     */
    public static void bolt(@Nonnull BossFight fight, @Nonnull Location ground, @Nonnull Color tint) {
        if (!enabled()) {
            return;
        }
        String model = "air_bolt_" + ThreadLocalRandom.current().nextInt(3);
        ItemDisplay display = spawn(fight, FloorDecals.floor(ground), model, tint);
        float w = 1.6F;
        display.setTransformation(vertical(w, 0.01F, BOLT_LENGTH));                // a point high above
        later(2, () -> animate(display, vertical(w, BOLT_LENGTH, BOLT_LENGTH / 2F), 3));   // drops to the ground
        later(6, () -> animate(display, vertical(w * 1.6F, BOLT_LENGTH, BOLT_LENGTH / 2F), 1));   // flash
        later(8, () -> animate(display, vertical(0.01F, BOLT_LENGTH, BOLT_LENGTH / 2F), 6));     // thins away
        later(16, display::remove);
    }

    private static Transformation vertical(float width, float length, float centre) {
        return new Transformation(new Vector3f(0F, centre, 0F), new Quaternionf(), new Vector3f(width, length, width), new Quaternionf());
    }

    /** The model (its length along y, centred) turned along {@code span}, its base at the display, {@code width} across. */
    private static Transformation along(Vector span, float width) {
        float length = (float) Math.max(0.01, span.length());
        Vector3f dir = span.lengthSquared() < 1e-6 ? new Vector3f(0, 1, 0) : new Vector3f((float) span.getX(), (float) span.getY(), (float) span.getZ()).normalize();
        Quaternionf turn = new Quaternionf().rotationTo(new Vector3f(0, 1, 0), dir);
        Vector3f half = new Vector3f(dir).mul(length / 2F);
        return new Transformation(half, turn, new Vector3f(width, length, width), new Quaternionf());
    }

    private static ItemDisplay spawn(BossFight fight, Location at, String model, Color tint) {
        ItemStack stack = new ItemStack(Material.PAPER);
        ItemMeta meta = stack.getItemMeta();
        meta.setItemModel(new NamespacedKey("occultech", model));
        stack.setItemMeta(meta);
        stack.setData(DataComponentTypes.DYED_COLOR, DyedItemColor.dyedItemColor(FloorDecals.visible(tint)));
        return fight.spawnExtra(ItemDisplay.class, flat(at), d -> {
            d.setItemStack(stack);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setBrightness(new Display.Brightness(15, 15));
            d.setShadowRadius(0F);
            d.setViewRange(3F);
        });
    }

    private static Location flat(Location at) {
        Location out = at.clone();
        out.setYaw(0F);
        out.setPitch(0F);
        return out;
    }

    private static void animate(ItemDisplay display, Transformation to, int ticks) {
        if (display.isValid()) {
            display.setInterpolationDelay(0);
            display.setInterpolationDuration(ticks);
            display.setTransformation(to);
        }
    }

    private static void later(long ticks, Runnable task) {
        Plugin plugin = Bukkit.getPluginManager().getPlugin("Occultech");
        if (plugin != null) {
            Bukkit.getScheduler().runTaskLater(plugin, task, ticks);
        }
    }
}
