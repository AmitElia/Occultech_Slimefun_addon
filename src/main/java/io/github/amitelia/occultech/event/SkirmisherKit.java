package io.github.amitelia.occultech.event;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Skirmisher: fast, hits and backs off. Generic move: a dash - a red lane through its target warns for 1.25 s, then it
 * dashes down it, hitting everyone in the lane once. The counter is to step off the lane.
 */
final class SkirmisherKit extends StaffKit {

    static final String ID = "RAID_SKIRMISHER";
    private static final Mechanic CUT = Mechanic.of(ID, "Quick cut", 16, Mechanic.Kind.MELEE, false);
    private static final Mechanic DASH = Mechanic.of(ID, "Dash", 26, Mechanic.Kind.AREA, true);
    private static final int DASH_WARNING = 25;
    private static final double DASH_LENGTH = 10;
    private static final double DASH_SPEED = 0.9;
    private static final double DASH_WIDTH = 1.3;
    private static final int RETREAT_TICKS = 20;
    private static final Color LANE = Color.fromRGB(230, 40, 40);

    private int retreatUntil;
    private Vector dash;
    private int dashTicks;
    private final Set<UUID> dashHit = new HashSet<>();

    SkirmisherKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        super(fight, body, member, home);
    }

    @Override
    protected double speed() {
        return 0.34;
    }

    @Override
    protected double keepDistance() {
        return fight.elapsed() < retreatUntil ? 7 : 1.5;
    }

    @Override
    protected Mechanic melee() {
        return CUT;
    }

    @Override
    protected int meleeCooldown() {
        return 15;
    }

    @Override
    protected void onMeleeHit(int now) {
        retreatUntil = now + RETREAT_TICKS;
    }

    @Override
    void move() {
        if (dashTicks <= 0) {
            super.move();
            return;
        }
        dashTicks--;
        body.setVelocity(dash.clone().setY(body.getVelocity().getY()));
        body.getWorld().spawnParticle(Particle.SWEEP_ATTACK, body.getLocation().add(0, 1, 0), 1, 0, 0, 0, 0);
        for (Player player : playersNear(body.getLocation(), DASH_WIDTH)) {
            if (dashHit.add(player.getUniqueId())) {
                fight.hit(player, DASH, body);
                knock(player, body.getLocation(), 0.6, 0.35);
            }
        }
    }

    @Override
    protected boolean special(int now) {
        if (target == null || dashTicks > 0 || body.isInsideVehicle()) {   // mounted, the mount charges instead
            nextSpecial = now + 20;
            return false;
        }
        nextSpecial = now + 140;
        Location from = body.getLocation();
        Location to = lane(from, target.getLocation(), DASH_LENGTH);
        Vector direction = to.toVector().subtract(from.toVector()).setY(0).normalize();
        body.getWorld().playSound(from, Sound.ITEM_TRIDENT_RIPTIDE_1, 1F, 1.4F);
        for (int t = 0; t <= DASH_WARNING; t += 5) {
            later(t, () -> drawLine(from.clone().add(0, 0.15, 0), to.clone().add(0, 0.15, 0), LANE, 0.4));
        }
        later(DASH_WARNING, () -> {
            if (!alive()) {
                return;
            }
            Abyss.face(body, to);
            dash = direction.multiply(DASH_SPEED);
            dashTicks = (int) Math.ceil(DASH_LENGTH / DASH_SPEED);
            dashHit.clear();
            body.getWorld().playSound(body.getLocation(), Sound.ENTITY_PLAYER_ATTACK_SWEEP, 1F, 0.8F);
        });
        return true;
    }
}
