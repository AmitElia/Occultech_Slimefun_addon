package io.github.amitelia.occultech.debug;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Chunk;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.data.BlockData;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Item;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Slime;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.items.OfferingBowl;
import io.github.amitelia.occultech.items.RitualAltar;
import io.github.amitelia.occultech.items.RitualService;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * In-game integration test, runnable from the console: {@code occultech selftest}.
 * <p>
 * Builds a real Initiate's circle next to spawn and checks: registration, circle detection, a crafting ritual, a
 * summoning ritual, every tier-0 boss spawning / ticking / dying cleanly (no vanilla drops, no slime splits, no
 * leftover entities), catalyst refunds and crash recovery. Restores the area afterwards.
 */
final class SelfTest {

    private static final String CATALYST = ItemKeys.slimefunId("SOVEREIGN_CATALYST");
    private static final String ACTIVE_KEY = "occultech_active_fight";
    private static final List<String> BOSSES = List.of("BROOD_MOTHER", "VOLLEY", "WITCH_COVEN", "GELATINOUS_SOVEREIGN");
    private static final List<String> TIER1_BOSSES = List.of("THE_UNBOUND", "NIGHT_MATRIARCH", "MIRRORED_MAGUS", "ARCHEVOKER");
    private static final List<String> TIER2_BOSSES = List.of("ABYSSAL_WARDEN", "TIDEBREAKER", "BLAZE_CHOIR", "TEMPEST", "DROWNED_ELDER");
    private static final List<String> TIER3_BOSSES = List.of("HOLLOW_WARLORD", "HEARTWOOD_HORROR", "DREAD_RIDERS", "CORRUPTED_COLOSSUS", "DOPPELGANGER");

    private record Step(long delay, Runnable action) {}

    private final Occultech plugin;
    private final RitualService rituals;
    private final BossService bosses;
    private final CommandSender sender;
    private final Map<Block, BlockData> previous = new LinkedHashMap<>();
    private final Deque<Step> steps = new ArrayDeque<>();
    private int passed;
    private int failed;
    private Block altar;
    private Chunk chunk;
    private BossFight currentFight;
    private Block bound;
    private Block testAltar;
    private Block shrine;
    private Block wart;
    private Chunk chunk2;
    private Chunk chunk3;
    private Block stand;
    private Block hive;
    private Block idolA;
    private Block idolB;
    private Block acolyte;
    private RitualRecipe acolyteRecipe;
    private int[] repairBowl;
    private org.bukkit.entity.Sheep sheep;
    private java.util.UUID minionOwner;
    private List<org.bukkit.entity.Mob> minionList = List.of();
    private org.bukkit.entity.LivingEntity victim;
    private int diamondsBefore;
    private org.bukkit.entity.Item testDrop;
    private Block broodEgg;
    private java.util.Set<java.util.UUID> slimesBefore = java.util.Set.of();

    SelfTest(Occultech plugin, CommandSender sender) {
        this.plugin = plugin;
        this.rituals = plugin.rituals();
        this.bosses = rituals.bosses();
        this.sender = sender;
    }

    void run() {
        say("&5[Occultech] Self-test starting...");
        bosses.setAwayRules(false);   // its fights run with nobody watching; the away timer is tested on its own
        then(0, this::registration);
        then(0, this::buildCircle);
        then(5, this::circleDetection);
        then(0, this::fillForHolograms);
        // Slimefun's block ticker needs a few seconds to start after the server boots
        then(120, this::hologramsShown);
        then(0, this::craftingRitual);
        then(RitualService.DURATION_TICKS + 20L, this::craftingResult);
        then(0, this::placeBroodEgg);
        then(40, this::broodEggWorks);
        then(0, this::lootTables);
        then(0, this::summonRitual);
        then(RitualService.DURATION_TICKS + 20L, this::summonResult);
        then(12, this::killCurrentFight);   // a fight's effects go with it: let the hit burst check see its frames first
        then(30, () -> checkFightEndedCleanly("Brood Mother (ritual)"));
        then(100, () -> check("the fight's sigil folds away when the fight is over", sigils().isEmpty(), String.valueOf(sigils())));
        for (String bossId : BOSSES) {
            then(0, () -> summonDirect(bossId));
            then(60, () -> checkFightRunning(bossId));
            then(0, () -> checkMovement(bossId));
            then(0, this::killCurrentFight);
            then(30, () -> checkFightEndedCleanly(ContentRegistrar.title(bossId)));
        }
        then(0, this::lootKeptForAbsent);
        then(0, this::refundOnInterruption);
        then(5, this::crashRecovery);
        then(5, this::awayStart);
        then(40, this::awayRecovering);
        then(100, this::awayEnded);
        then(5, this::banishEnds);
        then(5, this::saveStart);
        then(110, this::fightSaved);
        then(5, this::fightResumed);
        then(5, this::ritualCrash);

        // ---- tier 1
        then(0, this::buildUpgradeCircle);
        then(5, this::startAltarUpgrade);
        then(RitualService.DURATION_TICKS + 20L, this::altarUpgraded);
        then(0, this::buildBoundRing);
        then(5, this::boundCircleComplete);
        then(0, this::spiritEssenceRitual);
        then(RitualService.DURATION_TICKS + 20L, this::spiritEssenceResult);
        for (String bossId : TIER1_BOSSES) {
            then(0, () -> summonTier1(bossId));
            then(60, () -> checkFightRunning(bossId));
            then(0, () -> checkMovement(bossId));
            then(0, this::killCurrentFight);
            then(30, () -> checkFightEndedCleanly(ContentRegistrar.title(bossId)));
        }
        then(0, this::buildShrine);
        then(5, this::startHarvest);
        then(70, this::harvested);
        then(0, this::startGather);
        then(70, this::gathered);
        then(0, this::startWard);
        then(30, this::warded);
        then(100, this::strayOrbsSwept);
        then(0, this::scryingMirror);

        // ---- more shrine contracts and edge cases
        then(0, this::startBrewer);
        then(70, this::brewed);
        then(0, this::startShepherd);
        then(70, this::sheared);
        then(0, this::startBeekeeper);
        then(70, this::beesKept);
        then(0, this::speedRules);
        then(0, this::placementCap);
        then(0, this::startAcolyte);
        then(200, this::acolyteRestocked);
        then(0, this::contractSwap);
        then(50, this::contractSwapped);

        // ---- repair ritual and necromancy
        then(0, this::startRepair);
        then(RitualService.DURATION_TICKS + 20L, this::repaired);
        then(0, this::raiseMinions);
        then(100, this::minionsAttack);

        // ---- tier 2
        then(0, this::tier2Items);
        then(0, this::startAbyssalUpgrade);
        then(RitualService.DURATION_TICKS + 20L, this::abyssalUpgraded);
        // clearing and re-placing Slimefun blocks on the same spot must not happen in one tick: the storage is async
        then(0, this::clearForAbyssalRing);
        then(20, this::buildAbyssalRing);
        then(20, this::abyssalCircleComplete);
        then(0, this::startHelmRitual);
        then(RitualService.DURATION_TICKS + 20L, this::helmResult);
        for (String bossId : TIER2_BOSSES) {
            then(0, () -> summonTier1(bossId));
            then(60, () -> checkFightRunning(bossId));
            then(0, () -> checkMovement(bossId));
            if (bossId.equals("BLAZE_CHOIR")) {
                then(0, this::killAllButOneSinger);
                then(15, this::lastSingerBare);
            }
            then(0, this::killCurrentFight);
            then(30, () -> checkFightEndedCleanly(ContentRegistrar.title(bossId)));
        }
        then(0, this::placeGuardianEye);
        then(60, this::guardianEyeFired);
        then(0, this::tetherShrine);
        then(30, this::tethered);
        then(0, this::decorationPalette);
        then(60, this::trophyShown);

        // ---- tier 3
        then(0, this::tier3Items);
        then(0, this::startHollowUpgrade);
        then(RitualService.DURATION_TICKS + 20L, this::hollowUpgraded);
        then(0, this::clearForHollowRing);
        then(20, this::buildHollowRing);
        then(20, this::hollowCircleComplete);
        for (String bossId : TIER3_BOSSES) {
            then(0, () -> summonTier1(bossId));
            then(60, () -> checkFightRunning(bossId));
            then(0, () -> checkMovement(bossId));
            then(0, this::killCurrentFight);
            then(30, () -> checkFightEndedCleanly(ContentRegistrar.title(bossId)));
        }
        then(0, () -> summonTier1("GALLUS"));
        then(60, () -> checkFightRunning("GALLUS"));
        then(0, () -> checkMovement("GALLUS"));
        then(0, () -> setGallusHealth(0.6));
        then(20, this::gallusUnhorsed);
        then(0, () -> setGallusHealth(0.3));
        then(20, this::gallusHollowed);
        then(0, this::killCurrentFight);
        then(30, () -> checkFightEndedCleanly("Gallus"));
        then(0, this::buildArcaneAltar);
        then(10, this::startArcaneInfusion);
        then(90, this::arcaneResult);
        then(0, this::arcaneCrash);
        then(0, this::placeNexus);
        then(80, this::nexusLinked);
        then(70, this::nexusGathered);
        next();
    }

    // ------------------------------------------------------------------ steps

    /** The resource pack: loaded, item models set on items that have art (and only those), and served if self-hosted. */
    private void resourcePack() {
        var pack = plugin.resourcePack();
        check("resource pack loaded", pack.packSize() > 0 && pack.modelCount() > 0, pack.packSize() + " bytes, " + pack.modelCount() + " models");
        ItemStack silver = SlimefunItem.getById(ItemKeys.slimefunId("WARDED_SILVER")).getItem();
        var model = silver.getItemMeta() == null ? null : silver.getItemMeta().getItemModel();
        check("items with art get their occultech model", model != null && model.toString().equals("occultech:warded_silver"), String.valueOf(model));
        // any registered item the pack has no model for (none left once all art is done: then there is nothing to check)
        var bare = plugin.catalog().items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER)
            .filter(i -> pack.modelFor(i.id()) == null).map(i -> SlimefunItem.getById(ItemKeys.slimefunId(i.id())))
            .filter(java.util.Objects::nonNull).findFirst();
        check("items without art keep their vanilla look", bare.map(i -> i.getItem().getItemMeta() == null
            || !i.getItem().getItemMeta().hasItemModel()).orElse(true), bare.map(SlimefunItem::getId).orElse("-") + " has a model");
        long modelled = plugin.catalog().items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER)
            .map(i -> SlimefunItem.getById(ItemKeys.slimefunId(i.id()))).filter(java.util.Objects::nonNull)
            .filter(i -> i.getItem().getItemMeta() != null && i.getItem().getItemMeta().hasItemModel()).count();
        check(pack.modelCount() + " registered items carry a model", modelled == pack.modelCount(), modelled + " carry one");
        check("blocks are skinned (Initiate's Altar, Offering Bowl, glyphs...)", plugin.skins().isSkinned(ItemKeys.slimefunId("INITIATE_ALTAR"))
            && plugin.skins().isSkinned(ItemKeys.slimefunId("OFFERING_BOWL")), "no skins in the pack");
        if ("self-host".equals(pack.mode()) && pack.url() != null) {
            try {
                java.net.URI local = java.net.URI.create("http://localhost:" + pack.url().getPort() + pack.url().getPath());
                var client = java.net.http.HttpClient.newBuilder().connectTimeout(java.time.Duration.ofSeconds(3)).build();
                var response = client.send(java.net.http.HttpRequest.newBuilder(local).timeout(java.time.Duration.ofSeconds(3)).build(),
                    java.net.http.HttpResponse.BodyHandlers.ofByteArray());
                String sha1 = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-1").digest(response.body()));
                check("the pack is served and matches its hash", response.statusCode() == 200 && sha1.equals(pack.sha1()),
                    response.statusCode() + ", " + response.body().length + " bytes");
            } catch (Exception e) {
                check("the pack is served and matches its hash", false, e.toString());
            }
        }
    }

    private void registration() {
        ContentRegistrar registrar = plugin.registrar();
        ItemCatalog catalog = plugin.catalog();
        long expected = catalog.items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER).count();
        long registered = catalog.items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER)
            .filter(i -> SlimefunItem.getById(ItemKeys.slimefunId(i.id())) != null).count();
        check("all " + expected + " items up to tier " + ContentRegistrar.IMPLEMENTED_TIER + " registered", registered == expected, registered + " registered");
        check("no content problems", registrar.problems().isEmpty(), String.join("; ", registrar.problems()));
        check("researches registered", registrar.researchCount() == catalog.researches().size(), registrar.researchCount() + " registered");
        recipeClashes();
        // Session B1: every boss declares its attacks, so the combat log and the balance report cover all its damage
        List<Balance.Grade> grades = Balance.grades(plugin, 1);
        List<String> silent = bosses.blueprints().stream().map(io.github.amitelia.occultech.boss.BossBlueprint::id)
            .filter(id -> grades.stream().noneMatch(g -> g.mechanic().bossId().equals(id))).toList();
        check("every boss declares its attacks (" + grades.size() + " attacks)", silent.isEmpty(), "none for " + silent);
        // Session B2: tiers 0-2 hit inside their bands against benchmark gear (tier 3 waits for playtests)
        List<String> off = grades.stream().filter(g -> g.tier() <= 2 && !g.ok())
            .map(g -> g.mechanic().bossId() + " " + g.mechanic().name() + String.format(" %.0f%%", g.share() * 100)).toList();
        check("tier 0-2 boss attacks land in their bands", off.isEmpty(), String.join("; ", off));
        // Session B2 armor: Abyssal = max netherite, Hollow = Protection X with extra toughness
        ItemStack abyssal = SlimefunItem.getById(ItemKeys.slimefunId("ABYSSAL_HELMET")).getItem();
        check("Abyssal armor has Protection IV", abyssal.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION) == 4,
            String.valueOf(abyssal.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION)));
        ItemStack hollow = SlimefunItem.getById(ItemKeys.slimefunId("HOLLOW_CHESTPLATE")).getItem();
        var modifiers = hollow.getItemMeta().getAttributeModifiers();
        double toughness = modifiers == null ? 0 : modifiers.get(org.bukkit.attribute.Attribute.ARMOR_TOUGHNESS).stream().mapToDouble(m -> m.getAmount()).sum();
        double armor = modifiers == null ? 0 : modifiers.get(org.bukkit.attribute.Attribute.ARMOR).stream().mapToDouble(m -> m.getAmount()).sum();
        check("Hollow armor has Protection X, netherite armor and extra toughness",
            hollow.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION) == 10 && armor == 8 && toughness == 5,
            "protection " + hollow.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION) + ", armor " + armor + ", toughness " + toughness);
        resourcePack();
        long summons = rituals.recipes().stream().filter(RitualRecipe::isSummon).count();
        int expectedSummons = BOSSES.size() + TIER1_BOSSES.size() + TIER2_BOSSES.size() + TIER3_BOSSES.size() + 1;
        check(expectedSummons + " summoning rituals registered", summons == expectedSummons, summons + " summons");
    }

    /**
     * Two recipes with the same grid on the same machine (ours, or another addon's) mean one of them can never be
     * crafted (Session P4). Grids are compared shape and all: item id (or material) and amount per slot.
     */
    private void recipeClashes() {
        Map<String, String> grids = new java.util.HashMap<>();
        List<String> clashes = new java.util.ArrayList<>();
        int ours = 0;
        for (SlimefunItem item : io.github.thebusybiscuit.slimefun4.implementation.Slimefun.getRegistry().getEnabledSlimefunItems()) {
            if (item.getRecipeType() == null || item.getRecipe() == null
                || item.getRecipeType() == io.github.amitelia.occultech.setup.OccultechRecipeTypes.BOSS_DROP) {
                continue;   // a drop's grid only shows the boss: several drops of one boss share it, nothing is crafted
            }
            StringBuilder grid = new StringBuilder(item.getRecipeType().getKey().toString()).append('|');
            boolean any = false;
            for (ItemStack in : item.getRecipe()) {
                if (in == null || in.getType().isAir()) {
                    grid.append("-,");
                    continue;
                }
                SlimefunItem sf = SlimefunItem.getByItem(in);
                grid.append(sf != null ? sf.getId() : in.getType().name()).append('x').append(in.getAmount()).append(',');
                any = true;
            }
            if (!any) {
                continue;
            }
            boolean mine = item.getId().startsWith(ItemKeys.slimefunId(""));
            ours += mine ? 1 : 0;
            String other = grids.putIfAbsent(grid.toString(), item.getId());
            if (other != null && (mine || other.startsWith(ItemKeys.slimefunId("")))) {
                clashes.add(other + " = " + item.getId());
            }
        }
        check("no two recipes share a grid (" + ours + " Occultech recipes checked)", clashes.isEmpty(), String.join("; ", clashes));
    }

    private void buildCircle() {
        World world = Bukkit.getWorlds().get(0);
        // west of the showcase hallway, so the two never overlap
        int x = world.getSpawnLocation().getBlockX() - 48;
        int z = world.getSpawnLocation().getBlockZ() + 24;
        chunk = world.getChunkAt(x >> 4, z >> 4);
        chunk.addPluginChunkTicket(plugin);
        altar = world.getBlockAt(x, world.getHighestBlockYAt(x, z) + 1, z);
        DebugWorld.buildCircle(altar, 0, block -> previous.putIfAbsent(block, block.getBlockData()));
    }

    private org.bukkit.entity.ItemDisplay glyphSkinInTest;

    private void circleDetection() {
        var blocks = plugin.skins().blocks();
        if (blocks.enabled()) {
            customBlocks(blocks);
        } else {
            skinsOnBlocks();
        }
        Optional<RitualService.CircleCheck> check = rituals.checkCircle(altar);
        check("altar recognised", check.isPresent(), "id " + BlockStorage.checkID(altar));
        check("complete circle detected", check.isPresent() && check.get().complete(), check.map(c -> c.missing().size() + " missing").orElse("-"));

        Block corner = altar.getRelative(-2, 0, -2);
        BlockStorage.clearBlockInfo(corner);
        corner.setType(Material.AIR);
        plugin.skins().validate();
        if (!blocks.enabled()) {
            check("a removed block loses its skin", glyphSkinInTest == null || !glyphSkinInTest.isValid(), "the skin is still there");
        }
        Optional<RitualService.CircleCheck> broken = rituals.checkCircle(altar);
        check("missing glyph detected", broken.isPresent() && broken.get().missing().size() == 1, broken.map(c -> c.missing().size() + " missing").orElse("-"));
        DebugWorld.placeSlimefun(corner, Circles.CHALK_GLYPH, block -> {});
        check("altar menu exists", BlockStorage.getInventory(altar) != null, "no menu");

        if (blocks.enabled()) {
            customBlockLooks(blocks);
        } else {
            skinsFollowBlocks();
        }
    }

    /** Session N: the altar and the glyphs the build placed are custom blocks (a note block, tripwire states). */
    private void customBlocks(io.github.amitelia.occultech.items.CustomBlockService blocks) {
        Block glyphBlock = altar.getRelative(-2, 0, -2);
        var altarLook = blocks.lookOf(altar);
        check("the altar is its custom block (a note-block state)", altar.getType() == Material.NOTE_BLOCK && altarLook != null
            && altarLook.itemId().equals("INITIATE_ALTAR"), altar.getBlockData().getAsString());
        var glyphLook = blocks.lookOf(glyphBlock);
        check("a chalk glyph is a flat custom block (a tripwire state), one of its 4 looks", glyphBlock.getType() == Material.TRIPWIRE
            && glyphLook != null && glyphLook.itemId().equals("CHALK_GLYPH") && glyphLook.look() < 4, glyphBlock.getBlockData().getAsString());
        String before = altar.getBlockData().getAsString();
        plugin.skins().ensure(altar);
        check("ensure is idempotent", altar.getBlockData().getAsString().equals(before), altar.getBlockData().getAsString());
        org.bukkit.event.block.NotePlayEvent note = new org.bukkit.event.block.NotePlayEvent(altar, org.bukkit.Instrument.PIANO, new org.bukkit.Note(1));
        Bukkit.getPluginManager().callEvent(note);
        org.bukkit.event.block.BlockPhysicsEvent physics = new org.bukkit.event.block.BlockPhysicsEvent(altar, altar.getBlockData());
        Bukkit.getPluginManager().callEvent(physics);
        check("a custom block plays no note and ignores neighbour updates", note.isCancelled() && physics.isCancelled(),
            note.isCancelled() + " " + physics.isCancelled());
    }

    /** Session N: looks that follow the block - a tile's looks, a front - and old skins converted. */
    private void customBlockLooks(io.github.amitelia.occultech.items.CustomBlockService blocks) {
        Block tile = altar.getRelative(0, 0, 6);
        DebugWorld.placeSlimefun(tile, ItemKeys.slimefunId("TIDAL_TILE"), block -> previous.putIfAbsent(block, block.getBlockData()));
        boolean first = blocks.lookOf(tile) != null && blocks.lookOf(tile).look() == 0;
        blocks.place(tile, ItemKeys.slimefunId("TIDAL_TILE"), 3, null);
        check("a Tidal Tile shows its looks as custom blocks", first && blocks.lookOf(tile) != null && blocks.lookOf(tile).look() == 3,
            tile.getBlockData().getAsString());
        Block forge = altar.getRelative(2, 0, 6);
        DebugWorld.placeSlimefun(forge, ItemKeys.slimefunId("OCCULT_FORGE"), block -> previous.putIfAbsent(block, block.getBlockData()));
        blocks.place(forge, ItemKeys.slimefunId("OCCULT_FORGE"), 0, org.bukkit.block.BlockFace.EAST);
        var forgeLook = blocks.lookOf(forge);
        check("an Occult Forge's custom block faces its front", forgeLook != null && forgeLook.facing() == org.bukkit.block.BlockFace.EAST,
            forge.getBlockData().getAsString());
        // a block from before custom blocks, with its old skin: the skin goes, the block takes its look (brain coral)
        Block old = altar.getRelative(4, 0, 6);
        previous.putIfAbsent(old, old.getBlockData());
        old.setBlockData(Material.BRAIN_CORAL_BLOCK.createBlockData(), false);
        BlockStorage.store(old, ItemKeys.slimefunId("TIDAL_TILE"));
        org.bukkit.entity.ItemDisplay skin = old.getWorld().spawn(old.getLocation().add(0.5, 0.5, 0.5), org.bukkit.entity.ItemDisplay.class,
            d -> d.getPersistentDataContainer().set(io.github.amitelia.occultech.items.BlockSkinService.SKIN,
                org.bukkit.persistence.PersistentDataType.STRING, old.getX() + "," + old.getY() + "," + old.getZ() + "|" + ItemKeys.slimefunId("TIDAL_TILE")));
        plugin.skins().adopt(skin);
        var oldLook = blocks.lookOf(old);
        check("an old skinned block converts to its custom block, keeping its look", !skin.isValid() && oldLook != null
            && oldLook.itemId().equals("TIDAL_TILE") && oldLook.look() == 1, skin.isValid() + " " + old.getBlockData().getAsString());
        Block plain = altar.getRelative(6, 0, 6);
        previous.putIfAbsent(plain, plain.getBlockData());
        plain.setType(Material.NOTE_BLOCK, false);
        check("a plain note block isn't mistaken for an Occultech block", !blocks.isCustomState(plain), plain.getBlockData().getAsString());
        Block jar = altar.getRelative(7, 0, 6);
        DebugWorld.placeSlimefun(jar, ItemKeys.slimefunId("WISP_JAR"), block -> previous.putIfAbsent(block, block.getBlockData()));
        check("a model smaller than its cube is a chorus-plant custom block (it hides no neighbour's face)",
            jar.getType() == Material.CHORUS_PLANT && blocks.lookOf(jar) != null, jar.getBlockData().getAsString());
        BlockStorage.clearBlockInfo(jar);
        jar.setType(Material.AIR);
        check("the six decorations are custom blocks (G7)", java.util.stream.Stream.of("WISP_JAR", "BOTTLED_GALE", "WIND_CHIME",
            "OCCULT_ORRERY", "SOULFIRE_BRAZIER", "RUNE_OBELISK").allMatch(id -> blocks.isCustom(ItemKeys.slimefunId(id))),
            "a decoration isn't");
        for (Block block : List.of(tile, forge, old, plain)) {
            BlockStorage.clearBlockInfo(block);
            block.setType(Material.AIR);
        }
    }

    /** Display skins (custom-blocks mode skins): the altar and the glyphs placed by the build got their skin displays. */
    private void skinsOnBlocks() {
        Block glyphBlock = altar.getRelative(-2, 0, -2);
        org.bukkit.entity.ItemDisplay altarSkin = plugin.skins().ensure(altar);
        check("the altar wears its skin", altarSkin != null && altarSkin.getItemStack().getItemMeta().hasItemModel()
            && altarSkin.getItemStack().getItemMeta().getItemModel().toString().equals("occultech:initiate_altar"),
            altarSkin == null ? "no skin" : String.valueOf(altarSkin.getItemStack().getItemMeta().getItemModel()));
        org.bukkit.entity.ItemDisplay glyphSkin = plugin.skins().ensure(glyphBlock);
        check("a chalk glyph wears one of its 4 skins", glyphSkin != null
            && glyphSkin.getItemStack().getItemMeta().getItemModel().getKey().startsWith("chalk_glyph"),
            glyphSkin == null ? "no skin (" + BlockStorage.checkID(glyphBlock) + ")" : String.valueOf(glyphSkin.getItemStack().getItemMeta().getItemModel()));
        check("ensure is idempotent (no second skin)", plugin.skins().ensure(altar) == altarSkin, "a second display");
        glyphSkinInTest = glyphSkin;
    }

    /** Display skins: skins that follow their block, upright decorations, weathering. */
    private void skinsFollowBlocks() {
        // skins that follow their block: a Tidal Tile's coral (right-click swaps it), an Occult Forge's front
        Block tile = altar.getRelative(0, 0, 6);
        DebugWorld.placeSlimefun(tile, ItemKeys.slimefunId("TIDAL_TILE"), block -> previous.putIfAbsent(block, block.getBlockData()));
        org.bukkit.entity.ItemDisplay tileSkin = plugin.skins().ensure(tile);
        tile.setBlockData(Material.BRAIN_CORAL_BLOCK.createBlockData(), false);
        org.bukkit.entity.ItemDisplay swapped = plugin.skins().ensure(tile);
        plugin.skins().validate();
        check("a Tidal Tile's skin follows its coral", tileSkin != null && swapped == tileSkin && tileSkin.isValid()
            && "tidal_tile_v1".equals(tileSkin.getItemStack().getItemMeta().getItemModel().getKey()),
            tileSkin == null ? "no skin" : tileSkin.isValid() + " " + tileSkin.getItemStack().getItemMeta().getItemModel());
        Block forge = altar.getRelative(2, 0, 6);
        DebugWorld.placeSlimefun(forge, ItemKeys.slimefunId("OCCULT_FORGE"), block -> previous.putIfAbsent(block, block.getBlockData()));
        org.bukkit.block.data.Directional facing = (org.bukkit.block.data.Directional) forge.getBlockData();
        facing.setFacing(org.bukkit.block.BlockFace.EAST);
        forge.setBlockData(facing, false);
        org.bukkit.entity.ItemDisplay forgeSkin = plugin.skins().ensure(forge);
        org.joml.Quaternionf turn = forgeSkin == null ? null : forgeSkin.getTransformation().getLeftRotation();
        org.joml.Quaternionf east = new org.joml.Quaternionf().rotationY((float) Math.PI / 2);
        check("an Occult Forge's skin turns to its front", turn != null && Math.abs(turn.y - east.y) < 1e-3 && Math.abs(turn.w - east.w) < 1e-3,
            String.valueOf(turn));
        plugin.skins().remove(forge);   // what breaking, burning or an explosion does, in the same tick
        check("a skin comes off in the same tick its block breaks", forgeSkin != null && !forgeSkin.isValid(), "still there");
        // decorations whose skins are upright objects stand their sideways-placed vanilla block up (G7)
        Block chime = altar.getRelative(4, 0, 6);
        Block rod = altar.getRelative(5, 0, 6);
        previous.putIfAbsent(chime, chime.getBlockData());
        previous.putIfAbsent(rod, rod.getBlockData());
        org.bukkit.block.data.Orientable sideways = (org.bukkit.block.data.Orientable) Material.IRON_CHAIN.createBlockData();
        sideways.setAxis(org.bukkit.Axis.X);
        chime.setBlockData(sideways, false);
        org.bukkit.block.data.Directional wall = (org.bukkit.block.data.Directional) Material.LIGHTNING_ROD.createBlockData();
        wall.setFacing(org.bukkit.block.BlockFace.EAST);
        rod.setBlockData(wall, false);
        io.github.amitelia.occultech.items.BlockSkinService.upright(chime);
        io.github.amitelia.occultech.items.BlockSkinService.upright(rod);
        check("a Wind Chime's chain and an Orrery's rod stand upright under their skins",
            ((org.bukkit.block.data.Orientable) chime.getBlockData()).getAxis() == org.bukkit.Axis.Y
                && ((org.bukkit.block.data.Directional) rod.getBlockData()).getFacing() == org.bukkit.block.BlockFace.UP,
            chime.getBlockData().getAsString() + " " + rod.getBlockData().getAsString());
        // an Occult Orrery whose copper rod weathered gets its rod (and its skin) back
        Block orrery = altar.getRelative(6, 0, 6);
        DebugWorld.placeSlimefun(orrery, ItemKeys.slimefunId("OCCULT_ORRERY"), block -> previous.putIfAbsent(block, block.getBlockData()));
        orrery.setType(Material.OXIDIZED_LIGHTNING_ROD, false);
        plugin.skins().ensureIfMissing(orrery, io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem.getById(ItemKeys.slimefunId("OCCULT_ORRERY")));
        org.bukkit.entity.ItemDisplay orrerySkin = plugin.skins().ensure(orrery);
        check("an oxidized Occult Orrery turns back to its rod and keeps its skin", orrery.getType() == Material.LIGHTNING_ROD
            && orrerySkin != null && orrerySkin.isValid(), orrery.getType() + " " + orrerySkin);
        org.bukkit.block.BlockState aged = orrery.getState();
        aged.setType(Material.EXPOSED_LIGHTNING_ROD);
        org.bukkit.event.block.BlockFormEvent weathering = new org.bukkit.event.block.BlockFormEvent(orrery, aged);
        Bukkit.getPluginManager().callEvent(weathering);
        check("an Occult Orrery's rod doesn't weather", weathering.isCancelled(), "weathering went ahead");
        check("the six decorations have skins (G7)", java.util.stream.Stream.of("WISP_JAR", "BOTTLED_GALE", "WIND_CHIME",
            "OCCULT_ORRERY", "SOULFIRE_BRAZIER", "RUNE_OBELISK").allMatch(id -> plugin.skins().isSkinned(ItemKeys.slimefunId(id))),
            "a decoration has no skin");
        for (Block block : List.of(tile, forge, chime, rod, orrery)) {
            BlockStorage.clearBlockInfo(block);
            block.setType(Material.AIR);
        }
        plugin.skins().validate();
    }

    private void fillForHolograms() {
        rituals.recipes().stream().filter(r -> CATALYST.equals(r.outputId())).findFirst().ifPresent(this::fill);
    }

    private void hologramsShown() {
        long holograms = altar.getWorld().getNearbyEntities(altar.getLocation(), 4, 4, 4).stream()
            .filter(e -> e.getPersistentDataContainer().has(Keys.HOLOGRAM, org.bukkit.persistence.PersistentDataType.BYTE)).count();
        // 4 bowls + the altar, each an item display and a label
        check("holograms above the bowls and altar", holograms >= 10, holograms + " hologram entities");
    }

    private void placeBroodEgg() {
        broodEgg = altar.getRelative(4, 0, 0);
        DebugWorld.placeSlimefun(broodEgg, ItemKeys.slimefunId("BROOD_EGG"), block -> previous.putIfAbsent(block, block.getBlockData()));
    }

    private void broodEggWorks() {
        check("Brood Egg placed as a Slimefun block", ItemKeys.slimefunId("BROOD_EGG").equals(BlockStorage.checkID(broodEgg)), "not placed");
        check("Brood Egg has a store", BlockStorage.getInventory(broodEgg) != null, "no menu");
        var preset = me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset.getPreset(ItemKeys.slimefunId("BROOD_EGG"));
        check("cargo/Networks can pull 9 slots from the Brood Egg",
            preset != null && preset.getSlotsAccessedByItemTransport(me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow.WITHDRAW).length == 9,
            "wrong withdraw slots");
        check("cargo/Networks cannot insert into the Brood Egg",
            preset != null && preset.getSlotsAccessedByItemTransport(me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow.INSERT).length == 0,
            "insert allowed");
        // make it start to crack; its ticker must reset it
        if (broodEgg.getBlockData() instanceof org.bukkit.block.data.Hatchable hatchable) {
            hatchable.setHatch(hatchable.getMaximumHatch());
            broodEgg.setBlockData(hatchable, false);
        }
        if (plugin.skins().blocks().enabled()) {   // a custom block (a note-block state): there's nothing to hatch
            check("Brood Egg is a custom block (it can't hatch)", plugin.skins().blocks().isCustomState(broodEgg),
                broodEgg.getBlockData().getAsString());
        } else {
            Bukkit.getScheduler().runTaskLater(plugin, () -> check("Brood Egg never hatches (crack reset)",
                broodEgg.getBlockData() instanceof org.bukkit.block.data.Hatchable h && h.getHatch() == 0, "still cracked"), 30L);
        }
    }

    private void lootTables() {
        BossSpec brood = rituals.spec("BROOD_MOTHER").orElseThrow();
        check("Brood Mother can drop a Brood Egg", brood.bonusDrops().containsKey(ItemKeys.slimefunId("BROOD_EGG")), brood.bonusDrops().toString());
        for (String bossId : BOSSES) {
            BossSpec spec = rituals.spec(bossId).orElseThrow();
            check(ContentRegistrar.title(bossId) + " has mob drops and XP", !spec.mobDrops().isEmpty() && spec.xp() > 0, "none");
        }
    }

    private void craftingRitual() {
        RitualRecipe recipe = rituals.recipes().stream().filter(r -> CATALYST.equals(r.outputId())).findFirst().orElse(null);
        check("catalyst ritual recipe exists", recipe != null, "missing");
        if (recipe == null) {
            return;
        }
        fill(recipe);
        check("crafting ritual starts", rituals.begin(null, altar) == RitualService.Outcome.STARTED, "did not start");
        check("offerings consumed at start", bowlsEmpty(), "bowls not empty");
        check("altar locked during ritual", rituals.isLocked(altar.getLocation()), "not locked");
        check("the circle's sigil glows on the floor during the ritual", sigils().contains("ritual_sigil_t0"), String.valueOf(sigils()));
    }

    /** The ritual sigil holograms around the altar (their models). */
    private List<String> sigils() {
        return altar.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, altar.getLocation().add(0.5, 0.1, 0.5), 1.5).stream()
            .map(d -> d.getItemStack().getItemMeta())
            .filter(meta -> meta != null && meta.hasItemModel() && meta.getItemModel().getKey().startsWith("ritual_sigil"))
            .map(meta -> meta.getItemModel().getKey()).toList();
    }

    private void craftingResult() {
        check("ritual produced Sovereign's Catalyst", CATALYST.equals(idIn(RitualAltar.CENTER_SLOT)), String.valueOf(idIn(RitualAltar.CENTER_SLOT)));
        check("altar unlocked afterwards", !rituals.isLocked(altar.getLocation()), "still locked");
        Bukkit.getScheduler().runTaskLater(plugin, () -> check("the sigil folds away after the ritual", sigils().isEmpty(),
            String.valueOf(sigils())), 15L);
    }

    private void summonRitual() {
        DebugWorld.setAltarCenter(altar, null);
        RitualRecipe recipe = rituals.recipes().stream().filter(r -> "BROOD_MOTHER".equals(r.bossId())).findFirst().orElseThrow();
        fill(recipe);
        snapshotSlimes();
        check("summoning ritual starts with an empty altar", rituals.begin(null, altar) == RitualService.Outcome.STARTED, "did not start");
        check("a channeling summon holds its area (no second fight nearby)", !bosses.canSummon(altar.getLocation().add(60, 0, 0), 10)
            && bosses.canSummon(altar.getLocation().add(400, 0, 0), 10), "area not held");
        check("a summoning shows the circle's sigil (no second pentagram)", sigils().equals(List.of("ritual_sigil_t0")),
            String.valueOf(sigils()));
    }

    private void summonResult() {
        currentFight = bosses.fightAt(altar).orElse(null);
        if (currentFight != null) {
            var guard = new io.github.amitelia.occultech.items.CircleGuard(rituals);
            RitualService.CircleCheck circle = rituals.checkCircle(altar).orElseThrow();
            int[] bowl = circle.pattern().positionsOf(Circles.OFFERING_BOWL, circle.rotation()).get(0);
            check("a circle in use is bound (altar, bowls, the ground under them)", guard.isBound(altar)
                && guard.isBound(altar.getRelative(bowl[0], 0, bowl[1])) && guard.isBound(altar.getRelative(bowl[0], -1, bowl[1])),
                "not bound");
            check("blocks outside the circle stay free", !guard.isBound(altar.getRelative(circle.pattern().radius() + 2, 0, 0)), "bound");
            check("fight entities are safe from ClearLaggEnhanced", currentFight.bosses().stream().allMatch(b -> b.getScoreboardTags()
                .contains(io.github.amitelia.occultech.core.ClearLagGuard.PROTECTED)), "no CLE_PROTECTED tag");
            check("only one fight in an area", !bosses.canSummon(altar.getLocation().add(60, 0, 0), 10), "a second fight could start 60 blocks away");
        }
        check("the sigil stays on the floor, turning, through the boss fight", sigils().contains("ritual_sigil_t0"), String.valueOf(sigils()));
        if (currentFight != null && io.github.amitelia.occultech.boss.FloorDecals.enabled()) {   // Session O4 floor markings
            org.bukkit.Location spot = altar.getLocation().add(4.5, 0, 0.5);
            currentFight.telegraph(spot, 2, 40, org.bukkit.Color.RED, io.github.amitelia.occultech.boss.FloorDecals.Mark.SLAM);
            currentFight.addHazard(spot.clone().add(0, 0, 3), 2, 60, org.bukkit.Color.LIME, io.github.amitelia.occultech.boss.FloorDecals.Zone.ACID, p -> { });
            List<String> marks = altar.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, spot, 6).stream()
                .map(d -> d.getItemStack().getItemMeta()).filter(m -> m != null && m.hasItemModel() && m.getItemModel().getKey().startsWith("floor_"))
                .map(m -> m.getItemModel().getKey()).sorted().toList();
            check("boss attacks mark the floor (a warning ring, fill and symbol; an acid zone)",
                marks.containsAll(List.of("floor_warning_ring", "floor_warning_fill", "floor_mark_slam", "floor_zone_acid")), String.valueOf(marks));
            // from a spot like a player's: looking down, feet in the air - the marking must still lie flat on the floor
            org.bukkit.Location tilted = altar.getLocation().add(-4.5, 0.4, 0.5);
            tilted.setPitch(50F);
            tilted.setYaw(70F);
            currentFight.telegraph(tilted, 1.5, 40, org.bukkit.Color.ORANGE, io.github.amitelia.occultech.boss.FloorDecals.Mark.FLAME);
            io.github.amitelia.occultech.boss.FloorDecals.wedge(currentFight, altar.getLocation().add(0.5, 0, 4.5), new org.bukkit.util.Vector(1, 0, 0), 4, 30, org.bukkit.Color.RED);
            io.github.amitelia.occultech.boss.FloorDecals.lane(currentFight, altar.getLocation().add(0.5, 0, -4.5), new org.bukkit.util.Vector(0, 0, -1), 8, 3, 30, org.bukkit.Color.BLUE);
            io.github.amitelia.occultech.boss.FloorDecals.wave(currentFight, altar.getLocation().add(0.5, 0, 0.5), 1, 4, 30, org.bukkit.Color.AQUA);
            io.github.amitelia.occultech.boss.FloorDecals.splash(currentFight, altar.getLocation().add(-4.5, 0, 4.5), 2, org.bukkit.Color.PURPLE);
            List<org.bukkit.entity.ItemDisplay> flame = altar.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, tilted, 1.5).stream()
                .filter(d -> d.getItemStack().getItemMeta() != null && d.getItemStack().getItemMeta().hasItemModel()
                    && d.getItemStack().getItemMeta().getItemModel().getKey().equals("floor_mark_flame")).toList();
            double floorTop = altar.getWorld().getBlockAt(tilted.getBlockX(), altar.getY() - 1, tilted.getBlockZ()).getBoundingBox().getMaxY();
            check("a floor marking lies flat on the floor even from a tilted spot in the air", flame.size() == 1
                && flame.get(0).getLocation().getPitch() == 0F && flame.get(0).getLocation().getYaw() == 0F
                && Math.abs(flame.get(0).getLocation().getY() - floorTop) < 0.1,
                flame.isEmpty() ? "no marking" : String.format("pitch %.0f yaw %.0f y %.2f (floor %.2f)", flame.get(0).getLocation().getPitch(),
                    flame.get(0).getLocation().getYaw(), flame.get(0).getLocation().getY(), floorTop));
            List<String> shapes = altar.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, altar.getLocation(), 9).stream()
                .map(d -> d.getItemStack().getItemMeta()).filter(m -> m != null && m.hasItemModel()).map(m -> m.getItemModel().getKey()).toList();
            // effects in the air (Session O5): a beam between two points and a bolt from the sky
            io.github.amitelia.occultech.boss.AirEffects.Streak.create(currentFight, "air_beam", altar.getLocation().add(0.5, 3, 0.5),
                altar.getLocation().add(6.5, 1, 0.5), org.bukkit.Color.AQUA, 0.4F);
            io.github.amitelia.occultech.boss.AirEffects.bolt(currentFight, altar.getLocation().add(-6.5, 0, -6.5), org.bukkit.Color.PURPLE);
            List<String> air = altar.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, altar.getLocation(), 12).stream()
                .map(d -> d.getItemStack().getItemMeta()).filter(m -> m != null && m.hasItemModel()).map(m -> m.getItemModel().getKey())
                .filter(k -> k.startsWith("air_")).toList();
            // a hit burst plays from its first frame: the server steps the frame, then it goes (Session O5, phase 2)
            org.bukkit.Location burstAt = altar.getLocation().add(3.5, 2, -3.5);
            io.github.amitelia.occultech.boss.AirEffects.burst(currentFight, burstAt, io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT,
                org.bukkit.Color.ORANGE, 2F);
            java.util.function.Supplier<List<org.bukkit.entity.ItemDisplay>> bursts = () -> altar.getWorld()
                .getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, burstAt, 1).stream()
                .filter(d -> d.getItemStack().getItemMeta() != null && d.getItemStack().getItemMeta().hasItemModel()
                    && d.getItemStack().getItemMeta().getItemModel().getKey().equals("air_burst_impact")).toList();
            float first = bursts.get().isEmpty() ? -1 : bursts.get().get(0).getItemStack()
                .getData(io.papermc.paper.datacomponent.DataComponentTypes.CUSTOM_MODEL_DATA).floats().get(0);
            Bukkit.getScheduler().runTaskLater(plugin, () -> {
                float later = bursts.get().isEmpty() ? -1 : bursts.get().get(0).getItemStack()
                    .getData(io.papermc.paper.datacomponent.DataComponentTypes.CUSTOM_MODEL_DATA).floats().get(0);
                check("a hit burst starts at its first frame and steps through them", first == 0F && later == 2F, first + " then " + later);
            }, 5L);
            Bukkit.getScheduler().runTaskLater(plugin, () -> check("a hit burst is gone after its last frame", bursts.get().isEmpty(),
                bursts.get().size() + " left"), 14L);
            check("effects in the air appear (a beam, a plasma bolt)", air.contains("air_beam") && air.stream().anyMatch(k -> k.startsWith("air_bolt_")),
                String.valueOf(air));
            check("wedge, lane, wave and splash markings appear", shapes.containsAll(List.of("floor_warning_wedge", "floor_warning_lane",
                "floor_wave", "floor_splash")), String.valueOf(shapes.stream().filter(k -> k.startsWith("floor_")).distinct().toList()));
        }
        check("summoning ritual spawned the Brood Mother", currentFight != null && !currentFight.bosses().isEmpty(), "no fight");
        if (currentFight != null) {
            check("boss is tagged as summoned", currentFight.bosses().stream().allMatch(Keys::isSummoned), "untagged");
            check("second summon on a busy circle is refused", rituals.begin(null, altar) == RitualService.Outcome.BUSY, "not refused");
        }
    }

    private void summonDirect(String bossId) {
        snapshotSlimes();
        BossSpec spec = rituals.spec(bossId).orElseThrow();
        currentFight = bosses.summon(bossId, spec, altar, null);
        check(ContentRegistrar.title(bossId) + " spawns", !currentFight.bosses().isEmpty(), "no entities");
    }

    private void checkFightRunning(String bossId) {
        check(ContentRegistrar.title(bossId) + " is not scaled up for a solo summon", Math.abs(currentFight.healthMultiplier() - 1.0) < 0.001,
            "multiplier " + currentFight.healthMultiplier());
        check(ContentRegistrar.title(bossId) + " runs 3s without errors", !currentFight.isOver(),
            "ended early: " + currentFight.result());
        String aura = switch (bossId) {   // Session O5 phase 3: the aura showing its state
            case "BLAZE_CHOIR" -> "aura_flame";
            case "HOLLOW_WARLORD" -> "aura_soul_halo";
            case "HEARTWOOD_HORROR" -> "aura_roots";
            default -> null;
        };
        if (aura != null && io.github.amitelia.occultech.boss.AirEffects.enabled()) {
            org.bukkit.Location near = currentFight.bosses().isEmpty() ? altar.getLocation() : currentFight.bosses().get(0).getLocation();
            List<String> shown = near.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, near, 12).stream()
                .map(d -> d.getItemStack().getItemMeta() == null || !d.getItemStack().getItemMeta().hasItemModel() ? "?" + d.getItemStack().getType()
                    : d.getItemStack().getItemMeta().getItemModel().getKey()).toList();
            check(ContentRegistrar.title(bossId) + " wears its aura (" + aura + ")", shown.contains(aura), String.valueOf(shown));
        }
    }

    private void killAllButOneSinger() {
        if (currentFight != null) {
            List<LivingEntity> singers = List.copyOf(currentFight.bosses());
            for (int i = 1; i < singers.size(); i++) {
                singers.get(i).setHealth(0);
            }
        }
    }

    private void lastSingerBare() {
        LivingEntity last = currentFight == null || currentFight.bosses().isEmpty() ? null : currentFight.bosses().get(0);
        check("the Blaze Choir's last singer is never shielded", last != null && currentFight.bosses().size() == 1 && !last.isGlowing(),
            last == null ? "no singer" : currentFight.bosses().size() + " singers, glowing " + last.isGlowing());
    }

    private void killCurrentFight() {
        if (currentFight != null) {
            // copy: each death removes the boss from the fight's live list
            for (LivingEntity boss : List.copyOf(currentFight.bosses())) {
                boss.setHealth(0);
            }
        }
    }

    private void checkFightEndedCleanly(String name) {
        if (currentFight == null) {
            check(name + " fight existed", false, "no fight");
            return;
        }
        check(name + " ends in victory", currentFight.isOver() && currentFight.result() == BossFight.Result.VICTORY,
            String.valueOf(currentFight.result()));
        List<Entity> left = nearby().stream().filter(Keys::isSummoned).toList();
        check(name + " leaves no summoned entities", left.isEmpty(),
            left.size() + " left: " + left.stream().map(e -> e.getType() + (e.isDead() ? " (dead)" : "")).toList());
        List<Item> dropped = nearby().stream().filter(e -> e instanceof Item).map(e -> (Item) e).toList();
        check(name + " drops no vanilla loot", dropped.isEmpty(), dropped.size() + " items on the ground: "
            + dropped.stream().map(i -> i.getItemStack().getType() + "x" + i.getItemStack().getAmount()).distinct().limit(6).toList());
        // superflat worlds spawn wild slimes, so only count slimes that appeared during the fight
        long slimes = nearby().stream().filter(e -> e instanceof Slime && !slimesBefore.contains(e.getUniqueId()) && !Keys.isSummoned(e)).count();
        check(name + " leaves no split slimes", slimes == 0, slimes + " new slimes");
        nearby().stream().filter(e -> e instanceof Item).forEach(Entity::remove);
        currentFight = null;
    }

    private void lootKeptForAbsent() {
        check("a circle is free once its fight ends", !new io.github.amitelia.occultech.items.CircleGuard(rituals).isBound(altar), "still bound");
        java.util.UUID absent = java.util.UUID.randomUUID();
        bosses.reward(absent, "Test Boss", List.of("sf:" + ItemKeys.slimefunId("GRAVE_SALT") + ":2", "xp:5", "win:BROOD_MOTHER"));
        List<String> kept = bosses.pendingFor(absent);
        check("an absent fighter's reward is kept for their return", kept.contains("xp:5") && kept.size() == 4, String.valueOf(kept));
        bosses.discardPending(absent);
    }

    private void refundOnInterruption() {
        DebugWorld.setAltarCenter(altar, null);
        BossSpec spec = rituals.spec("GELATINOUS_SOVEREIGN").orElseThrow();
        BossFight fight = bosses.summon("GELATINOUS_SOVEREIGN", spec, altar, DebugWorld.item(CATALYST, 1));
        check("active-fight marker saved on the altar", BlockStorage.getLocationInfo(altar.getLocation(), ACTIVE_KEY) != null, "no marker");
        bosses.abort(fight, BossFight.Result.UNLOADED);
        check("interrupted gate fight refunds the catalyst", CATALYST.equals(idIn(RitualAltar.CENTER_SLOT)), String.valueOf(idIn(RitualAltar.CENTER_SLOT)));
        check("marker cleared after the fight", BlockStorage.getLocationInfo(altar.getLocation(), ACTIVE_KEY) == null, "marker left");
    }

    // ------------------------------------------------------------------ Session P2: leaving and giving up

    /** The stand-in catalyst of the P2 fights: no other test uses it, so any refund of it would show. */
    private static final String MARKER = ItemKeys.slimefunId("BANISHING_SALT");
    private BossFight awayFight;
    private double awayHealth;
    private int awayElapsed;

    private void awayStart() {
        check("Banishing Salt is registered", SlimefunItem.getById(ItemKeys.slimefunId("BANISHING_SALT")) != null, "missing");
        DebugWorld.setAltarCenter(altar, null);
        bosses.setAwayRules(true);
        bosses.setAwaySeconds(6);
        awayFight = bosses.summon("BROOD_MOTHER", rituals.spec("BROOD_MOTHER").orElseThrow(), altar, DebugWorld.item(MARKER, 1));
        LivingEntity boss = awayFight.bosses().get(0);
        boss.setHealth(boss.getAttribute(org.bukkit.attribute.Attribute.MAX_HEALTH).getValue() / 2);
        awayHealth = boss.getHealth();
        awayElapsed = awayFight.elapsed();
    }

    private void awayRecovering() {
        LivingEntity boss = awayFight.bosses().isEmpty() ? null : awayFight.bosses().get(0);
        check("with everyone gone the fight pauses (its clock stops)", awayFight.elapsed() == awayElapsed && awayFight.awayTicksLeft() >= 0,
            awayElapsed + " -> " + awayFight.elapsed() + ", left " + awayFight.awayTicksLeft());
        check("a boss everyone walked away from recovers", boss != null && boss.getHealth() > awayHealth,
            awayHealth + " -> " + (boss == null ? "gone" : boss.getHealth()));
    }

    private void awayEnded() {
        check("the away timer ends the fight (abandoned)", awayFight.isOver() && awayFight.result() == BossFight.Result.ABANDONED,
            String.valueOf(awayFight.result()));
        check("an abandoned fight's catalyst is lost", !refunded(), "refunded");
        if (!awayFight.isOver()) {
            bosses.abort(awayFight);   // don't let a failed check leak its boss into the rest of the test
        }
        bosses.setAwaySeconds(180);
        bosses.setAwayRules(false);
    }

    /** Whether the marker catalyst came back: in the altar, or dropped by it. */
    private boolean refunded() {
        boolean dropped = altar.getWorld().getNearbyEntities(altar.getLocation().add(0.5, 1, 0.5), 3, 3, 3, e -> e instanceof Item item
            && SlimefunItem.getByItem(item.getItemStack()) != null && MARKER.equals(SlimefunItem.getByItem(item.getItemStack()).getId())).size() > 0;
        return dropped || MARKER.equals(idIn(RitualAltar.CENTER_SLOT));
    }

    private void banishEnds() {
        DebugWorld.setAltarCenter(altar, null);
        BossFight fight = bosses.summon("BROOD_MOTHER", rituals.spec("BROOD_MOTHER").orElseThrow(), altar, DebugWorld.item(MARKER, 1));
        check("Banishing Salt finds the fight nearby", bosses.nearestFight(altar.getLocation().add(40, 0, 0), 48) == fight
            && bosses.nearestFight(altar.getLocation().add(200, 0, 0), 48) == null, "not found / found too far");
        fight.banish(null);
        check("banishing ends the fight", fight.isOver() && fight.result() == BossFight.Result.BANISHED, String.valueOf(fight.result()));
        check("a banished fight's catalyst is lost", !refunded(), "refunded");
        List<Entity> left = nearby().stream().filter(Keys::isSummoned).toList();
        check("banishing leaves no summoned entities", left.isEmpty(), left.size() + " left");
    }

    // ------------------------------------------------------------------ Session P3: restarts and crashes

    private BossFight savedFight;
    private int savedElapsed;

    private void saveStart() {
        DebugWorld.setAltarCenter(altar, null);
        savedFight = bosses.summon("BROOD_MOTHER", rituals.spec("BROOD_MOTHER").orElseThrow(), altar, DebugWorld.item(MARKER, 1));
        LivingEntity boss = savedFight.bosses().get(0);
        boss.setHealth(boss.getAttribute(org.bukkit.attribute.Attribute.MAX_HEALTH).getValue() * 0.4);
    }

    private void fightSaved() {
        String state = BlockStorage.getLocationInfo(altar.getLocation(), "occultech_fight_state");
        check("a running fight saves itself every few seconds", state != null && state.contains("BROOD_MOTHER"), String.valueOf(state));
        savedElapsed = savedFight.elapsed();
        bosses.abort(savedFight, BossFight.Result.SHUTDOWN);   // a server stop
        check("a server stop keeps the fight (no refund)", !refunded()
            && BlockStorage.getLocationInfo(altar.getLocation(), "occultech_fight_state") != null, "refunded or state lost");
        rituals.recoverAltar(altar);   // the altar loads again
    }

    private void fightResumed() {
        BossFight back = bosses.fightAt(altar).orElse(null);
        check("the fight resumes when its altar loads", back != null && back != savedFight, "no fight");
        if (back != null) {
            check("the resumed boss keeps its health", Math.abs(back.healthFraction() - 0.4) < 0.05, String.valueOf(back.healthFraction()));
            check("the resumed fight keeps its clock", back.elapsed() >= savedElapsed, savedElapsed + " -> " + back.elapsed());
            bosses.abort(back);
            check("a fight over for good clears its saved state",
                BlockStorage.getLocationInfo(altar.getLocation(), "occultech_fight_state") == null, "state left");
        }
        check("resuming never refunds the catalyst", !refunded(), "refunded");
    }

    private void ritualCrash() {
        RitualRecipe recipe = rituals.recipes().stream().filter(r -> CATALYST.equals(r.outputId())).findFirst().orElseThrow();
        fill(recipe);
        int offered = bowlTotal();
        check("a ritual for the crash test starts", rituals.begin(null, altar) == RitualService.Outcome.STARTED && bowlsEmpty(), "did not start");
        rituals.crashSessionsForTest();   // the server dies mid-ritual
        rituals.recoverAltar(altar);      // ...and the altar loads again
        check("a crash mid-ritual gives every offering back", bowlTotal() == offered, offered + " offered, " + bowlTotal() + " back");
        check("a crash mid-ritual gives the center item back", recipe.center() == null || idIn(RitualAltar.CENTER_SLOT) != null
            || altarHolds(recipe.center()), "center item lost");
        rituals.recoverAltar(altar);      // a second load returns nothing more
        check("crash returns happen only once", bowlTotal() == offered, bowlTotal() + " after a second load");
    }

    private boolean altarHolds(String key) {
        BlockMenu menu = BlockStorage.getInventory(altar);
        ItemStack item = menu == null ? null : menu.getItemInSlot(RitualAltar.CENTER_SLOT);
        return item != null && !item.getType().isAir();
    }

    private int bowlTotal() {
        int total = 0;
        RitualService.CircleCheck check = rituals.checkCircle(altar).orElseThrow();
        for (int[] offset : check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation())) {
            BlockMenu menu = BlockStorage.getInventory(altar.getRelative(offset[0], 0, offset[1]));
            ItemStack item = menu == null ? null : menu.getItemInSlot(OfferingBowl.SLOT);
            total += item == null || item.getType().isAir() ? 0 : item.getAmount();
        }
        return total;
    }

    private void crashRecovery() {
        DebugWorld.setAltarCenter(altar, null);
        // simulate a crash: the marker survived but the fight is gone
        BlockStorage.addBlockInfo(altar, ACTIVE_KEY, CATALYST);
        plugin.rituals().recoverAltar(altar);
        long dropped = altar.getWorld().getNearbyEntities(altar.getLocation().add(0.5, 1, 0.5), 2, 2, 2, e -> e instanceof Item).size();
        check("crash recovery returns the catalyst", CATALYST.equals(idIn(RitualAltar.CENTER_SLOT)), idIn(RitualAltar.CENTER_SLOT)
            + " (menu " + (BlockStorage.getInventory(altar) == null ? "missing" : "there") + ", " + dropped + " dropped, fight here: "
            + bosses.fightAt(altar).isPresent() + ")");
        check("crash marker cleared", BlockStorage.getLocationInfo(altar.getLocation(), ACTIVE_KEY) == null, "marker left");
    }

    // ------------------------------------------------------------------ tier 1 steps

    private void buildUpgradeCircle() {
        World world = Bukkit.getWorlds().get(0);
        int x = world.getSpawnLocation().getBlockX() - 48;
        int z = world.getSpawnLocation().getBlockZ() + 64;
        chunk2 = world.getChunkAt(x >> 4, z >> 4);
        chunk2.addPluginChunkTicket(plugin);
        bound = world.getBlockAt(x, world.getHighestBlockYAt(x, z) + 1, z);
        DebugWorld.buildCircle(bound, 0, this::remember);
    }

    private void startAltarUpgrade() {
        RitualRecipe upgrade = rituals.recipes().stream().filter(RitualRecipe::inPlace).findFirst().orElse(null);
        check("altar-upgrade ritual registered", upgrade != null, "missing");
        if (upgrade == null) {
            return;
        }
        fillAt(bound, upgrade);
        check("upgrade ritual starts with an empty altar", rituals.begin(null, bound) == RitualService.Outcome.STARTED, "did not start");
    }

    private void altarUpgraded() {
        check("Initiate's Altar upgraded in place to a Bound Altar", Circles.BOUND_ALTAR.equals(BlockStorage.checkID(bound)),
            String.valueOf(BlockStorage.checkID(bound)));
    }

    private void buildBoundRing() {
        io.github.amitelia.occultech.ritual.CirclePattern pattern = Circles.forTier(1);
        for (int dz = -3; dz <= 3; dz++) {
            for (int dx = -3; dx <= 3; dx++) {
                if (Math.abs(dx) == 3 || Math.abs(dz) == 3) {
                    DebugWorld.placeSlimefun(bound.getRelative(dx, 0, dz), pattern.glyphAt(dx, dz), this::remember);
                }
            }
        }
    }

    private void boundCircleComplete() {
        Optional<RitualService.CircleCheck> check = rituals.checkCircle(bound);
        check("7x7 Bound circle detected", check.isPresent() && check.get().tier() == 1 && check.get().complete(),
            check.map(c -> "tier " + c.tier() + ", " + c.missing().size() + " missing").orElse("-"));
        check("Bound circle has 8 offering bowls", check.isPresent() && check.get().pattern().positionsOf(Circles.OFFERING_BOWL, 0).size() == 8, "wrong");
    }

    private void spiritEssenceRitual() {
        RitualRecipe recipe = rituals.recipes().stream().filter(r -> ItemKeys.slimefunId("SPIRIT_ESSENCE").equals(r.outputId())).findFirst().orElse(null);
        check("Spirit Essence ritual registered", recipe != null, "missing");
        if (recipe != null) {
            fillAt(bound, recipe);
            check("Spirit Essence ritual starts on the Bound circle", rituals.begin(null, bound) == RitualService.Outcome.STARTED, "did not start");
        }
    }

    private void spiritEssenceResult() {
        BlockMenu menu = BlockStorage.getInventory(bound);
        ItemStack out = menu == null ? null : menu.getItemInSlot(RitualAltar.CENTER_SLOT);
        SlimefunItem item = out == null || out.getType().isAir() ? null : SlimefunItem.getByItem(out);
        check("ritual produced 4 Spirit Essence", item != null && item.getId().equals(ItemKeys.slimefunId("SPIRIT_ESSENCE")) && out.getAmount() == 4,
            item == null ? "nothing" : item.getId() + " x" + out.getAmount());
        DebugWorld.setAltarCenter(bound, null);
    }

    private void summonTier1(String bossId) {
        snapshotSlimes();
        BossSpec spec = rituals.spec(bossId).orElseThrow();
        testAltar = bound;
        currentFight = bosses.summon(bossId, spec, bound, null);
        check(ContentRegistrar.title(bossId) + " spawns", !currentFight.bosses().isEmpty(), "no entities");
        if (List.of("ABYSSAL_WARDEN", "DROWNED_ELDER").contains(bossId) && !currentFight.bosses().isEmpty()) {
            // with nobody in the arena, gliders head back to the altar: start one 10 blocks out and see it move
            currentFight.bosses().get(0).teleport(currentFight.center().clone().add(10, 2, 0));
        }
    }

    /** Scripted movement really moves (needs mobs ticking without players: activation range 0 on the test server). */
    private void checkMovement(String bossId) {
        if (currentFight == null || currentFight.bosses().isEmpty()) {
            return;
        }
        org.bukkit.Location center = currentFight.center();
        LivingEntity first = currentFight.bosses().get(0);
        double flat = Math.hypot(first.getLocation().getX() - center.getX(), first.getLocation().getZ() - center.getZ());
        switch (bossId) {
            case "ABYSSAL_WARDEN", "DROWNED_ELDER" -> check(ContentRegistrar.title(bossId) + " glides back toward the altar",
                flat < 8, String.format("%.1f blocks out (started at 10)", flat));
            case "BLAZE_CHOIR" -> {
                boolean orbiting = currentFight.bosses().stream().allMatch(b -> {
                    double d = Math.hypot(b.getLocation().getX() - center.getX(), b.getLocation().getZ() - center.getZ());
                    return d > 3.5 && d < 6.5 && b.getLocation().getY() > center.getY() + 1;
                });
                check("Blaze Choir circles the altar in the air", orbiting, "positions off the orbit");
            }
            case "TIDEBREAKER" -> check("Tidebreaker stays on its nautilus", first.getVehicle() != null, "dismounted");
            case "DREAD_RIDERS" -> check("both Dread Riders ride their horses", currentFight.bosses().stream().allMatch(b -> b.getVehicle() != null),
                "a rider is on foot");
            case "GALLUS" -> check("Gallus starts with its knight in the saddle", !first.getPassengers().isEmpty(), "no rider");
            case "DOPPELGANGER" -> check("the Doppelganger is a player model", first instanceof org.bukkit.entity.Mannequin, String.valueOf(first.getType()));
            case "NIGHT_MATRIARCH" -> {
                org.bukkit.Location anchor = first instanceof org.bukkit.entity.Phantom phantom ? phantom.getAnchorLocation() : null;
                check("Night Matriarch circles above its own altar", anchor != null
                    && Math.hypot(anchor.getX() - center.getX(), anchor.getZ() - center.getZ()) < 1, String.valueOf(anchor));
            }
            default -> { }
        }
    }

    private void buildShrine() {
        testAltar = altar;
        shrine = altar.getRelative(12, 0, 0);
        // the shrine may sit in the next chunk: keep it loaded (nobody is online during the test)
        chunk3 = shrine.getChunk();
        chunk3.addPluginChunkTicket(plugin);
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                Block soil = shrine.getRelative(dx, -1, dz);
                remember(soil);
                soil.setType(Material.SOUL_SAND, false);
                Block above = shrine.getRelative(dx, 0, dz);
                remember(above);
                above.setType(Material.AIR, false);
            }
        }
        DebugWorld.placeSlimefun(shrine, ItemKeys.slimefunId("SERVITOR_SHRINE"), this::remember);
        BlockStorage.addBlockInfo(shrine, "occultech_owner", new java.util.UUID(0, 0).toString());
        wart = shrine.getRelative(2, 0, 0);
        wart.setType(Material.NETHER_WART, false);
        org.bukkit.block.data.Ageable age = (org.bukkit.block.data.Ageable) wart.getBlockData();
        age.setAge(age.getMaximumAge());
        wart.setBlockData(age, false);
    }

    private void startHarvest() {
        setContract("HARVEST_CONTRACT");
    }

    private void harvested() {
        org.bukkit.block.data.Ageable age = wart.getBlockData() instanceof org.bukkit.block.data.Ageable a ? a : null;
        check("Harvest contract replants the wart", wart.getType() == Material.NETHER_WART && age != null && age.getAge() < age.getMaximumAge(),
            wart.getType() + " age " + (age == null ? "-" : age.getAge()));
        check("Harvest contract stores the crop", storeCount(Material.NETHER_WART) > 0, "store empty");
    }

    private void startGather() {
        // clear stray items (e.g. left by an earlier interrupted run) so we measure only our drop
        shrine.getWorld().getNearbyEntities(shrine.getLocation(), 8, 4, 8, e -> e instanceof org.bukkit.entity.Item).forEach(Entity::remove);
        diamondsBefore = storeCount(Material.DIAMOND);
        setContract("GATHER_CONTRACT");
        testDrop = shrine.getWorld().dropItem(shrine.getLocation().add(2.5, 0.5, 1.5), new ItemStack(Material.DIAMOND, 3));
        testDrop.setPickupDelay(0);
    }

    private void gathered() {
        int gained = storeCount(Material.DIAMOND) - diamondsBefore;
        check("Gather contract collects exactly the dropped items", gained == 3, gained + " diamonds gained");
        check("gathered item entity is gone", !testDrop.isValid(), "still on the ground");
    }

    private void startWard() {
        setContract("WARD_CONTRACT");
    }

    private org.bukkit.entity.ItemDisplay strayOrb;

    private void warded() {
        // a spirit stranded in a chunk that stopped ticking (Session P1): the shrine must sweep it, not keep it
        strayOrb = shrine.getWorld().spawn(shrine.getLocation().add(3.5, 1.6, 0.5), org.bukkit.entity.ItemDisplay.class, d -> {
            d.setPersistent(false);
            d.getPersistentDataContainer().set(Keys.SPIRIT_OF, org.bukkit.persistence.PersistentDataType.STRING,
                shrine.getWorld().getName() + "," + shrine.getX() + "," + shrine.getY() + "," + shrine.getZ());
        });
        check("Ward contract protects its area", plugin.servitors().isWarded(shrine.getLocation().add(5, 0, 5)), "not warded");
        check("Ward contract covers 24 blocks out", plugin.servitors().isWarded(shrine.getLocation().add(20, 0, 0)), "not warded at 20");
        check("Ward contract doesn't reach far", !plugin.servitors().isWarded(shrine.getLocation().add(40, 0, 0)), "warded too far");
    }

    private void strayOrbsSwept() {
        check("a stray Servitor orb is swept away", !strayOrb.isValid(), "still there");
        long orbs = shrine.getWorld().getNearbyEntities(shrine.getLocation().add(0.5, 1, 0.5), 30, 30, 30,
            e -> e.getPersistentDataContainer().has(Keys.SPIRIT_OF)).size();
        check("the Ward shrine has exactly one orb", orbs == 1, orbs + " orbs");
    }

    private void scryingMirror() {
        Block mirror = altar.getRelative(-6, 0, 0);
        DebugWorld.placeSlimefun(mirror, ItemKeys.slimefunId("SCRYING_MIRROR"), this::remember);
        BlockStorage.addBlockInfo(mirror, "occultech_link", altar.getWorld().getName() + ";" + altar.getX() + ";" + altar.getY() + ";" + altar.getZ());
        String status = io.github.amitelia.occultech.items.ScryingMirrorAccess.status(rituals, mirror);
        check("Scrying Mirror reads its linked circle", status.contains("Circle complete"), ChatColor.stripColor(status));
    }

    // ---- more contracts

    private void clearStore() {
        BlockMenu menu = BlockStorage.getInventory(shrine);
        if (menu != null) {
            for (int slot : io.github.amitelia.occultech.items.ServitorShrine.STORE) {
                menu.replaceExistingItem(slot, null);
            }
        }
    }

    private void supply(Material type, int amount) {
        BlockMenu menu = BlockStorage.getInventory(shrine);
        if (menu != null) {
            menu.pushItem(new ItemStack(type, amount), io.github.amitelia.occultech.items.ServitorShrine.STORE);
        }
    }

    private void startBrewer() {
        clearStore();
        stand = shrine.getRelative(-2, 0, 0);
        remember(stand);
        stand.setType(Material.BREWING_STAND, false);
        if (stand.getState() instanceof org.bukkit.block.BrewingStand bs) {
            ItemStack water = new ItemStack(Material.POTION);
            org.bukkit.inventory.meta.PotionMeta meta = (org.bukkit.inventory.meta.PotionMeta) water.getItemMeta();
            meta.setBasePotionType(org.bukkit.potion.PotionType.WATER);
            water.setItemMeta(meta);
            bs.getInventory().setItem(0, water);
        }
        supply(Material.NETHER_WART, 4);
        supply(Material.BLAZE_POWDER, 2);
        setContract("BREWER_CONTRACT");
    }

    private void brewed() {
        org.bukkit.block.BrewingStand bs = (org.bukkit.block.BrewingStand) stand.getState();
        ItemStack ingredient = bs.getInventory().getIngredient();
        boolean fueled = bs.getFuelLevel() > 0 || (bs.getInventory().getFuel() != null && bs.getInventory().getFuel().getType() == Material.BLAZE_POWDER);
        check("Brewer's Aid fuels the brewing stand", fueled, "no fuel");
        boolean wartIn = (ingredient != null && ingredient.getType() == Material.NETHER_WART) || bs.getBrewingTime() > 0 || storeCount(Material.NETHER_WART) < 4;
        check("Brewer's Aid adds nether wart to water bottles", wartIn, "no wart added");
        stand.setType(Material.AIR, false);
    }

    private void startShepherd() {
        clearStore();
        sheep = shrine.getWorld().spawn(shrine.getLocation().add(2.5, 0, 2.5), org.bukkit.entity.Sheep.class, s -> s.setColor(org.bukkit.DyeColor.PURPLE));
        setContract("SHEPHERD_CONTRACT");
    }

    private void sheared() {
        check("Shepherd shears the sheep", sheep.isSheared(), "not sheared");
        check("Shepherd stores wool of the sheep's color", storeCount(Material.PURPLE_WOOL) > 0, "no purple wool");
        sheep.remove();
    }

    private void startBeekeeper() {
        clearStore();
        hive = shrine.getRelative(0, 0, 2);
        remember(hive);
        hive.setType(Material.BEEHIVE, false);
        org.bukkit.block.data.type.Beehive data = (org.bukkit.block.data.type.Beehive) hive.getBlockData();
        data.setHoneyLevel(data.getMaximumHoneyLevel());
        hive.setBlockData(data, false);
        setContract("BEEKEEPER_CONTRACT");
    }

    private void beesKept() {
        org.bukkit.block.data.type.Beehive data = (org.bukkit.block.data.type.Beehive) hive.getBlockData();
        check("Beekeeper empties the full hive", data.getHoneyLevel() == 0, "honey level " + data.getHoneyLevel());
        check("Beekeeper stores honeycomb", storeCount(Material.HONEYCOMB) == 3, storeCount(Material.HONEYCOMB) + " honeycomb");
        hive.setType(Material.AIR, false);
    }

    private void speedRules() {
        var servitors = plugin.servitors();
        BlockStorage.addBlockInfo(shrine, "occultech_empowered_until", null);
        check("base speed: one action every 2s", servitors.intervalMs(shrine) == 2000, servitors.intervalMs(shrine) + "ms");
        servitors.empower(shrine);
        check("empowered: double speed", servitors.intervalMs(shrine) == 1000, servitors.intervalMs(shrine) + "ms");
        check("empowering banks one hour", Math.abs(servitors.empoweredFor(shrine) - 3_600_000L) < 5000, servitors.empoweredFor(shrine) + "ms");

        idolA = shrine.getRelative(3, 0, 3);
        idolB = shrine.getRelative(-3, 0, 3);
        DebugWorld.placeSlimefun(idolA, ItemKeys.slimefunId("FRENZY_IDOL"), this::remember);
        DebugWorld.placeSlimefun(idolB, ItemKeys.slimefunId("FRENZY_IDOL"), this::remember);
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            check("empowered + Frenzy Idol: x3 speed", servitors.intervalMs(shrine) == 666, servitors.intervalMs(shrine) + "ms");
            check("two Frenzy Idols don't stack", servitors.intervalMs(shrine) == 666, servitors.intervalMs(shrine) + "ms");
            BlockStorage.addBlockInfo(shrine, "occultech_empowered_until", null);
            check("idol alone: x1.5 speed", servitors.intervalMs(shrine) == 1333, servitors.intervalMs(shrine) + "ms");
            for (Block idol : List.of(idolA, idolB)) {
                plugin.rituals().holograms().clear(idol);
                BlockStorage.clearBlockInfo(idol);
                idol.setType(Material.AIR, false);
            }
        }, 40L);
    }

    private void placementCap() {
        var servitors = plugin.servitors();
        List<org.bukkit.Location> fakes = List.of(shrine.getLocation().add(4, 0, 0), shrine.getLocation().add(0, 0, 4), shrine.getLocation().add(-4, 0, 0));
        fakes.forEach(servitors::registerForTest);
        org.bukkit.Location here = shrine.getLocation().add(2, 0, 2);
        check("4 shrines within 12 blocks block a 5th", !servitors.canPlace(here), servitors.nearbyShrines(here) + " nearby");
        check("a shrine 30 blocks away is still allowed", servitors.canPlace(shrine.getLocation().add(30, 0, 0)), "blocked");
        fakes.forEach(servitors::unregisterForTest);
        check("with 3 fakes gone, placing is allowed again", servitors.canPlace(here), servitors.nearbyShrines(here) + " nearby");
    }

    private void startAcolyte() {
        // the acolyte needs an altar within 8 blocks: use the test circle, which sits 12 away, via a second shrine
        acolyte = altar.getRelative(6, 0, 0);
        remember(acolyte.getRelative(0, -1, 0));
        DebugWorld.placeSlimefun(acolyte, ItemKeys.slimefunId("SERVITOR_SHRINE"), this::remember);
        BlockStorage.addBlockInfo(acolyte, "occultech_owner", new java.util.UUID(0, 0).toString());
        RitualRecipe brood = rituals.recipes().stream().filter(r -> "BROOD_MOTHER".equals(r.bossId())).findFirst().orElseThrow();
        acolyteRecipe = brood;
        rituals.rememberRitual(altar, brood);
        RitualService.CircleCheck check = rituals.checkCircle(altar).orElseThrow();
        check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation()).forEach(o -> DebugWorld.setBowl(altar.getRelative(o[0], 0, o[1]), null));
        DebugWorld.setAltarCenter(altar, null);
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            BlockMenu menu = BlockStorage.getInventory(acolyte);
            if (menu == null) {
                return;
            }
            for (Map.Entry<String, Integer> offering : brood.offerings().entrySet()) {
                ItemStack stock = DebugWorld.item(offering.getKey(), offering.getValue() * 2);
                if (stock != null) {
                    menu.pushItem(stock, io.github.amitelia.occultech.items.ServitorShrine.STORE);
                }
            }
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ServitorShrine.CONTRACT_SLOT,
                SlimefunItem.getById(ItemKeys.slimefunId("ACOLYTE_CONTRACT")).getItem().clone());
        }, 5L);
    }

    private void acolyteRestocked() {
        RitualService.CircleCheck check = rituals.checkCircle(altar).orElseThrow();
        java.util.Map<String, Integer> inBowls = new java.util.HashMap<>();
        for (int[] o : check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation())) {
            BlockMenu menu = BlockStorage.getInventory(altar.getRelative(o[0], 0, o[1]));
            ItemStack item = menu == null ? null : menu.getItemInSlot(io.github.amitelia.occultech.items.OfferingBowl.SLOT);
            if (item != null && !item.getType().isAir()) {
                SlimefunItem sf = SlimefunItem.getByItem(item);
                inBowls.merge(sf != null ? sf.getId() : ItemKeys.vanilla(item.getType().name()), item.getAmount(), Integer::sum);
            }
        }
        check("Acolyte restocks every offering of the last ritual", inBowls.equals(acolyteRecipe.offerings()), inBowls.toString());
        check("Acolyte never starts the ritual", rituals.bosses().fightAt(altar).isEmpty() && !rituals.isLocked(altar.getLocation()), "started");
        plugin.rituals().holograms().clear(acolyte);
        plugin.servitors().unregisterForTest(acolyte.getLocation());
        BlockMenu menu = BlockStorage.getInventory(acolyte);
        if (menu != null) {
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ServitorShrine.CONTRACT_SLOT, null);
            for (int slot : io.github.amitelia.occultech.items.ServitorShrine.STORE) {
                menu.replaceExistingItem(slot, null);
            }
        }
        BlockStorage.clearBlockInfo(acolyte);
        acolyte.setType(Material.AIR, false);
        check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation()).forEach(o -> DebugWorld.setBowl(altar.getRelative(o[0], 0, o[1]), null));
    }

    private void contractSwap() {
        clearStore();
        setContract("WARD_CONTRACT");
    }

    private void contractSwapped() {
        check("swapping the contract changes the job (now Ward)", plugin.servitors().isWarded(shrine.getLocation().add(1, 0, 1)), "not warding");
        setContract("HARVEST_CONTRACT");
    }

    // ---- repair ritual

    private void startRepair() {
        rituals.checkCircle(altar).ifPresent(check ->
            check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation()).forEach(o -> DebugWorld.setBowl(altar.getRelative(o[0], 0, o[1]), null)));
        ItemStack bow = SlimefunItem.getById(ItemKeys.slimefunId("QUILLSHOT_BOW")).getItem().clone();
        org.bukkit.inventory.meta.Damageable meta = (org.bukkit.inventory.meta.Damageable) bow.getItemMeta();
        meta.setDamage(300);
        bow.setItemMeta(meta);
        DebugWorld.setAltarCenter(altar, bow);
        RitualService.CircleCheck check = rituals.checkCircle(altar).orElseThrow();
        int[] first = check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation()).get(0);
        DebugWorld.setBowl(altar.getRelative(first[0], 0, first[1]), DebugWorld.item(ItemKeys.slimefunId("FLETCHERS_QUILL"), 5));
        check("repair ritual starts (damaged bow + Fletcher's Quills)", rituals.begin(null, altar) == RitualService.Outcome.STARTED, "did not start");
        BlockMenu bowl = BlockStorage.getInventory(altar.getRelative(first[0], 0, first[1]));
        ItemStack left = bowl == null ? null : bowl.getItemInSlot(io.github.amitelia.occultech.items.OfferingBowl.SLOT);
        check("repair uses only the quills it needs (2 of 5)", left != null && left.getAmount() == 3, left == null ? "none left" : left.getAmount() + " left");
        repairBowl = first;
    }

    private void repaired() {
        BlockMenu menu = BlockStorage.getInventory(altar);
        ItemStack bow = menu == null ? null : menu.getItemInSlot(RitualAltar.CENTER_SLOT);
        int damage = bow != null && bow.getItemMeta() instanceof org.bukkit.inventory.meta.Damageable d ? d.getDamage() : -1;
        check("repair ritual restores the bow to full", damage == 0, "damage " + damage);
        DebugWorld.setAltarCenter(altar, null);
        DebugWorld.setBowl(altar.getRelative(repairBowl[0], 0, repairBowl[1]), null);
    }

    // ---- necromancy

    private void raiseMinions() {
        org.bukkit.Location at = altar.getLocation().add(-6, 0, 6);
        minionOwner = java.util.UUID.randomUUID();
        minionList = plugin.minions().raiseForTest(minionOwner, at, 2, 30);
        victim = altar.getWorld().spawn(at.clone().add(6, 0, 0), org.bukkit.entity.Cow.class);
        check("minions obey an attack order on any mob (a cow)", plugin.minions().command(minionOwner, victim), "order refused");
    }

    private void minionsAttack() {
        boolean targeting = minionList.stream().allMatch(m -> !m.isValid() || m.getTarget() == victim || victim.isDead());
        check("minions keep the ordered target", targeting, "targets: " + minionList.stream().map(m -> String.valueOf(m.getTarget())).toList());
        double max = victim.getAttribute(org.bukkit.attribute.Attribute.MAX_HEALTH).getValue();
        boolean playerNear = !victim.getWorld().getNearbyEntities(victim.getLocation(), 32, 32, 32, e -> e instanceof org.bukkit.entity.Player).isEmpty();
        if (playerNear) {
            check("minions actually hurt the target", victim.isDead() || victim.getHealth() < max, victim.getHealth() + "/" + max);
        } else {
            // Paper freezes mob AI far from players (entity activation range), so the bows only fire with someone nearby
            say("&e  SKIP &7minions actually hurt the target &8(needs a player within 32 blocks for mob AI)");
        }
        plugin.minions().dismissAll(minionOwner);
        victim.remove();
        check("dismissed minions are gone", minionList.stream().noneMatch(org.bukkit.entity.Entity::isValid), "still there");
    }

    // ---- tier 2

    private Block eye;
    private Block trophyBoard;
    private Chunk chunk4;
    private org.bukkit.entity.Husk husk;

    private void tier2Items() {
        ItemStack chest = SlimefunItem.getById(ItemKeys.slimefunId("ABYSSAL_CHESTPLATE")).getItem();
        check("Abyssal Chestplate has Thorns V", chest.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.THORNS) == 5,
            "thorns " + chest.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.THORNS));
        ItemStack breath = SlimefunItem.getById(ItemKeys.slimefunId("WYRMBREATH")).getItem();
        check("Wyrmbreath is holdable (consumable data)", breath.hasData(io.papermc.paper.datacomponent.DataComponentTypes.CONSUMABLE), "no data");
        for (String machine : List.of("OCCULT_FORGE", "SOUL_CONDENSER")) {
            SlimefunItem item = SlimefunItem.getById(ItemKeys.slimefunId(machine));
            int recipes = item instanceof io.github.amitelia.occultech.items.OccultMachine m ? m.getMachineRecipes().size() : -1;
            check(ContentRegistrar.title(machine) + " has its recipes", recipes > 0, recipes + " recipes");
        }
    }

    private void startAbyssalUpgrade() {
        String abyssal = ItemKeys.slimefunId("ABYSSAL_ALTAR");
        RitualRecipe upgrade = rituals.recipes().stream().filter(r -> r.inPlace() && abyssal.equals(r.outputId())).findFirst().orElse(null);
        check("Abyssal Altar upgrade ritual registered", upgrade != null, "missing");
        if (upgrade == null) {
            return;
        }
        testAltar = bound;
        fillAt(bound, upgrade);
        check("Abyssal upgrade starts on the Bound circle", rituals.begin(null, bound) == RitualService.Outcome.STARTED, "did not start");
    }

    private void abyssalUpgraded() {
        check("Bound Altar upgraded in place to an Abyssal Altar", ItemKeys.slimefunId("ABYSSAL_ALTAR").equals(BlockStorage.checkID(bound)),
            String.valueOf(BlockStorage.checkID(bound)));
    }

    /** Removes Bound-circle pieces that the 9x9 pattern replaces with something else. */
    private void clearForAbyssalRing() {
        io.github.amitelia.occultech.ritual.CirclePattern pattern = Circles.forTier(2);
        for (int dz = -4; dz <= 4; dz++) {
            for (int dx = -4; dx <= 4; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                Block block = bound.getRelative(dx, 0, dz);
                String id = BlockStorage.checkID(block);
                if ((dx == 0 && dz == 0) || glyph == null || glyph.equals(id) || id == null) {
                    continue;
                }
                remember(block);
                DebugWorld.emptyMenu(block);
                BlockStorage.clearBlockInfo(block);
                block.setType(Material.AIR, false);
            }
        }
    }

    private void buildAbyssalRing() {
        io.github.amitelia.occultech.ritual.CirclePattern pattern = Circles.forTier(2);
        for (int dz = -4; dz <= 4; dz++) {
            for (int dx = -4; dx <= 4; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                Block block = bound.getRelative(dx, 0, dz);
                if ((dx == 0 && dz == 0) || glyph == null || glyph.equals(BlockStorage.checkID(block))) {
                    continue;
                }
                DebugWorld.placeSlimefun(block, glyph, this::remember);
            }
        }
    }

    private void abyssalCircleComplete() {
        Optional<RitualService.CircleCheck> check = rituals.checkCircle(bound);
        check("9x9 Abyssal circle detected", check.isPresent() && check.get().tier() == 2 && check.get().complete(),
            check.map(c -> "tier " + c.tier() + ", " + c.missing().size() + " missing").orElse("-"));
    }

    private void startHelmRitual() {
        String helm = ItemKeys.slimefunId("ABYSSAL_HELMET");
        RitualRecipe recipe = rituals.recipes().stream().filter(r -> helm.equals(r.outputId())).findFirst().orElse(null);
        check("Abyssal Helm ritual registered", recipe != null, "missing");
        if (recipe == null) {
            return;
        }
        fillAt(bound, recipe);
        ItemStack enchanted = new ItemStack(Material.NETHERITE_HELMET);
        enchanted.addEnchantment(org.bukkit.enchantments.Enchantment.PROTECTION, 4);
        DebugWorld.setAltarCenter(bound, enchanted);
        check("Abyssal Helm ritual starts with an enchanted netherite helmet", rituals.begin(null, bound) == RitualService.Outcome.STARTED, "did not start");
    }

    private void helmResult() {
        BlockMenu menu = BlockStorage.getInventory(bound);
        ItemStack out = menu == null ? null : menu.getItemInSlot(RitualAltar.CENTER_SLOT);
        SlimefunItem item = out == null || out.getType().isAir() ? null : SlimefunItem.getByItem(out);
        long dropped = bound.getWorld().getNearbyEntities(bound.getLocation().add(0.5, 1, 0.5), 3, 3, 3, e -> e instanceof Item).size();
        check("ritual produced the Abyssal Helm", item != null && item.getId().equals(ItemKeys.slimefunId("ABYSSAL_HELMET")),
            (item == null ? "nothing" : item.getId()) + " (slot: " + (menu == null ? "no menu" : out == null ? "empty" : out.getType())
                + ", ritual still running: " + rituals.isLocked(bound.getLocation()) + ", " + dropped + " dropped)");
        check("the helmet's enchantments carry over (Protection IV)", out != null && out.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION) == 4,
            out == null ? "nothing" : out.getEnchantments().toString());
        DebugWorld.setAltarCenter(bound, null);
    }

    private void placeGuardianEye() {
        eye = bound.getRelative(-8, 0, 8);
        DebugWorld.placeSlimefun(eye, ItemKeys.slimefunId("GUARDIAN_EYE"), this::remember);
        // nobody is online: keep the eye's chunk loaded so Slimefun ticks it
        chunk4 = eye.getChunk();
        chunk4.addPluginChunkTicket(plugin);
        husk = bound.getWorld().spawn(eye.getLocation().add(4.5, 0, 0.5), org.bukkit.entity.Husk.class, h -> h.setAI(false));
    }

    private void guardianEyeFired() {
        double max = husk.getAttribute(org.bukkit.attribute.Attribute.MAX_HEALTH).getValue();
        check("Guardian Eye beams a hostile mob", husk.isDead() || husk.getHealth() < max, husk.getHealth() + "/" + max);
        if (plugin.skins().isSkinned(ItemKeys.slimefunId("GUARDIAN_EYE"))
            && SlimefunItem.getById(ItemKeys.slimefunId("GUARDIAN_EYE")) instanceof io.github.amitelia.occultech.items.GuardianEye guardian) {
            org.bukkit.entity.ItemDisplay orb = guardian.orb(eye);
            check("the Guardian Eye has its eye on top", orb != null && orb.isValid(), "no eye");
            if (orb != null) {
                // the eye's front (its model's north face, drawn facing +z) turned onto a gaze east and up
                io.github.amitelia.occultech.items.GuardianEye.look(orb, new org.bukkit.util.Vector(1, 1, 0));
                org.joml.Vector3f front = orb.getTransformation().getLeftRotation().transform(new org.joml.Vector3f(0, 0, 1));
                check("the eye turns to look along its gaze", Math.abs(front.x - 0.7071F) < 0.01F && Math.abs(front.y - 0.7071F) < 0.01F
                    && Math.abs(front.z) < 0.01F, String.valueOf(front));
            }
        }
        husk.remove();
        plugin.rituals().holograms().clear(eye);
    }

    private void tetherShrine() {
        BlockMenu menu = BlockStorage.getInventory(shrine);
        // an inferred menu size would stop at slot 17 and Slimefun would never save the store (items lost on reload)
        int size = menu == null ? -1 : menu.getPreset().getSize();
        check("shrine menu has an explicit 45-slot size (store is saved)", size == 45, "size " + size);
        if (menu != null) {
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ServitorShrine.UPGRADE_SLOT,
                SlimefunItem.getById(ItemKeys.slimefunId("ABYSSAL_TETHER")).getItem().clone());
        }
    }

    private void tethered() {
        int radius = plugin.servitors().radiusOf(shrine.getLocation());
        check("Abyssal Tether widens the Harvest radius 4 -> 7", radius == 7, "radius " + radius);
        BlockMenu menu = BlockStorage.getInventory(shrine);
        if (menu != null) {
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ServitorShrine.UPGRADE_SLOT, null);
        }
    }

    private Block prismatic;

    private void decorationPalette() {
        Block jar = bound.getRelative(-8, 0, -8);
        DebugWorld.placeSlimefun(jar, ItemKeys.slimefunId("WISP_JAR"), this::remember);
        var decorations = plugin.decorations();
        int before = decorations.paletteOf(jar);
        decorations.cyclePalette(jar, io.github.amitelia.occultech.items.DecorationService.Kind.WISP_JAR);
        check("right-click cycles a decoration's palette", decorations.paletteOf(jar) == (before + 1) % 4, before + " -> " + decorations.paletteOf(jar));

        Block coral = bound.getRelative(-8, 0, -6);
        DebugWorld.placeSlimefun(coral, ItemKeys.slimefunId("EVERLIVING_CORAL"), this::remember);
        decorations.cyclePalette(coral, io.github.amitelia.occultech.items.DecorationService.Kind.EVERLIVING_CORAL);
        check("Everliving Coral's palette swaps the coral type", coral.getType() == Material.BRAIN_CORAL, String.valueOf(coral.getType()));
        prismatic = bound.getRelative(-8, 0, -2);
        DebugWorld.placeSlimefun(prismatic, ItemKeys.slimefunId("PRISMATIC_NETHERRACK"), this::remember);
        remember(prismatic.getRelative(0, 1, 0));
        if (decorations.coloredFire()) {
            check("Prismatic Netherrack lights with its own fire (a light block, no vanilla fire)",
                decorations.lightPrismatic(prismatic) && prismatic.getRelative(0, 1, 0).getType() == Material.LIGHT,
                String.valueOf(prismatic.getRelative(0, 1, 0).getType()));
        }
        Block board = bound.getRelative(-8, 0, -4);
        DebugWorld.placeSlimefun(board, ItemKeys.slimefunId("TROPHY_BOARD"), this::remember);
        BlockStorage.addBlockInfo(board, "occultech_trophy", "ABYSSAL_WARDEN;3;Test");
        trophyBoard = board;
        plugin.decorations().setAlwaysVisible(true);
        for (String id : List.of("CHIMING_TILE", "MOONLIT_LILY", "WITCHCAP", "TIDAL_TILE", "PRISMATIC_NETHERRACK", "TROPHY_BOARD")) {
            check(ContentRegistrar.title(id) + " registered", SlimefunItem.getById(ItemKeys.slimefunId(id)) != null, "missing");
        }
    }

    private void trophyShown() {
        long models = trophyBoard.getWorld().getNearbyEntities(trophyBoard.getLocation().add(0.5, 1.5, 0.5), 1.5, 2, 1.5,
            e -> e instanceof org.bukkit.entity.Guardian && e.getPersistentDataContainer().has(Keys.HOLOGRAM)).size();
        check("Trophy Board shows a small model of the chosen boss", models == 1, models + " models");
        trophyBoard.getWorld().getNearbyEntities(trophyBoard.getLocation().add(0.5, 1.5, 0.5), 1.5, 2, 1.5,
            e -> e instanceof org.bukkit.entity.Guardian && e.getPersistentDataContainer().has(Keys.HOLOGRAM)).stream().findFirst()
            .ifPresent(statue -> {
                // a guardian is 0.85 across; with its spikes (x1.3) it should come out 0.75 blocks
                var scale = ((org.bukkit.entity.LivingEntity) statue).getAttribute(org.bukkit.attribute.Attribute.SCALE);
                double size = (scale == null ? 1 : scale.getValue()) * 0.85 * 1.3;
                check("the boss statue is the common statue size, standing on the pedestal's cushion",
                    Math.abs(size - 0.75) < 0.03 && Math.abs(statue.getLocation().getY() - (trophyBoard.getY() + 15 / 16.0)) < 0.02,
                    String.format("size %.2f (scale %s, box %.2f) at y %.2f", size, scale == null ? "-" : scale.getValue(),
                        Math.max(statue.getHeight(), statue.getWidth()), statue.getLocation().getY() - trophyBoard.getY()));
            });
        if (plugin.decorations().coloredFire()) {
            check("lit Prismatic Netherrack shows its coloured flames", plugin.decorations().partCount(prismatic) == 1,
                plugin.decorations().partCount(prismatic) + " parts");
            plugin.decorations().extinguishPrismatic(prismatic);
            check("its fire puts out (light and flames gone)", prismatic.getRelative(0, 1, 0).getType().isAir()
                && plugin.decorations().partCount(prismatic) == 0, String.valueOf(prismatic.getRelative(0, 1, 0).getType()));
        }
        plugin.decorations().remove(trophyBoard);
        plugin.decorations().setAlwaysVisible(false);
    }

    // ---- tier 3

    private Block nexus;

    private void tier3Items() {
        ItemStack crown = SlimefunItem.getById(ItemKeys.slimefunId("HOLLOW_HELMET")).getItem();
        if (plugin.resourcePack().hasEquipment("hollow")) {
            var worn = crown.getData(io.papermc.paper.datacomponent.DataComponentTypes.EQUIPPABLE);
            check("the Hollow Crown is worn as its 3D model (an equippable head item with no armor asset)",
                worn != null && worn.assetId() == null && worn.slot() == org.bukkit.inventory.EquipmentSlot.HEAD,
                worn == null ? "no equippable" : worn.slot() + " " + worn.assetId());
            var cuirass = SlimefunItem.getById(ItemKeys.slimefunId("HOLLOW_CHESTPLATE")).getItem()
                .getData(io.papermc.paper.datacomponent.DataComponentTypes.EQUIPPABLE);
            check("the Hollow Cuirass is worn in Occultech's look (equipment occultech:hollow)",
                cuirass != null && cuirass.assetId() != null && cuirass.assetId().asString().equals("occultech:hollow"),
                cuirass == null ? "no equippable" : String.valueOf(cuirass.assetId()));
        }
        check("Hollow Crown has Protection X", crown.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION) == 10,
            "protection " + crown.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.PROTECTION));
        SlimefunItem assembler = SlimefunItem.getById(ItemKeys.slimefunId("HOLLOW_ASSEMBLER"));
        int recipes = assembler instanceof io.github.amitelia.occultech.items.OccultMachine m ? m.getMachineRecipes().size() : -1;
        check("Hollow Assembler has its recipes", recipes >= 10, recipes + " recipes");
        int slots = assembler instanceof io.github.amitelia.occultech.items.OccultMachine m ? m.getInputSlots().length : -1;
        check("Hollow Assembler has 9 input slots", slots == 9, slots + " slots");
        SlimefunItem forge = SlimefunItem.getById(ItemKeys.slimefunId("OCCULT_FORGE"));
        int forgeSlots = forge instanceof io.github.amitelia.occultech.items.OccultMachine m ? m.getInputSlots().length : -1;
        check("Occult Forge keeps 4 input slots", forgeSlots == 4, forgeSlots + " slots");
        ItemStack censer = SlimefunItem.getById(ItemKeys.slimefunId("SOULFIRE_CENSER")).getItem();
        check("Soulfire Censer is holdable", censer.hasData(io.papermc.paper.datacomponent.DataComponentTypes.CONSUMABLE), "no data");
        for (String id : List.of("HOLLOW_HALO", "WISHBONE_TALISMAN", "AURA_TALISMAN", "GALLUS_EGG", "STORMSTRING_BOW", "DREADLANCE",
            "SERVITOR_NEXUS", "WATCHFUL_EYEBLOSSOM", "RESIN_TILE", "HOLLOW_GLYPH")) {
            check(ContentRegistrar.title(id) + " registered", SlimefunItem.getById(ItemKeys.slimefunId(id)) != null, "missing");
        }
        check("Abyssal and Hollow Glyphs are placeable",
            !(SlimefunItem.getById(ItemKeys.slimefunId("ABYSSAL_GLYPH")) instanceof io.github.thebusybiscuit.slimefun4.core.attributes.NotPlaceable)
                && !(SlimefunItem.getById(ItemKeys.slimefunId("HOLLOW_GLYPH")) instanceof io.github.thebusybiscuit.slimefun4.core.attributes.NotPlaceable),
            "not placeable");
    }

    private void startHollowUpgrade() {
        String hollow = ItemKeys.slimefunId("HOLLOW_ALTAR");
        RitualRecipe upgrade = rituals.recipes().stream().filter(r -> r.inPlace() && hollow.equals(r.outputId())).findFirst().orElse(null);
        check("Hollow Altar upgrade ritual registered", upgrade != null, "missing");
        if (upgrade == null) {
            return;
        }
        testAltar = bound;
        fillAt(bound, upgrade);
        check("Hollow upgrade starts on the Abyssal circle", rituals.begin(null, bound) == RitualService.Outcome.STARTED, "did not start");
    }

    private void hollowUpgraded() {
        check("Abyssal Altar upgraded in place to a Hollow Altar", ItemKeys.slimefunId("HOLLOW_ALTAR").equals(BlockStorage.checkID(bound)),
            String.valueOf(BlockStorage.checkID(bound)));
    }

    private void clearForHollowRing() {
        io.github.amitelia.occultech.ritual.CirclePattern pattern = Circles.forTier(3);
        for (int dz = -5; dz <= 5; dz++) {
            for (int dx = -5; dx <= 5; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                Block block = bound.getRelative(dx, 0, dz);
                String id = BlockStorage.checkID(block);
                if ((dx == 0 && dz == 0) || glyph == null || glyph.equals(id) || id == null) {
                    continue;
                }
                remember(block);
                DebugWorld.emptyMenu(block);
                BlockStorage.clearBlockInfo(block);
                block.setType(Material.AIR, false);
            }
        }
    }

    private void buildHollowRing() {
        io.github.amitelia.occultech.ritual.CirclePattern pattern = Circles.forTier(3);
        for (int dz = -5; dz <= 5; dz++) {
            for (int dx = -5; dx <= 5; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                Block block = bound.getRelative(dx, 0, dz);
                if ((dx == 0 && dz == 0) || glyph == null || glyph.equals(BlockStorage.checkID(block))) {
                    continue;
                }
                DebugWorld.placeSlimefun(block, glyph, this::remember);
            }
        }
    }

    private void hollowCircleComplete() {
        Optional<RitualService.CircleCheck> check = rituals.checkCircle(bound);
        check("11x11 Hollow circle detected", check.isPresent() && check.get().tier() == 3 && check.get().complete(),
            check.map(c -> "tier " + c.tier() + ", " + c.missing().size() + " missing").orElse("-"));
        check("Hollow circle has 12 offering bowls", check.isPresent() && check.get().pattern().positionsOf(Circles.OFFERING_BOWL, 0).size() == 12, "wrong");
    }

    private void setGallusHealth(double fraction) {
        if (currentFight != null && !currentFight.bosses().isEmpty()) {
            LivingEntity gallus = currentFight.bosses().get(0);
            gallus.setHealth(gallus.getAttribute(org.bukkit.attribute.Attribute.MAX_HEALTH).getValue() * fraction);
        }
    }

    private void gallusUnhorsed() {
        LivingEntity gallus = currentFight == null || currentFight.bosses().isEmpty() ? null : currentFight.bosses().get(0);
        check("Gallus throws its rider below two thirds", gallus != null && gallus.getPassengers().isEmpty(), "still mounted");
    }

    private void gallusHollowed() {
        LivingEntity gallus = currentFight == null || currentFight.bosses().isEmpty() ? null : currentFight.bosses().get(0);
        check("Gallus takes to the air in the Hollowing", gallus != null && !gallus.hasGravity(), "still grounded");
    }

    private Block arcane;
    private io.github.amitelia.occultech.items.ArcaneAltar.ArcaneRecipe arcaneRecipe;

    private void buildArcaneAltar() {
        io.github.amitelia.occultech.items.ArcaneAltar altarItem = plugin.registrar().arcaneAltar();
        check("Arcane Altar registered", altarItem != null, "missing");
        if (altarItem == null) {
            return;
        }
        long imported = altarItem.recipes().stream().filter(r -> !r.source().equals("Occultech")).count();
        check("Arcane Altar imported Slimefun's Ancient Altar recipes", imported >= 10, imported + " imported");
        arcane = altar.getRelative(-10, 0, -10);
        DebugWorld.placeSlimefun(arcane, ItemKeys.slimefunId("ARCANE_ALTAR"), this::remember);
        for (int[] o : new int[][] { { 2, 0 }, { 2, 2 }, { 0, 2 }, { -2, 2 }, { -2, 0 }, { -2, -2 }, { 0, -2 }, { 2, -2 } }) {
            DebugWorld.placeSlimefun(arcane.getRelative(o[0], 0, o[1]), ItemKeys.slimefunId("ARCANE_PEDESTAL"), this::remember);
        }
        arcaneRecipe = altarItem.recipes().stream().filter(r -> r.source().equals("Occultech")).findFirst().orElse(null);
    }

    private void startArcaneInfusion() {
        BlockMenu menu = arcane == null ? null : BlockStorage.getInventory(arcane);
        if (menu == null || arcaneRecipe == null) {
            check("Arcane Altar has a menu and an Occultech recipe", false, "menu " + menu + ", recipe " + arcaneRecipe);
            return;
        }
        int slot = 0;
        for (Map.Entry<String, Integer> need : arcaneRecipe.needs().entrySet()) {
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ArcaneAltar.INPUTS[slot++], DebugWorld.item(need.getKey(), need.getValue()));
        }
        String problem = plugin.registrar().arcaneAltar().tryInfuse(arcane, menu);
        check("Arcane Altar starts an infusion with the ingredients in the middle", problem == null, String.valueOf(problem));
        check("the infusion lays the pentagram on the ground", floorSigils(arcane).contains("ritual_sigil_pentagram"),
            String.valueOf(floorSigils(arcane)));
    }

    /** The floor sigil holograms on a block (their models). */
    private static List<String> floorSigils(Block at) {
        return at.getWorld().getNearbyEntitiesByType(org.bukkit.entity.ItemDisplay.class, at.getLocation().add(0.5, 0.1, 0.5), 1.5).stream()
            .map(d -> d.getItemStack().getItemMeta())
            .filter(meta -> meta != null && meta.hasItemModel() && meta.getItemModel().getKey().startsWith("ritual_sigil"))
            .map(meta -> meta.getItemModel().getKey()).toList();
    }

    private void arcaneResult() {
        BlockMenu menu = arcane == null ? null : BlockStorage.getInventory(arcane);
        ItemStack out = menu == null ? null : menu.getItemInSlot(io.github.amitelia.occultech.items.ArcaneAltar.OUTPUT);
        boolean ok = out != null && arcaneRecipe != null && out.isSimilar(arcaneRecipe.output());
        check("Arcane Altar infusion produces the result in about 3s", ok, out == null ? "nothing" : out.getType().toString());
        boolean emptied = menu != null && java.util.Arrays.stream(io.github.amitelia.occultech.items.ArcaneAltar.INPUTS)
            .allMatch(s -> menu.getItemInSlot(s) == null || menu.getItemInSlot(s).getType().isAir());
        check("Arcane Altar used up exactly the recipe's ingredients", emptied, "inputs left over");
        check("the pentagram is gone after the infusion", floorSigils(arcane).isEmpty(), String.valueOf(floorSigils(arcane)));
        check("Floor Sigil registered", SlimefunItem.getById(ItemKeys.slimefunId("FLOOR_SIGIL")) != null, "missing");
        check("every boss has a Hollow Halo style", io.github.amitelia.occultech.items.HaloStyle.values().length >= 19, "too few");
        plugin.rituals().holograms().clear(arcane);
    }

    private void arcaneCrash() {
        BlockMenu menu = arcane == null ? null : BlockStorage.getInventory(arcane);
        if (menu == null || arcaneRecipe == null) {
            return;
        }
        var altarItem = plugin.registrar().arcaneAltar();
        menu.replaceExistingItem(io.github.amitelia.occultech.items.ArcaneAltar.OUTPUT, null);
        int slot = 0;
        int put = 0;
        for (Map.Entry<String, Integer> need : arcaneRecipe.needs().entrySet()) {
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ArcaneAltar.INPUTS[slot++], DebugWorld.item(need.getKey(), need.getValue()));
            put += need.getValue();
        }
        check("a second infusion starts", altarItem.tryInfuse(arcane, menu) == null, "did not start");
        altarItem.crashForTest(arcane);    // the server dies mid-infusion
        altarItem.recoverCrashed(arcane);  // ...and the altar loads again
        altarItem.recoverCrashed(arcane);  // a second load gives nothing more
        int back = 0;
        for (int s : io.github.amitelia.occultech.items.ArcaneAltar.INPUTS) {
            ItemStack item = menu.getItemInSlot(s);
            back += item == null || item.getType().isAir() ? 0 : item.getAmount();
        }
        check("a crash mid-infusion gives the ingredients back, once", back == put, put + " put in, " + back + " back");
        for (int s : io.github.amitelia.occultech.items.ArcaneAltar.INPUTS) {
            menu.replaceExistingItem(s, null);
        }
    }

    private void placeNexus() {
        nexus = shrine.getRelative(0, 0, 3);
        DebugWorld.placeSlimefun(nexus, ItemKeys.slimefunId("SERVITOR_NEXUS"), this::remember);
    }

    private void nexusLinked() {
        org.bukkit.Location linked = plugin.servitors().nexusFor(shrine.getLocation());
        check("a Servitor Nexus links the nearby shrine", nexus.getLocation().equals(linked), String.valueOf(linked));
        // a gathering shrine delivers into the Nexus store
        clearStore();
        setContract("GATHER_CONTRACT");
        // Gather takes one stack per action: clear leftovers from earlier steps so ours is the one it finds
        shrine.getWorld().getNearbyEntities(shrine.getLocation(), 8, 4, 8, e -> e instanceof Item).forEach(Entity::remove);
        testDrop = shrine.getWorld().dropItem(shrine.getLocation().add(1.5, 0.5, 1.5), new ItemStack(Material.EMERALD, 3));
        testDrop.setPickupDelay(0);
    }

    private void nexusGathered() {
        BlockMenu store = BlockStorage.getInventory(nexus);
        int emeralds = 0;
        for (int slot : io.github.amitelia.occultech.items.ServitorNexus.STORE) {
            ItemStack item = store == null ? null : store.getItemInSlot(slot);
            if (item != null && item.getType() == Material.EMERALD) {
                emeralds += item.getAmount();
            }
        }
        check("gathered items arrive in the Nexus store (nothing is lost)", emeralds == 3 && !testDrop.isValid(),
            emeralds + " in the Nexus, drop " + (testDrop.isValid() ? "still on the ground" : "gone") + ", shrine: "
                + ChatColor.stripColor(org.bukkit.ChatColor.translateAlternateColorCodes('&', plugin.servitors().statusAt(shrine.getLocation()))) + ", contract "
                + plugin.servitors().contractAt(shrine.getLocation()) + ", chunk loaded " + shrine.getChunk().isLoaded()
                + ", tickets " + shrine.getChunk().getPluginChunkTickets().size());
        setContract("HARVEST_CONTRACT");
        plugin.rituals().holograms().clear(nexus);
    }

    private void setContract(String id) {
        BlockMenu menu = BlockStorage.getInventory(shrine);
        if (menu != null) {
            menu.replaceExistingItem(io.github.amitelia.occultech.items.ServitorShrine.CONTRACT_SLOT, SlimefunItem.getById(ItemKeys.slimefunId(id)).getItem().clone());
        }
    }

    private int storeCount(Material type) {
        BlockMenu menu = BlockStorage.getInventory(shrine);
        int count = 0;
        for (int slot : io.github.amitelia.occultech.items.ServitorShrine.STORE) {
            ItemStack item = menu == null ? null : menu.getItemInSlot(slot);
            if (item != null && item.getType() == type) {
                count += item.getAmount();
            }
        }
        return count;
    }

    private void remember(Block block) {
        previous.putIfAbsent(block, block.getBlockData());
    }

    private void fillAt(Block at, RitualRecipe recipe) {
        Block saved = altar;
        altar = at;
        fill(recipe);
        altar = saved;
    }

    // ------------------------------------------------------------------ helpers

    private void snapshotSlimes() {
        slimesBefore = nearby().stream().filter(e -> e instanceof Slime).map(Entity::getUniqueId).collect(java.util.stream.Collectors.toSet());
    }

    private void fill(RitualRecipe recipe) {
        boolean centerItem = recipe.center() != null && !recipe.inPlace();
        DebugWorld.setAltarCenter(altar, centerItem ? DebugWorld.item(recipe.center(), 1) : null);
        RitualService.CircleCheck check = rituals.checkCircle(altar).orElseThrow();
        List<int[]> bowls = check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation());
        bowls.forEach(offset -> DebugWorld.setBowl(altar.getRelative(offset[0], 0, offset[1]), null));
        int i = 0;
        for (Map.Entry<String, Integer> offering : recipe.offerings().entrySet()) {
            int[] offset = bowls.get(i++);
            DebugWorld.setBowl(altar.getRelative(offset[0], 0, offset[1]), DebugWorld.item(offering.getKey(), offering.getValue()));
        }
    }

    private boolean bowlsEmpty() {
        RitualService.CircleCheck check = rituals.checkCircle(altar).orElseThrow();
        for (int[] offset : check.pattern().positionsOf(Circles.OFFERING_BOWL, check.rotation())) {
            BlockMenu menu = BlockStorage.getInventory(altar.getRelative(offset[0], 0, offset[1]));
            ItemStack item = menu == null ? null : menu.getItemInSlot(OfferingBowl.SLOT);
            if (item != null && !item.getType().isAir()) {
                return false;
            }
        }
        return true;
    }

    private String idIn(int slot) {
        BlockMenu menu = BlockStorage.getInventory(altar);
        ItemStack item = menu == null ? null : menu.getItemInSlot(slot);
        SlimefunItem sfItem = item == null || item.getType().isAir() ? null : SlimefunItem.getByItem(item);
        return sfItem == null ? null : sfItem.getId();
    }

    private List<Entity> nearby() {
        Block center = testAltar == null ? altar : testAltar;
        return List.copyOf(center.getWorld().getNearbyEntities(center.getLocation(), 30, 24, 30));
    }

    private void finish() {
        for (Block block : previous.keySet()) {
            DebugWorld.emptyMenu(block);
            BlockStorage.clearBlockInfo(block);
        }
        previous.forEach((block, data) -> block.setBlockData(data, false));
        if (chunk != null) {
            chunk.removePluginChunkTicket(plugin);
        }
        if (chunk2 != null) {
            chunk2.removePluginChunkTicket(plugin);
        }
        if (chunk3 != null) {
            chunk3.removePluginChunkTicket(plugin);
        }
        if (chunk4 != null) {
            chunk4.removePluginChunkTicket(plugin);
        }
        bosses.setAwayRules(true);
        bosses.setAwaySeconds(plugin.getConfig().getInt("bosses.away-seconds", 180));
        say((failed == 0 ? "&a" : "&c") + "[Occultech] Self-test finished: " + passed + " passed, " + failed + " failed.");
    }

    private void then(long delay, Runnable action) {
        steps.add(new Step(delay, action));
    }

    private void next() {
        Step step = steps.poll();
        if (step == null) {
            finish();
            return;
        }
        Bukkit.getScheduler().runTaskLater(plugin, () -> {
            try {
                step.action().run();
            } catch (RuntimeException e) {
                check("step threw no exception", false, e.toString());
                plugin.getLogger().log(java.util.logging.Level.WARNING, "Self-test step failed", e);
            }
            next();
        }, Math.max(1, step.delay()));
    }

    private void check(String name, boolean ok, String detail) {
        if (ok) {
            passed++;
            say("&a  PASS &7" + name);
        } else {
            failed++;
            say("&c  FAIL &7" + name + " &8(" + detail + ")");
        }
    }

    private void say(String message) {
        sender.sendMessage(ChatColor.translateAlternateColorCodes('&', message));
    }
}
