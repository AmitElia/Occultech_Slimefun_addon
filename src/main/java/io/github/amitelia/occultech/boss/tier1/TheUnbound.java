package io.github.amitelia.occultech.boss.tier1;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Husk;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Vindicator;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 mini-boss (diamond gear, solo 2-4 min). A berserk vindicator ("Johnny") that attacks anything near it.
 * <ul>
 * <li>Speeds up as it loses health.</li>
 * <li>Cleave: a red wedge marks the area in front of it for 1.2s, then an axe sweep hits everything inside.</li>
 * <li>Thralls: every 20s two husk thralls rise. The Unbound attacks thralls near it; when it devours one it is
 * <b>sated</b> for 3s - stunned and taking 50% more damage. Bait it into its thralls.</li>
 * </ul>
 */
public final class TheUnbound extends BossBehavior {

    private static final Particle.DustOptions WEDGE = new Particle.DustOptions(Color.fromRGB(220, 30, 30), 1.3F);
    private static final int CLEAVE_INTERVAL = 120;
    private static final int CLEAVE_WARNING = 25;
    private static final int THRALL_INTERVAL = 400;
    private static final int SATED_TICKS = 60;
    private static final double BASE_SPEED = 0.33;
    private static final double CLEAVE_RANGE = 4.5;

    private final List<Husk> thralls = new ArrayList<>();
    private Vindicator unbound;
    private Vector cleaveDirection;
    private int cleaveAt = -1;
    private int satedUntil = -1;

    public TheUnbound(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        unbound = fight.spawnBoss(Vindicator.class, at, v -> {
            v.setJohnny(true);
            v.setCustomName(ChatColor.RED + "The Unbound");
            v.setCustomNameVisible(true);
            v.getEquipment().setItemInMainHand(new ItemStack(Material.IRON_AXE));
            BossFight.setAttribute(v, Attribute.MAX_HEALTH, 320);
            BossFight.setAttribute(v, Attribute.ATTACK_DAMAGE, 11);
            BossFight.setAttribute(v, Attribute.SCALE, 1.3);
            BossFight.setAttribute(v, Attribute.MOVEMENT_SPEED, BASE_SPEED);
            BossFight.setAttribute(v, Attribute.KNOCKBACK_RESISTANCE, 0.5);
            BossFight.setAttribute(v, Attribute.FOLLOW_RANGE, 32);
        });
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return isSated() ? damage * 1.5 : damage;
    }

    @Override
    public void tick() {
        if (!unbound.isValid()) {
            return;
        }
        int now = fight.elapsed();
        thralls.removeIf(t -> t.isDead() || !t.isValid());

        // stunned while sated
        boolean sated = isSated();
        unbound.setAI(!sated);
        if (sated) {
            unbound.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, unbound.getLocation().add(0, 2.4, 0), 2, 0.3, 0.2, 0.3, 0);
            return;
        }

        // enrage: up to 30% faster at low health
        BossFight.setAttribute(unbound, Attribute.MOVEMENT_SPEED, BASE_SPEED * (1 + 0.3 * (1 - fight.healthFraction())));

        if (every(THRALL_INTERVAL)) {
            for (int i = 0; i < 2; i++) {
                Husk thrall = fight.spawnAdd(Husk.class, fight.randomPoint(5, fight.radius() - 2), h -> {
                    h.setCustomName(ChatColor.GRAY + "Unbound Thrall");
                    BossFight.setAttribute(h, Attribute.MAX_HEALTH, 30);
                    h.setHealth(30);
                });
                if (thrall != null) {
                    thralls.add(thrall);
                }
            }
            fight.broadcast("&7Thralls rise. &fLure the Unbound into them!");
        }

        // it can't resist a thrall within reach
        for (Husk thrall : thralls) {
            if (thrall.getLocation().distanceSquared(unbound.getLocation()) < 9) {
                unbound.setTarget(thrall);
                break;
            }
        }

        if (every(CLEAVE_INTERVAL)) {
            Player target = fight.nearestPlayer(unbound.getLocation());
            if (target != null) {
                cleaveDirection = target.getLocation().toVector().subtract(unbound.getLocation().toVector()).setY(0);
                if (cleaveDirection.lengthSquared() < 0.01) {
                    cleaveDirection = unbound.getLocation().getDirection().setY(0);
                }
                cleaveDirection.normalize();
                cleaveAt = now + CLEAVE_WARNING;
                unbound.getWorld().playSound(unbound.getLocation(), Sound.ENTITY_VINDICATOR_CELEBRATE, 1.5F, 0.6F);
                FloorDecals.wedge(fight, unbound.getLocation(), cleaveDirection, CLEAVE_RANGE, CLEAVE_WARNING, WEDGE.getColor());
            }
        }
        if (cleaveAt > now && cleaveDirection != null && !FloorDecals.enabled()) {
            drawWedge();
        }
        if (now == cleaveAt && cleaveDirection != null) {
            cleave();
        }
    }

    @Override
    public void onAddDeath(Entity entity, @Nullable Player killer) {
        if (killer == null && thralls.contains(entity)) {
            satedUntil = fight.elapsed() + SATED_TICKS;
            unbound.getWorld().playSound(unbound.getLocation(), Sound.ENTITY_PLAYER_BURP, 2F, 0.5F);
            fight.broadcast("&7The Unbound gorges on its thrall - &fstrike now!");
        }
    }

    private boolean isSated() {
        return fight.elapsed() < satedUntil;
    }

    private void drawWedge() {
        Location origin = unbound.getLocation().add(0, 0.2, 0);
        for (double distance = 1; distance <= CLEAVE_RANGE; distance += 0.7) {
            for (double angle = -45; angle <= 45; angle += 15) {
                Vector v = cleaveDirection.clone().rotateAroundY(Math.toRadians(angle)).multiply(distance);
                origin.getWorld().spawnParticle(Particle.DUST, origin.clone().add(v), 1, 0, 0, 0, 0, WEDGE);
            }
        }
    }

    private void cleave() {
        Location origin = unbound.getLocation();
        origin.getWorld().playSound(origin, Sound.ENTITY_PLAYER_ATTACK_SWEEP, 2F, 0.6F);
        origin.getWorld().spawnParticle(Particle.SWEEP_ATTACK, origin.clone().add(cleaveDirection.clone().multiply(2)).add(0, 1, 0), 6, 1, 0.3, 1, 0);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, origin.clone().add(cleaveDirection.clone().multiply(2.2)).add(0, 1.2, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.SLASH,
            WEDGE.getColor(), 4.5F);
        List<LivingEntity> victims = new ArrayList<>(fight.players());
        victims.addAll(thralls);
        for (LivingEntity victim : victims) {
            Vector to = victim.getLocation().toVector().subtract(origin.toVector()).setY(0);
            if (to.length() <= CLEAVE_RANGE && to.lengthSquared() > 0.01 && Math.toDegrees(to.angle(cleaveDirection)) <= 45) {
                victim.damage(victim instanceof Player ? 9 : 40, unbound);
                victim.setVelocity(to.normalize().multiply(0.8).setY(0.35));
            }
        }
    }
}
