package io.github.amitelia.occultech.content;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.util.Set;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

class ItemCatalogTest {

    private static final Set<String> GRID_TYPES = Set.of("ENHANCED_CRAFTING_TABLE", "MAGIC_WORKBENCH", "ARMOR_FORGE", "ANCIENT_ALTAR", "SMELTERY");
    private static ItemCatalog catalog;

    @BeforeAll
    static void load() throws Exception {
        try (InputStream in = ItemCatalogTest.class.getResourceAsStream("/recipes.yml")) {
            assertNotNull(in, "recipes.yml must be packaged as a resource");
            catalog = ItemCatalog.load(in);
        }
    }

    @Test
    void loadsAllTiersItemsAndBosses() {
        assertEquals("Initiate", catalog.tier(0).name());
        assertTrue(catalog.items().size() >= 80);
        assertTrue(catalog.boss("GELATINOUS_SOVEREIGN").isPresent());
    }

    @Test
    void tierZeroItemsHaveALook() {
        catalog.items().stream().filter(i -> i.tier() == 0)
            .forEach(i -> assertNotNull(i.material(), i.id() + " needs a material"));
    }

    @Test
    void gridRecipesFitAThreeByThreeGrid() {
        for (ItemCatalog.ItemDef item : catalog.items()) {
            if (GRID_TYPES.contains(item.recipe().type())) {
                String[] grid = GridLayout.layout(item.recipe().inputs(), item.recipe().center());
                assertEquals(9, grid.length, item.id());
            }
        }
    }

    @Test
    void everyOccultechIngredientExists() {
        for (ItemCatalog.ItemDef item : catalog.items()) {
            for (String key : item.recipe().inputs().keySet()) {
                if (!key.startsWith("mc:") && !key.startsWith("sf:")) {
                    assertTrue(catalog.item(key).isPresent(), item.id() + " uses unknown item " + key);
                }
            }
        }
    }

    @Test
    void researchesOnlyListKnownItems() {
        assertFalse(catalog.researches().isEmpty());
        for (ItemCatalog.ResearchDef research : catalog.researches()) {
            research.items().forEach(id -> assertTrue(catalog.item(id).isPresent(), research.key() + " lists " + id));
        }
    }

    @Test
    void ritualRecipesHaveACenter() {
        catalog.items().stream().filter(i -> i.recipe().type().equals("RITUAL"))
            .forEach(i -> assertNotNull(i.recipe().center(), i.id()));
    }

    @Test
    void catalogKeysConvertToRuntimeKeys() {
        assertEquals("mc:STRING", ItemKeys.fromCatalog("mc:STRING"));
        assertEquals("MAGIC_LUMP_1", ItemKeys.fromCatalog("sf:MAGIC_LUMP_1"));
        assertEquals("OCCULTECH_GRAVE_SALT", ItemKeys.fromCatalog("GRAVE_SALT"));
    }
}
