package io.github.amitelia.occultech.event;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Endermite;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Player;
import org.bukkit.entity.Silverfish;
import org.bukkit.entity.TextDisplay;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * The developers' signatures (MrTroxy, Dj - Session E3).
 * <ul>
 * <li><b>hotfix</b>: takes turns between a HOTFIX beam (a lane warns, then the word fires down it), a HOTFIX stamp (the
 * word appears on the floor in a ring, then it lands) and a HOTFIX sweep (a fan warns, then a beam of the word swings
 * through it).</li>
 * <li><b>system_bug</b>: glowing endermites and silverfish named SYSTEM BUG (at most 4 per dev, a hit or two each).</li>
 * <li><b>rollback</b>: the spot where each nearby player stood 4 seconds ago is marked, then breaks. Keep moving.</li>
 * </ul>
 */
final class DevSignatures {

    static final String ID = "RAID_DEV";
    private static final Mechanic BEAM = Mechanic.of(ID, "HOTFIX beam", 10, Mechanic.Kind.MAGIC, true);
    private static final Mechanic STAMP = Mechanic.of(ID, "HOTFIX stamp", 26, Mechanic.Kind.AREA, true);
    private static final Mechanic SWEEP = Mechanic.of(ID, "HOTFIX sweep", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic BUG = Mechanic.of(ID, "SYSTEM BUG", 10, Mechanic.Kind.ADD, false);
    private static final Mechanic ROLLBACK = Mechanic.of(ID, "Rollback", 8, Mechanic.Kind.MAGIC, true);
    private static final Color HOTFIX = Color.fromRGB(255, 80, 40);
    private static final Color ROLLBACK_COLOR = Color.fromRGB(90, 200, 255);

    private DevSignatures() {}

    /** HOTFIX: beam, stamp, sweep in turn. */
    static final class Hotfix extends Signature {

        private static final int WARNING = 30;
        private static final double LANE_LENGTH = 14;
        private static final double STAMP_RADIUS = 3;
        private static final double SWEEP_LENGTH = 9;
        private static final double SWEEP_ARC = Math.toRadians(150);
        private static final int SWEEP_TICKS = 30;

        private int turn;
        // the sweep under way
        private final List<TextDisplay> sweep = new ArrayList<>();
        private final Set<UUID> sweepHit = new HashSet<>();
        private double sweepFrom;
        private int sweepTick = -1;

        Hotfix(StaffKit kit) {
            super(kit, 60);
        }

        @Override
        boolean cast(int now) {
            Player target = kit.target;
            if (target == null || sweepTick >= 0) {
                next = now + 20;
                return false;
            }
            switch (turn++ % 3) {
                case 0 -> beam(target);
                case 1 -> stamp(target);
                default -> sweep(target);
            }
            next = now + 100;
            return true;
        }

        private void beam(Player target) {
            Location from = kit.body.getLocation().add(0, 1.1, 0);
            Location to = from.clone().add(target.getLocation().add(0, 1.1, 0).toVector().subtract(from.toVector()).normalize().multiply(LANE_LENGTH));
            kit.claim(WARNING + 5);
            kit.body.getWorld().playSound(from, Sound.BLOCK_NOTE_BLOCK_BIT, 1.5F, 0.6F);
            kit.warnLane(kit.body.getLocation(), StaffKit.lane(kit.body.getLocation(), to, LANE_LENGTH), 2.4, WARNING, HOTFIX);
            kit.later(WARNING, () -> {
                if (!kit.alive()) {
                    return;
                }
                kit.body.swingMainHand();
                from.getWorld().playSound(from, Sound.BLOCK_BEACON_DEACTIVATE, 1.5F, 1.8F);
                List<TextDisplay> words = new ArrayList<>();
                Vector step = to.toVector().subtract(from.toVector()).normalize().multiply(2);
                Location at = from.clone();
                for (double d = 1; d < LANE_LENGTH; d += 2) {
                    at.add(step);
                    words.add(text(at, "HOTFIX", HOTFIX, 1.6F, false));
                }
                for (Player player : kit.playersAlong(from, to, 1.2)) {
                    kit.fight.hit(player, BEAM, kit.body);
                }
                kit.later(12, () -> words.forEach(TextDisplay::remove));
            });
        }

        private void stamp(Player target) {
            Location at = target.getLocation();
            kit.claim(WARNING + 5);
            kit.fight.telegraph(at, STAMP_RADIUS, WARNING, HOTFIX);
            TextDisplay word = text(at.clone().add(0, 0.05, 0), "HOTFIX", HOTFIX, 3F, true);
            at.getWorld().playSound(at, Sound.BLOCK_NOTE_BLOCK_BIT, 1.5F, 1.2F);
            kit.later(WARNING, () -> {
                at.getWorld().spawnParticle(Particle.EXPLOSION, at, 2, 1, 0.1, 1, 0);
                at.getWorld().playSound(at, Sound.BLOCK_ANVIL_LAND, 1F, 0.8F);
                if (kit.alive()) {
                    for (Player player : kit.playersNear(at, STAMP_RADIUS)) {
                        kit.fight.hit(player, STAMP, kit.body);
                    }
                }
                kit.later(10, word::remove);
            });
        }

        private void sweep(Player target) {
            Location center = kit.body.getLocation();
            Vector toTarget = target.getLocation().toVector().subtract(center.toVector());
            double aim = Math.atan2(toTarget.getZ(), toTarget.getX());
            sweepFrom = aim - SWEEP_ARC / 2;
            kit.claim(WARNING + SWEEP_TICKS);
            kit.body.getWorld().playSound(center, Sound.BLOCK_NOTE_BLOCK_BIT, 1.5F, 0.9F);
            // the fan it will swing through: its two edges and its rim
            for (int t = 0; t < WARNING; t += 5) {
                kit.later(t, () -> {
                    Location base = kit.body.getLocation().add(0, 0.15, 0);
                    kit.drawLine(base, point(base, sweepFrom, SWEEP_LENGTH), HOTFIX, 0.6);
                    kit.drawLine(base, point(base, sweepFrom + SWEEP_ARC, SWEEP_LENGTH), HOTFIX, 0.6);
                    for (double a = sweepFrom; a <= sweepFrom + SWEEP_ARC; a += 0.08) {
                        Location rim = point(base, a, SWEEP_LENGTH);
                        rim.getWorld().spawnParticle(Particle.DUST, rim, 1, 0, 0, 0, 0, new Particle.DustOptions(HOTFIX, 1.3F));
                    }
                });
            }
            kit.later(WARNING, () -> {
                if (!kit.alive()) {
                    return;
                }
                sweepHit.clear();
                Location base = kit.body.getLocation().add(0, 1.1, 0);
                for (double d = 1.8; d <= SWEEP_LENGTH; d += 1.8) {
                    TextDisplay word = text(point(base, sweepFrom, d), "HOTFIX", HOTFIX, 1.4F, false);
                    word.setTeleportDuration(1);
                    sweep.add(word);
                }
                sweepTick = 0;
                kit.body.getWorld().playSound(base, Sound.ENTITY_PLAYER_ATTACK_SWEEP, 1.5F, 0.6F);
            });
        }

        @Override
        void move() {
            if (sweepTick < 0) {
                return;
            }
            if (!kit.alive() || sweepTick > SWEEP_TICKS) {
                sweep.forEach(TextDisplay::remove);
                sweep.clear();
                sweepTick = -1;
                return;
            }
            double angle = sweepFrom + SWEEP_ARC * sweepTick / SWEEP_TICKS;
            Location base = kit.body.getLocation().add(0, 1.1, 0);
            for (int i = 0; i < sweep.size(); i++) {
                sweep.get(i).teleport(point(base, angle, 1.8 * (i + 1)));
            }
            for (Player player : kit.playersAlong(base, point(base, angle, SWEEP_LENGTH), 1.1)) {
                if (sweepHit.add(player.getUniqueId())) {
                    kit.fight.hit(player, SWEEP, kit.body);
                }
            }
            sweepTick++;
        }

        private static Location point(Location base, double angle, double distance) {
            return base.clone().add(Math.cos(angle) * distance, 0, Math.sin(angle) * distance);
        }
    }

    /** SYSTEM BUG: glowing endermites and silverfish. */
    static final class SystemBug extends Signature {

        private static final int MAX_BUGS = 4;
        private static final double BUG_HEALTH = 6;
        private final List<LivingEntity> bugs = new ArrayList<>();
        private boolean silverfish;

        SystemBug(StaffKit kit) {
            super(kit, 80);
        }

        @Override
        boolean cast(int now) {
            bugs.removeIf(b -> !b.isValid() || b.isDead());
            if (kit.target == null || bugs.size() >= MAX_BUGS) {
                next = now + 40;
                return false;
            }
            next = now + 240;
            kit.claim(10);
            kit.body.swingMainHand();
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_NOTE_BLOCK_DIDGERIDOO, 1.5F, 0.5F);
            for (int i = 0; i < 2 && bugs.size() < MAX_BUGS; i++) {
                Location at = kit.body.getLocation().add(i == 0 ? 1 : -1, 0.1, 1);
                Class<? extends Mob> type = (silverfish = !silverfish) ? Silverfish.class : Endermite.class;
                Mob bug = kit.fight.spawnAdd(type, at, b -> {
                    b.setCustomName(ChatColor.RED + "" + ChatColor.BOLD + "SYSTEM BUG");
                    b.setCustomNameVisible(true);
                    b.setGlowing(true);
                    BossFight.setAttribute(b, Attribute.MAX_HEALTH, BUG_HEALTH);
                    b.setHealth(BUG_HEALTH);
                    b.setTarget(kit.target);
                });
                if (bug == null) {
                    break;
                }
                kit.fight.label(bug, BUG);
                bugs.add(bug);
                at.getWorld().spawnParticle(Particle.ELECTRIC_SPARK, at.clone().add(0, 0.3, 0), 15, 0.3, 0.2, 0.3, 0.05);
            }
            return true;
        }
    }

    /** Rollback: where you stood 4 seconds ago breaks. */
    static final class Rollback extends Signature {

        /** Samples every 5 ticks: 17 of them span 4 seconds. */
        private static final int SAMPLES = 17;
        private static final int WARNING = 25;
        private static final double RADIUS = 1.8;
        private final Map<UUID, Deque<Location>> trail = new HashMap<>();
        private int age;

        Rollback(StaffKit kit) {
            super(kit, 120);
        }

        @Override
        void move() {
            if (age++ % 5 != 0) {
                return;
            }
            Set<UUID> here = new HashSet<>();
            for (Player player : kit.fight.players()) {
                here.add(player.getUniqueId());
                Deque<Location> steps = trail.computeIfAbsent(player.getUniqueId(), id -> new ArrayDeque<>());
                steps.addLast(player.getLocation());
                while (steps.size() > SAMPLES) {
                    steps.removeFirst();
                }
            }
            trail.keySet().retainAll(here);
        }

        @Override
        boolean cast(int now) {
            List<Location> spots = new ArrayList<>();
            for (Player player : kit.fight.players()) {
                Deque<Location> steps = trail.get(player.getUniqueId());
                if (steps != null && steps.size() >= SAMPLES && kit.within(player, 14)) {
                    spots.add(steps.peekFirst());
                    player.sendActionBar(Component.text("Rolling back 4 seconds... don't go back where you were!", NamedTextColor.AQUA));
                }
            }
            if (spots.isEmpty()) {
                next = now + 40;
                return false;
            }
            next = now + 200;
            kit.claim(WARNING);
            kit.body.swingMainHand();
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 1.5F, 0.5F);
            for (Location spot : spots) {
                kit.fight.telegraph(spot, RADIUS, WARNING, ROLLBACK_COLOR);
                TextDisplay word = text(spot.clone().add(0, 0.05, 0), "ROLLBACK", ROLLBACK_COLOR, 1.2F, true);
                kit.later(WARNING, () -> {
                    word.remove();
                    spot.getWorld().spawnParticle(Particle.REVERSE_PORTAL, spot.clone().add(0, 0.6, 0), 40, 0.6, 0.4, 0.6, 0.05);
                    spot.getWorld().playSound(spot, Sound.BLOCK_GLASS_BREAK, 1F, 0.7F);
                    if (kit.alive()) {
                        for (Player player : kit.playersNear(spot, RADIUS)) {
                            kit.fight.hit(player, ROLLBACK, kit.body);
                        }
                    }
                });
            }
            return true;
        }
    }
}
