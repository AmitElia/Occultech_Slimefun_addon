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

    public enum Result { VICTORY, ABANDONED, TIMEOUT, UNLOADED, SHUTDOWN, ERROR }

    private static final int ABANDON_TICKS = 30 * 20;
    private static final int PILLAR_TICKS = 10 * 20;
    private static final int MAX_ADDS = 10;
    private static final double MIN_DAMAGE_SHARE = 0.05;
    private static final double MIN_PRESENCE_SHARE = 0.25;
    private static final double BONUS_DROP_CHANCE = 0.25;

    /** A zone on the ground that affects players standing in it, drawn with a colored lingering cloud. */
    private record Hazard(Location center, double radius, int until, Consumer<Player> effect, AreaEffectCloud cloud) {}

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
    private final BossBehavior behavior;
    private final BossBar bar;
    private final int playersAtStart;

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
    private int emptyTicks;
    private boolean ended;
    private Result result;

    BossFight(BossService service, BossSpec spec, BossBlueprint blueprint, Block altar, @Nullable ItemStack refund) {
        this.service = service;
        this.spec = spec;
        this.altar = altar;
        this.center = altar.getLocation().add(0.5, 1, 0.5);
        this.refund = refund;
        this.playersAtStart = Math.max(1, playersInRadius(spec.arenaRadius()).size());
        this.bar = Bukkit.createBossBar(ChatColor.translateAlternateColorCodes('&', "&c" + spec.name()), BarColor.PURPLE, BarStyle.SEGMENTED_10);
        this.behavior = blueprint.factory().apply(this);
    }

    void start() {
        Chunk chunk = altar.getChunk();
        chunk.addPluginChunkTicket(service.plugin());
        behavior.spawn(center.clone());
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
        AreaEffectCloud cloud = spawnExtra(AreaEffectCloud.class, at, c -> {
            c.setRadius((float) radius);
            c.setRadiusPerTick(0);
            c.setDuration(durationTicks);
            c.setWaitTime(0);
            c.setParticle(Particle.ENTITY_EFFECT, color);
        });
        hazards.add(new Hazard(at.clone(), radius, elapsed + durationTicks, effect, cloud));
    }

    /** A short-lived colored circle warning where something will hit. */
    public void telegraph(Location at, double radius, int durationTicks, Color color) {
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

    /** Health multiplier: the configured base, plus a configured share per extra player present when summoned. */
    public double healthMultiplier() {
        return service.healthMultiplier() * (1 + service.healthPerExtraPlayer() * (playersAtStart - 1));
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

    @Nullable
    FightObject objectFor(Entity hitbox) {
        return objects.get(hitbox.getUniqueId());
    }

    double onBossDamagedByPlayer(LivingEntity boss, Player player, double amount) {
        double modified = behavior.modifyIncomingDamage(boss, amount);
        if (player.getGameMode() == GameMode.CREATIVE) {
            tainted.add(player.getUniqueId());
        }
        damage.merge(player.getUniqueId(), Math.min(modified, boss.getHealth()), Double::sum);
        lastBossDamaged = elapsed;
        return modified;
    }

    void onPlayerHitByFight() {
        lastBossHit = elapsed;
    }

    void onEntityDeath(Entity entity, @Nullable Player killer) {
        boolean boss = bosses.remove(entity);
        extras.remove(entity);
        if (!boss && !ended) {
            behavior.onAddDeath(entity, killer);
        }
    }

    void tick() {
        if (ended) {
            return;
        }
        elapsed += BossService.STEP;

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
        }
        emptyTicks = inArena.isEmpty() ? emptyTicks + BossService.STEP : 0;
        if (emptyTicks >= ABANDON_TICKS) {
            end(Result.ABANDONED);
            return;
        }
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
        } catch (RuntimeException e) {
            service.plugin().getLogger().severe("Boss " + spec.id() + " behavior failed: " + e);
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
                distributeLoot();
            }
            case ABANDONED -> broadcast("&7The circle falls quiet. " + spec.name() + " fades away.");
            case TIMEOUT -> broadcast("&7" + spec.name() + " grows bored of you and fades away.");
            case UNLOADED, SHUTDOWN, ERROR -> {
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
        altar.getChunk().removePluginChunkTicket(service.plugin());
        service.hooks().clearActive(altar);
        service.onFightEnded(this);
    }

    // ------------------------------------------------------------------ internals

    private void prepare(LivingEntity entity) {
        tag(entity);
        entity.setPersistent(true);
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

    private void leash() {
        for (LivingEntity boss : bosses) {
            Location at = boss.getLocation();
            double dx = at.getX() - center.getX();
            double dz = at.getZ() - center.getZ();
            boolean outside = dx * dx + dz * dz > Math.pow(spec.arenaRadius() + 1.5, 2) || Math.abs(at.getY() - center.getY()) > behavior.verticalLeash();
            if (outside || at.getWorld() != center.getWorld()) {
                boss.teleport(center.clone().add(0, 1, 0));
                heal(boss, 0.02);
                boss.getWorld().spawnParticle(Particle.REVERSE_PORTAL, boss.getLocation(), 40, 0.5, 1, 0.5, 0.05);
            }
        }
    }

    /** Extra mobs that wander (or phase, like vexes) out of the arena are brought back. */
    private void leashAdds() {
        double limit = Math.pow(spec.arenaRadius() + 3, 2);
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
                h.cloud().remove();
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
                    hazard.effect().accept(player);
                }
            }
        }
    }

    private void updateBar() {
        bar.setProgress(healthFraction());
        Set<Player> viewers = new HashSet<>(playersInRadius(spec.arenaRadius() + 16));
        for (Player player : new ArrayList<>(bar.getPlayers())) {
            if (!viewers.contains(player)) {
                bar.removePlayer(player);
            }
        }
        viewers.forEach(bar::addPlayer);
    }

    private void distributeLoot() {
        double total = damage.values().stream().mapToDouble(Double::doubleValue).sum();
        for (Map.Entry<UUID, Double> entry : damage.entrySet()) {
            Player player = Bukkit.getPlayer(entry.getKey());
            if (player == null || tainted.contains(entry.getKey())) {
                continue;
            }
            double share = total <= 0 ? 0 : entry.getValue() / total;
            double present = elapsed <= 0 ? 0 : presence.getOrDefault(entry.getKey(), 0) / (double) elapsed;
            if (share >= MIN_DAMAGE_SHARE && present >= MIN_PRESENCE_SHARE) {
                int amount = spec.drops() + (ThreadLocalRandom.current().nextDouble() < BONUS_DROP_CHANCE ? 1 : 0);
                service.hooks().giveLoot(player, spec.dropId(), amount);
                spec.bonusDrops().forEach((id, chance) -> {
                    if (ThreadLocalRandom.current().nextDouble() < chance) {
                        service.hooks().giveLoot(player, id, 1);
                    }
                });
                giveMobDrops(player);
            } else {
                player.sendMessage(ChatColor.GRAY + "You didn't contribute enough to " + spec.name() + " to earn a reward.");
            }
        }
    }

    /** The boss's curated vanilla drops and XP, handed to one contributor (never dropped for others to grab). */
    private void giveMobDrops(Player player) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        for (Map.Entry<String, int[]> drop : spec.mobDrops().entrySet()) {
            Material material = Material.matchMaterial(drop.getKey());
            int amount = random.nextInt(drop.getValue()[0], drop.getValue()[1] + 1);
            if (material == null || amount <= 0) {
                continue;
            }
            for (ItemStack rest : player.getInventory().addItem(new ItemStack(material, amount)).values()) {
                player.getWorld().dropItem(player.getLocation(), rest).setOwner(player.getUniqueId());
            }
        }
        if (spec.xp() > 0) {
            player.giveExp(spec.xp());
        }
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
