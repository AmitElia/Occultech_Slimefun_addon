package io.github.amitelia.occultech.debug;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.data.BlockData;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.GlowItemFrame;
import org.bukkit.entity.TextDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * {@code /occultech showcase}: builds a showcase next to spawn in the main world.
 * <ul>
 * <li>A display wall (12 blocks north of spawn) with every implemented item in glow item frames.</li>
 * <li>A row of circles (16 blocks south of spawn, 26 blocks apart so arenas don't overlap): one crafting demo and one
 * per boss, with the offerings already in the bowls - open the altar and press Begin Ritual.</li>
 * </ul>
 * Every block it changes is recorded in {@code plugins/Occultech/showcase.yml}; {@code /occultech showcase clear}
 * (or rebuilding) restores them exactly.
 */
final class Showcase {

    private static final String FILE = "showcase.yml";
    private static final int WALL_Z = -12;
    private static final int WALL_HALF_WIDTH = 13;
    private static final int WALL_HEIGHT = 6;
    private static final int CIRCLE_Z = 16;
    private static final int CIRCLE_SPACING = 26;
    private static final String CRAFTING_DEMO = ItemKeys.slimefunId("SOVEREIGN_CATALYST");
    private static final List<String> BOSS_ORDER = List.of("BROOD_MOTHER", "VOLLEY", "WITCH_COVEN", "GELATINOUS_SOVEREIGN");

    private final Occultech plugin;
    private final CommandSender sender;
    private final Map<Block, BlockData> previous = new LinkedHashMap<>();

    Showcase(Occultech plugin, CommandSender sender) {
        this.plugin = plugin;
        this.sender = sender;
    }

    void rebuild() {
        clear(false);
        World world = Bukkit.getWorlds().get(0);
        Location spawn = world.getSpawnLocation();

        buildWall(world, spawn.getBlockX(), spawn.getBlockZ() + WALL_Z);

        List<Runnable> fillers = new ArrayList<>();
        int x = spawn.getBlockX() - 2 * CIRCLE_SPACING;
        int z = spawn.getBlockZ() + CIRCLE_Z;

        Optional<RitualRecipe> demo = plugin.rituals().recipes().stream().filter(r -> CRAFTING_DEMO.equals(r.outputId())).findFirst();
        if (demo.isPresent()) {
            fillers.add(buildCircle(world, x, z, demo.get(), "&dCrafting demo: Sovereign's Catalyst",
                "&7Offerings are in the bowls and a slime", "&7block is on the altar. Press &fBegin Ritual&7."));
        }
        for (String bossId : BOSS_ORDER) {
            x += CIRCLE_SPACING;
            Optional<RitualRecipe> summon = plugin.rituals().recipes().stream().filter(r -> bossId.equals(r.bossId())).findFirst();
            if (summon.isEmpty()) {
                continue;
            }
            String name = ContentRegistrar.title(bossId);
            boolean major = summon.get().center() != null;
            fillers.add(buildCircle(world, x, z, summon.get(), "&c" + name + " &7(tier 0 " + (major ? "gate boss" : "mini-boss") + ")",
                "&7Open the altar and press &fBegin Ritual&7.", "&7Arena: 12 blocks around the altar."));
        }

        save(world);
        // Slimefun creates block menus a moment after the blocks are stored
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            fillers.forEach(Runnable::run);
            say("&a[Occultech] Showcase built: item wall 12 blocks north of spawn, "
                + fillers.size() + " ready circles 16 blocks south. &7Clear with /occultech showcase clear");
        }, 10L);
    }

    void clear(boolean announce) {
        World world = Bukkit.getWorlds().get(0);
        int removed = 0;
        for (Entity entity : world.getEntities()) {
            if (entity.getPersistentDataContainer().has(Keys.SHOWCASE, PersistentDataType.BYTE)) {
                entity.remove();
                removed++;
            }
        }

        File file = new File(plugin.getDataFolder(), FILE);
        int restored = 0;
        if (file.exists()) {
            YamlConfiguration data = YamlConfiguration.loadConfiguration(file);
            World saved = Bukkit.getWorld(data.getString("world", world.getName()));
            List<String> blocks = data.getStringList("blocks");
            for (int i = blocks.size() - 1; i >= 0; i--) {
                String[] parts = blocks.get(i).split(";", 4);
                Block block = saved.getBlockAt(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]));
                if (Circles.INITIATE_ALTAR.equals(BlockStorage.checkID(block))) {
                    plugin.rituals().bosses().fightAt(block).ifPresent(f -> plugin.rituals().bosses().abort(f));
                }
                if (BlockStorage.hasBlockInfo(block)) {
                    DebugWorld.emptyMenu(block);
                    BlockStorage.clearBlockInfo(block);
                }
                block.setBlockData(Bukkit.createBlockData(parts[3]), false);
                restored++;
            }
            file.delete();
        }
        if (announce) {
            say("&a[Occultech] Showcase cleared: " + restored + " blocks restored, " + removed + " displays removed.");
        }
    }

    private void buildWall(World world, int cx, int wallZ) {
        int y = world.getHighestBlockYAt(cx, wallZ) + 1;
        for (int dx = -WALL_HALF_WIDTH; dx <= WALL_HALF_WIDTH; dx++) {
            for (int dy = 0; dy < WALL_HEIGHT; dy++) {
                Block block = world.getBlockAt(cx + dx, y + dy, wallZ);
                record(block);
                block.setType(dy == WALL_HEIGHT - 1 ? Material.POLISHED_BLACKSTONE_BRICK_SLAB : Material.POLISHED_BLACKSTONE_BRICKS, false);
            }
        }

        List<ItemStack> items = new ArrayList<>();
        for (ItemCatalog.ItemDef def : plugin.catalog().items()) {
            SlimefunItem item = def.tier() <= ContentRegistrar.IMPLEMENTED_TIER ? SlimefunItem.getById(ItemKeys.slimefunId(def.id())) : null;
            if (item != null) {
                items.add(item.getItem().clone());
            }
        }

        int perRow = WALL_HALF_WIDTH + 1;
        for (int i = 0; i < items.size(); i++) {
            int row = i / perRow;
            int column = i % perRow;
            int frameX = cx - WALL_HALF_WIDTH + column * 2;
            int frameY = y + 3 - row * 2;
            if (frameY < y) {
                break;
            }
            Location at = new Location(world, frameX, frameY, wallZ + 1);
            ItemStack item = items.get(i);
            try {
                world.spawn(at, GlowItemFrame.class, frame -> {
                    frame.setFacingDirection(BlockFace.SOUTH, true);
                    frame.setItem(item, false);
                    frame.setFixed(true);
                    frame.setInvulnerable(true);
                    frame.getPersistentDataContainer().set(Keys.SHOWCASE, PersistentDataType.BYTE, (byte) 1);
                });
            } catch (IllegalArgumentException e) {
                plugin.getLogger().warning("Showcase: could not place an item frame at " + at.toVector());
            }
        }
        label(new Location(world, cx + 0.5, y + WALL_HEIGHT + 0.8, wallZ + 1.2),
            "&5&lOccultech &7- Tier 0 Initiate\n&7Hover an item frame to read it. Use &f/sf cheat &7to take items.");

        // working block demos in front of the wall
        Block egg = world.getBlockAt(cx + WALL_HALF_WIDTH + 3, world.getHighestBlockYAt(cx + WALL_HALF_WIDTH + 3, wallZ + 3) + 1, wallZ + 3);
        if (DebugWorld.placeSlimefun(egg, ItemKeys.slimefunId("BROOD_EGG"), this::record)) {
            label(egg.getLocation().add(0.5, 2.6, 0.5), "&fBrood Egg &7(live demo)\n&7Spins string over time. Right-click to collect.");
        }
    }

    /** Builds a circle on a small platform and returns a task that fills its menus once they exist. */
    private Runnable buildCircle(World world, int x, int z, RitualRecipe recipe, String title, String... lines) {
        int y = world.getHighestBlockYAt(x, z) + 1;
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                Block floor = world.getBlockAt(x + dx, y - 1, z + dz);
                record(floor);
                floor.setType(Material.POLISHED_DEEPSLATE, false);
            }
        }
        Block altar = world.getBlockAt(x, y, z);
        DebugWorld.buildCircle(altar, recipe.circle(), this::record);
        label(altar.getLocation().add(0.5, 3.4, 0.5), title + "\n" + String.join("\n", lines));
        // keep the chunk loaded until the menus are filled (the command may run with nobody nearby)
        altar.getChunk().addPluginChunkTicket(plugin);

        return () -> {
            altar.getChunk().removePluginChunkTicket(plugin);
            DebugWorld.setAltarCenter(altar, recipe.center() == null ? null : DebugWorld.item(recipe.center(), 1));
            var check = plugin.rituals().checkCircle(altar);
            if (check.isEmpty()) {
                return;
            }
            List<int[]> bowls = check.get().pattern().positionsOf(Circles.OFFERING_BOWL, check.get().rotation());
            int i = 0;
            for (Map.Entry<String, Integer> offering : recipe.offerings().entrySet()) {
                if (i < bowls.size()) {
                    int[] offset = bowls.get(i++);
                    DebugWorld.setBowl(altar.getRelative(offset[0], 0, offset[1]), DebugWorld.item(offering.getKey(), offering.getValue()));
                }
            }
        };
    }

    private void label(Location at, String text) {
        at.getWorld().spawn(at, TextDisplay.class, display -> {
            display.setText(ChatColor.translateAlternateColorCodes('&', text));
            display.setBillboard(Display.Billboard.CENTER);
            display.setShadowed(true);
            display.getPersistentDataContainer().set(Keys.SHOWCASE, PersistentDataType.BYTE, (byte) 1);
        });
    }

    private void record(Block block) {
        previous.putIfAbsent(block, block.getBlockData().clone());
    }

    private void save(World world) {
        YamlConfiguration data = new YamlConfiguration();
        data.set("world", world.getName());
        List<String> blocks = new ArrayList<>();
        previous.forEach((block, blockData) -> blocks.add(block.getX() + ";" + block.getY() + ";" + block.getZ() + ";" + blockData.getAsString()));
        data.set("blocks", blocks);
        try {
            plugin.getDataFolder().mkdirs();
            data.save(new File(plugin.getDataFolder(), FILE));
        } catch (IOException e) {
            plugin.getLogger().warning("Could not save showcase.yml: " + e.getMessage());
        }
    }

    private void say(String message) {
        sender.sendMessage(ChatColor.translateAlternateColorCodes('&', message));
    }
}
