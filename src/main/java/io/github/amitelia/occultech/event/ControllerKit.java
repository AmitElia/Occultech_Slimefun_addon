package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Sound;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Controller: keeps mid range and takes ground away. Generic move: zone denial - patches under up to two players warn
 * for 1.5 s, then hurt every second for 5 s. The counter is to keep moving.
 */
final class ControllerKit extends StaffKit {

    static final String ID = "RAID_CONTROLLER";
    private static final Mechanic SHOVE = Mechanic.of(ID, "Shove", 18, Mechanic.Kind.MELEE, false);
    private static final Mechanic DENIED = Mechanic.of(ID, "Denied ground", 9, Mechanic.Kind.ZONE, true);
    private static final double ZONE_RADIUS = 2.5;
    private static final int ZONE_WARNING = 30;
    private static final int ZONE_TICKS = 100;
    private static final Color COLOR = Color.fromRGB(70, 140, 230);

    ControllerKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        super(fight, body, member, home);
    }

    @Override
    protected double speed() {
        return 0.24;
    }

    @Override
    protected double keepDistance() {
        return 6;
    }

    @Override
    protected Mechanic melee() {
        return SHOVE;
    }

    @Override
    protected int meleeCooldown() {
        return 25;
    }

    @Override
    protected void onMeleeHit(int now) {
        if (target != null) {
            knock(target, body.getLocation(), 0.8, 0.3);   // a shove: back to mid range
        }
    }

    @Override
    protected boolean special(int now) {
        List<Player> players = new ArrayList<>(fight.players());
        if (players.isEmpty()) {
            nextSpecial = now + 20;
            return false;
        }
        nextSpecial = now + 120;
        Collections.shuffle(players);
        body.swingMainHand();
        body.getWorld().playSound(body.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 1F, 1.6F);
        for (Player player : players.subList(0, Math.min(2, players.size()))) {
            Location at = player.getLocation();
            fight.telegraph(at, ZONE_RADIUS, ZONE_WARNING, COLOR);
            later(ZONE_WARNING, () -> {
                if (alive()) {
                    fight.addHazard(at, ZONE_RADIUS, ZONE_TICKS, COLOR, io.github.amitelia.occultech.boss.FloorDecals.Zone.FROST, p -> fight.hit(p, DENIED, body));
                }
            });
        }
        return true;
    }
}
