package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Gadgeteer: mid range, beams and traps. A beam's lane warns for 1.5 s and then fires where it was aimed (step off the
 * line). A trap is a marked circle on the floor that snaps on the first player to walk into it (walk around it).
 */
final class GadgeteerKit extends StaffKit {

    static final String ID = "RAID_GADGETEER";
    private static final Mechanic WRENCH = Mechanic.of(ID, "Wrench", 18, Mechanic.Kind.MELEE, false);
    private static final Mechanic BEAM = Mechanic.of(ID, "Beam", 10, Mechanic.Kind.MAGIC, true);
    private static final Mechanic TRAP = Mechanic.of(ID, "Trap", 24, Mechanic.Kind.AREA, true);
    private static final int BEAM_WARNING = 30;
    private static final double BEAM_LENGTH = 16;
    private static final double BEAM_WIDTH = 1.1;
    private static final double TRAP_RADIUS = 1.3;
    private static final int TRAP_TICKS = 200;
    private static final int MAX_TRAPS = 3;
    private static final Color BEAM_COLOR = Color.fromRGB(255, 170, 30);
    private static final Color TRAP_COLOR = Color.fromRGB(240, 220, 60);

    private record Trap(Location at, int until) {}

    private final List<Trap> traps = new ArrayList<>();
    private boolean beamNext = true;

    GadgeteerKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        super(fight, body, member, home);
    }

    @Override
    protected double speed() {
        return 0.24;
    }

    @Override
    protected double keepDistance() {
        return 7;
    }

    @Override
    protected Mechanic melee() {
        return WRENCH;
    }

    @Override
    void tick(int now) {
        super.tick(now);
        traps.removeIf(trap -> now >= trap.until());
        for (Trap trap : List.copyOf(traps)) {
            List<Player> caught = playersNear(trap.at(), TRAP_RADIUS);
            if (!caught.isEmpty()) {
                traps.remove(trap);
                trap.at().getWorld().playSound(trap.at(), Sound.BLOCK_PISTON_EXTEND, 1F, 1.6F);
                trap.at().getWorld().spawnParticle(Particle.CRIT, trap.at().clone().add(0, 0.5, 0), 20, 0.5, 0.3, 0.5, 0.1);
                for (Player player : caught) {
                    fight.hit(player, TRAP, body);
                    player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 1));
                }
            }
        }
    }

    @Override
    protected boolean special(int now) {
        if (target == null) {
            nextSpecial = now + 20;
            return false;
        }
        nextSpecial = now + 100;
        if (beamNext || traps.size() >= MAX_TRAPS) {
            beam();
        } else {
            trap(now);
        }
        beamNext = !beamNext;
        return true;
    }

    private void beam() {
        Location from = body.getEyeLocation();
        Location aim = target.getLocation().add(0, 1, 0);
        Location to = from.clone().add(aim.toVector().subtract(from.toVector()).normalize().multiply(BEAM_LENGTH));
        body.getWorld().playSound(from, Sound.BLOCK_BEACON_ACTIVATE, 1F, 1.8F);
        warnLane(body.getLocation(), StaffKit.lane(body.getLocation(), to, BEAM_LENGTH), BEAM_WIDTH * 2, BEAM_WARNING, BEAM_COLOR);
        io.github.amitelia.occultech.boss.AirEffects.Streak aimLine = io.github.amitelia.occultech.boss.FloorDecals.enabled()
            ? io.github.amitelia.occultech.boss.AirEffects.Streak.create(fight, "air_beam", from, to, BEAM_COLOR, 0.08F) : null;
        later(BEAM_WARNING, () -> {
            if (!alive()) {
                return;
            }
            body.swingMainHand();
            from.getWorld().playSound(from, Sound.ENTITY_GUARDIAN_ATTACK, 1F, 1.5F);
            if (aimLine != null) {
                aimLine.fire(from, to);   // the thin aiming line flashes into the beam
            }
            Particle.DustOptions dust = new Particle.DustOptions(BEAM_COLOR, 2F);
            org.bukkit.util.Vector step = to.toVector().subtract(from.toVector()).normalize().multiply(0.3);
            Location at = from.clone();
            for (double d = 0; d < BEAM_LENGTH; d += 0.3) {
                at.add(step);
                at.getWorld().spawnParticle(Particle.DUST, at, 2, 0.05, 0.05, 0.05, 0, dust);
            }
            for (Player player : playersAlong(from, to, BEAM_WIDTH)) {
                fight.hit(player, BEAM, body);
            }
        });
    }

    private void trap(int now) {
        Location at = target.getLocation().add((Math.random() - 0.5) * 4, 0, (Math.random() - 0.5) * 4);
        at.setY(target.getLocation().getY());
        traps.add(new Trap(at, now + TRAP_TICKS));
        fight.telegraph(at, TRAP_RADIUS, TRAP_TICKS, TRAP_COLOR);
        body.swingMainHand();
        body.getWorld().playSound(at, Sound.BLOCK_TRIPWIRE_ATTACH, 1F, 1F);
    }
}
