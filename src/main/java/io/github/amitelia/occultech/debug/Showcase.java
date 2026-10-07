package io.github.amitelia.occultech.debug;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Chunk;
import org.bukkit.DyeColor;
import org.bukkit.GameRule;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.Chest;
import org.bukkit.block.CommandBlock;
import org.bukkit.block.data.FaceAttachable;
import org.bukkit.block.data.Ageable;
import org.bukkit.block.data.BlockData;
import org.bukkit.block.data.Directional;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Sheep;
import org.bukkit.entity.TextDisplay;
import org.bukkit.event.entity.CreatureSpawnEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

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
 * {@code /occultech showcase}: a hallway of progression running south from spawn.
 * <ul>
 * <li>One segment per tier. West side: pedestals with each item hovering above, plus the
 * tier's crafting-ritual demos. East side: a summoning arena with its edge marked by a glowing ring, the circle, and a
 * kit chest per boss holding exactly that boss's offerings (the first boss is already in the bowls).</li>
 * <li>A final "Servitors and Curios" segment with the live blocks and one working shrine per contract.</li>
 * <li>The grass is replaced by themed floors, natural mob spawning is switched off and natural mobs are removed.</li>
 * <li>West of the hallway, the studios: one per ritual recipe, cosmetic, machine, armor set and weapon, each on its own
 * white concrete floor before a white backdrop (back and side walls), evenly lit by hidden light blocks, with room in
 * front for a camera - for screenshots and recordings. No text anywhere in them (blocks carry no floating text; the
 * hallway keeps only its section titles).</li>
 * </ul>
 * Every block it changes (and the mob-spawning rule) is recorded in {@code plugins/Occultech/showcase.yml};
 * {@code /occultech showcase clear} (or rebuilding) restores them exactly.
 */
final class Showcase {

    private static final String FILE = "showcase.yml";
    private static final String DEMO_OWNER = new UUID(0, 0).toString();
    private static final int START_Z = 5;
    private static final int PATH_HALF_WIDTH = 3;
    private static final int PEDESTAL_SPACING = 3;
    private static final int[] PEDESTAL_COLUMNS = { -6, -9, -12 };
    private static final int WEST_EDGE = -24;
    private static final int EAST_EDGE = 58;
    private static final Map<Integer, List<String>> BOSS_ORDER = Map.of(
        0, List.of("BROOD_MOTHER", "VOLLEY", "WITCH_COVEN", "GELATINOUS_SOVEREIGN"),
        1, List.of("THE_UNBOUND", "NIGHT_MATRIARCH", "MIRRORED_MAGUS", "ARCHEVOKER"),
        2, List.of("ABYSSAL_WARDEN", "TIDEBREAKER", "BLAZE_CHOIR", "TEMPEST", "DROWNED_ELDER"),
        3, List.of("HOLLOW_WARLORD", "HEARTWOOD_HORROR", "DREAD_RIDERS", "CORRUPTED_COLOSSUS", "DOPPELGANGER", "GALLUS"));
    private static final Map<Integer, List<String>> CRAFT_DEMOS = Map.of(
        0, List.of("craft:SOVEREIGN_CATALYST", "upgrade:BOUND_ALTAR"),
        1, List.of("craft:SPIRIT_ESSENCE"),
        2, List.of("upgrade:ABYSSAL_ALTAR"),
        3, List.of("upgrade:HOLLOW_ALTAR"));
    private static final Material[] PEDESTALS = { Material.CHISELED_POLISHED_BLACKSTONE, Material.PURPUR_PILLAR, Material.PRISMARINE_BRICKS, Material.CHISELED_DEEPSLATE };
    /** A studio: floor and backdrop width (x), depth to the open front (z), the apron in front, wall height. */
    private static final int STUDIO_WIDTH = 19;
    private static final int STUDIO_DEPTH = 19;
    private static final int STUDIO_APRON = 6;
    private static final int STUDIO_WALL = 12;
    private static final int STUDIO_GAP = 4;
    private static final int STUDIOS_PER_ROW = 8;
    /** The studios' east edge, west of the hallway. */
    private static final int STUDIOS_EAST = -32;
    private static final Material[] RINGS = { Material.PEARLESCENT_FROGLIGHT, Material.VERDANT_FROGLIGHT, Material.OCHRE_FROGLIGHT, Material.CRYING_OBSIDIAN };

    private final Occultech plugin;
    private final CommandSender sender;
    private final Map<Block, BlockData> previous = new LinkedHashMap<>();
    private final Map<Integer, Block> summonAltars = new HashMap<>();
    private final Set<Chunk> ticketed = new HashSet<>();
    private final List<Runnable> fills = new ArrayList<>();
    /** Demos the showcase loop keeps running ("TYPE;x;y;z[;more]"), saved in showcase.yml. */
    private final List<String> loops = new ArrayList<>();
    /** One line per row of studios, for the build message. */
    private final List<String> studioRows = new ArrayList<>();
    private World world;
    private int floorY;
    private int ox;
    private int oz;
    private Boolean previousMobSpawning;

    Showcase(Occultech plugin, CommandSender sender) {
        this.plugin = plugin;
        this.sender = sender;
    }

    void rebuild() {
        clear(false);
        world = Bukkit.getWorlds().get(0);
        ox = world.getSpawnLocation().getBlockX();
        oz = world.getSpawnLocation().getBlockZ();
        floorY = world.getHighestBlockYAt(ox, oz);

        // plan the segments first, so the floor can be laid under all of them
        int z = oz + START_Z;
        List<int[]> segments = new ArrayList<>();
        for (int tier = 0; tier <= ContentRegistrar.IMPLEMENTED_TIER; tier++) {
            int radius = arenaRadius(tier);
            int pedestalRows = (itemsOf(tier).size() + PEDESTAL_COLUMNS.length - 1) / PEDESTAL_COLUMNS.length;
            int length = Math.max(pedestalRows * PEDESTAL_SPACING, 2 * radius + 3) + 4;
            segments.add(new int[] { tier, z, length });
            z += length;
        }
        int servitorStart = z;
        int end = z + 88;

        loadArea(oz + 1, end + 1);
        layFloor(oz + 2, end, segments, servitorStart);
        for (int[] segment : segments) {
            buildTier(segment[0], segment[1], segment[2]);
        }
        buildServitors(servitorStart);
        buildStudios();
        clearMobs();

        save();
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            fills.forEach(Runnable::run);
            ticketed.forEach(chunk -> chunk.removePluginChunkTicket(plugin));
            say("&a[Occultech] Showcase built: a hallway south of spawn (tiers 0-" + ContentRegistrar.IMPLEMENTED_TIER
                + ", then servitors). Natural mob spawning is off. &7Clear with /occultech showcase clear");
            summonAltars.forEach((tier, altar) -> say("&7Summoning altar, tier " + tier + ": " + altar.getX() + " " + altar.getY() + " " + altar.getZ()));
            studioRows.forEach(row -> say("&7Studios: " + row));
        }, 10L);
    }

    void clear(boolean announce) {
        World main = Bukkit.getWorlds().get(0);
        int removed = 0;
        for (Entity entity : main.getEntities()) {
            if (entity.getPersistentDataContainer().has(Keys.SHOWCASE, PersistentDataType.BYTE)) {
                entity.remove();
                removed++;
            }
        }

        File file = new File(plugin.getDataFolder(), FILE);
        int restored = 0;
        if (file.exists()) {
            YamlConfiguration data = YamlConfiguration.loadConfiguration(file);
            World saved = Bukkit.getWorld(data.getString("world", main.getName()));
            List<String> blocks = data.getStringList("blocks");
            // displays and mannequins in chunks that unloaded since the build: load each chunk's entities and remove them
            Set<Long> chunks = new HashSet<>();
            for (String entry : blocks) {
                String[] parts = entry.split(";", 4);
                int cx = Integer.parseInt(parts[0]) >> 4;
                int cz = Integer.parseInt(parts[2]) >> 4;
                if (chunks.add(((long) cx << 32) ^ (cz & 0xffffffffL))) {
                    for (Entity entity : saved.getChunkAt(cx, cz).getEntities()) {
                        if (entity.getPersistentDataContainer().has(Keys.SHOWCASE, PersistentDataType.BYTE) && entity.isValid()) {
                            entity.remove();
                            removed++;
                        }
                    }
                }
            }
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
                if (block.getState() instanceof Chest chest) {
                    chest.getBlockInventory().clear();
                }
                block.setBlockData(Bukkit.createBlockData(parts[3]), false);
                restored++;
            }
            if (data.contains("mob-spawning")) {
                saved.setGameRule(GameRule.DO_MOB_SPAWNING, data.getBoolean("mob-spawning"));
            }
            file.delete();
        }
        if (announce) {
            say("&a[Occultech] Showcase cleared: " + restored + " blocks restored, " + removed + " displays removed.");
        }
    }

    // ------------------------------------------------------------------ floor and area

    private void loadArea(int fromZ, int toZ) {
        for (int x = ox + WEST_EDGE; x <= ox + EAST_EDGE + 15; x += 16) {
            for (int z = fromZ; z <= toZ + 15; z += 16) {
                Chunk chunk = world.getChunkAt(x >> 4, z >> 4);
                if (ticketed.add(chunk)) {
                    chunk.addPluginChunkTicket(plugin);
                }
            }
        }
    }

    private void layFloor(int fromZ, int toZ, List<int[]> segments, int servitorStart) {
        Set<Integer> dividers = new HashSet<>();
        segments.forEach(segment -> dividers.add(segment[1]));
        dividers.add(servitorStart);
        for (int x = ox + WEST_EDGE; x <= ox + EAST_EDGE; x++) {
            for (int z = fromZ; z <= toZ; z++) {
                int dx = x - ox;
                Material floor;
                if (dividers.contains(z)) {
                    floor = Material.POLISHED_DEEPSLATE;
                } else if (Math.abs(dx) <= PATH_HALF_WIDTH) {
                    floor = (z - fromZ) % 6 == 0 && dx == 0 ? Material.SEA_LANTERN : Material.POLISHED_BLACKSTONE_BRICKS;
                } else if (Math.abs(dx) == PATH_HALF_WIDTH + 1) {
                    floor = Material.CHISELED_POLISHED_BLACKSTONE;
                } else {
                    floor = Material.DEEPSLATE_TILES;
                }
                setBlock(world.getBlockAt(x, floorY, z), floor);
            }
        }
    }

    private void clearMobs() {
        previousMobSpawning = world.getGameRuleValue(GameRule.DO_MOB_SPAWNING);
        world.setGameRule(GameRule.DO_MOB_SPAWNING, false);
        for (Entity entity : world.getEntities()) {
            if (entity instanceof LivingEntity && !(entity instanceof Player) && !Keys.isSummoned(entity) && Keys.minionOwner(entity) == null
                && !entity.getPersistentDataContainer().has(Keys.SHOWCASE, PersistentDataType.BYTE)
                && entity.getEntitySpawnReason() == CreatureSpawnEvent.SpawnReason.NATURAL) {
                entity.remove();
            }
        }
    }

    // ------------------------------------------------------------------ tier segments

    private void buildTier(int tier, int startZ, int length) {
        String gear = plugin.catalog().tier(tier).gear();
        title(new Location(world, ox + 0.5, floorY + 5, startZ + 1.5),
            "&5&lTIER " + tier + " - " + plugin.catalog().tier(tier).name().toUpperCase() + "\n&7Balanced for: &f" + gear);

        // west: pedestals, three columns, in catalog order
        List<ItemCatalog.ItemDef> items = itemsOf(tier);
        for (int i = 0; i < items.size(); i++) {
            int column = PEDESTAL_COLUMNS[i % PEDESTAL_COLUMNS.length];
            int row = i / PEDESTAL_COLUMNS.length;
            pedestal(world.getBlockAt(ox + column, floorY + 1, startZ + 2 + row * PEDESTAL_SPACING), items.get(i),
                PEDESTALS[Math.min(tier, PEDESTALS.length - 1)]);
        }

        // west, further out: crafting-ritual demos
        List<String> demos = CRAFT_DEMOS.getOrDefault(tier, List.of());
        for (int i = 0; i < demos.size(); i++) {
            int demoZ = startZ + (i + 1) * length / (demos.size() + 1);
            craftDemo(ox - 19, demoZ, tier, demos.get(i));
        }

        // east: the summoning arena
        int radius = arenaRadius(tier);
        int cx = ox + PATH_HALF_WIDTH + 3 + radius;
        int cz = startZ + length / 2;
        for (int dx = -radius - 1; dx <= radius + 1; dx++) {
            for (int dz = -radius - 1; dz <= radius + 1; dz++) {
                double distance = Math.sqrt(dx * dx + dz * dz);
                if (distance >= radius - 0.5 && distance < radius + 0.5) {
                    setBlock(world.getBlockAt(cx + dx, floorY, cz + dz), RINGS[Math.min(tier, RINGS.length - 1)]);
                }
            }
        }

        List<String> bosses = BOSS_ORDER.getOrDefault(tier, List.of());
        Optional<RitualRecipe> first = bosses.isEmpty() ? Optional.empty() : recipeFor(bosses.get(0));
        Block altar = circle(cx, cz, tier);
        summonAltars.put(tier, altar);
        first.ifPresent(recipe -> fills.add(() -> fill(altar, recipe)));

        for (int i = 0; i < bosses.size(); i++) {
            Block chest = world.getBlockAt(cx - radius + 3, floorY + 1, cz - 4 + i * 3);
            kit(chest, bosses.get(i));
            restockButton(chest.getRelative(0, 0, 1), altar, bosses.get(i));
        }
    }

    private void pedestal(Block base, ItemCatalog.ItemDef def, Material look) {
        SlimefunItem item = SlimefunItem.getById(ItemKeys.slimefunId(def.id()));
        if (item == null) {
            return;
        }
        setBlock(base, look);
        world.spawn(base.getLocation().add(0.5, 1.45, 0.5), ItemDisplay.class, display -> {
            display.setItemStack(item.getItem().clone());
            display.setBillboard(Display.Billboard.VERTICAL);
            display.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(0.65F, 0.65F, 0.65F), new AxisAngle4f()));
            tag(display);
        });
    }

    private void kit(Block chestBlock, String bossId) {
        Optional<RitualRecipe> recipe = recipeFor(bossId);
        if (recipe.isEmpty()) {
            return;
        }
        setBlock(chestBlock, Material.CHEST);
        if (chestBlock.getBlockData() instanceof Directional facing) {
            facing.setFacing(BlockFace.EAST);
            chestBlock.setBlockData(facing, false);
        }
        List<ItemStack> contents = new ArrayList<>();
        if (recipe.get().center() != null) {
            contents.add(DebugWorld.item(recipe.get().center(), 1));
        }
        recipe.get().offerings().forEach((key, amount) -> contents.add(DebugWorld.item(key, amount)));
        if (chestBlock.getState() instanceof Chest chest) {
            chest.getBlockInventory().clear();
            contents.stream().filter(java.util.Objects::nonNull).forEach(i -> chest.getBlockInventory().addItem(i));
        }
    }

    /** A command block with a button on top that refills the circle for one boss. */
    private void restockButton(Block at, Block altar, String bossId) {
        setBlock(at, Material.COMMAND_BLOCK);
        if (at.getState() instanceof CommandBlock commandBlock) {
            commandBlock.setCommand("occultech restock " + altar.getX() + " " + altar.getY() + " " + altar.getZ() + " " + bossId);
            commandBlock.update(true, false);
        }
        Block button = at.getRelative(0, 1, 0);
        setBlock(button, Material.POLISHED_BLACKSTONE_BUTTON);
        if (button.getBlockData() instanceof FaceAttachable face) {
            face.setAttachedFace(FaceAttachable.AttachedFace.FLOOR);
            button.setBlockData(face, false);
        }
    }

    /**
     * Refills a circle for a boss: the catalyst (gate bosses) on the altar, offerings in the bowls. Refuses while a
     * ritual or fight is running there. Used by the showcase buttons via {@code /occultech restock}.
     */
    static void restock(Occultech plugin, CommandSender sender, Block altar, String bossId) {
        String output = ItemKeys.slimefunId(bossId);
        Optional<RitualRecipe> recipe = plugin.rituals().recipes().stream()
            .filter(r -> bossId.equals(r.bossId()) || (!r.isSummon() && output.equals(r.outputId()))).findFirst();
        if (recipe.isPresent() && recipe.get().inPlace() && !plugin.rituals().isLocked(altar.getLocation())
            && !recipe.get().center().equals(BlockStorage.checkID(altar))) {
            // an upgrade ritual already ran here: put the altar it starts from back
            DebugWorld.emptyMenu(altar);
            BlockStorage.clearBlockInfo(altar);
            DebugWorld.placeSlimefun(altar, recipe.get().center(), block -> { });
        }
        if (recipe.isEmpty() || plugin.rituals().checkCircle(altar).isEmpty()) {
            sender.sendMessage("No ritual for " + bossId + " at that circle.");
            return;
        }
        String message;
        if (plugin.rituals().isLocked(altar.getLocation()) || plugin.rituals().bosses().fightAt(altar).isPresent()) {
            message = "&cThe circle is busy - finish or leave the fight first.";
        } else {
            fill(plugin, altar, recipe.get());
            altar.getWorld().playSound(altar.getLocation(), org.bukkit.Sound.BLOCK_AMETHYST_BLOCK_CHIME, 1F, 1.2F);
            altar.getWorld().spawnParticle(org.bukkit.Particle.SOUL, altar.getLocation().add(0.5, 1.2, 0.5), 20, 0.6, 0.4, 0.6, 0.02);
            message = "&dThe circle is stocked for &c" + ContentRegistrar.title(bossId) + "&d. Open the altar and press &fBegin Ritual&d.";
        }
        String colored = ChatColor.translateAlternateColorCodes('&', message);
        // command blocks can't show chat, so tell the players standing near the circle
        for (Player player : altar.getWorld().getNearbyPlayers(altar.getLocation(), 24)) {
            player.sendMessage(colored);
        }
        if (!(sender instanceof org.bukkit.command.BlockCommandSender)) {
            sender.sendMessage(colored);
        }
    }

    private void craftDemo(int x, int z, int tier, String entry) {
        boolean upgrade = entry.startsWith("upgrade:");
        String id = entry.substring(entry.indexOf(':') + 1);
        String output = ItemKeys.slimefunId(id);
        Optional<RitualRecipe> recipe = plugin.rituals().recipes().stream()
            .filter(r -> output.equals(r.outputId()) && r.inPlace() == upgrade).findFirst();
        if (recipe.isEmpty()) {
            return;
        }
        Block altar = circle(x, z, upgrade ? recipe.get().circle() : tier);
        fills.add(() -> fill(altar, recipe.get()));
    }

    private Block circle(int x, int z, int tier) {
        Block altar = world.getBlockAt(x, floorY + 1, z);
        DebugWorld.buildCircle(altar, tier, this::record);
        return altar;
    }

    private void fill(Block altar, RitualRecipe recipe) {
        fill(plugin, altar, recipe);
    }

    private static void fill(Occultech plugin, Block altar, RitualRecipe recipe) {
        boolean centerItem = recipe.center() != null && !recipe.inPlace();
        DebugWorld.setAltarCenter(altar, centerItem ? DebugWorld.item(recipe.center(), 1) : null);
        var check = plugin.rituals().checkCircle(altar);
        if (check.isEmpty()) {
            return;
        }
        List<int[]> bowls = check.get().pattern().positionsOf(Circles.OFFERING_BOWL, check.get().rotation());
        bowls.forEach(offset -> DebugWorld.setBowl(altar.getRelative(offset[0], 0, offset[1]), null));
        int i = 0;
        for (Map.Entry<String, Integer> offering : recipe.offerings().entrySet()) {
            if (i < bowls.size()) {
                int[] offset = bowls.get(i++);
                DebugWorld.setBowl(altar.getRelative(offset[0], 0, offset[1]), DebugWorld.item(offering.getKey(), offering.getValue()));
            }
        }
    }

    // ------------------------------------------------------------------ servitors and curios

    private void buildServitors(int startZ) {
        title(new Location(world, ox + 0.5, floorY + 5, startZ + 1.5), "&5&lSERVITORS & CURIOS\n&7Live blocks and one shrine per contract");
        int y = floorY + 1;

        // curios along the walkway
        demoBlock(world.getBlockAt(ox - 5, y, startZ + 3), "BROOD_EGG");
        demoBlock(world.getBlockAt(ox + 5, y, startZ + 3), "PHANTOM_ROOST");
        Block mirror = world.getBlockAt(ox + 5, y, startZ + 9);
        demoBlock(mirror, "SCRYING_MIRROR");
        Block watched = summonAltars.getOrDefault(1, summonAltars.get(0));
        if (watched != null) {
            BlockStorage.addBlockInfo(mirror, "occultech_link", world.getName() + ";" + watched.getX() + ";" + watched.getY() + ";" + watched.getZ());
        }

        // west column: harvest (with an idol), gather, ward; 14 apart so no more than 4 shrines within 12 blocks
        Block harvest = world.getBlockAt(ox - 14, y, startZ + 8);
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
        shrine(harvest, "HARVEST_CONTRACT", Map.of());
        demoBlock(world.getBlockAt(ox - 7, y, startZ + 8), "FRENZY_IDOL");

        Block gather = world.getBlockAt(ox - 14, y, startZ + 22);
        shrine(gather, "GATHER_CONTRACT", Map.of());
        fills.add(() -> {
            for (int i = 0; i < 4; i++) {
                world.dropItem(gather.getLocation().add(-2 + i, 0.5, 2.5), new ItemStack(Material.BONE, 4)).setPickupDelay(0);
            }
        });
        Block ward = world.getBlockAt(ox - 14, y, startZ + 36);
        shrine(ward, "WARD_CONTRACT", Map.of());
        fills.add(() -> {
            BlockMenu menu = BlockStorage.getInventory(ward);
            SlimefunItem tether = SlimefunItem.getById(ItemKeys.slimefunId("ABYSSAL_TETHER"));
            if (menu != null && tether != null) {
                menu.replaceExistingItem(ServitorShrine.UPGRADE_SLOT, tether.getItem().clone());
            }
        });

        // tier-2 curios and powered machines along the walkway
        demoBlock(world.getBlockAt(ox - 5, y, startZ + 15), "GUARDIAN_EYE");
        demoBlock(world.getBlockAt(ox + 5, y, startZ + 15), "PEARL_BED");
        demoBlock(world.getBlockAt(ox - 5, y, startZ + 21), "EMBER_BRAZIER");
        demoBlock(world.getBlockAt(ox + 5, y, startZ + 21), "WIND_CHIME");

        // decoration gallery across the end of the hall
        title(new Location(world, ox + 0.5, floorY + 5, startZ + 41.5), "&d&lDECORATIONS\n&7Sneak + right-click one to change its look");
        String[] decorations = { "WISP_JAR", "ABYSSAL_LANTERN", "RUNE_OBELISK", "OCCULT_ORRERY", "SOULFIRE_BRAZIER", "BOTTLED_GALE" };
        for (int i = 0; i < decorations.length; i++) {
            String id = decorations[i];
            demoBlock(world.getBlockAt(ox - 10 + i * 4, y, startZ + 45), id);
        }

        // cosmetics from every tier: flowers need soil, the netherrack is lit, tiles are laid in the floor to walk on
        setBlock(world.getBlockAt(ox - 10, y - 1, startZ + 50), Material.GRASS_BLOCK);
        demoBlock(world.getBlockAt(ox - 10, y, startZ + 50), "MOONLIT_LILY");
        setBlock(world.getBlockAt(ox - 5, y - 1, startZ + 50), Material.GRASS_BLOCK);
        demoBlock(world.getBlockAt(ox - 5, y, startZ + 50), "WITCHCAP");
        setBlock(world.getBlockAt(ox - 15, y - 1, startZ + 50), Material.GRASS_BLOCK);
        demoBlock(world.getBlockAt(ox - 15, y, startZ + 50), "WATCHFUL_EYEBLOSSOM");
        for (int dx = -3; dx <= 3; dx++) {
            DebugWorld.placeSlimefun(world.getBlockAt(ox + dx, y - 1, startZ + 56), ItemKeys.slimefunId("RESIN_TILE"), this::record);
        }
        demoBlock(world.getBlockAt(ox + 12, y - 1, startZ + 57), "FLOOR_SIGIL");
        demoBlock(world.getBlockAt(ox + 5, y, startZ + 50), "EVERLIVING_CORAL");
        Block netherrack = world.getBlockAt(ox + 10, y, startZ + 50);
        demoBlock(netherrack, "PRISMATIC_NETHERRACK");
        setBlock(netherrack.getRelative(0, 1, 0), Material.FIRE);
        for (int dx = -6; dx <= 6; dx++) {
            if (dx != 0) {
                DebugWorld.placeSlimefun(world.getBlockAt(ox + dx, y - 1, startZ + 54), ItemKeys.slimefunId(dx < 0 ? "CHIMING_TILE" : "TIDAL_TILE"), this::record);
            }
        }
        Block trophy = world.getBlockAt(ox, y, startZ + 50);
        demoBlock(trophy, "TROPHY_BOARD");
        // the showcase board starts on the Brood Mother so it isn't empty
        BlockStorage.addBlockInfo(trophy, "occultech_trophy", "BROOD_MOTHER;0;the showcase");

        // east column: brewer, shepherd, beekeeper
        Block brewer = world.getBlockAt(ox + 14, y, startZ + 8);
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
        shrine(brewer, "BREWER_CONTRACT", Map.of(Material.NETHER_WART, 16, Material.BLAZE_POWDER, 8));

        Block shepherd = world.getBlockAt(ox + 14, y, startZ + 22);
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                if (Math.abs(dx) == 3 || Math.abs(dz) == 3) {
                    setBlock(shepherd.getRelative(dx, 0, dz), Material.DARK_OAK_FENCE);
                }
            }
        }
        shrine(shepherd, "SHEPHERD_CONTRACT", Map.of());
        fills.add(() -> {
            DyeColor[] colors = { DyeColor.WHITE, DyeColor.PURPLE, DyeColor.BLACK };
            for (int i = 0; i < colors.length; i++) {
                DyeColor color = colors[i];
                world.spawn(shepherd.getLocation().add(-1.5 + i * 1.5, 0, 1.5), Sheep.class, sheep -> {
                    sheep.setColor(color);
                    sheep.setRemoveWhenFarAway(false);
                    tag(sheep);
                });
            }
        });

        Block beekeeper = world.getBlockAt(ox + 14, y, startZ + 36);
        for (int i = -1; i <= 1; i += 2) {
            Block hive = beekeeper.getRelative(i * 2, 0, 0);
            setBlock(hive, Material.BEEHIVE);
            org.bukkit.block.data.type.Beehive data = (org.bukkit.block.data.type.Beehive) hive.getBlockData();
            data.setHoneyLevel(data.getMaximumHoneyLevel());
            hive.setBlockData(data, false);
        }
        shrine(beekeeper, "BEEKEEPER_CONTRACT", Map.of());

        // Acolyte: beside the tier-0 summoning circle, stocked with the Brood Mother's offerings
        Block tier0 = summonAltars.get(0);
        Optional<RitualRecipe> brood = recipeFor("BROOD_MOTHER");
        if (tier0 != null && brood.isPresent()) {
            Block acolyte = tier0.getRelative(0, 0, 6);
            Map<Material, Integer> stock = Map.of(Material.STRING, 32, Material.SPIDER_EYE, 16, Material.FERMENTED_SPIDER_EYE, 4);
            shrine(acolyte, "ACOLYTE_CONTRACT", stock);
            loops.add("ACOLYTE;" + acolyte.getX() + ";" + acolyte.getY() + ";" + acolyte.getZ() + ";" + tier0.getX() + ";" + tier0.getY() + ";" + tier0.getZ());
            fills.add(() -> {
                plugin.rituals().rememberRitual(tier0, brood.get());
                SlimefunItem salt = SlimefunItem.getById(ItemKeys.slimefunId("GRAVE_SALT"));
                BlockMenu menu = BlockStorage.getInventory(acolyte);
                if (menu != null && salt != null) {
                    ItemStack salts = salt.getItem().clone();
                    salts.setAmount(16);
                    menu.pushItem(salts, ServitorShrine.STORE);
                }
            });
        }
        buildMachines(startZ + 62);
    }

    /**
     * Powered machines and the Servitor Nexus. Power: an Infinity Panel (InfinityExpansion2) through an Energy Regulator
     * and connectors - a real Slimefun network. Without InfinityExpansion2 the showcase loop keeps the machines charged.
     */
    private void buildMachines(int z0) {
        int y = floorY + 1;
        title(new Location(world, ox + 0.5, floorY + 5, z0 + 1.5), "&c&lMACHINES & POWER\n&7Working machines on a Slimefun power network");
        boolean generator = ShowcaseLoop.exists("IE_INFINITY_PANEL");
        if (generator) {
            demoBlock(world.getBlockAt(ox - 15, y, z0 + 6), "IE_INFINITY_PANEL");
        }
        demoBlock(world.getBlockAt(ox - 12, y, z0 + 6), "ENERGY_REGULATOR");
        demoBlock(world.getBlockAt(ox - 12, y, z0 + 8), "SMALL_CAPACITOR");
        for (int x : new int[] { -8, -3, 2 }) {
            DebugWorld.placeSlimefun(world.getBlockAt(ox + x, y, z0 + 6), "ENERGY_CONNECTOR", this::record);
        }
        String[] machines = { "OCCULT_FORGE", "SOUL_CONDENSER", "HOLLOW_ASSEMBLER" };
        for (int i = 0; i < machines.length; i++) {
            Block machine = world.getBlockAt(ox - 8 + i * 5, y, z0 + 4);
            demoBlock(machine, machines[i]);
            loops.add("MACHINE;" + machine.getX() + ";" + machine.getY() + ";" + machine.getZ());
            if (!generator) {
                loops.add("CHARGE;" + machine.getX() + ";" + machine.getY() + ";" + machine.getZ());
            }
        }

        // the Arcane Altar: everything in the middle, the pedestals only show it; the loop runs an infusion every 10s
        Block arcane = world.getBlockAt(ox + 13, y, z0 + 5);
        demoBlock(arcane, "ARCANE_ALTAR");
        for (int[] o : new int[][] { { 2, 0 }, { 2, 2 }, { 0, 2 }, { -2, 2 }, { -2, 0 }, { -2, -2 }, { 0, -2 }, { 2, -2 } }) {
            DebugWorld.placeSlimefun(arcane.getRelative(o[0], 0, o[1]), "OCCULTECH_ARCANE_PEDESTAL", this::record);
        }
        loops.add("ARCANE;" + arcane.getX() + ";" + arcane.getY() + ";" + arcane.getZ());

        // the Servitor Nexus with its own two shrines (far enough from the contract demos not to link them)
        int zn = z0 + 16;
        Block nexus = world.getBlockAt(ox, y, zn);
        demoBlock(nexus, "SERVITOR_NEXUS");
        Block linkedHarvest = world.getBlockAt(ox - 6, y, zn);
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                if (dx != 0 || dz != 0) {
                    setBlock(linkedHarvest.getRelative(dx, -1, dz), Material.SOUL_SAND);
                    Block wart = linkedHarvest.getRelative(dx, 0, dz);
                    setBlock(wart, Material.NETHER_WART);
                    Ageable age = (Ageable) wart.getBlockData();
                    age.setAge(age.getMaximumAge());
                    wart.setBlockData(age, false);
                }
            }
        }
        shrine(linkedHarvest, "HARVEST_CONTRACT", Map.of());
        Block linkedGather = world.getBlockAt(ox + 6, y, zn);
        shrine(linkedGather, "GATHER_CONTRACT", Map.of());
    }

    private void shrine(Block block, String contract, Map<Material, Integer> supplies) {
        demoBlock(block, "SERVITOR_SHRINE");
        String demo = contract.replace("_CONTRACT", "");
        if (List.of("HARVEST", "GATHER", "BREWER", "SHEPHERD", "BEEKEEPER").contains(demo)) {
            loops.add(demo + ";" + block.getX() + ";" + block.getY() + ";" + block.getZ());
        }
        BlockStorage.addBlockInfo(block, "occultech_owner", sender instanceof Player p ? p.getUniqueId().toString() : DEMO_OWNER);
        fills.add(() -> {
            BlockMenu menu = BlockStorage.getInventory(block);
            SlimefunItem item = SlimefunItem.getById(ItemKeys.slimefunId(contract));
            if (menu == null || item == null) {
                return;
            }
            menu.replaceExistingItem(ServitorShrine.CONTRACT_SLOT, item.getItem().clone());
            supplies.forEach((type, amount) -> menu.pushItem(new ItemStack(type, amount), ServitorShrine.STORE));
        });
    }

    private boolean demoBlock(Block block, String id) {
        return DebugWorld.placeSlimefun(block, ItemKeys.slimefunId(id), this::record);
    }

    // ------------------------------------------------------------------ studios

    /** What one studio shows, built on the block above its floor at the studio's middle. */
    private record Studio(String name, java.util.function.Consumer<Block> build) {}

    /**
     * The studios, west of the hallway: a row (or more) per kind - armor sets, weapons, machines, cosmetics, ritual
     * recipes - each studio on its own, its open front to the south.
     */
    private void buildStudios() {
        Map<String, List<Studio>> kinds = new LinkedHashMap<>();
        kinds.put("armor sets", List.of("FRENZIED", "ABYSSAL", "HOLLOW").stream()
            .filter(set -> SlimefunItem.getById(ItemKeys.slimefunId(set + "_HELMET")) != null)
            .map(set -> new Studio(set, center -> armorStudio(center, set))).toList());
        kinds.put("weapons", itemsWhere("weapon").stream().map(def -> new Studio(def.id(), center -> weaponStudio(center, def.id()))).toList());
        kinds.put("machines", itemsWhere("machine").stream().map(def -> new Studio(def.id(), center -> machineStudio(center, def.id()))).toList());
        kinds.put("cosmetics", itemsWhere("decoration").stream().map(def -> new Studio(def.id(), center -> cosmeticStudio(center, def.id()))).toList());
        kinds.put("ritual recipes", plugin.rituals().recipes().stream().filter(recipe -> !recipe.isSummon() && recipe.outputId() != null)
            .map(recipe -> new Studio(recipe.outputId(), center -> ritualStudio(center, recipe))).toList());

        int rows = kinds.values().stream().mapToInt(list -> (list.size() + STUDIOS_PER_ROW - 1) / STUDIOS_PER_ROW).sum();
        int pitchX = STUDIO_WIDTH + STUDIO_GAP;
        int pitchZ = STUDIO_DEPTH + STUDIO_APRON + STUDIO_GAP;
        int east = ox + STUDIOS_EAST;
        int north = oz + START_Z;
        for (int x = east - STUDIOS_PER_ROW * pitchX; x <= east + 15; x += 16) {
            for (int z = north; z <= north + rows * pitchZ + 15; z += 16) {
                Chunk chunk = world.getChunkAt(x >> 4, z >> 4);
                if (ticketed.add(chunk)) {
                    chunk.addPluginChunkTicket(plugin);
                }
            }
        }
        int z0 = north;
        for (Map.Entry<String, List<Studio>> kind : kinds.entrySet()) {
            List<Studio> studios = kind.getValue();
            for (int i = 0; i < studios.size(); i++) {
                if (i > 0 && i % STUDIOS_PER_ROW == 0) {
                    z0 += pitchZ;
                }
                int x0 = east - STUDIO_WIDTH - (i % STUDIOS_PER_ROW) * pitchX;
                studioShell(x0, z0);
                studios.get(i).build().accept(world.getBlockAt(x0 + STUDIO_WIDTH / 2, floorY + 1, z0 + STUDIO_DEPTH / 2));
            }
            if (!studios.isEmpty()) {
                studioRows.add(kind.getKey() + " (" + studios.size() + ") from x " + (east - 1) + ", z " + (z0 - (studios.size() - 1) / STUDIOS_PER_ROW * pitchZ)
                    + ", running west");
                z0 += pitchZ;
            }
        }
    }

    /** White concrete floor (with an apron in front for a camera), a white backdrop on three sides, hidden lights. */
    private void studioShell(int x0, int z0) {
        for (int x = x0; x < x0 + STUDIO_WIDTH; x++) {
            for (int z = z0; z < z0 + STUDIO_DEPTH + STUDIO_APRON; z++) {
                setBlock(world.getBlockAt(x, floorY, z), Material.WHITE_CONCRETE);
                boolean wall = z < z0 + STUDIO_DEPTH && (z == z0 || x == x0 || x == x0 + STUDIO_WIDTH - 1);
                for (int y = floorY + 1; y <= floorY + STUDIO_WALL; y++) {
                    if (wall) {
                        setBlock(world.getBlockAt(x, y, z), Material.WHITE_CONCRETE);
                    }
                }
            }
        }
        // light blocks (invisible, no collision) keep the studio evenly bright, day or night
        for (int lx = x0 + 3; lx < x0 + STUDIO_WIDTH - 1; lx += 6) {
            for (int lz = z0 + 3; lz < z0 + STUDIO_DEPTH + STUDIO_APRON - 1; lz += 6) {
                for (int ly : new int[] { floorY + 4, floorY + 9 }) {
                    setBlock(world.getBlockAt(lx, ly, lz), Material.LIGHT);
                }
            }
        }
    }

    private List<ItemCatalog.ItemDef> itemsWhere(String category) {
        return plugin.catalog().items().stream()
            .filter(def -> category.equals(def.category()) && SlimefunItem.getById(ItemKeys.slimefunId(def.id())) != null).toList();
    }

    /** A player-shaped stand (a Mannequin: no AI, can't be pushed or hurt, no caption), facing the camera. */
    private void mannequin(Block at, java.util.function.Consumer<org.bukkit.inventory.EntityEquipment> dress) {
        Location spot = at.getLocation().add(0.5, 0, 0.5);
        spot.setYaw(0);   // south: towards the open front
        world.spawn(spot, org.bukkit.entity.Mannequin.class, m -> {
            m.setDescription(net.kyori.adventure.text.Component.empty());
            m.setImmovable(true);
            m.setInvulnerable(true);
            m.setSilent(true);
            m.setRemoveWhenFarAway(false);
            dress.accept(m.getEquipment());
            tag(m);
        });
    }

    private static ItemStack stack(String id) {
        SlimefunItem item = SlimefunItem.getById(ItemKeys.slimefunId(id));
        return item == null ? null : item.getItem().clone();
    }

    private void armorStudio(Block center, String set) {
        mannequin(center, gear -> {
            gear.setHelmet(stack(set + "_HELMET"));
            gear.setChestplate(stack(set + "_CHESTPLATE"));
            gear.setLeggings(stack(set + "_LEGGINGS"));
            gear.setBoots(stack(set + "_BOOTS"));
        });
    }

    private void weaponStudio(Block center, String id) {
        mannequin(center, gear -> gear.setItemInMainHand(stack(id)));
    }

    /** A machine, front to the camera, kept charged and stocked by the showcase loop (the Arcane Altar infuses). */
    private void machineStudio(Block center, String id) {
        if (id.equals("ARCANE_ALTAR")) {
            demoBlock(center, id);
            for (int[] o : new int[][] { { 2, 0 }, { 2, 2 }, { 0, 2 }, { -2, 2 }, { -2, 0 }, { -2, -2 }, { 0, -2 }, { 2, -2 } }) {
                DebugWorld.placeSlimefun(center.getRelative(o[0], 0, o[1]), "OCCULTECH_ARCANE_PEDESTAL", this::record);
            }
            loops.add("ARCANE;" + center.getX() + ";" + center.getY() + ";" + center.getZ());
            return;
        }
        if (demoBlock(center, id) && plugin.customBlocks() != null && plugin.customBlocks().enabled()) {
            plugin.customBlocks().place(center, ItemKeys.slimefunId(id), 0, BlockFace.SOUTH);   // its front to the camera
        }
        loops.add("MACHINE;" + center.getX() + ";" + center.getY() + ";" + center.getZ());
        loops.add("CHARGE;" + center.getX() + ";" + center.getY() + ";" + center.getZ());
    }

    /** A cosmetic as it's used: tiles laid in the floor, flowers on grass, the netherrack lit, the trophy board filled. */
    private void cosmeticStudio(Block center, String id) {
        switch (id) {
            case "CHIMING_TILE", "TIDAL_TILE", "RESIN_TILE" -> {
                for (int dx = -2; dx <= 2; dx++) {
                    for (int dz = -2; dz <= 2; dz++) {
                        DebugWorld.placeSlimefun(center.getRelative(dx, -1, dz), ItemKeys.slimefunId(id), this::record);
                    }
                }
            }
            case "FLOOR_SIGIL" -> demoBlock(center.getRelative(0, -1, 0), id);
            case "MOONLIT_LILY", "WITCHCAP", "WATCHFUL_EYEBLOSSOM" -> {
                setBlock(center.getRelative(0, -1, 0), Material.GRASS_BLOCK);
                demoBlock(center, id);
            }
            case "PRISMATIC_NETHERRACK" -> {
                demoBlock(center, id);
                setBlock(center.getRelative(0, 1, 0), Material.FIRE);
            }
            case "TROPHY_BOARD" -> {
                demoBlock(center, id);
                BlockStorage.addBlockInfo(center, "occultech_trophy", "BROOD_MOTHER;0;the showcase");
            }
            default -> demoBlock(center, id);
        }
    }

    /**
     * A ritual ready to run: its circle (the altar a little behind the middle, so the whole circle is in shot) filled
     * with the offerings; press Begin Ritual. A button behind the east wall (out of shot) restocks it.
     */
    private void ritualStudio(Block center, RitualRecipe recipe) {
        Block altar = center.getRelative(0, 0, -1);
        DebugWorld.buildCircle(altar, recipe.circle(), this::record);
        fills.add(() -> fill(altar, recipe));
        Block outside = world.getBlockAt(center.getX() + STUDIO_WIDTH / 2 + 2, floorY, center.getZ() + STUDIO_DEPTH / 2 - 2);
        restockButton(outside, altar, recipe.outputId().substring(ItemKeys.PREFIX.length()));
    }

    // ------------------------------------------------------------------ helpers

    private List<ItemCatalog.ItemDef> itemsOf(int tier) {
        List<ItemCatalog.ItemDef> items = new ArrayList<>();
        for (ItemCatalog.ItemDef def : plugin.catalog().items()) {
            if (def.tier() == tier && SlimefunItem.getById(ItemKeys.slimefunId(def.id())) != null) {
                items.add(def);
            }
        }
        return items;
    }

    private Optional<RitualRecipe> recipeFor(String bossId) {
        return plugin.rituals().recipes().stream().filter(r -> bossId.equals(r.bossId())).findFirst();
    }

    private int arenaRadius(int tier) {
        return (int) Math.round(plugin.rituals().spec(BOSS_ORDER.get(tier).get(0)).map(s -> s.arenaRadius()).orElse(18.0 + 2 * tier));
    }

    private void setBlock(Block block, Material type) {
        record(block);
        block.setType(type, false);
    }

    private void title(Location at, String text) {
        world.spawn(at, TextDisplay.class, display -> {
            display.setText(ChatColor.translateAlternateColorCodes('&', text));
            display.setBillboard(Display.Billboard.CENTER);
            display.setShadowed(true);
            display.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(2F, 2F, 2F), new AxisAngle4f()));
            tag(display);
        });
    }

    private static void tag(Entity entity) {
        entity.getPersistentDataContainer().set(Keys.SHOWCASE, PersistentDataType.BYTE, (byte) 1);
    }

    private void record(Block block) {
        previous.putIfAbsent(block, block.getBlockData().clone());
    }

    private void save() {
        YamlConfiguration data = new YamlConfiguration();
        data.set("world", world.getName());
        if (previousMobSpawning != null) {
            data.set("mob-spawning", previousMobSpawning);
        }
        List<String> blocks = new ArrayList<>();
        previous.forEach((block, blockData) -> blocks.add(block.getX() + ";" + block.getY() + ";" + block.getZ() + ";" + blockData.getAsString()));
        data.set("blocks", blocks);
        data.set("loops", loops);
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
