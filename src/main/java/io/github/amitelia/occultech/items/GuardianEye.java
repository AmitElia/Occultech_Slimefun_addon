package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.FluidCollisionMode;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;

/**
 * Guardian Eye (rare Abyssal Warden drop): a sentry that fires a guardian beam at the nearest hostile mob within 12
 * blocks (line of sight) about twice a second. A Frenzy Idol within 8 blocks makes it 1.5x stronger (never stacks).
 * Never targets players, pets, minions or summoned bosses.
 *
 * <p>With the resource pack its block is a column (a block skin) and its eye a separate display on top that turns
 * to look at its target, or slowly round when there is none; the beam leaves from the eye.
 */
public class GuardianEye extends SlimefunItem {

    public static final double RANGE = 12;
    public static final double DAMAGE = 10;
    public static final double IDOL_MULTIPLIER = 1.5;
    /** About every Slimefun block tick (~0.6s). */
    private static final long INTERVAL_MS = 500;
    private static final Particle.DustOptions BEAM = new Particle.DustOptions(Color.fromRGB(110, 230, 220), 1.1F);
    private static final Particle.DustOptions FRENZIED = new Particle.DustOptions(Color.fromRGB(255, 150, 60), 1.3F);

    /** The eye's centre above the block (matches the column's cradle in the art). */
    public static final double EYE_HEIGHT = 1.4;
    private static final NamespacedKey ORB_MODEL = new NamespacedKey("occultech", "guardian_eye_orb");

    private final Map<Location, Long> lastShot = new HashMap<>();
    private final Map<Location, UUID> orbs = new HashMap<>();

    public GuardianEye(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, RitualService rituals,
        ServitorService servitors) {
        super(group, item, type, recipe, output);

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                boolean frenzied = servitors.idolNear(block.getLocation());
                rituals.holograms().show(block, null, "&3Guardian Eye" + (frenzied ? " &6(frenzied)" : ""));
                long now = System.currentTimeMillis();
                LivingEntity target = findTarget(block);
                ItemDisplay orb = orb(block);
                if (orb != null) {
                    Location eye = block.getLocation().add(0.5, EYE_HEIGHT, 0.5);
                    Vector gaze = target != null ? target.getLocation().add(0, target.getHeight() / 2, 0).toVector().subtract(eye.toVector())
                        : new Vector(Math.sin(now / 2400.0), -0.15, Math.cos(now / 2400.0));   // idle: looking slowly round
                    look(orb, gaze);
                }
                if (target != null && now - lastShot.getOrDefault(block.getLocation(), 0L) >= INTERVAL_MS) {
                    lastShot.put(block.getLocation(), now);
                    fire(block, target, frenzied);
                }
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                lastShot.remove(e.getBlock().getLocation());
                UUID orb = orbs.remove(e.getBlock().getLocation());
                if (orb != null && Bukkit.getEntity(orb) != null) {
                    Bukkit.getEntity(orb).remove();
                }
            }
        });
    }

    /** Damage per shot: 10, or 15 with a Frenzy Idol nearby. */
    public static double damage(boolean frenzied) {
        return frenzied ? DAMAGE * IDOL_MULTIPLIER : DAMAGE;
    }

    /**
     * The eye on top of the column: a display (not saved with the chunk - it is respawned while the block ticks).
     * None without the resource pack's art.
     */
    public ItemDisplay orb(Block block) {
        UUID id = orbs.get(block.getLocation());
        if (id != null && Bukkit.getEntity(id) instanceof ItemDisplay display && display.isValid()) {
            return display;
        }
        var skins = io.github.amitelia.occultech.Occultech.instance().skins();
        if (skins == null || !skins.isSkinned(getId())) {
            return null;
        }
        ItemStack stack = new ItemStack(Material.PAPER);
        ItemMeta meta = stack.getItemMeta();
        meta.setItemModel(ORB_MODEL);
        stack.setItemMeta(meta);
        ItemDisplay display = block.getWorld().spawn(block.getLocation().add(0.5, EYE_HEIGHT, 0.5), ItemDisplay.class, d -> {
            d.setItemStack(stack);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setPersistent(false);
            d.setShadowRadius(0F);
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
        orbs.put(block.getLocation(), display.getUniqueId());
        return display;
    }

    /**
     * Turns the eye to look along {@code gaze} (smoothly, over the next ticks). The eye's front is its model's north
     * face, which an item display draws facing +z; yaw then pitch turn +z onto the gaze.
     */
    public static void look(ItemDisplay orb, Vector gaze) {
        if (gaze.lengthSquared() < 1.0E-6) {
            return;
        }
        Vector dir = gaze.clone().normalize();
        float yaw = (float) Math.atan2(dir.getX(), dir.getZ());
        float pitch = (float) -Math.asin(Math.max(-1, Math.min(1, dir.getY())));
        orb.setInterpolationDelay(0);
        orb.setInterpolationDuration(10);
        orb.setTransformation(new Transformation(new Vector3f(), new Quaternionf().rotationY(yaw).rotateX(pitch),
            new Vector3f(1F, 1F, 1F), new Quaternionf()));
    }

    static LivingEntity findTarget(Block block) {
        Location eye = block.getLocation().add(0.5, EYE_HEIGHT, 0.5);
        LivingEntity best = null;
        double bestDistance = Double.MAX_VALUE;
        for (Entity entity : block.getWorld().getNearbyEntities(eye, RANGE, RANGE, RANGE)) {
            if (!(entity instanceof Monster monster) || Keys.isSummoned(entity) || Keys.minionOwner(entity) != null || monster.isDead()
                || entity.getPersistentDataContainer().has(Keys.HOLOGRAM)) {
                continue;
            }
            double distance = monster.getLocation().distanceSquared(eye);
            if (distance < bestDistance && distance <= RANGE * RANGE && lineOfSight(eye, monster)) {
                best = monster;
                bestDistance = distance;
            }
        }
        return best;
    }

    private static void fire(Block block, LivingEntity target, boolean frenzied) {
        Location eye = block.getLocation().add(0.5, EYE_HEIGHT, 0.5);
        Location to = target.getLocation().add(0, target.getHeight() / 2, 0);
        Vector step = to.toVector().subtract(eye.toVector());
        double length = step.length();
        step.normalize().multiply(0.35);
        Location point = eye.clone().add(step);   // from the eye's surface
        for (double d = 0; d < length; d += 0.35) {
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0, 0, 0, 0, frenzied ? FRENZIED : BEAM);
            point.add(step);
        }
        target.damage(damage(frenzied));
        block.getWorld().playSound(eye, Sound.ENTITY_GUARDIAN_ATTACK, 0.6F, frenzied ? 1.6F : 1.2F);
    }

    private static boolean lineOfSight(Location eye, LivingEntity target) {
        Location center = target.getLocation().add(0, target.getHeight() / 2, 0);
        Vector to = center.toVector().subtract(eye.toVector());
        return eye.getWorld().rayTraceBlocks(eye, to.clone().normalize(), to.length(), FluidCollisionMode.NEVER, true) == null;
    }
}
