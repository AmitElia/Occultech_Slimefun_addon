package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockBreakHandler;
import io.github.thebusybiscuit.slimefun4.implementation.Slimefun;
import me.mrCookieSlime.CSCoreLibPlugin.Configuration.Config;
import me.mrCookieSlime.Slimefun.Objects.handlers.BlockTicker;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset;
import me.mrCookieSlime.Slimefun.api.item_transport.ItemTransportFlow;

/**
 * Arcane Altar (tier 0): Occultech's take on Slimefun's Ancient Altar, and it crafts the Ancient Altar's recipes too.
 * <ul>
 * <li>Everything goes into the altar itself (9 input slots, cargo friendly); nothing is placed on pedestals.</li>
 * <li>8 Arcane Pedestals around it (a ring 2 blocks out) show floating copies of what's inside - for show only, they
 * never need restocking.</li>
 * <li>Infuse: about 3 seconds - the items rise and circle, motes stream into the altar over a turning sigil, then the
 * result appears. Recipes are shapeless with amounts; any extra item type in the altar blocks the recipe.</li>
 * </ul>
 */
public class ArcaneAltar extends SlimefunItem {

    public static final int[] INPUTS = { 10, 11, 12, 19, 20, 21, 28, 29, 30 };
    public static final int OUTPUT = 24;
    /** Block data: the ingredients a running infusion took ({@link CrashLedger}). */
    private static final String LEDGER_KEY = "occultech_infusion_taken";
    private static final int BUTTON = 22;
    private static final int INFO = 4;
    private static final int INFUSE_TICKS = 60;
    public static final String PEDESTAL = "OCCULTECH_ARCANE_PEDESTAL";
    private static final int[][] RING = { { 2, 0 }, { 2, 2 }, { 0, 2 }, { -2, 2 }, { -2, 0 }, { -2, -2 }, { 0, -2 }, { 2, -2 } };
    private static final Color ARCANE = Color.fromRGB(170, 110, 255);

    /** A shapeless recipe: required amounts by item key. */
    public record ArcaneRecipe(Map<String, Integer> needs, ItemStack output, String source) {}

    private final List<ArcaneRecipe> recipes = new ArrayList<>();
    private final Map<Location, ItemDisplay[]> shown = new HashMap<>();
    private final Map<Location, BukkitRunnable> infusing = new HashMap<>();
    /** The pentagram glowing on the ground under a running infusion (O2's crisp pentagram, a floor hologram). */
    private final Map<Location, RitualSigil> pentagrams = new HashMap<>();
    /** What each running infusion will produce (handed out early if the altar is broken or the server stops). */
    private final Map<Location, ItemStack> pending = new HashMap<>();
    private final Plugin plugin;

    public ArcaneAltar(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, Plugin plugin,
        RitualService rituals) {
        super(group, item, type, recipe, output);
        this.plugin = plugin;

        new BlockMenuPreset(getId(), MenuUtils.color("&5Arcane Altar")) {
            @Override
            public void init() {
                setSize(45);
                for (int slot = 0; slot < 45; slot++) {
                    if (!ArcaneAltar.contains(INPUTS, slot) && slot != OUTPUT && slot != BUTTON && slot != INFO) {
                        drawBackground(new int[] { slot });
                    }
                }
                addItem(INFO, MenuUtils.icon(Material.ENCHANTED_BOOK, "&5Arcane Altar", "&7Put every ingredient in here -",
                    "&7the pedestals around only show them.", "", "&7Crafts Occultech altar recipes and", "&7every Slimefun Ancient Altar recipe.",
                    "", "&7Needs 8 Arcane Pedestals, 2 blocks out", "&7(sides and corners)."), (p, s, i, a) -> false);
                addItem(BUTTON, MenuUtils.icon(Material.AMETHYST_CLUSTER, "&dInfuse", "&7Click to start the infusion."), (p, s, i, a) -> false);
            }

            @Override
            public boolean canOpen(Block block, Player player) {
                return MenuUtils.canOpen(block, player);
            }

            @Override
            public int[] getSlotsAccessedByItemTransport(ItemTransportFlow flow) {
                return flow == ItemTransportFlow.INSERT ? INPUTS : new int[] { OUTPUT };
            }

            @Override
            public void newInstance(BlockMenu menu, Block block) {
                menu.addMenuClickHandler(BUTTON, (p, slot, stack, action) -> {
                    infuse(p, block, menu);
                    return false;
                });
                // an infusion a crash cut short: its ingredients go back into the altar
                Bukkit.getScheduler().runTask(plugin, () -> recoverCrashed(block));
            }
        };

        addItemHandler(new BlockTicker() {
            @Override
            public boolean isSynchronized() {
                return true;
            }

            @Override
            public void tick(Block block, SlimefunItem sfItem, Config data) {
                if (!infusing.containsKey(block.getLocation())) {
                    BlockMenu menu = BlockStorage.getInventory(block);
                    if (menu != null) {
                        showOnPedestals(block, menu);
                    }
                }
                rituals.holograms().show(block, null, infusing.containsKey(block.getLocation()) ? "&dInfusing..." : "&5Arcane Altar");
            }
        });

        addItemHandler(new BlockBreakHandler(false, false) {
            @Override
            public void onPlayerBreak(BlockBreakEvent e, ItemStack tool, List<ItemStack> drops) {
                Location at = e.getBlock().getLocation();
                rituals.holograms().clear(e.getBlock());
                BukkitRunnable running = infusing.remove(at);
                if (running != null) {
                    running.cancel();
                }
                closePentagram(at);
                ItemStack result = pending.remove(at);
                if (result != null) {
                    at.getWorld().dropItemNaturally(at.clone().add(0.5, 1, 0.5), result);
                }
                clearDisplays(at);
                BlockMenu menu = BlockStorage.getInventory(e.getBlock());
                if (menu != null) {
                    menu.dropItems(at, INPUTS);
                    menu.dropItems(at, OUTPUT);
                }
            }
        });
    }

    // ------------------------------------------------------------------ recipes

    public void addRecipe(ItemStack[] inputs, ItemStack output, String source) {
        Map<String, Integer> needs = new LinkedHashMap<>();
        for (ItemStack input : inputs) {
            if (input != null && !input.getType().isAir()) {
                needs.merge(MenuUtils.keyOf(input), input.getAmount(), Integer::sum);
            }
        }
        if (!needs.isEmpty()) {
            recipes.add(new ArcaneRecipe(needs, output.clone(), source));
        }
    }

    public List<ArcaneRecipe> recipes() {
        return List.copyOf(recipes);
    }

    /** Adds every Slimefun Ancient Altar recipe (call once all addons have registered their items). */
    public int importAncientAltarRecipes() {
        int added = 0;
        for (SlimefunItem item : Slimefun.getRegistry().getEnabledSlimefunItems()) {
            if (RecipeType.ANCIENT_ALTAR.equals(item.getRecipeType()) && item.getRecipe() != null) {
                addRecipe(item.getRecipe(), item.getRecipeOutput(), item.getAddon().getName());
                added++;
            }
        }
        return added;
    }

    @Nullable
    private ArcaneRecipe match(BlockMenu menu) {
        Map<String, Integer> have = new HashMap<>();
        for (int slot : INPUTS) {
            ItemStack item = menu.getItemInSlot(slot);
            if (!MenuUtils.isEmpty(item)) {
                have.merge(MenuUtils.keyOf(item), item.getAmount(), Integer::sum);
            }
        }
        for (ArcaneRecipe recipe : recipes) {
            if (!have.keySet().equals(recipe.needs().keySet())) {
                continue;
            }
            boolean enough = recipe.needs().entrySet().stream().allMatch(e -> have.get(e.getKey()) >= e.getValue());
            if (enough) {
                return recipe;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------ infusion

    private void infuse(Player player, Block altar, BlockMenu menu) {
        String problem = tryInfuse(altar, menu);
        if (problem != null) {
            player.sendMessage(ChatColor.GRAY + problem);
            altar.getWorld().playSound(altar.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_HIT, 1F, 0.6F);
        }
    }

    /** Starts an infusion. Returns why it can't start, or null when it started. */
    @Nullable
    public String tryInfuse(Block altar, BlockMenu menu) {
        if (infusing.containsKey(altar.getLocation())) {
            return "The altar is already infusing.";
        }
        List<Block> missing = missingPedestals(altar);
        if (!missing.isEmpty()) {
            missing.forEach(b -> b.getWorld().spawnParticle(Particle.DUST, b.getLocation().add(0.5, 1, 0.5), 20, 0.2, 0.4, 0.2, 0,
                new Particle.DustOptions(Color.RED, 1.2F)));
            return "The altar needs 8 Arcane Pedestals around it (" + missing.size() + " missing - marked in red).";
        }
        ArcaneRecipe recipe = match(menu);
        if (recipe == null) {
            return "Nothing answers - no altar recipe uses exactly these ingredients.";
        }
        ItemStack out = menu.getItemInSlot(OUTPUT);
        if (!MenuUtils.isEmpty(out) && (!out.isSimilar(recipe.output()) || out.getAmount() + recipe.output().getAmount() > out.getMaxStackSize())) {
            return "Take the last result out first.";
        }
        // take the ingredients now, so nothing can be pulled out mid-infusion; the ledger gives them back after a crash
        List<CrashLedger.Entry> taken = new ArrayList<>();
        recipe.needs().forEach((key, amount) -> {
            int left = amount;
            for (int slot : INPUTS) {
                ItemStack item = menu.getItemInSlot(slot);
                if (left > 0 && !MenuUtils.isEmpty(item) && key.equals(MenuUtils.keyOf(item))) {
                    int take = Math.min(left, item.getAmount());
                    ItemStack took = item.clone();
                    took.setAmount(take);
                    menu.consumeItem(slot, take);
                    taken.add(CrashLedger.taken(menu, slot, took));
                    left -= take;
                }
            }
        });
        CrashLedger.save(altar, LEDGER_KEY, taken);
        animate(altar, menu, recipe.output());
        return null;
    }

    private List<Block> missingPedestals(Block altar) {
        List<Block> missing = new ArrayList<>();
        for (int[] offset : RING) {
            Block pedestal = altar.getRelative(offset[0], 0, offset[1]);
            if (!PEDESTAL.equals(BlockStorage.checkID(pedestal))) {
                missing.add(pedestal);
            }
        }
        return missing;
    }

    /** About 3 seconds: the shown items rise and circle, motes stream in over a turning sigil, then the result appears. */
    private void animate(Block altar, BlockMenu menu, ItemStack result) {
        Location center = altar.getLocation().add(0.5, 1.2, 0.5);
        ItemDisplay[] displays = shown.getOrDefault(altar.getLocation(), new ItemDisplay[RING.length]);
        altar.getWorld().playSound(center, Sound.BLOCK_ENCHANTMENT_TABLE_USE, 1F, 0.8F);
        altar.getWorld().playSound(center, Sound.BLOCK_BEACON_ACTIVATE, 0.7F, 1.6F);
        // the pentagram on the ground, across the pedestal ring; without the pack, drawn in particles
        RitualSigil pentagram = RitualSigil.show(altar, "ritual_sigil_pentagram", 5.6F);
        if (pentagram != null) {
            pentagrams.put(altar.getLocation(), pentagram);
        }
        BukkitRunnable task = new BukkitRunnable() {
            private int tick;

            @Override
            public void run() {
                tick += 2;
                double progress = tick / (double) INFUSE_TICKS;
                // the pentagram turns faster as the infusion builds: a quarter turn in 20 ticks, then 12, then 8
                int step = progress < 0.34 ? 20 : progress < 0.67 ? 12 : 8;
                if (pentagram == null) {
                    sigil(altar, tick * (0.03 + 0.06 * progress), progress);
                } else if (tick % step == 0) {
                    pentagram.turn(step);
                }
                for (int i = 0; i < RING.length; i++) {
                    Location pedestal = altar.getLocation().add(RING[i][0] + 0.5, 1.2, RING[i][1] + 0.5);
                    ItemDisplay display = displays[i];
                    if (display != null && display.isValid()) {
                        // rise, then spiral inward toward the altar
                        double angle = Math.atan2(RING[i][1], RING[i][0]) + progress * Math.PI * 2;
                        double radius = 2.0 * (1 - progress * 0.85);
                        Location spot = altar.getLocation().add(0.5 + Math.cos(angle) * radius, 1.3 + progress * 1.2, 0.5 + Math.sin(angle) * radius);
                        display.teleport(spot);
                        if (tick % 6 == 0) {
                            altar.getWorld().spawnParticle(Particle.TRAIL, spot, 1, 0, 0, 0, 0,
                                new Particle.Trail(center.clone().add(0, 0.8, 0), ARCANE, 20));
                        }
                    } else if (tick % 8 == 0) {
                        altar.getWorld().spawnParticle(Particle.TRAIL, pedestal, 1, 0, 0, 0, 0, new Particle.Trail(center, ARCANE, 20));
                    }
                }
                altar.getWorld().spawnParticle(Particle.ENCHANT, center.clone().add(0, 0.6, 0), 6, 0.4, 0.4, 0.4, 0.8);
                if (tick % 10 == 0) {
                    altar.getWorld().playSound(center, Sound.BLOCK_AMETHYST_BLOCK_CHIME, 0.8F, 0.6F + (float) progress);
                }
                if (tick >= INFUSE_TICKS) {
                    finish(altar, menu, result);
                    cancel();
                }
            }
        };
        infusing.put(altar.getLocation(), task);
        pending.put(altar.getLocation(), result.clone());
        task.runTaskTimer(plugin, 2L, 2L);
    }

    private void closePentagram(Location at) {
        RitualSigil pentagram = pentagrams.remove(at);
        if (pentagram != null) {
            pentagram.close();
        }
    }

    private void finish(Block altar, BlockMenu menu, ItemStack result) {
        CrashLedger.clear(altar, LEDGER_KEY);
        infusing.remove(altar.getLocation());
        closePentagram(altar.getLocation());
        pending.remove(altar.getLocation());
        clearDisplays(altar.getLocation());
        Location center = altar.getLocation().add(0.5, 1.4, 0.5);
        altar.getWorld().spawnParticle(Particle.END_ROD, center, 40, 0.2, 0.2, 0.2, 0.15);
        altar.getWorld().spawnParticle(Particle.DUST, center, 30, 0.5, 0.5, 0.5, 0, new Particle.DustOptions(Color.fromRGB(220, 180, 255), 1.4F));
        altar.getWorld().playSound(center, Sound.ENTITY_PLAYER_LEVELUP, 0.8F, 1.4F);
        ItemStack out = menu.getItemInSlot(OUTPUT);
        if (MenuUtils.isEmpty(out)) {
            menu.replaceExistingItem(OUTPUT, result.clone());
        } else if (out.isSimilar(result)) {
            ItemStack merged = out.clone();
            merged.setAmount(out.getAmount() + result.getAmount());
            menu.replaceExistingItem(OUTPUT, merged);
        } else {
            altar.getWorld().dropItemNaturally(center, result.clone());
        }
    }

    /** Without the resource pack: a circle with a turning pentagram on the ground, drawn in particles. */
    private static void sigil(Block altar, double spin, double progress) {
        Location base = altar.getLocation().add(0.5, 0.15, 0.5);
        double radius = 2.6;
        Particle.DustOptions ring = new Particle.DustOptions(ARCANE, 0.8F);
        Particle.DustOptions star = new Particle.DustOptions(Color.fromRGB(255, 200, 255), 0.6F + (float) progress * 0.6F);
        for (int i = 0; i < 24; i++) {
            double a = spin + Math.PI * 2 * i / 24;
            altar.getWorld().spawnParticle(Particle.DUST, base.clone().add(Math.cos(a) * radius, 0, Math.sin(a) * radius), 1, 0, 0, 0, 0, ring);
        }
        for (int i = 0; i < 5; i++) {
            double a1 = -spin + Math.PI * 2 * i / 5;
            double a2 = -spin + Math.PI * 2 * ((i + 2) % 5) / 5;
            for (double t = 0; t <= 1; t += 0.2) {
                double x = Math.cos(a1) * (1 - t) + Math.cos(a2) * t;
                double z = Math.sin(a1) * (1 - t) + Math.sin(a2) * t;
                altar.getWorld().spawnParticle(Particle.DUST, base.clone().add(x * radius, 0, z * radius), 1, 0, 0, 0, 0, star);
            }
        }
    }

    // ------------------------------------------------------------------ the pedestals show what's inside

    private void showOnPedestals(Block altar, BlockMenu menu) {
        List<ItemStack> distinct = new ArrayList<>();
        for (int slot : INPUTS) {
            ItemStack item = menu.getItemInSlot(slot);
            if (!MenuUtils.isEmpty(item) && distinct.stream().noneMatch(d -> d.isSimilar(item))) {
                ItemStack one = item.clone();
                one.setAmount(1);
                distinct.add(one);
            }
        }
        ItemDisplay[] displays = shown.computeIfAbsent(altar.getLocation(), l -> new ItemDisplay[RING.length]);
        for (int i = 0; i < RING.length; i++) {
            Block pedestal = altar.getRelative(RING[i][0], 0, RING[i][1]);
            ItemStack want = i < distinct.size() && PEDESTAL.equals(BlockStorage.checkID(pedestal)) ? distinct.get(i) : null;
            ItemDisplay display = displays[i];
            if (want == null) {
                if (display != null) {
                    display.remove();
                    displays[i] = null;
                }
                continue;
            }
            if (display == null || !display.isValid()) {
                Location at = pedestal.getLocation().add(0.5, 1.35, 0.5);
                display = altar.getWorld().spawn(at, ItemDisplay.class, d -> {
                    d.setPersistent(false);
                    d.setBillboard(Display.Billboard.VERTICAL);
                    d.setTeleportDuration(2);
                    d.setInterpolationDuration(20);
                    d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(0.5F, 0.5F, 0.5F), new AxisAngle4f()));
                    d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
                });
                displays[i] = display;
            }
            if (!want.isSimilar(display.getItemStack())) {
                display.setItemStack(want);
            }
            // a gentle bob, animated by the client
            float bob = (float) Math.sin(System.currentTimeMillis() / 600.0 + i) * 0.08F;
            display.setInterpolationDelay(0);
            display.setTransformation(new Transformation(new Vector3f(0, bob, 0), new AxisAngle4f(), new Vector3f(0.5F, 0.5F, 0.5F), new AxisAngle4f()));
        }
    }

    private void clearDisplays(Location at) {
        ItemDisplay[] displays = shown.remove(at);
        if (displays != null) {
            for (ItemDisplay display : displays) {
                if (display != null) {
                    display.remove();
                }
            }
        }
    }

    /** Gives back the ingredients of an infusion a crash cut short (never twice; see {@link CrashLedger}). */
    public void recoverCrashed(Block altar) {
        if (!infusing.containsKey(altar.getLocation())) {
            CrashLedger.restore(altar, LEDGER_KEY, plugin.getLogger());
        }
    }

    /** Self-test only: stops an infusion as a crash would (no result, the ledger left in place). */
    public void crashForTest(Block altar) {
        Location at = altar.getLocation();
        BukkitRunnable running = infusing.remove(at);
        if (running != null) {
            running.cancel();
        }
        pending.remove(at);
        closePentagram(at);
        clearDisplays(at);
    }

    /** Plugin disable: no displays left behind. */
    public void shutdown() {
        new ArrayList<>(shown.keySet()).forEach(this::clearDisplays);
        infusing.values().forEach(BukkitRunnable::cancel);
        infusing.clear();
        new ArrayList<>(pentagrams.keySet()).forEach(this::closePentagram);
        // the server is stopping: hand out the results now rather than lose them
        pending.forEach((at, result) -> {
            CrashLedger.clear(at.getBlock(), LEDGER_KEY);
            BlockMenu menu = BlockStorage.getInventory(at.getBlock());
            if (menu != null && MenuUtils.isEmpty(menu.getItemInSlot(OUTPUT))) {
                menu.replaceExistingItem(OUTPUT, result);
            } else {
                at.getWorld().dropItemNaturally(at.clone().add(0.5, 1, 0.5), result);
            }
        });
        pending.clear();
    }

    private static boolean contains(int[] slots, int slot) {
        for (int s : slots) {
            if (s == slot) {
                return true;
            }
        }
        return false;
    }

    /** Runs once all addons have loaded (Slimefun recipes from other addons exist by then). */
    public void importLater() {
        Bukkit.getScheduler().runTask(plugin, () -> plugin.getLogger().info("Arcane Altar: imported " + importAncientAltarRecipes()
            + " Slimefun Ancient Altar recipes"));
    }
}
