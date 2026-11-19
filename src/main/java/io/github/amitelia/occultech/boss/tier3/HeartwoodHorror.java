package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Creaking;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.AirEffects;
import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Prop;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Tier-3 mini-boss (Infinity gear). A giant creaking that - unlike every other creaking - never freezes when looked at
 * (Session R4: our own movement and attacks replace vanilla's AI). It stalks its target and fills the circle with area
 * attacks:
 * <ul>
 * <li>Heart markers: four creaking-heart markers stand around the circle (display entities, not real blocks). While
 * any stands, the Horror can't be hurt. Breaking all four opens a 20s window, then the hearts regrow. The hearts pulse
 * with thorns now and then, so breaking them is a fight of its own.</li>
 * <li>Swipe: a heavy blow at close range, at most every 2s.</li>
 * <li>Root eruptions: three lanes of roots burst from it, toward its target and to either side.</li>
 * <li>Sap rain: amber sap falls on marked spots - under every player and around the circle.</li>
 * <li>Ground slam: it brings the crutch and its great arm down together, and a ring of roots erupts where they land.</li>
 * <li>Creak: it goes dark, vanishes and strikes from behind a player.</li>
 * </ul>
 * Its hits are few and heavy. It is not tied to a real creaking heart, so its health is ours to manage; it takes an
 * eighth of the damage dealt.
 * <p>
 * The look comes from the Mythic body (Mobs/Skills HeartwoodHorror.yml, model occultech_heartwood_horror, session 8):
 * one move plays at a time, each clip started so its hands land on the server's moment, and every hit lands where the
 * model's hand is (HeartwoodHorrorRig, generated from the clips). Its blooms, lantern, eyelids and womb are tinted per
 * state: calm, vulnerable (the sleeper's eyes open), dark for the creak, dead. Without Mythic the fight plays as before
 * on a scaled vanilla creaking.
 */
public final class HeartwoodHorror extends BossBehavior {

    private static final Mechanic SWIPE = Mechanic.of("HEARTWOOD_HORROR", "Swipe", 47, Mechanic.Kind.MELEE, false);
    private static final Mechanic LUNGE_DAMAGE = Mechanic.of("HEARTWOOD_HORROR", "Lunge", 59, Mechanic.Kind.AREA, true);
    private static final Mechanic ERUPTION = Mechanic.of("HEARTWOOD_HORROR", "Root eruption", 55, Mechanic.Kind.AREA, true);
    private static final Mechanic SAP = Mechanic.of("HEARTWOOD_HORROR", "Sap rain", 45, Mechanic.Kind.AREA, true);
    private static final Mechanic SLAM = Mechanic.of("HEARTWOOD_HORROR", "Ground slam", 57, Mechanic.Kind.AREA, true);
    private static final Mechanic THORNS = Mechanic.of("HEARTWOOD_HORROR", "Heart thorns", 42, Mechanic.Kind.AREA, true);

    private static final double HEALTH = 320;
    private static final double ARMOR = 0.125;
    private static final int HEARTS = 4;
    private static final int HEART_HITS = 12;
    private static final int VULNERABLE_TICKS = 400;
    private static final double SPEED = 0.2;
    private static final double REACH = 3.2;
    private static final int SWIPE_COOLDOWN = 40;
    private static final int ERUPTION_INTERVAL = 140;
    private static final int SAP_INTERVAL = 180;
    private static final int SLAM_INTERVAL = 220;
    private static final int THORN_INTERVAL = 120;
    private static final int CREAK_INTERVAL = 260;
    private static final int WARNING = 30;
    private static final double LANE_LENGTH = 14;
    private static final double LANE_WIDTH = 2.2;
    private static final double SAP_RADIUS = 2.2;
    private static final double SLAM_RADIUS = 6;
    private static final double THORN_RADIUS = 3.5;
    private static final Color ROOTS = Color.fromRGB(90, 70, 50);
    private static final Color AMBER = Color.fromRGB(230, 140, 40);

    // ---- the model (session 7 clips, in ticks; contacts from HeartwoodHorrorRig) ----
    /** The walk clip's stride is 1.6 blocks a second: faster and the feet skate. */
    private static final double MODEL_SPEED = 0.08;
    /** It stops this far from its target (horizontal blocks): the great hand lands about 6.7 ahead. */
    private static final double HOLD = 5.0;
    /** It swipes at a target this far away (horizontal): the hand comes down on them. */
    private static final double SWIPE_MIN = 2.5;
    private static final double SWIPE_MAX = 8.0;
    /** Caught within this far (horizontal) of where the great hand lands. */
    private static final double SWIPE_HIT = 2.6;
    private static final double LUNGE_HIT = 2.4;
    private static final int SPAWN_CLIP = 84;
    private static final int SWIPE_CLIP = 28;
    private static final int LUNGE_CLIP = 24;
    private static final int ERUPTION_CLIP = 48;
    private static final int SAP_CLIP = 52;
    private static final int SLAM_CLIP = 46;
    /** The creak clip (the old 20-tick warning): it folds in, goes dark, and is gone. */
    private static final int CREAK_CLIP = 20;
    private static final int STAGGER_CLIP = 36;
    /** BetterModel's hit flash restores the tint it found, so the state tints are put back after it. */
    private static final int RETINT_AFTER = 12;
    private static final int RETARGET_TICKS = 160;
    private static final String[] GLOWS = {"blooms_crutch1", "blooms_crutch2", "blooms_crutch4", "blooms_great1",
        "blooms_great2", "blooms_great3", "blooms_lesser1", "blooms_lesser2", "blooms_thin1", "blooms_thin2",
        "blooms_back0", "blooms_back1", "blooms_back2", "blooms_back3", "hump_blooms"};

    /** A delayed area hit: when it lands, where, and what decides who's caught. */
    private record Pending(int at, Mechanic mechanic, java.util.function.Predicate<Location> caught, Runnable effect) {}

    private Creaking horror;
    private final List<BossFight.FightObject> hearts = new ArrayList<>();
    private final List<Pending> pending = new ArrayList<>();
    /** Roots and sap round it while its hearts make it invulnerable. */
    @Nullable private AirEffects.Aura roots;
    private int vulnerableUntil = -1;
    private int heartsLeft;
    private int nextSwipe;
    private int creakAt = -1;
    private Player creakTarget;
    private Player target;

    // ---- model only ----
    private boolean modelled;
    private int busyUntil;
    private boolean eruptionDue;
    private boolean sapDue;
    private boolean slamDue;
    private boolean creakDue;
    private boolean staggerDue;
    /** The facing a move locked as it started (null: it turns to its target). */
    @Nullable private Vector locked;
    private int swipeAt = -1;
    private int lungeAt = -1;
    private int digAt = -1;
    private int wombAt = -1;
    private int retintAt = -1;
    private int retargetAt;

    public HeartwoodHorror(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        modelled = fight.usesMythicBody();
        horror = fight.spawnBoss(Creaking.class, at.clone().add(0, 1, 0), c -> {
            c.setCustomName(ChatColor.GOLD + "Heartwood Horror");
            c.setCustomNameVisible(true);
            BossFight.setAttribute(c, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(c, Attribute.FOLLOW_RANGE, 48);
            BossFight.setAttribute(c, Attribute.KNOCKBACK_RESISTANCE, 1);
            // no vanilla AI: a creaking freezes while watched; ours walks and strikes whether you look or not
            Abyss.puppet(c);
            c.setGravity(true);
        });
        if (!modelled) {
            // the model is drawn as authored on an unscaled, invisible creaking; the vanilla body is scaled up instead
            BossFight.setAttribute(horror, Attribute.SCALE, 1.6);
        }
        busyUntil = fight.elapsed() + (modelled ? SPAWN_CLIP : 0);
        nextSwipe = busyUntil;
        growHearts();
    }

    /** Invulnerable while any heart stands. */
    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        if (fight.elapsed() >= vulnerableUntil) {
            Location at = modelled ? point(HeartwoodHorrorRig.WOMB) : boss.getLocation().add(0, 2, 0);
            boss.getWorld().spawnParticle(Particle.BLOCK, at, 12, 0.4, 0.6, 0.4, Material.PALE_OAK_LOG.createBlockData());
            boss.getWorld().playSound(boss.getLocation(), Sound.BLOCK_CREAKING_HEART_HURT, 1F, 0.6F);
            return 0;
        }
        return damage * ARMOR;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (modelled && boss == horror) {
            retintAt = fight.elapsed() + RETINT_AFTER;
        }
    }

    /** The model stays for its whole death clip, every light out. */
    @Override
    public void onBossDeath(LivingEntity boss) {
        if (!modelled || boss != horror) {
            return;
        }
        Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(Color.fromRGB(36, 32, 32).asRGB(), GLOWS);
            corpse.tint(Color.fromRGB(30, 26, 24).asRGB(), "heartlight");
            corpse.tint(Color.fromRGB(30, 26, 26).asRGB(), "eyelids");
            corpse.tint(Color.fromRGB(54, 46, 42).asRGB(), "chamber");
        }
    }

    /** Every tick: it stalks its target (with the model also: the contacts of the clip playing). */
    @Override
    public void move() {
        if (!horror.isValid()) {
            return;
        }
        if (!modelled) {
            if (target != null && target.isValid()) {
                Abyss.walk(horror, target.getLocation(), SPEED, REACH - 1);
            }
            return;
        }
        int now = fight.elapsed();
        if (swipeAt >= 0 && now >= swipeAt) {
            swipeAt = -1;
            landSwipe();
        }
        if (creakAt >= 0 && now >= creakAt) {
            creakAt = -1;
            arrive(now);
        }
        if (lungeAt >= 0 && now >= lungeAt) {
            lungeAt = -1;
            landLunge();
        }
        if (digAt >= 0 && now >= digAt) {
            digAt = -1;
            for (double[] hand : HeartwoodHorrorRig.DIG) {
                Location at = ground(point(hand));
                at.getWorld().spawnParticle(Particle.BLOCK, at.add(0, 0.2, 0), 24, 0.4, 0.2, 0.4, 0.2, Material.ROOTED_DIRT.createBlockData());
            }
        }
        if (wombAt >= 0 && now >= wombAt) {
            wombAt = -1;
            Location womb = point(HeartwoodHorrorRig.WOMB);
            womb.getWorld().spawnParticle(Particle.DUST, womb, 30, 0.6, 0.6, 0.6, 0, new Particle.DustOptions(AMBER, 1.6F));
            womb.getWorld().spawnParticle(Particle.FALLING_HONEY, womb, 16, 0.5, 0.3, 0.5, 0);
        }
        if (retintAt >= 0 && now >= retintAt) {
            retintAt = -1;
            act(state());
        }
        steer(now);
    }

    /**
     * Turns it to its target every tick (body and head: the lantern hangs from a head bone, so it stays level) and walks
     * it up to {@link #HOLD} at the walk clip's pace; it stands still while a clip plays. A move keeps the facing it
     * locked as it started.
     */
    private void steer(int now) {
        boolean live = target != null && target.isValid() && fight.players().contains(target);
        Vector facing = locked != null ? locked.clone()
            : live ? target.getLocation().toVector().subtract(horror.getLocation().toVector()).setY(0) : null;
        if (now < busyUntil || !live) {
            horror.setVelocity(new Vector(0, Math.min(0, horror.getVelocity().getY()), 0));
        } else {
            Abyss.walk(horror, target.getLocation(), MODEL_SPEED, HOLD);
        }
        if (facing != null && facing.lengthSquared() > 0.01) {
            float yaw = (float) Math.toDegrees(Math.atan2(-facing.getX(), facing.getZ()));
            horror.setRotation(yaw, 0F);
            horror.setBodyYaw(yaw);
        }
    }

    @Override
    public void tick() {
        if (!horror.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (modelled) {
            retarget(now);
        } else if (target == null || !fight.players().contains(target) || every(160)) {
            target = fight.nearestPlayer(horror.getLocation());
        }

        hearts.removeIf(heart -> !heart.isAlive());
        if (!hearts.isEmpty() && roots == null) {
            roots = AirEffects.Aura.create(fight, horror, "aura_roots", 0.02, modelled ? 4.4 : 2.4);
        } else if (hearts.isEmpty() && roots != null) {
            roots.end();
            roots = null;
        }
        boolean vulnerable = now < vulnerableUntil;
        if (hearts.isEmpty() && !vulnerable && vulnerableUntil >= 0 && now >= vulnerableUntil) {
            // the window closed: the hearts regrow
            vulnerableUntil = -1;
            if (!modelled) {
                horror.setGlowing(false);
            }
            growHearts();
            act(state());
        }
        if (vulnerable && every(10)) {
            Location at = modelled ? point(HeartwoodHorrorRig.WOMB) : horror.getLocation().add(0, 2, 0);
            horror.getWorld().spawnParticle(Particle.TRIAL_SPAWNER_DETECTION, at, 6, 0.5, 0.8, 0.5, 0.02);
        }
        if (every(20)) {   // the hearts pulse so players can find them
            for (BossFight.FightObject heart : hearts) {
                heart.location().getWorld().spawnParticle(Particle.DUST, heart.location().clone().add(0, 1.2, 0), 6, 0.2, 0.4, 0.2, 0,
                    new Particle.DustOptions(Color.fromRGB(255, 140, 40), 1.2F));
            }
        }

        if (modelled) {
            moves(now);
        } else {
            swipe(now);
            if (every(ERUPTION_INTERVAL)) {
                eruption(now);
            }
            if (every(SAP_INTERVAL)) {
                sapRain(now);
            }
            if (every(SLAM_INTERVAL)) {
                slam(now);
            }
            creak(now);
        }
        if (every(THORN_INTERVAL) && !hearts.isEmpty()) {
            thorns(now);
        }
        land(now);
    }

    // ------------------------------------------------------------------ the model: one move at a time

    /** Moves come due on their timers and start, one at a time, once nothing is playing. */
    private void moves(int now) {
        eruptionDue |= every(ERUPTION_INTERVAL);
        sapDue |= every(SAP_INTERVAL);
        slamDue |= every(SLAM_INTERVAL);
        creakDue |= every(CREAK_INTERVAL);
        if (now < busyUntil || swipeAt >= 0 || lungeAt >= 0 || creakAt >= 0) {
            return;
        }
        locked = null;
        if (staggerDue) {
            staggerDue = false;
            act("STAGGER");
            busyUntil = now + STAGGER_CLIP;
            return;
        }
        boolean live = target != null && target.isValid() && fight.players().contains(target);
        if (creakDue) {
            creakDue = false;
            creakTarget = fight.randomPlayer();
            if (creakTarget != null) {
                act("CREAK");
                creakAt = now + CREAK_CLIP;
                busyUntil = now + CREAK_CLIP + LUNGE_CLIP;
                creakTarget.playSound(creakTarget.getLocation(), Sound.ENTITY_CREAKING_AMBIENT, 2F, 0.5F);
                creakTarget.sendActionBar(ChatColor.GOLD + "Something creaks behind you...");
                return;
            }
        }
        if (slamDue && live) {
            slamDue = false;
            modelSlam(now);
            return;
        }
        if (eruptionDue && live) {
            eruptionDue = false;
            lock(target.getLocation());
            act("ERUPTION");
            busyUntil = now + ERUPTION_CLIP;
            digAt = now + HeartwoodHorrorRig.DIG_CONTACT;
            eruption(now);
            return;
        }
        if (sapDue) {
            sapDue = false;
            act("SAP");
            busyUntil = now + SAP_CLIP;
            wombAt = now + HeartwoodHorrorRig.SAP_CONTACT;
            sapRain(now);
            return;
        }
        if (live && now >= nextSwipe) {
            double distance = horizontal(target.getLocation());
            if (distance >= SWIPE_MIN && distance <= SWIPE_MAX) {
                // turned so the great hand comes down on the target, not on the line to it
                lock(target.getLocation(), HeartwoodHorrorRig.SWIPE);
                act("SWIPE");
                busyUntil = now + SWIPE_CLIP;
                swipeAt = now + HeartwoodHorrorRig.SWIPE_CONTACT;
                nextSwipe = now + SWIPE_COOLDOWN;
            }
        }
    }

    /** The great hand lands: everyone near where it comes down is caught. */
    private void landSwipe() {
        Location hand = ground(point(HeartwoodHorrorRig.SWIPE));
        for (Player player : fight.players()) {
            Vector to = player.getLocation().toVector().subtract(hand.toVector());
            double dy = to.getY();
            if (to.setY(0).length() <= SWIPE_HIT && Math.abs(dy) < 3) {
                fight.hit(player, SWIPE, horror);
                Vector push = to.lengthSquared() > 0.01 ? to.normalize().multiply(0.5) : new Vector();
                player.setVelocity(push.setY(0.3));
            }
        }
        hand.getWorld().spawnParticle(Particle.BLOCK, hand.clone().add(0, 0.2, 0), 30, 0.6, 0.15, 0.6, 0.2, Material.PALE_OAK_LOG.createBlockData());
        hand.getWorld().spawnParticle(Particle.BLOCK, hand.clone().add(0, 0.2, 0), 16, 0.6, 0.1, 0.6, 0.2, Material.ROOTED_DIRT.createBlockData());
    }

    /** The slam: the ring is centred where the crutch and the great hand will land, and erupts as they do. */
    private void modelSlam(int now) {
        lock(target.getLocation());
        act("SLAM");
        busyUntil = now + SLAM_CLIP;
        Location a = point(HeartwoodHorrorRig.SLAM[0]);
        Location b = point(HeartwoodHorrorRig.SLAM[1]);
        Location center = ground(a.add(b).multiply(0.5));
        int contact = HeartwoodHorrorRig.SLAM_CONTACT;
        fight.telegraph(center, SLAM_RADIUS, contact, ROOTS, FloorDecals.Mark.ROOTS);
        pending.add(new Pending(now + contact, SLAM, at -> horizontalSq(at, center) <= SLAM_RADIUS * SLAM_RADIUS
            && Math.abs(at.getY() - center.getY()) < 3, () -> slamEffect(center)));
    }

    /** It arrives crouched behind its prey, lights still out, and the lunge's stab lands on them. */
    private void arrive(int now) {
        Player prey = creakTarget;
        if (prey == null || !prey.isValid() || !fight.players().contains(prey)) {
            busyUntil = now;
            act(state());
            return;
        }
        double[] hand = HeartwoodHorrorRig.LUNGE;
        Vector facing = prey.getLocation().getDirection().setY(0);
        Location spot = behind(prey, facing, hand);
        if (spot == null) {
            // no room behind it: come from the middle of the circle instead
            facing = prey.getLocation().toVector().subtract(fight.center().toVector()).setY(0);
            spot = behind(prey, facing, hand);
        }
        if (spot == null) {
            spot = horror.getLocation();
            facing = prey.getLocation().toVector().subtract(spot.toVector()).setY(0);
        }
        horror.getWorld().spawnParticle(Particle.BLOCK, horror.getLocation().add(0, 1.5, 0), 40, 0.8, 1.5, 0.8, Material.PALE_OAK_LOG.createBlockData());
        horror.teleport(spot);
        locked = facing.lengthSquared() > 0.01 ? facing.normalize() : null;
        target = prey;
        act("LUNGE");
        act(state());
        lungeAt = now + HeartwoodHorrorRig.LUNGE_CONTACT;
        busyUntil = now + LUNGE_CLIP;
        nextSwipe = now + LUNGE_CLIP + SWIPE_COOLDOWN;
    }

    /**
     * Where the carrier stands so the lunge's hand ({ahead, up, right}) lands on {@code prey} while it faces
     * {@code facing}; null when that spot is outside the circle or inside a block.
     */
    @Nullable
    private Location behind(Player prey, Vector facing, double[] hand) {
        if (facing.lengthSquared() < 0.01) {
            return null;
        }
        Vector ahead = facing.clone().normalize();
        Vector right = new Vector(-ahead.getZ(), 0, ahead.getX());
        Location spot = prey.getLocation().subtract(ahead.clone().multiply(hand[0])).subtract(right.multiply(hand[2]));
        if (horizontalSq(spot, fight.center()) > (fight.radius() - 1) * (fight.radius() - 1)) {
            return null;
        }
        spot.setY(Abyss.groundY(spot));
        if (!spot.getBlock().isPassable() || !spot.clone().add(0, 1, 0).getBlock().isPassable()) {
            return null;
        }
        spot.setDirection(ahead);
        return spot;
    }

    private void landLunge() {
        Location hand = point(HeartwoodHorrorRig.LUNGE);
        for (Player player : fight.players()) {
            Vector to = player.getLocation().toVector().subtract(hand.toVector());
            double dy = player.getLocation().getY() + 1 - hand.getY();
            if (to.setY(0).length() <= LUNGE_HIT && Math.abs(dy) < 2.5) {
                fight.hit(player, LUNGE_DAMAGE, horror);
            }
        }
        hand.getWorld().spawnParticle(Particle.BLOCK, hand, 20, 0.4, 0.4, 0.4, 0.2, Material.PALE_OAK_LOG.createBlockData());
    }

    /** Locks the facing toward {@code at} for the move starting. */
    private void lock(Location at) {
        Vector to = at.toVector().subtract(horror.getLocation().toVector()).setY(0);
        locked = to.lengthSquared() > 0.01 ? to.normalize() : null;
        face();
    }

    /** Locks the facing so that the model's point {@code part} ({ahead, up, right}) lands on {@code at}. */
    private void lock(Location at, double[] part) {
        Vector to = at.toVector().subtract(horror.getLocation().toVector()).setY(0);
        if (to.lengthSquared() < 0.01) {
            locked = null;
            return;
        }
        // the part sits atan2(right, ahead) to the right of the facing: turn that much left of the target
        double turn = Math.atan2(part[2], part[0]);
        locked = to.normalize().rotateAroundY(turn);
        face();
    }

    private void face() {
        if (locked != null) {
            float yaw = (float) Math.toDegrees(Math.atan2(-locked.getX(), locked.getZ()));
            horror.setRotation(yaw, 0F);
            horror.setBodyYaw(yaw);
        }
    }

    private void act(String action) {
        if (modelled) {
            fight.playAction(horror, action);
        }
    }

    /** The tint for now: dark through the creak, vulnerable while its hearts are down, calm otherwise. */
    private String state() {
        if (creakAt >= 0) {
            return "OUT";
        }
        return fight.elapsed() < vulnerableUntil ? "VULNERABLE" : "CALM";
    }

    /**
     * Every 8-11s (or when its target is gone or out of the arena) it picks again: the top damager half the time,
     * otherwise the nearest player, so a group can trade its attention.
     */
    private void retarget(int now) {
        boolean lost = target == null || !target.isValid() || !fight.players().contains(target);
        if (!lost && now < retargetAt) {
            return;
        }
        Player next = ThreadLocalRandom.current().nextBoolean() ? fight.topDamager() : null;
        if (next == null || next == target && fight.players().size() > 1) {
            next = fight.nearestPlayer(horror.getLocation());
        }
        target = next;
        retargetAt = now + RETARGET_TICKS + ThreadLocalRandom.current().nextInt(13) * 5;
    }

    /** A point of the model ({ahead, up, right} blocks from the carrier's feet) turned with its body. */
    private Location point(double[] v) {
        Location at = horror.getLocation();
        double yaw = Math.toRadians(horror.getBodyYaw());
        Vector ahead = new Vector(-Math.sin(yaw), 0, Math.cos(yaw));
        Vector right = new Vector(-ahead.getZ(), 0, ahead.getX());
        return at.add(ahead.multiply(v[0])).add(0, v[1], 0).add(right.multiply(v[2]));
    }

    private double horizontal(Location at) {
        return Math.sqrt(horizontalSq(at, horror.getLocation()));
    }

    private static double horizontalSq(Location a, Location b) {
        double dx = a.getX() - b.getX();
        double dz = a.getZ() - b.getZ();
        return dx * dx + dz * dz;
    }

    // ------------------------------------------------------------------ attacks (the vanilla body, and shared)

    private void swipe(int now) {
        if (target == null || now < nextSwipe) {
            return;
        }
        if (target.getLocation().distanceSquared(horror.getLocation()) <= REACH * REACH) {
            nextSwipe = now + SWIPE_COOLDOWN;
            Abyss.face(horror, target.getEyeLocation());
            horror.swingMainHand();
            horror.getWorld().playSound(horror.getLocation(), Sound.ENTITY_CREAKING_ATTACK, 1.5F, 0.7F);
            fight.hit(target, SWIPE, horror);
        }
    }

    /** Three lanes of roots burst from it: toward its target and 35 degrees to either side. */
    private void eruption(int now) {
        Player aim = target != null ? target : fight.randomPlayer();
        if (aim == null) {
            return;
        }
        Location origin = ground(horror.getLocation());
        Vector toward = aim.getLocation().toVector().subtract(origin.toVector()).setY(0);
        if (toward.lengthSquared() < 0.01) {
            toward = new Vector(1, 0, 0);
        }
        toward.normalize();
        if (!modelled) {
            horror.getWorld().playSound(origin, Sound.BLOCK_ROOTS_PLACE, 2F, 0.5F);
        }
        for (double turn : new double[] { -35, 0, 35 }) {
            Vector dir = toward.clone().rotateAroundY(Math.toRadians(turn));
            FloorDecals.lane(fight, origin, dir, LANE_LENGTH, LANE_WIDTH, WARNING, ROOTS);
            pending.add(new Pending(now + WARNING, ERUPTION, at -> inLane(at, origin, dir), () -> {
                for (double t = 1; t <= LANE_LENGTH; t += 1.5) {
                    Location spot = origin.clone().add(dir.clone().multiply(t));
                    spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.4, 0), 8, 0.4, 0.4, 0.4, Material.PALE_OAK_LOG.createBlockData());
                }
                origin.getWorld().playSound(origin, Sound.BLOCK_ROOTS_BREAK, 2F, 0.6F);
            }));
        }
    }

    private static boolean inLane(Location at, Location origin, Vector dir) {
        Vector offset = at.toVector().subtract(origin.toVector()).setY(0);
        double along = offset.dot(dir);
        double across = offset.clone().subtract(dir.clone().multiply(along)).length();
        return along >= 0 && along <= LANE_LENGTH && across <= LANE_WIDTH / 2 + 0.3;
    }

    /** Sap falls on marked spots: under every player, and a few more around the circle. */
    private void sapRain(int now) {
        List<Location> spots = new ArrayList<>();
        for (Player player : fight.players()) {
            spots.add(ground(player.getLocation()));
        }
        for (int i = 0; i < 3; i++) {
            spots.add(ground(fight.randomPoint(2, fight.radius() - 2)));
        }
        fight.broadcast("&6Amber sap gathers overhead - &fmove!");
        for (Location spot : spots) {
            fight.telegraph(spot, SAP_RADIUS, WARNING + 5, AMBER);
            pending.add(new Pending(now + WARNING + 5, SAP, at -> at.distanceSquared(spot) <= SAP_RADIUS * SAP_RADIUS, () -> {
                spot.getWorld().spawnParticle(Particle.FALLING_HONEY, spot.clone().add(0, 3, 0), 30, SAP_RADIUS / 2, 0.5, SAP_RADIUS / 2, 0);
                spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.3, 0), 20, SAP_RADIUS / 2, 0.1, SAP_RADIUS / 2,
                    Material.RESIN_BLOCK.createBlockData());
                spot.getWorld().playSound(spot, Sound.BLOCK_HONEY_BLOCK_FALL, 1.5F, 0.6F);
            }));
        }
    }

    /** It stamps: a ring of roots erupts around it. */
    private void slam(int now) {
        Location center = ground(horror.getLocation());
        fight.telegraph(center, SLAM_RADIUS, WARNING, ROOTS, FloorDecals.Mark.ROOTS);
        horror.getWorld().playSound(center, Sound.ENTITY_CREAKING_ACTIVATE, 2F, 0.5F);
        pending.add(new Pending(now + WARNING, SLAM, at -> at.distanceSquared(center) <= SLAM_RADIUS * SLAM_RADIUS,
            () -> slamEffect(center)));
    }

    private void slamEffect(Location center) {
        FloorDecals.wave(fight, center, 0.5, SLAM_RADIUS, 10, ROOTS);
        AirEffects.burst(fight, center.clone().add(0, 0.8, 0), AirEffects.Burst.IMPACT, ROOTS, 5F);
        center.getWorld().spawnParticle(Particle.BLOCK, center.clone().add(0, 0.3, 0), 80, SLAM_RADIUS / 2, 0.2, SLAM_RADIUS / 2,
            Material.PALE_OAK_LOG.createBlockData());
        center.getWorld().playSound(center, Sound.ENTITY_GENERIC_EXPLODE, 1.2F, 0.5F);
    }

    /** Each standing heart pulses with thorns: breaking them is a fight of its own. */
    private void thorns(int now) {
        for (BossFight.FightObject heart : hearts) {
            Location center = ground(heart.location());
            fight.telegraph(center, THORN_RADIUS, WARNING - 5, AMBER, FloorDecals.Mark.SPIKES);
            pending.add(new Pending(now + WARNING - 5, THORNS, at -> at.distanceSquared(center) <= THORN_RADIUS * THORN_RADIUS, () -> {
                center.getWorld().spawnParticle(Particle.CRIT, center.clone().add(0, 0.8, 0), 40, THORN_RADIUS / 2, 0.5, THORN_RADIUS / 2, 0.2);
                center.getWorld().playSound(center, Sound.ENCHANT_THORNS_HIT, 1.5F, 0.6F);
            }));
        }
    }

    /** Lands every pending area hit whose time has come. */
    private void land(int now) {
        pending.removeIf(hit -> {
            if (now < hit.at()) {
                return false;
            }
            hit.effect().run();
            for (Player player : fight.players()) {
                if (hit.caught().test(player.getLocation())) {
                    fight.hit(player, hit.mechanic(), horror);
                    if (hit.mechanic() == ERUPTION || hit.mechanic() == SLAM) {
                        player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 2));
                    }
                }
            }
            return true;
        });
    }

    /** It creaks behind a player, then vanishes from where it stood and strikes from behind them. */
    private void creak(int now) {
        if (every(CREAK_INTERVAL) && creakAt < 0) {
            creakTarget = fight.randomPlayer();
            if (creakTarget != null) {
                creakAt = now + 20;
                horror.getWorld().playSound(creakTarget.getLocation(), Sound.ENTITY_CREAKING_AMBIENT, 2F, 0.5F);
                creakTarget.sendActionBar(ChatColor.GOLD + "Something creaks behind you...");
            }
        }
        if (creakAt >= 0 && now >= creakAt) {
            creakAt = -1;
            if (creakTarget != null && creakTarget.isValid() && fight.players().contains(creakTarget)) {
                lunge(creakTarget);
            }
        }
    }

    private void lunge(Player player) {
        Vector facing = player.getLocation().getDirection().setY(0);
        if (facing.lengthSquared() < 0.01) {
            facing = new Vector(1, 0, 0);
        }
        facing.normalize().multiply(-1.8);
        Location spot = player.getLocation().add(facing);
        spot.setY(Abyss.groundY(spot));
        spot.setDirection(player.getLocation().toVector().subtract(spot.toVector()));
        horror.getWorld().spawnParticle(Particle.BLOCK, horror.getLocation().add(0, 1.5, 0), 25, 0.5, 1, 0.5, Material.PALE_OAK_LOG.createBlockData());
        horror.teleport(spot);
        horror.swingMainHand();
        horror.getWorld().playSound(spot, Sound.ENTITY_CREAKING_ATTACK, 2F, 0.6F);
        fight.hit(player, LUNGE_DAMAGE, horror);
        target = player;
        nextSwipe = fight.elapsed() + SWIPE_COOLDOWN;
    }

    private static Location ground(Location at) {
        Location spot = at.clone();
        spot.setY(Abyss.groundY(at));
        return spot;
    }

    // ------------------------------------------------------------------ hearts

    private void growHearts() {
        heartsLeft = HEARTS;
        double offset = ThreadLocalRandom.current().nextDouble() * Math.PI;
        for (int i = 0; i < HEARTS; i++) {
            double angle = offset + Math.PI * 2 * i / HEARTS;
            double radius = Math.min(fight.radius() - 3, 15);
            Location at = fight.center().clone().add(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
            hearts.add(fight.spawnObject(at, Material.CREAKING_HEART, 1.2F, HEART_HITS, this::heartBroken));
        }
        fight.broadcast("&6Its hearts take root around the circle - &fbreak all four to make it bleed.");
        horror.getWorld().playSound(horror.getLocation(), Sound.BLOCK_CREAKING_HEART_SPAWN, 2F, 0.7F);
    }

    private void heartBroken() {
        int left = --heartsLeft;
        int now = fight.elapsed();
        // with the model a broken heart twitches it (only between moves: a clip never cuts into another)
        boolean free = modelled && now >= busyUntil && swipeAt < 0 && lungeAt < 0 && creakAt < 0;
        if (left > 0 && free) {
            act("TWITCH");
        } else if (left > 0 || !modelled) {
            horror.getWorld().playSound(horror.getLocation(), Sound.ENTITY_CREAKING_TWITCH, 2F, 0.7F);
        }
        if (modelled) {
            Location lantern = point(HeartwoodHorrorRig.LANTERN);
            lantern.getWorld().spawnParticle(Particle.DUST, lantern, 20, 0.4, 0.4, 0.4, 0, new Particle.DustOptions(AMBER, 1.4F));
        }
        if (left <= 0) {
            vulnerableUntil = now + VULNERABLE_TICKS;
            if (modelled) {
                // the sleeper's eyes open and the blooms go red; the stagger plays as soon as it's free
                act("VULNERABLE");
                if (free) {
                    act("STAGGER");
                    busyUntil = now + STAGGER_CLIP;
                } else {
                    staggerDue = true;
                }
            } else {
                horror.setGlowing(true);
            }
            fight.broadcast("&6The last heart breaks - &fthe Horror can be hurt for 20 seconds!");
        }
    }
}
