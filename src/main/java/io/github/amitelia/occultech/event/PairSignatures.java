package io.github.amitelia.occultech.event;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Earl and Sam fight together (a pair shares one slot - Session E4).
 * <ul>
 * <li><b>bond</b>: a tether between them hurts anyone who crosses it, and sweeps as they move.</li>
 * <li><b>together</b>: each takes half damage while they're within 6 blocks of each other - split them up. When one
 * falls, the other enrages (faster) for the rest of the fight.</li>
 * <li><b>rescue</b>: once a fight, when one drops below 30%, the other dashes over and their health evens out.</li>
 * <li><b>daggers</b> (Sam): melee hits poison for 3 s.</li>
 * </ul>
 */
final class PairSignatures {

    static final String ID = "RAID_PAIR";
    private static final Mechanic BOND = Mechanic.of(ID, "Bond", 7, Mechanic.Kind.MAGIC, true);
    private static final Color BOND_COLOR = Color.fromRGB(255, 120, 200);
    static final double TOGETHER = 6;

    private PairSignatures() {}

    private static boolean bothAlive(StaffKit kit) {
        return kit.alive() && kit.partner != null && kit.partner.alive();
    }

    /** The tether. Only the pair's lead (the one who names the partner) runs it, so there's one tether. */
    static final class Bond extends Signature {

        private final Map<UUID, Integer> touched = new HashMap<>();
        private int age;

        Bond(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // passive
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        @Override
        void move() {
            age++;
            if (kit.member.partner() == null || !bothAlive(kit)) {
                return;
            }
            Location a = kit.body.getLocation().add(0, 1, 0);
            Location b = kit.partner.body.getLocation().add(0, 1, 0);
            if (age % 3 == 0) {
                kit.drawLine(a, b, BOND_COLOR, 0.4);
            }
            for (Player player : kit.playersAlong(a, b, 0.8)) {
                Integer last = touched.get(player.getUniqueId());
                if (last == null || age - last >= 20) {
                    touched.put(player.getUniqueId(), age);
                    kit.fight.hit(player, BOND, kit.body);
                }
            }
        }
    }

    /** Half damage together; enraged alone. */
    static final class Together extends Signature {

        private boolean enraged;
        private int age;

        Together(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // passive
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        private boolean close() {
            return bothAlive(kit) && kit.within(kit.partner.body, TOGETHER);
        }

        @Override
        double incoming() {
            return close() ? 0.5 : 1;
        }

        @Override
        double pace() {
            return enraged ? 0.7 : 1;
        }

        @Override
        void move() {
            age++;
            if (!kit.alive() || kit.partner == null) {
                return;
            }
            if (!enraged && !kit.partner.alive()) {
                enraged = true;
                kit.fight.broadcast("&c" + kit.member.display() + " is furious!");
                kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_RAVAGER_ROAR, 1.5F, 1F);
            }
            if (age % 10 == 0) {
                if (enraged) {
                    kit.body.getWorld().spawnParticle(Particle.ANGRY_VILLAGER, kit.body.getLocation().add(0, 2, 0), 2, 0.3, 0.2, 0.3, 0);
                } else if (close()) {
                    kit.body.getWorld().spawnParticle(Particle.HEART, kit.body.getLocation().add(0, 2.1, 0), 1, 0.2, 0.1, 0.2, 0);
                }
            }
        }
    }

    /** Once a fight: the healthier one comes to the rescue. */
    static final class Rescue extends Signature {

        private static final double LOW = 0.3;
        private static final int DASH = 40;
        private static final double SPEED = 0.55;
        private boolean used;
        private int dashing = -1;

        Rescue(StaffKit kit) {
            super(kit, 20);
        }

        private static double fraction(StaffKit kit) {
            return kit.body.getHealth() / kit.body.getAttribute(Attribute.MAX_HEALTH).getValue();
        }

        @Override
        boolean cast(int now) {
            next = now + 10;
            if (used || !bothAlive(kit) || fraction(kit.partner) >= LOW || fraction(kit) <= fraction(kit.partner)) {
                return false;
            }
            used = true;
            for (Signature signature : kit.partner.signatures()) {
                if (signature instanceof Rescue other) {
                    other.used = true;   // once per pair
                }
            }
            next = Integer.MAX_VALUE;
            dashing = 0;
            kit.claim(DASH);
            kit.fight.broadcast("&d" + kit.member.display() + " rushes to " + kit.partner.member.display() + "'s side!");
            return true;
        }

        @Override
        boolean steering() {
            return dashing >= 0;
        }

        @Override
        void move() {
            if (dashing < 0) {
                return;
            }
            if (!bothAlive(kit)) {
                dashing = -1;
                return;
            }
            dashing++;
            Abyss.walk(kit.body, kit.partner.body.getLocation(), SPEED, 1.2);
            if (kit.within(kit.partner.body, 2.5) || dashing >= DASH) {
                dashing = -1;
                double even = (fraction(kit) + fraction(kit.partner)) / 2;
                for (StaffKit each : new StaffKit[] { kit, kit.partner }) {
                    each.body.setHealth(Math.max(1, even * each.body.getAttribute(Attribute.MAX_HEALTH).getValue()));
                    each.body.getWorld().spawnParticle(Particle.HEART, each.body.getLocation().add(0, 2, 0), 6, 0.4, 0.3, 0.4, 0);
                }
                kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 1.5F, 1.4F);
            }
        }
    }

    /** Sam's daggers: poison on melee. */
    static final class Daggers extends Signature {

        Daggers(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // passive
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        @Override
        void onMelee(Player player) {
            player.addPotionEffect(new PotionEffect(PotionEffectType.POISON, 60, 0));
        }
    }
}
