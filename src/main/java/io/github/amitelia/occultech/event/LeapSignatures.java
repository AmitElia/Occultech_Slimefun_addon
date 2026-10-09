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
 * Staff who leap (Session E10). The big landings hit the warned circle, wherever the body comes down.
 * <ul>
 * <li><b>hammer</b> (Amya): a hammer drop - a ring warns at a player, Amya leaps onto it and brings the hammer down;
 * the impact hits the ring and sends a shockwave ring out across the floor.</li>
 * <li><b>flop</b> (YahooFlop): doesn't walk - hops around, high, toward the fight ("Yahoo!"). Sometimes a huge jump onto
 * a big warned circle: a heavy landing and a shockwave, then YahooFlop lies flat as if in bed for a while, taking
 * extra damage.</li>
 * </ul>
 */
final class LeapSignatures {

    private static final Mechanic HAMMER = Mechanic.of("RAID_AMYA", "Hammer drop", 32, Mechanic.Kind.AREA, true);
    private static final Mechanic HAMMER_WAVE = Mechanic.of("RAID_AMYA", "Hammer shockwave", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic STOMP = Mechanic.of("RAID_YAHOO", "Flop stomp", 18, Mechanic.Kind.AREA, false);
    private static final Mechanic BELLY_FLOP = Mechanic.of("RAID_YAHOO", "Belly flop", 32, Mechanic.Kind.AREA, true);
    private static final Mechanic FLOP_WAVE = Mechanic.of("RAID_YAHOO", "Flop shockwave", 20, Mechanic.Kind.AREA, true);

    private LeapSignatures() {}

    /** A leap that lands on {@code spot} in about {@code ticks} (the body falls under gravity). */
    static Vector leap(Location from, Location spot, double up, int ticks) {
        Vector flat = spot.toVector().subtract(from.toVector()).setY(0);
        return flat.multiply(1.0 / Math.max(1, ticks)).setY(up);
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
        private int air = -1;

        Hammer(StaffKit kit) {
            super(kit, 60);
            kit.body.getEquipment().setItemInMainHand(new ItemStack(Material.MACE));
        }

        @Override
        boolean cast(int now) {
            Player target = kit.target;
            if (target == null || air >= 0 || !kit.within(target, 16) || !kit.body.isOnGround()) {
                next = now + 20;
                return false;
            }
            next = now + 160;
            kit.claim(WARNING + 10);
            spot = target.getLocation();
            spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
            kit.fight.telegraph(spot, RADIUS, WARNING, COLOR, FloorDecals.Mark.SLAM);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ITEM_MACE_SMASH_AIR, 2F, 0.6F);
            Abyss.face(kit.body, spot);
            kit.body.setVelocity(leap(kit.body.getLocation(), spot, 1.0, WARNING - 4));
            air = 0;
            return true;
        }

        @Override
        boolean steering() {
            return air >= 0;
        }

        @Override
        void move() {
            rings.removeIf(ring -> !ring.step());
            if (air < 0) {
                return;
            }
            air++;
            if (air >= WARNING) {
                air = -1;
                if (kit.alive()) {
                    kit.body.swingMainHand();
                    kit.body.getWorld().playSound(spot, Sound.ITEM_MACE_SMASH_GROUND_HEAVY, 2F, 0.8F);
                    land(kit, spot, RADIUS, HAMMER, HAMMER_WAVE, COLOR, rings);
                }
            }
        }
    }

    /** YahooFlop: hops everywhere, belly-flops, naps. */
    static final class Flop extends Signature {

        private static final int BIG_WARNING = 40;
        private static final double BIG_RADIUS = 6;
        private static final int NAP = 50;
        private static final Color COLOR = Color.fromRGB(255, 140, 200);
        private final java.util.List<RaidRing> rings = new java.util.ArrayList<>();
        @Nullable private Location spot;
        private int air = -1;
        private int nap = -1;
        private int nextHop;
        private int age;
        private boolean hopping;

        Flop(StaffKit kit) {
            super(kit, 100);
        }

        @Override
        boolean steering() {
            return true;   // YahooFlop never walks: hops, flops and naps
        }

        @Override
        double incoming() {
            return nap >= 0 ? 1.5 : 1;   // lying in "bed": easy to hit
        }

        @Override
        boolean cast(int now) {
            Player target = kit.target;
            if (target == null || air >= 0 || nap >= 0 || !kit.body.isOnGround()) {
                next = now + 20;
                return false;
            }
            next = now + 220;
            kit.claim(BIG_WARNING + NAP + 10);
            spot = target.getLocation();
            spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
            kit.fight.telegraph(spot, BIG_RADIUS, BIG_WARNING, COLOR, FloorDecals.Mark.SLAM);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_VILLAGER_CELEBRATE, 2F, 1.6F);
            kit.fight.broadcast("&d" + kit.member.display() + ": &fYAHOOOOO!");
            kit.body.setVelocity(leap(kit.body.getLocation(), spot, 1.5, BIG_WARNING - 2));
            air = 0;
            return true;
        }

        @Override
        void move() {
            age++;
            rings.removeIf(ring -> !ring.step());
            if (!kit.alive()) {
                return;
            }
            if (nap >= 0) {
                if (++nap >= NAP) {
                    nap = -1;
                    kit.body.setPose(Pose.STANDING, false);
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PLAYER_BURP, 1F, 1.2F);
                }
                return;
            }
            if (air >= 0) {
                air++;
                if (air >= BIG_WARNING) {
                    air = -1;
                    land(kit, spot, BIG_RADIUS, BELLY_FLOP, FLOP_WAVE, COLOR, rings);
                    nap = 0;
                    kit.body.setVelocity(new Vector());
                    kit.body.setPose(Pose.SLEEPING, true);               // flat on the floor, as if in bed
                    kit.fight.broadcast("&d" + kit.member.display() + " &7is taking a nap - &fhit now!");
                }
                return;
            }
            // ordinary hops: high, toward the fight; a small stomp where they land
            if (hopping && kit.body.isOnGround() && age > 4) {
                hopping = false;
                for (Player player : kit.playersNear(kit.body.getLocation(), 1.8)) {
                    kit.fight.hit(player, STOMP, kit.body);
                }
            }
            int now = kit.fight.elapsed();
            if (!hopping && kit.body.isOnGround() && now >= nextHop) {
                nextHop = now + 15;
                Location toward = kit.target != null && kit.fighting(kit.target) ? kit.target.getLocation() : kit.home;
                Vector flat = toward.toVector().subtract(kit.body.getLocation().toVector()).setY(0);
                double distance = flat.length();
                if (distance > 0.5) {
                    Abyss.face(kit.body, toward);
                    kit.body.setVelocity(flat.normalize().multiply(Math.min(0.45, distance / 12)).setY(0.95));
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_SLIME_JUMP, 1F, 1.4F);
                    hopping = true;
                    age = 0;
                }
            }
        }
    }
}
