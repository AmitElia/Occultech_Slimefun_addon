package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.Set;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.boss.BarColor;
import org.bukkit.boss.BarStyle;
import org.bukkit.boss.BossBar;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossBlueprint;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.BossSpec;

/**
 * One run of the Staff Raid (docs/staff-raid.md).
 * <p>
 * <b>Act 1, the Staff Floor:</b> {@code N} slots spread over the arena, each holding one staff member (or a pair) as an
 * event fight of its own. When one is beaten, a new random staff member steps into that slot a few seconds later. The
 * act ends after {@code killsPerTarget x N} kills, or when its time runs out. Act 1 has nothing to do with Act 2's bar.
 * <p>
 * <b>Act 2, the Council</b> ({@link CouncilBehavior}): X, Chlo and Pancake at the arena's middle with one shared health
 * pool sized for the players there. The raid is won when it runs out.
 */
final class StaffRaid {

    enum Act { STAFF_FLOOR, COUNCIL, OVER }

    /** Settings from config {@code raid.*}. */
    record Settings(double miniHealth, int act1Seconds, int killsPerTarget, RaidScaling scaling, double healthMultiplier,
        double councilHealth, CouncilBehavior.Cast council) {}

    /** How much room each staff member's starting spot has (the spots are spread so these don't overlap much). */
    static final double SLOT_RADIUS = 12;
    private static final int REFILL_TICKS = 60;

    /** One spot on the floor and who stands there. */
    private final class Slot {
        final Block floor;
        @Nullable BossFight fight;
        @Nullable StaffBehavior staff;
        int refillAt;

        Slot(Block floor) {
            this.floor = floor;
        }
    }

    private final BossService bosses;
    private final RaidArena arena;
    private final Settings settings;
    private final RosterPicker picker;
    private final int targets;
    @Nullable private final Integer fixedPlayers;
    private final List<Slot> slots = new ArrayList<>();
    private final BossBar bar;
    private double healthMultiplier;
    private Act act = Act.STAFF_FLOOR;
    private int ticks;
    private int kills;
    @Nullable private BossFight council;

    /**
     * @param targets      staff on the floor at once, or null to work it out from the players in the arena
     * @param fixedPlayers the player count to scale for, or null to count the players in the arena
     */
    StaffRaid(BossService bosses, RaidArena arena, StaffRoster roster, Settings settings, @Nullable Integer targets,
        @Nullable Integer fixedPlayers) {
        this.bosses = bosses;
        this.arena = arena;
        this.settings = settings;
        this.fixedPlayers = fixedPlayers;
        this.healthMultiplier = settings.healthMultiplier();
        this.picker = new RosterPicker(roster.slots(), new Random());
        this.targets = targets != null ? Math.max(1, Math.min(roster.slots().size(), targets))
            : Math.min(roster.slots().size(), settings.scaling().targets(players()));
        this.bar = Bukkit.createBossBar("", BarColor.BLUE, BarStyle.SEGMENTED_10);
    }

    void start() {
        for (double[] offset : RaidScaling.spots(targets, arena.radius())) {
            Slot slot = new Slot(arena.floor(offset[0], offset[1]));
            slots.add(slot);
            fill(slot);
        }
        announce("&b&lThe Staff Raid begins! &7" + targets + " staff hold the floor - beat " + goal() + " of them.");
        for (Player player : Bukkit.getOnlinePlayers()) {
            player.playSound(player.getLocation(), Sound.EVENT_RAID_HORN, 0.7F, 1F);
        }
        updateBar();
    }

    /** Every {@link BossService#STEP} ticks. */
    void tick() {
        if (act == Act.OVER) {
            return;
        }
        ticks += BossService.STEP;
        if (act == Act.STAFF_FLOOR) {
            for (Slot slot : slots) {
                if (slot.fight != null && slot.fight.isOver()) {
                    if (slot.fight.result() == BossFight.Result.VICTORY) {
                        kills++;
                        tellArena(Component.text(slot.fight.spec().name() + " is down! ", NamedTextColor.AQUA)
                            .append(Component.text(kills + "/" + goal(), NamedTextColor.WHITE)));
                    }
                    slot.fight = null;
                    slot.staff = null;
                    slot.refillAt = ticks + REFILL_TICKS;
                }
                if (slot.fight == null && ticks >= slot.refillAt && kills < goal()) {
                    fill(slot);
                    if (slot.fight != null) {
                        // someone new steps into an emptied slot: a heads-up for whoever is near
                        Location at = slot.floor.getLocation().add(0.5, 1, 0.5);
                        at.getWorld().spawnParticle(org.bukkit.Particle.CLOUD, at.clone().add(0, 1, 0), 30, 0.5, 1, 0.5, 0.05);
                        String text = ChatColor.translateAlternateColorCodes('&', "&b" + slot.fight.spec().name() + " &7steps onto the floor.");
                        for (Player player : at.getWorld().getPlayers()) {
                            if (player.getLocation().distanceSquared(at) <= Math.pow(SLOT_RADIUS + 10, 2)) {
                                player.sendMessage(text);
                            }
                        }
                    }
                }
            }
            if (ticks == (settings.act1Seconds() - 60) * 20) {
                announce("&b1 minute left &7on the Staff Floor - &f" + (goal() - kills) + " &7staff to go.");
            }
            if (kills >= goal() || ticks >= settings.act1Seconds() * 20) {
                endStaffFloor();
            }
        } else if (act == Act.COUNCIL && council != null && council.isOver()) {
            if (council.result() == BossFight.Result.VICTORY) {
                announce("&6&lThe Council has fallen! &eThe Staff Raid is won - GG everyone!");
                for (Player player : Bukkit.getOnlinePlayers()) {
                    player.playSound(player.getLocation(), Sound.UI_TOAST_CHALLENGE_COMPLETE, 1F, 1F);
                }
            }
            council = null;
            finish();
            return;
        }
        updateBar();
    }

    private int goal() {
        return settings.killsPerTarget() * targets;
    }

    /** A random staff member (or pair) steps into {@code slot}. */
    private void fill(Slot slot) {
        Set<String> onField = new HashSet<>();
        for (Slot other : slots) {
            if (other.staff != null) {
                onField.add(other.staff.members().get(0).name().toLowerCase(Locale.ROOT));
            }
        }
        List<StaffMember> members = picker.next(onField);
        if (members == null) {
            slot.refillAt = ticks + REFILL_TICKS;
            return;
        }
        double effective = settings.miniHealth() * healthMultiplier * settings.scaling().factor(players() / (double) targets);
        // the fight spans the whole arena (staff roam it, anyone in it can hit them); the body starts at the slot
        BossSpec spec = StaffBehavior.spec(members, arena.radius());
        Location start = slot.floor.getLocation().add(0.5, 1, 0.5);
        StaffBehavior[] made = new StaffBehavior[1];
        BossBlueprint blueprint = new BossBlueprint(StaffBehavior.ID, StaffBehavior.class, fight -> {
            made[0] = new StaffBehavior(fight, members, effective, start);
            return made[0];
        });
        slot.fight = bosses.startEvent(blueprint, spec, arena.floor(0, 0));
        slot.staff = made[0];
        slot.refillAt = -1;
    }

    private void endStaffFloor() {
        dismissAll();
        act = Act.COUNCIL;
        announce("&b&lThe staff floor is cleared! &7(" + kills + " staff beaten) &6&lThe Council arrives at the middle of the arena...");
        council = bosses.startEvent(CouncilBehavior.blueprint(settings.council(), councilPool()), CouncilBehavior.spec(arena.radius()),
            arena.floor(0, 0));
        for (Player player : Bukkit.getOnlinePlayers()) {
            player.playSound(player.getLocation(), Sound.ENTITY_WITHER_SPAWN, 0.6F, 0.8F);
        }
    }

    /** The Council's shared pool for the players now: council-health x players^0.9 x the health multiplier. */
    private double councilPool() {
        return settings.councilHealth() * healthMultiplier * settings.scaling().factor(players());
    }

    /** Admin: straight on to the next act (in Act 2: ends the raid). */
    void skip() {
        if (act == Act.STAFF_FLOOR) {
            endStaffFloor();
        } else if (act == Act.COUNCIL) {
            stop();
        }
    }

    /** The Council's fight in Act 2 (self-test), or null. */
    @Nullable
    BossFight council() {
        return council != null && !council.isOver() ? council : null;
    }

    /** Admin: ends the raid now. */
    void stop() {
        if (act == Act.OVER) {
            return;
        }
        dismissAll();
        announce("&7The Staff Raid has been called off.");
        finish();
    }

    private void finish() {
        act = Act.OVER;
        bar.removeAll();
    }

    private void dismissAll() {
        if (council != null && !council.isOver()) {
            bosses.abort(council, BossFight.Result.DISMISSED);
        }
        for (Slot slot : slots) {
            if (slot.fight != null && !slot.fight.isOver()) {
                bosses.abort(slot.fight, BossFight.Result.DISMISSED);
            }
            slot.fight = null;
            slot.staff = null;
        }
    }

    /** Admin {@code event hp}: changes staff health now, including those already on the floor. */
    void setHealthMultiplier(double multiplier) {
        this.healthMultiplier = multiplier;
        double effective = settings.miniHealth() * healthMultiplier * settings.scaling().factor(players() / (double) targets);
        for (Slot slot : slots) {
            if (slot.staff != null && slot.fight != null && !slot.fight.isOver()) {
                slot.staff.rescale(effective);
            }
        }
        if (council != null && !council.isOver() && council.behavior() instanceof CouncilBehavior behavior) {
            behavior.rescale(councilPool());
        }
    }

    /** The player count the raid scales for: the admin's number, or everyone fighting in the arena now. */
    int players() {
        if (fixedPlayers != null) {
            return Math.max(1, fixedPlayers);
        }
        int count = 0;
        for (Player player : arena.bukkitWorld().getPlayers()) {
            if (!player.isDead() && player.getGameMode() != GameMode.SPECTATOR && arena.contains(player.getLocation())) {
                count++;
            }
        }
        return Math.max(1, count);
    }

    boolean isOver() {
        return act == Act.OVER;
    }

    Act act() {
        return act;
    }

    /** The fights on the floor now (self-test, status). */
    @Nonnull
    List<BossFight> fights() {
        List<BossFight> out = new ArrayList<>();
        for (Slot slot : slots) {
            if (slot.fight != null && !slot.fight.isOver()) {
                out.add(slot.fight);
            }
        }
        return out;
    }

    int targets() {
        return targets;
    }

    RaidArena arena() {
        return arena;
    }

    int kills() {
        return kills;
    }

    @Nonnull
    List<String> status() {
        List<String> lines = new ArrayList<>();
        lines.add("Staff Raid: " + act.name().toLowerCase(Locale.ROOT).replace('_', ' ') + ", " + ticks / 20 + "s in, " + kills + "/"
            + goal() + " beaten, " + targets + " slots, scaled for " + players() + " players"
            + (fixedPlayers != null ? " (set)" : "") + ", health x" + healthMultiplier);
        for (Slot slot : slots) {
            Location at = slot.floor.getLocation();
            lines.add("  " + at.getBlockX() + " " + (at.getBlockY() + 1) + " " + at.getBlockZ() + ": " + (slot.fight == null || slot.fight.isOver()
                ? "empty" : slot.fight.spec().name() + " " + Math.round(slot.fight.healthFraction() * 100) + "%, " + slot.fight.players().size()
                    + " fighting"));
        }
        return lines;
    }

    private void updateBar() {
        if (act == Act.STAFF_FLOOR) {
            int left = Math.max(0, settings.act1Seconds() - ticks / 20);
            bar.setTitle(ChatColor.translateAlternateColorCodes('&', "&bStaff Raid &7- Act 1: the Staff Floor &f" + kills + "/" + goal()
                + " &7- " + left / 60 + ":" + String.format("%02d", left % 60)));
            bar.setProgress(Math.max(0, Math.min(1, kills / (double) goal())));
        } else if (act == Act.COUNCIL && council != null && council.behavior() instanceof CouncilBehavior behavior) {
            double share = behavior.poolFraction();
            RaidPace pace = RaidPace.of(share, council.elapsed());
            bar.setColor(BarColor.YELLOW);
            bar.setTitle(ChatColor.translateAlternateColorCodes('&', "&6Staff Raid &7- Act 2: &6The Council &f" + Math.round(share * 100)
                + "% &7- pace " + (pace.band() + 1) + "/3" + (pace.damageFactor() > 1 ? " &c(enraged)" : "")));
            bar.setProgress(Math.max(0, Math.min(1, share)));
        }
        // a server-wide event: everyone online sees how it goes (in Act 2, those in the arena see the Council's own bar)
        for (Player player : Bukkit.getOnlinePlayers()) {
            boolean show = act != Act.COUNCIL || !arena.contains(player.getLocation());
            if (show && !bar.getPlayers().contains(player)) {
                bar.addPlayer(player);
            } else if (!show && bar.getPlayers().contains(player)) {
                bar.removePlayer(player);
            }
        }
    }

    /** An action-bar line for everyone in the arena. */
    private void tellArena(Component line) {
        for (Player player : arena.bukkitWorld().getPlayers()) {
            if (arena.contains(player.getLocation())) {
                player.sendActionBar(line);
            }
        }
    }

    private static void announce(String message) {
        String text = ChatColor.translateAlternateColorCodes('&', message);
        Bukkit.getOnlinePlayers().forEach(player -> player.sendMessage(text));
        Bukkit.getConsoleSender().sendMessage(text);
    }
}
