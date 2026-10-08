package io.github.amitelia.occultech.event;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.BooleanSupplier;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.entity.Pose;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * X, the Founder (Council seat, Session E7): a giant. Walks slowly near the middle and crushes whoever is at his feet.
 * <ul>
 * <li><b>Stomp</b> (raid mechanic): a ring warns at his feet, then rings spread across the floor - jump them (two waves from
 * the middle band on).</li>
 * <li><b>Founder's Sweep</b> (raid mechanic): lasers turn around him, low ones to jump and full-height ones with a gap.</li>
 * <li><b>Foundation Stones</b> (raid mechanic): soak circles.</li>
 * <li><b>Kick</b>: a cone in front of him warns, then everyone in it flies.</li>
 * <li><b>Stagger</b>: enough damage at his feet in a short time and he drops to a knee for 4 s, taking half again as much.</li>
 * </ul>
 */
final class Founder extends CouncilMember {

    private static final Mechanic CRUSH = Mechanic.of(CouncilBehavior.ID, "Crush (Founder)", 22, Mechanic.Kind.MELEE, false);
    private static final Mechanic STOMP = Mechanic.of(CouncilBehavior.ID, "Stomp (Founder)", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic SWEEP = Mechanic.of(CouncilBehavior.ID, "Founder's Sweep (Founder)", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic STONE = Mechanic.of(CouncilBehavior.ID, "Foundation Stone (Founder)", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic CRUMBLE = Mechanic.of(CouncilBehavior.ID, "Crumbling foundation (Founder)", 30, Mechanic.Kind.AREA, true);
    private static final Mechanic KICK = Mechanic.of(CouncilBehavior.ID, "Kick (Founder)", 26, Mechanic.Kind.AREA, true);
    static final double SCALE = 6;
    private static final double REACH = 5;
    private static final double KICK_REACH = 8;
    private static final double KICK_HALF_ANGLE = Math.toRadians(30);
    /** Damage at his feet within 8 s, as a share of the pool, that drops him to a knee. */
    private static final double STAGGER_SHARE = 0.015;
    private static final int KNEEL = 80;

    private final Deque<double[]> footHits = new ArrayDeque<>();
    private int nextCrush;
    private int nextKick = 120;
    private int kneelUntil = -1;
    private int staggerReady;
    private boolean fullBeam;

    Founder(CouncilBehavior council, Location at, CouncilBehavior.Seat seat) {
        super(council, at, seat);
        BossFight.setAttribute(body, Attribute.SCALE, SCALE);
        BossFight.setAttribute(body, Attribute.KNOCKBACK_RESISTANCE, 1);
    }

    @Override
    List<BooleanSupplier> majors() {
        return List.of(this::stomp, this::sweep, this::stones);
    }

    @Override
    double incoming() {
        return kneeling() ? 1.5 : 1;
    }

    private boolean kneeling() {
        return fight.elapsed() < kneelUntil;
    }

    @Override
    void onHitBy(Player player, double damage) {
        if (!within(player, REACH + 1) || kneeling()) {
            return;
        }
        int now = fight.elapsed();
        footHits.addLast(new double[] { now, damage });
        double sum = 0;
        while (!footHits.isEmpty() && now - footHits.peekFirst()[0] > 160) {
            footHits.removeFirst();
        }
        for (double[] hit : footHits) {
            sum += hit[1];
        }
        if (now >= staggerReady && sum >= council.poolMax() * STAGGER_SHARE) {
            kneelUntil = now + KNEEL;
            staggerReady = now + KNEEL + 400;
            footHits.clear();
            body.setPose(Pose.SNEAKING, true);
            body.getWorld().playSound(body.getLocation(), Sound.ENTITY_IRON_GOLEM_DAMAGE, 2F, 0.5F);
            fight.broadcast("&6" + seat.display() + " &estumbles to a knee - &fhit hard now!");
        }
    }

    @Override
    void tick(int now) {
        if (kneelUntil >= 0 && now >= kneelUntil) {
            kneelUntil = -1;
            body.setPose(Pose.STANDING, false);
        }
        if (kneeling()) {
            return;
        }
        Player close = nearest();
        if (close != null && now >= nextCrush && within(close, REACH)) {
            nextCrush = now + 40;
            body.swingMainHand();
            council.hit(close, CRUSH, body);
            Abyss.face(body, close.getLocation());
        }
        if (close != null && now >= nextKick && within(close, KICK_REACH)) {
            nextKick = now + council.pace().cooldown(220);
            kick(close);
        }
    }

    @Override
    void move() {
        if (kneeling()) {
            body.setVelocity(new Vector(0, body.getVelocity().getY(), 0));
            return;
        }
        Player close = nearest();
        if (close != null) {
            walk(close.getLocation(), 0.12, REACH - 1, fight.radius() * 0.45);
        }
    }

    private void kick(Player toward) {
        Location at = body.getLocation();
        Vector aimAt = toward.getLocation().toVector().subtract(at.toVector());
        double aim = Math.atan2(aimAt.getZ(), aimAt.getX());
        Abyss.face(body, toward.getLocation());
        Particle.DustOptions dust = new Particle.DustOptions(Color.fromRGB(230, 80, 40), 1.5F);
        if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            io.github.amitelia.occultech.boss.FloorDecals.wedge(fight, at, aimAt, KICK_REACH, 25, Color.fromRGB(230, 80, 40));
        }
        for (int t = 0; t < 25 && !io.github.amitelia.occultech.boss.FloorDecals.enabled(); t += 5) {
            council.later(t, () -> {
                for (double a = aim - KICK_HALF_ANGLE; a <= aim + KICK_HALF_ANGLE; a += 0.08) {
                    for (double r = 2; r <= KICK_REACH; r += 1.5) {
                        at.getWorld().spawnParticle(Particle.DUST, at.clone().add(Math.cos(a) * r, 0.2, Math.sin(a) * r), 1, 0, 0, 0, 0, dust);
                    }
                }
            });
        }
        body.getWorld().playSound(at, Sound.ENTITY_RAVAGER_ROAR, 1.5F, 0.6F);
        council.later(25, () -> {
            if (!alive()) {
                return;
            }
            body.swingMainHand();
            Location now = body.getLocation();
            now.getWorld().playSound(now, Sound.ENTITY_IRON_GOLEM_ATTACK, 2F, 0.5F);
            for (Player player : fight.players()) {
                Vector to = player.getLocation().toVector().subtract(now.toVector());
                double distance = Math.hypot(to.getX(), to.getZ());
                if (distance <= KICK_REACH && Math.abs(RaidGeometry.angleBetween(Math.atan2(to.getZ(), to.getX()), aim)) <= KICK_HALF_ANGLE) {
                    council.hit(player, KICK, body);
                    player.setVelocity(new Vector(Math.cos(aim), 0, Math.sin(aim)).multiply(1.6).setY(0.55));
                }
            }
        });
    }

    private boolean stomp() {
        if (!alive() || kneeling()) {
            return false;
        }
        Location at = body.getLocation();
        fight.telegraph(at, 3.5, 30, Color.fromRGB(230, 120, 40));
        at.getWorld().playSound(at, Sound.ENTITY_RAVAGER_STEP, 2F, 0.4F);
        RaidPace pace = council.pace();
        council.later(30, () -> {
            if (!alive()) {
                return;
            }
            Location feet = body.getLocation();
            feet.getWorld().spawnParticle(Particle.EXPLOSION, feet, 4, 2, 0.2, 2, 0);
            feet.getWorld().spawnParticle(Particle.BLOCK, feet, 80, 3, 0.1, 3, Material.DIRT.createBlockData());
            feet.getWorld().playSound(feet, Sound.ENTITY_GENERIC_EXPLODE, 2F, 0.5F);
            for (int i = 0; i < pace.ringWaves(); i++) {
                council.add(new DelayedHazard(i * 15, new RaidRing(fight, feet, 0.35, fight.radius() - 1, RaidRing.LOW, Double.NaN,
                    Color.fromRGB(230, 120, 40), council.scaled(STOMP), body)), true);
            }
        });
        return true;
    }

    private boolean sweep() {
        if (!alive()) {
            return false;
        }
        RaidPace pace = council.pace();
        fullBeam = !fullBeam;
        double length = Math.min(16, fight.radius() * 0.5);
        double spin = (ThreadLocalRandom.current().nextBoolean() ? 1 : -1) * 0.03;
        council.add(new SpinningLaser(fight, body, pace.beams(), length, spin, fullBeam ? SpinningLaser.FULL : SpinningLaser.LOW,
            fullBeam ? length * 0.45 : Double.NaN, length * 0.45 + 2.5, 40, 220, pace.reverse(),
            fullBeam ? Color.fromRGB(255, 60, 60) : Color.fromRGB(255, 200, 40), council.scaled(SWEEP)), true);
        fight.broadcast("&6" + seat.display() + "&e's gaze sweeps the floor - " + (fullBeam ? "&fstand in the gaps!" : "&fjump the beams!"));
        return true;
    }

    private boolean stones() {
        if (!alive()) {
            return false;
        }
        council.soakCircles(STONE, CRUMBLE, body);
        body.getWorld().playSound(body.getLocation(), Sound.BLOCK_ANVIL_PLACE, 2F, 0.5F);
        fight.broadcast("&6" + seat.display() + " &elays the Foundation Stones - &ffill the circles!");
        return true;
    }
}
