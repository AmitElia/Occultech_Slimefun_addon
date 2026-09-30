package io.github.amitelia.occultech.boss.tier1;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Phantom;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 mini-boss (diamond gear). A giant phantom that can be summoned any time and never burns, but is stronger at
 * night (+20% damage, dives come faster).
 * <ul>
 * <li>Dive: a dark circle marks a player's spot for 1.5s, then it plunges onto it. The impact hurts anyone inside.</li>
 * <li>After each dive it lies <b>stunned on the ground for 2s</b> - the melee window.</li>
 * <li>Every 20s two small phantoms join (capped).</li>
 * </ul>
 */
public final class NightMatriarch extends BossBehavior {

    private static final Color SHADOW = Color.fromRGB(35, 20, 60);
    private static final int DIVE_INTERVAL_DAY = 160;
    private static final int DIVE_INTERVAL_NIGHT = 120;
    private static final int DIVE_WARNING = 30;
    private static final int DIVE_MAX_TICKS = 40;
    private static final int STUN_TICKS = 40;
    private static final int SWARM_INTERVAL = 400;
    private static final double DAMAGE = 9;

    private Phantom matriarch;
    private Location diveTarget;
    private int diveAt = -1;
    private int diveEnd = -1;
    private int stunnedUntil = -1;
    private int nextDive = 100;
    private boolean night;

    public NightMatriarch(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        matriarch = fight.spawnBoss(Phantom.class, at.clone().add(0, 6, 0), p -> {
            p.setCustomName(ChatColor.DARK_PURPLE + "Night Matriarch");
            p.setCustomNameVisible(true);
            p.setShouldBurnInDay(false);
            BossFight.setAttribute(p, Attribute.MAX_HEALTH, 260);
            BossFight.setAttribute(p, Attribute.ATTACK_DAMAGE, DAMAGE);
            BossFight.setAttribute(p, Attribute.SCALE, 4);
            BossFight.setAttribute(p, Attribute.FOLLOW_RANGE, 40);
        });
        matriarch.setAnchorLocation(anchor());
    }

    /** Phantoms circle an anchor point; keep it above the altar so it never drifts out of the arena. */
    private Location anchor() {
        return fight.center().clone().add(0, 9, 0);
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double verticalLeash() {
        return 20;
    }

    @Override
    public void tick() {
        if (!matriarch.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (matriarch.getAnchorLocation() == null || matriarch.getAnchorLocation().distanceSquared(anchor()) > 1) {
            matriarch.setAnchorLocation(anchor());
        }

        long time = matriarch.getWorld().getTime();
        boolean isNight = time >= 13000 && time <= 23000;
        if (isNight != night) {
            night = isNight;
            BossFight.setAttribute(matriarch, Attribute.ATTACK_DAMAGE, DAMAGE * (night ? 1.2 : 1));
            if (night) {
                fight.broadcast("&5Night falls - the Matriarch grows stronger!");
            }
        }

        if (now < stunnedUntil) {
            matriarch.setVelocity(new Vector());
            matriarch.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, matriarch.getLocation().add(0, 1.5, 0), 2, 0.4, 0.2, 0.4, 0);
            return;
        }
        if (stunnedUntil >= 0 && now >= stunnedUntil) {
            stunnedUntil = -1;
            // unaware = no AI but normal physics, unlike setAI(false), which can freeze a mob in the air
            matriarch.setAware(true);
            matriarch.setGlowing(false);
            matriarch.setVelocity(new Vector(0, 0.8, 0));
        }

        if (every(SWARM_INTERVAL)) {
            for (int i = 0; i < 2; i++) {
                fight.spawnAdd(Phantom.class, fight.randomPoint(3, 8).add(0, 6, 0), p -> {
                    p.setShouldBurnInDay(false);
                    BossFight.setAttribute(p, Attribute.MAX_HEALTH, 12);
                    p.setHealth(12);
                });
            }
        }

        if (now >= nextDive && diveAt < 0 && diveEnd < 0) {
            Player target = fight.randomPlayer();
            nextDive = now + (night ? DIVE_INTERVAL_NIGHT : DIVE_INTERVAL_DAY);
            if (target != null) {
                diveTarget = target.getLocation();
                diveAt = now + DIVE_WARNING;
                fight.telegraph(diveTarget, 3, DIVE_WARNING + 10, SHADOW);
                matriarch.getWorld().playSound(matriarch.getLocation(), Sound.ENTITY_PHANTOM_SWOOP, 2F, 0.6F);
            }
        }
        if (now == diveAt) {
            diveAt = -1;
            diveEnd = now + DIVE_MAX_TICKS;
            matriarch.setAware(false);
            matriarch.setTarget(null);
        }
        if (diveEnd >= 0) {
            Vector to = diveTarget.clone().add(0, 0.5, 0).toVector().subtract(matriarch.getLocation().toVector());
            if (to.length() < 2 || now >= diveEnd) {
                impact();
            } else {
                matriarch.setVelocity(to.normalize().multiply(Math.min(1.6, 0.4 + to.length() * 0.15)));
            }
        }
    }

    /** Top of the ground under a spot, so the stunned Matriarch lies on the floor rather than in the air. */
    private static double groundY(Location at) {
        org.bukkit.block.Block block = at.getBlock();
        for (int i = 0; i < 8 && block.isPassable(); i++) {
            block = block.getRelative(0, -1, 0);
        }
        return block.isPassable() ? at.getY() : block.getY() + 1;
    }

    private void impact() {
        diveEnd = -1;
        Location at = diveTarget.clone();
        at.setY(groundY(at));
        matriarch.teleport(at.clone().add(0, 0.3, 0));
        matriarch.setVelocity(new Vector());
        matriarch.setGlowing(true);
        stunnedUntil = fight.elapsed() + STUN_TICKS;
        at.getWorld().playSound(at, Sound.ENTITY_PHANTOM_BITE, 2F, 0.5F);
        at.getWorld().spawnParticle(Particle.SONIC_BOOM, at.clone().add(0, 0.5, 0), 1);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 9) {
                player.damage(night ? 8.4 : 7, matriarch);
            }
        }
        fight.broadcast("&7The Matriarch is grounded - &fattack!");
    }
}
