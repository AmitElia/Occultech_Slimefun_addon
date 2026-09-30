package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/**
 * Abyssal Anchor: a heavy weapon. Right-click hurls a spectral anchor on a chain (18 blocks). The first creature it hits
 * is dragged to you, slowed and hurt. Never grabs players. 4s cooldown, 1 durability per throw. Hits harder on wet
 * targets (in water or rain: x1.3).
 */
public class AbyssalAnchor extends OccultItem {

    private static final double SPEED = 1.5;
    private static final int MAX_TICKS = 12;
    private static final long COOLDOWN_MS = 4000;
    private static final double DAMAGE = 8;
    private static final double WET_MULTIPLIER = 1.3;
    private static final Particle.DustOptions CHAIN = new Particle.DustOptions(Color.fromRGB(70, 80, 90), 0.8F);

    private final Map<UUID, Long> cooldowns = new HashMap<>();

    public AbyssalAnchor(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, Plugin plugin) {
        super(group, item, type, recipe, output);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            long now = System.currentTimeMillis();
            if (now < cooldowns.getOrDefault(player.getUniqueId(), 0L)) {
                return;
            }
            if (!BoneScepter.useDurability(e.getItem())) {
                player.sendMessage(ChatColor.RED + "The anchor's chain is spent. Repair it with a ritual.");
                return;
            }
            cooldowns.put(player.getUniqueId(), now + COOLDOWN_MS);
            hurl(plugin, player);
        });
    }

    private static void hurl(Plugin plugin, Player player) {
        Location start = player.getEyeLocation().add(0, -0.3, 0);
        Vector direction = start.getDirection().normalize().multiply(SPEED);
        ItemDisplay anchor = player.getWorld().spawn(start, ItemDisplay.class, d -> {
            d.setPersistent(false);
            d.setItemStack(new ItemStack(Material.HEAVY_CORE));
            d.setTeleportDuration(1);
            d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(0.7F, 0.7F, 0.7F), new AxisAngle4f()));
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
        player.getWorld().playSound(start, Sound.ITEM_TRIDENT_THROW, 1F, 0.6F);

        new BukkitRunnable() {
            private int ticks;
            private final Location position = start.clone();

            @Override
            public void run() {
                if (!player.isOnline() || ticks++ >= MAX_TICKS || !anchor.isValid()) {
                    anchor.remove();
                    cancel();
                    return;
                }
                position.add(direction);
                if (!position.getBlock().isPassable()) {
                    player.getWorld().playSound(position, Sound.BLOCK_ANVIL_LAND, 0.5F, 1.4F);
                    anchor.remove();
                    cancel();
                    return;
                }
                anchor.teleport(position);
                chain(player.getEyeLocation().add(0, -0.3, 0), position);

                for (Entity entity : position.getWorld().getNearbyEntities(position, 1.2, 1.2, 1.2)) {
                    if (entity instanceof LivingEntity target && target != player && !(target instanceof Player)
                        && !(target instanceof org.bukkit.entity.ArmorStand) && Keys.minionOwner(target) == null) {
                        grab(player, target);
                        anchor.remove();
                        cancel();
                        return;
                    }
                }
            }
        }.runTaskTimer(plugin, 1L, 1L);
    }

    private static void grab(Player player, LivingEntity target) {
        Vector pull = player.getLocation().toVector().subtract(target.getLocation().toVector());
        double distance = pull.length();
        pull.normalize().multiply(Math.min(2.2, 0.25 * distance)).setY(0.35);
        target.setVelocity(pull);
        target.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 60, 1));
        target.damage(target.isInWaterOrRainOrBubbleColumn() ? DAMAGE * WET_MULTIPLIER : DAMAGE, player);
        target.getWorld().playSound(target.getLocation(), Sound.BLOCK_CHAIN_BREAK, 1.2F, 0.7F);
        target.getWorld().spawnParticle(Particle.CRIT, target.getLocation().add(0, 1, 0), 15, 0.3, 0.4, 0.3, 0.1);
    }

    private static void chain(Location from, Location to) {
        Vector step = to.toVector().subtract(from.toVector());
        double length = step.length();
        step.normalize().multiply(0.5);
        Location point = from.clone();
        for (double d = 0; d < length; d += 0.5) {
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0, 0, 0, 0, CHAIN);
            point.add(step);
        }
    }
}
