package io.github.amitelia.occultech.boss.tier2;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Drowned;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Trident;
import org.bukkit.entity.ZombieNautilus;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-2 mini-boss (max netherite). A drowned champion riding a zombie nautilus that "swims" through the air over land.
 * <ul>
 * <li>Ram charge: a line warns for 1s, then the nautilus charges along it, hurting and throwing anyone in the way.
 * After a charge it is <b>winded for 2s</b> - the melee window.</li>
 * <li>Trident volley: three tridents in a fan (they can't be picked up).</li>
 * <li>Melee: the rider's trident strikes anyone close.</li>
 * </ul>
 * The nautilus can't be hurt; only the rider counts. Takes a third of the damage dealt.
 */
public final class Tidebreaker extends BossBehavior {

    private static final double HEALTH = 300;
    private static final double ARMOR = 0.33;
    private static final Color WARNING = Color.fromRGB(40, 110, 200);
    private static final int CHARGE_INTERVAL = 160;
    private static final int CHARGE_WARNING = 20;
    private static final int CHARGE_TICKS = 25;
    private static final int WINDED_TICKS = 40;
    private static final int VOLLEY_INTERVAL = 200;
    private static final double RAM_DAMAGE = 38;
    private static final double MELEE_DAMAGE = 28;
    private static final double TRIDENT_DAMAGE = 24;

    private Drowned rider;
    private ZombieNautilus mount;
    private Vector chargeDirection;
    private int chargeAt = -1;
    private int chargeEnd = -1;
    private int windedUntil = -1;
    private int nextCharge = 80;
    private int nextMelee;
    private final java.util.Set<java.util.UUID> rammed = new java.util.HashSet<>();
    /** Who the nautilus swims after (chosen each step, followed every tick). */
    private Player chase;

    public Tidebreaker(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        Location start = at.clone().add(0, 1, 0);
        mount = fight.spawnExtra(ZombieNautilus.class, start, n -> {
            Abyss.puppet(n);
            n.setInvulnerable(true);
            n.setRemoveWhenFarAway(false);
            BossFight.setAttribute(n, Attribute.SCALE, 1.6);
        });
        rider = fight.spawnBoss(Drowned.class, start, d -> {
            d.setCustomName(ChatColor.BLUE + "Tidebreaker");
            d.setCustomNameVisible(true);
            Abyss.puppet(d);
            d.setGravity(true);
            d.setAdult();
            d.getEquipment().setItemInMainHand(new ItemStack(Material.TRIDENT));
            d.getEquipment().setHelmet(new ItemStack(Material.TURTLE_HELMET));
            BossFight.setAttribute(d, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(d, Attribute.SCALE, 1.3);
        });
        mount.addPassenger(rider);
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR;
    }

    @Override
    public void tick() {
        if (!rider.isValid()) {
            return;
        }
        int now = fight.elapsed();
        remount();

        if (now < windedUntil) {
            rider.getWorld().spawnParticle(Particle.SPLASH, rider.getLocation().add(0, 1.5, 0), 6, 0.4, 0.3, 0.4, 0);
            return;
        }
        if (chargeEnd >= 0) {
            return; // move() drives the charge
        }
        if (chargeAt >= 0) {
            if (now >= chargeAt) {
                chargeAt = -1;
                chargeEnd = now + CHARGE_TICKS;
                rammed.clear();
                mount.getWorld().playSound(mount.getLocation(), Sound.ENTITY_DOLPHIN_JUMP, 2F, 0.5F);
            }
            return;
        }

        Player target = fight.nearestPlayer(mount.getLocation());
        chase = target;
        if (target == null) {
            return;
        }
        Abyss.face(rider, target.getEyeLocation());

        if (now >= nextMelee && target.getLocation().distanceSquared(rider.getLocation()) <= 16) {
            nextMelee = now + 20;
            rider.swingMainHand();
            target.damage(MELEE_DAMAGE, rider);
        }
        if (every(VOLLEY_INTERVAL)) {
            volley(target);
        }
        if (now >= nextCharge) {
            nextCharge = now + CHARGE_INTERVAL;
            Player victim = fight.randomPlayer();
            if (victim != null) {
                chargeDirection = victim.getLocation().toVector().subtract(mount.getLocation().toVector()).setY(0);
                if (chargeDirection.lengthSquared() < 1) {
                    chargeDirection = new Vector(1, 0, 0);
                }
                chargeDirection.normalize();
                chargeAt = now + CHARGE_WARNING;
                warnLine();
            }
        }
    }

    @Override
    public void move() {
        if (!rider.isValid() || !mount.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (now < windedUntil || chargeAt >= 0) {
            mount.setVelocity(new Vector());
        } else if (chargeEnd >= 0) {
            charge(now);
        } else if (chase != null && chase.isValid() && chase.getWorld() == mount.getWorld()) {
            Abyss.glide(mount, chase.getLocation(), 0.2, 0.4, 2.5);
        } else {
            Abyss.glide(mount, fight.center(), 0.12, 0.4, 0);
        }
    }

    /** One tick of the ram charge. */
    private void charge(int now) {
        Location at = mount.getLocation();
        boolean blocked = !at.clone().add(chargeDirection.clone().multiply(1.5)).add(0, 0.5, 0).getBlock().isPassable();
        boolean outside = at.distanceSquared(fight.center()) > fight.radius() * fight.radius();
        if (now >= chargeEnd || blocked || outside) {
            chargeEnd = -1;
            windedUntil = now + WINDED_TICKS;
            mount.setVelocity(new Vector());
            fight.broadcast("&9The Tidebreaker is winded - &fstrike now!");
            return;
        }
        Vector velocity = chargeDirection.clone().multiply(0.7);
        velocity.setY((Abyss.groundY(at) + 0.4 - at.getY()) * 0.3);
        mount.setVelocity(velocity);
        at.getWorld().spawnParticle(Particle.BUBBLE_POP, at.clone().add(0, 0.8, 0), 4, 0.6, 0.4, 0.6, 0.05);
        for (Player player : fight.players()) {
            if (!rammed.contains(player.getUniqueId()) && player.getLocation().distanceSquared(at) <= 4.5) {
                rammed.add(player.getUniqueId());
                player.damage(RAM_DAMAGE, rider);
                player.setVelocity(chargeDirection.clone().multiply(1.1).setY(0.5));
            }
        }
    }

    private void warnLine() {
        Location from = mount.getLocation().add(0, 0.2, 0);
        Particle.DustOptions dust = new Particle.DustOptions(WARNING, 1.6F);
        for (double d = 0; d < 16; d += 0.5) {
            Location point = from.clone().add(chargeDirection.clone().multiply(d));
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0.3, 0, 0.3, 0, dust);
        }
        mount.getWorld().playSound(from, Sound.ENTITY_DROWNED_AMBIENT, 2F, 0.6F);
    }

    private void volley(Player target) {
        Location eye = rider.getEyeLocation();
        Vector aim = target.getEyeLocation().toVector().subtract(eye.toVector()).normalize();
        rider.swingMainHand();
        for (int i = -1; i <= 1; i++) {
            Vector direction = aim.clone().rotateAroundY(Math.toRadians(12 * i)).multiply(1.8).add(new Vector(0, 0.12, 0));
            Trident trident = rider.launchProjectile(Trident.class, direction);
            trident.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, TRIDENT_DAMAGE);
        }
        eye.getWorld().playSound(eye, Sound.ITEM_TRIDENT_THROW, 1.5F, 0.8F);
    }

    /** The engine may teleport the rider (leash, anti-pillar), which dismounts it: bring the nautilus along. */
    private void remount() {
        if (!mount.isValid() || mount.getPassengers().contains(rider)) {
            return;
        }
        mount.teleport(rider.getLocation());
        mount.addPassenger(rider);
    }
}
