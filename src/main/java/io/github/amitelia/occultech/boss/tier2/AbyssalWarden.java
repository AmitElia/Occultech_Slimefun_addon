package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Guardian;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-2 mini-boss (max netherite). A giant guardian that glides over the land instead of flopping.
 * <ul>
 * <li>Charged beam: tracks a player for 2s and turns white near the end; sprint sideways to dodge. Magic damage
 * (ignores armor, like the vanilla guardian laser).</li>
 * <li>Tail lash: anyone within 3.5 blocks is hit once a second.</li>
 * <li>Spike burst: a ring warns for 1s, then spikes hurt and push everyone close to it.</li>
 * <li>Below half health it charges two beams at once, more often.</li>
 * </ul>
 * Its hide is hard: it takes a third of the damage dealt (health attributes can't go past 1024 with group scaling).
 */
public final class AbyssalWarden extends BossBehavior {

    static final double HEALTH = 300;
    static final double ARMOR = 0.33;
    private static final Color BEAM = Color.fromRGB(90, 230, 210);
    private static final Color SPIKES = Color.fromRGB(230, 170, 60);
    private static final int BEAM_INTERVAL = 120;
    private static final int BEAM_INTERVAL_ENRAGED = 80;
    private static final int SPIKE_INTERVAL = 240;
    private static final io.github.amitelia.occultech.boss.Mechanic BEAM_HIT = io.github.amitelia.occultech.boss.Mechanic.of("ABYSSAL_WARDEN", "Beam", 15.5, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic SPIKE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("ABYSSAL_WARDEN", "Spikes", 30, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic LASH_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("ABYSSAL_WARDEN", "Lash", 23, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final double LASH_RANGE = 3.5;

    private Guardian warden;
    private final List<Abyss.Beam> beams = new ArrayList<>();
    private int nextBeam = 60;
    private int nextLash;
    /** Who it glides after (chosen each step, followed every tick). */
    private Player chase;
    private int spikesAt = -1;
    private boolean enraged;

    public AbyssalWarden(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        warden = fight.spawnBoss(Guardian.class, at.clone().add(0, 2, 0), g -> {
            g.setCustomName(ChatColor.DARK_AQUA + "Abyssal Warden");
            g.setCustomNameVisible(true);
            Abyss.puppet(g);
            BossFight.setAttribute(g, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(g, Attribute.SCALE, 3);
        });
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR;
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public void move() {
        if (!warden.isValid()) {
            return;
        }
        // close enough to lash anyone in melee; beams handle the rest
        if (chase != null && chase.isValid() && chase.getWorld() == warden.getWorld()) {
            Abyss.glide(warden, chase.getLocation(), 0.16, 1.5, 3);
        } else {
            Abyss.glide(warden, fight.center(), 0.1, 1.5, 0);
        }
    }

    @Override
    public void tick() {
        if (!warden.isValid()) {
            return;
        }
        int now = fight.elapsed();
        chase = fight.nearestPlayer(warden.getLocation());

        if (!enraged && fight.healthFraction() < 0.5) {
            enraged = true;
            fight.broadcast("&3The Warden's eye burns brighter - &ftwo beams at once!");
        }

        if (now >= nextBeam) {
            nextBeam = now + (enraged ? BEAM_INTERVAL_ENRAGED : BEAM_INTERVAL);
            List<Player> players = new ArrayList<>(fight.players());
            java.util.Collections.shuffle(players);
            for (int i = 0; i < Math.min(enraged ? 2 : 1, players.size()); i++) {
                beams.add(new Abyss.Beam(warden, players.get(i), now, 40, BEAM_HIT, BEAM));
            }
        }
        beams.forEach(beam -> beam.step(fight, now));
        beams.removeIf(Abyss.Beam::done);

        if (now >= nextLash) {
            for (Player player : fight.players()) {
                if (player.getLocation().add(0, 1, 0).distanceSquared(warden.getLocation().add(0, 1, 0)) <= LASH_RANGE * LASH_RANGE) {
                    fight.hit(player, LASH_DAMAGE, warden);
                    warden.getWorld().playSound(warden.getLocation(), Sound.ENTITY_GUARDIAN_HURT, 1F, 0.5F);
                    nextLash = now + 20;
                }
            }
        }

        if (every(SPIKE_INTERVAL) && spikesAt < 0) {
            spikesAt = now + 20;
            fight.telegraph(ground(warden.getLocation()), 5, 25, SPIKES, FloorDecals.Mark.SPIKES);
            warden.getWorld().playSound(warden.getLocation(), Sound.ENTITY_GUARDIAN_FLOP, 2F, 0.5F);
        }
        if (spikesAt >= 0 && now >= spikesAt) {
            spikesAt = -1;
            spikes();
        }
    }

    private static Location ground(Location at) {
        Location spot = at.clone();
        spot.setY(Abyss.groundY(at));
        return spot;
    }

    private void spikes() {
        Location at = warden.getLocation();
        at.getWorld().playSound(at, Sound.ENCHANT_THORNS_HIT, 2F, 0.6F);
        at.getWorld().spawnParticle(Particle.CRIT, at.clone().add(0, 1, 0), 60, 2.5, 1, 2.5, 0.4);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, ground(at).add(0, 1, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, SPIKES, 5F);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(ground(at)) <= 25) {
                fight.hit(player, SPIKE_DAMAGE, warden);
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.9).setY(0.35));
                }
            }
        }
    }
}
