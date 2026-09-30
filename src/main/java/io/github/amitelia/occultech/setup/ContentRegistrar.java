package io.github.amitelia.occultech.setup;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.Damageable;
import org.bukkit.inventory.meta.ItemMeta;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.content.GridLayout;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.content.ItemCatalog.ItemDef;
import io.github.amitelia.occultech.content.ItemCatalog.RecipeDef;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.items.OccultCodex;
import io.github.amitelia.occultech.items.OccultItem;
import io.github.amitelia.occultech.items.OfferingBowl;
import io.github.amitelia.occultech.items.RitualAltar;
import io.github.amitelia.occultech.items.RitualService;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;

/**
 * Turns the catalog (recipes.yml) into registered Slimefun items. Only tiers up to {@link #IMPLEMENTED_TIER}
 * are registered; later tiers stay design-only until their mechanics exist.
 * <p>
 * Problems (unknown materials, missing ingredients, unsupported recipe types) are collected rather than thrown,
 * so one bad entry doesn't take the whole addon down; they are logged and checked by {@code /occultech selftest}.
 */
public final class ContentRegistrar {

    public static final int IMPLEMENTED_TIER = 0;
    private static final double ARENA_RADIUS_BASE = 12;

    private static final int[] BOWL_DISPLAY_SLOTS = { 1, 3, 5, 7, 0, 2, 6, 8 };
    private static final Pattern MOB_NAME = Pattern.compile("\\b([A-Z][A-Z_]+)\\b");

    private final Occultech plugin;
    private final ItemCatalog catalog;
    private final RitualService rituals;
    private final Map<String, SlimefunItemStack> stacks = new LinkedHashMap<>();
    private final List<String> problems = new ArrayList<>();
    private int researchCount;

    public ContentRegistrar(Occultech plugin, ItemCatalog catalog, RitualService rituals) {
        this.plugin = plugin;
        this.catalog = catalog;
        this.rituals = rituals;
    }

    public void registerAll() {
        for (ItemDef def : catalog.items()) {
            if (def.tier() <= IMPLEMENTED_TIER) {
                stacks.put(def.id(), createStack(def));
            }
        }
        for (ItemDef def : catalog.items()) {
            if (def.tier() <= IMPLEMENTED_TIER) {
                register(def);
            }
        }
        researchCount = OccultechResearches.register(catalog, problems);
        registerSummons();
    }

    /** Each implemented boss becomes a summoning ritual: offerings in the bowls, the catalyst (if any) on the altar. */
    private void registerSummons() {
        for (ItemCatalog.BossDef boss : catalog.bosses()) {
            if (boss.tier() > IMPLEMENTED_TIER) {
                continue;
            }
            if (!rituals.bosses().has(boss.id())) {
                problems.add("Boss " + boss.id() + " has no behavior class");
                continue;
            }
            boolean major = "major".equals(boss.kind());
            BossSpec spec = new BossSpec(boss.id(), title(boss.id()), boss.tier(), major, ItemKeys.slimefunId(boss.drop()), boss.drops(),
                ARENA_RADIUS_BASE + 2.0 * boss.tier(), major ? 900 : 600);

            Map<String, Integer> offerings = new LinkedHashMap<>();
            boss.offerings().forEach((key, amount) -> offerings.put(ItemKeys.fromCatalog(key), amount));
            String center = boss.catalyst() == null ? null : ItemKeys.slimefunId(boss.catalyst());
            rituals.addSummon(RitualRecipe.summoning(boss.id(), center, Map.copyOf(offerings), boss.tier()), spec);
        }
    }

    @Nonnull
    public List<String> problems() {
        return Collections.unmodifiableList(problems);
    }

    @Nonnull
    public Map<String, SlimefunItemStack> stacks() {
        return Collections.unmodifiableMap(stacks);
    }

    public int researchCount() {
        return researchCount;
    }

    private SlimefunItemStack createStack(ItemDef def) {
        Material material = def.material() == null ? null : Material.matchMaterial(def.material());
        if (material == null) {
            problems.add(def.id() + ": unknown or missing material '" + def.material() + "'");
            material = Material.BARRIER;
        }

        List<String> lore = new ArrayList<>();
        lore.add("");
        for (String line : wrap(def.purpose(), 34)) {
            lore.add(color("&7" + line));
        }
        lore.add("");
        lore.add(color("&8Occultech - Tier " + def.tier() + " " + catalog.tier(def.tier()).name()));

        boolean glint = switch (def.category()) {
            case "boss_drop", "catalyst", "component" -> true;
            default -> false;
        };

        return new SlimefunItemStack(ItemKeys.slimefunId(def.id()), material, nameColor(def.category()) + def.name(), meta -> {
            meta.setLore(lore);
            if (glint) {
                meta.setEnchantmentGlintOverride(true);
            }
            if (def.durability() > 0 && meta instanceof Damageable damageable) {
                damageable.setMaxDamage(def.durability());
            }
        });
    }

    private void register(ItemDef def) {
        RecipeDef recipe = def.recipe();
        ItemGroup group = OccultechGroups.forTier(catalog, def.tier());
        SlimefunItemStack stack = stacks.get(def.id());
        ItemStack output = stack.item().clone();
        output.setAmount(Math.max(1, recipe.out()));

        RecipeType type;
        ItemStack[] grid;
        switch (recipe.type()) {
            case "ENHANCED_CRAFTING_TABLE", "MAGIC_WORKBENCH", "ARMOR_FORGE", "ANCIENT_ALTAR", "SMELTERY" -> {
                type = vanillaSlimefunType(recipe.type());
                grid = gridRecipe(def, recipe);
            }
            case "RITUAL" -> {
                type = OccultechRecipeTypes.RITUAL;
                grid = ritualRecipe(def, recipe);
            }
            case "BOSS_DROP" -> {
                type = OccultechRecipeTypes.BOSS_DROP;
                grid = bossDisplay(recipe.boss());
            }
            default -> {
                problems.add(def.id() + ": recipe type " + recipe.type() + " is not implemented yet");
                return;
            }
        }

        SlimefunItem item = switch (def.id()) {
            case "INITIATE_ALTAR" -> new RitualAltar(group, stack, type, grid, output, rituals);
            case "OFFERING_BOWL" -> new OfferingBowl(group, stack, type, grid, output, rituals);
            case "OCCULT_CODEX" -> new OccultCodex(group, stack, type, grid, output, rituals, plugin);
            // placeable circle pieces are plain Slimefun blocks
            case "CHALK_GLYPH", "TALLOW_CANDLE" -> new SlimefunItem(group, stack, type, grid, output);
            default -> new OccultItem(group, stack, type, grid, output);
        };
        item.register(plugin);
    }

    private static RecipeType vanillaSlimefunType(String type) {
        return switch (type) {
            case "ENHANCED_CRAFTING_TABLE" -> RecipeType.ENHANCED_CRAFTING_TABLE;
            case "MAGIC_WORKBENCH" -> RecipeType.MAGIC_WORKBENCH;
            case "ARMOR_FORGE" -> RecipeType.ARMOR_FORGE;
            case "ANCIENT_ALTAR" -> RecipeType.ANCIENT_ALTAR;
            case "SMELTERY" -> RecipeType.SMELTERY;
            default -> throw new IllegalArgumentException(type);
        };
    }

    private ItemStack[] gridRecipe(ItemDef def, RecipeDef recipe) {
        ItemStack[] grid = new ItemStack[9];
        try {
            String[] layout = GridLayout.layout(recipe.inputs(), recipe.center());
            for (int i = 0; i < 9; i++) {
                grid[i] = layout[i] == null ? null : resolve(def, layout[i], 1);
            }
        } catch (IllegalArgumentException e) {
            problems.add(def.id() + ": " + e.getMessage());
        }
        return grid;
    }

    private ItemStack[] ritualRecipe(ItemDef def, RecipeDef recipe) {
        ItemStack[] grid = new ItemStack[9];
        if (recipe.center() == null) {
            problems.add(def.id() + ": ritual recipe has no center item");
            return grid;
        }
        if (recipe.inputs().size() > BOWL_DISPLAY_SLOTS.length) {
            problems.add(def.id() + ": ritual has more offerings than the guide can show");
            return grid;
        }
        grid[4] = resolve(def, recipe.center(), 1);

        Map<String, Integer> offerings = new LinkedHashMap<>();
        int slot = 0;
        for (Map.Entry<String, Integer> entry : recipe.inputs().entrySet()) {
            grid[BOWL_DISPLAY_SLOTS[slot++]] = resolve(def, entry.getKey(), entry.getValue());
            offerings.put(ItemKeys.fromCatalog(entry.getKey()), entry.getValue());
        }

        rituals.addRecipe(RitualRecipe.crafting(ItemKeys.slimefunId(def.id()), Math.max(1, recipe.out()),
            ItemKeys.fromCatalog(recipe.center()), Map.copyOf(offerings), recipe.circle()));
        return grid;
    }

    private ItemStack[] bossDisplay(@Nullable String bossId) {
        ItemStack[] grid = new ItemStack[9];
        ItemCatalog.BossDef boss = bossId == null ? null : catalog.boss(bossId).orElse(null);
        if (boss == null) {
            problems.add("Unknown boss " + bossId);
            return grid;
        }
        Material egg = Material.ZOMBIE_HEAD;
        Matcher matcher = MOB_NAME.matcher(boss.base());
        if (matcher.find()) {
            Material candidate = Material.matchMaterial(matcher.group(1) + "_SPAWN_EGG");
            if (candidate != null) {
                egg = candidate;
            }
        }
        ItemStack icon = new ItemStack(egg);
        ItemMeta meta = icon.getItemMeta();
        meta.setDisplayName(color("&c" + title(boss.id())));
        meta.setLore(List.of(color("&7Tier " + boss.tier() + " " + ("major".equals(boss.kind()) ? "gate boss" : "mini-boss")),
            color("&7Drops at least " + boss.drops() + " per win")));
        icon.setItemMeta(meta);
        grid[4] = icon;
        return grid;
    }

    @Nullable
    private ItemStack resolve(ItemDef owner, String catalogKey, int amount) {
        String key = ItemKeys.fromCatalog(catalogKey);
        ItemStack item = null;

        if (ItemKeys.isVanilla(key)) {
            Material material = Material.matchMaterial(key.substring(ItemKeys.VANILLA.length()));
            if (material != null) {
                item = new ItemStack(material);
            }
        } else if (key.startsWith(ItemKeys.PREFIX)) {
            SlimefunItemStack stack = stacks.get(key.substring(ItemKeys.PREFIX.length()));
            if (stack != null) {
                item = stack.item().clone();
            }
        } else {
            SlimefunItem sfItem = SlimefunItem.getById(key);
            if (sfItem != null) {
                item = sfItem.getItem().clone();
            }
        }

        if (item == null) {
            problems.add(owner.id() + ": cannot resolve ingredient " + catalogKey);
            return null;
        }
        item.setAmount(amount);
        return item;
    }

    private static String nameColor(String category) {
        return switch (category) {
            case "boss_drop" -> "&d";
            case "catalyst" -> "&5";
            case "weapon", "charm", "armor" -> "&6";
            case "utility", "labor" -> "&b";
            default -> "&f";
        };
    }

    public static String title(String id) {
        StringBuilder out = new StringBuilder();
        for (String word : id.split("_")) {
            out.append(out.isEmpty() ? "" : " ").append(word.charAt(0)).append(word.substring(1).toLowerCase());
        }
        return out.toString();
    }

    private static List<String> wrap(String text, int width) {
        List<String> lines = new ArrayList<>();
        StringBuilder line = new StringBuilder();
        for (String word : text.split(" ")) {
            if (line.length() + word.length() + 1 > width && !line.isEmpty()) {
                lines.add(line.toString());
                line.setLength(0);
            }
            line.append(line.isEmpty() ? "" : " ").append(word);
        }
        if (!line.isEmpty()) {
            lines.add(line.toString());
        }
        return lines;
    }

    private static String color(String text) {
        return ChatColor.translateAlternateColorCodes('&', text);
    }
}
