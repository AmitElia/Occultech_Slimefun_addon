package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Breeze;
import org.bukkit.entity.BreezeWindCharge;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-2 mini-boss (max netherite). A great breeze that keeps its own hopping and wind-charge AI.
 * <ul>
 * <li>Gust volley: three wind charges; a direct hit hurts. Knockback stays vanilla-sized.</li>
 * <li>Squall ring: a ring of wind closes in from the arena edge to 5 blocks around the altar over 8s. Standing
 * outside it hurts every second - stay inside. It only ever asks players to move inward.</li>
 * <li>Wind burst: a warning circle around it, then everyone close is thrown up (gently) and hurt.</li>
 * <li>Below half health two small breezes join (capped).</li>
 * </ul>
 * Takes a third of the damage dealt.
 */
public final class Tempest extends BossBehavior {

    private static final double HEALTH = 300;
    private static final double ARMOR = 0.33;
    private static final Color WIND = Color.fromRGB(200, 230, 255);
    private static final int VOLLEY_INTERVAL = 100;
    private static final int BURST_INTERVAL = 160;
    private static final int RING_INTERVAL = 400;
    private static final int RING_TICKS = 160;
    private static final double RING_MIN = 5;
    private static final io.github.amitelia.occultech.boss.Mechanic CHARGE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TEMPEST", "Wind charge", 20, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic BURST_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TEMPEST", "Burst", 30, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic RING_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.piercing("TEMPEST", "Squall ring", 6, io.github.amitelia.occultech.boss.Mechanic.Kind.ZONE, true);

    private Breeze tempest;
    private int ringStart = -1;
    private int burstAt = -1;
    private boolean enraged;

    public Tempest(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        tempest = fight.spawnBoss(Breeze.class, at.clone().add(0, 1, 0), b -> {
            b.setCustomName(ChatColor.AQUA + "Tempest");
            b.setCustomNameVisible(true);
            BossFight.setAttribute(b, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(b, Attribute.SCALE, 2.5);
            BossFight.setAttribute(b, Attribute.FOLLOW_RANGE, 40);
        });
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR;
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double verticalLeash() {
        return 12;
    }

    @Override
    public void tick() {
        if (!tempest.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (tempest.getTarget() == null) {
            tempest.setTarget(fight.nearestPlayer(tempest.getLocation()));
        }

        if (!enraged && fight.healthFraction() < 0.5) {
            enraged = true;
            fight.broadcast("&bThe storm splits - &fsmall gales join the Tempest!");
            for (int i = 0; i < 2; i++) {
                fight.spawnAdd(Breeze.class, fight.randomPoint(3, 7).add(0, 1, 0), b -> {
                    BossFight.setAttribute(b, Attribute.MAX_HEALTH, 40);
                    b.setHealth(40);
                });
            }
        }

        if (every(VOLLEY_INTERVAL)) {
            volley();
        }
        if (every(BURST_INTERVAL) && burstAt < 0) {
            burstAt = now + 20;
            fight.telegraph(tempest.getLocation(), 4.5, 25, WIND, FloorDecals.Mark.WIND);
            tempest.getWorld().playSound(tempest.getLocation(), Sound.ENTITY_BREEZE_INHALE, 2F, 0.6F);
        }
        if (burstAt >= 0 && now >= burstAt) {
            burstAt = -1;
            burst();
        }

        if (every(RING_INTERVAL) && ringStart < 0) {
            ringStart = now;
            fight.broadcast("&bA squall closes in - &fget near the altar!");
            FloorDecals.wave(fight, fight.center(), fight.radius(), RING_MIN, RING_TICKS, org.bukkit.Color.fromRGB(200, 230, 240), RING_TICKS / 4);
        }
        if (ringStart >= 0) {
            squall(now);
        }
    }

    private void volley() {
        Player target = fight.randomPlayer();
        if (target == null) {
            return;
        }
        Vector aim = target.getEyeLocation().toVector().subtract(tempest.getEyeLocation().toVector()).normalize();
        for (int i = -1; i <= 1; i++) {
            BreezeWindCharge charge = tempest.launchProjectile(BreezeWindCharge.class, aim.clone().rotateAroundY(Math.toRadians(15 * i)).multiply(0.8));
            charge.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, CHARGE_DAMAGE.damage());
            fight.label(charge, CHARGE_DAMAGE);
        }
        tempest.getWorld().playSound(tempest.getLocation(), Sound.ENTITY_BREEZE_SHOOT, 1.5F, 0.8F);
    }

    private void burst() {
        Location at = tempest.getLocation();
        at.getWorld().spawnParticle(Particle.GUST_EMITTER_SMALL, at.clone().add(0, 1, 0), 1);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, at.clone().add(0, 1, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, WIND, 5F);
        at.getWorld().playSound(at, Sound.ENTITY_BREEZE_WIND_BURST, 2F, 0.7F);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 4.5 * 4.5) {
                fight.hit(player, BURST_DAMAGE, tempest);
                player.setVelocity(player.getVelocity().setY(0.9));
            }
        }
    }

    /** The ring shrinks from the arena edge to {@value #RING_MIN} blocks, hurting players outside it every second. */
    private void squall(int now) {
        double progress = (now - ringStart) / (double) RING_TICKS;
        if (progress > 1.25) {
            ringStart = -1;
            return;
        }
        double radius = Math.max(RING_MIN, fight.radius() - (fight.radius() - RING_MIN) * Math.min(1, progress));
        Location center = fight.center();
        int points = (int) (radius * 5);
        double offset = now * 0.05;
        for (int i = 0; i < points; i++) {
            double angle = offset + Math.PI * 2 * i / points;
            center.getWorld().spawnParticle(Particle.CLOUD, center.clone().add(Math.cos(angle) * radius, 0.5 + (i % 3) * 0.5, Math.sin(angle) * radius),
                1, 0, 0, 0, 0);
        }
        if (now % 20 == 0) {
            for (Player player : fight.players()) {
                Vector flat = player.getLocation().toVector().subtract(center.toVector()).setY(0);
                if (flat.length() > radius + 0.5) {
                    // the squall cuts through armor: standing outside must hurt even in netherite
                    fight.hit(player, RING_DAMAGE, tempest);
                }
            }
        }
    }
}
