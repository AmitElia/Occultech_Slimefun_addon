package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.BooleanSupplier;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Location;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossBlueprint;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Act 2, the Council (Session E7): X (the Founder, a giant), Chlo (an archer in the air) and Pancake (the brewer) in one
 * fight with <b>one shared health pool</b>. A hit on any of them comes off the pool, every body always shows the pool's
 * share of health, and when it runs out all three fall together. The pool can be far bigger than an entity's health
 * cap: the bodies only show it.
 * <p>
 * The conductor runs the raid mechanics (soak circles, markers, barriers, lasers, rings) at the pace of the bar
 * ({@link RaidPace}): as many at once as the band allows, cooldowns shrinking as the bar falls, a soft enrage after 15
 * minutes. Each member also has attacks of their own on their own cooldowns.
 */
public final class CouncilBehavior extends BossBehavior {

    public static final String ID = "RAID_COUNCIL";
    /** A body's health attribute: it only shows the pool's share. */
    static final double BODY_HEALTH = 1000;
    private static final int MAJOR_EVERY = 160;

    /** Who plays a seat on the Council (config {@code raid.council}). */
    public record Seat(@Nonnull String name, @Nonnull String display, @Nonnull String title) {}

    /** The three seats. */
    public record Cast(@Nonnull Seat founder, @Nonnull Seat archer, @Nonnull Seat brewer) {}

    /** A hazard under way; majors count toward the pace's overlap. */
    private record Tracked(RaidHazard hazard, boolean major) {}

    private record Pending(int at, Runnable action) {}

    private final Cast cast;
    /** A player count to size the raid mechanics for when more than are really there (testing 25-player density alone). */
    private final int crowd;
    private double poolMax;
    private double pool;
    private final List<CouncilMember> members = new ArrayList<>();
    private final List<Tracked> hazards = new ArrayList<>();
    private final List<Pending> pending = new ArrayList<>();
    private final List<BooleanSupplier> rotation = new ArrayList<>();
    /** Players thrown or carried into the air, and the fight tick they're safe to pick again. */
    private final Map<UUID, Integer> airborne = new HashMap<>();
    private RaidPace pace = RaidPace.of(1, 0);
    private int nextMajor = 60;
    private int turn;
    private int majorsLaunched;
    Founder founder;
    Archer archer;
    Brewer brewer;

    CouncilBehavior(BossFight fight, Cast cast, double pool, int crowd) {
        super(fight);
        this.cast = cast;
        this.crowd = crowd;
        this.poolMax = Math.max(1, pool);
        this.pool = this.poolMax;
    }

    @Nonnull
    static BossSpec spec(double radius) {
        return new BossSpec(ID, "The Council", RaidService.BENCHMARK_TIER, true, "", 0, radius, 3600, Map.of(), Map.of(), 0);
    }

    @Nonnull
    static BossBlueprint blueprint(Cast cast, double pool, int crowd) {
        return new BossBlueprint(ID, CouncilBehavior.class, fight -> new CouncilBehavior(fight, cast, pool, crowd));
    }

    /** The players the raid mechanics are sized for: everyone in the arena, or the test crowd if that's more. */
    int crowd() {
        return Math.max(fight.players().size(), crowd);
    }

    /** Admin/test: the bar jumps to {@code share} of the pool (to try a later pace band). */
    public void setShare(double share) {
        pool = poolMax * Math.max(0.01, Math.min(1, share));
        for (CouncilMember member : members) {
            if (member.alive()) {
                member.body.setHealth(Math.max(0.5, poolFraction() * BODY_HEALTH));
            }
        }
    }

    /** The pace band now, 0-2 (self-test). */
    public int paceBand() {
        return pace.band();
    }

    @Override
    public void spawn(Location at) {
        double radius = fight.radius();
        founder = new Founder(this, at.clone(), cast.founder());
        archer = new Archer(this, at.clone().add(radius * 0.3, 0, 0), cast.archer());
        brewer = new Brewer(this, at.clone().add(-radius * 0.3, 0, radius * 0.2), cast.brewer());
        members.addAll(List.of(founder, archer, brewer));
        for (CouncilMember member : members) {
            rotation.addAll(member.majors());
        }
        Collections.shuffle(rotation);
        fight.broadcast("&6&lThe Council convenes: &f" + cast.founder().display() + ", " + cast.archer().display() + " &6and &f"
            + cast.brewer().display() + "&6. One bar, three of them.");
    }

    // ------------------------------------------------------------------ the shared pool

    /** The share of the pool left. */
    public double poolFraction() {
        return pool / poolMax;
    }

    /**
     * Takes {@code amount} off the pool for a hit on {@code hit}; every other body is set to the pool's share now, and the
     * return is what the hit body itself must lose to match. At zero every body falls.
     */
    double absorb(LivingEntity hit, double amount) {
        pool = Math.max(0, pool - amount);
        double fraction = poolFraction();
        for (CouncilMember member : members) {
            if (member.body != hit && member.alive()) {
                member.body.setHealth(fraction <= 0 ? 0 : Math.max(0.5, fraction * BODY_HEALTH));
            }
        }
        double target = fraction <= 0 ? 0 : Math.max(0.5, fraction * BODY_HEALTH);
        return Math.max(0, hit.getHealth() - target);
    }

    /** Self-test: a hit of {@code amount} on {@code body}, as a player's hit would land. */
    public void strike(LivingEntity body, double amount) {
        double loss = absorb(body, amount);
        body.setHealth(Math.max(0, body.getHealth() - loss));
    }

    /** Heals the pool by {@code share} of its size (Pancake's drink). */
    void heal(double share) {
        pool = Math.min(poolMax, pool + poolMax * share);
        for (CouncilMember member : members) {
            if (member.alive()) {
                member.body.setHealth(Math.max(0.5, poolFraction() * BODY_HEALTH));
            }
        }
    }

    /** The admin changed {@code event hp}: the pool grows or shrinks, keeping its share. */
    void rescale(double newPool) {
        double fraction = poolFraction();
        poolMax = Math.max(1, newPool);
        pool = poolMax * fraction;
    }

    double poolMax() {
        return poolMax;
    }

    /** The pool's full size (self-test). */
    public double poolSize() {
        return poolMax;
    }

    @Nullable
    private CouncilMember memberOf(LivingEntity body) {
        for (CouncilMember member : members) {
            if (member.body == body) {
                return member;
            }
        }
        return null;
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        CouncilMember member = memberOf(boss);
        return absorb(boss, damage * (member == null ? 1 : member.incoming()));
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        CouncilMember member = memberOf(boss);
        if (member != null) {
            member.onHitBy(player, damage);
        }
    }

    // ------------------------------------------------------------------ the conductor

    @Override
    public void tick() {
        int now = fight.elapsed();
        pace = RaidPace.of(poolFraction(), now);
        List<Pending> ready = new ArrayList<>();
        for (Iterator<Pending> it = pending.iterator(); it.hasNext();) {
            Pending next = it.next();
            if (now >= next.at()) {
                ready.add(next);
                it.remove();
            }
        }
        ready.forEach(p -> p.action().run());
        airborne.values().removeIf(until -> now >= until);
        for (CouncilMember member : members) {
            if (member.alive()) {
                member.tick(now);
            }
        }
        if (now >= nextMajor && majors() < pace.overlap() && !rotation.isEmpty()) {
            for (int tries = 0; tries < rotation.size(); tries++) {
                if (rotation.get(turn++ % rotation.size()).getAsBoolean()) {
                    majorsLaunched++;
                    break;
                }
            }
            nextMajor = now + pace.cooldown(MAJOR_EVERY);
        }
    }

    @Override
    public void move() {
        for (CouncilMember member : members) {
            if (member.alive()) {
                member.move();
            }
        }
        hazards.removeIf(tracked -> !tracked.hazard().step());
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double verticalLeash() {
        return 24;   // Chlo flies, and carries people up
    }

    // ------------------------------------------------------------------ for the members

    RaidPace pace() {
        return pace;
    }

    BossFight fight() {
        return fight;
    }

    /** {@code mechanic} at the pace's damage (above 1 only once enraged). */
    Mechanic scaled(Mechanic mechanic) {
        return pace.damageFactor() > 1 ? mechanic.scaled(pace.damageFactor()) : mechanic;
    }

    void hit(Player player, Mechanic mechanic, LivingEntity source) {
        fight.hit(player, mechanic, mechanic.damage() * pace.damageFactor(), source);
    }

    /** Runs a raid mechanic; majors count toward how many may run at once. */
    void add(RaidHazard hazard, boolean major) {
        hazards.add(new Tracked(hazard, major));
    }

    int majors() {
        int count = 0;
        for (Tracked tracked : hazards) {
            if (tracked.major()) {
                count++;
            }
        }
        return count;
    }

    /** Whether {@code player} stands in a soak circle now. */
    boolean soaking(Player player) {
        for (Tracked tracked : hazards) {
            if (tracked.hazard() instanceof SoakCircle circle && circle.holds(player)) {
                return true;
            }
        }
        return false;
    }

    void later(int delay, Runnable action) {
        pending.add(new Pending(fight.elapsed() + delay, action));
    }

    /** Marks {@code player} as up in the air for {@code ticks}: nobody kidnaps or launches them meanwhile. */
    void airborne(Player player, int ticks) {
        airborne.put(player.getUniqueId(), fight.elapsed() + ticks);
    }

    boolean isAirborne(Player player) {
        return airborne.containsKey(player.getUniqueId());
    }

    /** Soak circles for {@code players}: about one in five to a circle, up to 3 circles, spread over the floor. */
    void soakCircles(Mechanic share, Mechanic empty, LivingEntity source) {
        int players = crowd();
        int circles = Math.max(1, Math.min(3, (players + 7) / 8));
        int needed = Math.max(1, (int) Math.round(players / 5.0));
        List<Location> spots = new ArrayList<>();
        for (int tries = 0; spots.size() < circles && tries < 30; tries++) {
            Location spot = fight.randomPoint(4, fight.radius() * 0.65);
            spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
            if (spots.stream().allMatch(s -> s.distanceSquared(spot) > 64)) {
                spots.add(spot);
            }
        }
        for (Location spot : spots) {
            add(new SoakCircle(fight, spot, 2.5, 100, needed, scaled(share), scaled(empty), source), true);
        }
    }

    /** How many raid mechanics the conductor has set off (self-test). */
    public int majorsLaunched() {
        return majorsLaunched;
    }

    /** The three bodies (self-test). */
    public List<LivingEntity> bodies() {
        List<LivingEntity> out = new ArrayList<>();
        members.forEach(member -> out.add(member.body));
        return out;
    }

    /** Health attribute every body gets. */
    static void prepare(LivingEntity body) {
        BossFight.setAttribute(body, Attribute.MAX_HEALTH, BODY_HEALTH);
    }
}
