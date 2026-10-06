package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

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

/**
 * Tier-2 gate boss (max netherite). An elder guardian gliding over the land.
 * <ul>
 * <li>Pressure: Mining Fatigue II on everyone in the arena (it also slows attacks).</li>
 * <li>Multi-beam: charges a beam at up to three players; each locks 0.5s before firing - step aside.</li>
 * <li>Every 20s two guardians join; they glide after players and fire small beams.</li>
 * <li>At half health, <b>Tidal Surge</b>: three waves roll out from it. Jump over each wave as it reaches you.</li>
 * </ul>
 * Its scales are thick: it takes a fifth of the damage dealt.
 */
public final class DrownedElder extends BossBehavior {

    private static final double HEALTH = 500;
    private static final double ARMOR = 0.2;
    private static final Color BEAM = Color.fromRGB(130, 90, 230);
    private static final Color ADD_BEAM = Color.fromRGB(90, 230, 210);
    private static final int FATIGUE_INTERVAL = 200;
    private static final int BEAM_INTERVAL = 160;
    private static final int BEAM_INTERVAL_SURGED = 110;
    private static final int GUARDIAN_INTERVAL = 400;
    private static final int ADD_BEAM_INTERVAL = 80;
    private static final io.github.amitelia.occultech.boss.Mechanic BEAM_HIT = io.github.amitelia.occultech.boss.Mechanic.of("DROWNED_ELDER", "Beam", 16, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic ADD_BEAM_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DROWNED_ELDER", "Guardian beam", 10, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic WAVE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DROWNED_ELDER", "Tidal wave", 33.5, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final double WAVE_SPEED = 0.6;
    private static final int WAVES = 3;
    private static final int WAVE_GAP = 40;

    private ElderGuardian elder;
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

    public DrownedElder(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        elder = fight.spawnBoss(ElderGuardian.class, at.clone().add(0, 2.5, 0), g -> {
            g.setCustomName(ChatColor.DARK_PURPLE + "Drowned Elder");
            g.setCustomNameVisible(true);
            Abyss.puppet(g);
            BossFight.setAttribute(g, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(g, Attribute.SCALE, 2.5);
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
            for (Player player : fight.players()) {
                player.addPotionEffect(new PotionEffect(PotionEffectType.MINING_FATIGUE, 300, 1));
            }
            elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_ELDER_GUARDIAN_CURSE, 1F, 1F);
        }

        if (!surged && fight.healthFraction() < 0.5) {
            surged = true;
            waveCenter = elder.getLocation();
            waveCenter.setY(Abyss.groundY(waveCenter));
            for (int i = 0; i < WAVES; i++) {
                waveStarts.add(now + 20 + i * WAVE_GAP);
            }
            fight.broadcast("&5&lTidal Surge! &fJump over each wave as it reaches you!");
            elder.getWorld().playSound(elder.getLocation(), Sound.ENTITY_ELDER_GUARDIAN_AMBIENT, 2F, 0.5F);
        }
        waves(now);

        if (now >= nextBeam && waveStarts.isEmpty()) {
            nextBeam = now + (surged ? BEAM_INTERVAL_SURGED : BEAM_INTERVAL);
            List<Player> players = new ArrayList<>(fight.players());
            Collections.shuffle(players);
            for (int i = 0; i < Math.min(3, players.size()); i++) {
                beams.add(new Abyss.Beam(elder, players.get(i), now, 40, BEAM_HIT, BEAM));
            }
        }
        beams.forEach(beam -> beam.step(fight, now));
        beams.removeIf(Abyss.Beam::done);

        if (every(GUARDIAN_INTERVAL)) {
            for (int i = 0; i < 2; i++) {
                Guardian guardian = fight.spawnAdd(Guardian.class, fight.randomPoint(4, 9).add(0, 1.5, 0), g -> {
                    Abyss.puppet(g);
                    BossFight.setAttribute(g, Attribute.MAX_HEALTH, 40);
                    g.setHealth(40);
                });
                if (guardian != null) {
                    guardians.add(guardian);
                }
            }
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
        if (!waveStarts.isEmpty() && waveCenter != null) {
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
