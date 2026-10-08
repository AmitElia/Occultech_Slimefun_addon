package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Player;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Proxy's and Atlas's signatures (the same kit - Session E3). Nothing here is a real block: the walls and the TNT are
 * displays, and the plugin does the pushing and the damage.
 * <ul>
 * <li><b>walls</b>: two crossing walls rise through the group, cutting it into pockets for 8 s. Touching one pushes
 * you back and shocks you.</li>
 * <li><b>tnt</b>: takes turns between throws (TNT lands on players and flashes for 2 s) and a line of TNT laid down a
 * lane, going off one after another.</li>
 * </ul>
 */
final class BuilderSignatures {

    static final String ID = "RAID_BUILDER";
    private static final Mechanic SHOCK = Mechanic.of(ID, "Wall shock", 8, Mechanic.Kind.ZONE, true);
    private static final Mechanic TNT = Mechanic.of(ID, "TNT", 28, Mechanic.Kind.AREA, true);
    private static final Color TNT_WARNING = Color.fromRGB(230, 60, 40);

    private BuilderSignatures() {}

    /** Two crossing walls through the group. */
    static final class Walls extends Signature {

        private static final double LENGTH = 10;
        private static final int WARNING = 25;
        private static final int LIFE = 160;
        private final List<RaidWall> walls = new ArrayList<>();

        Walls(StaffKit kit) {
            super(kit, 80);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || !walls.isEmpty()) {
                next = now + 20;
                return false;
            }
            next = now + 220;
            kit.claim(WARNING);
            kit.body.swingMainHand();
            Location center = kit.target.getLocation();
            double angle = ThreadLocalRandom.current().nextDouble(Math.PI);
            for (double turn : new double[] { angle, angle + Math.PI / 2 }) {
                Vector half = new Vector(Math.cos(turn), 0, Math.sin(turn)).multiply(LENGTH / 2);
                walls.add(new RaidWall(kit.fight, center.clone().subtract(half), center.clone().add(half), 3, Material.LIGHT_BLUE_STAINED_GLASS,
                    WARNING, LIFE, SHOCK, kit.body));
            }
            center.getWorld().playSound(center, Sound.BLOCK_SCAFFOLDING_PLACE, 1.5F, 0.6F);
            return true;
        }

        @Override
        void move() {
            walls.removeIf(wall -> !wall.step());
        }
    }

    /** TNT that isn't TNT: thrown, or laid in a line. */
    static final class Tnt extends Signature {

        private static final int FLIGHT = 16;
        private static final int FUSE = 40;
        private static final double RADIUS = 3;
        private static final int MAX = 8;
        private static final double LINE_LENGTH = 12;

        /** One fake TNT: flies from {@code from} to {@code to}, then flashes on its fuse and goes off. */
        private final class Bomb {
            final BlockDisplay display;
            final Location from;
            final Location to;
            final int flight;
            final int fuse;
            int age;

            Bomb(Location from, Location to, int flight, int fuse) {
                this.from = from.clone();
                this.to = to.clone();
                this.flight = flight;
                this.fuse = fuse;
                this.display = kit.fight.spawnExtra(BlockDisplay.class, flight > 0 ? from : to, d -> {
                    d.setBlock(Material.TNT.createBlockData());
                    d.setTransformation(new Transformation(new Vector3f(-0.4F, 0, -0.4F), new AxisAngle4f(), new Vector3f(0.8F, 0.8F, 0.8F),
                        new AxisAngle4f()));
                    d.setTeleportDuration(1);
                });
                kit.fight.telegraph(to, RADIUS, flight + fuse, TNT_WARNING);
            }

            /** False once it went off. */
            boolean step() {
                age++;
                if (age <= flight) {
                    double t = age / (double) flight;
                    Location at = from.clone().add(to.toVector().subtract(from.toVector()).multiply(t));
                    at.add(0, Math.sin(Math.PI * t) * 4, 0);
                    display.teleport(at);
                    return true;
                }
                int burning = age - flight;
                int every = burning > fuse - 12 ? 2 : 5;
                if (burning % every == 0) {
                    boolean white = (burning / every) % 2 == 0;
                    display.setBlock((white ? Material.WHITE_CONCRETE : Material.TNT).createBlockData());
                }
                if (burning == 1) {
                    to.getWorld().playSound(to, Sound.ENTITY_TNT_PRIMED, 1F, 1F);
                }
                if (burning < fuse) {
                    return true;
                }
                display.remove();
                to.getWorld().spawnParticle(Particle.EXPLOSION, to.clone().add(0, 0.5, 0), 3, 0.8, 0.4, 0.8, 0);
                to.getWorld().playSound(to, Sound.ENTITY_GENERIC_EXPLODE, 1F, 1F);
                for (Player player : kit.playersNear(to, RADIUS)) {
                    kit.fight.hit(player, TNT, kit.body);
                    StaffKit.knock(player, to, 0.9, 0.5);
                }
                return false;
            }
        }

        private final List<Bomb> bombs = new ArrayList<>();
        private boolean line;

        Tnt(StaffKit kit) {
            super(kit, 100);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || bombs.size() >= MAX || !kit.alive()) {
                next = now + 20;
                return false;
            }
            next = now + 140;
            line = !line;
            kit.body.swingMainHand();
            Location hand = kit.body.getLocation().add(0, 1.4, 0);
            if (line) {
                kit.claim(20);
                Location start = kit.body.getLocation();
                Location end = StaffKit.lane(start, kit.target.getLocation(), LINE_LENGTH);
                Vector step = end.toVector().subtract(start.toVector()).multiply(1 / 5.0);
                for (int i = 1; i <= 5; i++) {
                    Location spot = start.clone().add(step.clone().multiply(i));
                    bombs.add(new Bomb(spot, spot, 0, FUSE + i * 5));   // set down, not thrown: one after another
                }
                start.getWorld().playSound(start, Sound.BLOCK_GRASS_PLACE, 1.5F, 0.8F);
            } else {
                kit.claim(15);
                List<Player> targets = new ArrayList<>(kit.fight.players());
                java.util.Collections.shuffle(targets);
                for (Player player : targets.subList(0, Math.min(3, targets.size()))) {
                    if (bombs.size() < MAX) {
                        bombs.add(new Bomb(hand, player.getLocation(), FLIGHT, FUSE));
                    }
                }
                hand.getWorld().playSound(hand, Sound.ENTITY_SNOWBALL_THROW, 1.5F, 0.6F);
            }
            return true;
        }

        @Override
        void move() {
            for (Iterator<Bomb> it = bombs.iterator(); it.hasNext();) {
                Bomb bomb = it.next();
                if (!bomb.display.isValid() || !bomb.step()) {
                    bomb.display.remove();
                    it.remove();
                }
            }
        }
    }
}
