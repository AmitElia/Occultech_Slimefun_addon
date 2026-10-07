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
import io.github.amitelia.occultech.items.AbyssalAnchor;
import io.github.amitelia.occultech.items.BoneScepter;
import io.github.amitelia.occultech.items.ChoirBell;
import io.github.amitelia.occultech.items.CosmeticListener;
import io.github.amitelia.occultech.items.DecorationBlock;
import io.github.amitelia.occultech.items.StepTile;
import io.github.amitelia.occultech.items.DecorationService;
import io.github.amitelia.occultech.items.GuardianEye;
import io.github.amitelia.occultech.items.HeldWeapons;
import io.github.amitelia.occultech.items.MinionService;
import io.github.amitelia.occultech.items.OccultMachine;
import io.github.amitelia.occultech.items.WindChime;
import io.github.amitelia.occultech.items.BroodEgg;
import io.github.amitelia.occultech.items.FrenzyIdol;
import io.github.amitelia.occultech.items.ProducerBlock;
import io.github.amitelia.occultech.items.ScryingMirror;
import io.github.amitelia.occultech.items.ServitorShrine;
import io.github.amitelia.occultech.items.BanishingSalt;
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

    public static final int IMPLEMENTED_TIER = 3;
    private static final double ARENA_RADIUS_BASE = 18;
    private static final int MACHINE_SECONDS = 8;
    /** Assembling tier-3 gear takes longer than forging a material. */
    private static final int ASSEMBLER_SECONDS = 30;
    private static final java.util.Set<String> MACHINE_IDS = java.util.Set.of("OCCULT_FORGE", "SOUL_CONDENSER", "HOLLOW_ASSEMBLER", "ARCANE_ALTAR");
    private io.github.amitelia.occultech.items.ArcaneAltar arcaneAltar;

    private static final int[] BOWL_DISPLAY_SLOTS = { 1, 3, 5, 7, 0, 2, 6, 8 };
    private static final Pattern MOB_NAME = Pattern.compile("\\b([A-Z][A-Z_]+)\\b");

    private final Occultech plugin;
    private final ItemCatalog catalog;
    private final RitualService rituals;
    private final Map<String, SlimefunItemStack> stacks = new LinkedHashMap<>();
    private final Map<String, OccultMachine> machines = new LinkedHashMap<>();
    private final Map<String, RecipeType> machineTypes = new LinkedHashMap<>();
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
        registerAltRecipes();
        if (arcaneAltar != null) {
            arcaneAltar.importLater();
        }
        researchCount = OccultechResearches.register(catalog, problems);
        registerSummons();
    }

    /** Extra routes to an item made in an Occultech machine (e.g. Spirit Essence in the Soul Condenser). */
    private void registerAltRecipes() {
        for (ItemDef def : catalog.items()) {
            if (def.tier() > IMPLEMENTED_TIER) {
                continue;
            }
            for (RecipeDef alt : def.altRecipes()) {
                OccultMachine machine = machines.get(alt.type());
                if (machine != null) {
                    registerMachineRecipe(def, alt, machine);
                }
            }
        }
    }

    private void registerMachineRecipe(ItemDef def, RecipeDef recipe, OccultMachine machine) {
        List<ItemStack> inputs = new ArrayList<>();
        recipe.inputs().forEach((key, amount) -> {
            ItemStack item = resolve(def, key, amount);
            if (item != null) {
                inputs.add(item);
            }
        });
        ItemStack output = stacks.get(def.id()).item().clone();
        output.setAmount(Math.max(1, recipe.out()));
        int seconds = recipe.type().equals("HOLLOW_ASSEMBLER") ? ASSEMBLER_SECONDS : MACHINE_SECONDS;
        machine.registerRecipe(seconds, inputs.toArray(ItemStack[]::new), new ItemStack[] { output });
    }

    /** The Arcane Altar item (its recipes live on it), or null if not registered. */
    @javax.annotation.Nullable
    public io.github.amitelia.occultech.items.ArcaneAltar arcaneAltar() {
        return arcaneAltar;
    }

    @Nonnull
    public Map<String, OccultMachine> machines() {
        return Collections.unmodifiableMap(machines);
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

            // bonus drops: other items whose recipe is a chance-based drop from this boss (e.g. the Brood Egg)
            Map<String, Double> bonus = new LinkedHashMap<>();
            for (ItemDef def : catalog.items()) {
                if (def.tier() <= IMPLEMENTED_TIER && def.isBossDrop() && boss.id().equals(def.recipe().boss())
                    && !def.id().equals(boss.drop()) && def.recipe().chance() < 1) {
                    bonus.put(ItemKeys.slimefunId(def.id()), def.recipe().chance());
                }
            }
            Map<String, int[]> mobDrops = new LinkedHashMap<>();
            boss.mobDrops().forEach((key, range) -> {
                if (!ItemKeys.isVanilla(key) || Material.matchMaterial(key.substring(ItemKeys.VANILLA.length())) == null) {
                    problems.add("Boss " + boss.id() + ": mob drop " + key + " is not a vanilla item");
                } else {
                    mobDrops.put(key.substring(ItemKeys.VANILLA.length()), range);
                }
            });

            BossSpec spec = new BossSpec(boss.id(), title(boss.id()), boss.tier(), major, ItemKeys.slimefunId(boss.drop()), boss.drops(),
                ARENA_RADIUS_BASE + 2.0 * boss.tier(), major ? 900 : 600, Map.copyOf(bonus), Map.copyOf(mobDrops), boss.xp());

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

        if (def.repair() != null) {
            lore.add(lore.size() - 1, color("&8Repair: ritual with " + catalog.item(def.repair()).map(ItemCatalog.ItemDef::name).orElse(def.repair())));
            rituals.addRepair(ItemKeys.slimefunId(def.id()), ItemKeys.slimefunId(def.repair()));
        }
        org.bukkit.NamespacedKey model = Occultech.instance().resourcePack() == null ? null
            : Occultech.instance().resourcePack().modelFor(def.id());
        java.util.function.Consumer<ItemMeta> look = meta -> {
            meta.setLore(lore);
            if (model != null) {
                meta.setItemModel(model);   // Occultech's own model from its resource pack
            }
            if (glint) {
                meta.setEnchantmentGlintOverride(true);
            }
            if (def.durability() > 0 && meta instanceof Damageable damageable) {
                damageable.setMaxDamage(def.durability());
            }
            Material base = def.material() == null ? null : Material.matchMaterial(def.material());
            if (def.toughness() > 0 && base != null) {
                // armor toughness on top of the material's own armor (setting modifiers replaces the defaults, so copy them)
                org.bukkit.inventory.EquipmentSlot slot = base.getEquipmentSlot();
                meta.setAttributeModifiers(base.getDefaultAttributeModifiers(slot));
                meta.addAttributeModifier(org.bukkit.attribute.Attribute.ARMOR_TOUGHNESS, new org.bukkit.attribute.AttributeModifier(
                    Occultech.key("toughness_" + def.id().toLowerCase()), def.toughness(),
                    org.bukkit.attribute.AttributeModifier.Operation.ADD_NUMBER, slot.getGroup()));
            }
            def.enchants().forEach((name, level) -> {
                org.bukkit.enchantments.Enchantment enchantment = org.bukkit.Registry.ENCHANTMENT.get(org.bukkit.NamespacedKey.minecraft(name.toLowerCase()));
                if (enchantment != null) {
                    meta.addEnchant(enchantment, level, true);
                } else {
                    problems.add(def.id() + ": unknown enchantment " + name);
                }
            });
        };
        String id = ItemKeys.slimefunId(def.id());
        String name = nameColor(def.category()) + def.name();
        var customBlocks = Occultech.instance().customBlocks();
        if (customBlocks != null && def.head() == null) {
            material = customBlocks.itemMaterial(id, material);   // a custom block: made of the state it places (no blink)
        }
        // a head texture replaces the material look (textures come from recipes.yml `head`)
        SlimefunItemStack stack = def.head() != null ? new SlimefunItemStack(id, def.head(), name, look) : new SlimefunItemStack(id, material, name, look);
        if (customBlocks != null) {
            customBlocks.carryState((Object) stack instanceof ItemStack itemStack ? itemStack : stack.item(), id, null);
        }
        if (HeldWeapons.isHeld(id)) {
            // item() is a copy on Slimefun Legacy, where the stack itself is the ItemStack
            HeldWeapons.makeHoldable((Object) stack instanceof ItemStack itemStack ? itemStack : stack.item());
        }
        String set = def.id().substring(0, Math.max(0, def.id().indexOf('_'))).toLowerCase(java.util.Locale.ROOT);
        if ("armor".equals(def.category()) && Occultech.instance().resourcePack() != null
            && Occultech.instance().resourcePack().hasEquipment(set)) {
            wornLook((Object) stack instanceof ItemStack itemStack ? itemStack : stack.item(), set);
        }
        return stack;
    }

    /**
     * Worn armor drawn by the pack (Abyssal, Hollow): the chestplate, leggings and boots point their equippable at
     * Occultech's equipment asset {@code occultech:<set>} (textures, and the chestplate's 3D back pieces on the wings
     * layer); the helmet gets an equippable with no asset at all, so the game draws its own 3D item model on the head
     * (as it draws a carved pumpkin). Everything else about wearing it stays the vanilla piece's.
     */
    static void wornLook(ItemStack item, String set) {
        io.papermc.paper.datacomponent.item.Equippable worn = item.getData(io.papermc.paper.datacomponent.DataComponentTypes.EQUIPPABLE);
        if (worn == null) {
            return;
        }
        boolean helm = worn.slot() == org.bukkit.inventory.EquipmentSlot.HEAD;
        item.setData(io.papermc.paper.datacomponent.DataComponentTypes.EQUIPPABLE,
            io.papermc.paper.datacomponent.item.Equippable.equippable(worn.slot())
                .assetId(helm ? null : net.kyori.adventure.key.Key.key("occultech", set))
                .equipSound(worn.equipSound()).cameraOverlay(worn.cameraOverlay()).allowedEntities(worn.allowedEntities())
                .dispensable(worn.dispensable()).swappable(worn.swappable()).damageOnHurt(worn.damageOnHurt())
                .equipOnInteract(worn.equipOnInteract()).canBeSheared(worn.canBeSheared()).shearSound(worn.shearSound())
                .build());
    }

    private void register(ItemDef def) {
        RecipeDef recipe = def.recipe();
        ItemGroup group = OccultechGroups.forTier(catalog, def.tier());
        SlimefunItemStack stack = stacks.get(def.id());
        ItemStack output = stack.item().clone();
        output.setAmount(Math.max(1, recipe.out()));

        RecipeType type;
        ItemStack[] grid;
        if (machineTypes.containsKey(recipe.type())) {
            type = machineTypes.get(recipe.type());
            grid = machineGrid(def, recipe);
            if (recipe.type().equals("ARCANE_ALTAR") && arcaneAltar != null) {
                ItemStack result = stack.item().clone();
                result.setAmount(Math.max(1, recipe.out()));
                arcaneAltar.addRecipe(grid, result, "Occultech");
            }
            OccultMachine machine = machines.get(recipe.type());
            if (machine != null) {
                registerMachineRecipe(def, recipe, machine);
            }
            registerItem(def, group, stack, type, grid, output);
            return;
        }
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
                grid = bossDisplay(recipe.boss(), recipe.chance());
            }
            default -> {
                problems.add(def.id() + ": recipe type " + recipe.type() + " is not implemented yet");
                return;
            }
        }

        registerItem(def, group, stack, type, grid, output);
    }

    private ItemStack[] machineGrid(ItemDef def, RecipeDef recipe) {
        ItemStack[] grid = new ItemStack[9];
        int slot = 0;
        for (Map.Entry<String, Integer> input : recipe.inputs().entrySet()) {
            if (slot < 9) {
                grid[slot++] = resolve(def, input.getKey(), input.getValue());
            }
        }
        return grid;
    }

    private void registerItem(ItemDef def, ItemGroup group, SlimefunItemStack stack, RecipeType type, ItemStack[] grid, ItemStack output) {
        SlimefunItem item = switch (def.id()) {
            case "INITIATE_ALTAR", "BOUND_ALTAR", "ABYSSAL_ALTAR", "HOLLOW_ALTAR" -> new RitualAltar(group, stack, type, grid, output, rituals);
            case "ARCANE_ALTAR" -> arcaneAltar = new io.github.amitelia.occultech.items.ArcaneAltar(group, stack, type, grid, output, plugin, rituals);
            case "ARCANE_PEDESTAL" -> new SlimefunItem(group, stack, type, grid, output);
            case "OCCULT_FORGE" -> machine(def, new OccultMachine(group, stack, type, grid, output, "OCCULTECH_OCCULT_FORGE", Material.BLAZE_POWDER, 1024, 16, 1));
            case "SOUL_CONDENSER" -> machine(def, new OccultMachine(group, stack, type, grid, output, "OCCULTECH_SOUL_CONDENSER", Material.SOUL_SAND, 512, 8, 1));
            case "HOLLOW_ASSEMBLER" -> machine(def, new OccultMachine(group, stack, type, grid, output, "OCCULTECH_HOLLOW_ASSEMBLER", Material.ECHO_SHARD,
                8192, 128, 1, OccultMachine.LARGE_INPUTS));
            case "GUARDIAN_EYE" -> new GuardianEye(group, stack, type, grid, output, rituals, plugin.servitors());
            case "WIND_CHIME" -> new WindChime(group, stack, type, grid, output, rituals);
            case "PEARL_BED" -> new ProducerBlock(group, stack, type, grid, output, rituals, List.of(Material.PRISMARINE_SHARD, Material.PRISMARINE_SHARD, Material.PRISMARINE_CRYSTALS),
                "prismarine", plugin.getConfig().getInt("pearl-bed.seconds-per-item", 60), Material.PRISMARINE);
            case "EMBER_BRAZIER" -> new ProducerBlock(group, stack, type, grid, output, rituals, List.of(Material.BLAZE_POWDER), "blaze powder",
                plugin.getConfig().getInt("ember-brazier.seconds-per-item", 60), Material.MAGMA_BLOCK);
            case "WISP_JAR", "ABYSSAL_LANTERN", "RUNE_OBELISK", "OCCULT_ORRERY", "SOULFIRE_BRAZIER", "BOTTLED_GALE", "MOONLIT_LILY", "WITCHCAP",
                "EVERLIVING_CORAL", "PRISMATIC_NETHERRACK", "WATCHFUL_EYEBLOSSOM", "FLOOR_SIGIL" ->
                new DecorationBlock(group, stack, type, grid, output, plugin.decorations(), DecorationService.Kind.valueOf(def.id()));
            case "TROPHY_BOARD" -> new io.github.amitelia.occultech.items.TrophyBoard(group, stack, type, grid, output, plugin, plugin.decorations());
            case "RESIN_TILE" -> new StepTile(group, stack, type, grid, output, List.of(Material.RESIN_BRICKS));
            case "HOLLOW_HALO" -> new io.github.amitelia.occultech.items.Talisman(group, stack, type, grid, output,
                io.github.amitelia.occultech.items.TalismanService.Kind.HALO);
            case "WISHBONE_TALISMAN" -> new io.github.amitelia.occultech.items.Talisman(group, stack, type, grid, output,
                io.github.amitelia.occultech.items.TalismanService.Kind.WISHBONE);
            case "AURA_TALISMAN" -> new io.github.amitelia.occultech.items.Talisman(group, stack, type, grid, output,
                io.github.amitelia.occultech.items.TalismanService.Kind.AURA);
            case "GALLUS_EGG" -> new io.github.amitelia.occultech.items.GallusEgg(group, stack, type, grid, output, plugin);
            case "LICHS_PHYLACTERY" -> new BoneScepter(group, stack, type, grid, output, plugin.minions(), MinionService.Kind.HOLLOW_KNIGHT, 4,
                30_000, 6 * 60 * 60, 4);
            case "SERVITOR_NEXUS" -> new io.github.amitelia.occultech.items.ServitorNexus(group, stack, type, grid, output, rituals, plugin.servitors());
            case "CHIMING_TILE" -> new StepTile(group, stack, type, grid, output, List.of(Material.AMETHYST_BLOCK));
            case "TIDAL_TILE" -> new StepTile(group, stack, type, grid, output, List.copyOf(CosmeticListener.CORAL_BLOCKS.stream()
                .sorted().toList()));
            case "WYRMBREATH", "GUARDIANS_GAZE" -> new OccultItem(group, stack, type, grid, output);
            case "ABYSSAL_ANCHOR" -> new AbyssalAnchor(group, stack, type, grid, output, plugin);
            case "CHOIR_BELL" -> new ChoirBell(group, stack, type, grid, output);
            case "GRAVE_LANTERN" -> new BoneScepter(group, stack, type, grid, output, plugin.minions(), MinionService.Kind.WITHER_KNIGHT, 3, 25_000);
            case "OFFERING_BOWL" -> new OfferingBowl(group, stack, type, grid, output, rituals);
            case "OCCULT_CODEX" -> new OccultCodex(group, stack, type, grid, output, rituals, plugin);
            case "BANISHING_SALT" -> new BanishingSalt(group, stack, type, grid, output, rituals);
            case "BROOD_EGG" -> new BroodEgg(group, stack, type, grid, output, rituals, plugin.getConfig().getInt("brood-egg.seconds-per-string", 20));
            // placeable circle pieces are plain Slimefun blocks
            // circle pieces must be placeable (the default item class is not)
            case "CHALK_GLYPH", "TALLOW_CANDLE", "BOUND_GLYPH", "ABYSSAL_GLYPH", "HOLLOW_GLYPH" -> new SlimefunItem(group, stack, type, grid, output);
            case "SERVITOR_SHRINE" -> new ServitorShrine(group, stack, type, grid, output, rituals, plugin.servitors());
            case "FRENZY_IDOL" -> new FrenzyIdol(group, stack, type, grid, output, rituals, plugin.servitors());
            case "SCRYING_MIRROR" -> new ScryingMirror(group, stack, type, grid, output, rituals);
            case "PHANTOM_ROOST" -> new ProducerBlock(group, stack, type, grid, output, rituals, List.of(Material.PHANTOM_MEMBRANE), "membranes",
                plugin.getConfig().getInt("phantom-roost.seconds-per-membrane", 90), Material.BONE_BLOCK);
            case "BONE_SCEPTER" -> new BoneScepter(group, stack, type, grid, output, plugin.minions(), MinionService.Kind.SKELETON_ARCHER, 2, 20_000);
            default -> new OccultItem(group, stack, type, grid, output);
        };
        item.register(plugin);
        if (MACHINE_IDS.contains(def.id()) && !machineTypes.containsKey(def.id())) {
            machineTypes.put(def.id(), new RecipeType(Occultech.key(def.id().toLowerCase()), stack));
        }
    }

    private SlimefunItem machine(ItemDef def, OccultMachine machine) {
        machines.put(def.id(), machine);
        return machine;
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

        String center = ItemKeys.fromCatalog(recipe.center());
        rituals.addRecipe(recipe.inPlace()
            ? RitualRecipe.upgrade(ItemKeys.slimefunId(def.id()), center, Map.copyOf(offerings), recipe.circle())
            : RitualRecipe.crafting(ItemKeys.slimefunId(def.id()), Math.max(1, recipe.out()), center, Map.copyOf(offerings), recipe.circle()));
        return grid;
    }

    private ItemStack[] bossDisplay(@Nullable String bossId, double chance) {
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
        String dropLine = chance < 1
            ? "&7" + Math.round(chance * 100) + "% chance per win"
            : "&7Drops at least " + boss.drops() + " per win";
        meta.setLore(List.of(color("&7Tier " + boss.tier() + " " + ("major".equals(boss.kind()) ? "gate boss" : "mini-boss")), color(dropLine)));
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
