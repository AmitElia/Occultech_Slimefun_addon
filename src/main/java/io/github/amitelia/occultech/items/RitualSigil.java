package io.github.amitelia.occultech.items;

import io.github.amitelia.occultech.core.Keys;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.block.Block;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.List;

/**
 * The tier's sigil (Session B) as a glowing hologram on the ritual floor while a ritual runs: it unfolds across the
 * circle, turns, and folds away when the ritual ends. A summoning hands it to the boss fight: it keeps turning, slowly,
 * until the fight is over.
 *
 * <p>Item displays with flat models from the pack ({@code occultech:ritual_sigil_t0..t3}).
 * The turning is the client's: each step sets the next angle with an interpolation as long as the step, so the server
 * sends one update a second. Never saved with the chunk (a ritual lasts seconds).
 */
final class RitualSigil {

    /** Ticks per quarter turn during a ritual, and during the boss fight a summoning started. */
    private static final int STEP = 20;
    private static final int FIGHT_STEP = 80;
    private static final int UNFOLD = 10;
    private static final int FOLD = 8;
    /** Just above the glyph tiles. */
    private static final double FLOOR = 0.09;

    private final List<Layer> layers = new ArrayList<>();
    private int turns;

    private record Layer(ItemDisplay display, float size, float speed) {}

    private RitualSigil() {}

    /**
     * Lays the sigil of a {@code tier} circle {@code size} blocks across, centred on the altar. Null without the
     * resource pack's sigils.
     */
    @Nullable
    static RitualSigil show(@Nonnull Block altar, int tier, int size) {
        var pack = io.github.amitelia.occultech.Occultech.instance().resourcePack();
        if (pack == null || !pack.hasSigils()) {
            return null;
        }
        RitualSigil sigil = new RitualSigil();
        Location at = altar.getLocation().add(0.5, FLOOR, 0.5);
        sigil.layers.add(new Layer(spawn(at, "ritual_sigil_t" + tier), size, 1F));
        for (Layer layer : sigil.layers) {
            layer.display().setTransformation(transform(0F, 0.01F));
        }
        // the next tick: unfold (a display only interpolates from a state the client has already seen)
        Bukkit.getScheduler().runTaskLater(plugin(), () -> {
            for (Layer layer : sigil.layers) {
                animate(layer.display(), transform(0F, layer.size()), UNFOLD);
            }
        }, 2L);
        return sigil;
    }

    /** Called every {@link #STEP} ticks of the ritual: the next quarter turn. */
    void turn() {
        turn(STEP);
    }

    private void turn(int ticks) {
        turns++;
        for (Layer layer : layers) {
            animate(layer.display(), transform((float) (turns * layer.speed() * Math.PI / 2), layer.size()), ticks);
        }
    }

    /**
     * The summoning is done and its boss fight begins: the sigil stays on the floor, turning a quarter turn every four
     * seconds, until {@code fighting} says the fight is over (checked each step); then it folds away.
     */
    void keepWhile(@Nonnull java.util.function.BooleanSupplier fighting) {
        Bukkit.getScheduler().runTaskTimer(plugin(), task -> {
            boolean shown = layers.stream().allMatch(layer -> layer.display().isValid());
            if (!shown || !fighting.getAsBoolean()) {
                task.cancel();
                close();
                return;
            }
            turn(FIGHT_STEP);
        }, 1L, FIGHT_STEP);
    }

    static int step() {
        return STEP;
    }

    /** Folds the sigil away and removes it. */
    void close() {
        for (Layer layer : layers) {
            animate(layer.display(), transform((float) ((turns + 0.5) * layer.speed() * Math.PI / 2), 0.01F), FOLD);
            Bukkit.getScheduler().runTaskLater(plugin(), layer.display()::remove, FOLD + 2L);
        }
    }

    private static ItemDisplay spawn(Location at, String model) {
        ItemStack stack = new ItemStack(Material.PAPER);
        ItemMeta meta = stack.getItemMeta();
        meta.setItemModel(new NamespacedKey("occultech", model));
        stack.setItemMeta(meta);
        return at.getWorld().spawn(at, ItemDisplay.class, d -> {
            d.setItemStack(stack);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setBrightness(new Display.Brightness(15, 15));   // it stands inside the altar block: light it itself
            d.setShadowRadius(0F);
            d.setViewRange(2F);
            d.setPersistent(false);
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
    }

    private static Transformation transform(float angle, float size) {
        return new Transformation(new Vector3f(), new AxisAngle4f(angle, 0F, 1F, 0F), new Vector3f(size, 1F, size), new AxisAngle4f());
    }

    private static void animate(ItemDisplay display, Transformation to, int ticks) {
        if (!display.isValid()) {
            return;
        }
        display.setInterpolationDelay(0);
        display.setInterpolationDuration(ticks);
        display.setTransformation(to);
    }

    private static Plugin plugin() {
        return io.github.amitelia.occultech.Occultech.instance();
    }
}
