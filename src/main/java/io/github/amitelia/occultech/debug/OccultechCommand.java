package io.github.amitelia.occultech.debug;

import java.util.List;

import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;

import io.github.amitelia.occultech.Occultech;

/**
 * {@code /occultech} admin command:
 * <ul>
 * <li>{@code selftest}: in-game integration test (console friendly)</li>
 * <li>{@code showcase}: (re)build the item wall and ready-to-summon circles near spawn</li>
 * <li>{@code showcase clear}: remove the showcase and restore the original blocks</li>
 * </ul>
 */
public final class OccultechCommand implements TabExecutor {

    private final Occultech plugin;

    public OccultechCommand(Occultech plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 1 && args[0].equalsIgnoreCase("selftest")) {
            new SelfTest(plugin, sender).run();
            return true;
        }
        if (args.length >= 1 && args[0].equalsIgnoreCase("showcase")) {
            Showcase showcase = new Showcase(plugin, sender);
            if (args.length == 2 && args[1].equalsIgnoreCase("clear")) {
                showcase.clear(true);
            } else {
                showcase.rebuild();
            }
            return true;
        }
        sender.sendMessage("Usage: /" + label + " <selftest | showcase [clear]>");
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 1) {
            return List.of("selftest", "showcase");
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("showcase")) {
            return List.of("clear");
        }
        return List.of();
    }
}
