package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.annotation.Nullable;

import org.bukkit.Material;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.ritual.CirclePattern;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ChestMenu;

/**
 * The Occult Codex's pages, as Slimefun-style chest menus: circle layout (with live check when opened from an altar),
 * crafting rituals and summoning rituals.
 */
final class CodexMenu {

    private static final int[] LIST_SLOTS = listSlots();
    private static final int CENTER = 22;
    // first the four sides, then the four corners (used when a ritual has more than 4 offerings)
    private static final int[] BOWL_SLOTS = { 13, 21, 23, 31, 12, 14, 30, 32 };
    private static final int VIEW_ROWS = 5;
    private static final int VIEW_COLUMNS = 9;

    private final RitualService rituals;

    CodexMenu(RitualService rituals) {
        this.rituals = rituals;
    }

    void openHome(Player player) {
        ChestMenu menu = menu("&5Occult Codex", 27);
        button(menu, 11, MenuUtils.icon(Material.LODESTONE, "&5Summoning Circles", "&7How to lay out each circle.", "", "&eClick to open"),
            () -> openCircleList(player));
        button(menu, 13, MenuUtils.icon(Material.ENCHANTED_BOOK, "&dCrafting Rituals", "&7Items made on the altar.", "", "&eClick to open"),
            () -> openRitualList(player, false));
        button(menu, 15, MenuUtils.icon(Material.WITHER_SKELETON_SKULL, "&cSummoning Rituals", "&7Bosses you can call into a circle.", "", "&eClick to open"),
            () -> openRitualList(player, true));
        menu.addItem(22, MenuUtils.icon(Material.BOOK, "&7How rituals work",
            "&7Put the center item on the altar", "&7(or leave it empty for a mini-boss),", "&7one offering per Offering Bowl,",
            "&7then press &fBegin Ritual&7.", "", "&7Breaking the circle mid-ritual", "&7destroys the offerings."), (p, s, i, a) -> false);
        menu.open(player);
    }

    private void openCircleList(Player player) {
        ChestMenu menu = menu("&5Summoning Circles", 27);
        back(menu, player);
        for (int tier = 0; tier <= Circles.highestTier(); tier++) {
            int t = tier;
            int size = Circles.forTier(tier).radius() * 2 + 1;
            button(menu, 11 + tier * 2, MenuUtils.icon(tier == 0 ? Material.LODESTONE : tier == 1 ? Material.AMETHYST_BLOCK : Material.PRISMARINE_BRICKS, "&5" + Circles.name(tier),
                "&7" + size + "x" + size + ", tier " + tier, "", "&eClick to see the layout"), () -> openCircle(player, t, null));
        }
        menu.open(player);
    }

    void openCircle(Player player, int tier, @Nullable RitualService.CircleCheck check) {
        openCircle(player, tier, check, 0);
    }

    /**
     * @param check     a live check of an altar's circle to mark missing pieces, or null to just show the layout
     * @param rowOffset first pattern row shown (big circles scroll: the view is 5 rows tall)
     */
    void openCircle(Player player, int tier, @Nullable RitualService.CircleCheck check, int rowOffset) {
        CirclePattern pattern = Circles.forTier(tier);
        int size = pattern.radius() * 2 + 1;
        ChestMenu menu = menu("&5" + Circles.name(tier) + " &8(" + size + "x" + size + ")", 54);
        back(menu, player);
        int maxOffset = Math.max(0, size - VIEW_ROWS);
        if (rowOffset > 0) {
            button(menu, 3, MenuUtils.icon(Material.SPECTRAL_ARROW, "&7Scroll up"), () -> openCircle(player, tier, check, rowOffset - 1));
        }
        if (rowOffset < maxOffset) {
            button(menu, 5, MenuUtils.icon(Material.SPECTRAL_ARROW, "&7Scroll down"), () -> openCircle(player, tier, check, rowOffset + 1));
        }

        Set<String> missingCells = new HashSet<>();
        if (check != null) {
            for (int[] offset : check.missing()) {
                int[] cell = unrotate(offset, check.rotation());
                missingCells.add(cell[0] + "," + cell[1]);
            }
        }

        int r = pattern.radius();
        int leftColumn = (VIEW_COLUMNS - Math.min(size, VIEW_COLUMNS)) / 2;
        for (int dz = -r; dz <= r; dz++) {
            for (int dx = -r; dx <= r; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                int row = dz + r - rowOffset;
                if (glyph == null || row < 0 || row >= VIEW_ROWS || dx + r >= VIEW_COLUMNS) {
                    continue;
                }
                int slot = (row + 1) * 9 + leftColumn + dx + r;
                String name = nameOf(glyph);
                ItemStack icon = missingCells.contains(dx + "," + dz)
                    ? MenuUtils.icon(Material.RED_STAINED_GLASS_PANE, "&cMissing: " + name, "&7Place a " + name + " here.")
                    : withName(itemOf(glyph, 1), name + (check != null ? " &a✔" : ""));
                menu.addItem(slot, icon, (p, s, i, a) -> false);
            }
        }

        List<String> status = new ArrayList<>();
        if (check == null) {
            status.add("&7Right-click an altar with the");
            status.add("&7codex to check your own circle.");
        } else if (check.complete()) {
            status.add("&aThis circle is complete.");
        } else {
            status.add("&c" + check.missing().size() + " pieces missing or wrong,");
            status.add("&cshown as red glass.");
        }
        status.add("");
        status.add("&7Everything sits on the altar's layer.");
        status.add("&7Any rotation works.");
        menu.addItem(8, MenuUtils.icon(check == null || check.complete() ? Material.LIME_DYE : Material.RED_DYE, "&fCircle status",
            status.toArray(String[]::new)), (p, s, i, a) -> false);
        menu.open(player);
    }

    private void openRitualList(Player player, boolean summons) {
        ChestMenu menu = menu(summons ? "&cSummoning Rituals" : "&dCrafting Rituals", 54);
        back(menu, player);
        int index = 0;
        for (RitualRecipe recipe : rituals.recipes()) {
            if (recipe.isSummon() != summons || index >= LIST_SLOTS.length) {
                continue;
            }
            ItemStack icon = summons ? bossIcon(recipe) : withLore(itemOf(recipe.outputId(), recipe.outputAmount()), "", "&eClick to see the ritual");
            button(menu, LIST_SLOTS[index++], icon, () -> openRitual(player, recipe));
        }
        menu.open(player);
    }

    private void openRitual(Player player, RitualRecipe recipe) {
        ChestMenu menu = menu(recipe.isSummon() ? "&cSummoning Ritual" : "&dCrafting Ritual", 54);
        button(menu, 0, MenuUtils.icon(Material.ARROW, "&7Back"), () -> openRitualList(player, recipe.isSummon()));

        menu.addItem(CENTER, recipe.center() == null
            ? MenuUtils.icon(Material.LIGHT_GRAY_STAINED_GLASS_PANE, "&7Leave the altar empty", "&7Mini-boss summons need", "&7no center item.")
            : withLore(itemOf(recipe.center(), 1), "", "&5Place on the altar"), (p, s, i, a) -> false);

        int bowl = 0;
        for (Map.Entry<String, Integer> offering : recipe.offerings().entrySet()) {
            if (bowl < BOWL_SLOTS.length) {
                menu.addItem(BOWL_SLOTS[bowl++], withLore(itemOf(offering.getKey(), offering.getValue()), "", "&8Put in one Offering Bowl"),
                    (p, s, i, a) -> false);
            }
        }
        if (recipe.inPlace()) {
            menu.addItem(CENTER, withLore(itemOf(recipe.center(), 1), "", "&5This altar itself: leave its slot empty.", "&5The altar is upgraded in place."),
                (p, s, i, a) -> false);
        }

        menu.addItem(24, MenuUtils.icon(Material.SPECTRAL_ARROW, "&7becomes"), (p, s, i, a) -> false);
        menu.addItem(25, recipe.isSummon() ? bossIcon(recipe) : itemOf(recipe.outputId(), recipe.outputAmount()), (p, s, i, a) -> false);
        menu.addItem(49, MenuUtils.icon(Material.LODESTONE, "&5Needs: " + Circles.name(recipe.circle()) + " or larger",
            "&7Open the Circles page", "&7to see the layout."), (p, s, i, a) -> false);
        menu.open(player);
    }

    // ------------------------------------------------------------------ helpers

    private ItemStack bossIcon(RitualRecipe recipe) {
        BossSpec spec = rituals.spec(recipe.bossId()).orElse(null);
        if (spec == null) {
            return new ItemStack(Material.ZOMBIE_SPAWN_EGG);
        }
        SlimefunItem drop = SlimefunItem.getById(spec.dropId());
        return MenuUtils.icon(eggFor(spec.id()), "&c" + spec.name(),
            "&7Tier " + spec.tier() + (spec.major() ? " gate boss" : " mini-boss"),
            "&7Drops: &f" + spec.drops() + "x " + (drop == null ? spec.dropId() : drop.getItemName()) + " &7per win",
            "&7Arena radius: &f" + (int) spec.arenaRadius() + " blocks",
            "", "&eClick to see the ritual");
    }

    private static Material eggFor(String bossId) {
        return switch (bossId) {
            case "BROOD_MOTHER" -> Material.SPIDER_SPAWN_EGG;
            case "VOLLEY" -> Material.SKELETON_SPAWN_EGG;
            case "WITCH_COVEN" -> Material.WITCH_SPAWN_EGG;
            case "GELATINOUS_SOVEREIGN" -> Material.SLIME_SPAWN_EGG;
            case "THE_UNBOUND" -> Material.VINDICATOR_SPAWN_EGG;
            case "NIGHT_MATRIARCH" -> Material.PHANTOM_SPAWN_EGG;
            case "MIRRORED_MAGUS" -> Material.PILLAGER_SPAWN_EGG;
            case "ARCHEVOKER" -> Material.EVOKER_SPAWN_EGG;
            case "ABYSSAL_WARDEN" -> Material.GUARDIAN_SPAWN_EGG;
            case "TIDEBREAKER" -> Material.DROWNED_SPAWN_EGG;
            case "BLAZE_CHOIR" -> Material.BLAZE_SPAWN_EGG;
            case "TEMPEST" -> Material.BREEZE_SPAWN_EGG;
            case "DROWNED_ELDER" -> Material.ELDER_GUARDIAN_SPAWN_EGG;
            default -> Material.ZOMBIE_SPAWN_EGG;
        };
    }

    private static ItemStack itemOf(@Nullable String key, int amount) {
        ItemStack item;
        if (key == null) {
            item = new ItemStack(Material.BARRIER);
        } else if (ItemKeys.isVanilla(key)) {
            Material material = Material.matchMaterial(key.substring(ItemKeys.VANILLA.length()));
            item = new ItemStack(material == null ? Material.BARRIER : material);
        } else {
            SlimefunItem sfItem = SlimefunItem.getById(key);
            item = sfItem == null ? new ItemStack(Material.BARRIER) : sfItem.getItem().clone();
        }
        item.setAmount(Math.max(1, Math.min(64, amount)));
        return item;
    }

    private static String nameOf(String id) {
        SlimefunItem item = SlimefunItem.getById(id);
        return item == null ? id : item.getItemName();
    }

    private static ItemStack withName(ItemStack item, String name) {
        ItemMeta meta = item.getItemMeta();
        meta.setDisplayName(MenuUtils.color(name));
        item.setItemMeta(meta);
        return item;
    }

    private static ItemStack withLore(ItemStack item, String... extra) {
        ItemMeta meta = item.getItemMeta();
        List<String> lore = meta.hasLore() ? new ArrayList<>(meta.getLore()) : new ArrayList<>();
        for (String line : extra) {
            lore.add(MenuUtils.color(line));
        }
        meta.setLore(lore);
        item.setItemMeta(meta);
        return item;
    }

    /** World offset back to pattern coordinates (inverse of a clockwise quarter turn per rotation). */
    private static int[] unrotate(int[] offset, int rotation) {
        int dx = offset[0];
        int dz = offset[1];
        for (int i = 0; i < rotation; i++) {
            int tmp = dx;
            dx = dz;
            dz = -tmp;
        }
        return new int[] { dx, dz };
    }

    private ChestMenu menu(String title, int size) {
        ChestMenu menu = new ChestMenu(MenuUtils.color(title));
        menu.setEmptySlotsClickable(false);
        menu.setPlayerInventoryClickable(true);
        for (int slot = 0; slot < size; slot++) {
            menu.addItem(slot, MenuUtils.icon(Material.GRAY_STAINED_GLASS_PANE, " "), (p, s, i, a) -> false);
        }
        return menu;
    }

    private void back(ChestMenu menu, Player player) {
        button(menu, 0, MenuUtils.icon(Material.ARROW, "&7Back"), () -> openHome(player));
    }

    private static void button(ChestMenu menu, int slot, ItemStack icon, Runnable action) {
        menu.addItem(slot, icon, (p, s, i, a) -> {
            action.run();
            return false;
        });
    }

    private static int[] listSlots() {
        List<Integer> slots = new ArrayList<>();
        for (int row = 1; row < 5; row++) {
            for (int col = 1; col < 8; col++) {
                slots.add(row * 9 + col);
            }
        }
        return slots.stream().mapToInt(Integer::intValue).toArray();
    }
}
