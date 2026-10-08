package io.github.amitelia.occultech.event;

import java.util.List;

import javax.annotation.Nonnull;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

/**
 * {@code /occultech event ...}: runs the Staff Raid.
 * <ul>
 * <li>{@code arena set <radius>}: the arena is centered where you stand; {@code arena}: shows it and its problems</li>
 * <li>{@code start [targets] [players]}: starts the raid; the numbers override the staff on the floor and the player
 * count it scales for (to try a 25-player raid alone)</li>
 * <li>{@code skip}: on to the next act; {@code stop}: ends the raid</li>
 * <li>{@code hp <multiplier>}: staff health, live</li>
 * <li>{@code status}: the raid's state, slot by slot</li>
 * <li>{@code demo [soak|marker|barrier|laser|ring|all] [band 1-3]}, {@code demo stop}: Act 2's toolkit on its own, at the
 * arena's middle (or where you stand without an arena), at a pace band</li>
 * </ul>
 */
public final class RaidCommand {

    private RaidCommand() {}

    /** {@code args[0]} is "event". */
    public static void run(@Nonnull RaidService raids, @Nonnull CommandSender sender, @Nonnull String[] args) {
        String sub = args.length > 1 ? args[1].toLowerCase(java.util.Locale.ROOT) : "status";
        try {
            switch (sub) {
                case "arena" -> arena(raids, sender, args);
                case "start" -> {
                    Integer targets = args.length > 2 ? Integer.valueOf(args[2]) : null;
                    Integer players = args.length > 3 ? Integer.valueOf(args[3]) : null;
                    List<String> problems = raids.begin(targets, players);
                    if (!problems.isEmpty()) {
                        tell(sender, "&cThe raid can't start:");
                        problems.forEach(p -> tell(sender, "&c - " + p));
                    }
                }
                case "stop" -> {
                    if (!raids.running()) {
                        tell(sender, "&7No raid is running.");
                    }
                    raids.stop();
                }
                case "skip" -> raids.skip();
                case "hp" -> {
                    double multiplier = Math.max(0.05, Double.parseDouble(args[2]));
                    raids.setHealthMultiplier(multiplier);
                    tell(sender, raids.running() ? "&7Staff health is now x" + multiplier + "."
                        : "&7No raid is running; set raid.health-multiplier in config.yml for the next one.");
                }
                case "status" -> raids.status().forEach(line -> tell(sender, "&7" + line));
                case "demo" -> {
                    if (args.length > 2 && args[2].equalsIgnoreCase("stop")) {
                        raids.stopDemo();
                        tell(sender, "&7Toolkit demo stopped.");
                        return;
                    }
                    String what = args.length > 2 ? args[2] : "all";
                    int band = args.length > 3 ? Integer.parseInt(args[3]) : 1;
                    List<String> problems = raids.startDemo(raids.arena(), sender instanceof Player p ? p.getLocation() : null, what, band);
                    if (!problems.isEmpty()) {
                        problems.forEach(p -> tell(sender, "&c" + p));
                    } else {
                        tell(sender, "&aToolkit demo: &f" + what + " &aat pace band &f" + Math.max(1, Math.min(3, band))
                            + "&a. Stop it with /occultech event demo stop.");
                    }
                }
                default -> usage(sender);
            }
        } catch (NumberFormatException | ArrayIndexOutOfBoundsException e) {
            usage(sender);
        }
    }

    private static void arena(RaidService raids, CommandSender sender, String[] args) {
        if (args.length >= 4 && args[2].equalsIgnoreCase("set")) {
            if (!(sender instanceof Player player)) {
                tell(sender, "&cStand in the arena's middle in game to set it.");
                return;
            }
            Location at = player.getLocation();
            RaidArena arena = new RaidArena(at.getWorld().getName(), at.getBlockX(), at.getBlockY(), at.getBlockZ(), Double.parseDouble(args[3]));
            List<String> refused = raids.setArena(arena);
            if (!refused.isEmpty()) {
                refused.forEach(p -> tell(sender, "&c" + p));
                return;
            }
            tell(sender, "&aRaid arena set: " + describe(arena) + ".");
            arena.problems().forEach(p -> tell(sender, "&e - " + p));
            return;
        }
        RaidArena arena = raids.arena();
        if (arena == null) {
            tell(sender, "&7No raid arena yet: stand in its middle and use /occultech event arena set <radius>.");
            return;
        }
        tell(sender, "&7Raid arena: " + describe(arena) + ".");
        List<String> problems = arena.problems();
        tell(sender, problems.isEmpty() ? "&a - ready" : "&e - " + String.join("; ", problems));
    }

    private static String describe(RaidArena arena) {
        return arena.world() + " " + arena.x() + " " + arena.y() + " " + arena.z() + ", radius " + arena.radius();
    }

    private static void usage(CommandSender sender) {
        tell(sender, "&7Usage: /occultech event <arena [set <radius>] | start [targets] [players] | skip | stop | hp <multiplier> | status"
            + " | demo [hazard|all] [band] | demo stop>");
    }

    /** Tab completion after "event". */
    @Nonnull
    public static List<String> complete(@Nonnull String[] args) {
        if (args.length == 2) {
            return List.of("arena", "start", "skip", "stop", "hp", "status", "demo");
        }
        if (args.length == 3 && args[1].equalsIgnoreCase("arena")) {
            return List.of("set");
        }
        if (args.length == 3 && args[1].equalsIgnoreCase("demo")) {
            return List.of("all", "soak", "marker", "barrier", "laser", "ring", "stop");
        }
        if (args.length == 4 && args[1].equalsIgnoreCase("demo")) {
            return List.of("1", "2", "3");
        }
        return List.of();
    }

    private static void tell(CommandSender sender, String message) {
        sender.sendMessage(ChatColor.translateAlternateColorCodes('&', message));
    }
}
