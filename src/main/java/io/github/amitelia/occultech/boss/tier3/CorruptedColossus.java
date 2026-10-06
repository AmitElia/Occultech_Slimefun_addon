package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.EntityEffect;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.IronGolem;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Tier-3 mini-boss (Infinity gear): an iron golem rebuilt by occult machinery - the boss the addon is named for.
 * <ul>
 * <li>Shockwave slam: it rears up, a ring warns for 1.2s, then the ground shakes - anyone on the ground inside is hurt
 * and thrown up. Jump to dodge.</li>
 * <li>Corrupted pylons: three pylons (hittable markers) fire beams at players and repair the Colossus while they
 * stand. They come back every 30s.</li>
 * <li>Overload below 30%: sparks everywhere, faster and more frequent slams.</li>
 * </ul>
 * Takes a tenth of the damage dealt.
 */
public final class CorruptedColossus extends BossBehavior {

    private static final double HEALTH = 400;
    private static final double ARMOR = 0.1;
    private static final io.github.amitelia.occultech.boss.Mechanic SMASH = io.github.amitelia.occultech.boss.Mechanic.of("CORRUPTED_COLOSSUS", "Smash", 44, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic SLAM_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("CORRUPTED_COLOSSUS", "Slam", 58, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final double SLAM_RADIUS = 7;
    private static final io.github.amitelia.occultech.boss.Mechanic PYLON_BEAM = io.github.amitelia.occultech.boss.Mechanic.of("CORRUPTED_COLOSSUS", "Pylon beam", 32, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final int PYLONS = 3;
    private static final int PYLON_INTERVAL = 400;
    private static final double SPEED = 0.32;
    private static final Color CORRUPT = Color.fromRGB(150, 40, 200);

    private IronGolem colossus;
    private final List<BossFight.FightObject> pylons = new ArrayList<>();
    /** Each pylon's stream of energy to the Colossus (Session O5). */
    private final java.util.Map<BossFight.FightObject, io.github.amitelia.occultech.boss.AirEffects.Streak> links = new java.util.HashMap<>();
    private final List<Abyss.Beam> beams = new ArrayList<>();
    private int slamAt = -1;
    private Location slamCenter;
    private boolean overloaded;

    public CorruptedColossus(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        colossus = fight.spawnBoss(IronGolem.class, at.clone().add(0, 1, 0), g -> {
            g.setCustomName(ChatColor.LIGHT_PURPLE + "Corrupted Colossus");
            g.setCustomNameVisible(true);
            g.setPlayerCreated(false);
            BossFight.setAttribute(g, Attribute.MAX_HEALTH, HEALTH);
            fight.label(g, SMASH);
            BossFight.setAttribute(g, Attribute.SCALE, 1.8);
            BossFight.setAttribute(g, Attribute.FOLLOW_RANGE, 48);
            BossFight.setAttribute(g, Attribute.MOVEMENT_SPEED, SPEED);
        });
        raisePylons();
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR;
    }

    @Override
    public void tick() {
        if (!colossus.isValid()) {
            return;
        }
        int now = fight.elapsed();
        // iron golems never pick players on their own: keep it on the nearest one
        Player nearest = fight.nearestPlayer(colossus.getLocation());
        if (nearest != null && colossus.getTarget() != nearest) {
            colossus.setTarget(nearest);
        }

        if (!overloaded && fight.healthFraction() < 0.3) {
            overloaded = true;
            BossFight.setAttribute(colossus, Attribute.MOVEMENT_SPEED, 0.4);
            fight.broadcast("&dThe Colossus overloads - &fits slams come faster!");
        }
        if (overloaded && every(10)) {
            colossus.getWorld().spawnParticle(Particle.ELECTRIC_SPARK, colossus.getLocation().add(0, 2.5, 0), 12, 0.8, 1.2, 0.8, 0.1);
        }

        // pylons: beams at players, and repairs while they stand
        pylons.removeIf(p -> !p.isAlive());
        if (every(PYLON_INTERVAL) && pylons.isEmpty()) {
            raisePylons();
        }
        if (!pylons.isEmpty() && every(100)) {
            fight.healBoss(colossus, 0.01 * pylons.size());
            if (!io.github.amitelia.occultech.boss.AirEffects.enabled()) {
                for (BossFight.FightObject pylon : pylons) {
                    Abyss.line(pylon.location().clone().add(0, 1.5, 0), colossus.getLocation().add(0, 2, 0), new Particle.DustOptions(CORRUPT, 0.8F), 0.6);
                }
            }
        }
        if (io.github.amitelia.occultech.boss.AirEffects.enabled()) {
            // each standing pylon feeds the Colossus a stream of corrupt energy; it snaps when the pylon breaks
            links.entrySet().removeIf(entry -> {
                boolean keep = entry.getKey().isAlive() && entry.getValue().valid();
                if (!keep) {
                    entry.getValue().snap();
                }
                return !keep;
            });
            for (BossFight.FightObject pylon : pylons) {
                Location from = pylon.location().clone().add(0, 1.5, 0);
                Location to = colossus.getLocation().add(0, 2, 0);
                io.github.amitelia.occultech.boss.AirEffects.Streak link = links.get(pylon);
                if (link == null) {
                    links.put(pylon, io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "air_beam", from, to, CORRUPT, 0.18F));
                } else {
                    link.aim(from, to, 0.18F, io.github.amitelia.occultech.boss.BossService.STEP);
                }
            }
        }
        if (!pylons.isEmpty() && every(80)) {
            for (BossFight.FightObject pylon : pylons) {
                Player target = fight.randomPlayer();
                if (target != null) {
                    beams.add(new Abyss.Beam(colossus, () -> pylon.isAlive() ? pylon.location().clone().add(0, 1.8, 0) : null,
                        target, now, 30, PYLON_BEAM, CORRUPT));
                }
            }
        }
        beams.forEach(beam -> beam.step(fight, now));
        beams.removeIf(Abyss.Beam::done);

        if (every(overloaded ? 70 : 100) && slamAt < 0) {
            slamAt = now + 25;
            slamCenter = colossus.getLocation();
            slamCenter.setY(Abyss.groundY(slamCenter));
            fight.telegraph(slamCenter, SLAM_RADIUS, 30, CORRUPT, FloorDecals.Mark.SLAM);
            colossus.playEffect(EntityEffect.ENTITY_ATTACK);
            colossus.getWorld().playSound(colossus.getLocation(), Sound.ENTITY_IRON_GOLEM_ATTACK, 2F, 0.5F);
        }
        if (slamAt >= 0 && now >= slamAt) {
            slamAt = -1;
            slam();
        }
    }

    private void slam() {
        slamCenter.getWorld().playSound(slamCenter, Sound.ENTITY_GENERIC_EXPLODE, 1.5F, 0.6F);
        slamCenter.getWorld().spawnParticle(Particle.BLOCK, slamCenter.clone().add(0, 0.3, 0), 120, SLAM_RADIUS / 2, 0.2, SLAM_RADIUS / 2,
            Material.IRON_BLOCK.createBlockData());
        slamCenter.getWorld().spawnParticle(Particle.EXPLOSION, slamCenter.clone().add(0, 0.5, 0), 3, 1.5, 0.2, 1.5);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, slamCenter.clone().add(0, 0.8, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, CORRUPT, 5F);
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            boolean grounded = at.getY() - Abyss.groundY(at) < 0.6;
            if (grounded && at.distanceSquared(slamCenter) <= SLAM_RADIUS * SLAM_RADIUS) {
                fight.hit(player, SLAM_DAMAGE, colossus);
                player.setVelocity(new Vector(0, 0.9, 0));
            }
        }
    }

    private void raisePylons() {
        for (int i = 0; i < PYLONS; i++) {
            Location at = fight.randomPoint(6, Math.min(fight.radius() - 3, 14));
            pylons.add(fight.spawnObject(at, Material.LIGHTNING_ROD, 2F, 5, () ->
                at.getWorld().playSound(at, Sound.BLOCK_COPPER_BULB_TURN_OFF, 2F, 0.6F)));
        }
        fight.broadcast("&dCorrupted pylons rise - &fthey repair the Colossus and fire at you. Break them!");
    }
}
