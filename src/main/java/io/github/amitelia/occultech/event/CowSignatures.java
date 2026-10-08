package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Cow;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * pyr0's signatures: he's a black and white cow (Session E4).
 * <ul>
 * <li><b>stampede</b>: a wide lane warns, then he and three cows charge down it.</li>
 * <li><b>moo</b>: a deep moo knocks everyone in a cone in front of him away.</li>
 * <li><b>milk</b>: hurt, he stops to drink milk for 2 s - it heals him unless enough damage interrupts it.</li>
 * <li><b>hay</b>: shadows, then hay bales drop on players (and slow them).</li>
 * </ul>
 */
final class CowSignatures {

    static final String ID = "RAID_PYR0";
    private static final Mechanic STAMPEDE = Mechanic.of(ID, "Stampede", 28, Mechanic.Kind.AREA, true);
    private static final Mechanic MOO = Mechanic.of(ID, "MOO", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic HAY = Mechanic.of(ID, "Hay drop", 24, Mechanic.Kind.AREA, true);
    private static final Color DUST = Color.fromRGB(240, 240, 240);

    private CowSignatures() {}

    /** He and three cows charge down a lane. */
    static final class Stampede extends Signature {

        private static final int WARNING = 30;
        private static final double LENGTH = 12;
        private static final double SPEED = 0.8;
        private static final double WIDTH = 1.6;
        private final List<LivingEntity> herd = new ArrayList<>();
        private final Set<UUID> hit = new HashSet<>();
        private Vector charge;
        private int charging;

        Stampede(StaffKit kit) {
            super(kit, 80);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || charging > 0) {
                next = now + 20;
                return false;
            }
            next = now + 200;
            kit.claim(WARNING + 20);
            Location from = kit.body.getLocation();
            Location to = StaffKit.lane(from, kit.target.getLocation(), LENGTH);
            Vector along = to.toVector().subtract(from.toVector()).setY(0).normalize();
            Vector side = new Vector(-along.getZ(), 0, along.getX());
            if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
                kit.warnLane(from, to, WIDTH * 2 + 1.4, WARNING, DUST);   // one wide lane for the whole herd
            } else {
                for (int t = 0; t < WARNING; t += 5) {
                    kit.later(t, () -> {
                        for (double offset : new double[] { -WIDTH, 0, WIDTH }) {
                            Vector shift = side.clone().multiply(offset);
                            kit.drawLine(from.clone().add(shift).add(0, 0.15, 0), to.clone().add(shift).add(0, 0.15, 0), DUST, 0.5);
                        }
                    });
                }
            }
            for (double offset : new double[] { -1.6, 1.6, 0 }) {
                Location at = from.clone().add(side.clone().multiply(offset)).subtract(along.clone().multiply(offset == 0 ? 1.8 : 0.8));
                Cow cow = kit.fight.spawnAdd(Cow.class, at, c -> {
                    c.setAdult();
                    BossFight.setAttribute(c, Attribute.MAX_HEALTH, 10);
                    c.setHealth(10);
                });
                if (cow != null) {
                    Abyss.puppet(cow);
                    cow.setGravity(true);
                    Abyss.face(cow, to);
                    herd.add(cow);
                }
            }
            from.getWorld().playSound(from, Sound.ENTITY_COW_AMBIENT, 2F, 0.6F);
            kit.later(WARNING, () -> {
                if (kit.alive()) {
                    charge = along.multiply(SPEED);
                    charging = (int) Math.ceil(LENGTH / SPEED);
                    hit.clear();
                    Abyss.face(kit.body, to);
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_RAVAGER_STEP, 2F, 0.8F);
                } else {
                    herd.forEach(LivingEntity::remove);
                    herd.clear();
                }
            });
            return true;
        }

        @Override
        boolean steering() {
            return charging > 0;
        }

        @Override
        void move() {
            if (charging <= 0) {
                return;
            }
            charging--;
            List<LivingEntity> runners = new ArrayList<>(herd);
            runners.add(kit.body);
            for (LivingEntity runner : runners) {
                if (!runner.isValid() || runner.isDead()) {
                    continue;
                }
                runner.setVelocity(charge.clone().setY(runner.getVelocity().getY()));
                runner.getWorld().spawnParticle(Particle.BLOCK, runner.getLocation(), 3, 0.3, 0, 0.3, Material.DIRT.createBlockData());
                for (Player player : kit.playersNear(runner.getLocation(), 1.4)) {
                    if (hit.add(player.getUniqueId())) {
                        kit.fight.hit(player, STAMPEDE, kit.body);
                        StaffKit.knock(player, runner.getLocation(), 0.9, 0.5);
                    }
                }
            }
            if (charging == 0) {
                for (LivingEntity cow : herd) {
                    cow.getWorld().spawnParticle(Particle.POOF, cow.getLocation().add(0, 0.7, 0), 10, 0.3, 0.3, 0.3, 0.02);
                    cow.remove();
                }
                herd.clear();
            }
        }
    }

    /** A deep moo: a knockback cone. */
    static final class Moo extends Signature {

        private static final int WARNING = 15;
        private static final double REACH = 6;
        private static final double HALF_ANGLE = Math.toRadians(35);

        Moo(StaffKit kit) {
            super(kit, 120);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || !kit.within(kit.target, REACH)) {
                next = now + 20;
                return false;
            }
            next = now + 160;
            kit.claim(WARNING + 5);
            Location at = kit.body.getLocation();
            Abyss.face(kit.body, kit.target.getLocation());
            Vector toTarget = kit.target.getLocation().toVector().subtract(at.toVector());
            double aim = Math.atan2(toTarget.getZ(), toTarget.getX());
            at.getWorld().playSound(at, Sound.ENTITY_COW_HURT, 2F, 0.5F);
            Particle.DustOptions dust = new Particle.DustOptions(DUST, 1.3F);
            if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
                io.github.amitelia.occultech.boss.FloorDecals.wedge(kit.fight, at, toTarget, REACH, WARNING, DUST);
            }
            for (int t = 0; t < WARNING && !io.github.amitelia.occultech.boss.FloorDecals.enabled(); t += 5) {
                kit.later(t, () -> {
                    for (double edge : new double[] { aim - HALF_ANGLE, aim + HALF_ANGLE }) {
                        kit.drawLine(at.clone().add(0, 0.15, 0), at.clone().add(Math.cos(edge) * REACH, 0.15, Math.sin(edge) * REACH), DUST, 0.5);
                    }
                    for (double a = aim - HALF_ANGLE; a <= aim + HALF_ANGLE; a += 0.1) {
                        at.getWorld().spawnParticle(Particle.DUST, at.clone().add(Math.cos(a) * REACH, 0.15, Math.sin(a) * REACH), 1, 0, 0, 0, 0, dust);
                    }
                });
            }
            kit.later(WARNING, () -> {
                if (!kit.alive()) {
                    return;
                }
                Location here = kit.body.getLocation();
                here.getWorld().playSound(here, Sound.ENTITY_COW_AMBIENT, 3F, 0.4F);
                here.getWorld().spawnParticle(Particle.SONIC_BOOM, here.clone().add(Math.cos(aim) * 2, 1, Math.sin(aim) * 2), 1, 0, 0, 0, 0);
                for (Player player : kit.playersNear(here, REACH)) {
                    Vector to = player.getLocation().toVector().subtract(here.toVector());
                    if (Math.abs(RaidGeometry.angleBetween(Math.atan2(to.getZ(), to.getX()), aim)) <= HALF_ANGLE) {
                        kit.fight.hit(player, MOO, kit.body);
                        StaffKit.knock(player, here, 1.3, 0.45);
                    }
                }
            });
            return true;
        }
    }

    /** He drinks milk to heal, unless interrupted. */
    static final class Milk extends Signature {

        private static final int DRINK = 40;
        private static final double HURT_BELOW = 0.75;
        private static final double HEAL = 0.12;
        /** Damage that interrupts the drink, as a share of his health. */
        private static final double INTERRUPT = 0.08;
        private int drinking = -1;
        private double taken;
        private ItemStack held;

        Milk(StaffKit kit) {
            super(kit, 200);
        }

        @Override
        boolean cast(int now) {
            double max = kit.body.getAttribute(Attribute.MAX_HEALTH).getValue();
            if (kit.target == null || kit.body.getHealth() / max > HURT_BELOW) {
                next = now + 40;
                return false;
            }
            next = now + 300;
            kit.claim(DRINK + 5);
            drinking = 0;
            taken = 0;
            held = kit.body.getEquipment().getItemInMainHand();
            kit.body.getEquipment().setItemInMainHand(new ItemStack(Material.MILK_BUCKET));
            kit.fight.broadcast("&f" + kit.member.display() + " &7stops for some milk - &finterrupt him!");
            return true;
        }

        @Override
        boolean steering() {
            return drinking >= 0;
        }

        @Override
        void onHitBy(Player player, double damage) {
            if (drinking >= 0) {
                taken += damage;
            }
        }

        @Override
        void move() {
            if (drinking < 0) {
                return;
            }
            if (!kit.alive()) {
                drinking = -1;
                return;
            }
            double max = kit.body.getAttribute(Attribute.MAX_HEALTH).getValue();
            if (taken >= max * INTERRUPT) {
                finish();
                kit.body.getWorld().spawnParticle(Particle.ITEM, kit.body.getLocation().add(0, 1.4, 0), 20, 0.3, 0.2, 0.3, 0.1,
                    new ItemStack(Material.MILK_BUCKET));
                kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_COW_HURT, 1.5F, 1.2F);
                for (Player player : kit.fight.players()) {
                    player.sendActionBar(Component.text(kit.member.display() + " spilled the milk!", NamedTextColor.WHITE));
                }
                return;
            }
            if (drinking % 8 == 0) {
                kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_GENERIC_DRINK, 1F, 0.8F);
            }
            if (++drinking >= DRINK) {
                finish();
                kit.fight.healBoss(kit.body, HEAL);
                kit.body.getActivePotionEffects().forEach(e -> kit.body.removePotionEffect(e.getType()));
                kit.body.getWorld().spawnParticle(Particle.HEART, kit.body.getLocation().add(0, 2, 0), 5, 0.4, 0.2, 0.4, 0);
            }
        }

        private void finish() {
            drinking = -1;
            kit.body.getEquipment().setItemInMainHand(held);
        }
    }

    /** Hay bales drop on players. */
    static final class Hay extends Signature {

        private static final int WARNING = 35;
        private static final int FALL = 12;
        private static final double RADIUS = 1.5;

        Hay(StaffKit kit) {
            super(kit, 160);
        }

        @Override
        boolean cast(int now) {
            List<Player> players = new ArrayList<>(kit.fight.players());
            if (kit.target == null || players.isEmpty()) {
                next = now + 20;
                return false;
            }
            next = now + 180;
            kit.claim(15);
            java.util.Collections.shuffle(players);
            for (Player player : players.subList(0, Math.min(3, players.size()))) {
                Location spot = player.getLocation();
                kit.fight.telegraph(spot, RADIUS, WARNING, Color.fromRGB(200, 170, 50));
                kit.later(WARNING - FALL, () -> {
                    BlockDisplay bale = kit.fight.spawnExtra(BlockDisplay.class, spot.clone().add(0, 14, 0), d -> {
                        d.setBlock(Material.HAY_BLOCK.createBlockData());
                        d.setTransformation(new Transformation(new Vector3f(-0.5F, 0, -0.5F), new AxisAngle4f(), new Vector3f(1, 1, 1),
                            new AxisAngle4f()));
                    });
                    bale.setTeleportDuration(FALL);
                    bale.teleport(spot.clone());
                    kit.later(FALL, () -> {
                        bale.remove();
                        spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.5, 0), 30, 0.6, 0.3, 0.6,
                            Material.HAY_BLOCK.createBlockData());
                        spot.getWorld().playSound(spot, Sound.BLOCK_GRASS_BREAK, 1.5F, 0.6F);
                        if (kit.alive()) {
                            for (Player hitPlayer : kit.playersNear(spot, RADIUS)) {
                                kit.fight.hit(hitPlayer, HAY, kit.body);
                                hitPlayer.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 20, 1));
                            }
                        }
                    });
                });
            }
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_COW_AMBIENT, 1.5F, 1F);
            return true;
        }
    }
}
