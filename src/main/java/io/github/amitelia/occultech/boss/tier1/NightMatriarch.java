package io.github.amitelia.occultech.boss.tier1;

import io.github.amitelia.occultech.boss.FloorDecals;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Phantom;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 mini-boss (diamond gear). A giant phantom that can be summoned any time and never burns, but is stronger at
 * night (+20% damage, dives come faster).
 * <ul>
 * <li>Dive: a dark circle marks a player's spot for 1.5s, then it plunges onto it. The impact hurts anyone inside. A
 * dive that can't reach its mark (blocked, or out of time) is abandoned: she pulls up, nothing is hit.</li>
 * <li>After each dive it lies <b>stunned on the ground for 1.5s</b> - the melee window.</li>
 * <li>Every 12s small phantoms join (capped).</li>
 * <li>Her rake: when she sweeps close to a player she lunges, and the bite lands 6 ticks later on whoever is still in
 * reach.</li>
 * </ul>
 * With the Mythic body she is the sculk-infested phantom queen (docs/art/bosses/night_matriarch): the clips are timed
 * to these moments, and the sculk's glow shows day or night, flares for the dive's tell and gutters while she's
 * stunned. Without Mythic the fight plays as before on a scale-4 phantom.
 */
public final class NightMatriarch extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic DIVE = io.github.amitelia.occultech.boss.Mechanic.of("NIGHT_MATRIARCH", "Dive", 23, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic SWARM = io.github.amitelia.occultech.boss.Mechanic.of("NIGHT_MATRIARCH", "Phantom bite", 9, io.github.amitelia.occultech.boss.Mechanic.Kind.ADD, false);

    private static final Color SHADOW = Color.fromRGB(35, 20, 60);
    private static final int DIVE_INTERVAL_DAY = 100;
    private static final int DIVE_INTERVAL_NIGHT = 80;
    private static final int DIVE_WARNING = 30;
    private static final int DIVE_MAX_TICKS = 40;
    /** A dive that stops closing on its mark (something in the way) for this many ticks is abandoned. */
    private static final int DIVE_STALL_TICKS = 6;
    private static final int STUN_TICKS = 30;
    private static final int SWARM_INTERVAL = 240;
    /** Reach and pace of its rake: a bite whenever it sweeps past a player, at most once a second. */
    private static final double RAKE_REACH = 5;   // reach from her middle: she is a scale-4 phantom, or a 12-block model
    private static final int RAKE_COOLDOWN = 20;
    /** The rake's wind-up: the lunge shows for this long before the bite lands (the bite clip's contact is 0.3s). */
    private static final int BITE_LEAD = 6;
    private static final io.github.amitelia.occultech.boss.Mechanic BITE = io.github.amitelia.occultech.boss.Mechanic.of("NIGHT_MATRIARCH", "Bite", 17.5, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);

    private Phantom matriarch;
    private Location diveTarget;
    private int diveAt = -1;
    private int diveEnd = -1;
    private int stunnedUntil = -1;
    private int nextDive = 100;
    private int nextRake;
    private int biteAt = -1;
    private double diveDistance;
    private int diveStalled;
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
            BossFight.setAttribute(p, Attribute.MAX_HEALTH, 380);
            fight.label(p, BITE);
            BossFight.setAttribute(p, Attribute.FOLLOW_RANGE, 40);
        });
        if (mythic()) {
            // the model draws her at full size: the carrier stays unscaled under it
            act(isNight() ? "STATE_NIGHT" : "STATE_DAY", null);
        } else {
            BossFight.setAttribute(matriarch, Attribute.SCALE, 4);
        }
        matriarch.setAnchorLocation(anchor());
    }

    private boolean mythic() {
        return fight.usesMythicBody();
    }

    private void act(String action, @Nullable Entity target) {
        if (mythic()) {
            fight.playAction(matriarch, action, target);
        }
    }

    private boolean isNight() {
        long time = matriarch.getWorld().getTime();
        return time >= 13000 && time <= 23000;
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
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (fight.elapsed() >= stunnedUntil && diveEnd < 0 && diveAt < 0) {
            act("FLINCH", null);
        }
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

        boolean isNight = isNight();
        if (isNight != night) {
            night = isNight;
            BossFight.setAttribute(matriarch, Attribute.ATTACK_DAMAGE, BITE.damage() * (night ? 1.2 : 1));
            if (night) {
                fight.broadcast("&5Night falls - the Matriarch grows stronger!");
            }
            if (now >= stunnedUntil && diveAt < 0) {
                act(night ? "STATE_NIGHT" : "STATE_DAY", null);
            }
        }

        if (now < stunnedUntil) {
            if (!mythic()) {
                matriarch.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, matriarch.getLocation().add(0, 1.5, 0), 2, 0.4, 0.2, 0.4, 0);
            }
            return;
        }
        if (stunnedUntil >= 0 && now >= stunnedUntil) {
            stunnedUntil = -1;
            // unaware = no AI but normal physics, unlike setAI(false), which can freeze a mob in the air
            matriarch.setAware(true);
            matriarch.setGlowing(false);
            matriarch.setVelocity(new Vector(0, 0.8, 0));
            act("TAKEOFF", null);
            act(night ? "STATE_NIGHT" : "STATE_DAY", null);
        }
        if (mythic()) {
            // the sculk on her sheds sparks as she flies, more at night
            matriarch.getWorld().spawnParticle(Particle.SCULK_CHARGE_POP, matriarch.getLocation().add(0, 1, 0), night ? 4 : 2,
                1.8, 0.4, 1.8, 0.01);
        }

        rake(now);

        if (every(SWARM_INTERVAL)) {
            act("CALL", null);
            for (int i = 0; i < Math.min(4, 1 + fight.playersAtStart()); i++) {
                fight.spawnAdd(Phantom.class, fight.randomPoint(3, 8).add(0, 6, 0), p -> {
                    p.setShouldBurnInDay(false);
                    BossFight.setAttribute(p, Attribute.MAX_HEALTH, 12);
                    p.setHealth(12);
                    fight.label(p, SWARM);
                });
            }
        }

        if (now >= nextDive && diveAt < 0 && diveEnd < 0) {
            Player target = fight.randomPlayer();
            nextDive = now + (night ? DIVE_INTERVAL_NIGHT : DIVE_INTERVAL_DAY);
            if (target != null) {
                diveTarget = target.getLocation();
                diveAt = now + DIVE_WARNING;
                biteAt = -1;
                // the mark stays down until the dive is resolved (landed or abandoned), not just through the warning
                fight.telegraph(diveTarget, 3, DIVE_WARNING + DIVE_MAX_TICKS, SHADOW, FloorDecals.Mark.DIVE);
                matriarch.getWorld().playSound(matriarch.getLocation(), Sound.ENTITY_PHANTOM_SWOOP, 2F, 0.6F);
                act("TELL", target);
            }
        }
        if (diveAt >= 0 && now >= diveAt) {
            diveAt = -1;
            diveEnd = now + DIVE_MAX_TICKS;
            diveDistance = Double.MAX_VALUE;
            diveStalled = 0;
            matriarch.setAware(false);
            matriarch.setTarget(null);
            act("DIVE", null);
        }
    }

    /** Every tick: hold still while stunned, fly the dive smoothly, and land a rake's bite on its contact frame. */
    @Override
    public void move() {
        if (!matriarch.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (now < stunnedUntil) {
            matriarch.setVelocity(new Vector());
            return;
        }
        if (biteAt >= 0 && now >= biteAt) {
            biteAt = -1;
            landBite();
        }
        if (diveEnd >= 0) {
            Vector to = diveTarget.clone().add(0, 0.5, 0).toVector().subtract(matriarch.getLocation().toVector());
            double distance = to.length();
            diveStalled = distance > diveDistance - 0.05 ? diveStalled + 1 : 0;
            diveDistance = Math.min(diveDistance, distance);
            if (distance < 2) {
                impact();
            } else if (now >= diveEnd || diveStalled >= DIVE_STALL_TICKS) {
                abandonDive();
            } else {
                matriarch.setVelocity(to.normalize().multiply(Math.min(1.3, 0.3 + distance * 0.1)));
            }
        }
    }

    /**
     * Vanilla phantoms only swoop now and then, so the Matriarch also rakes: whenever it sweeps within reach of a player
     * (circling low, or after a dive) it lunges, and the bite lands {@link #BITE_LEAD} ticks later, at most once a second.
     */
    private void rake(int now) {
        if (now < nextRake || diveEnd >= 0 || diveAt >= 0 || biteAt >= 0) {
            return;
        }
        Location at = matriarch.getLocation().add(0, matriarch.getHeight() / 2, 0);
        for (Player player : fight.players()) {
            if (player.getLocation().add(0, 1, 0).distanceSquared(at) <= RAKE_REACH * RAKE_REACH) {
                biteAt = now + BITE_LEAD;
                nextRake = now + RAKE_COOLDOWN;
                matriarch.getWorld().playSound(at, Sound.ENTITY_PHANTOM_SWOOP, 1.2F, 1.3F);
                act("BITE", player);
                return;
            }
        }
    }

    /** The rake's bite: the nearest player still within reach (a step back during the lunge dodges it). */
    private void landBite() {
        Location at = matriarch.getLocation().add(0, matriarch.getHeight() / 2, 0);
        Player nearest = null;
        double best = (RAKE_REACH + 1) * (RAKE_REACH + 1);
        for (Player player : fight.players()) {
            double d = player.getLocation().add(0, 1, 0).distanceSquared(at);
            if (d <= best) {
                best = d;
                nearest = player;
            }
        }
        if (nearest != null) {
            fight.hit(nearest, BITE, BITE.damage() * (night ? 1.2 : 1), matriarch);
            matriarch.getWorld().playSound(at, Sound.ENTITY_PHANTOM_BITE, 1.2F, 0.7F);
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

    /** A dive that can't reach its mark: she pulls up and flies on; nothing is hit and she isn't stunned. */
    private void abandonDive() {
        diveEnd = -1;
        matriarch.setAware(true);
        matriarch.setVelocity(new Vector(0, 0.6, 0));
        matriarch.getWorld().playSound(matriarch.getLocation(), Sound.ENTITY_PHANTOM_FLAP, 2F, 0.6F);
        act("TAKEOFF", null);
        act(night ? "STATE_NIGHT" : "STATE_DAY", null);
    }

    private void impact() {
        diveEnd = -1;
        // she is within 2 blocks of her mark here: she lands on it (the mark showed where), on the ground under it
        Location at = diveTarget.clone();
        at.setY(groundY(at));
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, at.clone().add(0, 0.8, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, SHADOW, 3.5F);
        matriarch.teleport(at.clone().add(0, 0.3, 0));
        matriarch.setVelocity(new Vector());
        if (!mythic()) {
            matriarch.setGlowing(true);       // the model's own glow gutters instead (an invisible carrier would outline)
        }
        stunnedUntil = fight.elapsed() + STUN_TICKS;
        at.getWorld().playSound(at, Sound.ENTITY_PHANTOM_BITE, 2F, 0.5F);
        at.getWorld().spawnParticle(Particle.SONIC_BOOM, at.clone().add(0, 0.5, 0), 1);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 9) {
                fight.hit(player, DIVE, DIVE.damage() * (night ? 1.2 : 1), matriarch);
            }
        }
        act("IMPACT", null);
        fight.broadcast("&7The Matriarch is grounded - &fattack!");
    }

    @Override
    public void onBossDeath(LivingEntity boss) {
        io.github.amitelia.occultech.boss.Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(Color.fromRGB(34, 38, 42).asRGB(), "eye", "tendrils", "gill_left_0", "gill_left_1", "gill_left_2",
                "gill_right_0", "gill_right_1", "gill_right_2");               // the sculk's glow goes out
        }
    }
}
