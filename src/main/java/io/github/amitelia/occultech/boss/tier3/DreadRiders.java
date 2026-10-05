package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.AbstractHorse;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Skeleton;
import org.bukkit.entity.SkeletonHorse;
import org.bukkit.entity.Trident;
import org.bukkit.entity.Zombie;
import org.bukkit.entity.ZombieHorse;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-3 mini-boss (Infinity gear): two fast horsemen. Each rider has its own health; the horses can't be hurt.
 * <ul>
 * <li><b>Outrider</b> (skeleton): fragile and evasive, circles its target 14 blocks out. Snipe: an aiming line locks
 * on and fires, ending in a lightning strike; arrow volleys; arrow rain on a warned circle. All its lightning is
 * visual only (flash and thunder, no fire, no mob changes); the damage is the plugin's.</li>
 * <li><b>Vanguard</b> (zombie with a spear): tanky and brutal up close; warned lance charges (stunned 2s if cut short);
 * intercepts anyone who gets within 8 blocks of the Outrider.</li>
 * <li>When one falls, the other enrages: the Vanguard starts throwing spears, or the Outrider fires faster and closer.</li>
 * </ul>
 */
public final class DreadRiders extends BossBehavior {

    private static final double OUTRIDER_HEALTH = 200;
    private static final double VANGUARD_HEALTH = 260;
    private static final double OUTRIDER_ARMOR = 0.1;
    private static final double VANGUARD_ARMOR = 0.05;
    private static final io.github.amitelia.occultech.boss.Mechanic SNIPE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Storm snipe", 30, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic ARROW_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Arrow", 26, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic RAIN_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Arrow rain", 35, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic MELEE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Vanguard blade", 50, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic RAM_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Charge", 60, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic SPEAR_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Thrown spear", 40, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final double ORBIT = 14;
    private static final double ORBIT_ENRAGED = 8;
    private static final int CHARGE_WARNING = 20;
    private static final int CHARGE_TICKS = 25;
    private static final int STUN_TICKS = 40;
    private static final Color STORM = Color.fromRGB(170, 200, 255);
    private static final Color LANCE = Color.fromRGB(120, 20, 20);

    private Skeleton outrider;
    private Zombie vanguard;
    private SkeletonHorse outriderHorse;
    private ZombieHorse vanguardHorse;
    private Player outriderTarget;
    private Player vanguardTarget;
    private boolean outriderDown;
    private boolean vanguardDown;
    private double orbitAngle;
    private final List<Abyss.Beam> snipes = new ArrayList<>();
    private int rainAt = -1;
    private Location rainSpot;
    private Vector chargeDirection;
    private int chargeAt = -1;
    private int chargeEnd = -1;
    private int stunnedUntil = -1;
    private int nextCharge = 120;
    private int nextMelee;
    private final Set<UUID> rammed = new HashSet<>();

    public DreadRiders(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        Location west = at.clone().add(-4, 1, 0);
        Location east = at.clone().add(4, 1, 0);
        outriderHorse = fight.spawnExtra(SkeletonHorse.class, west, h -> mount(h));
        vanguardHorse = fight.spawnExtra(ZombieHorse.class, east, h -> mount(h));
        outrider = fight.spawnBoss(Skeleton.class, west, s -> {
            s.setCustomName(ChatColor.AQUA + "The Outrider");
            s.setCustomNameVisible(true);
            Abyss.puppet(s);
            s.setGravity(true);
            s.setShouldBurnInDay(false);
            s.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
            s.getEquipment().setHelmet(new ItemStack(Material.CHAINMAIL_HELMET));
            BossFight.setAttribute(s, Attribute.MAX_HEALTH, OUTRIDER_HEALTH);
        });
        vanguard = fight.spawnBoss(Zombie.class, east, z -> {
            z.setCustomName(ChatColor.DARK_RED + "The Vanguard");
            z.setCustomNameVisible(true);
            Abyss.puppet(z);
            z.setGravity(true);
            z.setAdult();
            z.setShouldBurnInDay(false);
            z.getEquipment().setItemInMainHand(new ItemStack(Material.NETHERITE_SPEAR));
            z.getEquipment().setHelmet(new ItemStack(Material.NETHERITE_HELMET));
            z.getEquipment().setChestplate(new ItemStack(Material.NETHERITE_CHESTPLATE));
            BossFight.setAttribute(z, Attribute.MAX_HEALTH, VANGUARD_HEALTH);
            BossFight.setAttribute(z, Attribute.SCALE, 1.2);
        });
        outriderHorse.addPassenger(outrider);
        vanguardHorse.addPassenger(vanguard);
    }

    private static void mount(AbstractHorse horse) {
        Abyss.puppet(horse);
        horse.setGravity(true);
        horse.setInvulnerable(true);
        Keys.setUnhittable(horse, true);
        horse.setTamed(true);
        BossFight.setAttribute(horse, Attribute.SCALE, 1.2);
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * (boss == vanguard ? VANGUARD_ARMOR : OUTRIDER_ARMOR);
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    // ------------------------------------------------------------------ every tick: the horses ride

    @Override
    public void move() {
        int now = fight.elapsed();
        if (!outriderDown && outriderHorse.isValid() && alive(outriderTarget)) {
            orbitAngle += 0.02;
            Location target = outriderTarget.getLocation();
            double radius = vanguardDown ? ORBIT_ENRAGED : ORBIT;
            double base = Math.atan2(outriderHorse.getLocation().getZ() - target.getZ(), outriderHorse.getLocation().getX() - target.getX());
            Location spot = target.clone().add(Math.cos(base + 0.35) * radius, 0, Math.sin(base + 0.35) * radius);
            Abyss.walk(outriderHorse, keepInside(spot), 0.34, 0);
            Abyss.face(outrider, outriderTarget.getEyeLocation());
        }
        if (!vanguardDown && vanguardHorse.isValid()) {
            if (now < stunnedUntil || chargeAt >= 0) {
                vanguardHorse.setVelocity(new Vector(0, vanguardHorse.getVelocity().getY(), 0));
            } else if (chargeEnd >= 0) {
                charge(now);
            } else if (alive(vanguardTarget)) {
                Abyss.walk(vanguardHorse, vanguardTarget.getLocation(), 0.3, 2);
                Abyss.face(vanguard, vanguardTarget.getEyeLocation());
            }
        }
    }

    private Location keepInside(Location spot) {
        Location center = fight.center();
        Vector offset = spot.toVector().subtract(center.toVector()).setY(0);
        double max = fight.radius() - 3;
        if (offset.length() > max) {
            offset.normalize().multiply(max);
        }
        return center.clone().add(offset);
    }

    // ------------------------------------------------------------------ every step: decisions

    @Override
    public void tick() {
        int now = fight.elapsed();
        checkDeaths();
        remount(outrider, outriderHorse, outriderDown);
        remount(vanguard, vanguardHorse, vanguardDown);

        if (!outriderDown) {
            if (!alive(outriderTarget) || every(160)) {
                outriderTarget = fight.randomPlayer();
            }
            outriderAttacks(now);
        }
        if (!vanguardDown) {
            vanguardTarget = fight.nearestPlayer(vanguard.getLocation());
            vanguardAttacks(now);
        }
    }

    private void outriderAttacks(int now) {
        if (outriderTarget == null) {
            return;
        }
        int snipeEvery = vanguardDown ? 60 : 100;
        if (every(snipeEvery)) {
            snipes.add(new Abyss.Beam(outrider, outriderTarget, now, 30, SNIPE_DAMAGE, STORM));
        }
        for (Abyss.Beam snipe : snipes) {
            for (Player hit : snipe.step(fight, now)) {
                // visual lightning only: no fire, no transformed mobs - and a plasma bolt with it (Session O5)
                hit.getWorld().strikeLightningEffect(hit.getLocation());
                io.github.amitelia.occultech.boss.AirEffects.bolt(fight, hit.getLocation(), STORM);
            }
        }
        snipes.removeIf(Abyss.Beam::done);

        if (every(vanguardDown ? 30 : 60)) {
            Vector aim = outriderTarget.getEyeLocation().toVector().subtract(outrider.getEyeLocation().toVector()).normalize();
            for (int i = -1; i <= 1; i++) {
                Arrow arrow = outrider.launchProjectile(Arrow.class, aim.clone().rotateAroundY(Math.toRadians(8 * i)).multiply(2.4));
                arrow.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, ARROW_DAMAGE.damage());
            fight.label(arrow, ARROW_DAMAGE);
            }
            outrider.getWorld().spawnParticle(Particle.ELECTRIC_SPARK, outrider.getEyeLocation(), 10, 0.3, 0.3, 0.3, 0.1);
            outrider.getWorld().playSound(outrider.getLocation(), Sound.ENTITY_SKELETON_SHOOT, 1.5F, 0.7F);
        }

        if (every(240) && rainAt < 0) {
            Player victim = fight.randomPlayer();
            if (victim != null) {
                rainSpot = victim.getLocation();
                rainAt = now + 30;
                fight.telegraph(rainSpot, 3.5, 35, STORM, FloorDecals.Mark.STORM);
                outrider.getWorld().playSound(outrider.getLocation(), Sound.ITEM_CROSSBOW_LOADING_END, 2F, 0.6F);
            }
        }
        if (rainAt >= 0 && now >= rainAt) {
            rainAt = -1;
            rainSpot.getWorld().strikeLightningEffect(rainSpot);
            io.github.amitelia.occultech.boss.AirEffects.bolt(fight, rainSpot, STORM);
            rainSpot.getWorld().spawnParticle(Particle.CRIT, rainSpot.clone().add(0, 2, 0), 80, 2, 2, 2, 0.4);
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(rainSpot) <= 3.5 * 3.5) {
                    fight.hit(player, RAIN_DAMAGE, outrider);
                }
            }
        }
    }

    private void vanguardAttacks(int now) {
        if (now < stunnedUntil || chargeEnd >= 0) {
            if (now < stunnedUntil) {
                vanguard.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, vanguard.getLocation().add(0, 2.2, 0), 2, 0.3, 0.1, 0.3, 0);
            }
            return;
        }
        if (chargeAt >= 0) {
            if (now >= chargeAt) {
                chargeAt = -1;
                chargeEnd = now + CHARGE_TICKS;
                rammed.clear();
                vanguard.getWorld().playSound(vanguard.getLocation(), Sound.ENTITY_ZOMBIE_HORSE_ANGRY, 2F, 0.6F);
            }
            return;
        }
        if (vanguardTarget != null && now >= nextMelee && vanguardTarget.getLocation().distanceSquared(vanguard.getLocation()) <= 3.5 * 3.5) {
            nextMelee = now + 20;
            vanguard.swingMainHand();
            fight.hit(vanguardTarget, MELEE_DAMAGE, vanguard);
        }
        // intercept: anyone closing in on the Outrider gets charged
        Player intercept = null;
        if (!outriderDown) {
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(outrider.getLocation()) <= 64) {
                    intercept = player;
                    break;
                }
            }
        }
        if (intercept != null && now >= nextCharge - 100) {
            startCharge(now, intercept, "&4The Vanguard intercepts!");
        } else if (now >= nextCharge) {
            Player victim = fight.randomPlayer();
            if (victim != null) {
                startCharge(now, victim, null);
            }
        }
        if (outriderDown && every(80) && vanguardTarget != null) {
            Vector aim = vanguardTarget.getEyeLocation().toVector().subtract(vanguard.getEyeLocation().toVector()).normalize();
            Trident spear = vanguard.launchProjectile(Trident.class, aim.multiply(2));
            spear.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, SPEAR_DAMAGE.damage());
            fight.label(spear, SPEAR_DAMAGE);
            vanguard.swingMainHand();
        }
    }

    private void startCharge(int now, Player victim, String message) {
        chargeDirection = victim.getLocation().toVector().subtract(vanguardHorse.getLocation().toVector()).setY(0);
        if (chargeDirection.lengthSquared() < 1) {
            chargeDirection = new Vector(1, 0, 0);
        }
        chargeDirection.normalize();
        chargeAt = now + CHARGE_WARNING;
        nextCharge = now + 180;
        Location from = vanguardHorse.getLocation().add(0, 0.2, 0);
        Particle.DustOptions dust = new Particle.DustOptions(LANCE, 1.6F);
        if (FloorDecals.enabled()) {
            FloorDecals.lane(fight, vanguardHorse.getLocation(), chargeDirection, 18, 3, CHARGE_WARNING, LANCE);
        }
        for (double d = 0; d < 18 && !FloorDecals.enabled(); d += 0.5) {
            from.getWorld().spawnParticle(Particle.DUST, from.clone().add(chargeDirection.clone().multiply(d)), 1, 0.3, 0, 0.3, 0, dust);
        }
        if (message != null) {
            fight.broadcast(message);
        }
    }

    /** One tick of the lance charge. */
    private void charge(int now) {
        Location at = vanguardHorse.getLocation();
        boolean blocked = !at.clone().add(chargeDirection.clone().multiply(1.5)).add(0, 0.5, 0).getBlock().isPassable();
        boolean outside = at.distanceSquared(fight.center()) > fight.radius() * fight.radius();
        if (now >= chargeEnd || blocked || outside) {
            chargeEnd = -1;
            vanguardHorse.setVelocity(new Vector());
            if (blocked || outside) {
                stunnedUntil = now + STUN_TICKS;
                fight.broadcast("&4The Vanguard stumbles - &fstrike now!");
            }
            return;
        }
        vanguardHorse.setVelocity(chargeDirection.clone().multiply(0.8).setY(vanguardHorse.getVelocity().getY()));
        for (Player player : fight.players()) {
            if (!rammed.contains(player.getUniqueId()) && player.getLocation().distanceSquared(at) <= 5) {
                rammed.add(player.getUniqueId());
                fight.hit(player, RAM_DAMAGE, vanguard);
                player.setVelocity(chargeDirection.clone().multiply(1.2).setY(0.5));
            }
        }
    }

    // ------------------------------------------------------------------ helpers

    private void checkDeaths() {
        if (!outriderDown && (!outrider.isValid() || outrider.isDead())) {
            outriderDown = true;
            dismissHorse(outriderHorse);
            if (!vanguardDown) {
                fight.broadcast("&4The Outrider falls - &fthe Vanguard takes up spears in its rage!");
            }
        }
        if (!vanguardDown && (!vanguard.isValid() || vanguard.isDead())) {
            vanguardDown = true;
            dismissHorse(vanguardHorse);
            if (!outriderDown) {
                fight.broadcast("&bThe Vanguard falls - &fthe Outrider rides closer and shoots faster!");
            }
        }
    }

    private static void dismissHorse(AbstractHorse horse) {
        if (horse.isValid()) {
            horse.getWorld().spawnParticle(Particle.SOUL, horse.getLocation().add(0, 1, 0), 30, 0.5, 0.6, 0.5, 0.03);
            horse.remove();
        }
    }

    /** The engine may teleport a rider (leash), which dismounts it: bring the horse along. */
    private static void remount(LivingEntity rider, AbstractHorse horse, boolean down) {
        if (down || !rider.isValid() || !horse.isValid() || horse.getPassengers().contains(rider)) {
            return;
        }
        horse.teleport(rider.getLocation());
        horse.addPassenger(rider);
    }

    private static boolean alive(Player player) {
        return player != null && player.isValid() && !player.isDead();
    }
}
