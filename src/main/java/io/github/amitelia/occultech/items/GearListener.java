package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.bukkit.Bukkit;
import org.bukkit.GameMode;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.player.PlayerItemMendEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.player.PlayerToggleFlightEvent;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.SkullMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;

/**
 * Tier-1 gear behavior.
 * <ul>
 * <li>Frenzy Cleaver: each hit within 3s of the last adds a stack of attack speed (max 5); stacks fade after 3s.</li>
 * <li>Duskwing Charm (carried): press jump in mid-air to double jump; no fall damage from that jump. 4s cooldown.</li>
 * <li>Mirror Ward (carried): dropping below 30% health spawns a decoy of you that nearby mobs chase for 5s. 60s cooldown.</li>
 * <li>Mending never repairs Occultech gear (it is repaired with its boss drop instead).</li>
 * <li>The Bone Scepter can't be used on animals (it looks like a bone, but it isn't one).</li>
 * <li>Abyssal armor (tier 2): helm Water Breathing, greaves Conduit Power while in water, boots Dolphin's Grace.
 * The 4/4 set bonus is in {@link WeaponListener}.</li>
 * </ul>
 */
public final class GearListener implements Listener {

    private static final String CLEAVER = ItemKeys.slimefunId("FRENZY_CLEAVER");
    private static final String DUSKWING = ItemKeys.slimefunId("DUSKWING_CHARM");
    private static final String MIRROR_WARD = ItemKeys.slimefunId("MIRROR_WARD");
    private static final String SCEPTER = ItemKeys.slimefunId("BONE_SCEPTER");
    private static final String ABYSSAL_HELMET = ItemKeys.slimefunId("ABYSSAL_HELMET");
    private static final String ABYSSAL_LEGGINGS = ItemKeys.slimefunId("ABYSSAL_LEGGINGS");
    private static final String ABYSSAL_BOOTS = ItemKeys.slimefunId("ABYSSAL_BOOTS");
    private static final NamespacedKey FRENZY = new NamespacedKey("occultech", "frenzy");
    private static final int MAX_STACKS = 5;
    private static final long STACK_WINDOW_MS = 3000;
    private static final long JUMP_COOLDOWN_MS = 4000;
    private static final long WARD_COOLDOWN_MS = 60_000;

    private final Plugin plugin;
    private final Map<UUID, Integer> stacks = new HashMap<>();
    private final Map<UUID, Long> lastHit = new HashMap<>();
    private final Map<UUID, Long> jumpReady = new HashMap<>();
    private final Map<UUID, Long> wardReady = new HashMap<>();
    private final Set<UUID> grantedFlight = new HashSet<>();
    private final Set<UUID> noFall = new HashSet<>();

    public GearListener(Plugin plugin) {
        this.plugin = plugin;
        Bukkit.getScheduler().runTaskTimer(plugin, this::tick, 5L, 5L);
    }

    private void tick() {
        long now = System.currentTimeMillis();
        for (Player player : Bukkit.getOnlinePlayers()) {
            UUID id = player.getUniqueId();

            // frenzy stacks fade
            Long last = lastHit.get(id);
            if (last != null && now - last > STACK_WINDOW_MS) {
                lastHit.remove(id);
                stacks.remove(id);
                setFrenzy(player, 0);
            }

            // double jump: allow "flight" while grounded with the charm, so pressing jump in mid-air fires the toggle event
            boolean survival = player.getGameMode() == GameMode.SURVIVAL || player.getGameMode() == GameMode.ADVENTURE;
            if (survival && player.isOnGround() && now >= jumpReady.getOrDefault(id, 0L) && carries(player, DUSKWING)) {
                if (!player.getAllowFlight()) {
                    player.setAllowFlight(true);
                    grantedFlight.add(id);
                }
            } else if (grantedFlight.contains(id) && (!survival || !carries(player, DUSKWING))) {
                player.setAllowFlight(false);
                grantedFlight.remove(id);
            }
            if (player.isOnGround()) {
                noFall.remove(id);
            }

            // abyssal armor
            if (is(player.getInventory().getHelmet(), ABYSSAL_HELMET)) {
                refresh(player, PotionEffectType.WATER_BREATHING);
            }
            if (player.isInWater() && is(player.getInventory().getLeggings(), ABYSSAL_LEGGINGS)) {
                refresh(player, PotionEffectType.CONDUIT_POWER);
            }
            if (is(player.getInventory().getBoots(), ABYSSAL_BOOTS)) {
                refresh(player, PotionEffectType.DOLPHINS_GRACE);
            }
        }
    }

    /** Keeps a worn-gear effect up (ambient, no particles) without replacing a stronger or longer one. */
    private static void refresh(Player player, PotionEffectType type) {
        PotionEffect current = player.getPotionEffect(type);
        if (current == null || (current.getAmplifier() == 0 && current.getDuration() < 40)) {
            player.addPotionEffect(new PotionEffect(type, 80, 0, true, false, true));
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onDoubleJump(PlayerToggleFlightEvent e) {
        Player player = e.getPlayer();
        if (!grantedFlight.contains(player.getUniqueId()) || !e.isFlying()) {
            return;
        }
        e.setCancelled(true);
        player.setAllowFlight(false);
        grantedFlight.remove(player.getUniqueId());
        jumpReady.put(player.getUniqueId(), System.currentTimeMillis() + JUMP_COOLDOWN_MS);
        noFall.add(player.getUniqueId());
        Vector boost = player.getLocation().getDirection().setY(0).normalize().multiply(0.6).setY(0.85);
        player.setVelocity(boost);
        player.getWorld().spawnParticle(Particle.CLOUD, player.getLocation(), 12, 0.3, 0.1, 0.3, 0.02);
        player.getWorld().playSound(player.getLocation(), Sound.ENTITY_PHANTOM_FLAP, 1F, 1.2F);
    }

    @EventHandler(ignoreCancelled = true)
    public void onFall(EntityDamageEvent e) {
        if (e.getCause() == EntityDamageEvent.DamageCause.FALL && noFall.remove(e.getEntity().getUniqueId())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onCleaverHit(EntityDamageByEntityEvent e) {
        if (!(e.getDamager() instanceof Player player) || !is(player.getInventory().getItemInMainHand(), CLEAVER)) {
            return;
        }
        long now = System.currentTimeMillis();
        UUID id = player.getUniqueId();
        Long last = lastHit.get(id);
        int stack = last != null && now - last <= STACK_WINDOW_MS ? Math.min(MAX_STACKS, stacks.getOrDefault(id, 0) + 1) : 1;
        stacks.put(id, stack);
        lastHit.put(id, now);
        setFrenzy(player, stack);
        if (stack == MAX_STACKS) {
            player.getWorld().spawnParticle(Particle.ANGRY_VILLAGER, player.getLocation().add(0, 2, 0), 1);
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onLowHealth(EntityDamageEvent e) {
        if (!(e.getEntity() instanceof Player player)) {
            return;
        }
        double max = player.getAttribute(Attribute.MAX_HEALTH).getValue();
        double after = player.getHealth() - e.getFinalDamage();
        long now = System.currentTimeMillis();
        if (after <= 0 || after > max * 0.3 || now < wardReady.getOrDefault(player.getUniqueId(), 0L) || !carries(player, MIRROR_WARD)) {
            return;
        }
        wardReady.put(player.getUniqueId(), now + WARD_COOLDOWN_MS);
        spawnDecoy(player);
    }

    /** Tools and weapons that look like blocks (the Gaze is an end rod, the Censer a soul torch) are never placed. */
    @EventHandler(priority = EventPriority.LOWEST, ignoreCancelled = true)
    public void onPlace(org.bukkit.event.block.BlockPlaceEvent e) {
        SlimefunItem item = SlimefunItem.getByItem(e.getItemInHand());
        if (item instanceof io.github.thebusybiscuit.slimefun4.core.attributes.NotPlaceable && item.getId().startsWith(ItemKeys.PREFIX)) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onMend(PlayerItemMendEvent e) {
        SlimefunItem item = SlimefunItem.getByItem(e.getItem());
        if (item != null && item.getId().startsWith(ItemKeys.PREFIX)) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onScepterOnEntity(PlayerInteractEntityEvent e) {
        if (is(e.getPlayer().getInventory().getItem(e.getHand()), SCEPTER)) {
            e.setCancelled(true);
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        UUID id = e.getPlayer().getUniqueId();
        if (grantedFlight.remove(id)) {
            e.getPlayer().setAllowFlight(false);
        }
        setFrenzy(e.getPlayer(), 0);
        stacks.remove(id);
        lastHit.remove(id);
        noFall.remove(id);
    }

    // ------------------------------------------------------------------ helpers

    private void spawnDecoy(Player player) {
        ArmorStand decoy = player.getWorld().spawn(player.getLocation(), ArmorStand.class, stand -> {
            stand.setPersistent(false);
            stand.setInvulnerable(true);
            stand.setArms(true);
            stand.setBasePlate(false);
            ItemStack head = new ItemStack(Material.PLAYER_HEAD);
            SkullMeta meta = (SkullMeta) head.getItemMeta();
            meta.setOwningPlayer(player);
            head.setItemMeta(meta);
            stand.getEquipment().setHelmet(head);
            stand.getEquipment().setChestplate(player.getInventory().getChestplate());
            stand.getEquipment().setLeggings(player.getInventory().getLeggings());
            stand.getEquipment().setBoots(player.getInventory().getBoots());
            // tagged like a minion so bosses are allowed to chase it
            stand.getPersistentDataContainer().set(Keys.MINION_OWNER, PersistentDataType.STRING, player.getUniqueId().toString());
        });
        player.getWorld().spawnParticle(Particle.CLOUD, player.getLocation().add(0, 1, 0), 20, 0.4, 0.8, 0.4, 0.02);
        player.getWorld().playSound(player.getLocation(), Sound.ENTITY_ILLUSIONER_MIRROR_MOVE, 1F, 1F);
        player.sendMessage(org.bukkit.ChatColor.AQUA + "Your Mirror Ward leaves a decoy behind!");

        for (int i = 0; i < 10; i++) {
            Bukkit.getScheduler().runTaskLater(plugin, () -> {
                if (!decoy.isValid()) {
                    return;
                }
                for (Entity nearby : decoy.getNearbyEntities(12, 6, 12)) {
                    if (nearby instanceof Mob mob && mob.getTarget() == player) {
                        mob.setTarget(decoy);
                    }
                }
            }, i * 10L);
        }
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            decoy.getWorld().spawnParticle(Particle.BLOCK, decoy.getLocation().add(0, 1, 0), 25, 0.3, 0.6, 0.3, Material.GLASS.createBlockData());
            decoy.remove();
        }, 100L);
    }

    private static void setFrenzy(Player player, int stack) {
        AttributeInstance speed = player.getAttribute(Attribute.ATTACK_SPEED);
        if (speed == null) {
            return;
        }
        for (AttributeModifier modifier : speed.getModifiers()) {
            if (FRENZY.equals(modifier.getKey())) {
                speed.removeModifier(modifier);
            }
        }
        if (stack > 0) {
            speed.addModifier(new AttributeModifier(FRENZY, 0.2 * stack, AttributeModifier.Operation.ADD_NUMBER, EquipmentSlotGroup.ANY));
        }
    }

    private static boolean carries(Player player, String id) {
        for (ItemStack item : player.getInventory().getContents()) {
            if (is(item, id)) {
                return true;
            }
        }
        return false;
    }

    private static boolean is(ItemStack item, String id) {
        if (item == null || item.getType().isAir()) {
            return false;
        }
        SlimefunItem sfItem = SlimefunItem.getByItem(item);
        return sfItem != null && sfItem.getId().equals(id);
    }
}
