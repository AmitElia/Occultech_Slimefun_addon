package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.AirEffects;
import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.Prop;

import java.util.ArrayList;
import java.util.List;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Guardian;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-2 mini-boss (max netherite): the Lost Helmet, a copper diving-helmet that glides over the land, a slit eye
 * crammed into its window.
 * <ul>
 * <li>Charged beam from the eye: tracks a player for 2s and turns white near the end; sprint sideways to dodge. Magic
 * damage (ignores armor, like the vanilla guardian laser).</li>
 * <li>Hose lash: anyone within 3.5 blocks is hit once a second.</li>
 * <li>Spike burst: a ring warns for 1s, then the valves blow, hurting and pushing everyone close. Then it rests.</li>
 * <li>Below half health the eye turns bloodshot and it charges two beams at once, more often.</li>
 * <li>At a third, a huge barnacled hand bursts out of its right side window and smashes: it turns and lunges so the
 * hand comes down on a ring round a player (1.25s warning), then stays down for a second.</li>
 * </ul>
 * Its hide is hard: it takes a third of the damage dealt (health attributes can't go past 1024 with group scaling).
 * With MythicMobs and BetterModel it wears the occultech_abyssal_warden model on an unscaled guardian (Session 8).
 */
public final class AbyssalWarden extends BossBehavior {

    static final double HEALTH = 270;
    static final double ARMOR = 0.33;
    private static final Color BEAM = Color.fromRGB(90, 230, 210);
    private static final Color SPIKES = Color.fromRGB(230, 170, 60);
    private static final Color SMASH = Color.fromRGB(120, 200, 150);
    private static final int BEAM_INTERVAL = 120;
    private static final int BEAM_INTERVAL_ENRAGED = 80;
    /** Alone, one player takes every beam, lash and spike: the solo pace is slower (Session R2). */
    private static final int SOLO_BEAM_INTERVAL = 160;
    private static final int SOLO_BEAM_INTERVAL_ENRAGED = 120;
    private static final int BEAM_CHARGE = 40;
    private static final int LASH_COOLDOWN = 20;
    private static final int SOLO_LASH_COOLDOWN = 35;
    /** After its spikes it rests, an opening to hit it. */
    private static final int REST_TICKS = 40;
    private static final int SPIKE_INTERVAL = 240;
    /** The burst at a third: the clip runs 2.4s; the hand is out from 0.8s. */
    private static final int BURST_TICKS = 48;
    /** The smash: a 1.25s warning, the hand stays down until 2.25s, the clip ends at 2.8s. */
    private static final int SMASH_TELL = 25;
    private static final int SMASH_TICKS = 56;
    private static final int SMASH_INTERVAL = 160;
    private static final int SOLO_SMASH_INTERVAL = 200;
    private static final double SMASH_RADIUS = 2.5;
    /** Where the hand lands in the smash, from the carrier in blocks: to his right and ahead (the s7 rig's contact key). */
    private static final double HAND_RIGHT = 4.17;
    private static final double HAND_AHEAD = 4.1;
    /** Where the eye sits in the model, from the carrier in blocks. */
    private static final double EYE_UP = 3.8;
    private static final double EYE_AHEAD = 2.0;
    private static final double EYE_RIGHT = 0.2;
    /** BetterModel's red hit flash; a tint set during it sticks, so the eye is tinted again once it is over. */
    private static final int HIT_FLASH = 10;
    private static final Mechanic BEAM_HIT = Mechanic.of("ABYSSAL_WARDEN", "Beam", 15.5, Mechanic.Kind.MAGIC, true);
    private static final Mechanic SPIKE_DAMAGE = Mechanic.of("ABYSSAL_WARDEN", "Spikes", 30, Mechanic.Kind.AREA, true);
    private static final Mechanic LASH_DAMAGE = Mechanic.of("ABYSSAL_WARDEN", "Lash", 23, Mechanic.Kind.MELEE, false);
    private static final Mechanic SMASH_DAMAGE = Mechanic.of("ABYSSAL_WARDEN", "Smash", 32, Mechanic.Kind.AREA, true);
    private static final double LASH_RANGE = 3.5;

    private Guardian warden;
    private final List<Abyss.Beam> beams = new ArrayList<>();
    private int nextBeam = 60;
    private int nextLash;
    /** Who it glides after (chosen each step, followed every tick). */
    private Player chase;
    private int spikesAt = -1;
    private boolean enraged;
    private int restUntil;
    /** From a third: the hand is out. */
    private boolean armOut;
    /** Bursting or smashing: no other attack starts, and it moves only as the smash needs. */
    private int busyUntil;
    private int nextSmash;
    private int smashAt = -1;
    @Nullable private Location smashSpot;
    @Nullable private Location smashFrom;
    private float smashYaw;
    /** The eye stays white from here until the beam fires. */
    private int trackingFrom = -1;
    private int trackingUntil = -1;
    private int lastHit = -100;
    private int lastFlinch = -100;
    private boolean tintDirty;
    /** A resumed fight puts its phase look back on the next step. */
    private boolean restoreLook;

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
        });
        if (!mythic()) {
            BossFight.setAttribute(warden, Attribute.SCALE, 3);
        }
    }

    private boolean mythic() {
        return fight.usesMythicBody();
    }

    /** Plays a skill on the model: the {@code _33} version from a third, where the clip has one. */
    private void act(String action, @Nullable Entity target) {
        if (mythic() && warden != null && warden.isValid()) {
            fight.playAction(warden, action, target);
        }
    }

    private String phased(String action) {
        return armOut ? action + "_33" : action;
    }

    /** How high the carrier floats: the model hangs its kelp from the carrier, the vanilla guardian hovers. */
    private double hover() {
        return mythic() ? 0.25 : 1.5;
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
    public int phase() {
        return armOut ? 3 : enraged ? 2 : 1;
    }

    // ------------------------------------------------------------------ every tick: the glide

    @Override
    public void move() {
        if (!warden.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (smashFrom != null && now < busyUntil) {
            lunge(now);
        } else if (now < restUntil || now < busyUntil) {
            // resting low after its spikes, or bursting: hold still, facing where it faced
            Location ahead = warden.getLocation().add(facing(warden.getBodyYaw()).multiply(0.5));
            Abyss.glide(warden, ahead, 0, now < restUntil ? (mythic() ? 0.05 : 1.2) : hover(), 1);
        } else if (chase != null && chase.isValid() && chase.getWorld() == warden.getWorld()) {
            Abyss.glide(warden, chase.getLocation(), solo() ? 0.12 : 0.16, hover(), 3);
        } else {
            Abyss.glide(warden, fight.center(), 0.1, hover(), 0);
        }
    }

    /** The smash: it swings round and closes in so the hand comes down on the ring, then holds still. */
    private void lunge(int now) {
        Location at = warden.getLocation();
        Vector velocity = new Vector();
        if (now < smashAt) {
            Vector to = smashFrom.toVector().subtract(at.toVector()).setY(0);
            double distance = to.length();
            if (distance > 0.1) {
                velocity = to.normalize().multiply(Math.min(0.3, distance * 0.3));
            }
        }
        double wantY = Abyss.groundY(at) + hover();
        velocity.setY(Math.max(-0.4, Math.min(0.4, (wantY - at.getY()) * 0.3)));
        warden.setVelocity(velocity);
        float yaw = at.getYaw();
        float delta = ((smashYaw - yaw) % 360 + 540) % 360 - 180;
        float turned = yaw + Math.max(-12, Math.min(12, delta));
        warden.setRotation(turned, 0);
        warden.setBodyYaw(turned);
    }

    // ------------------------------------------------------------------ every step: the attacks

    @Override
    public void tick() {
        if (!warden.isValid()) {
            return;
        }
        int now = fight.elapsed();
        chase = fight.nearestPlayer(warden.getLocation());
        if (restoreLook) {
            restoreLook = false;
            act(armOut ? "PHASE_33" : "PHASE_FURIOUS", null);
            tintEye(now);
        }

        if (!enraged && fight.healthFraction() < 0.5) {
            enraged = true;
            fight.broadcast("&3The Warden's eye burns brighter - &ftwo beams at once!");
            act("FURIOUS", null);
        }
        if (!armOut && fight.healthFraction() < 1 / 3.0 && now >= busyUntil && smashAt < 0) {
            burst(now);
        }

        boolean free = now >= busyUntil;
        if (now >= nextBeam && free) {
            nextBeam = now + (solo() ? (enraged ? SOLO_BEAM_INTERVAL_ENRAGED : SOLO_BEAM_INTERVAL) : (enraged ? BEAM_INTERVAL_ENRAGED : BEAM_INTERVAL));
            List<Player> players = new ArrayList<>(fight.players());
            java.util.Collections.shuffle(players);
            for (int i = 0; i < Math.min(enraged ? 2 : 1, players.size()); i++) {
                beams.add(new Abyss.Beam(warden, mythic() ? this::eye : null, players.get(i), now, BEAM_CHARGE, BEAM_HIT, BEAM));
            }
            if (!players.isEmpty()) {
                act(phased("BEAM"), players.get(0));
                trackingFrom = now + BEAM_CHARGE - 15;
                trackingUntil = now + BEAM_CHARGE + 2;
            }
        }
        beams.forEach(beam -> beam.step(fight, now));
        beams.removeIf(Abyss.Beam::done);
        if (trackingFrom >= 0 && now >= trackingFrom) {
            trackingFrom = -1;
            tintEye(now);
        }
        if (trackingUntil >= 0 && now >= trackingUntil) {
            trackingUntil = -1;
            tintEye(now);
        }

        if (now >= nextLash) {
            boolean lashed = false;
            for (Player player : fight.players()) {
                if (player.getLocation().add(0, 1, 0).distanceSquared(warden.getLocation().add(0, 1, 0)) <= LASH_RANGE * LASH_RANGE) {
                    fight.hit(player, LASH_DAMAGE, warden);
                    lashed = true;
                    nextLash = now + (solo() ? SOLO_LASH_COOLDOWN : LASH_COOLDOWN);
                }
            }
            if (lashed) {
                warden.getWorld().playSound(warden.getLocation(), Sound.ENTITY_GUARDIAN_HURT, 1F, 0.5F);
                if (free) {
                    act(phased("LASH"), null);
                }
            }
        }

        if (every(SPIKE_INTERVAL) && spikesAt < 0 && free) {
            spikesAt = now + 20;
            fight.telegraph(ground(warden.getLocation()), 5, 25, SPIKES, FloorDecals.Mark.SPIKES);
            warden.getWorld().playSound(warden.getLocation(), Sound.ENTITY_GUARDIAN_FLOP, 2F, 0.5F);
            act(phased("SPIKES"), null);
        }
        if (spikesAt >= 0 && now >= spikesAt) {
            spikesAt = -1;
            spikes();
            restUntil = now + REST_TICKS;
            act(phased("REST"), null);
            tintEye(now);
        }
        if (restUntil > 0 && now >= restUntil) {
            restUntil = 0;
            tintEye(now);
        }

        if (armOut && smashAt < 0 && now >= nextSmash && now >= busyUntil && spikesAt < 0 && now >= restUntil
            && chase != null && chase.isValid()) {
            startSmash(now, chase);
        }
        if (smashAt >= 0 && now >= smashAt) {
            smashAt = -1;
            smash();
        }
        if (now >= busyUntil) {
            smashFrom = null;
        }

        if (tintDirty && now - lastHit >= HIT_FLASH + 2) {
            tintDirty = false;
            act("UNTINT", null);
            tintEye(now);
        }
    }

    private boolean solo() {
        return fight.players().size() <= 1;
    }

    private static Location ground(Location at) {
        Location spot = at.clone();
        spot.setY(Abyss.groundY(at));
        return spot;
    }

    /** Which way a yaw faces, flat (Minecraft: yaw 0 faces +z, 90 faces -x). */
    private static Vector facing(float yaw) {
        double r = Math.toRadians(yaw);
        return new Vector(-Math.sin(r), 0, Math.cos(r));
    }

    /** His right for a yaw. */
    private static Vector right(float yaw) {
        double r = Math.toRadians(yaw);
        return new Vector(-Math.cos(r), 0, -Math.sin(r));
    }

    /** The eye in the model's window, where the beams leave. */
    private Location eye() {
        Location at = warden.getLocation();
        float yaw = warden.getBodyYaw();
        return at.add(0, EYE_UP, 0).add(facing(yaw).multiply(EYE_AHEAD)).add(right(yaw).multiply(EYE_RIGHT));
    }

    /** The eye's colour for where the fight stands. */
    private void tintEye(int now) {
        String state = trackingFrom < 0 && trackingUntil >= 0 && now < trackingUntil ? "TRACKING"
            : now < restUntil ? "RESTING" : enraged ? "FURIOUS" : "CALM";
        act("STATE_" + state, null);
    }

    private void spikes() {
        Location at = warden.getLocation();
        at.getWorld().playSound(at, Sound.ENCHANT_THORNS_HIT, 2F, 0.6F);
        at.getWorld().spawnParticle(Particle.CRIT, at.clone().add(0, 1, 0), 60, 2.5, 1, 2.5, 0.4);
        AirEffects.burst(fight, ground(at).add(0, 1, 0), AirEffects.Burst.IMPACT, SPIKES, 5F);
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

    // ------------------------------------------------------------------ a third: the hand

    private void burst(int now) {
        armOut = true;
        enraged = true;
        busyUntil = now + BURST_TICKS;
        nextSmash = now + BURST_TICKS + 40;
        beams.clear();
        trackingFrom = trackingUntil = -1;
        act("BURST", null);
        fight.broadcast("&3The Warden's side window bursts - &fa barnacled hand reaches out!");
        Location window = warden.getLocation().add(0, EYE_UP - 0.4, 0).add(right(warden.getBodyYaw()).multiply(2.2));
        warden.getWorld().playSound(window, Sound.BLOCK_GLASS_BREAK, 2F, 0.6F);
        warden.getWorld().spawnParticle(Particle.SPLASH, window, 60, 0.5, 0.5, 0.5, 0.3);
    }

    /**
     * Locks the ring on the target and works out where the carrier must be so the hand lands on it: the hand comes down
     * 45 degrees to his right, so he turns 45 degrees left of the target and closes in. The vanilla guardian has no
     * hand: it holds still and the ring is the whole attack.
     */
    private void startSmash(int now, Player target) {
        smashSpot = ground(target.getLocation());
        Vector to = smashSpot.toVector().subtract(warden.getLocation().toVector()).setY(0);
        float bearing = (float) Math.toDegrees(Math.atan2(-to.getX(), to.getZ()));
        if (mythic()) {
            smashYaw = bearing - 45;
            Vector hand = right(smashYaw).multiply(HAND_RIGHT).add(facing(smashYaw).multiply(HAND_AHEAD));
            smashFrom = smashSpot.clone().subtract(hand);
        } else {
            smashYaw = bearing;
            smashFrom = warden.getLocation();
        }
        smashAt = now + SMASH_TELL;
        busyUntil = now + SMASH_TICKS;
        nextSmash = now + (solo() ? SOLO_SMASH_INTERVAL : SMASH_INTERVAL);
        fight.telegraph(smashSpot, SMASH_RADIUS, SMASH_TELL, SMASH, FloorDecals.Mark.SLAM);
        act("SMASH", target);
    }

    private void smash() {
        if (smashSpot == null) {
            return;
        }
        Location at = smashSpot;
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 1.4F, 0.6F);
        AirEffects.burst(fight, at.clone().add(0, 0.5, 0), AirEffects.Burst.IMPACT, SMASH, 3F);
        at.getWorld().spawnParticle(Particle.SPLASH, at.clone().add(0, 0.3, 0), 80, 1.5, 0.2, 1.5, 0.4);
        for (Player player : fight.players()) {
            Location feet = player.getLocation();
            double dx = feet.getX() - at.getX();
            double dz = feet.getZ() - at.getZ();
            if (dx * dx + dz * dz <= SMASH_RADIUS * SMASH_RADIUS && Math.abs(feet.getY() - at.getY()) < 3) {
                fight.hit(player, SMASH_DAMAGE, warden);
                player.setVelocity(player.getVelocity().setY(0.5));
            }
        }
    }

    // ------------------------------------------------------------------ hits and death

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        int now = fight.elapsed();
        lastHit = now;
        tintDirty = true;
        if (now - lastFlinch > 12 && now >= busyUntil && spikesAt < 0 && now >= restUntil) {
            lastFlinch = now;
            act(phased("FLINCH"), null);
        }
    }

    @Override
    public void onBossDeath(LivingEntity boss) {
        Prop corpse = fight.corpse(boss);
        if (corpse == null) {
            return;
        }
        if (enraged) {
            corpse.hidePart("sclera");
            corpse.showPart("sclera_blood");
        }
        if (armOut) {
            corpse.hidePart("window_r_glass");
            for (String part : List.of("window_r_burst", "arm", "forearm", "hand")) {
                corpse.showPart(part);
            }
        }
        corpse.tint(Color.fromRGB(26, 34, 38).asRGB(), "iris");
    }

    // ------------------------------------------------------------------ saved with the fight

    @Override
    public String saveData() {
        return "enraged=" + (enraged ? 1 : 0) + ";arm=" + (armOut ? 1 : 0);
    }

    @Override
    public void restoreData(String data) {
        for (String entry : data.split(";")) {
            String[] kv = entry.split("=");
            if (kv.length == 2 && "1".equals(kv[1])) {
                switch (kv[0]) {
                    case "enraged" -> enraged = true;
                    case "arm" -> {
                        armOut = true;
                        enraged = true;
                        nextSmash = fight.elapsed() + 60;
                    }
                    default -> { }
                }
            }
        }
        restoreLook = enraged;
    }
}
