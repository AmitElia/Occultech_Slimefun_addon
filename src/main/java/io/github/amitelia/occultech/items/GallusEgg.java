package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Input;
import org.bukkit.Location;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Chicken;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/**
 * Gallus Egg: right-click to hatch a big rideable chicken for yourself. Movement keys steer it (it faces where you
 * look), jump flaps upward, and it glides down slowly. It can't be hurt, never lays eggs, and vanishes when you get off,
 * log out or change worlds. 5s cooldown.
 */
public class GallusEgg extends OccultItem implements Listener {

    private static final NamespacedKey MOUNT = new NamespacedKey("occultech", "gallus_mount");
    private static final long COOLDOWN_MS = 5000;
    private static final double SPEED = 0.32;
    private static final double SPRINT_SPEED = 0.42;
    private static final double FLAP = 0.55;
    private static final double GLIDE = -0.12;

    private final Map<UUID, Chicken> mounts = new HashMap<>();
    private final Map<UUID, Long> cooldowns = new HashMap<>();
    private final Map<UUID, Long> lastFlap = new HashMap<>();

    public GallusEgg(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, Plugin plugin) {
        super(group, item, type, recipe, output);
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::steer, 1L, 1L);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            long now = System.currentTimeMillis();
            if (mounts.containsKey(player.getUniqueId()) || player.isInsideVehicle()) {
                return;
            }
            if (now < cooldowns.getOrDefault(player.getUniqueId(), 0L)) {
                player.sendMessage(ChatColor.GRAY + "The egg is still warm.");
                return;
            }
            cooldowns.put(player.getUniqueId(), now + COOLDOWN_MS);
            hatch(player);
        });
    }

    private void hatch(Player player) {
        Location at = player.getLocation();
        Chicken mount = at.getWorld().spawn(at, Chicken.class, c -> {
            c.setPersistent(false);
            c.setInvulnerable(true);
            c.setAdult();
            c.setEggLayTime(Integer.MAX_VALUE);
            c.setCustomName(ChatColor.GOLD + player.getName() + "'s Gallus");
            c.setCustomNameVisible(false);
            Bukkit.getMobGoals().removeAllGoals(c);
            c.getAttribute(Attribute.SCALE).setBaseValue(2.6);
            c.getAttribute(Attribute.SAFE_FALL_DISTANCE).setBaseValue(1024);
            c.getPersistentDataContainer().set(MOUNT, PersistentDataType.STRING, player.getUniqueId().toString());
            c.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
        mount.addPassenger(player);
        mounts.put(player.getUniqueId(), mount);
        at.getWorld().spawnParticle(Particle.ITEM, at.clone().add(0, 0.5, 0), 20, 0.4, 0.3, 0.4, 0.05, new ItemStack(org.bukkit.Material.EGG));
        at.getWorld().playSound(at, Sound.ENTITY_CHICKEN_EGG, 1F, 0.6F);
    }

    /** Every tick: steer each mount from its rider's keys; remove mounts whose rider left. */
    private void steer() {
        long now = System.currentTimeMillis();
        for (Iterator<Map.Entry<UUID, Chicken>> it = mounts.entrySet().iterator(); it.hasNext();) {
            Map.Entry<UUID, Chicken> entry = it.next();
            Chicken mount = entry.getValue();
            Player rider = Bukkit.getPlayer(entry.getKey());
            if (rider == null || !mount.isValid() || !mount.getPassengers().contains(rider)) {
                dismiss(mount);
                it.remove();
                continue;
            }
            Input input = rider.getCurrentInput();
            double forward = (input.isForward() ? 1 : 0) - (input.isBackward() ? 1 : 0);
            double strafe = (input.isLeft() ? 1 : 0) - (input.isRight() ? 1 : 0);
            float yaw = rider.getLocation().getYaw();
            Vector look = new Vector(-Math.sin(Math.toRadians(yaw)), 0, Math.cos(Math.toRadians(yaw)));
            Vector left = new Vector(look.getZ(), 0, -look.getX());
            Vector move = look.multiply(forward).add(left.multiply(strafe));
            if (move.lengthSquared() > 0) {
                move.normalize().multiply(input.isSprint() ? SPRINT_SPEED : SPEED);
            }
            double y = mount.getVelocity().getY();
            if (input.isJump() && now - lastFlap.getOrDefault(entry.getKey(), 0L) > 350) {
                lastFlap.put(entry.getKey(), now);
                y = FLAP;
                mount.getWorld().playSound(mount.getLocation(), Sound.ENTITY_PARROT_FLY, 0.8F, 0.8F);
                mount.getWorld().spawnParticle(Particle.CLOUD, mount.getLocation(), 4, 0.4, 0.1, 0.4, 0.02);
            } else if (y < GLIDE) {
                y = GLIDE;
            }
            mount.setVelocity(move.setY(y));
            mount.setRotation(yaw, 0);
            mount.setBodyYaw(yaw);
        }
    }

    private static void dismiss(Chicken mount) {
        if (mount.isValid()) {
            mount.getWorld().spawnParticle(Particle.CLOUD, mount.getLocation().add(0, 0.5, 0), 12, 0.4, 0.3, 0.4, 0.02);
            mount.remove();
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        Chicken mount = mounts.remove(e.getPlayer().getUniqueId());
        if (mount != null) {
            dismiss(mount);
        }
    }

    /** Plugin disable: no mounts left behind. */
    public void shutdown() {
        mounts.values().forEach(GallusEgg::dismiss);
        mounts.clear();
    }
}
