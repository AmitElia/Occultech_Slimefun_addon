package io.github.amitelia.occultech.boss.tier1;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Illager;
import org.bukkit.entity.Illusioner;
import org.bukkit.entity.Pillager;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Snowball;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import com.destroystokyo.paper.entity.ai.GoalType;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Tier-1 mini-boss (diamond gear): the Masquerade, a towering horror clown magician. With the Mythic body he is a
 * pillager carrier under his model (an invisible illusioner would still draw its mirror images); without it, an
 * illusioner (a mob that never spawns in survival).
 * <ul>
 * <li>He stalks his target from 6 to 13 blocks, staring at it, and stands still for every gesture.</li>
 * <li>Every 3s he throws a fan of three playing cards at his target: his arm winds back first (12 ticks), then the
 * cards fly, slow enough to sidestep.</li>
 * <li>Every 10s a prism burst: a ring under a player that bursts with light 30 ticks later.</li>
 * <li>Every 15s he bows and splits into 3 reflections that look exactly like him, then blinks to a new spot among
 * them. The real Magus trails a faint white sparkle; the reflections don't. Hitting one shatters it, makes you glow
 * for 3s and lets him blink again.</li>
 * <li>Every 20s he snaps his fingers and Jack-in-the-Boxes pop up round the arena (two, one more per extra fighter,
 * at most four): each cranks for 1.5s, pops open, and bops in place throwing a dodgeable card every 2.5s until it is
 * broken (3 hits) or winds down after 15s.</li>
 * </ul>
 * Every gesture he makes, his reflections make too, at the same moment: only the sparkle tells them apart. The
 * reflections never target anyone, so they can't cast, and they never throw a damaging card. Ranged, so the
 * anti-pillar teleport is off.
 */
public final class Masquerade extends BossBehavior {

    private static final Mechanic CARD = Mechanic.of("MASQUERADE", "Card fan", 20, Mechanic.Kind.PROJECTILE, true);
    private static final Mechanic JACK_CARD = Mechanic.of("MASQUERADE", "Jack card", 8, Mechanic.Kind.ADD, true);
    private static final Mechanic PRISM = Mechanic.of("MASQUERADE", "Prism burst", 12, Mechanic.Kind.MAGIC, true);
    private static final Color PRISM_COLOR = Color.fromRGB(120, 170, 255);

    /** His walking pace: a long stride (the walk clip covers about 3 blocks a second). */
    private static final double SPEED = 0.3;
    private static final int FAN_INTERVAL = 60;
    /** BetterModel's red hit flash (ticks). */
    private static final int HIT_FLASH = 10;
    /** The throw clip's wind-up: the cards leave his palm this long after it starts. */
    private static final int FAN_WINDUP = 12;
    private static final double CARD_SPEED = 1.3;
    private static final int CARD_LIFE = 40;
    private static final int PRISM_INTERVAL = 200;
    private static final int PRISM_WARNING = 30;
    private static final double PRISM_RADIUS = 2.5;

    private static final int DECOY_INTERVAL = 300;
    private static final int DECOY_COUNT = 3;
    /** The curtsey: the reflections appear this long after the bow starts. */
    private static final int DECOY_WINDUP = 20;
    /** The blink: he vanishes this long after he starts folding in. */
    private static final int BLINK_WINDUP = 9;

    private static final int JACK_INTERVAL = 400;
    private static final int JACK_FIRST = 200;
    /** The snap: the boxes appear this long after his hand starts rising. */
    private static final int SNAP_WINDUP = 12;
    /** A box cranks this long (its music-box tune) before it pops open. */
    private static final int JACK_WARNING = 30;
    private static final int JACK_LIFE = 300;
    private static final int JACK_THROW_EVERY = 50;
    /** A jack's throw clip: three bops and the flick, the card leaving his hand this long after it starts. */
    private static final int JACK_THROW_WINDUP = 23;
    private static final double JACK_CARD_SPEED = 0.7;
    private static final int JACK_HITS = 3;
    private static final int MAX_JACKS = 4;
    private static final String JACK_MODEL = "occultech_masquerade_jack";

    private final List<Illager> decoys = new ArrayList<>();
    private final List<Jack> jacks = new ArrayList<>();
    /** Things set to happen on a later tick (the clips' release moments), run from {@link #move()}. */
    private final List<Timed> timeline = new ArrayList<>();
    private Illager magus;
    /** Who each body (him, each reflection) is facing and stalking, picked every step. */
    private final java.util.Map<Illager, Player> focus = new java.util.HashMap<>();
    /** Where each body drifts while it keeps its range, and until when. */
    private final java.util.Map<Illager, Location> drift = new java.util.HashMap<>();
    private final java.util.Map<Illager, Integer> driftUntil = new java.util.HashMap<>();
    private Location prismAt;
    private int prismStrike = -1;
    /** Until this tick he is in the middle of a gesture (a prism, a bow, a snap, a blink): no card fan starts. */
    private int busyUntil;
    private int lastFlinch = -100;
    /** The tick he was last hit (BetterModel's red hit flash lasts 10 ticks from the first hit of a run). */
    private int lastHit = -100;
    /** Until this tick his eyes are flared (a tell: the prism, the snap, the laugh). */
    private int eyesFlaredUntil;
    private int ticks;

    public Masquerade(BossFight fight) {
        super(fight);
    }

    private record Timed(int at, Runnable action) {}

    /** One Jack-in-the-Box: its fight object (model, hitbox, hits) and its clock. */
    private static final class Jack {
        final BossFight.FightObject object;
        /** Where it stands, turned the way it faces. */
        final Location feet;
        final int popAt;
        final int endAt;
        int nextThrow;

        Jack(BossFight.FightObject object, Location feet, int popAt) {
            this.object = object;
            this.feet = feet;
            this.popAt = popAt;
            this.endAt = popAt + JACK_LIFE;
            this.nextThrow = popAt + 20;
        }
    }

    @Override
    public void spawn(Location at) {
        magus = fight.spawnBoss(carrier(), at, m -> {
            dress(m);
            BossFight.setAttribute(m, Attribute.MOVEMENT_SPEED, SPEED);
            BossFight.setAttribute(m, Attribute.MAX_HEALTH, 220);
            BossFight.setAttribute(m, Attribute.KNOCKBACK_RESISTANCE, 0.3);
            BossFight.setAttribute(m, Attribute.FOLLOW_RANGE, 32);
        });
        if (mythic()) {
            // the model draws him and his cards: the invisible carrier holds nothing, and stays unscaled under it
            magus.getEquipment().setItemInMainHand(new ItemStack(Material.AIR));
            act(magus, "STATE_CALM", null);
        } else {
            magus.getEquipment().setItemInMainHand(new ItemStack(Material.PAPER));
            BossFight.setAttribute(magus, Attribute.SCALE, 1.2);
        }
    }

    private boolean mythic() {
        return fight.usesMythicBody();
    }

    /**
     * His carrier: a pillager under the model (it draws nothing when invisible; an invisible illusioner draws its
     * mirror images, which showed through the model), an illusioner without one.
     */
    private Class<? extends Illager> carrier() {
        return mythic() ? Pillager.class : Illusioner.class;
    }

    private void act(LivingEntity body, String action, @Nullable Entity target) {
        if (mythic()) {
            fight.playAction(body, action, target);
        }
    }

    /** A gesture he makes, and every reflection with him, at the same moment (only the sparkle tells them apart). */
    private void perform(String action, @Nullable Entity target) {
        act(magus, action, target);
        for (Illager decoy : decoys) {
            if (decoy.isValid()) {
                act(decoy, action, target);
            }
        }
    }

    private void later(int delay, Runnable action) {
        timeline.add(new Timed(ticks + delay, action));
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public void move() {
        ticks++;
        face(magus);
        for (Illager decoy : decoys) {
            face(decoy);
        }
        if (timeline.isEmpty()) {
            return;
        }
        List<Timed> due = new ArrayList<>();
        for (Iterator<Timed> it = timeline.iterator(); it.hasNext();) {
            Timed t = it.next();
            if (t.at() <= ticks) {
                due.add(t);
                it.remove();
            }
        }
        for (Timed t : due) {
            t.action().run();
        }
    }

    @Override
    public void tick() {
        if (!magus.isValid()) {
            return;
        }
        decoys.removeIf(d -> d.isDead() || !d.isValid());
        focus.keySet().removeIf(b -> !b.isValid());
        stalk(magus);
        for (Illager decoy : decoys) {
            stalk(decoy);
        }
        magus.getWorld().spawnParticle(Particle.END_ROD, magus.getLocation().add(0, 0.1, 0), 1, 0.2, 0, 0.2, 0);

        attack(fight.elapsed());
        jacks();
        if (every(60)) {
            cleanTint();
        }

        if (fight.elapsed() == 100 || every(DECOY_INTERVAL)) {
            conjure();
        }
        if (fight.elapsed() == JACK_FIRST || (fight.elapsed() > JACK_FIRST && (fight.elapsed() - JACK_FIRST) % JACK_INTERVAL == 0)) {
            snap();
        }
    }

    /**
     * Turns {@code body} to stare at the fighter it stalks, every tick, head and body (the model's head bone follows the
     * carrier's head, its body the carrier's body).
     */
    private void face(Illager body) {
        Player target = body == null ? null : focus.get(body);
        if (target == null || !body.isValid() || !target.isValid()) {
            return;
        }
        Vector look = target.getLocation().toVector().subtract(body.getLocation().toVector());
        float yaw = (float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ()));
        body.setBodyYaw(yaw);
        body.lookAt(target.getEyeLocation());
    }

    /**
     * Keeps {@code body} at its range from the nearest fighter: closes in past 13 blocks, backs off inside 6, and in
     * between drifts sideways round it; it stands still while a gesture plays. Him and every reflection alike.
     */
    private void stalk(Illager body) {
        Player target = fight.nearestPlayer(body.getLocation());
        if (target == null) {
            focus.remove(body);
            return;
        }
        focus.put(body, target);
        if (ticks < busyUntil) {
            body.getPathfinder().stopPathfinding();
            return;
        }
        Location from = body.getLocation();
        Vector to = target.getLocation().toVector().subtract(from.toVector()).setY(0);
        double d = to.length();
        if (d > 13) {
            body.getPathfinder().moveTo(target.getLocation(), 1.0);
        } else if (d < 6) {
            body.getPathfinder().moveTo(inArena(from.clone().subtract(to.normalize().multiply(5))), 1.15);
        } else {
            Location aim = drift.get(body);
            if (aim == null || ticks >= driftUntil.getOrDefault(body, 0) || aim.distanceSquared(from) < 1.5) {
                Vector side = new Vector(-to.getZ(), 0, to.getX()).normalize().multiply(ThreadLocalRandom.current().nextBoolean() ? 4 : -4);
                aim = inArena(from.clone().add(side));
                drift.put(body, aim);
                driftUntil.put(body, ticks + 40);
            }
            body.getPathfinder().moveTo(aim, 0.8);
        }
    }

    /** {@code at}, pulled back inside the arena (3 blocks from its edge). */
    private Location inArena(Location at) {
        Location c = fight.center();
        Vector off = at.toVector().subtract(c.toVector()).setY(0);
        double max = fight.radius() - 3;
        if (off.length() > max) {
            off.normalize().multiply(max);
        }
        Location out = c.clone().add(off);
        out.setY(at.getY());
        return out;
    }

    /**
     * A point on a model standing at {@code feet} turned to {@code yawDegrees}: {@code right}, {@code up} and
     * {@code forward} blocks from its feet (his hand at the moment of a throw).
     */
    private static Location point(Location feet, float yawDegrees, double right, double up, double forward) {
        double yaw = Math.toRadians(yawDegrees);
        Vector facing = new Vector(-Math.sin(yaw), 0, Math.cos(yaw));
        Vector toRight = new Vector(-Math.cos(yaw), 0, -Math.sin(yaw));
        return feet.clone().add(toRight.multiply(right)).add(facing.multiply(forward)).add(0, up, 0);
    }

    /** The bow: his reflections step out of him on the curtsey's release, and he blinks away among them. */
    private void conjure() {
        busyUntil = ticks + 40;
        perform("CURTSEY", null);
        later(DECOY_WINDUP, () -> {
            if (!magus.isValid()) {
                return;
            }
            for (int i = decoys.size(); i < DECOY_COUNT; i++) {
                Illager decoy = fight.spawnLookalike("DECOY", carrier(), fight.randomPoint(3, fight.radius() - 3), d -> {
                    dress(d);
                    BossFight.setAttribute(d, Attribute.MOVEMENT_SPEED, SPEED);
                    BossFight.setAttribute(d, Attribute.MAX_HEALTH, 1);
                    d.setHealth(1);
                });
                if (decoy != null) {
                    // reflections never pick a target of their own, so they can't cast spells or throw: the fight
                    // moves them and turns them to the nearest fighter, as it does him
                    Bukkit.getMobGoals().removeAllGoals(decoy, GoalType.TARGET);
                    if (mythic()) {
                        decoy.getEquipment().setItemInMainHand(new ItemStack(Material.AIR));
                        act(decoy, "STATE_CALM", null);
                    } else {
                        decoy.getEquipment().setItemInMainHand(new ItemStack(Material.PAPER));
                        BossFight.setAttribute(decoy, Attribute.SCALE, 1.2);
                    }
                    decoys.add(decoy);
                }
            }
            blink();
            fight.broadcast("&9The Masquerade splits into reflections. &7Find the one that sparkles.");
        });
    }

    /** The snap: the boxes appear round the arena on its release. */
    private void snap() {
        busyUntil = Math.max(busyUntil, ticks + 24);
        perform("SNAP", null);
        eyesFlaredUntil = Math.max(eyesFlaredUntil, ticks + 34);
        later(SNAP_WINDUP, () -> {
            if (!magus.isValid()) {
                return;
            }
            int count = Math.min(MAX_JACKS - jacks.size(), Math.max(2, fight.players().size() + 1));
            List<Location> placed = new ArrayList<>();
            for (Jack jack : jacks) {
                placed.add(jack.object.location());
            }
            for (int i = 0; i < count; i++) {
                Location at = jackSpot(placed);
                if (at == null) {
                    continue;
                }
                placed.add(at);
                Player facing = fight.nearestPlayer(at);
                if (facing != null) {
                    Vector look = facing.getLocation().toVector().subtract(at.toVector());
                    at.setYaw((float) Math.toDegrees(Math.atan2(-look.getX(), look.getZ())));
                }
                Jack[] self = new Jack[1];
                BossFight.FightObject object = fight.spawnObject(at, JACK_MODEL, Material.JACK_O_LANTERN, 1F, 0.9F, 2.0F,
                    JACK_HITS, () -> broke(self[0]));
                self[0] = new Jack(object, at.clone(), ticks + JACK_WARNING);
                jacks.add(self[0]);
            }
            magus.getWorld().playSound(magus.getLocation(), Sound.BLOCK_NOTE_BLOCK_BELL, 1.2F, 0.5F);
        });
    }

    /** A spot on the arena floor at least 6 blocks from every player and 3 from the other boxes, or null. */
    @Nullable
    private Location jackSpot(List<Location> placed) {
        for (int attempt = 0; attempt < 16; attempt++) {
            Location at = fight.randomPoint(3, fight.radius() - 2);
            boolean clear = fight.players().stream().noneMatch(p -> p.getLocation().distanceSquared(at) < 36);
            for (Location other : placed) {
                clear &= other.distanceSquared(at) >= 9;
            }
            if (clear) {
                return at;
            }
        }
        return null;
    }

    /** Each box: its crank and tune until it pops, then a card every 2.5s at the nearest fighter it can see. */
    private void jacks() {
        for (Iterator<Jack> it = jacks.iterator(); it.hasNext();) {
            Jack jack = it.next();
            if (!jack.object.isAlive()) {
                it.remove();
                continue;
            }
            Location at = jack.object.location();
            if (ticks < jack.popAt) {
                float pitch = 0.6F + 1.2F * (1F - (jack.popAt - ticks) / (float) JACK_WARNING);
                at.getWorld().playSound(at, Sound.BLOCK_NOTE_BLOCK_CHIME, 0.7F, pitch);
                at.getWorld().spawnParticle(Particle.NOTE, at.clone().add(0, 1.0, 0), 1, 0.2, 0.1, 0.2, 0.6);
                continue;
            }
            if (ticks - jack.popAt < BossService.STEP) {              // the pop, once
                at.getWorld().playSound(at, Sound.ENTITY_SLIME_JUMP, 1F, 0.8F);
                at.getWorld().playSound(at, Sound.ENTITY_ITEM_PICKUP, 1F, 0.5F);
            }
            if (ticks >= jack.endAt) {
                jack.object.tint(Color.fromRGB(96, 104, 112).asRGB(), "eyes");
                jack.object.retire("wind", 28);
                at.getWorld().playSound(at, Sound.BLOCK_NOTE_BLOCK_CHIME, 0.8F, 0.5F);
                it.remove();
                continue;
            }
            if (ticks >= jack.nextThrow) {
                Player target = visibleTarget(at.clone().add(0, 1.3, 0));
                if (target != null) {
                    jack.nextThrow = ticks + JACK_THROW_EVERY;
                    jack.object.animate("throw");
                    later(JACK_THROW_WINDUP, () -> {
                        if (jack.object.isAlive() && target.isValid()) {
                            Location hand = point(jack.feet, jack.feet.getYaw(), 0.25, 1.05, 0.45);
                            Vector aim = target.getEyeLocation().toVector().subtract(hand.toVector()).normalize();
                            throwCard(hand, aim.multiply(JACK_CARD_SPEED), JACK_CARD, 60);
                            hand.getWorld().playSound(hand, Sound.ITEM_BOOK_PAGE_TURN, 1F, 1.6F);
                        }
                    });
                } else {
                    jack.nextThrow = ticks + 10;
                }
            }
        }
    }

    /** The nearest fighter within 24 blocks that {@code from} can see, or null. */
    @Nullable
    private Player visibleTarget(Location from) {
        Player best = null;
        double bestDistance = 24 * 24;
        for (Player player : fight.players()) {
            Location eye = player.getEyeLocation();
            double d = eye.distanceSquared(from);
            if (d >= bestDistance) {
                continue;
            }
            Vector to = eye.toVector().subtract(from.toVector());
            if (from.getWorld().rayTraceBlocks(from, to, Math.sqrt(d), org.bukkit.FluidCollisionMode.NEVER, true) == null) {
                best = player;
                bestDistance = d;
            }
        }
        return best;
    }

    private void broke(Jack jack) {
        if (jack == null) {
            return;
        }
        jacks.remove(jack);
        Location at = jack.object.location().clone().add(0, 0.8, 0);
        for (Color c : new Color[] {Color.fromRGB(196, 24, 36), Color.WHITE, Color.fromRGB(30, 30, 34), Color.fromRGB(220, 180, 60)}) {
            at.getWorld().spawnParticle(Particle.DUST, at, 10, 0.4, 0.5, 0.4, 0, new Particle.DustOptions(c, 1.1F));
        }
        at.getWorld().playSound(at, Sound.BLOCK_NOTE_BLOCK_DIDGERIDOO, 1F, 1.8F);
    }

    /** A flying playing card: no gravity, slow enough to sidestep, gone after {@code life} ticks. */
    private void throwCard(Location from, Vector velocity, Mechanic mechanic, int life) {
        Snowball card = fight.spawnExtra(Snowball.class, from, s -> {
            s.setItem(cardItem());
            s.setGravity(false);
            s.setShooter(magus);
        });
        fight.label(card, mechanic);
        card.setVelocity(velocity);
        later(life, () -> {
            if (card.isValid()) {
                card.remove();
            }
        });
    }

    private static ItemStack cardItem() {
        ItemStack card = new ItemStack(Material.PAPER);
        ItemMeta meta = card.getItemMeta();
        meta.setItemModel(new NamespacedKey("occultech", "magus_card"));
        card.setItemMeta(meta);
        return card;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (boss != magus) {
            return;
        }
        lastHit = ticks;
        later(HIT_FLASH + 4, this::cleanTint);
        if (ticks - lastFlinch > 12 && ticks >= busyUntil) {
            lastFlinch = ticks;
            act(magus, "FLINCH", null);
        }
    }

    /**
     * Puts his tints right once a hit flash is over: every bone untinted, then his eyes (flared or calm, once: no delayed re-tint that could land on a flare). BetterModel's
     * flash restores each bone's previous tint when it ends, and a tint that lands during it (an eye flaring) records
     * the red as that previous tint, so he could stay red. Skipped while a flash may still be running; the newest
     * hit's own clean follows it.
     */
    private void cleanTint() {
        if (!mythic() || !magus.isValid() || ticks - lastHit < HIT_FLASH + 2) {
            return;
        }
        act(magus, "UNTINT", null);
        act(magus, ticks < eyesFlaredUntil ? "EYES_TELL" : "STATE_CALM", null);
    }

    @Override
    public void onAddDeath(Entity entity, @Nullable Player killer) {
        if (!(entity instanceof Illager decoy) || !decoys.remove(decoy)) {
            return;
        }
        focus.remove(decoy);
        // the mirror flash, then the reflection is gone at once: no corpse and no model left standing behind it
        act(decoy, "SHATTER", null);
        entity.getWorld().spawnParticle(Particle.BLOCK, entity.getLocation().add(0, 1, 0), 30, 0.3, 0.6, 0.3, Material.GLASS.createBlockData());
        entity.getWorld().playSound(entity.getLocation(), Sound.BLOCK_GLASS_BREAK, 1.2F, 1F);
        later(3, () -> {
            if (entity.isValid()) {
                entity.remove();
            }
        });
        if (killer != null) {
            killer.addPotionEffect(new PotionEffect(PotionEffectType.GLOWING, 60, 0));
            killer.sendMessage(ChatColor.GRAY + "You shattered a reflection - the Masquerade sees you!");
            act(magus, "LAUGH", killer);
            eyesFlaredUntil = Math.max(eyesFlaredUntil, ticks + 28);
            busyUntil = Math.max(busyUntil, ticks + 20);
            later(16, this::blink);
        }
    }

    @Override
    public void onBossDeath(LivingEntity boss) {
        io.github.amitelia.occultech.boss.Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(Color.fromRGB(40, 44, 48).asRGB(), "eyes");       // the eyes go out
        }
        for (Jack jack : jacks) {
            jack.object.retire("wind", 28);
        }
        jacks.clear();
    }

    /**
     * The card fan every 3s: the throw clip starts, and on its release 12 ticks later three cards fly at his target
     * (aimed then). Every 10s a prism burst: a ring under a player that bursts with light 30 ticks later. A prism, a
     * bow or a snap in progress holds the next fan back.
     */
    private void attack(int now) {
        if (every(FAN_INTERVAL) && ticks >= busyUntil && fight.nearestPlayer(magus.getLocation()) != null) {
            busyUntil = ticks + FAN_WINDUP + 4;
            perform("THROW", null);
            later(FAN_WINDUP, this::fan);
        }
        if (prismStrike < 0 && every(PRISM_INTERVAL)) {
            Player marked = fight.randomPlayer();
            if (marked != null) {
                prismAt = marked.getLocation();
                prismStrike = now + PRISM_WARNING;
                busyUntil = Math.max(busyUntil, ticks + PRISM_WARNING + 10);
                fight.telegraph(prismAt, PRISM_RADIUS, PRISM_WARNING, PRISM_COLOR);
                perform("PRISM", marked);
                eyesFlaredUntil = ticks + 44;
            }
        }
        if (prismStrike >= 0 && now >= prismStrike) {
            prismStrike = -1;
            prismAt.getWorld().spawnParticle(Particle.END_ROD, prismAt.clone().add(0, 0.5, 0), 40, 1.2, 0.6, 1.2, 0.08);
            prismAt.getWorld().playSound(prismAt, Sound.BLOCK_AMETHYST_BLOCK_BREAK, 1.5F, 1.4F);
            io.github.amitelia.occultech.boss.AirEffects.burst(fight, prismAt.clone().add(0, 0.8, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.CRACKLE,
                PRISM_COLOR, 3F);
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(prismAt) <= PRISM_RADIUS * PRISM_RADIUS) {
                    fight.hit(player, PRISM, magus);
                }
            }
        }
    }

    /** Three cards from his right hand at his target, 10 degrees apart. */
    private void fan() {
        if (!magus.isValid()) {
            return;
        }
        Player target = magus.getTarget() instanceof Player p && fight.players().contains(p) ? p : fight.nearestPlayer(magus.getLocation());
        if (target == null) {
            return;
        }
        // from the model's hand where the throw pose flings it: 2.2 blocks to his right, 3.9 up, 1.7 ahead
        Location hand = mythic() ? point(magus.getLocation(), magus.getBodyYaw(), 2.2, 3.9, 1.7)
            : magus.getEyeLocation().add(0, -0.4, 0);
        Vector aim = target.getEyeLocation().toVector().subtract(hand.toVector()).normalize();
        for (int i = -1; i <= 1; i++) {
            throwCard(hand, aim.clone().rotateAroundY(Math.toRadians(10 * i)).multiply(CARD_SPEED), CARD, CARD_LIFE);
        }
        magus.getWorld().playSound(magus.getLocation(), Sound.ENTITY_ILLUSIONER_CAST_SPELL, 1F, 1.4F);
        magus.getWorld().playSound(magus.getLocation(), Sound.ITEM_BOOK_PAGE_TURN, 1.2F, 1.4F);
    }

    /**
     * The blink: he folds in (with any reflection he'll swap with) and vanishes on the clip's release, 9 ticks later,
     * reappearing at a new spot or in a reflection's place (which takes his).
     */
    private void blink() {
        if (!magus.isValid()) {
            return;
        }
        busyUntil = Math.max(busyUntil, ticks + BLINK_WINDUP + 8);
        Illager swap = !decoys.isEmpty() && ThreadLocalRandom.current().nextBoolean()
            ? decoys.get(ThreadLocalRandom.current().nextInt(decoys.size())) : null;
        act(magus, "BLINK", null);
        if (swap != null) {
            act(swap, "BLINK", null);
        }
        later(BLINK_WINDUP, () -> {
            if (!magus.isValid()) {
                return;
            }
            Location from = magus.getLocation();
            Location to;
            if (swap != null && swap.isValid()) {
                to = swap.getLocation();
                swap.teleport(from);
            } else {
                to = fight.randomPoint(3, fight.radius() - 3);
            }
            from.getWorld().spawnParticle(Particle.CLOUD, from.clone().add(0, 1, 0), 15, 0.3, 0.6, 0.3, 0.02);
            magus.teleport(to);
            to.getWorld().playSound(to, Sound.ENTITY_ILLUSIONER_MIRROR_MOVE, 1F, 1F);
        });
    }

    private static void dress(Illager illager) {
        illager.setCustomName(ChatColor.BLUE + "Masquerade");
        illager.setCustomNameVisible(true);
        illager.setCanJoinRaid(false);
        illager.setPatrolLeader(false);
    }
}
