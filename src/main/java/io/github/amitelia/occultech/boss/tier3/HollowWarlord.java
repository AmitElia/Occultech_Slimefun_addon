package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;

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
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.WitherSkeleton;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.AirEffects;
import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.Prop;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Tier-3 mini-boss (Infinity gear). The Headsman: a giant wither skeleton in battered blackstone plate with an
 * executioner's sword, three taken skulls floating over his head - one for each of his warband.
 * <ul>
 * <li>Soul sweep: a ring warns for 1s while he draws the blade far back, then the whirl cuts everyone close - heavy
 * damage and Wither.</li>
 * <li>The chop: up close he raises the sword into a high guard and brings it straight down in front of him; it bites a
 * strip of floor 6 blocks long. Step aside while it's raised.</li>
 * <li>Warband: three guards join at the start and every 25s (capped), each bound to one of the skulls - the skull's fire
 * burns while its guard stands. While two or more stand, the Warlord takes half damage - shown by soul chains from the
 * skulls to the guards. Kill the guards, then the Warlord.</li>
 * <li>Below 35% he drives the sword into the floor and roars: faster, sweeping more often, eyes white-hot.</li>
 * </ul>
 * Health attributes cap at 1024, so it takes about a fifth of the damage dealt (~2200 effective health solo).
 * The look comes from the Mythic body (Mobs/Skills HollowWarlord.yml, model occultech_hollow_warlord): each clip starts
 * early enough to land on the server's moment (the sweep's contact 0.3 s in, the chop's 0.72 s, the call's 0.9 s, the
 * enrage's slam 1.05 s). Without Mythic the fight plays as before on a scaled vanilla wither skeleton.
 */
public final class HollowWarlord extends BossBehavior {

    private static final Mechanic GUARD = Mechanic.of("HOLLOW_WARLORD", "Guard", 30, Mechanic.Kind.ADD, false);

    /** The soul chains to the guards shielding it, drawn in the air (Session O5). */
    private final java.util.Map<WitherSkeleton, AirEffects.Streak> chains = new java.util.HashMap<>();
    /** The soul halo over it while its guards shield it. */
    @Nullable private AirEffects.Aura halo;

    private static final double HEALTH = 330;
    /** It re-picks its target this often (ticks, randomised up to +60): vanilla AI kept one target forever. */
    private static final int RETARGET_TICKS = 120;
    private static final double ARMOR = 0.18;
    private static final double GUARDED = 0.6;
    private static final Mechanic BLADE = Mechanic.of("HOLLOW_WARLORD", "Blade", 46, Mechanic.Kind.MELEE, false);
    private static final Mechanic CHOP = Mechanic.of("HOLLOW_WARLORD", "Chop", 46, Mechanic.Kind.MELEE, true);
    private static final Mechanic SWEEP_DAMAGE = Mechanic.of("HOLLOW_WARLORD", "Soul sweep", 62, Mechanic.Kind.AREA, true);
    private static final double SWEEP_RADIUS = 4.5;
    private static final int SWEEP_INTERVAL = 120;
    private static final int GUARD_INTERVAL = 500;
    private static final Color SOUL = Color.fromRGB(60, 200, 220);
    private static final Color SOUL_FIRE = Color.fromRGB(92, 232, 240);

    // ---- the model's timing (session 7 clips, in ticks) ----
    /** The windup clip is the sweep's 1 s warning; the sweep clip then cuts 0.3 s in. */
    private static final int WINDUP_CLIP = 20;
    private static final int SWEEP_CONTACT = 6;
    private static final int SWEEP_HOLD = 30;
    /** The chop: raised, held, down at 0.72 s; the clip is 1.5 s. */
    private static final int CHOP_CONTACT = 14;
    private static final int CHOP_CLIP = 30;
    private static final int CHOP_COOLDOWN = 44;
    /** He stops this far from his target and chops from there (blocks, horizontal from his feet). */
    private static final double HOLD = 3.6;
    private static final double CHOP_REACH = 5.0;
    private static final double CHOP_LENGTH = 6.2;
    private static final double CHOP_HALF_WIDTH = 1.3;
    private static final int CALL_CONTACT = 18;
    private static final int CALL_CLIP = 44;
    private static final int ENRAGE_SLAM = 21;
    private static final int ENRAGE_CLIP = 48;
    private static final int SPAWN_CLIP = 68;
    /** BetterModel's hit flash restores the tint it found, so the state tints are put back after it. */
    private static final int RETINT_AFTER = 12;
    private static final int FLINCH_COOLDOWN = 20;
    private static final int DEAD = Color.fromRGB(40, 44, 44).asRGB();
    /** Speed through the walk clip's stride (1.6 s a cycle), up to 30% faster as he weakens. */
    private static final double MODEL_SPEED = 0.26;

    private WitherSkeleton warlord;
    /** Each guard is bound to one skull: centre, left, right. */
    private final WitherSkeleton[] guards = new WitherSkeleton[3];
    private final boolean[] lit = {false, false, false};
    private int sweepAt = -1;
    private boolean enraged;
    private int retargetAt;

    // ---- model only ----
    private boolean modelled;
    private int busyUntil;
    private int sweepClipAt = -1;
    private int sweepEndsAt = -1;
    private int chopAt = -1;
    private Vector chopDirection;
    private int nextChop;
    private boolean callDue;
    private int callAt = -1;
    private int slamAt = -1;
    private int retintAt = -1;
    private int flinchReady;

    public HollowWarlord(BossFight fight) {
        super(fight);
    }

    /** With the model he chops from his own reach (see {@link #chop}); the vanilla body keeps vanilla melee. */
    @Override
    public boolean vanillaMelee() {
        return !modelled;
    }

    @Override
    public void spawn(Location at) {
        modelled = fight.usesMythicBody();
        warlord = fight.spawnBoss(WitherSkeleton.class, at.clone().add(0, 1, 0), w -> {
            w.setCustomName(ChatColor.DARK_GRAY + "Hollow Warlord");
            w.setCustomNameVisible(true);
            BossFight.setAttribute(w, Attribute.MAX_HEALTH, HEALTH);
            fight.label(w, BLADE);
            BossFight.setAttribute(w, Attribute.FOLLOW_RANGE, 48);
            BossFight.setAttribute(w, Attribute.KNOCKBACK_RESISTANCE, 1);
        });
        if (modelled) {
            // the model draws him, his plate and his sword: the invisible carrier holds and wears nothing, unscaled
            warlord.getEquipment().clear();
        } else {
            warlord.getEquipment().setItemInMainHand(new ItemStack(Material.NETHERITE_SWORD));
            warlord.getEquipment().setHelmet(new ItemStack(Material.NETHERITE_HELMET));
            warlord.getEquipment().setChestplate(new ItemStack(Material.NETHERITE_CHESTPLATE));
            warlord.getEquipment().setLeggings(new ItemStack(Material.NETHERITE_LEGGINGS));
            warlord.getEquipment().setBoots(new ItemStack(Material.NETHERITE_BOOTS));
            BossFight.setAttribute(warlord, Attribute.SCALE, 1.8);
        }
        busyUntil = fight.elapsed() + (modelled ? SPAWN_CLIP : 0);
        nextChop = busyUntil;
        spawnWarband(null);
        skullTints(true);
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR * (liveGuards() >= 2 ? GUARDED : 1);
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (!modelled || boss != warlord) {
            return;
        }
        int now = fight.elapsed();
        retintAt = now + RETINT_AFTER;
        if (now >= busyUntil && now >= flinchReady) {
            flinchReady = now + FLINCH_COOLDOWN;
            act("FLINCH");
        }
    }

    /** The model stays for its whole death clip, every fire out. */
    @Override
    public void onBossDeath(LivingEntity boss) {
        if (!modelled || boss != warlord) {
            return;
        }
        Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(DEAD, "eyes", "brand", "soul_c", "soul_l", "soul_r");
        }
    }

    // ---- every tick: the clips' contacts, and (model) steering and gaze -------------------------------------------------

    @Override
    public void move() {
        if (warlord == null || !warlord.isValid() || !modelled) {
            return;
        }
        int now = fight.elapsed();
        if (sweepClipAt >= 0 && now >= sweepClipAt) {
            sweepClipAt = -1;
            act("SWEEP");
        }
        if (sweepAt >= 0 && now >= sweepAt) {
            sweepAt = -1;
            sweep();
        }
        if (sweepEndsAt >= 0 && now >= sweepEndsAt) {
            sweepEndsAt = -1;
            act(hisState());
        }
        if (chopAt >= 0 && now >= chopAt) {
            chopAt = -1;
            landChop();
        }
        if (callAt >= 0 && now >= callAt) {
            callAt = -1;
            spawnWarband(point(HollowWarlordRig.PLANT));
        }
        if (slamAt >= 0 && now >= slamAt) {
            slamAt = -1;
            slam();
        }
        if (retintAt >= 0 && now >= retintAt) {
            retintAt = -1;
            act(hisState());
            skullTints(true);
        }
        steer(now);
    }

    /**
     * Turns him to his target every tick (body and head: the model's head follows the carrier's) and walks him up to
     * arm's length; he stands still while a clip plays. Through the chop he keeps the facing he raised the sword on.
     */
    private void steer(int now) {
        Player target = warlord.getTarget() instanceof Player p && fight.players().contains(p) ? p : null;
        Vector facing = chopAt >= 0 && chopDirection != null ? chopDirection.clone()
            : target != null ? target.getLocation().toVector().subtract(warlord.getLocation().toVector()).setY(0) : null;
        if (facing != null && facing.lengthSquared() > 0.01) {
            float yaw = (float) Math.toDegrees(Math.atan2(-facing.getX(), facing.getZ()));
            warlord.setBodyYaw(yaw);
            warlord.setRotation(yaw, 0F);
        }
        boolean busy = now < busyUntil || sweepAt >= 0 || chopAt >= 0;
        if (busy || target == null) {
            warlord.getPathfinder().stopPathfinding();
            warlord.setVelocity(new Vector(0, Math.min(0, warlord.getVelocity().getY()), 0));
            return;
        }
        if (horizontal(target) > HOLD) {
            warlord.getPathfinder().moveTo(target.getLocation(), 1.0);
        } else {
            warlord.getPathfinder().stopPathfinding();
        }
    }

    @Override
    public void tick() {
        if (!warlord.isValid()) {
            return;
        }
        int now = fight.elapsed();
        retarget(now);
        skullTints(false);

        // faster as it weakens: up to +50% speed (the model's stride, up to +30%)
        double speed = modelled ? MODEL_SPEED * (1 + 0.3 * (1 - fight.healthFraction()))
            : 0.25 * (1 + 0.5 * (1 - fight.healthFraction()));
        BossFight.setAttribute(warlord, Attribute.MOVEMENT_SPEED, speed);
        if (!enraged && fight.healthFraction() < 0.35) {
            enraged = true;
            fight.broadcast("&8The Warlord's blade drinks the dark - &fit hunts faster!");
            if (modelled) {
                // the enrage interrupts nothing that has a warning out: it waits for a free moment (below)
                enrageDue = true;
            }
        }
        if (modelled && enrageDue && free(now)) {
            enrageDue = false;
            act("ENRAGE");
            busyUntil = now + ENRAGE_CLIP;
            slamAt = now + ENRAGE_SLAM;
        }

        if (every(GUARD_INTERVAL)) {
            if (modelled) {
                callDue = true;
            } else {
                spawnWarband(null);
            }
        }
        if (callDue && free(now)) {
            callDue = false;
            act("CALL");
            busyUntil = now + CALL_CLIP;
            callAt = now + CALL_CONTACT;
        }
        chainsAndHalo();

        if (every(enraged ? 80 : SWEEP_INTERVAL)) {
            sweepDue = true;
        }
        // with the model a sweep waits for the clip playing to end (a call or the enrage), never cutting into it
        if (sweepDue && sweepAt < 0 && (!modelled || free(now))) {
            sweepDue = false;
            Location ground = warlord.getLocation();
            ground.setY(Abyss.groundY(ground));
            if (modelled) {
                // the windup clip is the warning; the sweep clip follows and cuts on its contact
                chopAt = -1;
                sweepClipAt = now + WINDUP_CLIP;
                sweepAt = now + WINDUP_CLIP + SWEEP_CONTACT;
                sweepEndsAt = sweepAt + 10;
                busyUntil = Math.max(busyUntil, now + WINDUP_CLIP + SWEEP_HOLD);
                fight.telegraph(ground, SWEEP_RADIUS, WINDUP_CLIP + SWEEP_CONTACT, Color.fromRGB(40, 40, 40), FloorDecals.Mark.SWEEP);
                act("WINDUP");
            } else {
                sweepAt = now + 20;
                fight.telegraph(ground, SWEEP_RADIUS, 25, Color.fromRGB(40, 40, 40), FloorDecals.Mark.SWEEP);
                warlord.getWorld().playSound(warlord.getLocation(), Sound.ENTITY_WITHER_SKELETON_AMBIENT, 2F, 0.5F);
            }
        }
        if (!modelled && sweepAt >= 0 && now >= sweepAt) {
            sweepAt = -1;
            sweep();
        }
        if (modelled && free(now) && now >= nextChop && warlord.getTarget() instanceof Player target
            && fight.players().contains(target) && horizontal(target) <= CHOP_REACH) {
            chop(target, now);
        }
    }

    private boolean enrageDue;
    private boolean sweepDue;

    /** Nothing playing and no warning out: a new move may start. */
    private boolean free(int now) {
        return now >= busyUntil && sweepAt < 0 && chopAt < 0 && callAt < 0 && slamAt < 0;
    }

    private void act(String action) {
        if (modelled) {
            fight.playAction(warlord, action);
        }
    }

    private String hisState() {
        if (sweepAt >= 0) {
            return "TELL";
        }
        return enraged && !enrageDue ? "ENRAGED" : "CALM";
    }

    /** Each skull's fire follows its guard: lit while it stands, out once it falls (all at once when {@code force}). */
    private void skullTints(boolean force) {
        String[] keys = {"C", "L", "R"};
        for (int i = 0; i < 3; i++) {
            boolean alive = guards[i] != null && guards[i].isValid() && !guards[i].isDead();
            if (force || alive != lit[i]) {
                lit[i] = alive;
                act("SOUL_" + keys[i] + (alive ? "_LIT" : "_DARK"));
            }
        }
    }

    /**
     * Every 6-9s (or when its target is gone or out of the arena) it picks again: the top damager half the time - it
     * goes for whoever hurts it most - otherwise the nearest player, so a group can trade its attention.
     */
    private void retarget(int now) {
        LivingEntity current = warlord.getTarget();
        boolean lost = !(current instanceof Player p) || !fight.players().contains(p);
        if (!lost && now < retargetAt) {
            return;
        }
        Player next = ThreadLocalRandom.current().nextBoolean() ? fight.topDamager() : null;
        if (next == null || next == current && fight.players().size() > 1) {
            next = fight.nearestPlayer(warlord.getLocation());
        }
        warlord.setTarget(next);
        retargetAt = now + RETARGET_TICKS + ThreadLocalRandom.current().nextInt(13) * 5;
    }

    private double horizontal(LivingEntity other) {
        return other.getLocation().toVector().subtract(warlord.getLocation().toVector()).setY(0).length();
    }

    /** A point of the model ({ahead, up, right} blocks from the carrier's feet) turned with his body. */
    private Location point(double[] v) {
        Location at = warlord.getLocation();
        double yaw = Math.toRadians(warlord.getBodyYaw());
        Vector ahead = new Vector(-Math.sin(yaw), 0, Math.cos(yaw));
        Vector right = new Vector(-ahead.getZ(), 0, ahead.getX());
        return at.add(ahead.multiply(v[0])).add(0, v[1], 0).add(right.multiply(v[2]));
    }

    // ---- the moves --------------------------------------------------------------------------------------------------------

    /** The chop (model): raised into the high guard now, down on its contact; the facing is locked as it starts. */
    private void chop(Player target, int now) {
        chopDirection = target.getLocation().toVector().subtract(warlord.getLocation().toVector()).setY(0);
        if (chopDirection.lengthSquared() < 0.01) {
            chopDirection = warlord.getLocation().getDirection().setY(0);
        }
        chopDirection.normalize();
        chopAt = now + CHOP_CONTACT;
        busyUntil = now + CHOP_CLIP;
        nextChop = now + (enraged ? CHOP_COOLDOWN - 10 : CHOP_COOLDOWN);
        act("ATTACK");
    }

    /** Everyone on the strip of floor the blade comes down on (it bites from his feet out to the blade's end). */
    private void landChop() {
        if (chopDirection == null) {
            return;
        }
        Location at = warlord.getLocation();
        Vector side = new Vector(-chopDirection.getZ(), 0, chopDirection.getX());
        for (Player player : fight.players()) {
            Vector to = player.getLocation().toVector().subtract(at.toVector());
            double dy = to.getY();
            to.setY(0);
            double along = to.dot(chopDirection);
            if (along > 0.3 && along <= CHOP_LENGTH && Math.abs(to.dot(side)) <= CHOP_HALF_WIDTH && Math.abs(dy) < 3) {
                fight.hit(player, CHOP, warlord);
                player.setVelocity(chopDirection.clone().multiply(0.6).setY(0.35));
            }
        }
        Location bite = point(HollowWarlordRig.CHOP);
        bite.setY(Abyss.groundY(bite) + 0.1);
        bite.getWorld().spawnParticle(Particle.BLOCK, bite, 40, 0.5, 0.1, 0.5, 0.2, Material.BLACKSTONE.createBlockData());
        bite.getWorld().spawnParticle(Particle.SOUL_FIRE_FLAME, bite, 14, 0.4, 0.1, 0.4, 0.04);
        for (double d = 1; d <= CHOP_LENGTH; d += 0.8) {
            Location crack = at.clone().add(chopDirection.clone().multiply(d));
            crack.setY(Abyss.groundY(crack) + 0.1);
            crack.getWorld().spawnParticle(Particle.SOUL, crack, 2, 0.2, 0.05, 0.2, 0.01);
        }
    }

    private void sweep() {
        Location at = warlord.getLocation();
        if (!modelled) {
            warlord.swingMainHand();
            at.getWorld().playSound(at, Sound.ENTITY_PLAYER_ATTACK_SWEEP, 2F, 0.6F);
        }
        AirEffects.burst(fight, at.clone().add(0, modelled ? 2.4 : 1.3, 0), AirEffects.Burst.SLASH, SOUL, (float) (SWEEP_RADIUS * 2));
        for (int i = 0; i < 24; i++) {
            double angle = Math.PI * 2 * i / 24;
            at.getWorld().spawnParticle(Particle.SWEEP_ATTACK, at.clone().add(Math.cos(angle) * 3, modelled ? 2.2 : 1, Math.sin(angle) * 3), 1);
        }
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= SWEEP_RADIUS * SWEEP_RADIUS) {
                fight.hit(player, SWEEP_DAMAGE, warlord);
                player.addPotionEffect(new PotionEffect(PotionEffectType.WITHER, 100, 1));
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.8).setY(0.3));
                }
            }
        }
    }

    /** The enrage's slam: the sword driven into the floor in front of him (look only: it hurts nobody). */
    private void slam() {
        Location bite = point(HollowWarlordRig.SLAM);
        bite.setY(Abyss.groundY(bite) + 0.1);
        bite.getWorld().spawnParticle(Particle.BLOCK, bite, 60, 0.8, 0.1, 0.8, 0.3, Material.BLACKSTONE.createBlockData());
        bite.getWorld().spawnParticle(Particle.SOUL_FIRE_FLAME, bite, 40, 1.2, 0.2, 1.2, 0.08);
        bite.getWorld().spawnParticle(Particle.SOUL, bite.clone().add(0, 0.5, 0), 30, 2.0, 0.3, 2.0, 0.04);
        AirEffects.burst(fight, bite.clone().add(0, 0.3, 0), AirEffects.Burst.SLASH, SOUL_FIRE, 6F);
    }

    /** The guards answer: up to three, each bound to a free skull; with the model they rise round the planted sword. */
    private void spawnWarband(@Nullable Location from) {
        for (int i = 0; i < 3; i++) {
            if (guards[i] != null && guards[i].isValid() && !guards[i].isDead()) {
                continue;
            }
            WitherSkeleton guard = fight.spawnAdd(WitherSkeleton.class, fight.randomPoint(3, 8).add(0, 1, 0), g -> {
                g.getEquipment().setItemInMainHand(new ItemStack(Material.STONE_SWORD));
                g.getEquipment().setHelmet(new ItemStack(Material.CHAINMAIL_HELMET));
                BossFight.setAttribute(g, Attribute.MAX_HEALTH, 60);
                g.setHealth(60);
                fight.label(g, GUARD);
            });
            guards[i] = guard;
            if (guard != null) {
                guard.setTarget(fight.randomPlayer());
                guard.getWorld().spawnParticle(Particle.SOUL, guard.getLocation().add(0, 1, 0), 16, 0.3, 0.6, 0.3, 0.03);
            }
        }
        if (from != null) {
            from.setY(Abyss.groundY(from) + 0.1);
            from.getWorld().spawnParticle(Particle.SOUL_FIRE_FLAME, from, 30, 0.8, 0.1, 0.8, 0.06);
            from.getWorld().spawnParticle(Particle.SOUL, from.clone().add(0, 0.4, 0), 24, 1.6, 0.2, 1.6, 0.03);
        }
        skullTints(false);
        fight.broadcast("&8The warband answers its Warlord - &fcut them down to break its guard.");
    }

    /** Soul chains from the skulls (the carrier, without the model) to each living guard while two or more shield him. */
    private void chainsAndHalo() {
        boolean bound = liveGuards() >= 2;
        if (bound && halo == null) {
            // over the skulls with the model (the carrier is a normal-size wither skeleton under it)
            halo = modelled ? AirEffects.Aura.create(fight, warlord, "aura_soul_halo", 3.2, 5.0)
                : AirEffects.Aura.create(fight, warlord, "aura_soul_halo", 1.04, 1.5);
        } else if (!bound && halo != null) {
            halo.end();
            halo = null;
        }
        if (AirEffects.enabled()) {
            // a chain snaps when its guard dies or the shield breaks (Session O5)
            chains.entrySet().removeIf(entry -> {
                boolean keep = bound && entry.getKey().isValid() && !entry.getKey().isDead() && entry.getValue().valid();
                if (!keep) {
                    entry.getValue().snap();
                }
                return !keep;
            });
            if (bound) {
                for (int i = 0; i < 3; i++) {
                    WitherSkeleton guard = guards[i];
                    if (guard == null || !guard.isValid() || guard.isDead()) {
                        continue;
                    }
                    Location from = modelled ? point(HollowWarlordRig.SKULLS[i]) : warlord.getLocation().add(0, 2, 0);
                    Location to = guard.getLocation().add(0, 1.2, 0);
                    AirEffects.Streak chain = chains.get(guard);
                    if (chain == null) {
                        chains.put(guard, AirEffects.Streak.create(fight, "air_chain", from, to, SOUL, 0.45F));
                    } else {
                        chain.aim(from, to, 0.45F, BossService.STEP);
                    }
                }
            }
        } else if (bound && every(10)) {
            for (int i = 0; i < 3; i++) {
                WitherSkeleton guard = guards[i];
                if (guard != null && guard.isValid() && !guard.isDead()) {
                    Location from = modelled ? point(HollowWarlordRig.SKULLS[i]) : warlord.getLocation().add(0, 2, 0);
                    Abyss.line(from, guard.getLocation().add(0, 1.2, 0), new Particle.DustOptions(SOUL, 0.6F), 0.7);
                }
            }
        }
    }

    private int liveGuards() {
        int count = 0;
        for (WitherSkeleton guard : guards) {
            if (guard != null && guard.isValid() && !guard.isDead()) {
                count++;
            }
        }
        return count;
    }
}
