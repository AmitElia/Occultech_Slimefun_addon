package io.github.amitelia.occultech.debug;

import java.util.List;

import org.bukkit.Bukkit;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.command.BlockCommandSender;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;

import io.github.amitelia.occultech.Occultech;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * {@code /occultech} admin command:
 * <ul>
 * <li>{@code selftest}: in-game integration test (console friendly)</li>
 * <li>{@code showcase}: (re)build the item wall and ready-to-summon circles near spawn</li>
 * <li>{@code showcase clear}: remove the showcase and restore the original blocks</li>
 * <li>{@code studio <armor|weapons|machines|cosmetics|rituals> [next|prev|N]}, {@code studio stop}: the showcase studios'
 * camera (see {@link StudioCamera})</li>
 * <li>{@code restock <x> <y> <z> <BOSS_ID>}: refill a circle's altar and bowls for a boss (showcase buttons)</li>
 * <li>{@code inspect <x> <y> <z>}: print a Slimefun block's id and menu contents (debugging)</li>
 * <li>{@code unlockhalos <player>}: unlock every Hollow Halo style for a player (operators always have them)</li>
 * </ul>
 */
public final class OccultechCommand implements TabExecutor {

    private final Occultech plugin;

    public OccultechCommand(Occultech plugin) {
        this.plugin = plugin;
    }

    /** Keeps the showcase's machine and contract demos running (a no-op without a showcase). */
    public static void startShowcaseLoop(Occultech plugin) {
        new ShowcaseLoop(plugin);
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
        if (args.length >= 2 && args[0].equalsIgnoreCase("studio")) {
            if (sender instanceof org.bukkit.entity.Player player) {
                StudioCamera.command(plugin, player, args[1], args.length > 2 ? args[2] : null);
            } else {
                sender.sendMessage("Only a player can use the studio camera.");
            }
            return true;
        }
        if (args.length == 1 && args[0].equalsIgnoreCase("balance")) {
            List<String> lines = new java.util.ArrayList<>();
            Balance.report(plugin, lines);
            lines.forEach(sender::sendMessage);
            return true;
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("kit")) {
            if (!(sender instanceof org.bukkit.entity.Player player)) {
                sender.sendMessage("Only a player can take a kit.");
            } else {
                try {
                    Balance.kit(player, Math.max(0, Math.min(3, Integer.parseInt(args[1]))));
                } catch (NumberFormatException e) {
                    sender.sendMessage("Usage: /occultech kit <0-3>");
                }
            }
            return true;
        }
        if (args.length >= 1 && args[0].equalsIgnoreCase("fights")) {
            fights(sender, args);
            return true;
        }
        if (args.length == 4 && args[0].equalsIgnoreCase("begin")) {
            Block altar = blockAt(sender, args);
            if (altar != null) {
                sender.sendMessage("Ritual at " + altar.getX() + " " + altar.getY() + " " + altar.getZ() + ": " + plugin.rituals().begin(null, altar));
            }
            return true;
        }
        if (args.length == 5 && args[0].equalsIgnoreCase("restock")) {
            Block altar = blockAt(sender, args);
            if (altar != null) {
                Showcase.restock(plugin, sender, altar, args[4].toUpperCase());
            }
            return true;
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("inspect") && args[1].equalsIgnoreCase("shrines")) {
            java.util.Set<Block> shrines = new java.util.LinkedHashSet<>();
            plugin.servitors().shrineLocations().forEach(at -> shrines.add(at.getBlock()));
            // also the showcase's shrines, which only tick while someone is near
            java.io.File file = new java.io.File(plugin.getDataFolder(), "showcase.yml");
            if (file.exists()) {
                var data = org.bukkit.configuration.file.YamlConfiguration.loadConfiguration(file);
                World world = Bukkit.getWorld(data.getString("world", Bukkit.getWorlds().get(0).getName()));
                for (String entry : data.getStringList("blocks")) {
                    String[] parts = entry.split(";", 4);
                    Block block = world.getBlockAt(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]));
                    if ("OCCULTECH_SERVITOR_SHRINE".equals(BlockStorage.checkID(block))) {
                        shrines.add(block);
                    }
                }
            }
            shrines.forEach(block -> inspect(sender, block));
            return true;
        }
        if (args.length >= 6 && args[0].equalsIgnoreCase("setslot")) {
            Block block = blockAt(sender, args);
            BlockMenu menu = block == null ? null : BlockStorage.getInventory(block);
            if (menu != null) {
                int amount = args.length > 6 ? Integer.parseInt(args[6]) : 1;
                menu.replaceExistingItem(Integer.parseInt(args[4]), args[5].equalsIgnoreCase("none") ? null : DebugWorld.item(args[5], amount));
                inspect(sender, block);
            }
            return true;
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("iteminfo")) {
            io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem item = io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem.getById(args[1].toUpperCase());
            if (item == null) {
                sender.sendMessage("No Slimefun item " + args[1]);
                return true;
            }
            org.bukkit.inventory.ItemStack stack = item.getItem();
            sender.sendMessage(item.getId() + " (" + stack.getType() + ", " + item.getClass().getSimpleName() + ")");
            stack.getEnchantments().forEach((e, level) -> sender.sendMessage("  enchant " + e.getKey().getKey() + " " + level));
            var meta = stack.getItemMeta();
            if (meta != null) {
                if (meta.hasAttributeModifiers()) {
                    meta.getAttributeModifiers().forEach((attribute, modifier) -> sender.sendMessage("  attribute " + attribute.getKey().getKey() + " "
                        + modifier.getOperation() + " " + modifier.getAmount() + " " + modifier.getSlotGroup()));
                }
                sender.sendMessage("  unbreakable " + meta.isUnbreakable());
                if (meta.hasLore()) {
                    meta.getLore().forEach(line -> sender.sendMessage("  lore " + org.bukkit.ChatColor.stripColor(line)));
                }
            }
            return true;
        }
        if (args.length >= 1 && args[0].equalsIgnoreCase("skins")) {
            if (!(sender instanceof org.bukkit.entity.Player player)) {
                sender.sendMessage("Run it in game: it skins the Occultech blocks around you.");
                return true;
            }
            int radius = args.length > 1 ? Math.min(64, Integer.parseInt(args[1])) : 24;
            int made = plugin.skins().ensureAround(player.getLocation(), radius);
            sender.sendMessage(plugin.skins().blocks().enabled()
                ? "Made " + made + " Occultech block(s) within " + radius + " blocks their custom blocks."
                : "Skinned " + made + " Occultech block(s) within " + radius + " blocks (" + plugin.skins().count() + " skins tracked).");
            return true;
        }
        if (args.length == 1 && args[0].equalsIgnoreCase("pack")) {
            var pack = plugin.resourcePack();
            sender.sendMessage("Resource pack: mode " + pack.mode() + ", " + pack.modelCount() + " item models, "
                + pack.packSize() / 1024 + " KiB, sha1 " + pack.sha1() + (pack.url() != null ? ", " + pack.url() : ""));
            if (sender instanceof org.bukkit.entity.Player player) {
                pack.send(player);
                sender.sendMessage("Sent it to you again" + (pack.url() != null ? " from " + pack.urlFor(player) : "") + ".");
            }
            return true;
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("unlockhalos")) {
            org.bukkit.entity.Player target = Bukkit.getPlayerExact(args[1]);
            if (target == null) {
                sender.sendMessage("No online player " + args[1]);
            } else {
                target.getPersistentDataContainer().set(io.github.amitelia.occultech.items.HaloStyle.ALL_UNLOCKED,
                    org.bukkit.persistence.PersistentDataType.BYTE, (byte) 1);
                sender.sendMessage("Unlocked every Hollow Halo style for " + target.getName() + ".");
                target.sendMessage(org.bukkit.ChatColor.GOLD + "Every Hollow Halo style is now unlocked for you.");
            }
            return true;
        }
        if (args.length == 4 && args[0].equalsIgnoreCase("inspect")) {
            Block block = blockAt(sender, args);
            if (block != null) {
                inspect(sender, block);
            }
            return true;
        }
        sender.sendMessage("Usage: /" + label + " <selftest | showcase [clear] | restock x y z BOSS | inspect x y z | pack | skins [radius]>");
        return true;
    }

    /** Coordinates from args 1-3, in the sender's world (command blocks and players) or the main world (console). */
    private static Block blockAt(CommandSender sender, String[] args) {
        World world = sender instanceof BlockCommandSender block ? block.getBlock().getWorld()
            : sender instanceof org.bukkit.entity.Entity entity ? entity.getWorld() : Bukkit.getWorlds().get(0);
        try {
            return world.getBlockAt(Integer.parseInt(args[1]), Integer.parseInt(args[2]), Integer.parseInt(args[3]));
        } catch (NumberFormatException e) {
            sender.sendMessage("Coordinates must be whole numbers.");
            return null;
        }
    }

    /** {@code fights}: every running boss fight; {@code fights end N}: ends fight N (no loot, the catalyst is lost). */
    private void fights(CommandSender sender, String[] args) {
        List<io.github.amitelia.occultech.boss.BossFight> fights = List.copyOf(plugin.rituals().bosses().fights());
        if (args.length >= 2 && args[1].equalsIgnoreCase("stats")) {
            if (fights.isEmpty()) {
                sender.sendMessage("No boss fight is running.");
            }
            for (int i = 0; i < fights.size(); i++) {
                if (args.length == 3 && !args[2].equals(String.valueOf(i + 1))) {
                    continue;
                }
                fights.get(i).stats().forEach(sender::sendMessage);
            }
            return;
        }
        if (args.length == 3 && args[1].equalsIgnoreCase("end")) {
            try {
                io.github.amitelia.occultech.boss.BossFight fight = fights.get(Integer.parseInt(args[2]) - 1);
                plugin.rituals().bosses().abort(fight);
                sender.sendMessage("Ended " + fight.spec().name() + ".");
            } catch (RuntimeException e) {
                sender.sendMessage("No fight " + args[2] + " (see /occultech fights).");
            }
            return;
        }
        sender.sendMessage(fights.size() + " boss fight(s) running.");
        for (int i = 0; i < fights.size(); i++) {
            io.github.amitelia.occultech.boss.BossFight fight = fights.get(i);
            Block altar = fight.altar();
            int away = fight.awayTicksLeft();
            sender.sendMessage("  " + (i + 1) + ". " + fight.spec().name() + " at " + altar.getWorld().getName() + " " + altar.getX() + " "
                + altar.getY() + " " + altar.getZ() + ": " + Math.round(fight.healthFraction() * 100) + "% health, " + fight.elapsed() / 20
                + "s in, " + fight.players().size() + " in the arena" + (away >= 0 ? ", everyone away (" + away / 20 + "s left)" : ""));
        }
    }

    private static void inspect(CommandSender sender, Block block) {
        sender.sendMessage("Block " + block.getType() + " at " + block.getX() + " " + block.getY() + " " + block.getZ()
            + ": Slimefun id " + BlockStorage.checkID(block));
        BlockMenu menu = BlockStorage.getInventory(block);
        if (menu == null) {
            sender.sendMessage("  no menu");
            return;
        }
        for (int slot = 0; slot < menu.toInventory().getSize(); slot++) {
            org.bukkit.inventory.ItemStack item = menu.getItemInSlot(slot);
            if (item != null && !item.getType().isAir() && !menu.getPreset().getPresetSlots().contains(slot)) {
                io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem sf = io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem.getByItem(item);
                sender.sendMessage("  slot " + slot + ": " + (sf != null ? sf.getId() : item.getType()) + " x" + item.getAmount());
            }
        }
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 1) {
            return List.of("selftest", "showcase", "studio", "restock", "inspect", "unlockhalos", "iteminfo", "setslot", "fights", "begin", "kit", "balance");
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("showcase")) {
            return List.of("clear");
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("studio")) {
            return List.of("armor", "weapons", "machines", "cosmetics", "rituals", "stop");
        }
        if (args.length == 3 && args[0].equalsIgnoreCase("studio")) {
            return List.of("next", "prev");
        }
        if (args.length == 2 && args[0].equalsIgnoreCase("fights")) {
            return List.of("end", "stats");
        }
        return List.of();
    }
}
