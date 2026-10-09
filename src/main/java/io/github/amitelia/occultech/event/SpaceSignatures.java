package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Charles's signatures: space, space travel, astronomy (Session E4).
 * <ul>
 * <li><b>meteors</b>: shadows grow on the floor (under players and around them), then meteors fall into them.</li>
 * <li><b>moons</b>: three moons orbit him for 10 s; touching one hurts. Time your way in between them.</li>
 * <li><b>black_hole</b>: a black hole grows over him for 2 s, then pulls everyone near toward him (sprint to get away)
 * and collapses on whoever is still close.</li>
 * <li><b>low_gravity</b>: a low-gravity field around him (slow falling, high jumps) - every so often, and always while the
 * black hole charges, so dodging gets floaty. Potion effects only: nothing is left on a player afterwards.</li>
 * </ul>
 */
final class SpaceSignatures {

    static final String ID = "RAID_CHARLES";
    private static final Mechanic METEOR = Mechanic.of(ID, "Meteor", 26, Mechanic.Kind.AREA, true);
    private static final Mechanic MOON = Mechanic.of(ID, "Moon", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic BLACK_HOLE = Mechanic.of(ID, "Black hole", 10, Mechanic.Kind.MAGIC, true);
    private static final Color SHADOW = Color.fromRGB(60, 40, 90);

    private SpaceSignatures() {}

    /** A block display centred on its location (blocks draw from their corner). */
    private static BlockDisplay rock(StaffKit kit, Location at, Material look, float size) {
        return kit.fight.spawnExtra(BlockDisplay.class, at, d -> {
            d.setBlock(look.createBlockData());
            d.setTransformation(new Transformation(new Vector3f(-size / 2, -size / 2, -size / 2), new AxisAngle4f(),
                new Vector3f(size, size, size), new AxisAngle4f()));
            d.setBrightness(new org.bukkit.entity.Display.Brightness(15, 15));
        });
    }

    /** Meteors fall into growing shadows. */
    static final class Meteors extends Signature {

        private static final int WARNING = 40;
        private static final int FALL = 15;
        private static final double RADIUS = 2.2;

        Meteors(StaffKit kit) {
            super(kit, 60);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null) {
                next = now + 20;
                return false;
            }
            next = now + 180;
            kit.claim(20);
            kit.body.swingMainHand();
            List<Location> spots = new ArrayList<>();
            List<Player> players = new ArrayList<>(kit.fight.players());
            java.util.Collections.shuffle(players);
            for (Player player : players.subList(0, Math.min(3, players.size()))) {
                spots.add(player.getLocation());
            }
            ThreadLocalRandom random = ThreadLocalRandom.current();
            for (int i = 0; i < 2; i++) {
                spots.add(kit.target.getLocation().add(random.nextDouble(-4, 4), 0, random.nextDouble(-4, 4)));
            }
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_BEACON_ACTIVATE, 1.5F, 0.5F);
            for (Location spot : spots) {
                kit.fight.telegraph(spot, RADIUS, WARNING, SHADOW);
                kit.later(WARNING - FALL, () -> {
                    BlockDisplay meteor = rock(kit, spot.clone().add(0, 18, 0), Material.MAGMA_BLOCK, 1.3F);
                    meteor.setTeleportDuration(FALL);
                    meteor.teleport(spot.clone().add(0, 0.6, 0));
                    spot.getWorld().playSound(spot, Sound.ENTITY_BLAZE_SHOOT, 1F, 0.5F);
                    kit.later(FALL, () -> {
                        meteor.remove();
                        spot.getWorld().spawnParticle(Particle.EXPLOSION, spot.clone().add(0, 0.5, 0), 2, 0.6, 0.2, 0.6, 0);
                        spot.getWorld().spawnParticle(Particle.FLAME, spot.clone().add(0, 0.3, 0), 30, RADIUS / 2, 0.2, RADIUS / 2, 0.05);
                        spot.getWorld().playSound(spot, Sound.ENTITY_GENERIC_EXPLODE, 1F, 0.8F);
                        if (kit.alive()) {
                            for (Player player : kit.playersNear(spot, RADIUS)) {
                                kit.fight.hit(player, METEOR, kit.body);
                            }
                        }
                    });
                });
            }
            return true;
        }
    }

    /** Three moons in orbit. */
    static final class Moons extends Signature {

        private static final int LIFE = 200;
        private static final double ORBIT = 3.5;
        private static final double SPIN = 0.07;
        private static final double TOUCH = 1.1;
        private final List<BlockDisplay> moons = new ArrayList<>();
        private final Map<UUID, Integer> touched = new HashMap<>();
        private double angle;
        private int age = -1;

        Moons(StaffKit kit) {
            super(kit, 100);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || age >= 0) {
                next = now + 20;
                return false;
            }
            next = now + 280;
            kit.claim(10);
            age = 0;
            touched.clear();
            for (int i = 0; i < 3; i++) {
                BlockDisplay moon = rock(kit, kit.body.getLocation().add(0, 1, 0), Material.END_STONE, 0.9F);
                moon.setTeleportDuration(1);
                moons.add(moon);
            }
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_CHIME, 2F, 0.5F);
            return true;
        }

        @Override
        void move() {
            if (age < 0) {
                return;
            }
            if (++age > LIFE || !kit.alive()) {
                moons.forEach(BlockDisplay::remove);
                moons.clear();
                age = -1;
                return;
            }
            angle += SPIN;
            Location center = kit.body.getLocation().add(0, 1, 0);
            for (int i = 0; i < moons.size(); i++) {
                double a = angle + Math.PI * 2 * i / moons.size();
                Location at = center.clone().add(Math.cos(a) * ORBIT, 0, Math.sin(a) * ORBIT);
                moons.get(i).teleport(at);
                for (Player player : kit.playersNear(at, TOUCH)) {
                    Integer last = touched.get(player.getUniqueId());
                    if (last == null || age - last >= 20) {
                        touched.put(player.getUniqueId(), age);
                        kit.fight.hit(player, MOON, kit.body);
                        StaffKit.knock(player, at, 0.7, 0.3);
                    }
                }
            }
        }
    }

    /** A black hole: grows, pulls, collapses. */
    static final class BlackHole extends Signature {

        private static final int WARNING = 40;
        private static final int PULL = 50;
        private static final double REACH = 9;
        private static final double COLLAPSE = 3;
        /** A nudge toward the hole every tick: far weaker than a sprint, so running away works. */
        private static final double PULL_STRENGTH = 0.07;
        private static final double MAX_PULLED_SPEED = 0.45;
        private static final Color PULL_COLOR = Color.fromRGB(150, 90, 230);
        private static final Color COLLAPSE_COLOR = Color.fromRGB(230, 60, 90);
        @javax.annotation.Nullable private org.bukkit.entity.Display hole;
        @javax.annotation.Nullable private org.bukkit.entity.ItemDisplay pullRing;
        private Location ground;
        private int pulling = -1;
        private float spin;

        BlackHole(StaffKit kit) {
            super(kit, 160);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || !kit.within(kit.target, REACH) || hole != null) {
                next = now + 20;
                return false;
            }
            next = now + 260;
            kit.claim(WARNING + PULL);
            ground = kit.body.getLocation();
            ground.setY(ground.getWorld().getHighestBlockYAt(ground) + 1);
            Location at = ground.clone().add(0, 2.6, 0);
            at.setYaw(0F);
            at.setPitch(0F);
            if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
                hole = io.github.amitelia.occultech.boss.FloorDecals.model(kit.fight, at, "raid_black_hole", null);
                hole.setTransformation(holeShape(0.05F, 0F));
                pullRing = io.github.amitelia.occultech.boss.FloorDecals.flat(kit.fight, ground, "floor_warning_ring", PULL_COLOR, REACH * 2);
            } else {
                hole = rock(kit, at, Material.BLACK_CONCRETE, 0.2F);
            }
            org.bukkit.entity.Display grown = hole;
            kit.later(1, () -> {
                if (grown.isValid()) {
                    grown.setInterpolationDelay(0);
                    grown.setInterpolationDuration(WARNING);
                    grown.setTransformation(holeShape(io.github.amitelia.occultech.boss.FloorDecals.enabled() ? 2.6F : 1.6F, 0F));
                }
            });
            at.getWorld().playSound(at, Sound.BLOCK_PORTAL_TRIGGER, 1.5F, 0.6F);
            for (Signature signature : kit.signatures()) {
                if (signature instanceof LowGravity field) {
                    field.open(WARNING);   // floaty while it charges, not during the pull
                }
            }
            kit.later(WARNING, () -> {
                pulling = 0;
                kit.fight.telegraph(ground, COLLAPSE, PULL, COLLAPSE_COLOR, io.github.amitelia.occultech.boss.FloorDecals.Mark.DANGER);
            });
            return true;
        }

        /** The hole's look: {@code size} across, turned {@code turn} about the vertical (the disk swirls round). */
        private static Transformation holeShape(float size, float turn) {
            return new Transformation(new Vector3f(), new AxisAngle4f(turn, 0, 1, 0), new Vector3f(size, size, size), new AxisAngle4f());
        }

        @Override
        boolean steering() {
            return hole != null;   // Charles holds still while the black hole charges and pulls
        }

        @Override
        void move() {
            if (hole == null) {
                return;
            }
            if (pulling < 0) {
                return;
            }
            pulling++;
            if (pulling % 5 == 0 && hole.isValid() && io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
                spin += 0.6F;
                hole.setInterpolationDelay(0);
                hole.setInterpolationDuration(5);
                hole.setTransformation(holeShape(2.6F, spin));
            }
            for (Player player : kit.playersNear(ground, REACH)) {
                Vector in = ground.toVector().subtract(player.getLocation().toVector()).setY(0);
                if (in.lengthSquared() > 0.36) {
                    Vector v = player.getVelocity().add(in.normalize().multiply(PULL_STRENGTH));
                    Vector flat = v.clone().setY(0);
                    if (flat.length() > MAX_PULLED_SPEED) {
                        flat.normalize().multiply(MAX_PULLED_SPEED);
                    }
                    player.setVelocity(flat.setY(v.getY()));
                }
            }
            if (pulling >= PULL || !kit.alive()) {
                Location center = hole.getLocation();
                hole.remove();
                hole = null;
                if (pullRing != null) {
                    pullRing.remove();
                    pullRing = null;
                }
                pulling = -1;
                center.getWorld().spawnParticle(Particle.SQUID_INK, center, 60, 1.5, 1, 1.5, 0.2);
                center.getWorld().playSound(center, Sound.ENTITY_WARDEN_SONIC_BOOM, 1F, 1.4F);
                if (kit.alive()) {
                    for (Player player : kit.playersNear(ground, COLLAPSE)) {
                        kit.fight.hit(player, BLACK_HOLE, kit.body);
                    }
                }
            }
        }
    }

    /** A low-gravity field around him. */
    static final class LowGravity extends Signature {

        private static final int LIFE = 120;
        private static final double RADIUS = 7;
        private int left;
        private int age;
        @javax.annotation.Nullable private org.bukkit.entity.ItemDisplay edge;

        LowGravity(StaffKit kit) {
            super(kit, 200);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null) {
                next = now + 20;
                return false;
            }
            next = now + 320;
            open(LIFE);
            return true;
        }

        /** Opens (or keeps open) the field for {@code ticks}. */
        void open(int ticks) {
            if (left <= 0) {
                kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_BEACON_AMBIENT, 2F, 1.6F);
            }
            left = Math.max(left, ticks);
        }

        @Override
        void move() {
            if (left <= 0) {
                if (edge != null) {
                    edge.remove();
                    edge = null;
                }
                return;
            }
            left--;
            Location center = kit.body.getLocation();
            if (io.github.amitelia.occultech.boss.FloorDecals.enabled() && kit.alive()) {
                // the field's edge: a pale ring on the floor that follows him
                if (edge == null || !edge.isValid()) {
                    edge = io.github.amitelia.occultech.boss.FloorDecals.flat(kit.fight, center, "floor_warning_ring", org.bukkit.Color.fromRGB(170, 210, 255), RADIUS * 2);
                    edge.setTeleportDuration(1);
                } else {
                    Location floor = center.clone();
                    floor.setY(edge.getLocation().getY());
                    floor.setYaw(0F);
                    floor.setPitch(0F);
                    edge.teleport(floor);
                }
            }
            if (age++ % 5 != 0 || !kit.alive()) {
                return;
            }
            for (int i = 0; i < 24 && !io.github.amitelia.occultech.boss.FloorDecals.enabled(); i++) {
                double a = Math.PI * 2 * i / 24 + age * 0.02;
                center.getWorld().spawnParticle(Particle.END_ROD, center.clone().add(Math.cos(a) * RADIUS, 0.2, Math.sin(a) * RADIUS), 1, 0, 0.1, 0, 0);
            }
            for (Player player : kit.playersNear(center, RADIUS)) {
                player.addPotionEffect(new PotionEffect(PotionEffectType.SLOW_FALLING, 15, 0, false, false));
                player.addPotionEffect(new PotionEffect(PotionEffectType.JUMP_BOOST, 15, 2, false, false));
            }
        }
    }
}
