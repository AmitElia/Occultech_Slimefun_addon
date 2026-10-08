package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Display;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * A barrier that sweeps the arena (Act 2, Session E6): a wall across the whole floor, too tall to jump, with one gap.
 * It shows at one edge first, then moves across; walk through the gap as it passes. Touching it hurts once and shoves
 * you along with it. Display entities only, no blocks.
 */
final class MovingBarrier implements RaidHazard {

    private static final double HEIGHT = 3;
    private static final float THICKNESS = 0.4F;
    private static final double REACH = 0.7;

    private final BossFight fight;
    private final Location middle;
    private final Vector dir;
    private final Vector across;
    private final double halfLength;
    private final double gapCenter;
    private final double gapHalfWidth;
    private final double speed;
    private final int warnTicks;
    private final Mechanic mechanic;
    private final LivingEntity source;
    private final List<BlockDisplay> pieces = new ArrayList<>();
    private final Set<UUID> hit = new HashSet<>();
    private double travelled;
    private int age;

    /**
     * @param angle     the direction it moves (radians, {@code atan2(dz, dx)})
     * @param halfWidth half the arena's width it spans (usually the arena radius)
     */
    MovingBarrier(BossFight fight, Location middle, double angle, double halfWidth, double speed, double gapHalfWidth, int warnTicks,
        Material look, Mechanic mechanic, LivingEntity source) {
        this.fight = fight;
        this.middle = middle.clone();
        this.dir = new Vector(Math.cos(angle), 0, Math.sin(angle));
        this.across = new Vector(-dir.getZ(), 0, dir.getX());
        this.halfLength = halfWidth;
        this.gapHalfWidth = gapHalfWidth;
        double room = halfWidth - gapHalfWidth - 2;
        this.gapCenter = room > 0 ? ThreadLocalRandom.current().nextDouble(-room, room) : 0;
        this.speed = speed;
        this.warnTicks = warnTicks;
        this.mechanic = mechanic;
        this.source = source;
        // two slabs, one each side of the gap
        piece(look, -halfLength, gapCenter - gapHalfWidth);
        piece(look, gapCenter + gapHalfWidth, halfLength);
        middle.getWorld().playSound(line(), Sound.BLOCK_BEACON_ACTIVATE, 2F, 0.6F);
    }

    /** Where the barrier's line crosses the arena's middle line now. */
    private Location line() {
        return middle.clone().add(dir.clone().multiply(-halfLength + travelled));
    }

    private void piece(Material look, double from, double to) {
        float length = (float) (to - from);
        if (length <= 0.1) {
            return;
        }
        // the block's +x runs along the barrier; turning by theta around y maps +x to (cos, 0, -sin)
        float theta = (float) Math.atan2(-across.getZ(), across.getX());
        Vector3f shift = new Vector3f(0, 0, -THICKNESS / 2).rotateY(theta);
        Location at = line().add(across.clone().multiply(from));
        BlockDisplay display = fight.spawnExtra(BlockDisplay.class, at, d -> {
            d.setBlock(look.createBlockData());
            d.setTransformation(new Transformation(shift, new AxisAngle4f(theta, 0, 1, 0), new Vector3f(length, (float) HEIGHT, THICKNESS),
                new AxisAngle4f()));
            d.setBrightness(new Display.Brightness(15, 15));
            d.setTeleportDuration(1);
        });
        pieces.add(display);
    }

    @Override
    public boolean step() {
        age++;
        if (age <= warnTicks) {
            return true;
        }
        travelled += speed;
        if (travelled > halfLength * 2) {
            pieces.forEach(BlockDisplay::remove);
            return false;
        }
        Vector move = dir.clone().multiply(speed);
        for (BlockDisplay piece : pieces) {
            piece.teleport(piece.getLocation().add(move));
        }
        Location line = line();
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            if (at.getY() > line.getY() + HEIGHT || at.getY() < line.getY() - 1 || hit.contains(player.getUniqueId())) {
                continue;
            }
            Vector offset = at.toVector().subtract(line.toVector());
            double along = offset.dot(dir);
            double side = offset.dot(across);
            if (RaidGeometry.barrierHits(along, side, gapCenter, gapHalfWidth, REACH, halfLength)) {
                hit.add(player.getUniqueId());
                fight.hit(player, mechanic, source);
                player.setVelocity(dir.clone().multiply(0.9).setY(0.3));
            }
        }
        return true;
    }
}
