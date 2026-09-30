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
        then(0, this::killCurrentFight);
        then(30, () -> checkFightEndedCleanly("Brood Mother (ritual)"));
        for (String bossId : BOSSES) {
            then(0, () -> summonDirect(bossId));
            then(60, () -> checkFightRunning(bossId));
            then(0, this::killCurrentFight);
            then(30, () -> checkFightEndedCleanly(ContentRegistrar.title(bossId)));
        }
        then(0, this::refundOnInterruption);
        then(5, this::crashRecovery);

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
        then(0, this::buildAbyssalRing);
        then(5, this::abyssalCircleComplete);
        then(0, this::startHelmRitual);
        then(RitualService.DURATION_TICKS + 20L, this::helmResult);
        for (String bossId : TIER2_BOSSES) {
            then(0, () -> summonTier1(bossId));
            then(60, () -> checkFightRunning(bossId));
            then(0, this::killCurrentFight);
            then(30, () -> checkFightEndedCleanly(ContentRegistrar.title(bossId)));
        }
        then(0, this::placeGuardianEye);
        then(60, this::guardianEyeFired);
        then(0, this::tetherShrine);
        then(30, this::tethered);
        then(0, this::decorationPalette);
        next();
    }

    // ------------------------------------------------------------------ steps

    private void registration() {
        ContentRegistrar registrar = plugin.registrar();
        ItemCatalog catalog = plugin.catalog();
        long expected = catalog.items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER).count();
        long registered = catalog.items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER)
            .filter(i -> SlimefunItem.getById(ItemKeys.slimefunId(i.id())) != null).count();
        check("all " + expected + " items up to tier " + ContentRegistrar.IMPLEMENTED_TIER + " registered", registered == expected, registered + " registered");
        check("no content problems", registrar.problems().isEmpty(), String.join("; ", registrar.problems()));
        check("researches registered", registrar.researchCount() == catalog.researches().size(), registrar.researchCount() + " registered");
        long summons = rituals.recipes().stream().filter(RitualRecipe::isSummon).count();
        int expectedSummons = BOSSES.size() + TIER1_BOSSES.size() + TIER2_BOSSES.size();
        check(expectedSummons + " summoning rituals registered", summons == expectedSummons, summons + " summons");
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

    private void circleDetection() {
        Optional<RitualService.CircleCheck> check = rituals.checkCircle(altar);
        check("altar recognised", check.isPresent(), "id " + BlockStorage.checkID(altar));
        check("complete circle detected", check.isPresent() && check.get().complete(), check.map(c -> c.missing().size() + " missing").orElse("-"));

        Block corner = altar.getRelative(-2, 0, -2);
        BlockStorage.clearBlockInfo(corner);
        corner.setType(Material.AIR);
        Optional<RitualService.CircleCheck> broken = rituals.checkCircle(altar);
        check("missing glyph detected", broken.isPresent() && broken.get().missing().size() == 1, broken.map(c -> c.missing().size() + " missing").orElse("-"));
        DebugWorld.placeSlimefun(corner, Circles.CHALK_GLYPH, block -> {});
        check("altar menu exists", BlockStorage.getInventory(altar) != null, "no menu");
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
        Bukkit.getScheduler().runTaskLater(plugin, () -> check("Brood Egg never hatches (crack reset)",
            broodEgg.getBlockData() instanceof org.bukkit.block.data.Hatchable h && h.getHatch() == 0, "still cracked"), 30L);
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
    }

    private void craftingResult() {
        check("ritual produced Sovereign's Catalyst", CATALYST.equals(idIn(RitualAltar.CENTER_SLOT)), String.valueOf(idIn(RitualAltar.CENTER_SLOT)));
        check("altar unlocked afterwards", !rituals.isLocked(altar.getLocation()), "still locked");
    }

    private void summonRitual() {
        DebugWorld.setAltarCenter(altar, null);
        RitualRecipe recipe = rituals.recipes().stream().filter(r -> "BROOD_MOTHER".equals(r.bossId())).findFirst().orElseThrow();
        fill(recipe);
        snapshotSlimes();
        check("summoning ritual starts with an empty altar", rituals.begin(null, altar) == RitualService.Outcome.STARTED, "did not start");
    }

    private void summonResult() {
        currentFight = bosses.fightAt(altar).orElse(null);
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
        long drops = nearby().stream().filter(e -> e instanceof Item).count();
        check(name + " drops no vanilla loot", drops == 0, drops + " items on the ground");
        // superflat worlds spawn wild slimes, so only count slimes that appeared during the fight
        long slimes = nearby().stream().filter(e -> e instanceof Slime && !slimesBefore.contains(e.getUniqueId()) && !Keys.isSummoned(e)).count();
        check(name + " leaves no split slimes", slimes == 0, slimes + " new slimes");
        nearby().stream().filter(e -> e instanceof Item).forEach(Entity::remove);
        currentFight = null;
    }

    private void refundOnInterruption() {
        DebugWorld.setAltarCenter(altar, null);
        BossSpec spec = rituals.spec("GELATINOUS_SOVEREIGN").orElseThrow();
        BossFight fight = bosses.summon("GELATINOUS_SOVEREIGN", spec, altar, DebugWorld.item(CATALYST, 1));
        check("active-fight marker saved on the altar", BlockStorage.getLocationInfo(altar.getLocation(), ACTIVE_KEY) != null, "no marker");
        bosses.abort(fight, BossFight.Result.SHUTDOWN);
        check("interrupted gate fight refunds the catalyst", CATALYST.equals(idIn(RitualAltar.CENTER_SLOT)), String.valueOf(idIn(RitualAltar.CENTER_SLOT)));
        check("marker cleared after the fight", BlockStorage.getLocationInfo(altar.getLocation(), ACTIVE_KEY) == null, "marker left");
    }

    private void crashRecovery() {
        DebugWorld.setAltarCenter(altar, null);
        // simulate a crash: the marker survived but the fight is gone
        BlockStorage.addBlockInfo(altar, ACTIVE_KEY, CATALYST);
        plugin.rituals().recoverAltar(altar);
        check("crash recovery returns the catalyst", CATALYST.equals(idIn(RitualAltar.CENTER_SLOT)), String.valueOf(idIn(RitualAltar.CENTER_SLOT)));
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
        check("Harvest contract replants the wart", wart.getType() == Material.NETHER_WART && age != null && age.getAge() == 0,
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

    private void warded() {
        check("Ward contract protects its area", plugin.servitors().isWarded(shrine.getLocation().add(5, 0, 5)), "not warded");
        check("Ward contract doesn't reach far", !plugin.servitors().isWarded(shrine.getLocation().add(20, 0, 0)), "warded too far");
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

    private void buildAbyssalRing() {
        io.github.amitelia.occultech.ritual.CirclePattern pattern = Circles.forTier(2);
        for (int dz = -4; dz <= 4; dz++) {
            for (int dx = -4; dx <= 4; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                Block block = bound.getRelative(dx, 0, dz);
                if ((dx == 0 && dz == 0) || glyph == null || glyph.equals(BlockStorage.checkID(block))) {
                    continue;
                }
                remember(block);
                if (BlockStorage.hasBlockInfo(block)) {
                    DebugWorld.emptyMenu(block);
                    BlockStorage.clearBlockInfo(block);
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
        check("ritual produced the Abyssal Helm", item != null && item.getId().equals(ItemKeys.slimefunId("ABYSSAL_HELMET")),
            item == null ? "nothing" : item.getId());
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
        for (String id : List.of("CHIMING_TILE", "MOONLIT_LILY", "WITCHCAP", "TIDAL_TILE", "PRISMATIC_NETHERRACK")) {
            check(ContentRegistrar.title(id) + " registered", SlimefunItem.getById(ItemKeys.slimefunId(id)) != null, "missing");
        }
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
