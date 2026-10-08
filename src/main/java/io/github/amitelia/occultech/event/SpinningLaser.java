package io.github.amitelia.occultech.event;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Spinning lasers (Act 2, Session E6): beams turning around a boss. A low beam is jumped over; a full-height one has a
 * safe stretch along it (a gap) where it passes over you. They show still for a moment, then turn; at a fast pace they
 * can change direction. A player is hit at most once every 0.75 s.
 */
final class SpinningLaser implements RaidHazard {

    static final double LOW = 0.8;
    static final double FULL = 3;
    private static final double HALF_WIDTH = 0.5;
    private static final int COOLDOWN = 15;

    private final BossFight fight;
    private final LivingEntity pivot;
    private final int beams;
    private final double length;
    private final double height;
    private final double gapFrom;
    private final double gapTo;
    private final int warnTicks;
    private final int lifeTicks;
    private final boolean reverses;
    private final Color color;
    private final Mechanic mechanic;
    private final Map<UUID, Integer> hit = new HashMap<>();
    private double angle;
    private double spin;
    private int age;
    /** With the pack: a beam streak per beam, row and section (a full-height beam with a gap has two sections). */
    private final java.util.List<io.github.amitelia.occultech.boss.AirEffects.Streak> streaks = new java.util.ArrayList<>();
    /** With the pack: a full-height beam's curtains (one per section). */
    private final java.util.List<org.bukkit.entity.ItemDisplay> curtains = new java.util.ArrayList<>();

    /**
     * @param spin     radians per tick (negative: the other way)
     * @param gapFrom  a full-height beam's gap starts this far out (NaN for none)
     * @param reverses whether it changes direction halfway
     */
    SpinningLaser(BossFight fight, LivingEntity pivot, int beams, double length, double spin, double height, double gapFrom, double gapTo,
        int warnTicks, int lifeTicks, boolean reverses, Color color, Mechanic mechanic) {
        this.fight = fight;
        this.pivot = pivot;
        this.beams = beams;
        this.length = length;
        this.spin = spin;
        this.height = height;
        this.gapFrom = gapFrom;
        this.gapTo = gapTo;
        this.warnTicks = warnTicks;
        this.lifeTicks = lifeTicks;
        this.reverses = reverses;
        this.color = color;
        this.mechanic = mechanic;
        this.angle = Math.random() * Math.PI * 2;
        pivot.getWorld().playSound(pivot.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 2F, 0.5F);
    }

    @Override
    public boolean step() {
        age++;
        if (age > warnTicks + lifeTicks || !pivot.isValid() || pivot.isDead()) {
            streaks.forEach(io.github.amitelia.occultech.boss.AirEffects.Streak::snap);
            curtains.forEach(org.bukkit.entity.ItemDisplay::remove);
            return false;
        }
        boolean live = age > warnTicks;
        if (live) {
            if (reverses && age == warnTicks + lifeTicks / 2) {
                spin = -spin;
                pivot.getWorld().playSound(pivot.getLocation(), Sound.BLOCK_BEACON_DEACTIVATE, 2F, 1.6F);
            }
            angle += spin;
        }
        Location center = pivot.getLocation();
        if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            beams(center, live);
        } else if (live || age % 3 == 0) {
            draw(center, live);
        }
        if (!live) {
            return true;
        }
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            Integer last = hit.get(player.getUniqueId());
            if (last != null && age - last < COOLDOWN) {
                continue;
            }
            for (int i = 0; i < beams; i++) {
                double beam = angle + Math.PI * 2 * i / beams;
                if (RaidGeometry.laserHits(at.getX() - center.getX(), at.getZ() - center.getZ(), at.getY() - center.getY(), beam, HALF_WIDTH,
                    length, height, gapFrom, gapTo)) {
                    hit.put(player.getUniqueId(), age);
                    fight.hit(player, mechanic, pivot);
                    break;
                }
            }
        }
        return true;
    }

    /**
     * The pack's beams, re-aimed every tick as they spin. A low beam is a laser at shin height (thin while it warns, full
     * once it turns); a full-height one is a curtain of light per section, a line on the floor while it warns that rises
     * to its height once it turns.
     */
    private void beams(Location center, boolean live) {
        double[][] sections = Double.isNaN(gapFrom) ? new double[][] { { 0.8, length } } : new double[][] { { 0.8, gapFrom }, { gapTo, length } };
        int i = 0;
        for (int b = 0; b < beams; b++) {
            double beam = angle + Math.PI * 2 * b / beams;
            double cos = Math.cos(beam);
            double sin = Math.sin(beam);
            for (double[] section : sections) {
                if (height > LOW) {
                    Location from = center.clone().add(cos * section[0], 0, sin * section[0]);
                    Location to = center.clone().add(cos * section[1], 0, sin * section[1]);
                    Location middle = from.clone().add(to).multiply(0.5);
                    middle.setYaw(0F);
                    middle.setPitch(0F);
                    org.bukkit.util.Transformation shape = RaidWall.paneShape(to.getX() - from.getX(), to.getZ() - from.getZ(), live ? height : 0.15);
                    if (i >= curtains.size()) {
                        org.bukkit.entity.ItemDisplay curtain = io.github.amitelia.occultech.boss.FloorDecals.model(fight, middle, "raid_laser_wall", color);
                        curtain.setTeleportDuration(1);
                        curtain.setTransformation(shape);
                        curtains.add(curtain);
                    } else {
                        org.bukkit.entity.ItemDisplay curtain = curtains.get(i);
                        curtain.teleport(middle);
                        curtain.setInterpolationDelay(0);
                        curtain.setInterpolationDuration(age == warnTicks + 1 ? 6 : 1);   // rises as it starts to turn
                        curtain.setTransformation(shape);
                    }
                } else {
                    Location from = center.clone().add(cos * section[0], 0.4, sin * section[0]);
                    Location to = center.clone().add(cos * section[1], 0.4, sin * section[1]);
                    float width = live ? 0.6F : 0.15F;
                    if (i >= streaks.size()) {
                        streaks.add(io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "raid_laser", from, to, color, width));
                    } else {
                        streaks.get(i).aim(from, to, width, 1);
                    }
                }
                i++;
            }
        }
    }

    private void draw(Location center, boolean live) {
        Particle.DustOptions dust = new Particle.DustOptions(color, live ? 1.4F : 0.8F);
        double[] rows = height > LOW ? new double[] { 0.4, 1.4, 2.4 } : new double[] { 0.4 };
        double step = live ? 0.5 : 1;
        for (int i = 0; i < beams; i++) {
            double beam = angle + Math.PI * 2 * i / beams;
            double cos = Math.cos(beam);
            double sin = Math.sin(beam);
            for (double d = 0.8; d <= length; d += step) {
                if (!Double.isNaN(gapFrom) && d >= gapFrom && d <= gapTo) {
                    continue;
                }
                for (double row : rows) {
                    center.getWorld().spawnParticle(Particle.DUST, center.getX() + cos * d, center.getY() + row, center.getZ() + sin * d, 1, 0, 0, 0,
                        0, dust);
                }
            }
        }
    }
}
