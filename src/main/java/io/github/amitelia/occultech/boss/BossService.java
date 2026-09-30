package io.github.amitelia.occultech.boss;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.block.Block;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
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
    private double healthMultiplier = 1.0;
    private double healthPerExtraPlayer = 0.25;

    public BossService(Plugin plugin, FightHooks hooks) {
        this.plugin = plugin;
        this.hooks = hooks;
    }

    public void start() {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        task = Bukkit.getScheduler().runTaskTimer(plugin, this::tick, STEP, STEP);
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

    /** False if another fight's arena would overlap an arena of this radius at this altar. */
    public boolean canSummon(@Nonnull Location altar, double radius) {
        for (BossFight fight : fights.values()) {
            Location other = fight.center();
            if (other.getWorld() == altar.getWorld() && other.distance(altar.clone().add(0.5, 1, 0.5)) < fight.radius() + radius) {
                return false;
            }
        }
        return true;
    }

    @Nonnull
    public Optional<BossFight> fightAt(@Nonnull Block altar) {
        return fights.values().stream().filter(f -> f.altar().equals(altar)).findFirst();
    }

    @Nonnull
    public BossFight summon(@Nonnull String bossId, @Nonnull BossSpec spec, @Nonnull Block altar, @Nullable ItemStack refund) {
        BossBlueprint blueprint = blueprints.get(bossId);
        if (blueprint == null) {
            throw new IllegalArgumentException("No behavior registered for boss " + bossId);
        }
        BossFight fight = new BossFight(this, spec, blueprint, altar, refund);
        fights.put(fight.id(), fight);
        hooks.markActive(altar, refund);
        fight.start();
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
    }

    Plugin plugin() {
        return plugin;
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
        return null;
    }

    // ------------------------------------------------------------------ damage & targeting

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onDamage(EntityDamageEvent e) {
        Entity victim = e.getEntity();
        if (!Keys.isSummoned(victim)) {
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
            if (!fromFight) {
                e.setCancelled(true);
            }
            return;
        }
        if (!PLAYER_CAUSES.contains(e.getCause())) {
            e.setCancelled(true);
            return;
        }

        BossFight fight = fightOf(victim);
        if (fight != null && fight.isBoss(victim) && victim instanceof LivingEntity boss) {
            e.setDamage(fight.onBossDamagedByPlayer(boss, player, e.getDamage()));
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
        if (Keys.isSummoned(e.getEntity()) && e.getTarget() != null && !(e.getTarget() instanceof Player)) {
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
            object.hit();
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
        }
    }

    @EventHandler
    public void onDeath(EntityDeathEvent e) {
        if (!Keys.isSummoned(e.getEntity())) {
            return;
        }
        e.getDrops().clear();
        e.setDroppedExp(0);
        BossFight fight = fightOf(e.getEntity());
        if (fight != null) {
            fight.onEntityDeath(e.getEntity());
        }
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
