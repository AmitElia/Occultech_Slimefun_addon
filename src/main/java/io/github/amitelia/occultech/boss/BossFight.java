package io.github.amitelia.occultech.boss;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Chunk;
import org.bukkit.Color;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.block.Block;
import org.bukkit.boss.BarColor;
import org.bukkit.boss.BarStyle;
import org.bukkit.boss.BossBar;
import org.bukkit.entity.AreaEffectCloud;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Interaction;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Player;
import org.bukkit.inventory.EntityEquipment;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.core.Keys;

/**
 * One running boss fight at an altar. Owns every entity it spawns and removes all of them when it ends.
 * <p>
 * Engine rules applied here: arena leash, anti-pillaring, abandonment and time limits, boss bar, contribution
 * tracking and personal loot. Rules that need events (no block changes, no vanilla drops, no leashing, ...) live in
 * {@link BossService}.
 */
public final class BossFight {

    /**
     * Held weapons (Wyrmbreath, Gaze, Censer, Stormstring) deal small damage many times a second; boss armor is tuned for
     * big single hits, so these count this much more against bosses.
     */
    private static final double HELD_WEAPON_BONUS = 2.5;

    public enum Result { VICTORY, ABANDONED, BANISHED, TIMEOUT, UNLOADED, SHUTDOWN, ERROR, DISMISSED }

    /** Share of a boss's max health it regains per second while everyone has walked out of the arena. */
    private static final double AWAY_REGEN_PER_SECOND = 0.02;
    private static final int PILLAR_TICKS = 10 * 20;
    private static final int MAX_ADDS = 10;
    private static final double MIN_DAMAGE_SHARE = 0.05;
    private static final double MIN_PRESENCE_SHARE = 0.25;
    private static final double BONUS_DROP_CHANCE = 0.25;

    /** A zone on the ground that affects players standing in it, drawn with a colored lingering cloud. */
    private record Hazard(Location center, double radius, int until, Consumer<Player> effect, Entity visual, String label) {}

    // ------------------------------------------------------------------ Session B1: every hit attributed

    /** The fight and mechanic of the damage being dealt right now (read by the combat log's damage listener). */
    record Hit(BossFight fight, String label) {}

    static final ThreadLocal<Hit> CURRENT = new ThreadLocal<>();
    /** Entity data: the mechanic a creature's melee or a projectile deals (for the combat log). */
    static final org.bukkit.NamespacedKey MECHANIC = new org.bukkit.NamespacedKey("occultech", "mechanic");

    private CombatLog log;

    CombatLog log() {
        if (log == null) {
            log = new CombatLog(spec.id(), spec.tier());
        }
        return log;
    }

    /** Lines for {@code /occultech fights stats}. */
    @Nonnull
    public List<String> stats() {
        return log().summary(elapsed);
    }

    /**
     * Deals {@code mechanic} to {@code victim} from {@code source}: every scripted hit goes through here, so the combat
     * log knows what hurt whom. Magic ignores armor (Protection still counts), like the vanilla guardian laser.
     */
    public void hit(LivingEntity victim, Mechanic mechanic, LivingEntity source) {
        hit(victim, mechanic, mechanic.damage(), source);
    }

    /** As {@link #hit(LivingEntity, Mechanic, LivingEntity)} with an amount worked out on the spot (a reflected share). */
    public void hit(LivingEntity victim, Mechanic mechanic, double amount, LivingEntity source) {
        CURRENT.set(new Hit(this, mechanic.name()));
        try {
            if (mechanic.ignoresArmor()) {
                victim.damage(amount, org.bukkit.damage.DamageSource.builder(org.bukkit.damage.DamageType.INDIRECT_MAGIC)
                    .withCausingEntity(source).withDirectEntity(source).build());
            } else {
                victim.damage(amount, source);
            }
        } finally {
            CURRENT.remove();
        }
    }

    /**
     * Marks a creature's melee, or a projectile (fangs, a thrown potion), as {@code mechanic}: a creature gets that attack
     * damage, anything else deals exactly the mechanic's damage when it hits a player.
     */
    public void label(Entity entity, Mechanic mechanic) {
        entity.getPersistentDataContainer().set(MECHANIC, PersistentDataType.STRING, mechanic.name());
        if (entity instanceof LivingEntity living) {
            setAttribute(living, Attribute.ATTACK_DAMAGE, mechanic.damage());
        } else {
            entity.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, mechanic.damage());
        }
    }

    /**
     * What {@code owner}'s own vanilla attacks of {@code type} deal - an illusioner's arrows, an evoker's vexes and fangs:
     * each one is labelled {@code mechanic} as it appears (see {@link BossService}).
     */
    public void labelSpawns(LivingEntity owner, org.bukkit.entity.EntityType type, Mechanic mechanic) {
        owner.getPersistentDataContainer().set(spawnsKey(type), PersistentDataType.STRING, mechanic.name() + "|" + mechanic.damage());
    }

    static org.bukkit.NamespacedKey spawnsKey(org.bukkit.entity.EntityType type) {
        return new org.bukkit.NamespacedKey("occultech", "spawns_" + type.name().toLowerCase());
    }

    /** Labels {@code spawned} from its owner's {@link #labelSpawns}, if it has one for that kind. */
    void labelFromOwner(Entity owner, Entity spawned) {
        String line = owner == null ? null : owner.getPersistentDataContainer().get(spawnsKey(spawned.getType()), PersistentDataType.STRING);
        if (line != null) {
            int bar = line.lastIndexOf('|');
            label(spawned, new Mechanic(spec.id(), line.substring(0, bar), Double.parseDouble(line.substring(bar + 1)), Mechanic.Kind.PROJECTILE, false, false));
        }
    }

    private final Map<UUID, Integer> lastMelee = new HashMap<>();

    /** False if {@code attacker}'s vanilla melee hit comes before its behavior's cooldown is over (the hit is cancelled). */
    boolean meleeReady(Entity attacker) {
        int cooldown = behavior.meleeCooldownTicks();
        if (cooldown <= 0) {
            return true;
        }
        int now = Bukkit.getCurrentTick();
        Integer last = lastMelee.get(attacker.getUniqueId());
        if (last != null && now - last < cooldown) {
            return false;
        }
        lastMelee.put(attacker.getUniqueId(), now);
        return true;
    }

    /** Auras following their bosses (Session O5, phase 3). */
    private final List<AirEffects.Aura> auras = new ArrayList<>();

    /** Keeps {@code aura} on its host each step until it ends. */
    void trackAura(AirEffects.Aura aura) {
        auras.add(aura);
    }

    /** A hittable object (egg sac, ward crystal): an item display with an interaction hitbox. */
    public final class FightObject {

        private final ItemDisplay display;
        private final Interaction hitbox;
        private final Runnable onBreak;
        private int hits;

        private FightObject(ItemDisplay display, Interaction hitbox, int hits, Runnable onBreak) {
            this.display = display;
            this.hitbox = hitbox;
            this.hits = hits;
            this.onBreak = onBreak;
        }

        public boolean isAlive() {
            return hits > 0 && hitbox.isValid();
        }

        public Location location() {
            return display.getLocation();
        }

        void hit() {
            if (--hits > 0) {
                display.getWorld().spawnParticle(Particle.CRIT, display.getLocation(), 8, 0.2, 0.2, 0.2, 0.1);
                display.getWorld().playSound(display.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_HIT, 1F, 1.2F);
                return;
            }
            display.getWorld().spawnParticle(Particle.BLOCK, display.getLocation(), 20, 0.3, 0.3, 0.3, Material.COBWEB.createBlockData());
            display.getWorld().playSound(display.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_BREAK, 1F, 0.8F);
            AirEffects.burst(BossFight.this, display.getLocation().clone().add(0, 0.6, 0), AirEffects.Burst.SOUL, Color.fromRGB(180, 140, 255), 2.4F);
            remove();
            onBreak.run();
        }

        /** Remove without triggering the break callback (e.g. an egg sac that hatched). */
        public void remove() {
            hits = 0;
            display.remove();
            hitbox.remove();
            objects.remove(hitbox.getUniqueId());
        }
    }

    private final UUID id = UUID.randomUUID();
    private final BossService service;
    private final BossSpec spec;
    private final Block altar;
    private final Location center;
    private final ItemStack refund;
    /**
     * An event fight (the Staff Raid): started by admins at an arena, not by a ritual. No altar, catalyst, loot or saved
     * state; its health is set by its behavior; with nobody near, it just waits.
     */
    private final boolean event;
    private final BossBehavior behavior;
    private final BossBar bar;
    private int playersAtStart;
    /** Every main boss in spawn order, dead ones too: saved health lines up with a fresh spawn on resume. */
    private final List<LivingEntity> spawnedBosses = new ArrayList<>();
    private int saveCounter;

    private final List<LivingEntity> bosses = new ArrayList<>();
    private final List<Entity> extras = new ArrayList<>();
    private final List<Hazard> hazards = new ArrayList<>();
    private final Map<UUID, FightObject> objects = new HashMap<>();
    private final Map<UUID, Double> damage = new HashMap<>();
    private final Map<UUID, Integer> presence = new HashMap<>();
    private final Set<UUID> tainted = new HashSet<>();

    private int elapsed;
    private int lastBossHit;
    private int lastBossDamaged = -1000;
    /** Ticks without a living player in the arena (Session P2: the away timer). */
    private int awayTicks;
    /** Players who died in the fight or disconnected from it and haven't come back yet: while one is out, the boss waits. */
    private final Set<UUID> excused = new HashSet<>();
    @Nullable private UUID summoner;
    private boolean ended;
    private Result result;

    BossFight(BossService service, BossSpec spec, BossBlueprint blueprint, Block altar, @Nullable ItemStack refund) {
        this(service, spec, blueprint, altar, refund, false);
    }

    BossFight(BossService service, BossSpec spec, BossBlueprint blueprint, Block altar, @Nullable ItemStack refund, boolean event) {
        this.service = service;
        this.event = event;
        this.spec = spec;
        this.altar = altar;
        this.center = altar.getLocation().add(0.5, 1, 0.5);
        this.refund = refund;
        this.playersAtStart = Math.max(1, playersInRadius(spec.arenaRadius()).size());
        this.bar = Bukkit.createBossBar(ChatColor.translateAlternateColorCodes('&', "&c" + spec.name()), BarColor.PURPLE, BarStyle.SEGMENTED_10);
        this.behavior = blueprint.factory().apply(this);
    }

    void start() {
        // keep the whole arena loaded, not just the altar's chunk, so nothing in the fight unloads mid-fight
        service.holdChunks(arenaChunks());
        behavior.spawn(center.clone());
        if (event) {
            center.getWorld().playSound(center, Sound.ENTITY_PLAYER_LEVELUP, 1F, 0.6F);
            return;
        }
        broadcast("&5The circle flares - &c" + spec.name() + " &5answers the summons!");
        center.getWorld().playSound(center, Sound.ENTITY_WITHER_SPAWN, 0.6F, 1.4F);
    }

    // ------------------------------------------------------------------ API for behaviors

    /** Spawns a main boss entity (the fight is won when all of them are dead), scaled for the group size. */
    @Nonnull
    public <T extends LivingEntity> T spawnBoss(Class<T> type, Location at, Consumer<T> setup) {
        T entity = at.getWorld().spawn(at, type, e -> {
            prepare(e);
            setup.accept(e);
            scaleHealth(e);
        });
        bosses.add(entity);
        spawnedBosses.add(entity);
        return entity;
    }

    /** Spawns an extra mob for this fight, or returns null when the extra-mob cap is reached. */
    @Nullable
    public <T extends LivingEntity> T spawnAdd(Class<T> type, Location at, Consumer<T> setup) {
        if (liveAdds() >= MAX_ADDS) {
            return null;
        }
        T entity = at.getWorld().spawn(at, type, e -> {
            prepare(e);
            setup.accept(e);
        });
        extras.add(entity);
        return entity;
    }

    /** Spawns a non-living fight entity (display, cloud, projectile) that is removed when the fight ends. */
    @Nonnull
    public <T extends Entity> T spawnExtra(Class<T> type, Location at, Consumer<T> setup) {
        T entity = at.getWorld().spawn(at, type, e -> {
            tag(e);
            e.setPersistent(false);
            setup.accept(e);
        });
        extras.add(entity);
        return entity;
    }

    /** A hittable object: {@code hits} player hits destroy it and run {@code onBreak}. */
    @Nonnull
    public FightObject spawnObject(Location at, Material look, float scale, int hits, Runnable onBreak) {
        ItemDisplay display = spawnExtra(ItemDisplay.class, at.clone().add(0, 0.4 * scale, 0), d -> {
            d.setItemStack(new ItemStack(look));
            d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(scale, scale, scale), new AxisAngle4f()));
            d.setBillboard(org.bukkit.entity.Display.Billboard.VERTICAL);
        });
        Interaction hitbox = spawnExtra(Interaction.class, at, i -> {
            i.setInteractionWidth(0.9F * scale);
            i.setInteractionHeight(0.9F * scale);
            i.setResponsive(true);
        });
        FightObject object = new FightObject(display, hitbox, hits, onBreak);
        objects.put(hitbox.getUniqueId(), object);
        return object;
    }

    /**
     * A ground hazard: a colored circle that applies {@code effect} to players inside once per second.
     * Uses a lingering-potion cloud for the visual, never the dragon-breath particle (bottles could collect it).
     */
    public void addHazard(Location at, double radius, int durationTicks, Color color, Consumer<Player> effect) {
        addHazard(at, radius, durationTicks, color, null, effect);
    }

    /**
     * A ground hazard drawn as its {@code zone}'s animated surface (Session O4 floor markings) when the resource pack is
     * in use; otherwise (or without a zone) a coloured potion-cloud circle.
     */
    public void addHazard(Location at, double radius, int durationTicks, Color color, @Nullable FloorDecals.Zone zone,
        Consumer<Player> effect) {
        if (zone != null && FloorDecals.enabled()) {
            Entity surface = FloorDecals.zone(this, at, radius, durationTicks, zone);
            hazards.add(new Hazard(at.clone(), radius, elapsed + durationTicks, effect, surface, "Zone: " + zone.name().toLowerCase()));
            return;
        }
        AreaEffectCloud cloud = spawnExtra(AreaEffectCloud.class, at, c -> {
            c.setRadius((float) radius);
            c.setRadiusPerTick(0);
            c.setDuration(durationTicks);
            c.setWaitTime(0);
            c.setParticle(Particle.ENTITY_EFFECT, color);
        });
        hazards.add(new Hazard(at.clone(), radius, elapsed + durationTicks, effect, cloud, zone == null ? "Hazard" : "Zone: " + zone.name().toLowerCase()));
    }

    /** A short-lived colored circle warning where something will hit. */
    public void telegraph(Location at, double radius, int durationTicks, Color color) {
        telegraph(at, radius, durationTicks, color, FloorDecals.Mark.DANGER);
    }

    /**
     * Warns where an attack will land: with the resource pack, a floor marking (Session O4) - a ring at the exact hit
     * radius, a fill growing to it as the hit nears, the attack's {@code mark} - tinted to {@code color}; without it, a
     * coloured particle circle.
     */
    public void telegraph(Location at, double radius, int durationTicks, Color color, FloorDecals.Mark mark) {
        if (FloorDecals.enabled()) {
            FloorDecals.warning(this, at, radius, durationTicks, color, mark);
            return;
        }
        spawnExtra(AreaEffectCloud.class, at, c -> {
            c.setRadius((float) radius);
            c.setRadiusPerTick(0);
            c.setDuration(durationTicks);
            c.setWaitTime(0);
            c.setParticle(Particle.ENTITY_EFFECT, color);
        });
        Particle.DustOptions dust = new Particle.DustOptions(color, 1.4F);
        for (int i = 0; i < 24; i++) {
            double angle = Math.PI * 2 * i / 24;
            at.getWorld().spawnParticle(Particle.DUST, at.clone().add(Math.cos(angle) * radius, 0.15, Math.sin(angle) * radius), 1, 0, 0, 0, 0, dust);
        }
    }

    /**
     * Whether {@code player} stands in the arena (Session P2): only hits from in here count, so nobody fights from outside.
     * A little slack past the edge, where the leash pushes bosses back.
     */
    public boolean inArena(Player player) {
        double reach = spec.arenaRadius() + 1.5;
        return player.getWorld() == center.getWorld() && player.getGameMode() != GameMode.SPECTATOR
            && player.getLocation().distanceSquared(center) <= reach * reach;
    }

    /** Who may end this fight early: whoever summoned it, anyone who has hurt the boss, or an operator. */
    public boolean mayBanish(Player player) {
        return player.isOp() || player.getUniqueId().equals(summoner) || damage.containsKey(player.getUniqueId());
    }

    /** Ends the fight now, without loot or refund (the summoners gave up). */
    public void banish(@Nullable Player by) {
        broadcast("&7" + (by == null ? "Someone" : by.getName()) + " banishes &c" + spec.name() + "&7. The catalyst is lost.");
        end(Result.BANISHED);
    }

    void setSummoner(@Nullable UUID summoner) {
        this.summoner = summoner;
    }

    /** A player died in the fight or disconnected from it: until they're back, the boss waits instead of recovering. */
    void excuse(Player player) {
        if (!ended && (presence.containsKey(player.getUniqueId()) || inArena(player))) {
            excused.add(player.getUniqueId());
        }
    }

    /** This fight as it stands, to resume it after a restart or crash. */
    @Nonnull
    public FightState state() {
        List<Double> health = new ArrayList<>();
        for (LivingEntity boss : spawnedBosses) {
            AttributeInstance max = boss.getAttribute(Attribute.MAX_HEALTH);
            health.add(boss.isDead() || !bosses.contains(boss) || max == null ? 0 : boss.getHealth() / max.getValue());
        }
        return new FightState(spec.id(), elapsed, health, playersAtStart, summoner, new HashMap<>(damage), new HashMap<>(presence));
    }

    void setPlayersAtStart(int players) {
        this.playersAtStart = Math.max(1, players);
    }

    /**
     * Picks up where {@code state} left off, right after the fresh spawn: the clock, each boss's health (bosses that were
     * dead die again), and who fought. Everyone who fought counts as away through no fault of their own: the boss waits.
     */
    void restore(FightState state) {
        elapsed = state.elapsed();
        damage.putAll(state.damage());
        presence.putAll(state.presence());
        excused.addAll(state.presence().keySet());
        for (int i = 0; i < spawnedBosses.size() && i < state.health().size(); i++) {
            LivingEntity boss = spawnedBosses.get(i);
            AttributeInstance max = boss.getAttribute(Attribute.MAX_HEALTH);
            double fraction = state.health().get(i);
            if (max != null && fraction <= 0) {
                boss.setHealth(0);
            } else if (max != null) {
                boss.setHealth(Math.max(1, Math.min(max.getValue(), fraction * max.getValue())));
            }
        }
        service.hooks().saveState(altar, state().format());
    }

    /** Ticks left on the away timer, or -1 while someone is in the arena. */
    public int awayTicksLeft() {
        return awayTicks == 0 ? -1 : Math.max(0, service.awayTicks() - awayTicks);
    }

    /** Players inside the arena (alive, not spectating). */
    @Nonnull
    public List<Player> players() {
        return playersInRadius(spec.arenaRadius());
    }

    @Nullable
    public Player randomPlayer() {
        List<Player> players = players();
        return players.isEmpty() ? null : players.get(ThreadLocalRandom.current().nextInt(players.size()));
    }

    @Nullable
    public Player nearestPlayer(Location to) {
        Player best = null;
        double bestDistance = Double.MAX_VALUE;
        for (Player player : players()) {
            double d = player.getLocation().distanceSquared(to);
            if (d < bestDistance) {
                best = player;
                bestDistance = d;
            }
        }
        return best;
    }

    /** A random point on the arena floor within {@code radius} of the center. */
    @Nonnull
    public Location randomPoint(double minRadius, double maxRadius) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        double angle = random.nextDouble(Math.PI * 2);
        double distance = minRadius + random.nextDouble(Math.max(0.01, maxRadius - minRadius));
        return center.clone().add(Math.cos(angle) * distance, 0, Math.sin(angle) * distance);
    }

    public int liveAdds() {
        int count = 0;
        for (Entity e : extras) {
            if (e instanceof LivingEntity living && !living.isDead() && living.isValid()) {
                count++;
            }
        }
        return count;
    }

    /** Remaining health of all main boss entities as a fraction of their combined maximum. */
    public double healthFraction() {
        double health = 0;
        double max = 0;
        for (LivingEntity boss : bosses) {
            AttributeInstance attribute = boss.getAttribute(Attribute.MAX_HEALTH);
            max += attribute == null ? 20 : attribute.getValue();
            health += boss.isDead() ? 0 : boss.getHealth();
        }
        return max <= 0 ? 0 : Math.max(0, Math.min(1, health / max));
    }

    /**
     * Health multiplier: the configured base, plus a configured share per extra player present when summoned. An event
     * fight's behavior sets its own health (raid scaling), so its multiplier is 1.
     */
    public double healthMultiplier() {
        return event ? 1 : service.healthMultiplier() * service.groupScaling().factor(playersAtStart);
    }

    /** Falls this fight caused and hasn't seen land yet: player -> the mechanic to log the fall under. */
    private final Map<UUID, String> falls = new HashMap<>();

    /**
     * {@code player} was thrown up by {@code mechanic} (a kidnap, an updraft): when they land, the combat log records the
     * fall damage under it. Only a record: the fall is ordinary vanilla fall damage.
     */
    public void expectFall(Player player, String mechanic) {
        falls.put(player.getUniqueId(), mechanic);
    }

    /** The mechanic a pending fall of {@code player} belongs to (taken: a fall is logged once), or null. */
    @Nullable
    String takeFall(UUID player) {
        return falls.remove(player);
    }

    // ------------------------------------------------------------------ Session E8: what a fight costs the server

    private long costNanos;
    private int costTicks;
    private double msPerTick;

    /** Adds {@code nanos} of server time spent on this fight. */
    void cost(long nanos) {
        costNanos += nanos;
    }

    /** One server tick passed: every 100, the average cost is worked out afresh. */
    void costTick() {
        if (++costTicks >= 100) {
            msPerTick = costNanos / 100.0 / 1_000_000.0;
            costNanos = 0;
            costTicks = 0;
        }
    }

    /** Average server time this fight took per tick over the last 5 s (ms). */
    public double msPerTick() {
        return msPerTick;
    }

    /** Living extra creatures and other fight entities (displays, projectiles...) it holds now. */
    public int entityCount() {
        int count = 0;
        for (Entity extra : extras) {
            if (extra.isValid()) {
                count++;
            }
        }
        return count + bosses.size();
    }

    /** This fight's behavior (the raid's tools look at their own). */
    @Nonnull
    public BossBehavior behavior() {
        return behavior;
    }

    /** Whether this is an event fight (the Staff Raid), not a summoned one. */
    public boolean isEvent() {
        return event;
    }

    public int playersAtStart() {
        return playersAtStart;
    }

    public void broadcast(String message) {
        String text = ChatColor.translateAlternateColorCodes('&', message);
        for (Player player : playersInRadius(spec.arenaRadius() + 16)) {
            player.sendMessage(text);
        }
    }

    public static void setAttribute(LivingEntity entity, Attribute attribute, double value) {
        AttributeInstance instance = entity.getAttribute(attribute);
        if (instance != null) {
            instance.setBaseValue(value);
        }
    }

    @Nonnull
    public List<LivingEntity> bosses() {
        return Collections.unmodifiableList(bosses);
    }

    @Nonnull
    public Location center() {
        return center.clone();
    }

    public double radius() {
        return spec.arenaRadius();
    }

    public int elapsed() {
        return elapsed;
    }

    @Nonnull
    public BossSpec spec() {
        return spec;
    }

    @Nonnull
    public UUID id() {
        return id;
    }

    @Nonnull
    public Block altar() {
        return altar;
    }

    public boolean isOver() {
        return ended;
    }

    @Nullable
    public Result result() {
        return result;
    }

    // ------------------------------------------------------------------ engine callbacks (from BossService)

    boolean isBoss(Entity entity) {
        return entity instanceof LivingEntity living && bosses.contains(living);
    }

    /** Whether a player's projectile about to hit {@code boss} should pass harmlessly instead (the behavior decides). */
    boolean deflects(LivingEntity boss, org.bukkit.entity.Projectile projectile) {
        try {
            return !ended && behavior.deflectProjectile(boss, projectile);
        } catch (RuntimeException e) {
            service.plugin().getLogger().severe("Boss " + spec.id() + " deflection failed: " + e);
            return false;
        }
    }

    @Nullable
    FightObject objectFor(Entity hitbox) {
        return objects.get(hitbox.getUniqueId());
    }

    double onBossDamagedByPlayer(LivingEntity boss, Player player, double amount) {
        double raw = Keys.HELD_WEAPON_HIT.get() ? amount * HELD_WEAPON_BONUS : amount;
        double modified = behavior.modifyIncomingDamage(boss, raw);
        behavior.onDamagedBy(boss, player, modified);
        if (player.getGameMode() == GameMode.CREATIVE) {
            tainted.add(player.getUniqueId());
        }
        damage.merge(player.getUniqueId(), Math.min(modified, boss.getHealth()), Double::sum);
        lastBossDamaged = elapsed;
        log().dealt(player.getUniqueId(), player.getName(), weaponOf(player), raw, modified, elapsed);
        return modified;
    }

    private static String weaponOf(Player player) {
        if (Keys.HELD_WEAPON_HIT.get()) {
            ItemStack using = player.getActiveItem();
            ItemStack held = using.getType().isAir() ? player.getInventory().getItemInMainHand() : using;
            return "held: " + itemName(held);
        }
        return itemName(player.getInventory().getItemInMainHand());
    }

    private static String itemName(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return "fist";
        }
        return item.hasItemMeta() && item.getItemMeta().hasDisplayName()
            ? org.bukkit.ChatColor.stripColor(item.getItemMeta().getDisplayName()) : item.getType().name().toLowerCase();
    }

    void onPlayerHitByFight() {
        lastBossHit = elapsed;
    }

    void onEntityDeath(Entity entity, @Nullable Player killer) {
        boolean boss = bosses.remove(entity);
        extras.remove(entity);
        if (!boss && !ended) {
            if (entity instanceof LivingEntity) {
                AirEffects.burst(this, entity.getLocation().add(0, entity.getHeight() / 2, 0), AirEffects.Burst.SOUL, Color.fromRGB(110, 220, 255), 2F);
            }
            behavior.onAddDeath(entity, killer);
        }
    }

    void tick() {
        if (ended) {
            return;
        }
        if (!event && ++saveCounter % 20 == 0) {   // every 5 s: a crash loses at most that much of the fight
            service.hooks().saveState(altar, state().format());
        }

        for (LivingEntity boss : bosses) {
            if (!boss.isValid() && !boss.isDead()) {
                end(Result.UNLOADED);
                return;
            }
        }
        bosses.removeIf(LivingEntity::isDead);
        if (bosses.isEmpty()) {
            end(Result.VICTORY);
            return;
        }

        List<Player> inArena = players();
        for (Player player : inArena) {
            presence.merge(player.getUniqueId(), BossService.STEP, Integer::sum);
            excused.remove(player.getUniqueId());
        }
        if (inArena.isEmpty() && event && service.awayRules()) {
            // an event fight waits for players to come over: no clock, no attacks, no recovery, no end
            // (the self-test turns the away rules off, and then it runs unattended like any fight)
            leash();
            leashAdds();
            extras.removeIf(e -> !e.isValid());
            updateBar();
            return;
        }
        if (inArena.isEmpty() && service.awayRules()) {
            away();
            return;
        }
        if (awayTicks > 0) {
            awayTicks = 0;
            bar.setTitle(ChatColor.translateAlternateColorCodes('&', "&c" + spec.name()));
            broadcast("&5" + spec.name() + " &7turns back to the circle.");
        }
        elapsed += BossService.STEP;
        if (elapsed >= spec.timeLimitSeconds() * 20) {
            end(Result.TIMEOUT);
            return;
        }

        leash();
        leashAdds();
        antiPillar(inArena);
        applyHazards();
        extras.removeIf(e -> !e.isValid());
        updateBar();

        try {
            behavior.tick();
            auras.removeIf(aura -> !aura.follow());
        } catch (RuntimeException e) {
            service.plugin().getLogger().severe("Boss " + spec.id() + " behavior failed: " + e);
            end(Result.ERROR);
        }
    }

    /**
     * Nobody alive in the arena: the fight pauses (no attacks, no scripted moves, the clock stops) for the away time, then
     * ends with the catalyst lost. If everyone walked off, the boss recovers meanwhile - stepping out to heal doesn't pay;
     * if someone died or disconnected, it waits as it is, so they can come back to the same fight.
     */
    private void away() {
        boolean waiting = !excused.isEmpty();
        int left = service.awayTicks() - awayTicks;
        if (awayTicks == 0 || left == 60 * 20 || left == 30 * 20) {
            String time = left / 1200 + ":" + String.format("%02d", left / 20 % 60);
            tellParticipants(waiting
                ? "&5" + spec.name() + " &7waits in the circle. Come back within &f" + time + "&7, or it fades with the catalyst."
                : "&7You left the circle: &c" + spec.name() + " &7recovers, and fades in &f" + time + " &7unless someone returns.");
        }
        awayTicks += BossService.STEP;
        if (awayTicks >= service.awayTicks()) {
            end(Result.ABANDONED);
            return;
        }
        if (!waiting) {
            for (LivingEntity boss : bosses) {
                heal(boss, AWAY_REGEN_PER_SECOND * BossService.STEP / 20.0);
            }
        }
        int seconds = (service.awayTicks() - awayTicks) / 20;
        bar.setTitle(ChatColor.translateAlternateColorCodes('&', "&c" + spec.name() + (waiting ? " &7- waiting " : " &7- recovering, fades in ")
            + seconds / 60 + ":" + String.format("%02d", seconds % 60)));
        leash();
        leashAdds();
        extras.removeIf(e -> !e.isValid());
        updateBar();
    }

    private void tellParticipants(String message) {
        String text = ChatColor.translateAlternateColorCodes('&', message);
        for (UUID id : presence.keySet()) {
            Player player = Bukkit.getPlayer(id);
            if (player != null) {
                player.sendMessage(text);
            }
        }
    }

    /** The player who has dealt the most damage so far (online and in the arena), or null. */
    @Nullable
    public Player topDamager() {
        Player best = null;
        double most = 0;
        for (Player player : players()) {
            double dealt = damage.getOrDefault(player.getUniqueId(), 0.0);
            if (dealt > most) {
                best = player;
                most = dealt;
            }
        }
        return best;
    }

    /** Every chunk the arena (plus a small margin) overlaps. */
    private List<Chunk> arenaChunks() {
        double reach = spec.arenaRadius() + 6;
        int minX = (int) Math.floor((center.getX() - reach) / 16);
        int maxX = (int) Math.floor((center.getX() + reach) / 16);
        int minZ = (int) Math.floor((center.getZ() - reach) / 16);
        int maxZ = (int) Math.floor((center.getZ() + reach) / 16);
        List<Chunk> chunks = new ArrayList<>();
        for (int x = minX; x <= maxX; x++) {
            for (int z = minZ; z <= maxZ; z++) {
                chunks.add(center.getWorld().getChunkAt(x, z));
            }
        }
        return chunks;
    }

    /** Every tick: the behavior's scripted movement. */
    void move() {
        if (ended || bosses.isEmpty() || awayTicks > 0) {
            return;
        }
        try {
            behavior.move();
        } catch (RuntimeException e) {
            service.plugin().getLogger().severe("Boss " + spec.id() + " movement failed: " + e);
            end(Result.ERROR);
        }
    }

    /** Ends the fight: loot on victory, refund when the players aren't at fault, and always removes everything. */
    void end(Result how) {
        if (ended) {
            return;
        }
        ended = true;
        result = how;

        switch (how) {
            case VICTORY -> {
                broadcast("&a" + spec.name() + " has been defeated!");
                center.getWorld().playSound(center, Sound.UI_TOAST_CHALLENGE_COMPLETE, 1F, 1F);
                if (!event) {
                    distributeLoot();
                }
            }
            case ABANDONED -> broadcast("&7The circle falls quiet. " + spec.name() + " fades away, and the catalyst with it.");
            case BANISHED -> center.getWorld().playSound(center, Sound.BLOCK_BEACON_DEACTIVATE, 1F, 0.6F);
            case TIMEOUT -> broadcast("&7" + spec.name() + " grows bored of you and fades away.");
            case SHUTDOWN -> {
                if (!event) {
                    // the fight is kept: saved here, it resumes when the altar loads again (Session P3)
                    service.hooks().saveState(altar, state().format());
                    broadcast("&7The circle holds its breath - " + spec.name() + " will return when the world wakes.");
                }
            }
            case DISMISSED -> center.getWorld().spawnParticle(Particle.CLOUD, center, 30, 0.6, 1, 0.6, 0.02);
            case UNLOADED, ERROR -> {
                broadcast("&7The ritual was interrupted. The catalyst returns to the altar.");
                if (refund != null) {
                    service.hooks().refund(altar, refund.clone());
                }
            }
        }

        for (LivingEntity boss : bosses) {
            boss.remove();
        }
        for (Entity extra : extras) {
            extra.remove();
        }
        bosses.clear();
        extras.clear();
        hazards.clear();
        objects.clear();
        bar.removeAll();
        service.releaseChunks(arenaChunks());
        if (log != null) {
            log.write(new java.io.File(service.plugin().getDataFolder(), "combat-log"), how.name(), elapsed, playersAtStart, healthMultiplier());
        }
        if (how != Result.SHUTDOWN && !event) {
            service.hooks().clearActive(altar);
        }
        service.onFightEnded(this);
    }

    // ------------------------------------------------------------------ internals

    private void prepare(LivingEntity entity) {
        tag(entity);
        // an event fight never resumes after a restart, so its creatures aren't saved with the world (the fight holds
        // their chunks loaded); a summoned fight's are, so it can resume (Session P3)
        entity.setPersistent(!event);
        entity.setRemoveWhenFarAway(false);
        entity.setCanPickupItems(false);
        EntityEquipment equipment = entity.getEquipment();
        if (equipment != null) {
            for (EquipmentSlot slot : EquipmentSlot.values()) {
                try {
                    equipment.setDropChance(slot, 0F);
                } catch (IllegalArgumentException ignored) {
                    // slot not supported by this entity type
                }
            }
        }
    }

    private void scaleHealth(LivingEntity entity) {
        AttributeInstance max = entity.getAttribute(Attribute.MAX_HEALTH);
        if (max != null) {
            max.setBaseValue(max.getBaseValue() * healthMultiplier());
            entity.setHealth(max.getValue());
        }
    }

    private void tag(Entity entity) {
        entity.getPersistentDataContainer().set(Keys.SUMMONED, PersistentDataType.BYTE, (byte) 1);
        entity.getPersistentDataContainer().set(Keys.FIGHT, PersistentDataType.STRING, id.toString());
    }

    /**
     * Keeps bosses in the arena. Past the edge they are pushed back in (no teleport, so fights near the edge flow);
     * only a boss far outside (or knocked out vertically) is placed back, just inside the edge where it left.
     */
    private void leash() {
        double radius = spec.arenaRadius();
        for (LivingEntity boss : bosses) {
            Location at = boss.getLocation();
            double dx = at.getX() - center.getX();
            double dz = at.getZ() - center.getZ();
            double distance = Math.sqrt(dx * dx + dz * dz);
            boolean vertical = Math.abs(at.getY() - center.getY()) > behavior.verticalLeash();
            if (at.getWorld() != center.getWorld() || vertical || distance > radius + 6) {
                Location back = distance < 0.1 ? center.clone() : center.clone().add(dx / distance * (radius - 3), 0, dz / distance * (radius - 3));
                back.setY(center.getY() + 1);
                back.setDirection(center.toVector().subtract(back.toVector()));
                boss.teleport(back);
                heal(boss, 0.02);
                boss.getWorld().spawnParticle(Particle.REVERSE_PORTAL, boss.getLocation(), 40, 0.5, 1, 0.5, 0.05);
            } else if (distance > radius) {
                org.bukkit.util.Vector inward = new org.bukkit.util.Vector(-dx / distance, 0, -dz / distance).multiply(0.5);
                boss.setVelocity(inward.setY(Math.max(boss.getVelocity().getY(), 0.1)));
            }
        }
    }

    /** Extra mobs that wander (or phase, like vexes) out of the arena are brought back. */
    private void leashAdds() {
        double limit = Math.pow(spec.arenaRadius() + 6, 2);
        for (Entity extra : extras) {
            if (extra instanceof LivingEntity living && !living.isDead()
                && (living.getWorld() != center.getWorld() || living.getLocation().distanceSquared(center) > limit)) {
                living.teleport(center.clone().add(0, 1, 0));
            }
        }
    }

    /** Takes over an entity the boss spawned itself (e.g. an evoker's vexes). False if the extra-mob cap is reached. */
    boolean adopt(Entity entity) {
        if (entity instanceof LivingEntity && liveAdds() >= MAX_ADDS) {
            return false;
        }
        tag(entity);
        entity.setPersistent(false);
        extras.add(entity);
        return true;
    }

    private void antiPillar(List<Player> inArena) {
        if (!behavior.usesAntiPillar() || inArena.isEmpty() || bosses.isEmpty()) {
            return;
        }
        boolean beingHurt = elapsed - lastBossDamaged < 100;
        if (elapsed - lastBossHit < PILLAR_TICKS || !beingHurt) {
            return;
        }
        LivingEntity boss = bosses.get(0);
        Player target = nearestPlayer(boss.getLocation());
        if (target == null) {
            return;
        }
        Location spot = safeSpotNear(target.getLocation());
        if (spot != null) {
            boss.getWorld().spawnParticle(Particle.REVERSE_PORTAL, boss.getLocation(), 30, 0.5, 1, 0.5, 0.05);
            boss.teleport(spot);
            boss.getWorld().playSound(spot, Sound.ENTITY_ENDERMAN_TELEPORT, 1F, 0.7F);
            if (boss instanceof Mob mob) {
                mob.setTarget(target);
            }
        }
        lastBossHit = elapsed;
    }

    @Nullable
    private Location safeSpotNear(Location at) {
        int[][] offsets = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 }, { 1, 1 }, { -1, -1 }, { 1, -1 }, { -1, 1 } };
        for (int[] offset : offsets) {
            Block feet = at.getBlock().getRelative(offset[0], 0, offset[1]);
            if (feet.isPassable() && feet.getRelative(0, 1, 0).isPassable() && !feet.getRelative(0, -1, 0).isPassable()) {
                Location spot = feet.getLocation().add(0.5, 0, 0.5);
                if (spot.distanceSquared(center) <= spec.arenaRadius() * spec.arenaRadius()) {
                    return spot;
                }
            }
        }
        return null;
    }

    private void applyHazards() {
        hazards.removeIf(h -> {
            if (elapsed >= h.until()) {
                h.visual().remove();
                return true;
            }
            return false;
        });
        if (elapsed % 20 != 0) {
            return;
        }
        for (Hazard hazard : hazards) {
            for (Player player : players()) {
                Location at = player.getLocation();
                double dx = at.getX() - hazard.center().getX();
                double dz = at.getZ() - hazard.center().getZ();
                if (dx * dx + dz * dz <= hazard.radius() * hazard.radius() && Math.abs(at.getY() - hazard.center().getY()) < 2) {
                    CURRENT.set(new Hit(this, hazard.label()));
                    try {
                        hazard.effect().accept(player);
                    } finally {
                        CURRENT.remove();
                    }
                }
            }
        }
    }

    private void updateBar() {
        bar.setProgress(healthFraction());
        // an event fight's bar shows only to players near its creatures: a raid has many fights over one arena
        Set<Player> viewers = event ? playersNearBosses(20) : new HashSet<>(playersInRadius(spec.arenaRadius() + 16));
        for (Player player : new ArrayList<>(bar.getPlayers())) {
            if (!viewers.contains(player)) {
                bar.removePlayer(player);
            }
        }
        viewers.forEach(bar::addPlayer);
    }

    /**
     * Rewards everyone who earned a share. A fighter who isn't online at the moment of victory (disconnected, crashed)
     * gets theirs when they next join (Session P4).
     */
    private void distributeLoot() {
        double total = damage.values().stream().mapToDouble(Double::doubleValue).sum();
        for (Map.Entry<UUID, Double> entry : damage.entrySet()) {
            Player player = Bukkit.getPlayer(entry.getKey());
            if (tainted.contains(entry.getKey())) {
                continue;
            }
            double share = total <= 0 ? 0 : entry.getValue() / total;
            double present = elapsed <= 0 ? 0 : presence.getOrDefault(entry.getKey(), 0) / (double) elapsed;
            if (share >= MIN_DAMAGE_SHARE && present >= MIN_PRESENCE_SHARE) {
                service.reward(entry.getKey(), spec.name(), rewards());
            } else if (player != null) {
                player.sendMessage(ChatColor.GRAY + "You didn't contribute enough to " + spec.name() + " to earn a reward.");
            }
        }
    }

    /** One share, rolled now: "sf:ID:n", "mc:MATERIAL:n", "xp:n", "win:BOSS" (see {@link BossService#reward}). */
    private List<String> rewards() {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        List<String> out = new ArrayList<>();
        out.add("sf:" + spec.dropId() + ":" + (spec.drops() + (random.nextDouble() < BONUS_DROP_CHANCE ? 1 : 0)));
        spec.bonusDrops().forEach((id, chance) -> {
            if (random.nextDouble() < chance) {
                out.add("sf:" + id + ":1");
            }
        });
        for (Map.Entry<String, int[]> drop : spec.mobDrops().entrySet()) {
            Material material = Material.matchMaterial(drop.getKey());
            int amount = random.nextInt(drop.getValue()[0], drop.getValue()[1] + 1);
            if (material != null && amount > 0) {
                out.add("mc:" + material.name() + ":" + amount);
            }
        }
        if (spec.xp() > 0) {
            out.add("xp:" + spec.xp());
        }
        out.add("win:" + spec.id());
        return out;
    }

    private void heal(LivingEntity entity, double fraction) {
        AttributeInstance max = entity.getAttribute(Attribute.MAX_HEALTH);
        if (max != null) {
            entity.setHealth(Math.min(max.getValue(), entity.getHealth() + max.getValue() * fraction));
        }
    }

    /** Heals a boss entity by a fraction of its maximum health. */
    public void healBoss(LivingEntity boss, double fraction) {
        heal(boss, fraction);
    }

    private Set<Player> playersNearBosses(double reach) {
        Set<Player> out = new HashSet<>();
        for (Player player : players()) {
            for (LivingEntity boss : bosses) {
                if (boss.getWorld() == player.getWorld() && boss.getLocation().distanceSquared(player.getLocation()) <= reach * reach) {
                    out.add(player);
                    break;
                }
            }
        }
        return out;
    }

    private List<Player> playersInRadius(double radius) {
        List<Player> out = new ArrayList<>();
        Collection<Player> players = center.getWorld().getPlayers();
        for (Player player : players) {
            if (!player.isDead() && player.getGameMode() != GameMode.SPECTATOR && player.getLocation().distanceSquared(center) <= radius * radius) {
                out.add(player);
            }
        }
        return out;
    }
}
