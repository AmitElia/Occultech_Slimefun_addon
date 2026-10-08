package io.github.amitelia.occultech.event;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * An expanding ring on the floor (FM's radio waves; Act 2's stomps and shockwaves). A low ring is jumped over; a tall
 * one has a gap to walk through. Each ring hits a player at most once. Call {@link #step()} every tick until it's done.
 */
final class RaidRing implements RaidHazard {

    /** A ring you jump over. */
    static final double LOW = 0.8;
    /** A ring too tall to jump: walk through its gap. */
    static final double TALL = 3;
    private static final double GAP_HALF_WIDTH = 1.6;

    private final BossFight fight;
    private final Location center;
    private final double speed;
    private final double maxRadius;
    private final double height;
    private final double gapAngle;
    private final Color color;
    private final Mechanic mechanic;
    @Nullable private final LivingEntity source;
    private final Set<UUID> hit = new HashSet<>();
    private double radius = 0.8;
    private int age;

    /**
     * @param gapAngle direction of the gap (radians, {@code atan2(dz, dx)}), or NaN for a ring without one
     */
    RaidRing(BossFight fight, Location center, double speed, double maxRadius, double height, double gapAngle, Color color,
        Mechanic mechanic, @Nullable LivingEntity source) {
        this.fight = fight;
        this.center = center.clone();
        this.speed = speed;
        this.maxRadius = maxRadius;
        this.height = height;
        this.gapAngle = gapAngle;
        this.color = color;
        this.mechanic = mechanic;
        this.source = source;
        if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            // the pack's travelling wave, timed to this ring (a tall ring keeps its particle curtain, which shows the gap)
            io.github.amitelia.occultech.boss.FloorDecals.wave(fight, this.center, radius, maxRadius, (int) Math.ceil((maxRadius - radius) / speed), color);
        }
    }

    /** One tick: grows, draws (every other tick), hits. False once it's past its reach. */
    @Override
    public boolean step() {
        radius += speed;
        if (radius > maxRadius) {
            return false;
        }
        if (age++ % 2 == 0 && (height > LOW || !io.github.amitelia.occultech.boss.FloorDecals.enabled())) {
            draw();
        }
        double band = Math.max(0.6, speed);
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            if (!hit.contains(player.getUniqueId()) && RaidGeometry.ringHits(at.getX() - center.getX(), at.getZ() - center.getZ(),
                at.getY() - center.getY(), radius, band, height, gapAngle, GAP_HALF_WIDTH)) {
                hit.add(player.getUniqueId());
                fight.hit(player, mechanic, source);
                Vector out = at.toVector().subtract(center.toVector()).setY(0);
                if (out.lengthSquared() > 0.01) {
                    player.setVelocity(out.normalize().multiply(0.5).setY(0.25));
                }
            }
        }
        return true;
    }

    private void draw() {
        double spacing = height > LOW ? 0.9 : 0.6;
        int points = (int) Math.min(90, Math.ceil(Math.PI * 2 * radius / spacing));
        Particle.DustOptions dust = new Particle.DustOptions(color, height > LOW ? 1.6F : 1.2F);
        double[] rows = height > LOW ? new double[] { 0.4, 1.4, 2.4 } : new double[] { 0.3 };
        for (int i = 0; i < points; i++) {
            double angle = Math.PI * 2 * i / points;
            if (!Double.isNaN(gapAngle) && Math.abs(RaidGeometry.angleBetween(angle, gapAngle)) * radius <= GAP_HALF_WIDTH) {
                continue;
            }
            double x = center.getX() + Math.cos(angle) * radius;
            double z = center.getZ() + Math.sin(angle) * radius;
            for (double row : rows) {
                center.getWorld().spawnParticle(Particle.DUST, x, center.getY() + row, z, 1, 0, 0, 0, 0, dust);
            }
        }
    }
}
