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

    private final List<BossFight.FightObject> wards = new ArrayList<>();
    /** The ring round Volley while a ward stands, and each ward's stream of light to it (Session O5). */
    @javax.annotation.Nullable private io.github.amitelia.occultech.boss.AirEffects.Aura wardRing;
    private final java.util.Map<BossFight.FightObject, io.github.amitelia.occultech.boss.AirEffects.Streak> links = new java.util.HashMap<>();
    private Skeleton archer;
    private int volleyAt = -1;
    private int arrowsLeft;
    private int arrowIndex;

    public Volley(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        archer = fight.spawnBoss(Skeleton.class, at, s -> {
            s.setCustomName(ChatColor.GOLD + "Volley");
            s.setCustomNameVisible(true);
            s.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
            s.getEquipment().setHelmet(new ItemStack(Material.CHAINMAIL_HELMET));
            BossFight.setAttribute(s, Attribute.MAX_HEALTH, 160);
            BossFight.setAttribute(s, Attribute.SCALE, 1.4);
            BossFight.setAttribute(s, Attribute.MOVEMENT_SPEED, 0.27);
            BossFight.setAttribute(s, Attribute.KNOCKBACK_RESISTANCE, 0.5);
            BossFight.setAttribute(s, Attribute.FOLLOW_RANGE, 32);
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
                Location from = ward.location().clone().add(0, 0.5, 0);
                Location to = archer.getLocation().add(0, 1.2, 0);
                io.github.amitelia.occultech.boss.AirEffects.Streak link = links.get(ward);
                if (link == null) {
                    links.put(ward, io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "air_beam", from, to, org.bukkit.Color.fromRGB(190, 140, 255), 0.16F));
                } else {
                    link.aim(from, to, 0.16F, io.github.amitelia.occultech.boss.BossService.STEP);
                }
            }
        }

        if (every(WARD_INTERVAL) && wards.isEmpty()) {
            for (int i = 0; i < 2; i++) {
                wards.add(fight.spawnObject(fight.randomPoint(4, Math.min(9, fight.radius() - 2)), Material.AMETHYST_CLUSTER, 1.4F, 4, () -> {
                    if (!hasWards()) {
                        fight.broadcast("&dVolley's wards shatter - it is exposed!");
                    }
                }));
            }
            fight.broadcast("&7Volley raises ward crystals. &fBreak them to pierce its guard!");
        }
        if (hasWards() && archer.isValid() && !io.github.amitelia.occultech.boss.AirEffects.enabled()) {
            for (BossFight.FightObject ward : wards) {
                beam(ward.location().clone().add(0, 0.5, 0), archer.getLocation().add(0, 1.2, 0));
            }
        }

        if (every(VOLLEY_INTERVAL) && archer.isValid()) {
            volleyAt = now + VOLLEY_WARNING;
            archer.setGlowing(true);
            archer.getWorld().playSound(archer.getLocation(), Sound.ITEM_CROSSBOW_LOADING_MIDDLE, 1.5F, 0.8F);
        }
        if (now == volleyAt) {
            archer.setGlowing(false);
            arrowsLeft = 5;
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

    private boolean hasWards() {
        for (BossFight.FightObject ward : wards) {
            if (ward.isAlive()) {
                return true;
            }
        }
        return false;
    }

    private void shoot(Player target) {
        Location from = archer.getEyeLocation();
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
