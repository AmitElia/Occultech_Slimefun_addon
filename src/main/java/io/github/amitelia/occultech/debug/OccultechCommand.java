package io.github.amitelia.occultech.debug;

import java.util.List;

import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;

import io.github.amitelia.occultech.Occultech;

/**
 * {@code /occultech} admin command. Subcommands: {@code selftest}.
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
        sender.sendMessage("Usage: /" + label + " selftest");
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String label, String[] args) {
        return args.length == 1 ? List.of("selftest") : List.of();
    }
}
