package io.github.amitelia.occultech.event;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.entity.Pose;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * goob's signature, <b>flight</b> (goob's skin is the Duolingo owl - Session E10): goob flies like a bird, lying flat in
 * the swimming pose, circling above the fight out of melee reach. Now and then a landing circle warns under a player,
 * goob dives on it like a bird of prey and strikes there, then stays low for a moment - the window to hit back - before
 * climbing again.
 */
final class OwlSignature extends Signature {

    static final String ID = "RAID_GOOB";
    private static final Mechanic DIVE = Mechanic.of(ID, "Talon dive", 28, Mechanic.Kind.AREA, true);
    private static final double HOVER = 5;
    private static final double ORBIT = 6;
    private static final int MARK = 25;
    private static final int DIVE_TICKS = 25;
    private static final int PERCH = 40;
    private static final double RADIUS = 2.5;
    private static final Color WARNING = Color.fromRGB(120, 200, 70);

    private enum Phase { CIRCLE, MARK, DIVE, PERCH }

    private Phase phase = Phase.CIRCLE;
    private int ticks;
    private double orbit = Math.random() * Math.PI * 2;
    @Nullable private Location spot;

    OwlSignature(StaffKit kit) {
        super(kit, 60);
        kit.body.setGravity(false);
        kit.body.setPose(Pose.SWIMMING, true);
    }

    @Override
    boolean steering() {
        return true;   // goob flies: the kit neither walks nor swings
    }

    @Override
    boolean cast(int now) {
        Player target = kit.target;
        if (target == null || phase != Phase.CIRCLE) {
            next = now + 20;
            return false;
        }
        next = now + 130;
        kit.claim(MARK + DIVE_TICKS + PERCH);
        spot = target.getLocation();
        spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
        kit.fight.telegraph(spot, RADIUS, MARK + 10, WARNING, FloorDecals.Mark.DIVE);
        kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PARROT_IMITATE_PHANTOM, 2F, 0.8F);
        phase = Phase.MARK;
        ticks = 0;
        return true;
    }

    @Override
    void move() {
        if (!kit.alive()) {
            return;
        }
        ticks++;
        switch (phase) {
            case CIRCLE, MARK -> {
                // circle above whoever it hunts (or its spot), lying flat, facing where it flies
                Location over = kit.target != null && kit.fighting(kit.target) ? kit.target.getLocation() : kit.home;
                orbit += 0.04;
                Location point = over.clone().add(Math.cos(orbit) * ORBIT, 0, Math.sin(orbit) * ORBIT);
                Abyss.glide(kit.body, point, 0.32, HOVER, 0.3);
                if (phase == Phase.MARK && ticks >= MARK) {
                    phase = Phase.DIVE;
                    ticks = 0;
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PHANTOM_SWOOP, 2F, 1.2F);
                }
            }
            case DIVE -> {
                Vector to = spot.toVector().add(new Vector(0, 0.3, 0)).subtract(kit.body.getLocation().toVector());
                Abyss.face(kit.body, spot);
                if (to.lengthSquared() < 1.2 || ticks >= DIVE_TICKS) {
                    strike();
                    phase = Phase.PERCH;
                    ticks = 0;
                } else {
                    kit.body.setVelocity(to.normalize().multiply(Math.min(1.3, to.length())));
                }
            }
            case PERCH -> {
                kit.body.setVelocity(new Vector());
                if (ticks >= PERCH) {
                    phase = Phase.CIRCLE;
                    ticks = 0;
                }
            }
        }
    }

    private void strike() {
        kit.body.setVelocity(new Vector());
        spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.2, 0), 30, 1.2, 0.2, 1.2, Material.WHITE_WOOL.createBlockData());
        spot.getWorld().playSound(spot, Sound.ENTITY_PLAYER_ATTACK_KNOCKBACK, 1.5F, 0.8F);
        for (Player player : kit.playersNear(spot, RADIUS)) {
            kit.fight.hit(player, DIVE, kit.body);
            StaffKit.knock(player, spot, 0.8, 0.4);
        }
    }
}
