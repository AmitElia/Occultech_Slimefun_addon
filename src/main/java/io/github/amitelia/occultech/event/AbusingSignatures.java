package io.github.amitelia.occultech.event;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.papermc.paper.datacomponent.item.ResolvableProfile;

/**
 * Abusing's signatures (his skin is a creeper - Session E3).
 * <ul>
 * <li><b>replicas</b>: small copies of him run at players; next to one they swell and hiss for 1.5 s (a ring warns),
 * then burst. One hit kills a replica, so the counter is to swat them on the way in. At most 6.</li>
 * <li><b>big_fuse</b>: he swells himself inside a wide ring, then blasts everyone near him away. Step out.</li>
 * </ul>
 * The bursts are particles and plugin damage: nothing in the world is affected.
 */
final class AbusingSignatures {

    static final String ID = "RAID_ABUSING";
    private static final Mechanic REPLICA_BLAST = Mechanic.of(ID, "Replica blast", 24, Mechanic.Kind.AREA, true);
    private static final Mechanic BIG_FUSE = Mechanic.of(ID, "Big fuse", 32, Mechanic.Kind.AREA, true);
    private static final Color FUSE = Color.fromRGB(120, 230, 90);

    private AbusingSignatures() {}

    /** Small copies of him that run at players and burst. */
    static final class Replicas extends Signature {

        private static final int MAX = 6;
        private static final double SCALE = 0.5;
        private static final int FUSE_TICKS = 30;
        private static final double BLAST_RADIUS = 3;
        private static final double TRIGGER = 2.2;
        /** Each replica and the tick its fuse was lit (-1: still running). */
        private final Map<Mannequin, Integer> replicas = new HashMap<>();
        private int age;

        Replicas(StaffKit kit) {
            super(kit, 60);
        }

        @Override
        boolean cast(int now) {
            replicas.keySet().removeIf(r -> !r.isValid() || r.isDead());
            if (kit.target == null || replicas.size() >= MAX) {
                next = now + 40;
                return false;
            }
            next = now + 160;
            kit.claim(10);
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_CREEPER_HURT, 1.5F, 1.6F);
            for (int i = 0; i < 2 && replicas.size() < MAX; i++) {
                Location at = kit.body.getLocation().add(i == 0 ? 1 : -1, 0.1, 0.6);
                Mannequin replica = kit.fight.spawnAdd(Mannequin.class, at, m -> {
                    m.setProfile(ResolvableProfile.resolvableProfile().name(kit.member.skin()).build());
                    m.setDescription(net.kyori.adventure.text.Component.empty());
                    BossFight.setAttribute(m, Attribute.SCALE, SCALE);
                    BossFight.setAttribute(m, Attribute.MAX_HEALTH, 1);
                    m.setHealth(1);
                });
                if (replica == null) {
                    break;
                }
                replicas.put(replica, -1);
                at.getWorld().spawnParticle(Particle.POOF, at.clone().add(0, 0.5, 0), 10, 0.2, 0.3, 0.2, 0.02);
            }
            return true;
        }

        @Override
        void move() {
            age++;
            Iterator<Map.Entry<Mannequin, Integer>> it = replicas.entrySet().iterator();
            while (it.hasNext()) {
                Map.Entry<Mannequin, Integer> entry = it.next();
                Mannequin replica = entry.getKey();
                if (!replica.isValid() || replica.isDead()) {
                    it.remove();
                    continue;
                }
                int lit = entry.getValue();
                if (lit < 0) {
                    Player near = kit.fight.nearestPlayer(replica.getLocation());
                    if (near == null) {
                        continue;
                    }
                    Abyss.walk(replica, near.getLocation(), 0.3, 0.8);
                    if (near.getLocation().distanceSquared(replica.getLocation()) <= TRIGGER * TRIGGER) {
                        entry.setValue(age);
                        replica.setVelocity(replica.getVelocity().setX(0).setZ(0));
                        kit.fight.telegraph(replica.getLocation(), BLAST_RADIUS, FUSE_TICKS, FUSE);
                        replica.getWorld().playSound(replica.getLocation(), Sound.ENTITY_CREEPER_PRIMED, 1.2F, 1F);
                    }
                    continue;
                }
                int burning = age - lit;
                // swell and flash while the fuse burns
                BossFight.setAttribute(replica, Attribute.SCALE, SCALE * (1 + 0.25 * burning / FUSE_TICKS + 0.06 * Math.sin(burning)));
                if (burning % 4 == 0) {
                    replica.getWorld().spawnParticle(Particle.WHITE_ASH, replica.getLocation().add(0, 0.5, 0), 8, 0.3, 0.3, 0.3, 0);
                }
                if (burning >= FUSE_TICKS) {
                    Location at = replica.getLocation();
                    at.getWorld().spawnParticle(Particle.EXPLOSION, at, 2, 0.5, 0.3, 0.5, 0);
                    at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 1F, 1.3F);
                    for (Player player : kit.playersNear(at, BLAST_RADIUS)) {
                        kit.fight.hit(player, REPLICA_BLAST, kit.body);
                        StaffKit.knock(player, at, 0.7, 0.4);
                    }
                    replica.remove();
                    it.remove();
                }
            }
        }
    }

    /** He swells inside a wide ring, then blasts everyone near away. */
    static final class BigFuse extends Signature {

        private static final int WARNING = 40;
        private static final double RADIUS = 5;
        private int lit = -1;
        private int age;

        BigFuse(StaffKit kit) {
            super(kit, 140);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null || !kit.within(kit.target, 7)) {
                next = now + 20;
                return false;
            }
            next = now + 220;
            kit.claim(WARNING + 5);
            lit = age;
            Location at = kit.body.getLocation();
            kit.fight.telegraph(at, RADIUS, WARNING, FUSE);
            at.getWorld().playSound(at, Sound.ENTITY_CREEPER_PRIMED, 2F, 0.6F);
            kit.later(WARNING, () -> {
                BossFight.setAttribute(kit.body, Attribute.SCALE, 1);
                lit = -1;
                if (!kit.alive()) {
                    return;
                }
                Location center = kit.body.getLocation();
                center.getWorld().spawnParticle(Particle.EXPLOSION_EMITTER, center, 1, 0, 0, 0, 0);
                center.getWorld().playSound(center, Sound.ENTITY_GENERIC_EXPLODE, 1.5F, 0.6F);
                for (Player player : kit.playersNear(center, RADIUS)) {
                    kit.fight.hit(player, BIG_FUSE, kit.body);
                    StaffKit.knock(player, center, 1.3, 0.6);
                }
            });
            return true;
        }

        @Override
        void move() {
            age++;
            if (lit >= 0 && kit.alive()) {
                int burning = age - lit;
                BossFight.setAttribute(kit.body, Attribute.SCALE, 1 + 0.25 * Math.min(1, burning / (double) WARNING) + 0.05 * Math.sin(burning * 0.8));
                if (burning % 4 == 0) {
                    kit.body.getWorld().spawnParticle(Particle.WHITE_ASH, kit.body.getLocation().add(0, 1, 0), 15, 0.5, 0.6, 0.5, 0);
                }
            }
        }
    }
}
