package io.github.amitelia.occultech.event;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * A wall that isn't made of blocks (Proxy and Atlas; Act 2's barriers): a stretched block display, kept by the plugin.
 * A player who touches it is pushed back to their own side and shocked (at most once a second). It warns as a line on
 * the floor first, then rises. No world block changes. Call {@link #step()} every tick until it's done.
 */
final class RaidWall implements RaidHazard {

    private static final double REACH = 0.6;
    private static final float THICKNESS = 0.3F;
    private static final int RISE_TICKS = 8;

    private final BossFight fight;
    private final Location a;
    private final Location b;
    private final double height;
    private final Material look;
    private final int warnTicks;
    private final int lifeTicks;
    private final Mechanic mechanic;
    @Nullable private final LivingEntity source;
    private final Map<UUID, Integer> shocked = new HashMap<>();
    @Nullable private BlockDisplay display;
    private int age;

    RaidWall(BossFight fight, Location a, Location b, double height, Material look, int warnTicks, int lifeTicks, Mechanic mechanic,
        @Nullable LivingEntity source) {
        this.fight = fight;
        this.a = a.clone();
        this.b = b.clone();
        this.b.setY(a.getY());
        this.height = height;
        this.look = look;
        this.warnTicks = warnTicks;
        this.lifeTicks = lifeTicks;
        this.mechanic = mechanic;
        this.source = source;
    }

    /** One tick. False once the wall is gone. */
    @Override
    public boolean step() {
        age++;
        if (age < warnTicks) {
            if (age % 4 == 1) {
                warn();
            }
            return true;
        }
        if (age == warnTicks) {
            rise();
        } else if (age == warnTicks + 1 && display != null && display.isValid()) {
            // a tick after it appears: grow to full height, smoothly
            Transformation flat = display.getTransformation();
            display.setInterpolationDelay(0);
            display.setInterpolationDuration(RISE_TICKS);
            display.setTransformation(new Transformation(flat.getTranslation(), flat.getLeftRotation(),
                new Vector3f(flat.getScale().x(), (float) height, THICKNESS), flat.getRightRotation()));
        }
        if (age >= warnTicks + lifeTicks) {
            if (display != null) {
                display.remove();
            }
            return false;
        }
        if (age >= warnTicks + RISE_TICKS / 2) {
            hold();
        }
        return true;
    }

    /** Whether the wall stands now (risen, not yet gone). */
    boolean standing() {
        return display != null && display.isValid();
    }

    private void warn() {
        Particle.DustOptions dust = new Particle.DustOptions(Color.fromRGB(120, 200, 255), 1.3F);
        Vector ab = b.toVector().subtract(a.toVector());
        double length = ab.length();
        for (double d = 0; d <= length; d += 0.5) {
            Location at = a.clone().add(ab.clone().multiply(d / Math.max(0.01, length)));
            at.getWorld().spawnParticle(Particle.DUST, at.getX(), at.getY() + 0.15, at.getZ(), 1, 0, 0, 0, 0, dust);
        }
    }

    private void rise() {
        double dx = b.getX() - a.getX();
        double dz = b.getZ() - a.getZ();
        float length = (float) Math.hypot(dx, dz);
        // the block's +x runs along the wall; turning by theta around y maps +x to (cos, 0, -sin)
        float theta = (float) Math.atan2(-dz, dx);
        AxisAngle4f turn = new AxisAngle4f(theta, 0, 1, 0);
        // centre the slab's thickness on the line: its local -z/2 offset, turned the same way
        Vector3f shift = new Vector3f(0, 0, -THICKNESS / 2).rotateY(theta);
        display = fight.spawnExtra(BlockDisplay.class, a, d -> {
            d.setBlock(look.createBlockData());
            d.setTransformation(new Transformation(shift, turn, new Vector3f(length, 0.01F, THICKNESS), new AxisAngle4f()));
            d.setBrightness(new org.bukkit.entity.Display.Brightness(15, 15));
        });
        a.getWorld().playSound(a.clone().add(dx / 2, 0, dz / 2), Sound.BLOCK_PISTON_EXTEND, 1F, 0.6F);
    }

    /** Pushes back (and shocks) anyone touching the wall. */
    private void hold() {
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            if (at.getY() < a.getY() - 0.5 || at.getY() > a.getY() + height) {
                continue;
            }
            double[] off = RaidGeometry.fromWall(at.getX(), at.getZ(), a.getX(), a.getZ(), b.getX(), b.getZ());
            if (off[0] > REACH) {
                continue;
            }
            player.setVelocity(new Vector(off[1], 0, off[2]).multiply(0.6).setY(0.2));
            Integer last = shocked.get(player.getUniqueId());
            if (last == null || age - last >= 20) {
                shocked.put(player.getUniqueId(), age);
                fight.hit(player, mechanic, source);
                player.getWorld().spawnParticle(Particle.ELECTRIC_SPARK, at.clone().add(0, 1, 0), 10, 0.2, 0.4, 0.2, 0.05);
            }
        }
    }
}
