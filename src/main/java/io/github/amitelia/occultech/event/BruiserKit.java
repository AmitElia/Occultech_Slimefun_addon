package io.github.amitelia.occultech.event;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Bruiser: slow, heavy melee, can't be knocked around. Generic move: a ground slam - a ring warns for 1.5 s, then
 * everyone inside is hit and thrown back. The counter is to step out of the ring.
 */
final class BruiserKit extends StaffKit {

    static final String ID = "RAID_BRUISER";
    private static final Mechanic BLOW = Mechanic.of(ID, "Heavy blow", 22, Mechanic.Kind.MELEE, false);
    private static final Mechanic SLAM = Mechanic.of(ID, "Ground slam", 30, Mechanic.Kind.AREA, true);
    private static final double SLAM_RADIUS = 4;
    private static final int SLAM_WARNING = 30;
    private static final Color WARNING = Color.fromRGB(220, 90, 40);

    BruiserKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        super(fight, body, member, home);
    }

    @Override
    protected void prepareBody() {
        BossFight.setAttribute(body, Attribute.KNOCKBACK_RESISTANCE, 1);
    }

    @Override
    protected double speed() {
        return 0.22;
    }

    @Override
    protected double keepDistance() {
        return 1.5;
    }

    @Override
    protected Mechanic melee() {
        return BLOW;
    }

    @Override
    protected int meleeCooldown() {
        return 30;
    }

    @Override
    protected boolean special(int now) {
        if (target == null || !within(target, 8)) {
            nextSpecial = now + 20;   // only worth it with someone close
            return false;
        }
        nextSpecial = now + 160;
        Location at = body.getLocation();
        fight.telegraph(at, SLAM_RADIUS, SLAM_WARNING, WARNING);
        body.getWorld().playSound(at, Sound.ENTITY_RAVAGER_ROAR, 1F, 1.3F);
        later(SLAM_WARNING, () -> {
            if (!alive()) {
                return;
            }
            Location center = body.getLocation();
            center.getWorld().spawnParticle(Particle.EXPLOSION, center, 3, 1.5, 0.2, 1.5, 0);
            center.getWorld().spawnParticle(Particle.BLOCK, center, 60, SLAM_RADIUS / 2, 0.1, SLAM_RADIUS / 2, Material.STONE.createBlockData());
            center.getWorld().playSound(center, Sound.ENTITY_GENERIC_EXPLODE, 1F, 0.7F);
            for (Player player : playersNear(center, SLAM_RADIUS)) {
                fight.hit(player, SLAM, body);
                knock(player, center, 0.9, 0.45);
            }
        });
        return true;
    }
}
