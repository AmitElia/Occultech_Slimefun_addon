package io.github.amitelia.occultech.debug;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.bukkit.Bukkit;
import org.bukkit.Chunk;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.data.BlockData;
import org.bukkit.command.CommandSender;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.items.OfferingBowl;
import io.github.amitelia.occultech.items.RitualAltar;
import io.github.amitelia.occultech.items.RitualService;
import io.github.amitelia.occultech.ritual.CirclePattern;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * In-game integration test, runnable from the console: {@code occultech selftest}.
 * <p>
 * Checks registration, then builds a real Initiate's circle next to spawn, verifies circle detection (including a
 * missing piece), runs the Sovereign's Catalyst ritual end to end, and restores the area afterwards.
 */
final class SelfTest {

    private static final String TEST_OUTPUT = ItemKeys.slimefunId("SOVEREIGN_CATALYST");

    private final Occultech plugin;
    private final CommandSender sender;
    private final Map<Block, BlockData> previous = new LinkedHashMap<>();
    private final List<Block> placed = new ArrayList<>();
    private int passed;
    private int failed;
    private Block altar;
    private Chunk chunk;

    SelfTest(Occultech plugin, CommandSender sender) {
        this.plugin = plugin;
        this.sender = sender;
    }

    void run() {
        say("&5[Occultech] Self-test starting...");
        ContentRegistrar registrar = plugin.registrar();
        ItemCatalog catalog = plugin.catalog();

        long expected = catalog.items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER).count();
        long registered = catalog.items().stream().filter(i -> i.tier() <= ContentRegistrar.IMPLEMENTED_TIER)
            .filter(i -> SlimefunItem.getById(ItemKeys.slimefunId(i.id())) != null).count();
        check("all " + expected + " tier-0 items registered", registered == expected, registered + " registered");
        check("no content problems", registrar.problems().isEmpty(), String.join("; ", registrar.problems()));
        check("researches registered", registrar.researchCount() == catalog.researches().size(), registrar.researchCount() + " registered");
        check("ritual recipes loaded", !plugin.rituals().recipes().isEmpty(), plugin.rituals().recipes().size() + " recipes");

        World world = Bukkit.getWorlds().get(0);
        int x = world.getSpawnLocation().getBlockX() + 24;
        int z = world.getSpawnLocation().getBlockZ() + 24;
        chunk = world.getChunkAt(x >> 4, z >> 4);
        chunk.addPluginChunkTicket(plugin);
        altar = world.getBlockAt(x, world.getHighestBlockYAt(x, z) + 1, z);

        CirclePattern pattern = Circles.forTier(0);
        int r = pattern.radius();
        for (int dz = -r; dz <= r; dz++) {
            for (int dx = -r; dx <= r; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                if (glyph != null) {
                    place(altar.getRelative(dx, 0, dz), glyph);
                }
            }
        }
        // give Slimefun a moment to create the block menus
        Bukkit.getScheduler().runTaskLater(plugin, this::circleStage, 5L);
    }

    private void circleStage() {
        RitualService rituals = plugin.rituals();
        Optional<RitualService.CircleCheck> check = rituals.checkCircle(altar);
        check("altar recognised", check.isPresent(), "BlockStorage id " + BlockStorage.checkID(altar));
        check("complete circle detected", check.isPresent() && check.get().complete(),
            check.map(c -> c.missing().size() + " missing").orElse("no check"));

        Block corner = altar.getRelative(-2, 0, -2);
        String cornerId = BlockStorage.checkID(corner);
        BlockStorage.clearBlockInfo(corner);
        corner.setType(Material.AIR);
        Optional<RitualService.CircleCheck> broken = rituals.checkCircle(altar);
        check("missing glyph detected", broken.isPresent() && broken.get().missing().size() == 1,
            broken.map(c -> c.missing().size() + " missing").orElse("no check"));
        place(corner, cornerId);

        BlockMenu altarMenu = BlockStorage.getInventory(altar);
        check("altar menu exists", altarMenu != null, "no menu");
        Optional<RitualRecipe> recipe = rituals.recipes().stream().filter(rr -> rr.outputId().equals(TEST_OUTPUT)).findFirst();
        check("catalyst ritual recipe exists", recipe.isPresent(), "not loaded");
        if (altarMenu == null || recipe.isEmpty() || check.isEmpty()) {
            finish();
            return;
        }

        altarMenu.replaceExistingItem(RitualAltar.CENTER_SLOT, item(recipe.get().center(), 1));
        List<int[]> bowlOffsets = check.get().pattern().positionsOf(Circles.OFFERING_BOWL, check.get().rotation());
        List<BlockMenu> bowls = new ArrayList<>();
        int i = 0;
        for (Map.Entry<String, Integer> offering : recipe.get().offerings().entrySet()) {
            int[] offset = bowlOffsets.get(i++);
            BlockMenu bowl = BlockStorage.getInventory(altar.getRelative(offset[0], 0, offset[1]));
            if (bowl != null) {
                bowl.replaceExistingItem(OfferingBowl.SLOT, item(offering.getKey(), offering.getValue()));
                bowls.add(bowl);
            }
        }
        check("offering bowl menus exist", bowls.size() == recipe.get().offerings().size(), bowls.size() + " menus");

        RitualService.Outcome outcome = rituals.begin(null, altar);
        check("ritual starts", outcome == RitualService.Outcome.STARTED, outcome.name());
        check("offerings consumed at start", bowls.stream().allMatch(b -> empty(b.getItemInSlot(OfferingBowl.SLOT))), "bowls not empty");
        check("altar locked during ritual", rituals.isLocked(altar.getLocation()), "not locked");

        Bukkit.getScheduler().runTaskLater(plugin, () -> resultStage(altarMenu), RitualService.DURATION_TICKS + 20L);
    }

    private void resultStage(BlockMenu altarMenu) {
        ItemStack result = altarMenu.getItemInSlot(RitualAltar.CENTER_SLOT);
        SlimefunItem resultItem = empty(result) ? null : SlimefunItem.getByItem(result);
        check("ritual produced Sovereign's Catalyst", resultItem != null && resultItem.getId().equals(TEST_OUTPUT),
            resultItem == null ? "nothing in the altar" : resultItem.getId());
        check("altar unlocked afterwards", !plugin.rituals().isLocked(altar.getLocation()), "still locked");
        finish();
    }

    private void finish() {
        for (Block block : placed) {
            BlockMenu menu = BlockStorage.getInventory(block);
            if (menu != null) {
                boolean bowl = Circles.OFFERING_BOWL.equals(BlockStorage.checkID(block));
                menu.replaceExistingItem(bowl ? OfferingBowl.SLOT : RitualAltar.CENTER_SLOT, null);
            }
            BlockStorage.clearBlockInfo(block);
        }
        previous.forEach(Block::setBlockData);
        chunk.removePluginChunkTicket(plugin);
        say((failed == 0 ? "&a" : "&c") + "[Occultech] Self-test finished: " + passed + " passed, " + failed + " failed.");
    }

    private void place(Block block, String id) {
        SlimefunItem item = SlimefunItem.getById(id);
        if (item == null) {
            check("place " + id, false, "item not registered");
            return;
        }
        previous.putIfAbsent(block, block.getBlockData());
        if (!placed.contains(block)) {
            placed.add(block);
        }
        block.setType(item.getItem().getType());
        BlockStorage.store(block, id);
    }

    private static ItemStack item(String key, int amount) {
        ItemStack stack;
        if (ItemKeys.isVanilla(key)) {
            stack = new ItemStack(Material.valueOf(key.substring(ItemKeys.VANILLA.length())));
        } else {
            stack = SlimefunItem.getById(key).getItem().clone();
        }
        stack.setAmount(amount);
        return stack;
    }

    private static boolean empty(ItemStack item) {
        return item == null || item.getType().isAir() || item.getAmount() <= 0;
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
        sender.sendMessage(org.bukkit.ChatColor.translateAlternateColorCodes('&', message));
    }
}
