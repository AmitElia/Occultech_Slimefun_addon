package io.github.amitelia.occultech.boss.tier0;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.CaveSpider;
import org.bukkit.entity.Player;
import org.bukkit.entity.Spider;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-0 mini-boss (iron gear). A giant spider.
 * <ul>
 * <li>Egg sacs: lays 2 sacs every 12s; each hatches 3 cave spiders after 6s unless smashed (3 hits).</li>
 * <li>Web zone: marks a player's spot (1.5s warning), then a white zone slows anyone inside for 8s.</li>
 * <li>Pounce: crouches and hisses for 1s, then leaps at a distant player.</li>
 * </ul>
 */
public final class BroodMother extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic BITE = io.github.amitelia.occultech.boss.Mechanic.of("BROOD_MOTHER", "Bite", 8, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic SPIDERLING = io.github.amitelia.occultech.boss.Mechanic.of("BROOD_MOTHER", "Spiderling bite", 4, io.github.amitelia.occultech.boss.Mechanic.Kind.ADD, false);

    private static final Color WEB = Color.fromRGB(235, 235, 235);
    private static final int SAC_INTERVAL = 240;
    private static final int HATCH_DELAY = 120;
    private static final int WEB_INTERVAL = 200;
    private static final int WEB_WARNING = 30;
    private static final int POUNCE_INTERVAL = 160;
    private static final int POUNCE_WARNING = 20;
    /** Her candles go out as she weakens (the model's flame groups; Mythic hides them): knees and flank, then thorax and head, then the pile. */
    private static final double[] SNUFF_AT = {0.75, 0.5, 0.25};

    private record Sac(BossFight.FightObject object, int hatchAt) {}

    private final List<Sac> sacs = new ArrayList<>();
    private Spider mother;
    private Location webTarget;
    private int webAt = -1;
    private Player pounceTarget;
    private int pounceAt = -1;
    private int snuffed;

    public BroodMother(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        mother = fight.spawnBoss(Spider.class, at, s -> {
            fight.label(s, BITE);
            if (!fight.usesMythicBody()) {   // the Mythic body sets these in its mob file and stays unscaled under the model
                s.setCustomName(ChatColor.DARK_RED + "Brood Mother");
                s.setCustomNameVisible(true);
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 320);
                BossFight.setAttribute(s, Attribute.SCALE, 2.2);
                BossFight.setAttribute(s, Attribute.MOVEMENT_SPEED, 0.37);
                BossFight.setAttribute(s, Attribute.KNOCKBACK_RESISTANCE, 0.6);
                BossFight.setAttribute(s, Attribute.FOLLOW_RANGE, 32);
            }
        });
    }

    @Override
    public void move() {
        if (pounceTarget == null || mother == null || !mother.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (now < pounceAt && pounceTarget.isValid()) {
            // the tell: she crouches where she stands, turned to her mark (walking on in the crouch read as a glide)
            mother.getPathfinder().stopPathfinding();
            mother.setVelocity(mother.getVelocity().setX(0).setZ(0));
            face(pounceTarget.getLocation().toVector().subtract(mother.getLocation().toVector()));
        } else if (now >= pounceAt && now <= pounceAt + 15) {
            Vector flight = mother.getVelocity().setY(0);
            if (flight.lengthSquared() > 1e-3) {
                face(flight);                // in the air she faces the way she flies
            }
        }
    }

    private void face(Vector direction) {
        if (direction.setY(0).lengthSquared() < 1e-6) {
            return;
        }
        float yaw = (float) Math.toDegrees(Math.atan2(-direction.getX(), direction.getZ()));
        mother.setRotation(yaw, 0F);
        mother.setBodyYaw(yaw);
    }

    @Override
    public void tick() {
        int now = fight.elapsed();

        if (every(SAC_INTERVAL)) {
            layEggs(now);
        }
        // after a restart the resumed fight sees the low health again and puts the candles out again
        if (mother.isValid()) {
            double left = mother.getHealth() / mother.getAttribute(Attribute.MAX_HEALTH).getValue();
            while (snuffed < SNUFF_AT.length && left < SNUFF_AT[snuffed]) {
                fight.playAction(mother, "SNUFF_" + Math.round(SNUFF_AT[snuffed] * 100));
                snuffed++;
            }
        }
        sacs.removeIf(sac -> {
            if (!sac.object().isAlive()) {
                return true;
            }
            if (now >= sac.hatchAt()) {
                hatch(sac.object().location());
                sac.object().remove();
                return true;
            }
            sac.object().location().getWorld().spawnParticle(Particle.ITEM_SLIME, sac.object().location(), 1, 0.2, 0.2, 0.2, 0);
            return false;
        });

        if (every(WEB_INTERVAL)) {
            Player target = fight.randomPlayer();
            if (target != null) {
                webTarget = target.getLocation();
                webAt = now + WEB_WARNING;
                fight.telegraph(webTarget, 3, WEB_WARNING, WEB, FloorDecals.Mark.WEB);
                fight.playAction(mother, "WEB_PREPARE", target);
                target.playSound(target.getLocation(), Sound.ENTITY_SPIDER_AMBIENT, 1F, 0.6F);
            }
        }
        if (now == webAt) {
            fight.addHazard(webTarget, 3, 160, WEB, FloorDecals.Zone.WEB,
                player -> player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 1, false, true)));
            webTarget.getWorld().spawnParticle(Particle.BLOCK, webTarget, 30, 1.5, 0.1, 1.5, Material.COBWEB.createBlockData());
        }

        if (every(POUNCE_INTERVAL) && mother.isValid()) {
            Player target = fight.nearestPlayer(mother.getLocation());
            if (target != null && target.getLocation().distance(mother.getLocation()) > 5) {
                pounceTarget = target;
                pounceAt = now + POUNCE_WARNING;
                fight.telegraph(target.getLocation(), 2.5, POUNCE_WARNING + 10, org.bukkit.Color.fromRGB(150, 30, 30), FloorDecals.Mark.DIVE);
                fight.playAction(mother, "POUNCE_PREPARE", target);
                mother.getWorld().playSound(mother.getLocation(), Sound.ENTITY_SPIDER_AMBIENT, 1.5F, 0.5F);
                mother.getWorld().spawnParticle(Particle.CRIT, mother.getLocation().add(0, 1, 0), 25, 0.6, 0.4, 0.6, 0.1);
            }
        }
        if (now == pounceAt && pounceTarget != null && pounceTarget.isValid() && mother.isValid()) {
            Vector jump = pounceTarget.getLocation().toVector().subtract(mother.getLocation().toVector());
            jump.setY(0).multiply(0.14).setY(0.75);
            mother.setVelocity(jump);
            mother.setTarget(pounceTarget);
        }
    }

    private void layEggs(int now) {
        for (int i = 0; i < 2; i++) {
            Location at = fight.randomPoint(3, Math.min(8, fight.radius() - 2));
            BossFight.FightObject sac = fight.spawnObject(at, Material.SNIFFER_EGG, 1.3F, 3, () -> {});
            sacs.add(new Sac(sac, now + HATCH_DELAY));
        }
        fight.broadcast("&7The Brood Mother lays egg sacs. &fSmash them before they hatch!");
        if (mother.isValid()) {
            fight.playAction(mother, "EGG_SAC");
        }
    }

    private void hatch(Location at) {
        at.getWorld().playSound(at, Sound.ENTITY_TURTLE_EGG_HATCH, 1F, 0.8F);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 20, 0.3, 0.3, 0.3, Material.COBWEB.createBlockData());
        for (int i = 0; i < 3; i++) {
            fight.spawnAdd(CaveSpider.class, at, spider -> {
                BossFight.setAttribute(spider, Attribute.MAX_HEALTH, 12);
                spider.setHealth(12);
                fight.label(spider, SPIDERLING);
            });
        }
    }
}
