package io.github.amitelia.occultech.boss;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Chunk;
import org.bukkit.Location;
import org.bukkit.block.Block;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.ChatColor;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.entity.Tameable;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityChangeBlockEvent;
import org.bukkit.event.entity.EntityCombustEvent;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.entity.EntityDamageEvent.DamageCause;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.EntityExplodeEvent;
import org.bukkit.event.entity.EntityPortalEvent;
import org.bukkit.event.entity.EntityTargetLivingEntityEvent;
import org.bukkit.event.entity.EntityTransformEvent;
import org.bukkit.event.entity.ProjectileLaunchEvent;
import org.bukkit.event.entity.SlimeSplitEvent;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.entity.PlayerLeashEntityEvent;
import org.bukkit.event.world.EntitiesLoadEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitTask;

import io.github.amitelia.occultech.core.Keys;
import io.papermc.paper.event.player.PrePlayerAttackEntityEvent;

/**
 * Runs all boss fights and enforces the engine's anti-abuse rules through events:
 * <ul>
 * <li>summoned entities never change blocks, burn in daylight, split, transform, use portals, get leashed, ridden,
 * name-tagged or traded with, and give no vanilla drops or XP</li>
 * <li>they only take damage from players (or from each other); environmental damage is ignored</li>
 * <li>they only target players</li>
 * <li>summoned entities left over from a crash are removed when their chunk loads</li>
 * </ul>
 */
public final class BossService implements Listener {

    public static final int STEP = 5;

    private static final Set<DamageCause> PLAYER_CAUSES = EnumSet.of(DamageCause.ENTITY_ATTACK, DamageCause.ENTITY_SWEEP_ATTACK,
        DamageCause.PROJECTILE, DamageCause.MAGIC, DamageCause.THORNS, DamageCause.ENTITY_EXPLOSION);

    private final Plugin plugin;
    private final FightHooks hooks;
    private final Map<String, BossBlueprint> blueprints = new HashMap<>();
    private final Map<UUID, BossFight> fights = new LinkedHashMap<>();
    private BukkitTask task;
    private BukkitTask moveTask;
    private double healthMultiplier = 1.0;
    private double healthPerExtraPlayer = 0.25;

    public BossService(Plugin plugin, FightHooks hooks) {
        this.plugin = plugin;
        this.hooks = hooks;
    }

    public void start() {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        task = Bukkit.getScheduler().runTaskTimer(plugin, this::tick, STEP, STEP);
        // scripted movement runs every tick, so puppeted bosses glide instead of lurching once per step
        moveTask = Bukkit.getScheduler().runTaskTimer(plugin, this::move, 1L, 1L);
    }

    /** Boss health tuning (from config.yml). */
    public void setHealthScaling(double multiplier, double perExtraPlayer) {
        this.healthMultiplier = Math.max(0.05, multiplier);
        this.healthPerExtraPlayer = Math.max(0, perExtraPlayer);
    }

    double healthMultiplier() {
        return healthMultiplier;
    }

    double healthPerExtraPlayer() {
        return healthPerExtraPlayer;
    }

    public void register(@Nonnull BossBlueprint blueprint) {
        blueprints.put(blueprint.id(), blueprint);
    }

    public boolean has(@Nonnull String bossId) {
        return blueprints.containsKey(bossId);
    }

    /** Summons still channeling: altar block -> arena radius. They hold their area like a running fight. */
    private final Map<Location, Double> reserved = new HashMap<>();
    private double minFightDistance = 96;
    private int awayTicks = 180 * 20;
    private boolean awayRules = true;
    /** Banish requests waiting for their confirming second use: player -> (fight, when). */
    private final Map<UUID, Map.Entry<UUID, Long>> banishRequests = new HashMap<>();

    /** How long a fight waits with nobody alive in its arena before it ends (config {@code bosses.away-seconds}). */
    public void setAwaySeconds(int seconds) {
        this.awayTicks = Math.max(5, seconds) * 20;
    }

    int awayTicks() {
        return awayTicks;
    }

    /** The self-test runs fights with nobody watching: it turns the away timer off while it does. */
    public void setAwayRules(boolean on) {
        this.awayRules = on;
    }

    boolean awayRules() {
        return awayRules;
    }

    /** The running fight whose altar is nearest {@code at}, within {@code range} blocks of its arena's edge. */
    @Nullable
    public BossFight nearestFight(@Nonnull Location at, double range) {
        BossFight best = null;
        double bestDistance = Double.MAX_VALUE;
        for (BossFight fight : fights.values()) {
            if (fight.center().getWorld() != at.getWorld()) {
                continue;
            }
            double distance = fight.center().distance(at);
            if (distance <= fight.radius() + range && distance < bestDistance) {
                best = fight;
                bestDistance = distance;
            }
        }
        return best;
    }

    /**
     * Ends {@code fight} early for {@code player} (the Codex on its altar, or Banishing Salt). The first use only asks:
     * the same use again within 5 seconds banishes. True once banished.
     */
    public boolean requestBanish(@Nonnull Player player, @Nonnull BossFight fight) {
        if (!fight.mayBanish(player)) {
            player.sendMessage(ChatColor.GRAY + "Only its summoner or those who fought it can banish " + fight.spec().name() + ".");
            return false;
        }
        long now = System.currentTimeMillis();
        Map.Entry<UUID, Long> asked = banishRequests.get(player.getUniqueId());
        if (asked == null || !asked.getKey().equals(fight.id()) || now - asked.getValue() > 5000) {
            banishRequests.put(player.getUniqueId(), Map.entry(fight.id(), now));
            player.sendMessage(ChatColor.translateAlternateColorCodes('&', "&7Banish &c" + fight.spec().name()
                + "&7? The catalyst will be lost. &fDo it again within 5 seconds &7to banish."));
            return false;
        }
        banishRequests.remove(player.getUniqueId());
        fight.banish(player);
        return true;
    }

    /** Fights (running or channeling) must be at least this far apart, besides their arenas not overlapping. */
    public void setMinFightDistance(double blocks) {
        this.minFightDistance = Math.max(0, blocks);
    }

    /**
     * False if another fight - running, or a summon still channeling - is too close: arenas may not overlap, and fights
     * keep {@code bosses.min-fight-distance} apart. The altar's own reservation doesn't count.
     */
    public boolean canSummon(@Nonnull Location altar, double radius) {
        Location here = altar.getBlock().getLocation();
        Location center = here.clone().add(0.5, 1, 0.5);
        for (BossFight fight : fights.values()) {
            if (tooClose(fight.center(), fight.radius(), center, radius)) {
                return false;
            }
        }
        for (Map.Entry<Location, Double> other : reserved.entrySet()) {
            if (!other.getKey().equals(here) && tooClose(other.getKey().clone().add(0.5, 1, 0.5), other.getValue(), center, radius)) {
                return false;
            }
        }
        return true;
    }

    private boolean tooClose(Location a, double radiusA, Location b, double radiusB) {
        return a.getWorld() == b.getWorld() && a.distance(b) < Math.max(radiusA + radiusB, minFightDistance);
    }

    /** A summon starts channeling here: nothing else may start nearby until it ends ({@link #release}). */
    public void reserve(@Nonnull Location altar, double radius) {
        reserved.put(altar.getBlock().getLocation(), radius);
    }

    public void release(@Nonnull Location altar) {
        reserved.remove(altar.getBlock().getLocation());
    }

    @Nonnull
    public Optional<BossFight> fightAt(@Nonnull Block altar) {
        return fights.values().stream().filter(f -> f.altar().equals(altar)).findFirst();
    }

    @Nonnull
    public BossFight summon(@Nonnull String bossId, @Nonnull BossSpec spec, @Nonnull Block altar, @Nullable ItemStack refund) {
        return summon(bossId, spec, altar, refund, null);
    }

    /** Summons a boss; {@code summoner} may banish it later even before hitting it. */
    @Nonnull
    public BossFight summon(@Nonnull String bossId, @Nonnull BossSpec spec, @Nonnull Block altar, @Nullable ItemStack refund,
        @Nullable UUID summoner) {
        BossBlueprint blueprint = blueprints.get(bossId);
        if (blueprint == null) {
            throw new IllegalArgumentException("No behavior registered for boss " + bossId);
        }
        BossFight fight = new BossFight(this, spec, blueprint, altar, refund);
        fight.setSummoner(summoner);
        fights.put(fight.id(), fight);
        hooks.markActive(altar, refund);
        fight.start();
        return fight;
    }

    /**
     * Brings back a fight saved by a restart or crash (Session P3): a fresh spawn for the same group size, then the saved
     * clock, health and fighters. Null if the boss no longer exists.
     */
    @Nullable
    public BossFight resume(@Nonnull FightState state, @Nonnull BossSpec spec, @Nonnull Block altar, @Nullable ItemStack refund) {
        BossBlueprint blueprint = blueprints.get(state.bossId());
        if (blueprint == null) {
            return null;
        }
        BossFight fight = new BossFight(this, spec, blueprint, altar, refund);
        fight.setSummoner(state.summoner());
        fight.setPlayersAtStart(state.playersAtStart());
        fights.put(fight.id(), fight);
        hooks.markActive(altar, refund);
        fight.start();
        fight.restore(state);
        fight.broadcast("&5The circle stirs - &c" + spec.name() + " &5returns to finish what was started.");
        return fight;
    }

    @Nonnull
    public Collection<BossFight> fights() {
        return Collections.unmodifiableCollection(fights.values());
    }

    /** Ends a fight without loot or refund (admin tools). */
    public void abort(@Nonnull BossFight fight) {
        fight.end(BossFight.Result.ABANDONED);
    }

    /** Ends a fight with a specific result, e.g. {@link BossFight.Result#SHUTDOWN} to test refunds. */
    public void abort(@Nonnull BossFight fight, @Nonnull BossFight.Result result) {
        fight.end(result);
    }

    /** Ends every fight with a refund; called on plugin disable. */
    public void shutdown() {
        for (BossFight fight : new ArrayList<>(fights.values())) {
            fight.end(BossFight.Result.SHUTDOWN);
        }
        if (task != null) {
            task.cancel();
        }
        if (moveTask != null) {
            moveTask.cancel();
        }
    }

    Plugin plugin() {
        return plugin;
    }

    /** Arenas can share chunks, so chunk tickets are counted: a chunk is released when the last fight lets go. */
    private final Map<Chunk, Integer> heldChunks = new HashMap<>();

    void holdChunks(List<Chunk> chunks) {
        for (Chunk chunk : chunks) {
            if (heldChunks.merge(chunk, 1, Integer::sum) == 1) {
                chunk.addPluginChunkTicket(plugin);
            }
        }
    }

    void releaseChunks(List<Chunk> chunks) {
        for (Chunk chunk : chunks) {
            Integer left = heldChunks.computeIfPresent(chunk, (c, n) -> n <= 1 ? null : n - 1);
            if (left == null) {
                chunk.removePluginChunkTicket(plugin);
            }
        }
    }

    FightHooks hooks() {
        return hooks;
    }

    void onFightEnded(BossFight fight) {
        fights.remove(fight.id());
    }

    private void tick() {
        for (BossFight fight : new ArrayList<>(fights.values())) {
            fight.tick();
        }
    }

    private void move() {
        for (BossFight fight : new ArrayList<>(fights.values())) {
            fight.move();
        }
    }

    @Nullable
    private BossFight fightOf(@Nullable Entity entity) {
        String id = Keys.fightOf(entity);
        if (id == null) {
            return null;
        }
        try {
            return fights.get(UUID.fromString(id));
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    /** The player responsible for damage: the attacker, a projectile's shooter or a pet's owner. */
    @Nullable
    private static Player responsiblePlayer(Entity damager) {
        if (damager instanceof Player player) {
            return player;
        }
        if (damager instanceof Projectile projectile && projectile.getShooter() instanceof Player player) {
            return player;
        }
        if (damager instanceof Tameable pet && pet.getOwner() instanceof Player player) {
            return player;
        }
        // necromancy minions (and their arrows) fight for their owner
        Entity source = damager instanceof Projectile p && p.getShooter() instanceof Entity shooter ? shooter : damager;
        UUID owner = Keys.minionOwner(source);
        return owner == null ? null : Bukkit.getPlayer(owner);
    }

    // ------------------------------------------------------------------ damage & targeting

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onDamage(EntityDamageEvent e) {
        Entity victim = e.getEntity();
        if (!Keys.isSummoned(victim)) {
            return;
        }
        if (Keys.isUnhittable(victim)) {
            // mounts and protected riders: nothing hurts them, not even creative players (who ignore invulnerability)
            e.setCancelled(true);
            return;
        }
        if (!(e instanceof EntityDamageByEntityEvent byEntity)) {
            // environment can't hurt summoned creatures (walls, lava, falls, cramming, drowning...)
            if (e.getCause() != DamageCause.KILL && e.getCause() != DamageCause.WORLD_BORDER) {
                e.setCancelled(true);
            }
            return;
        }

        Entity damager = byEntity.getDamager();
        Player player = responsiblePlayer(damager);
        if (player == null) {
            // summoned creatures may hurt each other (e.g. a stray splash potion); other mobs may not help
            boolean fromFight = Keys.isSummoned(damager)
                || (damager instanceof Projectile p && p.getShooter() instanceof Entity shooter && Keys.isSummoned(shooter));
            // ...but a boss is never hurt by its own fight (e.g. The Unbound's thralls, stray fireballs), only by players
            BossFight own = fightOf(victim);
            if (!fromFight || (own != null && own.isBoss(victim))) {
                e.setCancelled(true);
            }
            return;
        }
        if (!PLAYER_CAUSES.contains(e.getCause())) {
            e.setCancelled(true);
            return;
        }
        BossFight arena = fightOf(victim);
        if (arena != null && !arena.inArena(player)) {
            // fought from outside the circle (a bow from the treeline, a pet sent in): it doesn't count
            e.setCancelled(true);
            outsideHint(player);
            return;
        }
        String owner = victim.getPersistentDataContainer().get(Keys.OWNED_BY, PersistentDataType.STRING);
        if (owner != null && !owner.equals(player.getUniqueId().toString())) {
            // someone else's reflection: everyone breaks their own
            e.setCancelled(true);
            return;
        }

        BossFight fight = fightOf(victim);
        if (fight != null && fight.isBoss(victim) && victim instanceof LivingEntity boss) {
            e.setDamage(fight.onBossDamagedByPlayer(boss, player, e.getDamage()));
        }
    }

    /** Fight projectiles can carry their own damage (vanilla tridents and fireballs are too weak for later tiers). */
    @EventHandler(ignoreCancelled = true)
    public void onProjectileHit(EntityDamageByEntityEvent e) {
        if (e.getEntity() instanceof Player && e.getDamager() instanceof Projectile projectile) {
            Double damage = projectile.getPersistentDataContainer().get(Keys.DAMAGE, PersistentDataType.DOUBLE);
            if (damage != null && Keys.isSummoned(projectile)) {
                e.setDamage(damage);
            }
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPlayerHurt(EntityDamageByEntityEvent e) {
        if (!(e.getEntity() instanceof Player)) {
            return;
        }
        Entity source = e.getDamager();
        if (source instanceof Projectile projectile && projectile.getShooter() instanceof Entity shooter) {
            source = shooter;
        }
        BossFight fight = fightOf(source);
        if (fight != null) {
            fight.onPlayerHitByFight();
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onTarget(EntityTargetLivingEntityEvent e) {
        Entity target = e.getTarget();
        if (!Keys.isSummoned(e.getEntity()) || target == null || target instanceof Player) {
            return;
        }
        // players' necromancy minions are fair game; so are the fight's own extras (e.g. the Unbound's thralls)
        boolean minion = Keys.minionOwner(target) != null;
        boolean sameFight = Keys.isSummoned(target) && java.util.Objects.equals(Keys.fightOf(target), Keys.fightOf(e.getEntity()));
        if (!minion && !sameFight) {
            e.setCancelled(true);
        }
    }

    /** Vexes and fangs an evoker boss creates on its own become part of its fight. */
    @EventHandler(ignoreCancelled = true)
    public void onSpawn(org.bukkit.event.entity.EntitySpawnEvent e) {
        Entity owner = null;
        if (e.getEntity() instanceof org.bukkit.entity.Vex vex) {
            owner = vex.getSummoner();
        } else if (e.getEntity() instanceof org.bukkit.entity.EvokerFangs fangs) {
            owner = fangs.getOwner();
        }
        BossFight fight = fightOf(owner);
        if (fight != null && !Keys.isSummoned(e.getEntity()) && !fight.adopt(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onObjectAttack(PrePlayerAttackEntityEvent e) {
        BossFight fight = fightOf(e.getAttacked());
        if (fight == null) {
            return;
        }
        BossFight.FightObject object = fight.objectFor(e.getAttacked());
        if (object != null) {
            e.setCancelled(true);
            if (fight.inArena(e.getPlayer())) {
                object.hit();
            } else {
                outsideHint(e.getPlayer());
            }
        }
    }

    // ------------------------------------------------------------------ no griefing, no abuse

    @EventHandler(ignoreCancelled = true)
    public void onChangeBlock(EntityChangeBlockEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onExplode(EntityExplodeEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.blockList().clear();
        }
    }

    /** Fireballs and other fight sources never light blocks. */
    @EventHandler(ignoreCancelled = true)
    public void onIgnite(org.bukkit.event.block.BlockIgniteEvent e) {
        Entity source = e.getIgnitingEntity();
        if (source instanceof Projectile projectile && projectile.getShooter() instanceof Entity shooter && Keys.isSummoned(shooter)) {
            e.setCancelled(true);
        } else if (Keys.isSummoned(source)) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onCombust(EntityCombustEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onSplit(SlimeSplitEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onTransform(EntityTransformEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onPortal(EntityPortalEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onLeash(PlayerLeashEntityEvent e) {
        if (Keys.isSummoned(e.getEntity())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onInteract(PlayerInteractEntityEvent e) {
        // name tags, riding, trading, feeding: none of it works on summoned creatures
        if (Keys.isSummoned(e.getRightClicked())) {
            e.setCancelled(true);
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onLaunch(ProjectileLaunchEvent e) {
        if (e.getEntity().getShooter() instanceof Entity shooter && Keys.isSummoned(shooter)) {
            e.getEntity().getPersistentDataContainer().set(Keys.SUMMONED, PersistentDataType.BYTE, (byte) 1);
            String fight = Keys.fightOf(shooter);
            if (fight != null) {
                e.getEntity().getPersistentDataContainer().set(Keys.FIGHT, PersistentDataType.STRING, fight);
            }
            if (e.getEntity() instanceof AbstractArrow arrow) {
                arrow.setPickupStatus(AbstractArrow.PickupStatus.DISALLOWED);
            }
            // tracked, so nothing a boss fired outlives its fight
            BossFight owner = fightOf(shooter);
            if (owner != null) {
                owner.adopt(e.getEntity());
            }
        }
    }

    @EventHandler
    public void onDeath(EntityDeathEvent e) {
        if (!Keys.isSummoned(e.getEntity())) {
            return;
        }
        e.getDrops().clear();
        e.setDroppedExp(0);
        // corpses finish their death animation only while ticked; far from players they can linger forever
        Entity corpse = e.getEntity();
        Bukkit.getScheduler().runTaskLater(plugin, corpse::remove, 22L);
        BossFight fight = fightOf(e.getEntity());
        if (fight != null) {
            fight.onEntityDeath(e.getEntity(), e.getEntity().getKiller());
        }
    }

    private final Map<UUID, Long> lastHint = new HashMap<>();

    private void outsideHint(Player player) {
        long now = System.currentTimeMillis();
        if (now - lastHint.getOrDefault(player.getUniqueId(), 0L) > 3000) {
            lastHint.put(player.getUniqueId(), now);
            player.sendActionBar(net.kyori.adventure.text.Component.text("Only blows struck inside the circle reach it.",
                net.kyori.adventure.text.format.NamedTextColor.GRAY));
        }
    }

    /** A player who dies in a fight, or disconnects from one, is excused: the boss waits for them instead of recovering. */
    @EventHandler
    public void onPlayerDeath(org.bukkit.event.entity.PlayerDeathEvent e) {
        for (BossFight fight : fights.values()) {
            fight.excuse(e.getEntity());
        }
    }

    @EventHandler
    public void onQuit(org.bukkit.event.player.PlayerQuitEvent e) {
        for (BossFight fight : fights.values()) {
            fight.excuse(e.getPlayer());
        }
        banishRequests.remove(e.getPlayer().getUniqueId());
        lastHint.remove(e.getPlayer().getUniqueId());
    }

    @EventHandler
    public void onEntitiesLoad(EntitiesLoadEvent e) {
        for (Entity entity : e.getEntities()) {
            if (Keys.isSummoned(entity) && fightOf(entity) == null) {
                // left over from a crash or unload: the fight no longer exists
                entity.remove();
            }
        }
    }
}
