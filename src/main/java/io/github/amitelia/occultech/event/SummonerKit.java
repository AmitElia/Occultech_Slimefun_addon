package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Zombie;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Summoner: keeps its distance and calls for help - a few weak helpers (capped) that run at players. The counter is
 * to clear the helpers fast, or ignore them and dive the summoner.
 */
final class SummonerKit extends StaffKit {

    static final String ID = "RAID_SUMMONER";
    private static final Mechanic SWIPE = Mechanic.of(ID, "Swipe", 15, Mechanic.Kind.MELEE, false);
    private static final Mechanic HELPER = Mechanic.of(ID, "Helper", 12, Mechanic.Kind.ADD, false);
    private static final int MAX_HELPERS = 3;
    private static final double HELPER_HEALTH = 20;

    private final List<LivingEntity> helpers = new ArrayList<>();

    SummonerKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        super(fight, body, member, home);
    }

    @Override
    protected double speed() {
        return 0.22;
    }

    @Override
    protected double keepDistance() {
        return 8;
    }

    @Override
    protected Mechanic melee() {
        return SWIPE;
    }

    @Override
    protected boolean special(int now) {
        helpers.removeIf(h -> !h.isValid() || h.isDead());
        if (target == null || helpers.size() >= MAX_HELPERS) {
            nextSpecial = now + 40;
            return false;
        }
        nextSpecial = now + 200;
        body.swingMainHand();
        body.getWorld().playSound(body.getLocation(), Sound.ENTITY_EVOKER_PREPARE_SUMMON, 1F, 1.3F);
        for (int i = 0; i < 2 && helpers.size() < MAX_HELPERS; i++) {
            Location at = body.getLocation().add((i == 0 ? 1.2 : -1.2), 0.1, 0.8);
            Zombie helper = fight.spawnAdd(Zombie.class, at, z -> {
                z.setAdult();
                z.setCustomName(ChatColor.GRAY + member.display() + "'s helper");
                z.setCustomNameVisible(false);
                BossFight.setAttribute(z, Attribute.MAX_HEALTH, HELPER_HEALTH);
                z.setHealth(HELPER_HEALTH);
                z.setTarget(target);
            });
            if (helper == null) {
                break;   // the fight's cap on extra mobs
            }
            fight.label(helper, HELPER);
            helpers.add(helper);
            at.getWorld().spawnParticle(Particle.POOF, at.clone().add(0, 1, 0), 12, 0.3, 0.5, 0.3, 0.02);
        }
        return true;
    }
}
