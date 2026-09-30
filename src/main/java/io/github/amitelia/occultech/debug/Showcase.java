package io.github.amitelia.occultech.debug;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Predicate;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.data.Ageable;
import org.bukkit.block.data.BlockData;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.GlowItemFrame;
import org.bukkit.entity.Player;
import org.bukkit.entity.TextDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.items.ServitorShrine;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * {@code /occultech showcase}: builds a showcase next to spawn in the main world.
 * <ul>
 * <li>A display wall 12 blocks north of spawn with every implemented item in glow item frames.</li>
 * <li>Live block demos east of the wall: Brood Egg, Phantom Roost, Frenzy Idol, a Servitor Shrine harvesting a nether
 * wart field, and a Scrying Mirror watching the Archevoker's circle.</li>
 * <li>One row of ready circles per tier south of spawn (tier 0 at +16, tier 1 at +48), spaced so arenas don't overlap:
 * a crafting demo plus one circle per boss, offerings already in the bowls - open the altar and press Begin Ritual.</li>
 * </ul>
 * Every block it changes is recorded in {@code plugins/Occultech/showcase.yml}; {@code /occultech showcase clear}
 * (or rebuilding) restores them exactly.
 */
final class Showcase {

    private static final String FILE = "showcase.yml";
    private static final int WALL_Z = -12;
    private static final int WALL_HALF_WIDTH = 13;
    private static final int FRAMES_PER_ROW = WALL_HALF_WIDTH + 1;
    private static final String DEMO_OWNER = new UUID(0, 0).toString();

    /** One row of circles per tier: z offset from spawn, spacing, and what to build. */
    private record Row(int tier, int z, int spacing, List<String> circles) {}

    private static final List<Row> ROWS = List.of(
        new Row(0, 16, 26, List.of("craft:SOVEREIGN_CATALYST", "BROOD_MOTHER", "VOLLEY", "WITCH_COVEN", "GELATINOUS_SOVEREIGN", "upgrade:BOUND_ALTAR")),
        new Row(1, 48, 30, List.of("craft:SPIRIT_ESSENCE", "THE_UNBOUND", "NIGHT_MATRIARCH", "MIRRORED_MAGUS", "ARCHEVOKER"))
    );

    private final Occultech plugin;
    private final CommandSender sender;
    private final Map<Block, BlockData> previous = new LinkedHashMap<>();
    private final Map<String, Block> altars = new HashMap<>();

    Showcase(Occultech plugin, CommandSender sender) {
        this.plugin = plugin;
        this.sender = sender;
    }

    void rebuild() {
        clear(false);
        World world = Bukkit.getWorlds().get(0);
        Location spawn = world.getSpawnLocation();

        List<Runnable> fillers = new ArrayList<>();
        for (Row row : ROWS) {
            int count = row.circles().size();
            int x = spawn.getBlockX() - (count - 1) * row.spacing() / 2;
            for (String entry : row.circles()) {
                Runnable filler = buildEntry(world, x, spawn.getBlockZ() + row.z(), row.tier(), entry);
                if (filler != null) {
                    fillers.add(filler);
                }
                x += row.spacing();
            }
        }

        int wallZ = spawn.getBlockZ() + WALL_Z;
        buildWall(world, spawn.getBlockX(), wallZ);
        Runnable demos = buildDemos(world, spawn.getBlockX() + WALL_HALF_WIDTH + 3, wallZ + 3);

        save(world);
        // Slimefun creates block menus a moment after the blocks are stored
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            fillers.forEach(Runnable::run);
            demos.run();
            say("&a[Occultech] Showcase built: item wall + live demos north of spawn, " + fillers.size()
                + " ready circles south (tier 0 at +16, tier 1 at +48). &7Clear with /occultech showcase clear");
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
                String id = BlockStorage.checkID(block);
                if (id != null && Circles.tierOfAltar(id).isPresent()) {
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

    // ------------------------------------------------------------------ circles

    /** "craft:ID" = crafting demo, "upgrade:ID" = altar-upgrade demo, anything else = boss id. */
    private Runnable buildEntry(World world, int x, int z, int tier, String entry) {
        Predicate<RitualRecipe> match;
        String title;
        String hint;
        if (entry.startsWith("craft:")) {
            String output = ItemKeys.slimefunId(entry.substring(6));
            match = r -> output.equals(r.outputId()) && !r.inPlace();
            title = "&dCrafting demo: " + ContentRegistrar.title(entry.substring(6));
            hint = "&7Everything is in place. Press &fBegin Ritual&7.";
        } else if (entry.startsWith("upgrade:")) {
            String output = ItemKeys.slimefunId(entry.substring(8));
            match = r -> output.equals(r.outputId()) && r.inPlace();
            title = "&dUpgrade demo: Initiate's Altar -> " + ContentRegistrar.title(entry.substring(8));
            hint = "&7Altar slot stays empty. Press &fBegin Ritual&7.";
        } else {
            match = r -> entry.equals(r.bossId());
            boolean major = plugin.catalog().boss(entry).map(b -> "major".equals(b.kind())).orElse(false);
            title = "&c" + ContentRegistrar.title(entry) + " &7(tier " + tier + " " + (major ? "gate boss" : "mini-boss") + ")";
            hint = "&7Open the altar and press &fBegin Ritual&7.";
        }
        Optional<RitualRecipe> recipe = plugin.rituals().recipes().stream().filter(match).findFirst();
        if (recipe.isEmpty()) {
            return null;
        }
        Block altar = buildCircle(world, x, z, tier, title, hint);
        altars.put(entry, altar);
        return () -> fill(altar, recipe.get());
    }

    private Block buildCircle(World world, int x, int z, int tier, String title, String hint) {
        int y = world.getHighestBlockYAt(x, z) + 1;
        int radius = Circles.forTier(tier).radius() + 1;
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                setBlock(world.getBlockAt(x + dx, y - 1, z + dz), Material.POLISHED_DEEPSLATE);
            }
        }
        Block altar = world.getBlockAt(x, y, z);
        DebugWorld.buildCircle(altar, tier, this::record);
        label(altar.getLocation().add(0.5, 3.4, 0.5), title + "\n" + hint);
        // keep the chunk loaded until the menus are filled (the command may run with nobody nearby)
        altar.getChunk().addPluginChunkTicket(plugin);
        return altar;
    }

    private void fill(Block altar, RitualRecipe recipe) {
        altar.getChunk().removePluginChunkTicket(plugin);
        boolean centerItem = recipe.center() != null && !recipe.inPlace();
        DebugWorld.setAltarCenter(altar, centerItem ? DebugWorld.item(recipe.center(), 1) : null);
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
    }

    // ------------------------------------------------------------------ wall and demos

    private void buildWall(World world, int cx, int wallZ) {
        List<ItemStack> items = new ArrayList<>();
        for (ItemCatalog.ItemDef def : plugin.catalog().items()) {
            SlimefunItem item = def.tier() <= ContentRegistrar.IMPLEMENTED_TIER ? SlimefunItem.getById(ItemKeys.slimefunId(def.id())) : null;
            if (item != null) {
                items.add(item.getItem().clone());
            }
        }
        int rows = Math.max(1, (items.size() + FRAMES_PER_ROW - 1) / FRAMES_PER_ROW);
        int height = rows * 2 + 2;

        int y = world.getHighestBlockYAt(cx, wallZ) + 1;
        for (int dx = -WALL_HALF_WIDTH; dx <= WALL_HALF_WIDTH; dx++) {
            for (int dy = 0; dy < height; dy++) {
                setBlock(world.getBlockAt(cx + dx, y + dy, wallZ),
                    dy == height - 1 ? Material.POLISHED_BLACKSTONE_BRICK_SLAB : Material.POLISHED_BLACKSTONE_BRICKS);
            }
        }

        for (int i = 0; i < items.size(); i++) {
            int row = i / FRAMES_PER_ROW;
            int frameX = cx - WALL_HALF_WIDTH + (i % FRAMES_PER_ROW) * 2;
            int frameY = y + height - 3 - row * 2;
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
        label(new Location(world, cx + 0.5, y + height + 0.8, wallZ + 1.2),
            "&5&lOccultech &7- Tiers 0-" + ContentRegistrar.IMPLEMENTED_TIER + "\n&7Hover an item frame to read it. Use &f/sf cheat &7to take items.");
    }

    /** Live block demos east of the wall, and one working shrine per contract. Returns a task that fills menus. */
    private Runnable buildDemos(World world, int x, int z) {
        int y = world.getHighestBlockYAt(x, z) + 1;
        List<Runnable> fills = new ArrayList<>();
        demoBlock(world.getBlockAt(x, y, z), "BROOD_EGG", "&fBrood Egg &7(live)\n&7Spins string. Right-click to collect.");
        demoBlock(world.getBlockAt(x + 3, y, z), "PHANTOM_ROOST", "&fPhantom Roost &7(live)\n&7Makes phantom membranes.");
        demoBlock(world.getBlockAt(x + 6, y, z), "FRENZY_IDOL", "&6Frenzy Idol\n&7Harvest shrine next to it works 1.5x faster.");

        // Harvest: a ripe nether wart field (the idol above is within 8 blocks)
        Block harvest = world.getBlockAt(x + 12, y, z + 4);
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                setBlock(harvest.getRelative(dx, -1, dz), Material.SOUL_SAND);
                if (dx != 0 || dz != 0) {
                    Block wart = harvest.getRelative(dx, 0, dz);
                    setBlock(wart, Material.NETHER_WART);
                    Ageable age = (Ageable) wart.getBlockData();
                    age.setAge(age.getMaximumAge());
                    wart.setBlockData(age, false);
                }
            }
        }
        fills.add(shrine(harvest, "HARVEST_CONTRACT", "&5Contract: Harvest\n&7Reaps and replants the wart.", Map.of()));

        Block mirror = world.getBlockAt(x + 3, y, z + 4);
        demoBlock(mirror, "SCRYING_MIRROR", "&dScrying Mirror\n&7Watching the Archevoker's circle.");
        Block archevoker = altars.get("ARCHEVOKER");
        if (archevoker != null) {
            BlockStorage.addBlockInfo(mirror, "occultech_link", archevoker.getWorld().getName() + ";" + archevoker.getX() + ";" + archevoker.getY() + ";" + archevoker.getZ());
        }

        // the other contracts in a row further east, 13 apart (so no more than 4 shrines within 12 blocks)
        int cx = x + 26;
        int cz = z + 4;

        Block gather = world.getBlockAt(cx, y, cz);
        fills.add(shrine(gather, "GATHER_CONTRACT", "&5Contract: Gather\n&7Drop items nearby - it collects them.", Map.of()));
        fills.add(() -> {
            for (int i = 0; i < 4; i++) {
                world.dropItem(gather.getLocation().add(-2 + i, 0.5, 2.5), new ItemStack(Material.BONE, 4)).setPickupDelay(0);
            }
        });

        Block ward = world.getBlockAt(cx + 13, y, cz);
        fills.add(shrine(ward, "WARD_CONTRACT", "&5Contract: Ward\n&7No hostile mobs spawn within 8 blocks.", Map.of()));

        Block brewer = world.getBlockAt(cx + 26, y, cz);
        for (int i = -1; i <= 1; i += 2) {
            Block stand = brewer.getRelative(i * 2, 0, 0);
            setBlock(stand, Material.BREWING_STAND);
            fills.add(() -> {
                if (stand.getState() instanceof org.bukkit.block.BrewingStand bs) {
                    for (int slot = 0; slot < 3; slot++) {
                        ItemStack water = new ItemStack(Material.POTION);
                        org.bukkit.inventory.meta.PotionMeta meta = (org.bukkit.inventory.meta.PotionMeta) water.getItemMeta();
                        meta.setBasePotionType(org.bukkit.potion.PotionType.WATER);
                        water.setItemMeta(meta);
                        bs.getInventory().setItem(slot, water);
                    }
                }
            });
        }
        fills.add(shrine(brewer, "BREWER_CONTRACT", "&5Contract: Brewer's Aid\n&7Fuels the stands and adds nether wart.",
            Map.of(Material.NETHER_WART, 16, Material.BLAZE_POWDER, 8)));

        Block shepherd = world.getBlockAt(cx + 39, y, cz);
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                if (Math.abs(dx) == 3 || Math.abs(dz) == 3) {
                    setBlock(shepherd.getRelative(dx, 0, dz), Material.OAK_FENCE);
                }
            }
        }
        fills.add(shrine(shepherd, "SHEPHERD_CONTRACT", "&5Contract: Shepherd\n&7Shears the sheep in the pen.", Map.of()));
        fills.add(() -> {
            org.bukkit.DyeColor[] colors = { org.bukkit.DyeColor.WHITE, org.bukkit.DyeColor.PURPLE, org.bukkit.DyeColor.BLACK };
            for (int i = 0; i < 3; i++) {
                org.bukkit.DyeColor color = colors[i];
                world.spawn(shepherd.getLocation().add(-1.5 + i * 1.5, 0, 1.5), org.bukkit.entity.Sheep.class, sheep -> {
                    sheep.setColor(color);
                    sheep.getPersistentDataContainer().set(Keys.SHOWCASE, PersistentDataType.BYTE, (byte) 1);
                });
            }
        });

        Block beekeeper = world.getBlockAt(cx + 52, y, cz);
        for (int i = -1; i <= 1; i += 2) {
            Block hive = beekeeper.getRelative(i * 2, 0, 0);
            setBlock(hive, Material.BEEHIVE);
            org.bukkit.block.data.type.Beehive data = (org.bukkit.block.data.type.Beehive) hive.getBlockData();
            data.setHoneyLevel(data.getMaximumHoneyLevel());
            hive.setBlockData(data, false);
        }
        fills.add(shrine(beekeeper, "BEEKEEPER_CONTRACT", "&5Contract: Beekeeper\n&7Takes honeycomb from full hives.", Map.of()));

        // Acolyte: next to the Brood Mother circle, stocked with its offerings
        Block brood = altars.get("BROOD_MOTHER");
        if (brood != null) {
            Block acolyte = brood.getRelative(0, 0, -7);
            Map<Material, Integer> stock = Map.of(Material.STRING, 32, Material.SPIDER_EYE, 16, Material.FERMENTED_SPIDER_EYE, 4);
            fills.add(shrine(acolyte, "ACOLYTE_CONTRACT", "&5Contract: Acolyte\n&7Summon the Brood Mother once;\n&7it then restocks the bowls.", stock));
            fills.add(() -> {
                SlimefunItem salt = SlimefunItem.getById(ItemKeys.slimefunId("GRAVE_SALT"));
                BlockMenu menu = BlockStorage.getInventory(acolyte);
                if (menu != null && salt != null) {
                    ItemStack salts = salt.getItem().clone();
                    salts.setAmount(16);
                    menu.pushItem(salts, ServitorShrine.STORE);
                }
            });
        }

        return () -> fills.forEach(Runnable::run);
    }

    /** Places a shrine with a contract and optional starting supplies. Returns the fill task. */
    private Runnable shrine(Block block, String contract, String label, Map<Material, Integer> supplies) {
        demoBlock(block, "SERVITOR_SHRINE", label);
        BlockStorage.addBlockInfo(block, "occultech_owner", sender instanceof Player p ? p.getUniqueId().toString() : DEMO_OWNER);
        return () -> {
            BlockMenu menu = BlockStorage.getInventory(block);
            SlimefunItem item = SlimefunItem.getById(ItemKeys.slimefunId(contract));
            if (menu == null || item == null) {
                return;
            }
            menu.replaceExistingItem(ServitorShrine.CONTRACT_SLOT, item.getItem().clone());
            supplies.forEach((type, amount) -> menu.pushItem(new ItemStack(type, amount), ServitorShrine.STORE));
        };
    }

    private void demoBlock(Block block, String id, String label) {
        if (DebugWorld.placeSlimefun(block, ItemKeys.slimefunId(id), this::record)) {
            label(block.getLocation().add(0.5, 2.6, 0.5), label);
        }
    }

    private void setBlock(Block block, Material type) {
        record(block);
        block.setType(type, false);
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
