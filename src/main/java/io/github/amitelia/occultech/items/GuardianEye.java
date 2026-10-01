package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.bukkit.Color;
import org.bukkit.FluidCollisionMode;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

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
 */
public class GuardianEye extends SlimefunItem {

    public static final double RANGE = 12;
    public static final double DAMAGE = 10;
    public static final double IDOL_MULTIPLIER = 1.5;
    /** About every Slimefun block tick (~0.6s). */
    private static final long INTERVAL_MS = 500;
    private static final Particle.DustOptions BEAM = new Particle.DustOptions(Color.fromRGB(110, 230, 220), 1.1F);
    private static final Particle.DustOptions FRENZIED = new Particle.DustOptions(Color.fromRGB(255, 150, 60), 1.3F);

    private final Map<Location, Long> lastShot = new HashMap<>();

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
                if (now - lastShot.getOrDefault(block.getLocation(), 0L) >= INTERVAL_MS) {
                    LivingEntity target = findTarget(block);
                    if (target != null) {
                        lastShot.put(block.getLocation(), now);
                        fire(block, target, frenzied);
                    }
                }
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                rituals.holograms().clear(e.getBlock());
                lastShot.remove(e.getBlock().getLocation());
            }
        });
    }

    /** Damage per shot: 10, or 15 with a Frenzy Idol nearby. */
    public static double damage(boolean frenzied) {
        return frenzied ? DAMAGE * IDOL_MULTIPLIER : DAMAGE;
    }

    static LivingEntity findTarget(Block block) {
        Location eye = block.getLocation().add(0.5, 1.2, 0.5);
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
        Location eye = block.getLocation().add(0.5, 1.2, 0.5);
        Location to = target.getLocation().add(0, target.getHeight() / 2, 0);
        Vector step = to.toVector().subtract(eye.toVector());
        double length = step.length();
        step.normalize().multiply(0.35);
        Location point = eye.clone();
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
