package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.FluidCollisionMode;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerItemConsumeEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.RayTraceResult;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.papermc.paper.datacomponent.DataComponentTypes;
import io.papermc.paper.datacomponent.item.Consumable;
import io.papermc.paper.datacomponent.item.consumable.ItemUseAnimation;
import net.kyori.adventure.key.Key;

/**
 * Hold-to-use weapons. The items carry a "consumable" component with a silent, practically endless use, so holding
 * right-click keeps them in use; every 2 ticks this service checks who is using one and runs its effect.
 * <ul>
 * <li><b>Wyrmbreath</b>: a cone of vanilla fire particles; creatures in the cone (6 blocks, 25 degrees, line of sight)
 * burn and take damage. Heat builds while firing; at 100 it overheats and locks for 3s. Never ignites blocks.</li>
 * <li><b>Guardian's Gaze</b>: locks a beam onto the creature you aim at (40 blocks); damage ramps up the longer it's
 * held, and the lock breaks without line of sight.</li>
 * </ul>
 * Neither hurts players. Both use 1 durability per second of use and stop at their last point.
 */
public final class HeldWeapons implements Listener {

    public static final String WYRMBREATH = ItemKeys.slimefunId("WYRMBREATH");
    public static final String GAZE = ItemKeys.slimefunId("GUARDIANS_GAZE");
    /** Tier-3 Wyrmbreath: a longer blue soul-fire cone that runs 5s before it overheats. */
    public static final String CENSER = ItemKeys.slimefunId("SOULFIRE_CENSER");
    private static final Set<String> HELD = Set.of(WYRMBREATH, GAZE, CENSER);

    private static final double FIRE_RANGE = 6;
    private static final double FIRE_ANGLE = 25;
    private static final double BEAM_RANGE = 40;
    /** How far off the crosshair (degrees) the Gaze still finds a target. */
    private static final double BEAM_AIM_ASSIST = 6;
    private static final int OVERHEAT = 100;
    private static final long OVERHEAT_LOCK_MS = 3000;
    private static final Particle.DustOptions BEAM = new Particle.DustOptions(Color.fromRGB(90, 220, 210), 0.9F);

    private final Map<UUID, Integer> heat = new HashMap<>();
    private final Map<UUID, Long> lockedUntil = new HashMap<>();
    private final Map<UUID, LivingEntity> gazeTarget = new HashMap<>();
    private final Map<UUID, Integer> gazeTicks = new HashMap<>();
    private final Map<UUID, Integer> useTicks = new HashMap<>();
    private int tick;

    public HeldWeapons(Plugin plugin) {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::tick, 2L, 2L);
    }

    public static boolean isHeld(String id) {
        return HELD.contains(id);
    }

    /** Lets the item be "used" by holding right-click, silently and (practically) forever. */
    public static void makeHoldable(ItemStack item) {
        item.setData(DataComponentTypes.CONSUMABLE, Consumable.consumable()
            .consumeSeconds(3600)
            .animation(ItemUseAnimation.BOW)
            .hasConsumeParticles(false)
            .sound(Key.key("minecraft", "intentionally_empty"))
            .build());
    }

    @EventHandler(ignoreCancelled = true)
    public void onConsume(PlayerItemConsumeEvent e) {
        SlimefunItem item = SlimefunItem.getByItem(e.getItem());
        if (item != null && HELD.contains(item.getId())) {
            e.setCancelled(true);
        }
    }

    private void tick() {
        tick += 2;
        long now = System.currentTimeMillis();
        for (Player player : Bukkit.getOnlinePlayers()) {
            UUID id = player.getUniqueId();
            String using = player.hasActiveItem() ? idOf(player.getActiveItem()) : null;

            if (!WYRMBREATH.equals(using) && !CENSER.equals(using)) {
                heat.computeIfPresent(id, (k, h) -> h <= 2 ? null : h - 2);
            }
            if (!GAZE.equals(using)) {
                gazeTarget.remove(id);
                gazeTicks.remove(id);
            }
            if (using == null) {
                useTicks.remove(id);
                continue;
            }

            // the item in hand (getActiveItem() is a copy, so durability must be taken from the real stack)
            ItemStack item = player.getInventory().getItem(player.getActiveItemHand());
            if (now < lockedUntil.getOrDefault(id, 0L)) {
                player.clearActiveItem();
                continue;
            }
            int used = useTicks.merge(id, 2, Integer::sum);
            if (used % 20 == 0 && !BoneScepter.useDurability(item)) {
                player.clearActiveItem();
                player.sendMessage(ChatColor.RED + "It is spent. Repair it with a ritual.");
                continue;
            }
            if (WYRMBREATH.equals(using) || CENSER.equals(using)) {
                breathe(player, now, CENSER.equals(using));
            } else if (GAZE.equals(using)) {
                gaze(player);
            }
        }
    }

    // ------------------------------------------------------------------ Wyrmbreath

    private void breathe(Player player, long now, boolean censer) {
        UUID id = player.getUniqueId();
        // the Censer heats up slower: 5s of fire before it locks
        int h = heat.merge(id, censer ? 2 : 3, Integer::sum);
        double range = censer ? 9 : FIRE_RANGE;
        double angle = censer ? 30 : FIRE_ANGLE;
        Particle flame = censer ? Particle.SOUL_FIRE_FLAME : Particle.FLAME;
        if (h >= OVERHEAT) {
            heat.put(id, OVERHEAT);
            lockedUntil.put(id, now + OVERHEAT_LOCK_MS);
            player.clearActiveItem();
            player.getWorld().playSound(player.getLocation(), Sound.BLOCK_FIRE_EXTINGUISH, 1F, 0.8F);
            player.sendActionBar(ChatColor.RED + (censer ? "The Censer" : "Wyrmbreath") + " overheated!");
            return;
        }
        player.sendActionBar(heatBar(h));

        Location eye = player.getEyeLocation();
        Vector look = eye.getDirection();
        ThreadLocalRandom random = ThreadLocalRandom.current();
        Location mouth = eye.clone().add(look.clone().multiply(0.8)).add(0, -0.25, 0);
        for (int i = 0; i < 7; i++) {
            Vector spread = look.clone().add(new Vector(random.nextGaussian(), random.nextGaussian(), random.nextGaussian()).multiply(0.13)).normalize();
            double speed = (0.35 + random.nextDouble() * 0.25) * (censer ? 1.4 : 1);
            player.getWorld().spawnParticle(flame, mouth, 0, spread.getX(), spread.getY(), spread.getZ(), speed);
            if (i % 2 == 0) {
                player.getWorld().spawnParticle(Particle.SMALL_FLAME, mouth, 0, spread.getX(), spread.getY(), spread.getZ(), speed * 1.2);
            }
        }
        if (random.nextInt(4) == 0) {
            player.getWorld().spawnParticle(Particle.LAVA, mouth.clone().add(look.clone().multiply(2)), 1);
            player.getWorld().spawnParticle(Particle.LARGE_SMOKE, mouth.clone().add(look.clone().multiply(3)), 1, 0.2, 0.2, 0.2, 0.01);
        }
        if (tick % 8 == 0) {
            player.getWorld().playSound(eye, Sound.ENTITY_BLAZE_SHOOT, 0.5F, 0.6F);
        }
        if (tick % 4 != 0) {
            return;
        }
        for (Entity entity : player.getNearbyEntities(range, range, range)) {
            if (!(entity instanceof LivingEntity target) || !validTarget(player, target)) {
                continue;
            }
            Vector to = target.getLocation().add(0, target.getHeight() / 2, 0).toVector().subtract(eye.toVector());
            if (to.length() <= range && Math.toDegrees(to.angle(look)) <= angle && hasLineOfSight(eye, target)) {
                hurt(target, censer ? 9 : 4, player);
                target.setFireTicks(Math.max(target.getFireTicks(), 80));
            }
        }
    }

    private static String heatBar(int heatLevel) {
        int filled = heatLevel / 10;
        StringBuilder bar = new StringBuilder(ChatColor.GOLD + "Heat ");
        for (int i = 0; i < 10; i++) {
            bar.append(i < filled ? (heatLevel > 70 ? ChatColor.RED : ChatColor.GOLD) : ChatColor.DARK_GRAY).append('|');
        }
        return bar.toString();
    }

    // ------------------------------------------------------------------ Guardian's Gaze

    private void gaze(Player player) {
        UUID id = player.getUniqueId();
        Location eye = player.getEyeLocation();
        LivingEntity target = gazeTarget.get(id);
        if (target != null && (!target.isValid() || target.isDead() || target.getLocation().distance(eye) > BEAM_RANGE || !hasLineOfSight(eye, target))) {
            target = null;
            gazeTarget.remove(id);
            gazeTicks.remove(id);
        }
        if (target == null) {
            LivingEntity found = aimedAt(player, eye);
            if (found == null) {
                drawBeam(eye.clone().add(0, -0.2, 0), beamEnd(eye));
                return;
            }
            target = found;
            gazeTarget.put(id, target);
            player.getWorld().playSound(eye, Sound.ENTITY_GUARDIAN_ATTACK, 0.8F, 1.4F);
        }

        int held = gazeTicks.merge(id, 2, Integer::sum);
        Location center = target.getLocation().add(0, target.getHeight() / 2, 0);
        drawBeam(eye.clone().add(0, -0.2, 0), center);
        if (held % 10 == 0) {
            double damage = Math.min(10, 3 + held / 20.0);
            hurt(target, damage, player);
            player.sendActionBar(ChatColor.AQUA + "Gaze " + ChatColor.WHITE + String.format("%.0f", damage) + " dmg");
        }
    }

    private static void drawBeam(Location from, Location to) {
        Vector step = to.toVector().subtract(from.toVector());
        double length = step.length();
        if (length < 0.1) {
            return;
        }
        step.normalize().multiply(0.4);
        Location point = from.clone();
        for (double d = 0; d < length; d += 0.4) {
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0, 0, 0, 0, BEAM);
            point.add(step);
        }
    }

    /** The valid creature closest to the crosshair within a small cone, in line of sight. */
    private static LivingEntity aimedAt(Player player, Location eye) {
        Vector look = eye.getDirection();
        LivingEntity best = null;
        double bestAngle = BEAM_AIM_ASSIST;
        for (Entity entity : player.getNearbyEntities(BEAM_RANGE, BEAM_RANGE, BEAM_RANGE)) {
            if (!(entity instanceof LivingEntity living) || !validTarget(player, living)) {
                continue;
            }
            Vector to = living.getLocation().add(0, living.getHeight() / 2, 0).toVector().subtract(eye.toVector());
            double distance = to.length();
            if (distance > BEAM_RANGE || distance < 0.5) {
                continue;
            }
            // big creatures are easier to hit: allow their half-width on top of the cone
            double allowance = Math.toDegrees(Math.atan(living.getWidth() / 2 / distance));
            double angle = Math.toDegrees(to.angle(look)) - allowance;
            if (angle < bestAngle && hasLineOfSight(eye, living)) {
                best = living;
                bestAngle = angle;
            }
        }
        return best;
    }

    /** Where a beam that hits nothing stops: the first block, or full range. */
    private static Location beamEnd(Location eye) {
        RayTraceResult block = eye.getWorld().rayTraceBlocks(eye, eye.getDirection(), BEAM_RANGE, FluidCollisionMode.NEVER, true);
        return block == null ? eye.clone().add(eye.getDirection().multiply(BEAM_RANGE)) : block.getHitPosition().toLocation(eye.getWorld());
    }

    /**
     * Damage from a held weapon. These hit several times a second, faster than a creature's invulnerability frames
     * (which would otherwise swallow almost every tick of damage), so the frames are cleared first.
     */
    static void hurt(LivingEntity target, double amount, Player player) {
        target.setNoDamageTicks(0);
        Keys.HELD_WEAPON_HIT.set(true);
        try {
            target.damage(amount, player);
        } finally {
            Keys.HELD_WEAPON_HIT.set(false);
        }
    }

    // ------------------------------------------------------------------ helpers

    /** Creatures only: never players, other players' minions or armor stands. */
    private static boolean validTarget(Player shooter, LivingEntity target) {
        // mounts can't be hurt, and the Gaze must lock onto the rider, not the horse under it
        return target != shooter && !(target instanceof Player) && !(target instanceof org.bukkit.entity.ArmorStand)
            && Keys.minionOwner(target) == null && !target.isDead() && !Keys.isUnhittable(target)
            && !target.getPersistentDataContainer().has(Keys.HOLOGRAM);
    }

    private static boolean hasLineOfSight(Location eye, LivingEntity target) {
        Location center = target.getLocation().add(0, target.getHeight() / 2, 0);
        Vector to = center.toVector().subtract(eye.toVector());
        RayTraceResult block = eye.getWorld().rayTraceBlocks(eye, to.clone().normalize(), to.length(), FluidCollisionMode.NEVER, true);
        return block == null;
    }

    private static String idOf(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return null;
        }
        SlimefunItem sfItem = SlimefunItem.getByItem(item);
        return sfItem == null ? null : sfItem.getId();
    }
}
