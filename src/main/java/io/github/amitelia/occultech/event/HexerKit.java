package io.github.amitelia.occultech.event;

import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

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
 * Hexer: mid range, marks a player. The mark glows over their head for 3 s, then bursts on everyone within 3 blocks of
 * them - the marked player included. The counter is to spread out: the marked player walks away from the others.
 */
final class HexerKit extends StaffKit {

    static final String ID = "RAID_HEXER";
    private static final Mechanic TOUCH = Mechanic.of(ID, "Hex touch", 16, Mechanic.Kind.MELEE, false);
    private static final Mechanic BURST = Mechanic.of(ID, "Hex burst", 9, Mechanic.Kind.MAGIC, true);
    private static final int MARK_TICKS = 60;
    private static final double BURST_RADIUS = 3;
    private static final Color HEX = Color.fromRGB(170, 60, 220);

    HexerKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        super(fight, body, member, home);
    }

    @Override
    protected double speed() {
        return 0.26;
    }

    @Override
    protected double keepDistance() {
        return 7;
    }

    @Override
    protected Mechanic melee() {
        return TOUCH;
    }

    @Override
    protected boolean special(int now) {
        List<Player> players = fight.players();
        if (players.isEmpty()) {
            nextSpecial = now + 20;
            return false;
        }
        nextSpecial = now + 120;
        Player marked = players.get(ThreadLocalRandom.current().nextInt(players.size()));
        body.swingMainHand();
        body.getWorld().playSound(body.getLocation(), Sound.ENTITY_EVOKER_CAST_SPELL, 1F, 1.4F);
        marked.addPotionEffect(new PotionEffect(PotionEffectType.GLOWING, MARK_TICKS, 0, false, false));
        marked.sendActionBar(Component.text("You are hexed - get away from the others!", NamedTextColor.LIGHT_PURPLE));
        for (Signature signature : signatures()) {
            if (signature instanceof TricksterSignatures.Denied denied) {
                denied.mark(marked, MARK_TICKS);
            }
        }
        Particle.DustOptions dust = new Particle.DustOptions(HEX, 1.6F);
        for (int t = 0; t < MARK_TICKS; t += 5) {
            later(t, () -> {
                if (marked.isOnline()) {
                    marked.getWorld().spawnParticle(Particle.DUST, marked.getLocation().add(0, 2.4, 0), 6, 0.25, 0.1, 0.25, 0, dust);
                }
            });
        }
        later(MARK_TICKS, () -> {
            if (!alive() || !fighting(marked)) {
                return;
            }
            Location at = marked.getLocation();
            at.getWorld().spawnParticle(Particle.WITCH, at.clone().add(0, 1, 0), 60, BURST_RADIUS / 2, 0.6, BURST_RADIUS / 2, 0.05);
            at.getWorld().playSound(at, Sound.ENTITY_ZOMBIE_VILLAGER_CURE, 0.8F, 1.8F);
            for (Player player : playersNear(at, BURST_RADIUS)) {
                fight.hit(player, BURST, body);
            }
        });
        return true;
    }
}
