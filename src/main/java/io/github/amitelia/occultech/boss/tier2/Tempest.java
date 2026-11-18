package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Blaze;
import org.bukkit.entity.Breeze;
import org.bukkit.entity.BreezeWindCharge;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Player;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Prop;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-2 mini-boss (max netherite): the Shattered Seal, a great wind sealed in a carved ritual seal that the summoning
 * cracked. Without a model it is a great breeze that keeps its own hopping and wind-charge AI.
 * <ul>
 * <li>Gust volley: three wind charges; a direct hit hurts. Knockback stays vanilla-sized. With the model the seal snaps
 * together first and the charges leave its heart 0.7 s later.</li>
 * <li>Squall ring: a ring of wind closes in from the arena edge to 5 blocks around the altar over 8s. Standing
 * outside it hurts every second - stay inside. It only ever asks players to move inward.</li>
 * <li>Wind burst: a warning circle around it, then everyone close is thrown up (gently) and hurt.</li>
 * <li>Spent: for 1.5 s after a burst it hangs still, its seal on the floor: an opening to hit it.</li>
 * <li>Below half health two small breezes join (capped). With the model the seal breaks in two as they come.</li>
 * </ul>
 * Takes a third of the damage dealt.
 * <p>
 * With MythicMobs and BetterModel the body is the model on an invisible blaze (a breeze would still draw its wind and
 * eyes: its layers ignore invisibility), puppeted and steered here: it keeps its distance from its target, turns to face
 * it, and stands still while spent.
 */
public final class Tempest extends BossBehavior {

    private static final double HEALTH = 300;
    private static final double ARMOR = 0.33;
    private static final Color WIND = Color.fromRGB(200, 230, 255);
    private static final int VOLLEY_INTERVAL = 140;
    private static final int BURST_INTERVAL = 220;
    /** After a burst it hangs in the air, spent: an opening to hit it (Session R2). */
    private static final int SPENT_TICKS = 30;
    private static final int RING_INTERVAL = 400;
    private static final int RING_TICKS = 160;
    private static final double RING_MIN = 5;
    /** The volley clip's contact: the charges leave 14 ticks after it starts. */
    private static final int VOLLEY_LEAD = 14;
    /** The volley clip is 1.4 s long. */
    private static final int VOLLEY_CLIP = 28;
    /** The split clip's contact: the seal breaks in two (and the gales come) 20 ticks after it starts. */
    private static final int SPLIT_LEAD = 20;
    /** BetterModel's hit flash restores the tint it found, so the state tint is put back after it. */
    private static final int RETINT_AFTER = 12;
    /** The model's heart over the carrier's feet, in blocks: the charges leave it. */
    private static final double HEART = 4.5;
    /** The model's lowest point sits this far over the floor. */
    private static final double HOVER = 0.3;
    private static final double KEEP_DISTANCE = 7;
    private static final double DRIFT_SPEED = 0.14;
    private static final int DEAD = Color.fromRGB(44, 40, 40).asRGB();
    /** The tintable bones (BetterModel names, tag prefix dropped). */
    private static final String[] GLOWS = {"heart", "circlet", "eyes", "shard0", "shard1", "shard2", "shard3", "shard4", "shard5", "shard6"};
    private static final io.github.amitelia.occultech.boss.Mechanic CHARGE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TEMPEST", "Wind charge", 20, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic BURST_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TEMPEST", "Burst", 30, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic RING_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.piercing("TEMPEST", "Squall ring", 4, io.github.amitelia.occultech.boss.Mechanic.Kind.ZONE, true);

    private Mob tempest;
    private boolean modelled;
    private int ringStart = -1;
    private int burstAt = -1;
    private boolean enraged;
    private int spentUntil = -1;
    /** Model only: the volley waiting for its clip's contact, at whom, and when the clip ends. */
    private int volleyAt = -1;
    private int volleyEnds = -1;
    private Player volleyTarget;
    /** Model only: the gales waiting for the split's contact. */
    private int galesAt = -1;
    private int retintAt = -1;
    /** No flinch while an attack clip plays (it would cut it), and not more than once in 15 ticks. */
    private int busyUntil;
    private int flinchReady;

    public Tempest(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        modelled = fight.usesMythicBody();
        if (modelled) {
            tempest = fight.spawnBoss(Blaze.class, at.clone().add(0, HOVER, 0), b -> {
                b.setCustomName(ChatColor.AQUA + "Tempest");
                b.setCustomNameVisible(true);
                Abyss.puppet(b);
                BossFight.setAttribute(b, Attribute.MAX_HEALTH, HEALTH);
                BossFight.setAttribute(b, Attribute.SCALE, 1.0);   // the model is drawn at its own size
            });
        } else {
            tempest = fight.spawnBoss(Breeze.class, at.clone().add(0, 1, 0), b -> {
                b.setCustomName(ChatColor.AQUA + "Tempest");
                b.setCustomNameVisible(true);
                BossFight.setAttribute(b, Attribute.MAX_HEALTH, HEALTH);
                BossFight.setAttribute(b, Attribute.SCALE, 3);   // a bigger target
                BossFight.setAttribute(b, Attribute.MOVEMENT_SPEED, 0.42);
                BossFight.setAttribute(b, Attribute.JUMP_STRENGTH, 0.3);
                BossFight.setAttribute(b, Attribute.FOLLOW_RANGE, 40);
            });
        }
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
        if (!modelled && tempest.getTarget() == null) {
            tempest.setTarget(fight.nearestPlayer(tempest.getLocation()));
        }

        if (!enraged && fight.healthFraction() < 0.5) {
            enraged = true;
            fight.broadcast("&bThe storm splits - &fsmall gales join the Tempest!");
            if (modelled) {
                act("SPLIT");
                galesAt = now + SPLIT_LEAD;
                busyUntil = Math.max(busyUntil, now + 48);
            } else {
                gales();
            }
        }

        if (spentUntil >= 0 && now >= spentUntil) {
            spentUntil = -1;
            if (modelled) {
                act("RECOVER");
                act(stateTint());
                busyUntil = Math.max(busyUntil, now + 16);
            } else {
                tempest.setAware(true);
            }
        }
        if (spentUntil >= 0) {
            tempest.getWorld().spawnParticle(Particle.CLOUD, tempest.getLocation().add(0, 1.5, 0), 3, 0.4, 0.3, 0.4, 0.01);
            if (ringStart >= 0) {
                squall(now);   // the squall closes in all the same
            }
            return;   // spent: no attacks, no moving
        }
        if (every(VOLLEY_INTERVAL) && volleyAt < 0) {
            if (modelled) {
                volleyTarget = fight.randomPlayer();
                if (volleyTarget != null) {
                    act("VOLLEY");
                    volleyAt = now + VOLLEY_LEAD;
                    volleyEnds = now + VOLLEY_CLIP;
                    busyUntil = Math.max(busyUntil, volleyEnds);
                }
            } else {
                volley(fight.randomPlayer());
            }
        }
        if (every(BURST_INTERVAL) && burstAt < 0) {
            burstAt = now + 20;
            fight.telegraph(tempest.getLocation(), 4.5, 25, WIND, FloorDecals.Mark.WIND);
            tempest.getWorld().playSound(tempest.getLocation(), Sound.ENTITY_BREEZE_INHALE, 2F, 0.6F);
            if (modelled) {
                act("BURST");      // drawn in through the warning, flung out on its contact (1.0 s)
                busyUntil = Math.max(busyUntil, burstAt);
            }
        }
        if (burstAt >= 0 && now >= burstAt) {
            burstAt = -1;
            burst();
            spentUntil = now + SPENT_TICKS;
            tempest.setVelocity(new Vector());
            if (modelled) {
                act("SPENT");
                busyUntil = Math.max(busyUntil, spentUntil);
            } else {
                tempest.setAware(false);
            }
        }

        if (every(RING_INTERVAL) && ringStart < 0) {
            ringStart = now;
            fight.broadcast("&bA squall closes in - &fget near the altar!");
            FloorDecals.wave(fight, fight.center(), fight.radius(), RING_MIN, RING_TICKS, org.bukkit.Color.fromRGB(200, 230, 240), RING_TICKS / 4);
            if (modelled) {
                act("SQUALL");
            }
        }
        if (ringStart >= 0) {
            squall(now);
        }
    }

    /** Every tick, model only: the charges leave on the volley's contact, the gales on the split's, the tint comes back
     * after a hit flash, and the carrier is steered: it keeps its distance from its target and faces it. */
    @Override
    public void move() {
        if (!modelled || !tempest.isValid() || tempest.isDead()) {
            return;
        }
        int now = fight.elapsed();
        if (volleyAt >= 0 && now >= volleyAt) {
            volleyAt = -1;
            if (volleyTarget != null && volleyTarget.isValid() && fight.players().contains(volleyTarget)) {
                volley(volleyTarget);
            }
        }
        if (volleyEnds >= 0 && now >= volleyEnds) {
            volleyEnds = -1;
            act(stateTint());
        }
        if (galesAt >= 0 && now >= galesAt) {
            galesAt = -1;
            gales();
        }
        if (retintAt >= 0 && now >= retintAt) {
            retintAt = -1;
            act(burstAt >= 0 || volleyAt >= 0 ? "STATE_TELL" : stateTint());
        }
        Player target = volleyTarget != null && volleyAt >= 0 ? volleyTarget : fight.nearestPlayer(tempest.getLocation());
        Location at = tempest.getLocation();
        if (target != null) {
            Vector look = target.getLocation().toVector().subtract(at.toVector()).setY(0);
            if (look.lengthSquared() > 0.01) {
                float yaw = (float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ()));
                tempest.setRotation(yaw, 0);
                tempest.setBodyYaw(yaw);
            }
        }
        if (spentUntil >= 0 || burstAt >= 0 || target == null) {
            tempest.setVelocity(new Vector(0, (fight.center().getY() + HOVER - at.getY()) * 0.2, 0));
            return;   // spent or winding up a burst: it holds still
        }
        // keep its distance from the target, inside the arena, a slow drift round it
        Vector away = at.toVector().subtract(target.getLocation().toVector()).setY(0);
        if (away.lengthSquared() < 0.01) {
            away = new Vector(1, 0, 0);
        }
        Location spot = target.getLocation().add(away.normalize().rotateAroundY(0.15).multiply(KEEP_DISTANCE));
        Vector fromCentre = spot.toVector().subtract(fight.center().toVector()).setY(0);
        double limit = Math.max(3, fight.radius() - 3);
        if (fromCentre.length() > limit) {
            spot = fight.center().clone().add(fromCentre.normalize().multiply(limit));
        }
        spot.setY(fight.center().getY() + HOVER);
        Vector step = spot.toVector().subtract(at.toVector());
        if (step.length() > DRIFT_SPEED) {
            step.normalize().multiply(DRIFT_SPEED);
        }
        tempest.setVelocity(step);
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (!modelled || boss != tempest) {
            return;
        }
        int now = fight.elapsed();
        retintAt = now + RETINT_AFTER;
        if (now >= busyUntil && spentUntil < 0 && now >= flinchReady) {
            flinchReady = now + 15;
            act("FLINCH");
        }
    }

    /** The model stays for its whole death clip, its heart, glyphs and eyes out. */
    @Override
    public void onBossDeath(LivingEntity boss) {
        if (!modelled || boss != tempest) {
            return;
        }
        Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(DEAD, GLOWS);
        }
    }

    private String stateTint() {
        return spentUntil >= 0 ? "STATE_SPENT" : enraged ? "STATE_STORM" : "STATE_CALM";
    }

    private void act(String action) {
        fight.playAction(tempest, action);
    }

    private void gales() {
        for (int i = 0; i < 2; i++) {
            fight.spawnAdd(Breeze.class, fight.randomPoint(3, 7).add(0, 1, 0), b -> {
                BossFight.setAttribute(b, Attribute.MAX_HEALTH, 40);
                b.setHealth(40);
            });
        }
    }

    private void volley(Player target) {
        if (target == null) {
            return;
        }
        // with the model the charges leave its heart, in front of the seal; the plain breeze shoots from its eyes
        Location from = modelled
            ? tempest.getLocation().add(0, HEART, 0).add(target.getEyeLocation().toVector().subtract(tempest.getLocation().toVector())
                .setY(0).normalize().multiply(1.6))
            : tempest.getEyeLocation();
        Vector aim = target.getEyeLocation().toVector().subtract(from.toVector()).normalize();
        for (int i = -1; i <= 1; i++) {
            Vector velocity = aim.clone().rotateAroundY(Math.toRadians(15 * i)).multiply(0.8);
            BreezeWindCharge charge = tempest.launchProjectile(BreezeWindCharge.class, velocity);
            if (modelled) {
                charge.teleport(from);
                charge.setVelocity(velocity);
            }
            charge.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, CHARGE_DAMAGE.damage());
            fight.label(charge, CHARGE_DAMAGE);
        }
        tempest.getWorld().playSound(from, Sound.ENTITY_BREEZE_SHOOT, 1.5F, 0.8F);
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
            if (modelled) {
                act("SQUALL_END");
            }
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
