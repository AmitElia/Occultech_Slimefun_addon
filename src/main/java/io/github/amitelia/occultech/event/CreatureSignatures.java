package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Bat;
import org.bukkit.entity.Bee;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Fox;
import org.bukkit.entity.Horse;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Staff who fight alongside animals (Session E5). Every animal is one of the fight's own creatures: tagged, no drops,
 * can't be ridden, leashed, tamed or kept.
 * <ul>
 * <li><b>bees</b> (bee_grand): a few angry bees at a time; vanilla bees sting with poison and die after stinging.</li>
 * <li><b>bats</b> (Bat): a swarm circles him and hides him (he takes half damage meanwhile), then a player is marked and
 * the swarm dives on the spot.</li>
 * <li><b>foxes</b> (Jenn): a couple of foxes dart in, bite, and dart out again.</li>
 * <li><b>mount</b> (Griffon): he fights from horseback and charges down warned lanes; kill the horse and he's on foot.</li>
 * </ul>
 */
final class CreatureSignatures {

    private static final Mechanic BEE_STING = Mechanic.of("RAID_BEE", "Bee sting", 8, Mechanic.Kind.ADD, false);
    private static final Mechanic BAT_DIVE = Mechanic.of("RAID_BAT", "Bat dive", 24, Mechanic.Kind.AREA, true);
    private static final Mechanic FOX_BITE = Mechanic.of("RAID_JENN", "Fox bite", 10, Mechanic.Kind.ADD, false);
    private static final Mechanic CHARGE = Mechanic.of("RAID_GRIFFON", "Mount charge", 26, Mechanic.Kind.AREA, true);

    private CreatureSignatures() {}

    /** bee_grand's bees. */
    static final class Bees extends Signature {

        private static final int MAX = 5;
        private final List<Bee> bees = new ArrayList<>();

        Bees(StaffKit kit) {
            super(kit, 60);
        }

        @Override
        boolean cast(int now) {
            bees.removeIf(b -> !b.isValid() || b.isDead());
            if (kit.target == null || bees.size() >= MAX) {
                next = now + 40;
                return false;
            }
            next = now + 200;
            kit.claim(10);
            kit.body.swingMainHand();
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_BEEHIVE_EXIT, 1.5F, 1F);
            for (int i = 0; i < 3 && bees.size() < MAX; i++) {
                Location at = kit.body.getLocation().add(0, 1.8, 0);
                Player target = kit.target;
                Bee bee = kit.fight.spawnAdd(Bee.class, at, b -> {
                    b.setAnger(600);
                    b.setTarget(target);
                    BossFight.setAttribute(b, Attribute.MAX_HEALTH, 8);
                    b.setHealth(8);
                });
                if (bee == null) {
                    break;
                }
                kit.fight.label(bee, BEE_STING);
                bees.add(bee);
            }
            return true;
        }
    }

    /** Bat's swarm: hides him, then dives on a marked spot. */
    static final class Bats extends Signature {

        private static final int COUNT = 6;
        private static final int SWARM = 40;
        private static final int MARK = 30;
        private static final int DIVE = 25;
        private static final double RADIUS = 2.5;
        private final List<Bat> bats = new ArrayList<>();
        private int phaseTicks = -1;
        private boolean diving;
        @Nullable private Location spot;
        private int age;

        Bats(StaffKit kit) {
            super(kit, 100);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || phaseTicks >= 0) {
                next = now + 20;
                return false;
            }
            next = now + 240;
            kit.claim(SWARM + 10);
            for (int i = 0; i < COUNT; i++) {
                Bat bat = kit.fight.spawnExtra(Bat.class, kit.body.getLocation().add(0, 1.5, 0), b -> {
                    b.setAwake(true);
                    b.setSilent(true);
                });
                Abyss.puppet(bat);
                bats.add(bat);
            }
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_BAT_TAKEOFF, 2F, 0.6F);
            phaseTicks = 0;
            diving = false;
            return true;
        }

        @Override
        double incoming() {
            return phaseTicks >= 0 && !diving ? 0.5 : 1;   // hidden in the swarm
        }

        @Override
        void move() {
            age++;
            if (phaseTicks < 0) {
                return;
            }
            phaseTicks++;
            bats.removeIf(b -> !b.isValid() || b.isDead());
            if (!diving) {
                Location center = kit.body.getLocation().add(0, 1.2, 0);
                for (int i = 0; i < bats.size(); i++) {
                    double a = age * 0.25 + Math.PI * 2 * i / Math.max(1, bats.size());
                    Location want = center.clone().add(Math.cos(a) * 1.3, Math.sin(age * 0.3 + i) * 0.5, Math.sin(a) * 1.3);
                    bats.get(i).setVelocity(want.toVector().subtract(bats.get(i).getLocation().toVector()).multiply(0.5));
                }
                if (phaseTicks == SWARM) {
                    Player marked = kit.fight.randomPlayer();
                    if (marked == null || !kit.alive()) {
                        end();
                        return;
                    }
                    spot = marked.getLocation();
                    kit.fight.telegraph(spot, RADIUS, MARK, Color.fromRGB(60, 50, 50));
                    marked.playSound(marked.getLocation(), Sound.ENTITY_BAT_AMBIENT, 2F, 0.6F);
                }
                if (phaseTicks == SWARM + MARK) {
                    diving = true;
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PHANTOM_SWOOP, 2F, 1.4F);
                }
                return;
            }
            for (Bat bat : bats) {
                bat.setVelocity(spot.toVector().add(new Vector(0, 0.5, 0)).subtract(bat.getLocation().toVector()).normalize().multiply(0.8));
            }
            if (phaseTicks >= SWARM + MARK + DIVE) {
                spot.getWorld().spawnParticle(Particle.SMOKE, spot.clone().add(0, 0.5, 0), 40, RADIUS / 2, 0.4, RADIUS / 2, 0.02);
                spot.getWorld().playSound(spot, Sound.ENTITY_BAT_HURT, 2F, 0.5F);
                if (kit.alive()) {
                    for (Player player : kit.playersNear(spot, RADIUS)) {
                        kit.fight.hit(player, BAT_DIVE, kit.body);
                    }
                }
                end();
            }
        }

        private void end() {
            bats.forEach(Entity::remove);
            bats.clear();
            phaseTicks = -1;
            diving = false;
        }
    }

    /** Jenn's foxes: dart in, bite, dart out. */
    static final class Foxes extends Signature {

        private static final int MAX = 3;
        private static final int RETREAT = 30;
        private final Map<Fox, Integer> foxes = new HashMap<>();
        private int age;

        Foxes(StaffKit kit) {
            super(kit, 80);
        }

        @Override
        boolean cast(int now) {
            foxes.keySet().removeIf(f -> !f.isValid() || f.isDead());
            if (kit.target == null || foxes.size() >= MAX) {
                next = now + 40;
                return false;
            }
            next = now + 220;
            kit.claim(10);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_FOX_AMBIENT, 1.5F, 1.2F);
            for (int i = 0; i < 2 && foxes.size() < MAX; i++) {
                Fox fox = kit.fight.spawnAdd(Fox.class, kit.body.getLocation().add(i == 0 ? 1 : -1, 0.1, 0.5), f -> {
                    f.setFoxType(Fox.Type.RED);
                    BossFight.setAttribute(f, Attribute.MAX_HEALTH, 10);
                    f.setHealth(10);
                });
                if (fox == null) {
                    break;
                }
                Abyss.puppet(fox);
                fox.setGravity(true);
                foxes.put(fox, 0);
            }
            return true;
        }

        @Override
        void move() {
            age++;
            foxes.keySet().removeIf(f -> !f.isValid() || f.isDead());
            for (Map.Entry<Fox, Integer> entry : foxes.entrySet()) {
                Fox fox = entry.getKey();
                Player near = kit.fight.nearestPlayer(fox.getLocation());
                if (near == null) {
                    continue;
                }
                if (age < entry.getValue()) {
                    // darting out: away from them
                    Vector away = fox.getLocation().toVector().subtract(near.getLocation().toVector()).setY(0);
                    if (away.lengthSquared() < 0.01) {
                        away = new Vector(1, 0, 0);
                    }
                    Abyss.walk(fox, fox.getLocation().add(away.normalize().multiply(6)), 0.4, 0.5);
                    continue;
                }
                Abyss.walk(fox, near.getLocation(), 0.45, 0.6);
                if (fox.getLocation().distanceSquared(near.getLocation()) <= 1.7) {
                    kit.fight.hit(near, FOX_BITE, fox);
                    fox.getWorld().playSound(fox.getLocation(), Sound.ENTITY_FOX_BITE, 1F, 1F);
                    entry.setValue(age + RETREAT);
                }
            }
        }
    }

    /** Griffon on horseback. */
    static final class Mount extends Signature {

        private static final int WARNING = 25;
        private static final double LENGTH = 10;
        private static final double SPEED = 0.8;
        private static final double MOUNT_HEALTH = 40;
        @Nullable private Horse horse;
        private Vector charge;
        private int charging;
        private final Set<UUID> hit = new HashSet<>();

        Mount(StaffKit kit) {
            super(kit, 60);
            horse = kit.fight.spawnAdd(Horse.class, kit.body.getLocation(), h -> {
                h.setAdult();
                h.setColor(Horse.Color.WHITE);
                h.setStyle(Horse.Style.WHITE);
                h.getInventory().setSaddle(new ItemStack(Material.SADDLE));
                BossFight.setAttribute(h, Attribute.MAX_HEALTH, MOUNT_HEALTH);
                h.setHealth(MOUNT_HEALTH);
            });
            if (horse != null) {
                Abyss.puppet(horse);
                horse.setGravity(true);
                horse.addPassenger(kit.body);
            }
        }

        private boolean riding() {
            return horse != null && horse.isValid() && !horse.isDead() && horse.getPassengers().contains(kit.body);
        }

        @Override
        boolean cast(int now) {
            if (!riding() || kit.target == null || charging > 0) {
                next = now + 20;
                return false;
            }
            next = now + 140;
            kit.claim(WARNING + 15);
            Location from = horse.getLocation();
            Location to = StaffKit.lane(from, kit.target.getLocation(), LENGTH);
            Vector along = to.toVector().subtract(from.toVector()).setY(0).normalize();
            Color red = Color.fromRGB(230, 60, 40);
            for (int t = 0; t < WARNING; t += 5) {
                kit.later(t, () -> kit.drawLine(from.clone().add(0, 0.15, 0), to.clone().add(0, 0.15, 0), red, 0.4));
            }
            horse.getWorld().playSound(from, Sound.ENTITY_HORSE_ANGRY, 1.5F, 1F);
            kit.later(WARNING, () -> {
                if (riding() && kit.alive()) {
                    charge = along.multiply(SPEED);
                    charging = (int) Math.ceil(LENGTH / SPEED);
                    hit.clear();
                    Abyss.face(horse, to);
                    horse.getWorld().playSound(horse.getLocation(), Sound.ENTITY_HORSE_GALLOP, 2F, 1F);
                }
            });
            return true;
        }

        @Override
        void move() {
            if (!riding()) {
                return;
            }
            if (charging > 0) {
                charging--;
                horse.setVelocity(charge.clone().setY(horse.getVelocity().getY()));
                for (Player player : kit.playersNear(horse.getLocation(), 1.7)) {
                    if (hit.add(player.getUniqueId())) {
                        kit.fight.hit(player, CHARGE, kit.body);
                        StaffKit.knock(player, horse.getLocation(), 1, 0.5);
                    }
                }
                return;
            }
            // the horse carries him: toward his target, or home when too far out
            Location center = kit.fight.center();
            boolean far = horse.getLocation().distanceSquared(center) > Math.pow(kit.fight.radius() - 1, 2);
            Player target = kit.target;
            if (!far && target != null && kit.fighting(target)) {
                Abyss.walk(horse, target.getLocation(), 0.34, 2);
            } else {
                Abyss.walk(horse, center, 0.25, 1);
            }
        }

        @Override
        void onAddDeath(Entity entity, @Nullable Player killer) {
            if (entity.equals(horse)) {
                horse = null;
                kit.fight.broadcast("&f" + kit.member.display() + " &7is thrown from the saddle - &fon foot now!");
                kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_HORSE_DEATH, 1.5F, 1F);
            }
        }
    }
}
