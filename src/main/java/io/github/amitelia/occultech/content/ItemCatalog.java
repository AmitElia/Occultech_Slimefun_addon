package io.github.amitelia.occultech.content;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.yaml.snakeyaml.Yaml;

/**
 * Parsed form of {@code docs/recipes.yml} (packaged into the jar as {@code recipes.yml}).
 * Pure Java so it can be unit tested; turning it into Slimefun items happens in {@code setup/}.
 */
public final class ItemCatalog {

    public record TierDef(int tier, String name, String gear) {}

    /**
     * @param inputs catalog keys ({@code mc:X}, {@code sf:X} or an Occultech id) to amounts, in file order
     */
    public record RecipeDef(String type, int out, @Nullable String center, int circle, Map<String, Integer> inputs, @Nullable String boss,
        double chance, boolean inPlace) {}

    /**
     * @param head   optional player-head texture replacing the material look
     * @param repair Occultech id of the item that repairs this one in a repair ritual, or null
     */
    public record ItemDef(String id, int tier, String category, String name, String purpose, @Nullable String material, int durability, RecipeDef recipe,
        @Nullable String head, @Nullable String repair, Map<String, Integer> enchants, List<RecipeDef> altRecipes, double toughness) {

        public boolean isBossDrop() {
            return "BOSS_DROP".equals(recipe.type());
        }
    }

    public record ResearchDef(String key, int id, String name, int cost, List<String> items) {}

    /**
     * @param mobDrops vanilla item key to {min, max} per contributor
     */
    public record BossDef(String id, int tier, String kind, String base, String drop, int drops, @Nullable String catalyst, Map<String, Integer> offerings,
        Map<String, int[]> mobDrops, int xp) {}

    private final Map<Integer, TierDef> tiers;
    private final Map<String, ItemDef> items;
    private final Map<String, ResearchDef> researches;
    private final Map<String, BossDef> bosses;

    private ItemCatalog(Map<Integer, TierDef> tiers, Map<String, ItemDef> items, Map<String, ResearchDef> researches, Map<String, BossDef> bosses) {
        this.tiers = tiers;
        this.items = items;
        this.researches = researches;
        this.bosses = bosses;
    }

    @Nonnull
    public static ItemCatalog load(@Nonnull InputStream in) {
        Map<String, Object> root = new Yaml().load(in);

        Map<Integer, TierDef> tiers = new LinkedHashMap<>();
        map(root.get("tiers")).forEach((k, v) -> {
            Map<String, Object> t = map(v);
            int tier = Integer.parseInt(String.valueOf(k));
            tiers.put(tier, new TierDef(tier, str(t.get("name")), str(t.get("gear"))));
        });

        Map<String, ItemDef> items = new LinkedHashMap<>();
        map(root.get("items")).forEach((id, v) -> {
            Map<String, Object> i = map(v);
            items.put(id, new ItemDef(id, integer(i.get("tier"), 0), str(i.get("cat")), str(i.get("name")), str(i.get("purpose")),
                (String) i.get("material"), integer(i.get("durability"), 0), recipe(map(i.get("recipe"))), (String) i.get("head"),
                (String) i.get("repair"), amounts(i.get("enchants")), altRecipes(i.get("alt_recipes")),
                i.get("toughness") instanceof Number n ? n.doubleValue() : 0));
        });

        Map<String, ResearchDef> researches = new LinkedHashMap<>();
        map(root.get("researches")).forEach((key, v) -> {
            Map<String, Object> r = map(v);
            List<String> ids = new ArrayList<>();
            for (Object o : (List<?>) r.get("items")) {
                ids.add(String.valueOf(o));
            }
            researches.put(key, new ResearchDef(key, integer(r.get("id"), 0), str(r.get("name")), integer(r.get("cost"), 1), List.copyOf(ids)));
        });

        Map<String, BossDef> bosses = new LinkedHashMap<>();
        map(root.get("bosses")).forEach((id, v) -> {
            Map<String, Object> b = map(v);
            bosses.put(id, new BossDef(id, integer(b.get("tier"), 0), str(b.get("kind")), str(b.get("base")), str(b.get("drop")),
                integer(b.get("drops"), 1), (String) b.get("catalyst"), amounts(b.get("offerings")), ranges(b.get("mob_drops")),
                integer(b.get("xp"), 0)));
        });

        return new ItemCatalog(Collections.unmodifiableMap(tiers), Collections.unmodifiableMap(items),
            Collections.unmodifiableMap(researches), Collections.unmodifiableMap(bosses));
    }

    @Nonnull
    public Collection<ItemDef> items() {
        return items.values();
    }

    @Nonnull
    public Optional<ItemDef> item(@Nonnull String id) {
        return Optional.ofNullable(items.get(id));
    }

    @Nonnull
    public Collection<ResearchDef> researches() {
        return researches.values();
    }

    @Nonnull
    public Collection<BossDef> bosses() {
        return bosses.values();
    }

    @Nonnull
    public Optional<BossDef> boss(@Nonnull String id) {
        return Optional.ofNullable(bosses.get(id));
    }

    @Nonnull
    public TierDef tier(int tier) {
        TierDef def = tiers.get(tier);
        if (def == null) {
            throw new IllegalArgumentException("Unknown tier " + tier);
        }
        return def;
    }

    private static List<RecipeDef> altRecipes(Object o) {
        if (!(o instanceof List<?> list)) {
            return List.of();
        }
        List<RecipeDef> out = new ArrayList<>();
        for (Object entry : list) {
            out.add(recipe(map(entry)));
        }
        return List.copyOf(out);
    }

    private static RecipeDef recipe(Map<String, Object> r) {
        return new RecipeDef(str(r.get("type")), integer(r.get("out"), 1), (String) r.get("center"), integer(r.get("circle"), 0),
            amounts(r.get("in")), (String) r.get("boss"), r.get("chance") instanceof Number n ? n.doubleValue() : 1.0,
            Boolean.TRUE.equals(r.get("in_place")));
    }

    /** "min-max" (or a single number) per key. */
    private static Map<String, int[]> ranges(Object o) {
        Map<String, int[]> out = new LinkedHashMap<>();
        map(o).forEach((k, v) -> {
            String text = String.valueOf(v).trim();
            int dash = text.indexOf('-', 1);
            int min = Integer.parseInt(dash < 0 ? text : text.substring(0, dash).trim());
            int max = dash < 0 ? min : Integer.parseInt(text.substring(dash + 1).trim());
            out.put(k, new int[] { Math.min(min, max), Math.max(min, max) });
        });
        return Collections.unmodifiableMap(out);
    }

    private static Map<String, Integer> amounts(Object o) {
        Map<String, Integer> out = new LinkedHashMap<>();
        map(o).forEach((k, v) -> out.put(k, integer(v, 1)));
        return Collections.unmodifiableMap(out);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object o) {
        if (o == null) {
            return Map.of();
        }
        Map<String, Object> out = new LinkedHashMap<>();
        ((Map<Object, Object>) o).forEach((k, v) -> out.put(String.valueOf(k), v));
        return out;
    }

    private static String str(Object o) {
        return o == null ? "" : String.valueOf(o);
    }

    private static int integer(Object o, int fallback) {
        return o instanceof Number n ? n.intValue() : fallback;
    }
}
