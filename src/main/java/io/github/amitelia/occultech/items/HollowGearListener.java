package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.entity.Tameable;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.entity.EntityPotionEffectEvent;
import org.bukkit.event.entity.EntityShootBowEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;

/**
 * Tier-3 gear behavior.
 * <ul>
 * <li>Hollow armor: Crown - immune to Darkness and Blindness; Cuirass - immune to Wither; Greaves - immune to
 * Slowness; Sabatons - no fall damage. Full set: -25% damage from summoned creatures (see {@link WeaponListener}),
 * faint soul wisps drifting off the armor, and battle regeneration: every hit you land gives Regeneration I, which runs
 * out a few seconds after your last hit (Infinity armor regenerates all the time; Hollow only while you fight).</li>
 * <li>Dreadlance: every hit heals 15% of the damage dealt, at most 4 health per second.</li>
 * <li>Stormstring Bow: a hit calls lightning on the creature and arcs to 2 more hostile mobs within 6 blocks. The
 * lightning is visual only (no fire, no transformed mobs); never hits players, pets or minions.</li>
 * <li>Heartwood Aegis: blocking with it heals you; holding it gives players within 6 blocks Regeneration I.</li>
 * </ul>
 */
public final class HollowGearListener implements Listener {

    public static final String CROWN = ItemKeys.slimefunId("HOLLOW_HELMET");
    public static final String CUIRASS = ItemKeys.slimefunId("HOLLOW_CHESTPLATE");
    public static final String GREAVES = ItemKeys.slimefunId("HOLLOW_LEGGINGS");
    public static final String SABATONS = ItemKeys.slimefunId("HOLLOW_BOOTS");
    private static final String DREADLANCE = ItemKeys.slimefunId("DREADLANCE");
    private static final String STORMSTRING = ItemKeys.slimefunId("STORMSTRING_BOW");
    private static final String AEGIS = ItemKeys.slimefunId("HEARTWOOD_AEGIS");
    private static final org.bukkit.NamespacedKey STORM_ARROW = new org.bukkit.NamespacedKey("occultech", "storm_arrow");
    private static final double LIFESTEAL = 0.15;
    private static final double LIFESTEAL_CAP_PER_SECOND = 4;
    private static final double STORM_DAMAGE = 12;
    private static final double ARC_DAMAGE = 8;
    private static final Particle.DustOptions WISP = new Particle.DustOptions(Color.fromRGB(90, 220, 230), 0.6F);
    private static final Particle.DustOptions ABYSSAL = new Particle.DustOptions(Color.fromRGB(60, 200, 190), 0.7F);

    private final Map<UUID, double[]> lifesteal = new HashMap<>();
    private int ticks;

    public HollowGearListener(Plugin plugin) {
        Bukkit.getScheduler().runTaskTimer(plugin, this::tick, 10L, 10L);
    }

    private void tick() {
        ticks += 10;
        for (Player player : Bukkit.getOnlinePlayers()) {
            if (ticks % 20 == 0 && WeaponListener.wearsAbyssalSet(player)) {
                // Abyssal set: bubbles rising around you and a slow teal swirl at your feet
                ThreadLocalRandom random = ThreadLocalRandom.current();
                player.getWorld().spawnParticle(Particle.BUBBLE_POP, player.getLocation().add(random.nextDouble(-0.4, 0.4), random.nextDouble(0.2, 1.8),
                    random.nextDouble(-0.4, 0.4)), 2, 0.05, 0.1, 0.05, 0.02);
                double a = ticks * 0.05;
                for (int i = 0; i < 3; i++) {
                    double angle = a + Math.PI * 2 * i / 3;
                    player.getWorld().spawnParticle(Particle.DUST, player.getLocation().add(Math.cos(angle) * 0.6, 0.1, Math.sin(angle) * 0.6), 1, 0, 0, 0, 0,
                        ABYSSAL);
                }
                if (random.nextInt(4) == 0) {
                    player.getWorld().spawnParticle(Particle.NAUTILUS, player.getLocation().add(0, 1.2, 0), 3, 0.3, 0.4, 0.3, 0.2);
                }
            }
            if (wearsHollowSet(player) && ticks % 20 == 0) {
                player.getWorld().spawnParticle(Particle.DUST, player.getLocation().add(0, 1, 0), 2, 0.3, 0.5, 0.3, 0, WISP);
                player.getWorld().spawnParticle(Particle.SOUL, player.getLocation().add(0, 0.2, 0), 1, 0.2, 0.1, 0.2, 0.005);
            }
            boolean aegisHeld = is(player.getInventory().getItemInMainHand(), AEGIS) || is(player.getInventory().getItemInOffHand(), AEGIS);
            if (!aegisHeld) {
                continue;
            }
            if (player.isBlocking()) {
                double max = player.getAttribute(Attribute.MAX_HEALTH).getValue();
                player.setHealth(Math.min(max, player.getHealth() + 1));
                player.getWorld().spawnParticle(Particle.HAPPY_VILLAGER, player.getLocation().add(0, 1.2, 0), 2, 0.3, 0.3, 0.3, 0);
            }
            if (ticks % 40 == 0) {
                for (Player ally : player.getWorld().getNearbyPlayers(player.getLocation(), 6)) {
                    ally.addPotionEffect(new PotionEffect(PotionEffectType.REGENERATION, 60, 0, true, true, true));
                }
            }
        }
    }

    // ------------------------------------------------------------------ Hollow armor

    @EventHandler(ignoreCancelled = true)
    public void onEffect(EntityPotionEffectEvent e) {
        if (!(e.getEntity() instanceof Player player) || e.getNewEffect() == null) {
            return;
        }
        PotionEffectType type = e.getNewEffect().getType();
        boolean blocked = ((type == PotionEffectType.DARKNESS || type == PotionEffectType.BLINDNESS) && is(player.getInventory().getHelmet(), CROWN))
            || (type == PotionEffectType.WITHER && is(player.getInventory().getChestplate(), CUIRASS))
            || (type == PotionEffectType.SLOWNESS && is(player.getInventory().getLeggings(), GREAVES));
        if (blocked) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onFall(EntityDamageEvent e) {
        if (e.getCause() == EntityDamageEvent.DamageCause.FALL && e.getEntity() instanceof Player player && is(player.getInventory().getBoots(), SABATONS)) {
            e.setCancelled(true);
        }
    }

    public static boolean wearsHollowSet(Player player) {
        return is(player.getInventory().getHelmet(), CROWN) && is(player.getInventory().getChestplate(), CUIRASS)
            && is(player.getInventory().getLeggings(), GREAVES) && is(player.getInventory().getBoots(), SABATONS);
    }

    // ------------------------------------------------------------------ Dreadlance

    /** How long battle regeneration lasts after a hit, and when a hit tops it up (ticks). */
    private static final int BATTLE_REGEN_TICKS = 100;
    private static final int BATTLE_REGEN_TOP_UP = 50;

    /**
     * Hollow set (4/4): every hit the wearer lands - melee, arrow, held weapon - keeps Regeneration I going. The effect is
     * only topped up once half of it has run, because Regeneration I heals when its remaining time crosses a multiple of
     * 50 ticks: refreshed on every hit, a fast attacker would never reach one and never heal.
     */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onBattleRegen(EntityDamageByEntityEvent e) {
        Entity source = e.getDamager() instanceof Projectile projectile && projectile.getShooter() instanceof Entity shooter ? shooter : e.getDamager();
        if (!(source instanceof Player player) || !(e.getEntity() instanceof LivingEntity) || e.getEntity() instanceof org.bukkit.entity.ArmorStand
            || e.getFinalDamage() <= 0 || !wearsHollowSet(player)) {
            return;
        }
        PotionEffect current = player.getPotionEffect(PotionEffectType.REGENERATION);
        if (current == null || (current.getAmplifier() == 0 && current.getDuration() <= BATTLE_REGEN_TOP_UP)) {
            player.addPotionEffect(new PotionEffect(PotionEffectType.REGENERATION, BATTLE_REGEN_TICKS, 0, true, true, true));
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onLanceHit(EntityDamageByEntityEvent e) {
        if (!(e.getDamager() instanceof Player player) || !is(player.getInventory().getItemInMainHand(), DREADLANCE)
            || !(e.getEntity() instanceof LivingEntity) || e.getFinalDamage() <= 0) {
            return;
        }
        long second = System.currentTimeMillis() / 1000;
        double[] window = lifesteal.computeIfAbsent(player.getUniqueId(), k -> new double[] { second, 0 });
        if (window[0] != second) {
            window[0] = second;
            window[1] = 0;
        }
        double heal = Math.min(e.getFinalDamage() * LIFESTEAL, LIFESTEAL_CAP_PER_SECOND - window[1]);
        if (heal <= 0) {
            return;
        }
        window[1] += heal;
        double max = player.getAttribute(Attribute.MAX_HEALTH).getValue();
        player.setHealth(Math.min(max, player.getHealth() + heal));
        player.getWorld().spawnParticle(Particle.DUST, e.getEntity().getLocation().add(0, 1, 0), 6, 0.3, 0.4, 0.3, 0,
            new Particle.DustOptions(Color.fromRGB(170, 0, 20), 1F));
    }

    // ------------------------------------------------------------------ Stormstring Bow

    @EventHandler(ignoreCancelled = true)
    public void onShoot(EntityShootBowEvent e) {
        if (e.getEntity() instanceof Player && is(e.getBow(), STORMSTRING) && e.getProjectile() instanceof AbstractArrow arrow) {
            arrow.getPersistentDataContainer().set(STORM_ARROW, PersistentDataType.BYTE, (byte) 1);
            arrow.setPickupStatus(AbstractArrow.PickupStatus.CREATIVE_ONLY);
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onStormHit(EntityDamageByEntityEvent e) {
        if (!(e.getDamager() instanceof Projectile arrow) || !arrow.getPersistentDataContainer().has(STORM_ARROW)
            || !(arrow.getShooter() instanceof Player shooter) || !(e.getEntity() instanceof LivingEntity hit) || !stormTarget(hit)) {
            return;
        }
        arrow.getPersistentDataContainer().remove(STORM_ARROW);
        Bukkit.getScheduler().runTask(Bukkit.getPluginManager().getPlugin("Occultech"), () -> {
            if (!hit.isValid()) {
                return;
            }
            // visual lightning only: never fire, never charged creepers or turned pigs/villagers
            hit.getWorld().strikeLightningEffect(hit.getLocation());
            HeldWeapons.strike(hit, STORM_DAMAGE, shooter);
            int arcs = 0;
            for (Entity near : hit.getNearbyEntities(6, 4, 6)) {
                if (arcs >= 2) {
                    break;
                }
                if (near instanceof LivingEntity next && next != hit && stormTarget(next) && (next instanceof Monster || Keys.isSummoned(next))) {
                    arcs++;
                    drawArc(hit, next);
                    next.getWorld().strikeLightningEffect(next.getLocation());
                    HeldWeapons.strike(next, ARC_DAMAGE, shooter);
                }
            }
        });
    }

    /** Never players, pets, necromancy minions, or display-only creatures. */
    private static boolean stormTarget(LivingEntity entity) {
        return !(entity instanceof Player) && !(entity instanceof Tameable tame && tame.isTamed()) && Keys.minionOwner(entity) == null
            && !entity.getPersistentDataContainer().has(Keys.HOLOGRAM) && !(entity instanceof org.bukkit.entity.ArmorStand);
    }

    private static void drawArc(LivingEntity from, LivingEntity to) {
        var a = from.getLocation().add(0, from.getHeight() / 2, 0);
        var b = to.getLocation().add(0, to.getHeight() / 2, 0);
        var step = b.toVector().subtract(a.toVector());
        double length = step.length();
        step.normalize().multiply(0.4);
        var point = a.clone();
        for (double d = 0; d < length; d += 0.4) {
            point.getWorld().spawnParticle(Particle.ELECTRIC_SPARK, point, 1, 0.05, 0.05, 0.05, 0);
            point.add(step);
        }
        from.getWorld().playSound(a, Sound.ENTITY_LIGHTNING_BOLT_IMPACT, 0.6F, 1.6F);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        lifesteal.remove(e.getPlayer().getUniqueId());
    }

    static boolean is(ItemStack item, String id) {
        if (item == null || item.getType().isAir()) {
            return false;
        }
        SlimefunItem sfItem = SlimefunItem.getByItem(item);
        return sfItem != null && sfItem.getId().equals(id);
    }
}
