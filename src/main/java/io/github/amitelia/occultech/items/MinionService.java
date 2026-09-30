package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.entity.Skeleton;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.EntityTargetLivingEntityEvent;
import org.bukkit.event.entity.ProjectileLaunchEvent;
import org.bukkit.event.player.PlayerChangedWorldEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;

import io.github.amitelia.occultech.core.Keys;

/**
 * Necromancy minions: undead that fight for a player for a short time.
 * <ul>
 * <li>They attack hostile mobs, bosses, and whatever their owner hits or is hit by; never players, villagers, animals
 * or other minions. They never hurt players.</li>
 * <li>They follow their owner, don't burn in daylight, never drop anything, and despawn when their time runs out or
 * the owner logs out, dies or changes world. They are never saved with the world.</li>
 * <li>Mobs killed only by minions give no XP, so AFK minion farms don't pay.</li>
 * <li>Against bosses they fight at full strength and their damage counts as their owner's.</li>
 * </ul>
 */
public final class MinionService implements Listener {

    private record Minion(Mob entity, UUID owner, long expires) {}

    private final Map<UUID, List<Minion>> byOwner = new HashMap<>();

    public MinionService(Plugin plugin) {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::tick, 10L, 10L);
    }

    /** Raises skeleton archers around the owner. */
    public void raiseSkeletons(Player owner, int count, int seconds) {
        long expires = System.currentTimeMillis() + seconds * 1000L;
        for (int i = 0; i < count; i++) {
            double angle = ThreadLocalRandom.current().nextDouble(Math.PI * 2);
            Location at = owner.getLocation().add(Math.cos(angle) * 1.5, 0, Math.sin(angle) * 1.5);
            Skeleton skeleton = owner.getWorld().spawn(at, Skeleton.class, s -> {
                s.setPersistent(false);
                s.setRemoveWhenFarAway(false);
                s.setShouldBurnInDay(false);
                s.setCanPickupItems(false);
                s.setCustomName(ChatColor.GRAY + owner.getName() + "'s Bound Skeleton");
                s.setCustomNameVisible(false);
                s.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
                s.getEquipment().setHelmet(new ItemStack(Material.LEATHER_HELMET));
                for (EquipmentSlot slot : new EquipmentSlot[] { EquipmentSlot.HAND, EquipmentSlot.HEAD }) {
                    s.getEquipment().setDropChance(slot, 0F);
                }
                s.getPersistentDataContainer().set(Keys.MINION_OWNER, PersistentDataType.STRING, owner.getUniqueId().toString());
            });
            byOwner.computeIfAbsent(owner.getUniqueId(), k -> new ArrayList<>()).add(new Minion(skeleton, owner.getUniqueId(), expires));
            at.getWorld().spawnParticle(Particle.SOUL, at.clone().add(0, 1, 0), 20, 0.3, 0.6, 0.3, 0.02);
        }
        owner.getWorld().playSound(owner.getLocation(), Sound.ENTITY_SKELETON_AMBIENT, 1F, 0.6F);
    }

    public int count(Player owner) {
        List<Minion> minions = byOwner.get(owner.getUniqueId());
        return minions == null ? 0 : minions.size();
    }

    // ------------------------------------------------------------------ upkeep

    private void tick() {
        long now = System.currentTimeMillis();
        byOwner.entrySet().removeIf(entry -> {
            Player owner = Bukkit.getPlayer(entry.getKey());
            entry.getValue().removeIf(minion -> {
                boolean gone = !minion.entity().isValid() || minion.entity().isDead();
                if (gone || now >= minion.expires() || owner == null || owner.isDead() || owner.getWorld() != minion.entity().getWorld()) {
                    dismiss(minion.entity());
                    return true;
                }
                follow(minion.entity(), owner);
                return false;
            });
            return entry.getValue().isEmpty();
        });
    }

    private static void follow(Mob minion, Player owner) {
        double distance = minion.getLocation().distanceSquared(owner.getLocation());
        if (distance > 16 * 16) {
            minion.teleport(owner.getLocation());
        } else if (distance > 25 && minion.getTarget() == null) {
            minion.getPathfinder().moveTo(owner, 1.2);
        }
    }

    private static void dismiss(Entity minion) {
        if (minion.isValid()) {
            minion.getWorld().spawnParticle(Particle.SOUL, minion.getLocation().add(0, 1, 0), 10, 0.2, 0.5, 0.2, 0.02);
            minion.remove();
        }
    }

    private void dismissAll(UUID owner) {
        List<Minion> minions = byOwner.remove(owner);
        if (minions != null) {
            minions.forEach(m -> dismiss(m.entity()));
        }
    }

    /** Removes every minion (plugin disable). */
    public void shutdown() {
        new ArrayList<>(byOwner.keySet()).forEach(this::dismissAll);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        dismissAll(e.getPlayer().getUniqueId());
    }

    @EventHandler
    public void onOwnerDeath(PlayerDeathEvent e) {
        dismissAll(e.getEntity().getUniqueId());
    }

    @EventHandler
    public void onWorldChange(PlayerChangedWorldEvent e) {
        dismissAll(e.getPlayer().getUniqueId());
    }

    // ------------------------------------------------------------------ targeting & damage rules

    @EventHandler(ignoreCancelled = true)
    public void onTarget(EntityTargetLivingEntityEvent e) {
        UUID owner = Keys.minionOwner(e.getEntity());
        if (owner == null || e.getTarget() == null) {
            return;
        }
        if (!mayAttack(e.getTarget())) {
            e.setCancelled(true);
        }
    }

    /** Owner hits something, or something hits the owner: their minions go after it. */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onOwnerFight(EntityDamageByEntityEvent e) {
        Entity damager = source(e.getDamager());
        if (damager instanceof Player owner && e.getEntity() instanceof LivingEntity victim && mayAttack(victim)) {
            command(owner.getUniqueId(), victim);
        } else if (e.getEntity() instanceof Player owner && damager instanceof LivingEntity attacker && mayAttack(attacker)) {
            command(owner.getUniqueId(), attacker);
        }
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onMinionHurtsPlayer(EntityDamageByEntityEvent e) {
        if (e.getEntity() instanceof Player && Keys.minionOwner(source(e.getDamager())) != null) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onLaunch(ProjectileLaunchEvent e) {
        if (e.getEntity().getShooter() instanceof Entity shooter && Keys.minionOwner(shooter) != null && e.getEntity() instanceof AbstractArrow arrow) {
            arrow.setPickupStatus(AbstractArrow.PickupStatus.DISALLOWED);
        }
    }

    @EventHandler
    public void onDeath(EntityDeathEvent e) {
        if (Keys.minionOwner(e.getEntity()) != null) {
            e.getDrops().clear();
            e.setDroppedExp(0);
            return;
        }
        // no XP for kills made only by minions
        if (e.getEntity().getKiller() == null && e.getEntity().getLastDamageCause() instanceof EntityDamageByEntityEvent last
            && Keys.minionOwner(source(last.getDamager())) != null) {
            e.setDroppedExp(0);
        }
    }

    private void command(UUID owner, LivingEntity target) {
        List<Minion> minions = byOwner.get(owner);
        if (minions != null) {
            for (Minion minion : minions) {
                if (minion.entity() != target) {
                    minion.entity().setTarget(target);
                }
            }
        }
    }

    /** Minions fight hostile mobs and bosses only: never players, villagers, animals or other minions. */
    private static boolean mayAttack(@Nullable Entity target) {
        if (target == null || target instanceof Player || Keys.minionOwner(target) != null) {
            return false;
        }
        return target instanceof Monster || Keys.isSummoned(target);
    }

    private static Entity source(Entity damager) {
        return damager instanceof Projectile projectile && projectile.getShooter() instanceof Entity shooter ? shooter : damager;
    }
}
