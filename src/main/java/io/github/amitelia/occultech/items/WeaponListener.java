package io.github.amitelia.occultech.items;

import org.bukkit.Bukkit;
import org.bukkit.Sound;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityShootBowEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.Plugin;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;

/**
 * Tier-0 weapon and charm behavior.
 * <ul>
 * <li>Quillshot Bow: a fully drawn shot fires two more arrows 3 ticks apart. The extra arrows can't be picked up,
 * so the bow never creates arrows.</li>
 * <li>Warding Charm: while carried, damage from summoned creatures (entities tagged {@link Keys#SUMMONED}) is reduced by 15%.
 * Only one charm counts.</li>
 * <li>Abyssal armor 4/4 (tier 2): damage from summoned creatures is reduced by 20% (stacks with the charm).</li>
 * </ul>
 */
public final class WeaponListener implements Listener {

    public static final String QUILLSHOT_BOW = ItemKeys.slimefunId("QUILLSHOT_BOW");
    public static final String WARDING_CHARM = ItemKeys.slimefunId("WARDING_CHARM");
    private static final float FULL_DRAW = 0.95F;
    private static final double WARDING_MULTIPLIER = 0.85;
    private static final double ABYSSAL_SET_MULTIPLIER = 0.8;
    private static final java.util.List<String> ABYSSAL_SET = java.util.List.of(ItemKeys.slimefunId("ABYSSAL_HELMET"),
        ItemKeys.slimefunId("ABYSSAL_CHESTPLATE"), ItemKeys.slimefunId("ABYSSAL_LEGGINGS"), ItemKeys.slimefunId("ABYSSAL_BOOTS"));

    private final Plugin plugin;

    public WeaponListener(Plugin plugin) {
        this.plugin = plugin;
    }

    @EventHandler(ignoreCancelled = true)
    public void onShoot(EntityShootBowEvent e) {
        if (!(e.getEntity() instanceof Player player) || e.getForce() < FULL_DRAW || !(e.getProjectile() instanceof AbstractArrow first)) {
            return;
        }
        SlimefunItem bow = SlimefunItem.getByItem(e.getBow());
        if (bow == null || !bow.getId().equals(QUILLSHOT_BOW) || !bow.canUse(player, true)) {
            return;
        }

        double speed = first.getVelocity().length();
        double damage = first.getDamage();
        boolean critical = first.isCritical();
        for (int i = 1; i <= 2; i++) {
            Bukkit.getScheduler().runTaskLater(plugin, () -> {
                if (!player.isOnline() || player.isDead()) {
                    return;
                }
                Arrow arrow = player.launchProjectile(Arrow.class, player.getLocation().getDirection().multiply(speed));
                arrow.setDamage(damage);
                arrow.setCritical(critical);
                arrow.setPickupStatus(AbstractArrow.PickupStatus.CREATIVE_ONLY);
                player.getWorld().playSound(player.getLocation(), Sound.ENTITY_ARROW_SHOOT, 1F, 1.4F);
            }, i * 3L);
        }
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onDamage(EntityDamageByEntityEvent e) {
        if (!(e.getEntity() instanceof Player player)) {
            return;
        }
        Entity source = e.getDamager();
        if (source instanceof Projectile projectile && projectile.getShooter() instanceof Entity shooter) {
            source = shooter;
        }
        if (!Keys.isSummoned(source)) {
            return;
        }
        if (carries(player, WARDING_CHARM)) {
            e.setDamage(e.getDamage() * WARDING_MULTIPLIER);
        }
        if (wearsAbyssalSet(player)) {
            e.setDamage(e.getDamage() * ABYSSAL_SET_MULTIPLIER);
        }
    }

    public static boolean wearsAbyssalSet(Player player) {
        ItemStack[] armor = { player.getInventory().getHelmet(), player.getInventory().getChestplate(), player.getInventory().getLeggings(),
            player.getInventory().getBoots() };
        for (int i = 0; i < armor.length; i++) {
            SlimefunItem piece = armor[i] == null || armor[i].getType().isAir() ? null : SlimefunItem.getByItem(armor[i]);
            if (piece == null || !piece.getId().equals(ABYSSAL_SET.get(i))) {
                return false;
            }
        }
        return true;
    }

    private static boolean carries(Player player, String id) {
        for (ItemStack item : player.getInventory().getContents()) {
            if (item != null && !item.getType().isAir()) {
                SlimefunItem sfItem = SlimefunItem.getByItem(item);
                if (sfItem != null && sfItem.getId().equals(id)) {
                    return true;
                }
            }
        }
        return false;
    }
}
