package io.github.amitelia.occultech.event;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.entity.Pose;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Staff who leap (Session E10). Leaps are scripted arcs (no physics, no waiting for the ground): they land exactly where
 * they warned, every time.
 * <ul>
 * <li><b>hammer</b> (Amya): a hammer drop - a ring warns at a player, Amya leaps onto its centre and brings the hammer
 * down; the impact hits the ring and sends a shockwave ring out across the floor.</li>
 * <li><b>flop</b> (SuckedBean): never walks - hops all the time, high, toward the fight, with a small stomp where each hop
 * lands. Now and then a huge jump onto the centre of a big warned circle: a belly flop and a shockwave, then a nap flat
 * on the floor (as if in bed), taking extra damage.</li>
 * <li><b>mines</b> (YahooFlop): retreats often - runs away from the crowd, taunting - and whoever gives chase gets a
 * pressure-plate mine flicked down a few steps ahead of them, right where they're running: visible at once, armed a
 * moment later, it goes off when stepped on.</li>
 * </ul>
 */
final class LeapSignatures {

    private static final Mechanic HAMMER = Mechanic.of("RAID_AMYA", "Hammer drop", 32, Mechanic.Kind.AREA, true);
    private static final Mechanic HAMMER_WAVE = Mechanic.of("RAID_AMYA", "Hammer shockwave", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic STOMP = Mechanic.of("RAID_SUCKEDBEAN", "Flop stomp", 18, Mechanic.Kind.AREA, false);
    private static final Mechanic BELLY_FLOP = Mechanic.of("RAID_SUCKEDBEAN", "Belly flop", 32, Mechanic.Kind.AREA, true);
    private static final Mechanic FLOP_WAVE = Mechanic.of("RAID_SUCKEDBEAN", "Flop shockwave", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic MINE = Mechanic.of("RAID_YAHOO", "Pressure mine", 24, Mechanic.Kind.AREA, true);

    private LeapSignatures() {}

    /** The floor at {@code at}'s column, kept inside the arena (a leap never leaves it). */
    static Location floorSpot(StaffKit kit, Location at) {
        Location spot = at.clone();
        Location center = kit.fight.center();
        double reach = kit.fight.radius() - 2;
        double dx = spot.getX() - center.getX();
        double dz = spot.getZ() - center.getZ();
        double d = Math.hypot(dx, dz);
        if (d > reach) {
            spot.setX(center.getX() + dx / d * reach);
            spot.setZ(center.getZ() + dz / d * reach);
        }
        spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
        return spot;
    }

    /** A scripted jump: from where the body is to {@code to}, {@code ticks} long, {@code height} over the straight line. */
    static final class Arc {

        private final StaffKit kit;
        private final Location from;
        private final Location to;
        private final int ticks;
        private final double height;
        private int t;

        Arc(StaffKit kit, Location to, int ticks, double height) {
            this.kit = kit;
            this.from = kit.body.getLocation();
            this.to = to.clone();
            this.ticks = Math.max(2, ticks);
            this.height = height;
            Abyss.face(kit.body, to);
            kit.body.setGravity(false);
            kit.body.setVelocity(new Vector());
        }

        /** One tick of flight; true once it has landed (on {@code to} exactly). */
        boolean step() {
            t++;
            double f = Math.min(1, (double) t / ticks);
            Location at = from.clone().add(to.clone().subtract(from).toVector().multiply(f));
            at.setY(from.getY() + (to.getY() - from.getY()) * f + 4 * height * f * (1 - f));
            at.setYaw(kit.body.getLocation().getYaw());
            at.setPitch(0F);
            if (kit.alive()) {
                kit.body.teleport(at);
                kit.body.setVelocity(new Vector());
            }
            if (t >= ticks) {
                kit.body.setGravity(true);
                return true;
            }
            return false;
        }

        /** Stops mid-air (the body fell, or a bigger leap takes over): it comes down under gravity. */
        void cancel() {
            kit.body.setGravity(true);
        }
    }

    /** A heavy landing on {@code spot}: everyone within {@code radius} is hit and thrown; a shockwave ring goes out. */
    static void land(StaffKit kit, Location spot, double radius, Mechanic hit, Mechanic wave, Color color, java.util.List<RaidRing> rings) {
        spot.getWorld().spawnParticle(Particle.EXPLOSION, spot.clone().add(0, 0.3, 0), 4, radius / 3, 0.2, radius / 3, 0);
        spot.getWorld().spawnParticle(Particle.BLOCK, spot, 60, radius / 2, 0.1, radius / 2, Material.DIRT.createBlockData());
        spot.getWorld().playSound(spot, Sound.ENTITY_GENERIC_EXPLODE, 1.5F, 0.6F);
        for (Player player : kit.playersNear(spot, radius)) {
            kit.fight.hit(player, hit, kit.body);
            StaffKit.knock(player, spot, 1.0, 0.6);
        }
        rings.add(new RaidRing(kit.fight, spot, 0.35, 12, RaidRing.LOW, Double.NaN, color, wave, kit.body));
    }

    /** Amya's hammer drops. */
    static final class Hammer extends Signature {

        private static final int WARNING = 30;
        private static final double RADIUS = 4.5;
        private static final Color COLOR = Color.fromRGB(240, 170, 60);
        private final java.util.List<RaidRing> rings = new java.util.ArrayList<>();
        @Nullable private Location spot;
        @Nullable private Arc arc;

        Hammer(StaffKit kit) {
            super(kit, 60);
            kit.body.getEquipment().setItemInMainHand(new ItemStack(Material.MACE));
        }

        @Override
        boolean cast(int now) {
            Player target = kit.target;
            if (target == null || arc != null || !kit.within(target, 16)) {
                next = now + 20;
                return false;
            }
            next = now + 160;
            kit.claim(WARNING + 10);
            spot = floorSpot(kit, target.getLocation());
            kit.fight.telegraph(spot, RADIUS, WARNING, COLOR, FloorDecals.Mark.SLAM);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ITEM_MACE_SMASH_AIR, 2F, 0.6F);
            arc = new Arc(kit, spot, WARNING, 5);
            return true;
        }

        @Override
        boolean steering() {
            return arc != null;
        }

        @Override
        void move() {
            rings.removeIf(ring -> !ring.step());
            if (arc == null) {
                return;
            }
            if (!kit.alive()) {
                arc.cancel();
                arc = null;
                return;
            }
            if (arc.step()) {
                arc = null;
                kit.body.swingMainHand();
                kit.body.getWorld().playSound(spot, Sound.ITEM_MACE_SMASH_GROUND_HEAVY, 2F, 0.8F);
                land(kit, spot, RADIUS, HAMMER, HAMMER_WAVE, COLOR, rings);
            }
        }
    }

    /** SuckedBean: hops everywhere, belly-flops onto the centre of the circle, naps. */
    static final class Flop extends Signature {

        private static final int BIG_WARNING = 40;
        private static final double BIG_RADIUS = 6;
        private static final int NAP = 50;
        private static final int HOP_TICKS = 14;
        private static final int HOP_REST = 5;
        private static final Color COLOR = Color.fromRGB(255, 140, 200);
        private final java.util.List<RaidRing> rings = new java.util.ArrayList<>();
        @Nullable private Location spot;
        @Nullable private Arc arc;
        private boolean big;
        private int nap = -1;
        private int rest;

        Flop(StaffKit kit) {
            super(kit, 100);
        }

        @Override
        boolean steering() {
            return true;   // SuckedBean never walks: hops, flops and naps
        }

        @Override
        double incoming() {
            return nap >= 0 ? 1.5 : 1;   // lying in "bed": easy to hit
        }

        @Override
        boolean cast(int now) {
            Player target = kit.target;
            if (target == null || big || nap >= 0) {
                next = now + 20;
                return false;
            }
            next = now + 200;
            kit.claim(BIG_WARNING + NAP + 10);
            spot = floorSpot(kit, target.getLocation());
            kit.fight.telegraph(spot, BIG_RADIUS, BIG_WARNING, COLOR, FloorDecals.Mark.SLAM);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_VILLAGER_CELEBRATE, 2F, 1.6F);
            kit.fight.broadcast("&d" + kit.member.display() + ": &fYAHOOOOO!");
            if (arc != null) {
                arc.cancel();
            }
            arc = new Arc(kit, spot, BIG_WARNING, 9);   // up high, and down on the circle's centre as it fills
            big = true;
            return true;
        }

        @Override
        void move() {
            rings.removeIf(ring -> !ring.step());
            if (!kit.alive()) {
                if (arc != null) {
                    arc.cancel();
                    arc = null;
                }
                return;
            }
            if (nap >= 0) {
                kit.body.setVelocity(new Vector(0, Math.min(0, kit.body.getVelocity().getY()), 0));
                if (++nap >= NAP) {
                    nap = -1;
                    kit.body.setPose(Pose.STANDING, false);
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PLAYER_BURP, 1F, 1.2F);
                }
                return;
            }
            if (arc != null) {
                if (!arc.step()) {
                    return;
                }
                arc = null;
                if (big) {
                    big = false;
                    land(kit, spot, BIG_RADIUS, BELLY_FLOP, FLOP_WAVE, COLOR, rings);
                    nap = 0;
                    kit.body.setPose(Pose.SLEEPING, true);               // flat on the floor, as if in bed
                    kit.fight.broadcast("&d" + kit.member.display() + " &7is taking a nap - &fhit now!");
                } else {
                    Location at = kit.body.getLocation();                // a small stomp where each hop lands
                    at.getWorld().spawnParticle(Particle.BLOCK, at, 12, 0.6, 0.05, 0.6, Material.DIRT.createBlockData());
                    for (Player player : kit.playersNear(at, 1.8)) {
                        kit.fight.hit(player, STOMP, kit.body);
                    }
                    rest = HOP_REST;
                }
                return;
            }
            if (rest-- > 0) {
                return;
            }
            // the next hop: high, up to 4 blocks toward the fight
            Location toward = kit.target != null && kit.fighting(kit.target) ? kit.target.getLocation() : kit.home;
            Vector flat = toward.toVector().subtract(kit.body.getLocation().toVector()).setY(0);
            double step = Math.min(4, Math.max(0, flat.length() - 1));
            Location to = kit.body.getLocation().add(flat.lengthSquared() > 0.01 ? flat.normalize().multiply(step) : new Vector());
            arc = new Arc(kit, floorSpot(kit, to), HOP_TICKS, 2.6);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_SLIME_JUMP, 1F, 1.4F);
        }
    }

    /** YahooFlop: retreats, baiting a chase, and mines the path of whoever follows. */
    static final class Mines extends Signature {

        private static final int RETREAT = 120;
        private static final int MAX_MINES = 8;
        private static final int MINE_LIFE = 200;
        private static final int MINE_ARM = 4;
        private static final double MINE_RADIUS = 2.2;
        private static final double TRIGGER = 0.85;

        private record Mine(org.bukkit.entity.BlockDisplay plate, Location at, int armedAt, int until) {}

        private final java.util.List<Mine> mines = new java.util.ArrayList<>();
        /** Where each player was last tick: their running direction and speed. */
        private final java.util.Map<java.util.UUID, Location> last = new java.util.HashMap<>();
        private int retreating = -1;
        private int nextMine;

        Mines(StaffKit kit) {
            super(kit, 80);
        }

        @Override
        boolean steering() {
            return retreating >= 0;   // running away: the kit neither walks toward anyone nor swings
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || retreating >= 0) {
                next = now + 20;
                return false;
            }
            next = now + RETREAT + 80;   // back at it about 4 s after a retreat ends
            retreating = 0;
            kit.fight.broadcast("&d" + kit.member.display() + ": &fCatch me if you can!");
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_VILLAGER_TRADE, 2F, 1.6F);
            return true;
        }

        /** A pressure-plate mine at {@code at}: visible at once, armed a moment later, it goes off when stepped on. */
        private void layMine(Location at) {
            Location spot = floorSpot(kit, at);
            spot.setYaw(0F);
            spot.setPitch(0F);
            org.bukkit.entity.BlockDisplay plate = kit.fight.spawnExtra(org.bukkit.entity.BlockDisplay.class, spot, d -> {
                d.setBlock(Material.HEAVY_WEIGHTED_PRESSURE_PLATE.createBlockData());
                d.setTransformation(new org.bukkit.util.Transformation(new org.joml.Vector3f(-0.6F, 0.01F, -0.6F), new org.joml.AxisAngle4f(),
                    new org.joml.Vector3f(1.2F, 1, 1.2F), new org.joml.AxisAngle4f()));
                d.setGlowing(true);
                d.setGlowColorOverride(Color.fromRGB(255, 40, 40));
            });
            int now = kit.fight.elapsed();
            mines.add(new Mine(plate, spot, now + MINE_ARM, now + MINE_LIFE));
            spot.getWorld().playSound(spot, Sound.BLOCK_STONE_PRESSURE_PLATE_CLICK_ON, 1.5F, 0.6F);
            kit.body.swingMainHand();
        }

        /** Every tick: a mine someone steps on (once armed) goes off; old ones fade. */
        private void mines() {
            int now = kit.fight.elapsed();
            for (java.util.Iterator<Mine> it = mines.iterator(); it.hasNext();) {
                Mine mine = it.next();
                if (now >= mine.until() || !mine.plate().isValid()) {
                    mine.plate().remove();
                    it.remove();
                    continue;
                }
                if (now < mine.armedAt()) {
                    continue;
                }
                boolean stepped = false;
                for (Player player : kit.fight.players()) {
                    Location p = player.getLocation();
                    double dx = p.getX() - mine.at().getX();
                    double dz = p.getZ() - mine.at().getZ();
                    if (dx * dx + dz * dz < TRIGGER * TRIGGER && Math.abs(p.getY() - mine.at().getY()) < 1) {
                        stepped = true;
                        break;
                    }
                }
                if (stepped) {
                    mine.plate().remove();
                    it.remove();
                    Location at = mine.at();
                    at.getWorld().spawnParticle(Particle.EXPLOSION, at.clone().add(0, 0.4, 0), 2, 0.4, 0.2, 0.4, 0);
                    at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 1.3F, 1.4F);
                    for (Player player : kit.playersNear(at, MINE_RADIUS)) {
                        kit.fight.hit(player, MINE, kit.body);
                        StaffKit.knock(player, at, 0.5, 0.7);
                    }
                }
            }
        }

        @Override
        void move() {
            mines();
            // each player's motion since last tick: where they're running, and how fast
            java.util.Map<java.util.UUID, Vector> motion = new java.util.HashMap<>();
            for (Player player : kit.fight.players()) {
                Location before = last.put(player.getUniqueId(), player.getLocation());
                if (before != null && before.getWorld() == player.getWorld()) {
                    motion.put(player.getUniqueId(), player.getLocation().toVector().subtract(before.toVector()).setY(0));
                }
            }
            if (retreating < 0 || !kit.alive()) {
                return;
            }
            retreating++;
            Location me = kit.body.getLocation();
            // run away from the crowd, staying in the arena: bait them into following
            if (kit.target != null) {
                Vector away = me.toVector().subtract(kit.target.getLocation().toVector()).setY(0);
                if (away.lengthSquared() < 0.01) {
                    away = new Vector(1, 0, 0);
                }
                away.normalize();
                Location flee = me.clone().add(away.clone().multiply(5));
                Location center = kit.fight.center();
                double reach = kit.fight.radius() - 4;
                if (flee.distanceSquared(center) > reach * reach) {   // cornered: slip round along the edge
                    Vector side = new Vector(-away.getZ(), 0, away.getX());
                    Vector in = center.toVector().subtract(me.toVector()).setY(0);
                    flee = me.clone().add(side.multiply(5)).add(in.lengthSquared() > 0.01 ? in.normalize().multiply(2) : new Vector());
                }
                Abyss.walk(kit.body, flee, 0.36, 0);
            }
            // whoever chases gets a mine a few steps ahead of where they're running (armed before they get there)
            int now = kit.fight.elapsed();
            if (now >= nextMine && mines.size() < MAX_MINES) {
                for (Player player : kit.fight.players()) {
                    double d = player.getLocation().distance(me);
                    Vector run = motion.get(player.getUniqueId());
                    if (d < 2.5 || d > 10 || run == null) {
                        continue;
                    }
                    double speed = run.length();
                    Vector toMe = me.toVector().subtract(player.getLocation().toVector()).setY(0).normalize();
                    if (speed < 0.08 || run.clone().normalize().dot(toMe) < 0.3) {
                        continue;   // standing still, or not coming this way
                    }
                    double ahead = Math.min(d - 1, 1.6 + speed * (MINE_ARM + 3));
                    layMine(player.getLocation().add(run.clone().normalize().multiply(ahead)));
                    nextMine = now + 12;
                    break;
                }
            }
            if (retreating >= RETREAT) {
                retreating = -1;
            }
        }
    }
}
