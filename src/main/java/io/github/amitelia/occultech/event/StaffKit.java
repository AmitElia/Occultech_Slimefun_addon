package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * One staff member's kit (Session E2): how their body moves, their melee, and their archetype's generic move. Every
 * kit has the same stats budget; they differ in how they fight. Signatures (E3-E5) come on top.
 * <p>
 * All attacks are {@link Mechanic}s graded against max-enchanted netherite ({@link RaidService#BENCHMARK_TIER}).
 * Timing is in fight ticks ({@link BossFight#elapsed()}); the kit's {@link #tick} runs every boss step, {@link #move}
 * every tick.
 */
abstract class StaffKit {

    protected final BossFight fight;
    protected final Mannequin body;
    protected final StaffMember member;
    protected final Location home;
    @Nullable protected Player target;
    protected int nextMelee;
    protected int nextSpecial;
    /** Until this fight tick the body is busy with a warned move: nothing else starts (so moves take turns). */
    protected int busyUntil;
    /** The other body of a pair (Earl + Sam), or null. */
    @Nullable StaffKit partner;
    private final List<Pending> pending = new ArrayList<>();
    private final List<Signature> signatures = new ArrayList<>();

    /** Something the kit has warned about and will do at fight tick {@code at}. */
    private record Pending(int at, Runnable action) {}

    protected StaffKit(BossFight fight, Mannequin body, StaffMember member, Location home) {
        this.fight = fight;
        this.body = body;
        this.member = member;
        this.home = home.clone();
        // staggered, so a slot full of staff doesn't open with everything at once
        this.nextSpecial = fight.elapsed() + 40 + 5 * ThreadLocalRandom.current().nextInt(12);
    }

    @Nonnull
    static StaffKit of(Archetype archetype, BossFight fight, Mannequin body, StaffMember member, Location home) {
        return switch (archetype) {
            case BRUISER -> new BruiserKit(fight, body, member, home);
            case CONTROLLER -> new ControllerKit(fight, body, member, home);
            case SKIRMISHER -> new SkirmisherKit(fight, body, member, home);
            case SUMMONER -> new SummonerKit(fight, body, member, home);
            case GADGETEER -> new GadgeteerKit(fight, body, member, home);
            case HEXER -> new HexerKit(fight, body, member, home);
        };
    }

    /** Loads every kit class, so their mechanics are declared (the balance report). */
    static void loadAll() {
        for (Class<?> kit : List.of(BruiserKit.class, ControllerKit.class, SkirmisherKit.class, SummonerKit.class, GadgeteerKit.class,
            HexerKit.class, DevSignatures.class, AbusingSignatures.class, RadioSignature.class, BuilderSignatures.class,
            SamuraiSignatures.class, SpaceSignatures.class, CowSignatures.class, PairSignatures.class, BurrowSignature.class,
            TricksterSignatures.class, CreatureSignatures.class, SpiderSignature.class, JollySignatures.class)) {
            try {
                Class.forName(kit.getName(), true, kit.getClassLoader());
            } catch (ClassNotFoundException e) {
                throw new IllegalStateException(e);
            }
        }
    }

    // ------------------------------------------------------------------ what each kit sets

    /** Walking speed (blocks per tick). */
    protected abstract double speed();

    /** How far from its target it likes to stand. */
    protected abstract double keepDistance();

    @Nonnull
    protected abstract Mechanic melee();

    /** Ticks between melee hits. */
    protected int meleeCooldown() {
        return 20;
    }

    /** The archetype's generic move, when its time comes ({@link #nextSpecial}); false if it had nothing to do. */
    protected abstract boolean special(int now);

    /** The archetype's own setup once the body is in the world (attributes, gear). */
    protected void prepareBody() {}

    /** Called once the body is in the world: the archetype's setup, then the signatures. */
    final void setup() {
        prepareBody();
        for (String id : member.signatures()) {
            Signature signature = Signature.create(id, this);
            if (signature != null) {
                signatures.add(signature);
            }
        }
    }

    /** Marks the body busy for {@code ticks} (a warned move is under way). */
    void claim(int ticks) {
        busyUntil = Math.max(busyUntil, fight.elapsed() + ticks);
    }

    /** Whether a signature is steering the body now (a vanish, a rescue dash): the kit doesn't walk or swing. */
    boolean steered() {
        for (Signature signature : signatures) {
            if (signature.steering()) {
                return true;
            }
        }
        return false;
    }

    /** The share of a hit this body takes, after its signatures (1 = all of it). */
    double incomingFactor() {
        double factor = 1;
        for (Signature signature : signatures) {
            factor *= signature.incoming();
        }
        return factor;
    }

    /** A player's hit landed on this body. */
    void onHitBy(Player player, double damage) {
        for (Signature signature : signatures) {
            signature.onHitBy(player, damage);
        }
    }

    /** One of the fight's extra creatures died. */
    void onAddDeath(org.bukkit.entity.Entity entity, @Nullable Player killer) {
        for (Signature signature : signatures) {
            signature.onAddDeath(entity, killer);
        }
    }

    /** True if a signature sidesteps this projectile. */
    boolean deflect(org.bukkit.entity.Projectile projectile) {
        for (Signature signature : signatures) {
            if (signature.deflect(projectile)) {
                return true;
            }
        }
        return false;
    }

    /** How far a ranged signature keeps the body from its target, or 0 for a melee fighter. */
    double range() {
        double range = 0;
        for (Signature signature : signatures) {
            range = Math.max(range, signature.range());
        }
        return range;
    }

    /** Below 1 the body moves and swings faster (an enraged partner); a signature sets it. */
    double paceFactor() {
        double factor = 1;
        for (Signature signature : signatures) {
            factor *= signature.pace();
        }
        return factor;
    }

    /** The signatures this kit carries (built ones only). */
    List<Signature> signatures() {
        return signatures;
    }

    // ------------------------------------------------------------------ the loop

    boolean alive() {
        return body.isValid() && !body.isDead();
    }

    void tick(int now) {
        Iterator<Pending> due = pending.iterator();
        List<Pending> ready = new ArrayList<>();
        while (due.hasNext()) {
            Pending next = due.next();
            if (now >= next.at()) {
                ready.add(next);
                due.remove();
            }
        }
        // warned moves finish (or clean up) even if the body fell meanwhile; each checks alive() before it hurts anyone
        ready.forEach(p -> p.action().run());
        if (!alive()) {
            return;
        }

        target = chooseTarget();
        if (!steered() && range() == 0 && target != null && now >= nextMelee && within(target, 3)) {
            nextMelee = now + (int) Math.round(meleeCooldown() * paceFactor());
            body.swingMainHand();
            fight.hit(target, melee(), body);
            onMeleeHit(now);
            Player hit = target;
            signatures.forEach(s -> s.onMelee(hit));
        }
        if (now < busyUntil) {
            return;
        }
        // a signature that's due goes first: they're what makes each staff member themselves
        for (Signature signature : signatures) {
            if (now >= signature.next && signature.cast(now)) {
                return;
            }
        }
        if (!steered() && range() == 0 && now >= nextSpecial && special(now)) {
            claim(30);
        }
    }

    /** Every tick: the signatures' moving parts (sweeps, rings, walls, runners), even after this body fell. */
    void moveSignatures() {
        signatures.forEach(Signature::move);
    }

    void move() {
        if (!alive() || steered() || body.isInsideVehicle()) {   // a rider goes where the mount takes them
            return;
        }
        if (fighting(target)) {
            double range = range();
            Abyss.walk(body, target.getLocation(), speed() / paceFactor(), range > 0 ? range : keepDistance());
        } else if (body.getLocation().distanceSquared(home) > 4) {
            Abyss.walk(body, home, speed() * 0.7, 0.5);
        }
    }

    /** After a melee hit lands (skirmishers back off). */
    protected void onMeleeHit(int now) {}

    @Nullable
    protected Player chooseTarget() {
        return fight.nearestPlayer(body.getLocation());
    }

    // ------------------------------------------------------------------ helpers

    /** Runs {@code action} {@code delay} fight ticks from now (after its warning). */
    protected void later(int delay, Runnable action) {
        pending.add(new Pending(fight.elapsed() + delay, action));
    }

    protected boolean fighting(@Nullable Player player) {
        return player != null && player.isOnline() && !player.isDead() && player.getGameMode() != GameMode.SPECTATOR
            && fight.inArena(player);
    }

    protected boolean within(LivingEntity other, double blocks) {
        return other.getWorld() == body.getWorld() && other.getLocation().distanceSquared(body.getLocation()) <= blocks * blocks;
    }

    /** Players inside {@code radius} of {@code at} (across the ground, and within 2.5 blocks up or down). */
    @Nonnull
    protected List<Player> playersNear(Location at, double radius) {
        List<Player> out = new ArrayList<>();
        for (Player player : fight.players()) {
            Location p = player.getLocation();
            double dx = p.getX() - at.getX();
            double dz = p.getZ() - at.getZ();
            if (dx * dx + dz * dz <= radius * radius && Math.abs(p.getY() - at.getY()) < 2.5) {
                out.add(player);
            }
        }
        return out;
    }

    /** Players within {@code width} of the segment {@code from} -> {@code to} (a beam or dash lane). */
    @Nonnull
    protected List<Player> playersAlong(Location from, Location to, double width) {
        List<Player> out = new ArrayList<>();
        Vector a = from.toVector();
        Vector ab = to.toVector().subtract(a);
        double length = ab.lengthSquared();
        for (Player player : fight.players()) {
            Vector p = player.getLocation().toVector().add(new Vector(0, 1, 0));
            double t = length == 0 ? 0 : Math.max(0, Math.min(1, p.clone().subtract(a).dot(ab) / length));
            if (a.clone().add(ab.clone().multiply(t)).distanceSquared(p) <= width * width) {
                out.add(player);
            }
        }
        return out;
    }

    /**
     * Warns of a lane on the floor from {@code from} to {@code to}, {@code width} wide, for {@code ticks}: the pack's lane
     * marking (its fill reaches the end as the hit lands), or, without the pack, a dotted line redrawn meanwhile.
     */
    protected void warnLane(Location from, Location to, double width, int ticks, Color color) {
        if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            org.bukkit.util.Vector dir = to.toVector().subtract(from.toVector()).setY(0);
            if (dir.lengthSquared() > 0.01) {
                io.github.amitelia.occultech.boss.FloorDecals.lane(fight, from, dir, dir.length(), width, ticks, color);
            }
            return;
        }
        for (int t = 0; t < ticks; t += 5) {
            later(t, () -> drawLine(from.clone().add(0, 0.15, 0), to.clone().add(0, 0.15, 0), color, 0.4));
        }
    }

    /**
     * Warns of a fan on the floor from {@code origin}, centred on {@code aim} (radians, atan2 of z and x),
     * {@code arc} wide (radians), {@code range} long: the pack's true sector, which traces the hit exactly. False without
     * the pack (the caller draws its particles).
     */
    protected boolean warnFan(Location origin, double aim, double arc, double range, int ticks, Color color) {
        if (!io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            return false;
        }
        io.github.amitelia.occultech.boss.FloorDecals.sector(fight, origin, new org.bukkit.util.Vector(Math.cos(aim), 0, Math.sin(aim)), range, Math.toDegrees(arc), ticks, color);
        return true;
    }

    /**
     * Players standing in a floor lane from {@code from} to {@code to}, {@code halfWidth} either side of its line, measured
     * across the ground (within 2.5 blocks up or down) - exactly what {@link #warnLane} draws.
     */
    @Nonnull
    protected List<Player> playersInLane(Location from, Location to, double halfWidth) {
        List<Player> out = new ArrayList<>();
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            double[] off = RaidGeometry.fromWall(at.getX(), at.getZ(), from.getX(), from.getZ(), to.getX(), to.getZ());
            if (off[0] <= halfWidth && Math.abs(at.getY() - from.getY()) < 2.5) {
                out.add(player);
            }
        }
        return out;
    }

    /** A dotted warning line on the floor from {@code from} to {@code to}. */
    protected void drawLine(Location from, Location to, Color color, double step) {
        Particle.DustOptions dust = new Particle.DustOptions(color, 1.3F);
        Vector ab = to.toVector().subtract(from.toVector());
        double length = ab.length();
        if (length < 0.01) {
            return;
        }
        ab.normalize();
        for (double d = 0; d <= length; d += step) {
            Location at = from.clone().add(ab.clone().multiply(d));
            at.getWorld().spawnParticle(Particle.DUST, at, 1, 0.05, 0.02, 0.05, 0, dust);
        }
    }

    /** A point {@code length} blocks from {@code from} toward {@code toward}, at {@code from}'s height. */
    @Nonnull
    protected static Location lane(Location from, Location toward, double length) {
        Vector flat = toward.toVector().subtract(from.toVector()).setY(0);
        if (flat.lengthSquared() < 0.01) {
            flat = from.getDirection().setY(0);
        }
        return from.clone().add(flat.normalize().multiply(length));
    }

    /** Knocks {@code player} away from {@code from}. */
    protected static void knock(Player player, Location from, double strength, double up) {
        Vector away = player.getLocation().toVector().subtract(from.toVector()).setY(0);
        if (away.lengthSquared() < 0.01) {
            away = new Vector(0, 0, 1);
        }
        player.setVelocity(away.normalize().multiply(strength).setY(up));
    }
}
