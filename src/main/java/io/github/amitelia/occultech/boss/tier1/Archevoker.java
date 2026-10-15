package io.github.amitelia.occultech.boss.tier1;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Evoker;
import org.bukkit.entity.EvokerFangs;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Vex;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 gate boss (diamond gear, 4-6 min): an illager dark priest on a floating woodland-mansion throne
 * (docs/art/bosses/archevoker/overhaul/plan.md). He never lifts a finger himself while his two gilded casting hands live.
 * <ul>
 * <li>Fang patterns are drawn on the floor a second before they strike: the cyan hand draws the line towards a player and
 * the ring round them, the purple hand the spiral out from him and the burst round him when someone comes too close.
 * Each pattern's warning is in its hand's colour.</li>
 * <li>The hands are his totems: killable, hard to kill and evasive. They hover out of melee reach and dart away (and
 * can't be hurt for a second) after a hit; while drawing a pattern a hand swoops low and holds still - its opening.</li>
 * <li>While a hand lives he cheats death once: the hands catch him and he returns at 40%. Each dead hand makes him
 * stronger (faster patterns; he casts its patterns himself); with both dead he rises off his throne and can't come
 * back, but casts two patterns at once, harder, and bursts twice as often.</li>
 * <li>No vexes. Which hands live and whether he has revived are saved with the fight.</li>
 * </ul>
 */
public final class Archevoker extends BossBehavior {

    private static final Mechanic FANGS = Mechanic.of("ARCHEVOKER", "Fangs", 12, Mechanic.Kind.MAGIC, true);
    private static final Mechanic FANGS_RISEN = Mechanic.of("ARCHEVOKER", "Fangs (risen)", 16, Mechanic.Kind.MAGIC, true);

    private static final int PATTERN_WARNING = 20;
    private static final int BURST_WARNING = 15;
    private static final int BURST_COOLDOWN = 100;
    private static final double HOLD_FAR = 8;
    private static final double TOO_CLOSE = 3.5;
    private static final double HAND_HEALTH = 110;
    /** A hand hovers this high (its carrier's feet; the hand itself is drawn 0.5-3 blocks above that): out of reach. */
    private static final double HOVER_HEIGHT = 4.5;
    /** ...and swoops this low to draw: within a sword's reach, clear of the fangs. */
    private static final double SWOOP_HEIGHT = 1.6;
    private static final int DODGE_TICKS = 20;
    private static final int CAUGHT_TICKS = 52;
    private static final int RISE_TICKS = 40;
    private static final int HIT_FLASH = 10;

    private enum Pattern { LINE, RING, SPIRAL }

    private enum Glow {
        CYAN("HAND_CYAN", 1, Color.fromRGB(80, 220, 250)),
        PURPLE("HAND_PURPLE", -1, Color.fromRGB(186, 104, 255));

        final String part;
        /** Which side of him it hovers: his right (cyan, +1) or his left (purple, -1); his right is his yaw + 90. */
        final int side;
        final Color colour;

        Glow(String part, int side, Color colour) {
            this.part = part;
            this.side = side;
            this.colour = colour;
        }
    }

    private static final Color RISEN = Color.fromRGB(206, 96, 255);

    /** One casting hand: its carrier, where it hovers, and what it is doing. */
    private static final class Hand {
        final Glow glow;
        Vex body;
        boolean dead;
        double drift;                // degrees off its home side, changed by darts and drifting
        int nextDrift;
        @Nullable Location swoopAt;  // where it draws, while drawing
        int swoopUntil;
        int immuneUntil;
        int dartUntil;

        Hand(Glow glow) {
            this.glow = glow;
        }

        boolean alive() {
            return !dead && body != null && body.isValid();
        }
    }

    private record Timed(int at, Runnable action) {}

    private final Map<Glow, Hand> hands = new EnumMap<>(Glow.class);
    private final List<Timed> timeline = new ArrayList<>();
    private Evoker priest;
    private int ticks;
    private boolean revived;
    private boolean risen;
    private int busyUntil;
    private int lastHit = -100;
    private int lastFlinch = -100;
    private int tellUntil;
    private int nextFold = 300;

    private List<Location> pending = List.of();
    private List<Location> pendingSecond = List.of();
    private int strikeAt = -1;
    private int nextPattern = 80;
    private int patternIndex;
    private int nextBurst;
    private int burstAt = -1;
    private List<Location> burstPoints = List.of();

    public Archevoker(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        priest = fight.spawnBoss(Evoker.class, at, e -> {
            e.setCustomName(ChatColor.DARK_PURPLE + "Archevoker");
            e.setCustomNameVisible(true);
            BossFight.setAttribute(e, Attribute.MAX_HEALTH, 700);
            BossFight.setAttribute(e, Attribute.KNOCKBACK_RESISTANCE, 0.8);
            BossFight.setAttribute(e, Attribute.FOLLOW_RANGE, 32);
            BossFight.setAttribute(e, Attribute.MOVEMENT_SPEED, 0.3);
            fight.labelSpawns(e, org.bukkit.entity.EntityType.EVOKER_FANGS, FANGS);
        });
        if (!mythic()) {
            BossFight.setAttribute(priest, Attribute.SCALE, 1.6);
        }
        // the evoker's own mind would flee, summon vexes and cast its own fangs: he casts only through the fight
        Bukkit.getMobGoals().removeAllGoals(priest);
        for (Glow glow : Glow.values()) {
            Hand hand = new Hand(glow);
            hands.put(glow, hand);
            hand.body = spawnHand(glow, home(hand));
        }
        later(2, () -> tintPriest());
        fight.broadcast("&5Two gilded hands rise beside the Archevoker. &fWhile one lives, he cannot die.");
    }

    private Vex spawnHand(Glow glow, Location at) {
        Vex vex = fight.spawnLookalike(glow.part, Vex.class, at, v -> {
            v.setAI(false);
            v.setGravity(false);
            v.setSilent(true);
            v.setCustomName((glow == Glow.CYAN ? ChatColor.AQUA : ChatColor.LIGHT_PURPLE) + "Gilded Hand");
            BossFight.setAttribute(v, Attribute.MAX_HEALTH, HAND_HEALTH * fight.healthMultiplier());
            v.setHealth(HAND_HEALTH * fight.healthMultiplier());
            if (v.getEquipment() != null) {
                v.getEquipment().setItemInMainHand(new ItemStack(Material.AIR));
            }
        });
        if (vex != null) {
            act(vex, glow.part + "_CALM", null);
        }
        return vex;
    }

    private boolean mythic() {
        return fight.usesMythicBody();
    }

    private void act(LivingEntity body, String action, @Nullable Entity target) {
        if (mythic() && body != null && body.isValid()) {
            fight.playAction(body, action, target);
        }
    }

    private void later(int delay, Runnable action) {
        timeline.add(new Timed(ticks + delay, action));
    }

    private int handsAlive() {
        return (int) hands.values().stream().filter(Hand::alive).count();
    }

    @Override
    public int phase() {
        return risen ? 3 : (handsAlive() == 2 ? 1 : 2);
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public boolean vanillaMelee() {
        return false;
    }

    @Override
    public double verticalLeash() {
        return 10;
    }

    // ------------------------------------------------------------------ every tick: the hands fly, he looks at you

    @Override
    public void move() {
        ticks++;
        if (priest == null || !priest.isValid()) {
            return;
        }
        Player target = fight.nearestPlayer(priest.getLocation());
        if (target != null && ticks >= busyUntil) {
            Vector look = target.getLocation().toVector().subtract(priest.getLocation().toVector());
            priest.setBodyYaw((float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ())));
            priest.lookAt(target.getEyeLocation());
        }
        for (Hand hand : hands.values()) {
            if (hand.alive()) {
                fly(hand, target);
            }
        }
        if (!timeline.isEmpty()) {
            List<Timed> due = new ArrayList<>();
            for (Iterator<Timed> it = timeline.iterator(); it.hasNext();) {
                Timed t = it.next();
                if (t.at() <= ticks) {
                    due.add(t);
                    it.remove();
                }
            }
            due.forEach(t -> t.action().run());
        }
    }

    /** Where a hand hovers: beside him, on its own side, out of reach, drifting round. */
    private Location home(Hand hand) {
        Location base = priest.getLocation();
        double yaw = Math.toRadians(priest.getBodyYaw() + 90 * hand.glow.side + hand.drift);
        Location at = base.clone().add(-Math.sin(yaw) * 3.4, HOVER_HEIGHT, Math.cos(yaw) * 3.4);
        at.setY(fight.center().getY() + HOVER_HEIGHT);
        return at;
    }

    /** One tick of a hand's flight towards where it should be, facing the fighter nearest to it. */
    private void fly(Hand hand, @Nullable Player target) {
        Location goal;
        if (ticks < busyUntil && revivingCatch()) {
            Location base = priest.getLocation();
            double yaw = Math.toRadians(priest.getBodyYaw());
            // in front of his chest, one each side, holding him up
            goal = base.clone().add(-Math.sin(yaw) * 2.2 - Math.cos(yaw) * 1.2 * hand.glow.side, 3.6,
                Math.cos(yaw) * 2.2 - Math.sin(yaw) * 1.2 * hand.glow.side);
        } else if (hand.swoopAt != null && ticks < hand.swoopUntil) {
            goal = hand.swoopAt;
        } else {
            hand.swoopAt = null;
            if (ticks >= hand.nextDrift) {
                hand.drift = ThreadLocalRandom.current().nextDouble(-40, 40);
                hand.nextDrift = ticks + 60 + ThreadLocalRandom.current().nextInt(40);
            }
            goal = home(hand);
        }
        Location now = hand.body.getLocation();
        Vector step = goal.toVector().subtract(now.toVector());
        double rate = ticks < hand.dartUntil || hand.swoopAt != null ? 0.35 : 0.15;
        Location next = now.clone().add(step.multiply(rate));
        Location facing = target != null ? target.getLocation() : priest.getLocation();
        Vector look = facing.toVector().subtract(next.toVector());
        next.setYaw((float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ())));
        next.setPitch(0F);
        hand.body.teleport(next);
        hand.body.setBodyYaw(next.getYaw());                   // the model turns with the carrier's body
    }

    private boolean catching;

    private boolean revivingCatch() {
        return catching;
    }

    // ------------------------------------------------------------------ every step: the patterns and the burst

    @Override
    public void tick() {
        if (priest == null || !priest.isValid()) {
            return;
        }
        int now = fight.elapsed();
        holdGround(now);
        if (every(60)) {
            cleanTint();
        }
        if (now >= nextPattern && strikeAt < 0 && ticks >= busyUntil) {
            castPattern(now);
        } else if (!risen && strikeAt < 0 && burstAt < 0 && ticks >= busyUntil && ticks >= nextFold
            && nextPattern - now > 90) {
            // now and then, between patterns, he folds his arms and waits
            nextFold = ticks + 400 + ThreadLocalRandom.current().nextInt(200);
            act(priest, "FOLD", null);
        }
        if (strikeAt > now && !FloorDecals.enabled()) {
            for (Location point : pending) {
                point.getWorld().spawnParticle(Particle.DUST, point.clone().add(0, 0.15, 0), 2, 0.15, 0, 0.15, 0,
                    new Particle.DustOptions(risen ? RISEN : Color.fromRGB(160, 60, 220), 1.4F));
            }
        }
        if (strikeAt >= 0 && now >= strikeAt) {
            strikeAt = -1;
            fangs(pending);
            fangs(pendingSecond);
            pendingSecond = List.of();
            priest.getWorld().playSound(priest.getLocation(), Sound.ENTITY_EVOKER_CAST_SPELL, 2F, risen ? 0.7F : 1F);
        }
    }

    private int interval() {
        boolean low = fight.healthFraction() < 0.5;
        return switch (risen ? 0 : handsAlive()) {
            case 2 -> low ? 90 : 120;
            case 1 -> low ? 70 : 90;
            default -> low ? 50 : 60;
        };
    }

    private static Glow owner(Pattern pattern) {
        return pattern == Pattern.SPIRAL ? Glow.PURPLE : Glow.CYAN;
    }

    private void castPattern(int now) {
        Player target = fight.randomPlayer();
        nextPattern = now + interval();
        if (target == null) {
            return;
        }
        Pattern pattern = Pattern.values()[patternIndex++ % Pattern.values().length];
        pending = pattern(pattern, target.getLocation());
        Color colour = risen ? RISEN : owner(pattern).colour;
        for (Location point : pending) {
            fight.telegraph(point, 0.6, PATTERN_WARNING, colour, null);
        }
        if (risen) {
            // he casts for himself now: a second pattern at once, on someone else if there is anyone else
            Player second = fight.players().size() > 1 ? fight.players().stream().filter(p -> p != target)
                .skip(ThreadLocalRandom.current().nextInt(fight.players().size() - 1)).findFirst().orElse(target) : target;
            Pattern other = Pattern.values()[patternIndex++ % Pattern.values().length];
            pendingSecond = pattern(other, second.getLocation());
            for (Location point : pendingSecond) {
                fight.telegraph(point, 0.6, PATTERN_WARNING, RISEN, null);
            }
            act(priest, "RISEN_CAST", target);
        } else {
            act(priest, pattern.name(), target);
            Hand hand = hands.get(owner(pattern));
            if (hand.alive()) {
                swoop(hand, swoopSpot(pattern, target.getLocation()), PATTERN_WARNING + 10);
            }
        }
        flare(PATTERN_WARNING);
        strikeAt = now + PATTERN_WARNING;
        priest.getWorld().playSound(priest.getLocation(), Sound.ENTITY_EVOKER_PREPARE_ATTACK, 2F, 0.8F);
    }

    /** The hand flies down to draw: low, within reach, holding still - its opening. */
    private void swoop(Hand hand, Location at, int duration) {
        hand.swoopAt = at;
        hand.swoopUntil = ticks + duration;
        act(hand.body, hand.glow.part + "_TELL", null);
        later(duration, () -> act(hand.body, hand.glow.part + "_CALM", null));
    }

    /** Where a hand draws each pattern: beside it, never on its fangs. */
    private Location swoopSpot(Pattern pattern, Location target) {
        Location origin = priest.getLocation();
        Vector toTarget = target.toVector().subtract(origin.toVector()).setY(0);
        if (toTarget.lengthSquared() < 0.01) {
            toTarget = new Vector(1, 0, 0);
        }
        toTarget.normalize();
        Vector side = new Vector(-toTarget.getZ(), 0, toTarget.getX());
        Location spot = switch (pattern) {
            case LINE -> origin.clone().add(toTarget.clone().multiply(4)).add(side.multiply(1.6));
            case RING -> target.clone().subtract(toTarget.clone().multiply(1.2));
            case SPIRAL -> origin.clone().add(side.multiply(-2.5));
        };
        return low(spot);
    }

    private Location low(Location spot) {
        Location out = inArena(spot);
        out.setY(fight.center().getY() + SWOOP_HEIGHT);
        return out;
    }

    private Location inArena(Location at) {
        Vector off = at.toVector().subtract(fight.center().toVector()).setY(0);
        double max = fight.radius() - 1.5;
        if (off.length() > max) {
            off.normalize().multiply(max);
        }
        return fight.center().clone().add(off);
    }

    private void fangs(List<Location> points) {
        Mechanic mechanic = risen ? FANGS_RISEN : FANGS;
        for (Location point : points) {
            point.getWorld().spawn(point, EvokerFangs.class, f -> {
                f.setOwner(priest);
                fight.label(f, mechanic);
            });
        }
    }

    /** Holds about 8 blocks from his target (the throne glides), and answers anyone closer than 3.5 with a burst. */
    private void holdGround(int now) {
        Player target = fight.nearestPlayer(priest.getLocation());
        if (target == null) {
            return;
        }
        double distance = target.getLocation().distance(priest.getLocation());
        if (ticks < busyUntil) {
            priest.getPathfinder().stopPathfinding();
        } else if (distance > HOLD_FAR) {
            priest.getPathfinder().moveTo(target.getLocation(), 1.0);
        } else if (distance < HOLD_FAR - 2) {
            priest.getPathfinder().stopPathfinding();
        }
        // a pattern already being drawn has the hands and his arms: the burst waits for it
        if (burstAt < 0 && strikeAt < 0 && now >= nextBurst && distance < TOO_CLOSE && ticks >= busyUntil) {
            nextBurst = now + (risen ? BURST_COOLDOWN / 2 : BURST_COOLDOWN);
            burstAt = now + BURST_WARNING;
            List<Location> points = new ArrayList<>();
            Location origin = priest.getLocation();
            for (int i = 0; i < 10; i++) {
                double angle = Math.PI * 2 * i / 10;
                points.add(floor(origin.clone().add(Math.cos(angle) * 2.2, 0, Math.sin(angle) * 2.2)));
            }
            burstPoints = points;
            Color colour = risen ? RISEN : Glow.PURPLE.colour;
            for (Location point : points) {
                fight.telegraph(point, 0.6, BURST_WARNING, colour, null);
            }
            act(priest, risen ? "RISEN_CAST" : "BURST", target);
            Hand purple = hands.get(Glow.PURPLE);
            if (!risen && purple.alive()) {
                Vector toward = target.getLocation().toVector().subtract(origin.toVector()).setY(0);
                Location spot = toward.lengthSquared() < 0.01 ? origin.clone().add(1.2, 0, 0)
                    : origin.clone().add(toward.normalize().multiply(1.2));
                swoop(purple, low(spot), BURST_WARNING + 10);
            }
            flare(BURST_WARNING);
            priest.getWorld().playSound(origin, Sound.ENTITY_EVOKER_PREPARE_ATTACK, 2F, 1.3F);
        }
        if (burstAt >= 0 && now >= burstAt) {
            burstAt = -1;
            fangs(burstPoints);
        }
    }

    private Location floor(Location at) {
        Location out = at.clone();
        out.setY(fight.center().getY());
        return out;
    }

    private List<Location> pattern(Pattern pattern, Location target) {
        List<Location> points = new ArrayList<>();
        Location origin = priest.getLocation();
        switch (pattern) {
            case RING -> {
                for (int i = 0; i < 14; i++) {
                    double angle = Math.PI * 2 * i / 14;
                    points.add(floor(target.clone().add(Math.cos(angle) * 3, 0, Math.sin(angle) * 3)));
                }
            }
            case LINE -> {
                Vector step = target.toVector().subtract(origin.toVector()).setY(0);
                if (step.lengthSquared() < 0.01) {
                    step = new Vector(1, 0, 0);
                }
                step.normalize();
                for (int i = 1; i <= 16; i++) {
                    points.add(floor(origin.clone().add(step.clone().multiply(i))));
                }
            }
            case SPIRAL -> {
                for (int i = 0; i < 24; i++) {
                    double angle = i * 0.55;
                    double radius = 1.5 + i * 0.45;
                    points.add(floor(origin.clone().add(Math.cos(angle) * radius, 0, Math.sin(angle) * radius)));
                }
            }
        }
        points.removeIf(p -> p.distanceSquared(fight.center()) > fight.radius() * fight.radius());
        return points;
    }

    // ------------------------------------------------------------------ the hands: dodging, dying

    @Override
    public double modifyAddDamage(LivingEntity add, Player player, double damage) {
        Hand hand = handOf(add);
        if (hand == null) {
            return damage;
        }
        if (ticks < hand.immuneUntil) {
            return 0;                                          // still darting away from the last hit
        }
        act(add, hand.glow.part + "_HIT", null);
        if (hand.swoopAt == null || ticks >= hand.swoopUntil) {
            // hovering: it darts off to another spot and can't be hurt on the way
            hand.drift = (hand.drift > 0 ? -1 : 1) * ThreadLocalRandom.current().nextDouble(50, 90);
            hand.nextDrift = ticks + 80;
            hand.immuneUntil = ticks + DODGE_TICKS;
            hand.dartUntil = ticks + 8;
            add.getWorld().playSound(add.getLocation(), Sound.ENTITY_BREEZE_JUMP, 1F, 1.6F);
        }
        return damage;
    }

    @Nullable
    private Hand handOf(Entity entity) {
        for (Hand hand : hands.values()) {
            if (hand.body != null && hand.body.equals(entity)) {
                return hand;
            }
        }
        return null;
    }

    @Override
    public void onAddDeath(Entity entity, @Nullable Player killer) {
        Hand hand = handOf(entity);
        if (hand == null || hand.dead) {
            return;
        }
        hand.dead = true;
        if (entity instanceof LivingEntity living) {
            io.github.amitelia.occultech.boss.Prop corpse = fight.corpse(living);
            if (corpse != null) {
                corpse.showPart("eyelid");                     // the eye shuts as it falls
                corpse.tint(Color.fromRGB(52, 52, 60).asRGB(), "eye", "circle");
            }
        }
        entity.getWorld().playSound(entity.getLocation(), Sound.BLOCK_BELL_RESONATE, 1.6F, 0.6F);
        handLost(hand.glow, true);
    }

    /** A hand is gone: he recoils, his light dims; with both gone he rises and can't come back. */
    private void handLost(Glow glow, boolean live) {
        if (handsAlive() == 0 && !risen) {
            risen = true;
            if (live) {
                fight.broadcast("&5Both hands have fallen. &cThe Archevoker rises from his throne - he will not be caught again!");
                act(priest, "RISE", null);
                busyUntil = ticks + RISE_TICKS;
                priest.getWorld().playSound(priest.getLocation(), Sound.ENTITY_EVOKER_PREPARE_SUMMON, 2F, 0.5F);
            }
            later(live ? RISE_TICKS : 2, this::tintPriest);
        } else if (live) {
            fight.broadcast(glow == Glow.CYAN ? "&bThe cyan hand falls. &fThe Archevoker draws its patterns himself."
                : "&dThe purple hand falls. &fThe Archevoker draws its patterns himself.");
            act(priest, "HAND_LOST", null);
            later(4, this::tintPriest);
        } else {
            later(2, this::tintPriest);
        }
    }

    // ------------------------------------------------------------------ the priest: cheating death, flinching, tints

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        if (boss != priest || revived || handsAlive() == 0 || damage < boss.getHealth()) {
            return damage;
        }
        revived = true;
        double max = boss.getAttribute(Attribute.MAX_HEALTH).getValue();
        boss.setHealth(max * 0.4);
        boss.getWorld().spawnParticle(Particle.TOTEM_OF_UNDYING, boss.getLocation().add(0, 3.5, 0), 80, 0.8, 1.2, 0.8, 0.4);
        boss.getWorld().playSound(boss.getLocation(), Sound.ITEM_TOTEM_USE, 1.5F, 0.8F);
        fight.broadcast("&5The gilded hands catch the Archevoker - he cheats death!");
        act(priest, "CAUGHT", null);
        busyUntil = ticks + CAUGHT_TICKS;
        catching = true;
        strikeAt = -1;
        burstAt = -1;
        for (Hand hand : hands.values()) {
            hand.swoopAt = null;
        }
        later(CAUGHT_TICKS, () -> {
            catching = false;
            tintPriest();
        });
        return 0;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (boss != priest) {
            return;
        }
        lastHit = ticks;
        later(HIT_FLASH + 4, this::cleanTint);
        if (ticks - lastFlinch > 12 && ticks >= busyUntil) {
            lastFlinch = ticks;
            act(priest, "FLINCH", null);
        }
    }

    /** His glow flares while a pattern is being drawn, then settles back. */
    private void flare(int duration) {
        tellUntil = ticks + duration;
        act(priest, "STATE_TELL", null);
        later(duration + 2, this::tintPriest);
    }

    /** His glow for where the fight stands: calm, dimmed with a hand lost, violet risen, gold while caught. */
    private void tintPriest() {
        if (priest == null || !priest.isValid()) {
            return;
        }
        String state = risen ? "STATE_RISEN" : catching ? "STATE_CAUGHT" : ticks < tellUntil ? "STATE_TELL"
            : handsAlive() == 2 ? "STATE_CALM" : "STATE_WOUNDED";
        act(priest, state, null);
    }

    /**
     * Puts his tints right once a hit flash is over (BetterModel's flash restores each bone's previous tint when it
     * ends; a tint that lands during it records the red as that previous tint). Skipped while a flash may still run.
     */
    private void cleanTint() {
        if (!mythic() || priest == null || !priest.isValid() || ticks - lastHit < HIT_FLASH + 2) {
            return;
        }
        act(priest, "UNTINT", null);
        tintPriest();
        for (Hand hand : hands.values()) {
            if (hand.alive()) {
                act(hand.body, hand.glow.part + (hand.swoopAt != null && ticks < hand.swoopUntil ? "_TELL" : "_CALM"), null);
            }
        }
    }

    @Override
    public void onBossDeath(LivingEntity boss) {
        io.github.amitelia.occultech.boss.Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(Color.fromRGB(46, 48, 56).asRGB(), "eyes", "ring", "runes");
        }
    }

    // ------------------------------------------------------------------ saved with the fight

    @Override
    public String saveData() {
        return "revived=" + (revived ? 1 : 0) + ";cyan=" + (hands.get(Glow.CYAN).dead ? 0 : 1)
            + ";purple=" + (hands.get(Glow.PURPLE).dead ? 0 : 1);
    }

    @Override
    public void restoreData(String data) {
        for (String entry : data.split(";")) {
            String[] kv = entry.split("=");
            if (kv.length != 2) {
                continue;
            }
            switch (kv[0]) {
                case "revived" -> revived = "1".equals(kv[1]);
                case "cyan", "purple" -> {
                    Hand hand = hands.get("cyan".equals(kv[0]) ? Glow.CYAN : Glow.PURPLE);
                    if ("0".equals(kv[1]) && hand != null && !hand.dead) {
                        // a hand killed before the restart stays dead: its fresh carrier goes without a death
                        hand.dead = true;
                        if (hand.body != null) {
                            hand.body.remove();
                        }
                    }
                }
                default -> { }
            }
        }
        for (Hand hand : hands.values()) {
            if (hand.dead) {
                handLost(hand.glow, false);
                break;
            }
        }
    }
}
