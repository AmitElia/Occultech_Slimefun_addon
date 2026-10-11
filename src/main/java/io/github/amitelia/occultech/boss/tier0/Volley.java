package io.github.amitelia.occultech.boss.tier0;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Skeleton;
import org.bukkit.entity.SpectralArrow;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-0 mini-boss (iron gear). A rapid-fire skeleton archer.
 * <ul>
 * <li>Volley: glows and draws audibly for 1s, then fires 5 arrows 3 ticks apart, cycling slowness, poison and spectral.</li>
 * <li>Wards: every 15s raises 2 amethyst ward crystals (4 hits each); while any stands, Volley takes 70% less damage.</li>
 * </ul>
 * Ranged, so the engine's anti-pillar teleport is off.
 */
public final class Volley extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic ARROW = io.github.amitelia.occultech.boss.Mechanic.of("VOLLEY", "Arrow", 6, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);

    private static final int VOLLEY_INTERVAL = 120;
    private static final int VOLLEY_WARNING = 20;
    private static final int WARD_INTERVAL = 300;
    private static final double WARDED_MULTIPLIER = 0.3;
    private static final Particle.DustOptions WARD_BEAM = new Particle.DustOptions(Color.fromRGB(170, 110, 255), 1F);

    // ---- the Amethyst Crone model (Mythic body): tools/art/bosses/volley_ship.py measures these from the model ----
    /** Where the bolt leaves the arbalest in the aim pose, in blocks: x to Volley's left, y up, z ahead. */
    private static final Vector MUZZLE = new Vector(-1.21, 2.893, 5.213);
    /** The ward model's core tip above the ward's anchor, and the geode on Volley's hump above his feet. */
    private static final double WARD_TIP = 1.24;
    private static final double GEODE = 3.0;
    /** Between bursts the model fires single snap shots: one every SHOT_INTERVAL ticks, SHOT_RELEASE after its clip starts. */
    private static final int SHOT_INTERVAL = 40;
    private static final int SHOT_RELEASE = 10;
    private static final double CRACK_AT = 0.4;

    private final List<BossFight.FightObject> wards = new ArrayList<>();
    /** The ring round Volley while a ward stands, and each ward's stream of light to it (Session O5). */
    @javax.annotation.Nullable private io.github.amitelia.occultech.boss.AirEffects.Aura wardRing;
    private final java.util.Map<BossFight.FightObject, io.github.amitelia.occultech.boss.AirEffects.Streak> links = new java.util.HashMap<>();
    private Skeleton archer;
    private int volleyAt = -1;
    private int arrowsLeft;
    private int arrowIndex;
    private int nextShotAt;
    private int shotAt = -1;
    /** Below 40% health the big glowing shards on the hump have snapped (the model's cracked variant). */
    private boolean cracked;

    public Volley(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        archer = fight.spawnBoss(Skeleton.class, at, s -> {
            if (!fight.usesMythicBody()) {
                s.setCustomName(ChatColor.GOLD + "Volley");
                s.setCustomNameVisible(true);
                s.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
                s.getEquipment().setHelmet(new ItemStack(Material.CHAINMAIL_HELMET));
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 160);
                BossFight.setAttribute(s, Attribute.MOVEMENT_SPEED, 0.27);
                BossFight.setAttribute(s, Attribute.KNOCKBACK_RESISTANCE, 0.5);
                BossFight.setAttribute(s, Attribute.FOLLOW_RANGE, 32);
                BossFight.setAttribute(s, Attribute.SCALE, 1.4);
            }
        });
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return hasWards() ? damage * WARDED_MULTIPLIER : damage;
    }

    @Override
    public void tick() {
        int now = fight.elapsed();
        wards.removeIf(ward -> !ward.isAlive());
        if (hasWards() && wardRing == null && archer.isValid()) {
            wardRing = io.github.amitelia.occultech.boss.AirEffects.Aura.create(fight, archer, "aura_ward", 0.02, 2.6);
        } else if (!hasWards() && wardRing != null) {
            wardRing.end();
            wardRing = null;
        }
        if (io.github.amitelia.occultech.boss.AirEffects.enabled()) {
            links.entrySet().removeIf(entry -> {
                boolean keep = entry.getKey().isAlive() && archer.isValid() && entry.getValue().valid();
                if (!keep) {
                    entry.getValue().snap();
                }
                return !keep;
            });
            for (BossFight.FightObject ward : wards) {
                Location from = wardTop(ward);
                Location to = archer.getLocation().add(0, fight.usesMythicBody() ? GEODE : 1.2, 0);
                io.github.amitelia.occultech.boss.AirEffects.Streak link = links.get(ward);
                if (link == null) {
                    links.put(ward, io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "air_beam", from, to, org.bukkit.Color.fromRGB(190, 140, 255), 0.16F));
                } else {
                    link.aim(from, to, 0.16F, io.github.amitelia.occultech.boss.BossService.STEP);
                }
            }
        }

        if (every(WARD_INTERVAL) && wards.isEmpty()) {
            fight.playAction(archer, "WARDS_PREPARE");
            for (int i = 0; i < 2; i++) {
                wards.add(fight.spawnObject(fight.randomPoint(4, Math.min(9, fight.radius() - 2)), "occultech_volley_ward",
                    Material.AMETHYST_CLUSTER, 1.4F, 1.4F, 2.0F, 4, () -> {
                    if (!hasWards()) {
                        fight.broadcast("&dVolley's wards shatter - it is exposed!");
                        if (archer.isValid()) {
                            fight.playAction(archer, "WARDS_BROKEN");
                        }
                    }
                }));
            }
            fight.broadcast("&7Volley raises ward crystals. &fBreak them to pierce its guard!");
        }
        if (hasWards() && archer.isValid() && !io.github.amitelia.occultech.boss.AirEffects.enabled()) {
            for (BossFight.FightObject ward : wards) {
                beam(wardTop(ward), archer.getLocation().add(0, fight.usesMythicBody() ? GEODE : 1.2, 0));
            }
        }

        if (!cracked && archer.isValid() && archer.getHealth() < archer.getAttribute(Attribute.MAX_HEALTH).getValue() * CRACK_AT) {
            cracked = true;      // after a restart the resumed fight sees the low health again and re-applies the look
            fight.playAction(archer, "CRACKED");
        }
        if (fight.usesMythicBody() && archer.isValid()) {
            snapShots(now);
        }

        if (every(VOLLEY_INTERVAL) && archer.isValid()) {
            volleyAt = now + VOLLEY_WARNING;
            archer.setGlowing(true);
            fight.playAction(archer, "BURST_PREPARE", fight.nearestPlayer(archer.getLocation()));
            if (!fight.usesMythicBody()) {
                archer.getWorld().playSound(archer.getLocation(), Sound.ITEM_CROSSBOW_LOADING_MIDDLE, 1.5F, 0.8F);
            }
        }
        if (now == volleyAt) {
            archer.setGlowing(false);
            arrowsLeft = 5;
            fight.playAction(archer, "BURST_CONTACT");
        }
        if (arrowsLeft > 0 && archer.isValid()) {
            // STEP is 5 ticks; fire one arrow per step for a tight burst
            Player target = fight.nearestPlayer(archer.getLocation());
            if (target != null) {
                shoot(target);
            }
            arrowsLeft--;
        }
    }

    /**
     * The model's single shots between bursts (the vanilla bow AI is off for the Mythic body): the "SHOT" clip loads,
     * raises and fires the arbalest, and the arrow leaves when its string is released. Never inside a burst.
     */
    private void snapShots(int now) {
        boolean bursting = (volleyAt >= 0 && now >= volleyAt - VOLLEY_WARNING - io.github.amitelia.occultech.boss.BossService.STEP
            && now <= volleyAt + 6 * io.github.amitelia.occultech.boss.BossService.STEP) || arrowsLeft > 0 || every(VOLLEY_INTERVAL);
        if (now == shotAt) {
            shotAt = -1;
            Player target = fight.nearestPlayer(archer.getLocation());
            if (target != null && !bursting) {
                shoot(target);
            }
        }
        if (!bursting && shotAt < 0 && now >= nextShotAt && fight.nearestPlayer(archer.getLocation()) != null) {
            fight.playAction(archer, "SHOT", fight.nearestPlayer(archer.getLocation()));
            shotAt = now + SHOT_RELEASE;
            nextShotAt = now + SHOT_INTERVAL;
        }
    }

    private Location wardTop(BossFight.FightObject ward) {
        return ward.location().clone().add(0, ward.hasProp() ? WARD_TIP : 0.5, 0);
    }

    /**
     * Where an arrow leaves: the arbalest's muzzle for the model (turned with Volley), the eye for the vanilla body.
     * A close target pulls the point back along the barrel, so an arrow never starts beside or behind a player.
     */
    private Location launchPoint(Player target) {
        Location eye = archer.getEyeLocation();
        if (!fight.usesMythicBody()) {
            return eye;
        }
        Location feet = archer.getLocation();
        Location muzzle = feet.clone().add(MUZZLE.clone().rotateAroundY(-Math.toRadians(feet.getYaw())));
        Vector barrel = muzzle.toVector().subtract(eye.toVector());
        double reach = barrel.length();
        double room = eye.distance(target.getEyeLocation()) - 1.5;
        Location from = eye.clone().add(barrel.multiply(Math.max(0, Math.min(1, room / reach))));
        return from.getBlock().getType().isSolid() ? eye : from;
    }

    private boolean hasWards() {
        for (BossFight.FightObject ward : wards) {
            if (ward.isAlive()) {
                return true;
            }
        }
        return false;
    }

    private void shoot(Player target) {
        if (fight.usesMythicBody()) {
            // the model aims where the carrier looks: turn to the target before the shot leaves the muzzle
            Vector look = target.getLocation().toVector().subtract(archer.getLocation().toVector());
            archer.setRotation((float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ())), 0F);
        }
        Location from = launchPoint(target);
        Vector direction = target.getEyeLocation().toVector().subtract(from.toVector()).normalize();
        direction.add(new Vector((Math.random() - 0.5) * 0.06, 0.04, (Math.random() - 0.5) * 0.06)).multiply(2.1);

        AbstractArrow arrow;
        switch (arrowIndex++ % 3) {
            case 0 -> {
                Arrow a = archer.launchProjectile(Arrow.class, direction);
                a.addCustomEffect(new PotionEffect(PotionEffectType.SLOWNESS, 60, 0), true);
                arrow = a;
            }
            case 1 -> {
                Arrow a = archer.launchProjectile(Arrow.class, direction);
                a.addCustomEffect(new PotionEffect(PotionEffectType.POISON, 60, 0), true);
                arrow = a;
            }
            default -> arrow = archer.launchProjectile(SpectralArrow.class, direction);
        }
        if (fight.usesMythicBody()) {
            arrow.teleport(from);
            arrow.setVelocity(direction);
        }
        // arrow damage scales with speed: 1.2 x 2.1 ~ 3 per arrow, a full volley ~ 45% of an iron-geared player's health
        arrow.setDamage(1.2);
        fight.label(arrow, ARROW);
        arrow.setPickupStatus(AbstractArrow.PickupStatus.DISALLOWED);
        archer.getWorld().playSound(from, Sound.ENTITY_SKELETON_SHOOT, 1F, 1.3F);
    }

    private static void beam(Location from, Location to) {
        Vector step = to.toVector().subtract(from.toVector());
        double length = step.length();
        step.normalize().multiply(0.6);
        Location point = from.clone();
        for (double d = 0; d < length; d += 0.6) {
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0, 0, 0, 0, WARD_BEAM);
            point.add(step);
        }
    }
}
