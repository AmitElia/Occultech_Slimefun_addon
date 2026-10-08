package io.github.amitelia.occultech.event;

import java.io.File;
import java.io.IOException;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityToggleGlideEvent;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.PlayerRespawnEvent;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import io.github.amitelia.occultech.boss.BossService;

/**
 * The Staff Raid's home: the arena, the roster and settings from config, and the raid running now (at most one).
 * While a raid runs, players who die in the arena come back at its edge, and nobody glides with an elytra in it.
 */
public final class RaidService implements Listener {

    /** The raid is tuned for max-enchanted netherite: tier 2's benchmark kit. */
    public static final int BENCHMARK_TIER = 2;

    /** Loads the raid's attack classes, so the balance report sees their mechanics (ids starting {@code RAID_}). */
    public static void loadMechanics() {
        StaffKit.loadAll();
        try {
            Class.forName(ToolkitDemo.class.getName(), true, ToolkitDemo.class.getClassLoader());
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException(e);
        }
    }

    /** Whether a mechanic's boss id is one of the raid's. */
    public static boolean isRaid(String bossId) {
        return bossId.startsWith("RAID_");
    }

    private final JavaPlugin plugin;
    private final BossService bosses;
    private final File arenaFile;
    @Nullable private RaidArena arena;
    private StaffRoster roster;
    private StaffRaid.Settings settings;
    @Nullable private StaffRaid raid;
    /** A running toolkit demo (/occultech event demo), or null. */
    @Nullable private io.github.amitelia.occultech.boss.BossFight demo;
    private BukkitTask task;
    /** Players who died in the arena during the raid: they respawn at its edge. */
    private final Set<UUID> diedHere = new HashSet<>();

    public RaidService(@Nonnull JavaPlugin plugin, @Nonnull BossService bosses) {
        this.plugin = plugin;
        this.bosses = bosses;
        this.arenaFile = new File(plugin.getDataFolder(), "raid-arena.yml");
    }

    public void start() {
        load();
        Bukkit.getPluginManager().registerEvents(this, plugin);
        task = Bukkit.getScheduler().runTaskTimer(plugin, this::tick, BossService.STEP, BossService.STEP);
    }

    /** Reads the arena and config {@code raid.*} (the roster included). */
    public void load() {
        arena = RaidArena.load(arenaFile);
        ConfigurationSection config = plugin.getConfig().getConfigurationSection("raid");
        if (config == null) {
            config = plugin.getConfig().createSection("raid");
        }
        roster = StaffRoster.parse(config.getMapList("roster"));
        roster.problems().forEach(problem -> plugin.getLogger().warning("Raid roster: " + problem));
        RaidScaling scaling = new RaidScaling(config.getDouble("players-per-target", 2.5), config.getInt("max-targets", 10),
            config.getDouble("health-exponent", 0.9));
        settings = new StaffRaid.Settings(config.getDouble("staff-health", 600), config.getInt("act1-minutes", 8) * 60,
            Math.max(1, config.getInt("kills-per-target", 2)), scaling, Math.max(0.05, config.getDouble("health-multiplier", 1.0)));
    }

    public void shutdown() {
        stopDemo();
        if (raid != null) {
            raid.stop();
            raid = null;
        }
        if (task != null) {
            task.cancel();
        }
    }

    private void tick() {
        if (raid == null) {
            return;
        }
        raid.tick();
        if (raid.isOver()) {
            raid = null;
            diedHere.clear();
        }
    }

    // ------------------------------------------------------------------ admin

    /** Saves the arena here, or returns why it can't be. Empty problems = saved. */
    @Nonnull
    public List<String> setArena(@Nonnull RaidArena arena) {
        if (raid != null) {
            return List.of("a raid is running; stop it first");
        }
        try {
            arena.save(arenaFile);
        } catch (IOException e) {
            return List.of("could not save " + arenaFile.getName() + ": " + e.getMessage());
        }
        this.arena = arena;
        return List.of();
    }

    @Nullable
    public RaidArena arena() {
        return arena;
    }

    @Nonnull
    public StaffRoster roster() {
        return roster;
    }

    /**
     * Starts a raid, or returns why it can't start.
     *
     * @param targets staff on the floor at once (null: from the players in the arena)
     * @param players the player count to scale for (null: count the arena)
     */
    @Nonnull
    public List<String> begin(@Nullable Integer targets, @Nullable Integer players) {
        if (arena == null) {
            return List.of("no arena: stand in its middle and use /occultech event arena set <radius>");
        }
        return begin(arena, targets, players);
    }

    /** As {@link #begin(Integer, Integer)} at another arena than the saved one (the self-test's). */
    @Nonnull
    public List<String> begin(@Nonnull RaidArena arena, @Nullable Integer targets, @Nullable Integer players) {
        if (raid != null) {
            return List.of("a raid is already running");
        }
        stopDemo();
        List<String> problems = arena.problems();
        if (!problems.isEmpty()) {
            return problems;
        }
        if (roster.slots().size() < RaidScaling.MIN_TARGETS) {
            return List.of("the roster (config raid.roster) needs at least " + RaidScaling.MIN_TARGETS + " entries");
        }
        raid = new StaffRaid(bosses, arena, roster, settings, targets, players);
        raid.start();
        return List.of();
    }

    @Nullable
    StaffRaid raid() {
        return raid;
    }

    public boolean running() {
        return raid != null;
    }

    /** Staff beaten so far in the running raid. */
    public int kills() {
        return raid == null ? 0 : raid.kills();
    }

    public void stop() {
        if (raid != null) {
            raid.stop();
            raid = null;
            diedHere.clear();
        }
    }

    public void skip() {
        if (raid != null) {
            raid.skip();
        }
    }

    public void setHealthMultiplier(double multiplier) {
        if (raid != null) {
            raid.setHealthMultiplier(multiplier);
        }
    }

    /**
     * Starts the Act 2 toolkit demo: at {@code arena}'s middle when there is one, otherwise at {@code at} (20 blocks
     * around). {@code what} is one hazard (soak, marker, barrier, laser, ring) or "all"; {@code band} the pace, 1-3.
     */
    @Nonnull
    public List<String> startDemo(@Nullable RaidArena arena, @Nullable org.bukkit.Location at, String what, int band) {
        if (raid != null) {
            return List.of("a raid is running");
        }
        List<ToolkitDemo.Hazard> cycle;
        if (what.equalsIgnoreCase("all")) {
            cycle = List.of(ToolkitDemo.Hazard.values());
        } else {
            try {
                cycle = List.of(ToolkitDemo.Hazard.valueOf(what.toUpperCase(java.util.Locale.ROOT)));
            } catch (IllegalArgumentException e) {
                return List.of("no hazard " + what + " (soak, marker, barrier, laser, ring or all)");
            }
        }
        org.bukkit.block.Block floor;
        double radius;
        if (arena != null && arena.bukkitWorld() != null) {
            floor = arena.floor(0, 0);
            radius = arena.radius();
        } else if (at != null) {
            floor = at.getBlock().getRelative(0, -1, 0);
            radius = 20;
        } else {
            return List.of("no arena set; run it in game to use where you stand");
        }
        stopDemo();
        demo = bosses.startEvent(ToolkitDemo.blueprint(cycle, band), ToolkitDemo.spec(radius), floor);
        return List.of();
    }

    /** Ends the toolkit demo, if one runs. */
    public void stopDemo() {
        if (demo != null && !demo.isOver()) {
            bosses.abort(demo, io.github.amitelia.occultech.boss.BossFight.Result.DISMISSED);
        }
        demo = null;
    }

    /** The running toolkit demo (self-test), or null. */
    @Nullable
    public io.github.amitelia.occultech.boss.BossFight demo() {
        return demo != null && !demo.isOver() ? demo : null;
    }

    /** How many hazards the demo has set off (self-test). */
    public int demoLaunched() {
        return demo != null && demo.behavior() instanceof ToolkitDemo toolkit ? toolkit.launched() : 0;
    }

    @Nonnull
    public List<String> status() {
        return raid == null ? List.of("No Staff Raid is running.") : raid.status();
    }

    /** The fights on the floor (self-test). */
    @Nonnull
    public List<io.github.amitelia.occultech.boss.BossFight> fights() {
        return raid == null ? List.of() : raid.fights();
    }

    // ------------------------------------------------------------------ the arena's rules while a raid runs

    private boolean inRaid(Player player) {
        return raid != null && raid.arena().contains(player.getLocation());
    }

    @EventHandler
    public void onDeath(PlayerDeathEvent e) {
        if (inRaid(e.getEntity())) {
            diedHere.add(e.getEntity().getUniqueId());
        }
    }

    @EventHandler
    public void onRespawn(PlayerRespawnEvent e) {
        if (diedHere.remove(e.getPlayer().getUniqueId()) && raid != null) {
            e.setRespawnLocation(raid.arena().edge());
        }
    }

    /** Jolly's trick arrows: whatever annoying effect the arrow carries lands with it. */
    @EventHandler(priority = org.bukkit.event.EventPriority.MONITOR, ignoreCancelled = true)
    public void onTrickArrow(org.bukkit.event.entity.EntityDamageByEntityEvent e) {
        if (e.getEntity() instanceof Player player) {
            JollySignatures.applyTrick(player, e.getDamager());
        }
    }

    /** No gliding in the arena while a raid runs: Act 2 throws players up, and an elytra would make that free. */
    @EventHandler(ignoreCancelled = true)
    public void onGlide(EntityToggleGlideEvent e) {
        if (e.isGliding() && e.getEntity() instanceof Player player && inRaid(player)) {
            e.setCancelled(true);
        }
    }
}
