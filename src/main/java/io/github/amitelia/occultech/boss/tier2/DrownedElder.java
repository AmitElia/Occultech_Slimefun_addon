package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Supplier;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.ElderGuardian;
import org.bukkit.entity.Guardian;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Prop;

/**
 * Tier-2 gate boss (max netherite). An elder guardian gliding over the land; with the model, the Abyssal Serpent: the
 * Elder Guardian grown into an 18-block sea serpent with a webbed spike hood.
 * <ul>
 * <li>Pressure: Mining Fatigue II on everyone in the arena (it also slows attacks). With the model it coils overhead,
 * flares its hood and glares down; the pulse comes on the glare.</li>
 * <li>Multi-beam: charges a beam at up to three players; each locks 0.5s before firing - step aside. With the model it
 * coils into an S, its gills swing open, and each beam leaves one of the three eyes under them.</li>
 * <li>Every 20s two guardians join; they glide after players and fire small beams. With the model they shed from its
 * body after a shudder.</li>
 * <li>At half health, <b>Tidal Surge</b>: three waves roll out. Jump over each wave as it reaches you. With the model it
 * dives head first into the floor (the waves start where it went in) and bursts back out after the last wave.</li>
 * </ul>
 * Its scales are thick: it takes a fifth of the damage dealt.
 * <p>
 * With MythicMobs and BetterModel the body is the model on an unscaled, invisible elder guardian at the floor, the
 * head's centre about 4 blocks over it. Its moves are clips played from where the carrier stands, so the carrier holds
 * still through each of them (the coil, the glare, the shed, the surge, the rise from the circle) and turns slowly
 * otherwise: the whole body swings with it.
 */
public final class DrownedElder extends BossBehavior {

    private static final double HEALTH = 500;
    private static final double ARMOR = 0.2;
    private static final Color BEAM = Color.fromRGB(130, 90, 230);
    private static final Color ADD_BEAM = Color.fromRGB(90, 230, 210);
    private static final int FATIGUE_INTERVAL = 200;
    private static final int BEAM_INTERVAL = 160;
    private static final int BEAM_INTERVAL_SURGED = 110;
    private static final int BEAM_CHARGE = 40;
    private static final int GUARDIAN_INTERVAL = 400;
    private static final int ADD_BEAM_INTERVAL = 80;
    private static final io.github.amitelia.occultech.boss.Mechanic BEAM_HIT = io.github.amitelia.occultech.boss.Mechanic.of("DROWNED_ELDER", "Beam", 16, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic ADD_BEAM_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DROWNED_ELDER", "Guardian beam", 10, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic WAVE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DROWNED_ELDER", "Tidal wave", 33.5, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final double WAVE_SPEED = 0.6;
    private static final int WAVES = 3;
    private static final int WAVE_GAP = 40;

    // ---- the model's timing (session 7 clips; contacts in ticks from the clip's start) ----
    /** The model's lowest swimming point is well over the floor; the carrier itself sits on it. */
    private static final double MODEL_HOVER = 0.0;
    /** Degrees the modelled carrier turns per tick at most: the whole 18-block body swings with it. */
    private static final float MODEL_TURN = 1.5F;
    private static final int AIM_CLIP = 52;
    /** The beam eyes go white this long before the beams fire (Abyss.Beam turns them white then too). */
    private static final int LOCK_BEFORE = 15;
    private static final int STARE_PULSE = 20;
    private static final int STARE_END_TINT = 44;
    private static final int STARE_CLIP = 52;
    private static final int SHED_CONTACT = 10;
    private static final int SHED_CLIP = 24;
    private static final int DIVE_CONTACT = 20;
    private static final int EMERGE_CLIP = 52;
    private static final int EMERGE_OUT = 14;
    private static final int SPAWN_CLIP = 80;
    /** BetterModel's hit flash restores the tint it found, so the state tint is put back after it. */
    private static final int RETINT_AFTER = 12;
    private static final int DEAD_BEAM = Color.fromRGB(40, 44, 48).asRGB();
    private static final int DEAD_HEAD = Color.fromRGB(52, 50, 54).asRGB();

    private ElderGuardian elder;
    private boolean modelled;
    private final List<Abyss.Beam> beams = new ArrayList<>();
    private final List<Guardian> guardians = new ArrayList<>();
    private final List<Integer> waveStarts = new ArrayList<>();
    private final java.util.Map<Integer, java.util.Set<java.util.UUID>> waveHits = new java.util.HashMap<>();
    /** Which waves have their floor marking already rolling out (Session O4). */
    private final java.util.Set<Integer> waveShown = new java.util.HashSet<>();
    private Location waveCenter;
    private int nextBeam = 80;
    private boolean surged;
    /** Movement goals, chosen each step and followed every tick. */
    private Player chase;
    private int chaseUntil;
    /** It keeps a target at least this long (it used to switch every step to whoever was nearest). */
    private static final int CHASE_TICKS = 160;
    /** Degrees it turns per tick at most: a slow, heavy turn. */
    private static final float TURN = 4F;
    private final java.util.Map<Guardian, Player> guardianTargets = new java.util.HashMap<>();

    // ---- model only: what waits for a clip's contact ----
    private Location spawnedAt;
    /** No new move (and no flinch) while a clip plays; the carrier holds still. */
    private int busyUntil;
    private int flinchReady;
    private int retintAt = -1;
    private int lockAt = -1;
    private int aimEnds = -1;
    private boolean stareDue;
    private int pulseAt = -1;
    private int stareEndAt = -1;
    private boolean shedDue;
    private int shedAt = -1;
    private int emergeAt = -1;
    private int holeBAt = -1;

    public DrownedElder(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        modelled = fight.usesMythicBody();
        spawnedAt = at.clone();
        elder = fight.spawnBoss(ElderGuardian.class, at.clone().add(0, modelled ? MODEL_HOVER : 2.5, 0), g -> {
            g.setCustomName(ChatColor.DARK_PURPLE + "Drowned Elder");
            g.setCustomNameVisible(true);
            Abyss.puppet(g);
            BossFight.setAttribute(g, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(g, Attribute.SCALE, modelled ? 1.0 : 2.5);   // the model is drawn at its own size
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
    public void tick() {
        if (!elder.isValid()) {
            return;
        }
        int now = fight.elapsed();
        guardians.removeIf(g -> !g.isValid() || g.isDead());

        boolean keep = chase != null && chase.isValid() && !chase.isDead() && fight.players().contains(chase) && fight.elapsed() < chaseUntil;
        if (!keep) {
            chase = fight.nearestPlayer(elder.getLocation());
            chaseUntil = fight.elapsed() + CHASE_TICKS;
        }

        if (every(FATIGUE_INTERVAL)) {
            if (modelled) {
                stareDue = true;                 // the pulse comes on the stare's glare
            } else {
                pulse();
            }
        }
        if (modelled && stareDue && free(now)) {
            stareDue = false;
            act("STARE");
            pulseAt = now + STARE_PULSE;
            stareEndAt = now + STARE_END_TINT;
            busyUntil = now + STARE_CLIP;
        }

        if (!surged && fight.healthFraction() < 0.5) {
            surged = true;
            if (modelled) {
                // it dives head first into the floor ahead of it; the waves start where it went in, on the dive's contact
                act("DIVE");
                act("STATE_SURGED");
                waveCenter = point(DrownedElderRig.HOLE_A);
                emergeAt = now + DIVE_CONTACT + (WAVES - 1) * WAVE_GAP + 20;
                busyUntil = emergeAt + EMERGE_CLIP;
                lockAt = -1;
            } else {
                waveCenter = elder.getLocation();
            }
            waveCenter.setY(Abyss.groundY(waveCenter));
            for (int i = 0; i < WAVES; i++) {
                waveStarts.add(now + 20 + i * WAVE_GAP);
            }
            fight.broadcast("&5&lTidal Surge! &fJump over each wave as it reaches you!");
            elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_ELDER_GUARDIAN_AMBIENT, 2F, 0.5F);
        }
        waves(now);

        if (now >= nextBeam && waveStarts.isEmpty() && (!modelled || free(now))) {
            nextBeam = now + (surged ? BEAM_INTERVAL_SURGED : BEAM_INTERVAL);
            List<Player> players = new ArrayList<>(fight.players());
            Collections.shuffle(players);
            int count = Math.min(3, players.size());
            if (modelled && count > 0) {
                act("AIM");
                lockAt = now + BEAM_CHARGE - LOCK_BEFORE;
                aimEnds = now + BEAM_CHARGE + 4;
                busyUntil = now + AIM_CLIP;
            }
            for (int i = 0; i < count; i++) {
                Player target = players.get(i);
                beams.add(modelled
                    ? new Abyss.Beam(elder, eye(i, target, now), target, now, BEAM_CHARGE, BEAM_HIT, BEAM)
                    : new Abyss.Beam(elder, target, now, BEAM_CHARGE, BEAM_HIT, BEAM));
            }
        }
        beams.forEach(beam -> beam.step(fight, now));
        beams.removeIf(Abyss.Beam::done);

        if (every(GUARDIAN_INTERVAL)) {
            if (modelled) {
                shedDue = true;
            } else {
                guardiansJoin(null);
            }
        }
        if (modelled && shedDue && free(now) && waveStarts.isEmpty()) {
            shedDue = false;
            act("SHED");
            shedAt = now + SHED_CONTACT;
            busyUntil = now + SHED_CLIP;
        }
        for (int i = 0; i < guardians.size(); i++) {
            Guardian guardian = guardians.get(i);
            Player target = fight.nearestPlayer(guardian.getLocation());
            if (target == null) {
                continue;
            }
            guardianTargets.put(guardian, target);
            if ((now + i * 20) % ADD_BEAM_INTERVAL == 0 && target.getLocation().distanceSquared(guardian.getLocation()) <= 144) {
                beams.add(new Abyss.Beam(guardian, target, now, 30, ADD_BEAM_DAMAGE, ADD_BEAM));
            }
        }
    }

    @Override
    public void move() {
        if (!elder.isValid()) {
            return;
        }
        if (modelled) {
            moveModelled();
        } else if (!waveStarts.isEmpty() && waveCenter != null) {
            Abyss.glideSmooth(elder, waveCenter, 0.12, 3, 0, TURN);
        } else if (chase != null && chase.isValid() && chase.getWorld() == elder.getWorld()) {
            Abyss.glideSmooth(elder, chase.getLocation(), 0.1, 2.5, 9, TURN);
        } else {
            Abyss.glideSmooth(elder, fight.center(), 0.1, 2.5, 0, TURN);
        }
        guardianTargets.entrySet().removeIf(entry -> !entry.getKey().isValid() || entry.getKey().isDead());
        guardianTargets.forEach((guardian, target) -> {
            if (target.isValid() && target.getWorld() == guardian.getWorld()) {
                Abyss.glide(guardian, target.getLocation(), 0.18, 1.2, 4);
            }
        });
    }

    /** Every tick, model only: the clip contacts, the tints, and the carrier: still through every clip, else gliding. */
    private void moveModelled() {
        int now = fight.elapsed();
        if (lockAt >= 0 && now >= lockAt) {
            lockAt = -1;
            act("LOCK");
        }
        if (aimEnds >= 0 && now >= aimEnds) {
            aimEnds = -1;
            act(stateTint());
        }
        if (pulseAt >= 0 && now >= pulseAt) {
            pulseAt = -1;
            pulse();
        }
        if (stareEndAt >= 0 && now >= stareEndAt) {
            stareEndAt = -1;
            act("STARE_END");
        }
        if (shedAt >= 0 && now >= shedAt) {
            shedAt = -1;
            guardiansJoin(point(DrownedElderRig.SHED));
        }
        if (emergeAt >= 0 && now >= emergeAt) {
            emergeAt = -1;
            act("EMERGE");
            holeBAt = now + EMERGE_OUT;
        }
        if (holeBAt >= 0 && now >= holeBAt) {
            holeBAt = -1;
            Location hole = point(DrownedElderRig.HOLE_B);
            hole.setY(Abyss.groundY(hole));
            hole.getWorld().spawnParticle(Particle.SPLASH, hole.clone().add(0, 0.3, 0), 60, 1.2, 0.4, 1.2, 0.2);
            hole.getWorld().spawnParticle(Particle.BUBBLE_POP, hole.clone().add(0, 0.6, 0), 24, 1.0, 0.6, 1.0, 0.05);
        }
        if (retintAt >= 0 && now >= retintAt) {
            retintAt = -1;
            act(lockAt < 0 && aimEnds >= 0 ? "LOCK" : stateTint());
        }
        boolean spawning = now < SPAWN_CLIP && flat(elder.getLocation(), spawnedAt) < 4;
        boolean aiming = aimEnds >= 0 || lockAt >= 0;
        if (now < busyUntil || spawning) {
            // a clip plays from where the carrier stands: it holds still (aiming, it may still turn slowly on its target)
            Location at = elder.getLocation();
            elder.setVelocity(new Vector(0, (Abyss.groundY(at) + MODEL_HOVER - at.getY()) * 0.2, 0));
            if (aiming && chase != null && chase.isValid() && chase.getWorld() == elder.getWorld()) {
                Abyss.turnToward(elder, chase.getLocation(), MODEL_TURN * 0.5F);
            }
            return;
        }
        if (chase != null && chase.isValid() && chase.getWorld() == elder.getWorld()) {
            Abyss.glideSmooth(elder, chase.getLocation(), 0.1, MODEL_HOVER, 9, MODEL_TURN);
        } else {
            Abyss.glideSmooth(elder, fight.center(), 0.1, MODEL_HOVER, 0, MODEL_TURN);
        }
        elder.setRotation(elder.getBodyYaw(), 0F);   // the model's head keeps in line with its body
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (!modelled || boss != elder) {
            return;
        }
        int now = fight.elapsed();
        retintAt = now + RETINT_AFTER;
        if (now >= busyUntil && now >= flinchReady) {
            flinchReady = now + 15;
            act("FLINCH");
        }
    }

    /** The model stays for its whole death clip, every eye dark. */
    @Override
    public void onBossDeath(LivingEntity boss) {
        if (!modelled || boss != elder) {
            return;
        }
        Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(DEAD_BEAM, "eye2", "eye4", "eye6");
            corpse.tint(DEAD_HEAD, "eye");
        }
    }

    private boolean free(int now) {
        return now >= busyUntil && waveStarts.isEmpty() && emergeAt < 0;
    }

    private String stateTint() {
        return surged ? "STATE_SURGED" : "STATE_CALM";
    }

    private void act(String action) {
        fight.playAction(elder, action);
    }

    private void pulse() {
        for (Player player : fight.players()) {
            player.addPotionEffect(new PotionEffect(PotionEffectType.MINING_FATIGUE, 300, 1));
        }
        elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_ELDER_GUARDIAN_CURSE, 1F, 1F);
        if (modelled) {
            act("PULSE");
            Location glare = point(DrownedElderRig.STARE_EYE);
            glare.getWorld().spawnParticle(Particle.GLOW, glare, 30, 0.5, 0.5, 0.5, 0.02);
        }
    }

    private void guardiansJoin(Location near) {
        for (int i = 0; i < 2; i++) {
            Location spot = near == null ? fight.randomPoint(4, 9).add(0, 1.5, 0)
                : near.clone().add((i == 0 ? 1.5 : -1.5), -1.0, 0);
            if (near != null) {
                spot.getWorld().spawnParticle(Particle.BUBBLE_POP, spot, 16, 0.4, 0.4, 0.4, 0.05);
            }
            Guardian guardian = fight.spawnAdd(Guardian.class, spot, g -> {
                Abyss.puppet(g);
                BossFight.setAttribute(g, Attribute.MAX_HEALTH, 40);
                g.setHealth(40);
            });
            if (guardian != null) {
                guardians.add(guardian);
            }
        }
    }

    // ---- the model's parts in the world ----

    /** A rig point ({ahead, up, right} blocks from the carrier's feet) in the world, for the carrier's body yaw now. */
    private Location point(double[] rig) {
        float yaw = elder.getBodyYaw();
        return elder.getLocation().add(0, rig[1], 0).add(facing(yaw).multiply(rig[0])).add(right(yaw).multiply(rig[2]));
    }

    /**
     * Beam eye {@code index} (0..2: segments 3, 5, 7) through the aim clip, the side nearer the target: where its beam
     * leaves. The clip started at {@code started}; after its contact the eye stays where it was then.
     */
    private Supplier<Location> eye(int index, Player target, int started) {
        return () -> {
            double seconds = (fight.elapsed() - started) / 20.0;
            double[] frames = DrownedElderRig.AIM_FRAMES;
            int k = 0;
            while (k < frames.length - 2 && seconds > frames[k + 1]) {
                k++;
            }
            double f = Math.max(0, Math.min(1, (seconds - frames[k]) / (frames[k + 1] - frames[k])));
            Location best = null;
            for (double[][] side : DrownedElderRig.EYES[index]) {
                double[] a = side[k];
                double[] b = side[k + 1];
                Location at = point(new double[] {a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f});
                if (best == null || (target.isValid() && at.distanceSquared(target.getEyeLocation()) < best.distanceSquared(target.getEyeLocation()))) {
                    best = at;
                }
            }
            return best;
        };
    }

    /** Which way a yaw faces, flat (Minecraft: yaw 0 faces +z, 90 faces -x). */
    private static Vector facing(float yaw) {
        double r = Math.toRadians(yaw);
        return new Vector(-Math.sin(r), 0, Math.cos(r));
    }

    /** The right-hand side for a yaw. */
    private static Vector right(float yaw) {
        double r = Math.toRadians(yaw);
        return new Vector(-Math.cos(r), 0, -Math.sin(r));
    }

    private static double flat(Location a, Location b) {
        return a.getWorld() != b.getWorld() ? Double.MAX_VALUE : Math.hypot(a.getX() - b.getX(), a.getZ() - b.getZ());
    }

    /** Each wave is a ring expanding from the surge point; players on the ground when it passes them are hit. */
    private void waves(int now) {
        if (waveStarts.isEmpty()) {
            return;
        }
        double maxRadius = fight.radius() + 1;
        boolean anyActive = false;
        for (int w = 0; w < waveStarts.size(); w++) {
            int start = waveStarts.get(w);
            if (now < start) {
                anyActive = true;
                continue;
            }
            double radius = (now - start) * WAVE_SPEED;
            if (radius > maxRadius) {
                continue;
            }
            if (!waveShown.contains(w)) {
                waveShown.add(w);
                FloorDecals.wave(fight, waveCenter, radius, maxRadius, (int) Math.ceil((maxRadius - radius) / WAVE_SPEED),
                    org.bukkit.Color.fromRGB(70, 170, 230));
            }
            anyActive = true;
            int points = (int) Math.max(12, radius * 5);
            for (int i = 0; i < points; i++) {
                double angle = Math.PI * 2 * i / points;
                Location point = waveCenter.clone().add(Math.cos(angle) * radius, 0.3, Math.sin(angle) * radius);
                point.getWorld().spawnParticle(Particle.SPLASH, point, 3, 0.1, 0.2, 0.1, 0);
                if (i % 3 == 0) {
                    point.getWorld().spawnParticle(Particle.BUBBLE_POP, point.clone().add(0, 0.4, 0), 1, 0, 0, 0, 0);
                }
            }
            if ((now - start) % 20 == 0) {
                waveCenter.getWorld().playSound(waveCenter, Sound.ENTITY_GENERIC_SPLASH, 1.5F, 0.6F);
            }
            java.util.Set<java.util.UUID> hit = waveHits.computeIfAbsent(w, k -> new java.util.HashSet<>());
            for (Player player : fight.players()) {
                double distance = player.getLocation().toVector().subtract(waveCenter.toVector()).setY(0).length();
                boolean grounded = player.getLocation().getY() - Abyss.groundY(player.getLocation()) < 0.6;
                if (!hit.contains(player.getUniqueId()) && Math.abs(distance - radius) <= 1.5 && grounded) {
                    hit.add(player.getUniqueId());
                    fight.hit(player, WAVE_DAMAGE, elder);
                    Vector push = player.getLocation().toVector().subtract(waveCenter.toVector()).setY(0);
                    if (push.lengthSquared() > 0.01) {
                        player.setVelocity(push.normalize().multiply(0.6).setY(0.3));
                    }
                }
            }
        }
        if (!anyActive) {
            waveStarts.clear();
            waveHits.clear();
            fight.broadcast("&5The surge ebbs.");
        }
    }
}
