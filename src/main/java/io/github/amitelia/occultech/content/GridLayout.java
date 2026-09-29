package io.github.amitelia.occultech.content;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Places a recipe's ingredient counts onto a 3x3 grid (slot 4 = center) in a symmetric, deterministic way,
 * so recipes.yml only needs counts. Bigger groups take whole rings (edges or corners), pairs take opposite
 * slots, singles take the center.
 */
public final class GridLayout {

    private static final int[] EDGES = { 1, 3, 5, 7 };
    private static final int[] CORNERS = { 0, 2, 6, 8 };
    private static final int[][] PAIRS = { { 1, 7 }, { 3, 5 }, { 0, 8 }, { 2, 6 } };
    private static final int[] FILL_ORDER = { 4, 1, 7, 3, 5, 0, 8, 2, 6 };

    private GridLayout() {}

    /**
     * @param inputs ingredient key to count, in file order
     * @param center optional key that must sit in the center slot (e.g. the Ancient Altar's middle item)
     * @return 9 slots, null for empty
     */
    @Nonnull
    public static String[] layout(@Nonnull Map<String, Integer> inputs, @Nullable String center) {
        int total = inputs.values().stream().mapToInt(Integer::intValue).sum();
        if (total > 9) {
            throw new IllegalArgumentException("Recipe needs " + total + " slots, a 3x3 grid has 9");
        }

        String[] grid = new String[9];
        List<Map.Entry<String, Integer>> entries = new ArrayList<>(inputs.entrySet());

        if (center != null) {
            if (!inputs.containsKey(center)) {
                throw new IllegalArgumentException("Center item " + center + " is not an input");
            }
            grid[4] = center;
            entries.replaceAll(e -> e.getKey().equals(center) ? Map.entry(center, e.getValue() - 1) : e);
        }

        // Stable sort: larger groups claim the symmetric positions first
        entries.sort((a, b) -> Integer.compare(b.getValue(), a.getValue()));

        for (Map.Entry<String, Integer> entry : entries) {
            String key = entry.getKey();
            int left = entry.getValue();

            while (left >= 4 && (take(grid, EDGES, key) || take(grid, CORNERS, key))) {
                left -= 4;
            }
            while (left >= 2 && takePair(grid, key)) {
                left -= 2;
            }
            if (left % 2 == 1 && grid[4] == null) {
                grid[4] = key;
                left--;
            }
            for (int slot : FILL_ORDER) {
                if (left == 0) {
                    break;
                }
                if (grid[slot] == null) {
                    grid[slot] = key;
                    left--;
                }
            }
        }
        return grid;
    }

    private static boolean take(String[] grid, int[] slots, String key) {
        for (int slot : slots) {
            if (grid[slot] != null) {
                return false;
            }
        }
        for (int slot : slots) {
            grid[slot] = key;
        }
        return true;
    }

    private static boolean takePair(String[] grid, String key) {
        for (int[] pair : PAIRS) {
            if (grid[pair[0]] == null && grid[pair[1]] == null) {
                grid[pair[0]] = key;
                grid[pair[1]] = key;
                return true;
            }
        }
        return false;
    }
}
