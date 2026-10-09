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
        for (Class<?> type : java.util.List.of(ToolkitDemo.class, Founder.class, Archer.class, Brewer.class)) {
            try {
                Class.forName(type.getName(), true, type.getClassLoader());
            } catch (ClassNotFoundException e) {
                throw new IllegalStateException(e);
            }
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
        RaidSkins.load(new File(plugin.getDataFolder(), "raid-skins.yml"), plugin.getLogger());
        roster.problems().forEach(problem -> plugin.getLogger().warning("Raid roster: " + problem));
        RaidScaling scaling = new RaidScaling(config.getDouble("players-per-target", 2.5), config.getInt("max-targets", 10),
            config.getDouble("health-exponent", 0.9));
        settings = new StaffRaid.Settings(config.getDouble("staff-health", 600), config.getInt("act1-minutes", 8) * 60,
            Math.max(1, config.getInt("kills-per-target", 2)), scaling, Math.max(0.05, config.getDouble("health-multiplier", 1.0)),
            config.getDouble("council-health", 6000), new CouncilBehavior.Cast(seat(config, "founder", "XmpriX", "X", "Community Founder"),
                seat(config, "archer", "Leyfr", "Chlo", "Partnered Owner"), seat(config, "brewer", "PancakeAcoustics", "Pancake", "Staff COO")));
    }

    private static CouncilBehavior.Seat seat(ConfigurationSection config, String role, String name, String display, String title) {
        ConfigurationSection seat = config.getConfigurationSection("council." + role);
        if (seat == null) {
            return new CouncilBehavior.Seat(name, display, title);
        }
        return new CouncilBehavior.Seat(seat.getString("name", name), seat.getString("display", display), seat.getString("title", title));
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
        int now = (++steps) * BossService.STEP;
        if ((raid != null || demo != null) && now - lastBudgetWarning > 1200 && now % 100 == 0) {
            double cost = eventMsPerTick();
            if (cost > BUDGET_MS) {
                lastBudgetWarning = now;
                plugin.getLogger().warning(String.format(java.util.Locale.ROOT, "The Staff Raid takes %.1f ms a tick (budget %.1f): see /occultech event perf",
                    cost, BUDGET_MS));
            }
        }
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
    /** The skin (username) of the staff member or council seat named {@code who} (username or shown name); else {@code who}. */
    public String skinOf(String who) {
        for (StaffMember member : roster.members().values()) {
            if (member.name().equalsIgnoreCase(who) || member.display().equalsIgnoreCase(who)) {
                return member.skin();
            }
        }
        CouncilBehavior.Cast cast = settings.council();
        for (CouncilBehavior.Seat seat : List.of(cast.founder(), cast.archer(), cast.brewer())) {
            if (seat.name().equalsIgnoreCase(who) || seat.display().equalsIgnoreCase(who)) {
                return seat.name();
            }
        }
        return who;
    }

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
        return begin(arena, targets, players, List.of());
    }

    /**
     * As {@link #begin(RaidArena, Integer, Integer)} with a test line-up: these staff (usernames or display names) go
     * onto the floor first, a slot each (a pair shares one); after them the picks are random. With no targets given,
     * there are as many slots as names.
     */
    @Nonnull
    public List<String> begin(@Nonnull RaidArena arena, @Nullable Integer targets, @Nullable Integer players, List<String> names) {
        List<List<StaffMember>> lineup = new java.util.ArrayList<>();
        for (String name : names) {
            List<StaffMember> slot = slotOf(name);
            if (slot == null) {
                return List.of("nobody called " + name + " on the roster");
            }
            if (!lineup.contains(slot)) {
                lineup.add(slot);
            }
        }
        if (targets == null && !lineup.isEmpty()) {
            targets = lineup.size();
        }
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
        raid.lineup(lineup);
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

    /** The Council's fight while Act 2 runs (self-test), or null. */
    @Nullable
    public io.github.amitelia.occultech.boss.BossFight council() {
        return raid == null ? null : raid.council();
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

    // ------------------------------------------------------------------ testing one staff member or one act

    /** Staff spawned on their own with {@code event spawn}. */
    private final List<io.github.amitelia.occultech.boss.BossFight> tests = new java.util.ArrayList<>();

    /**
     * Spawns one staff member (or their pair) by username or display name at {@code at}, outside any raid, with health
     * for {@code players}. Their fight spans the arena when {@code at} is in it, else 20 blocks around.
     */
    /** The roster slot holding {@code name} (username or display name, any case), or null. */
    @Nullable
    private List<StaffMember> slotOf(String name) {
        for (List<StaffMember> slot : roster.slots()) {
            for (StaffMember member : slot) {
                if (member.name().equalsIgnoreCase(name) || member.display().equalsIgnoreCase(name)) {
                    return slot;
                }
            }
        }
        return null;
    }

    @Nonnull
    public List<String> spawnTest(String name, org.bukkit.Location at, int players) {
        java.util.List<StaffMember> slot = slotOf(name);
        if (slot == null) {
            return List.of("nobody called " + name + " on the roster");
        }
        org.bukkit.block.Block middle;
        double radius;
        if (arena != null && arena.contains(at)) {
            middle = arena.floor(0, 0);
            radius = arena.radius();
        } else {
            middle = at.getBlock().getRelative(0, -1, 0);
            radius = 20;
        }
        double effective = settings.miniHealth() * settings.healthMultiplier() * settings.scaling().factor(players);
        tests.removeIf(io.github.amitelia.occultech.boss.BossFight::isOver);
        tests.add(bosses.startEvent(StaffBehavior.blueprint(slot, effective, at), StaffBehavior.spec(slot, radius), middle));
        return List.of();
    }

    /** Removes everyone spawned with {@code event spawn}. */
    public int clearTests() {
        int cleared = 0;
        for (io.github.amitelia.occultech.boss.BossFight fight : tests) {
            if (!fight.isOver()) {
                bosses.abort(fight, io.github.amitelia.occultech.boss.BossFight.Result.DISMISSED);
                cleared++;
            }
        }
        tests.clear();
        return cleared;
    }

    /** Starts a raid straight at Act 2, the Council. */
    @Nonnull
    public List<String> beginCouncil(@Nullable Integer players) {
        return beginCouncil(arena, players, 1);
    }

    /**
     * Starts a raid straight at Act 2, the Council, at pace {@code band} (1-3: the bar starts full, at 50% or at 20%).
     * {@code players} also sizes the raid mechanics, to see a big raid's density alone.
     */
    @Nonnull
    public List<String> beginCouncil(@Nullable RaidArena at, @Nullable Integer players, int band) {
        if (at == null) {
            return List.of("no arena: stand in its middle and use /occultech event arena set <radius>");
        }
        List<String> problems = begin(at, 1, players);
        if (problems.isEmpty() && raid != null) {
            raid.skip();
            if (raid.council() != null && raid.council().behavior() instanceof CouncilBehavior council && band > 1) {
                council.setShare(band >= 3 ? 0.2 : 0.5);
            }
        }
        return problems;
    }

    // ------------------------------------------------------------------ Session E8: what the raid costs the server

    /** Server time a whole raid may take per tick before it's flagged (ms; a tick has 50). */
    public static final double BUDGET_MS = 5;
    private int lastBudgetWarning = -100000;
    private int steps;

    /** Every event fight running now (raid, tests, demo). */
    private List<io.github.amitelia.occultech.boss.BossFight> eventFights() {
        return bosses.fights().stream().filter(io.github.amitelia.occultech.boss.BossFight::isEvent).toList();
    }

    /** Server time all event fights take per tick now (ms, averaged over 5 s). */
    public double eventMsPerTick() {
        return eventFights().stream().mapToDouble(io.github.amitelia.occultech.boss.BossFight::msPerTick).sum();
    }

    /** {@code /occultech event perf}: each event fight's cost and entities, and the total against the budget. */
    @Nonnull
    public List<String> perf() {
        List<io.github.amitelia.occultech.boss.BossFight> fights = eventFights();
        List<String> lines = new java.util.ArrayList<>();
        double total = 0;
        int entities = 0;
        for (io.github.amitelia.occultech.boss.BossFight fight : fights) {
            total += fight.msPerTick();
            entities += fight.entityCount();
            lines.add(String.format(java.util.Locale.ROOT, "  %-24s %5.2f ms/tick, %3d entities, %d adds", fight.spec().name(), fight.msPerTick(),
                fight.entityCount(), fight.liveAdds()));
        }
        lines.add(0, String.format(java.util.Locale.ROOT, "%d event fights: %.2f ms/tick in all (budget %.1f ms), %d entities%s", fights.size(), total,
            BUDGET_MS, entities, total > BUDGET_MS ? " - OVER BUDGET" : ""));
        return lines;
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

    /** A kidnapped player can't get off Chlo's seat until they're dropped; a staff rider never leaves their mount. */
    @EventHandler(ignoreCancelled = true)
    public void onDismount(org.bukkit.event.entity.EntityDismountEvent e) {
        if (e.getEntity() instanceof Player && Archer.isSeat(e.getDismounted())) {
            e.setCancelled(true);
        } else if (e.getDismounted().getPersistentDataContainer().has(CreatureSignatures.MOUNT) && e.getDismounted().isValid()
            && !e.getEntity().isDead() && e.getEntity().isValid()) {
            e.setCancelled(true);
        }
    }

    /** ...nor pearl or chorus out of it. */
    @EventHandler(ignoreCancelled = true)
    public void onEscape(org.bukkit.event.player.PlayerTeleportEvent e) {
        org.bukkit.event.player.PlayerTeleportEvent.TeleportCause cause = e.getCause();
        if ((cause == org.bukkit.event.player.PlayerTeleportEvent.TeleportCause.ENDER_PEARL
            || cause == org.bukkit.event.player.PlayerTeleportEvent.TeleportCause.CONSUMABLE_EFFECT) && Archer.isSeat(e.getPlayer().getVehicle())) {
            e.setCancelled(true);
        }
    }

    /** Quitting mid-carry: off the seat, and back on the ground where they were. */
    @EventHandler
    public void onQuit(org.bukkit.event.player.PlayerQuitEvent e) {
        Player player = e.getPlayer();
        org.bukkit.entity.Entity seat = player.getVehicle();
        if (Archer.isSeat(seat)) {
            seat.getPersistentDataContainer().remove(Archer.SEAT);
            seat.eject();
            org.bukkit.Location at = player.getLocation();
            at.setY(at.getWorld().getHighestBlockYAt(at) + 1);
            player.teleport(at);
            player.setFallDistance(0);
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
