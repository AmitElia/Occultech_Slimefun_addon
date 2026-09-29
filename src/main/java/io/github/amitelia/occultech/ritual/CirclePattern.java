package io.github.amitelia.occultech.ritual;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.BiFunction;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * A square summoning-circle layout, centered on the altar block.
 * <p>
 * Rows are strings of equal odd length; each character is a key into the legend
 * ({@code ' '} means "anything"). The pattern is matched in all four rotations.
 * <p>
 * Pure Java (no Bukkit types) so matching can be unit tested. The world side
 * supplies a lookup {@code (dx, dz) -> glyphId} relative to the altar.
 */
public final class CirclePattern {

    public static final char ANY = ' ';

    private final char[][] grid;
    private final Map<Character, String> legend;
    private final int radius;

    public CirclePattern(@Nonnull List<String> rows, @Nonnull Map<Character, String> legend) {
        int size = rows.size();
        if (size == 0 || size % 2 == 0) {
            throw new IllegalArgumentException("Circle pattern must have an odd number of rows");
        }

        this.grid = new char[size][];
        for (int i = 0; i < size; i++) {
            String row = rows.get(i);
            if (row.length() != size) {
                throw new IllegalArgumentException("Circle pattern must be square, row " + i + " has length " + row.length());
            }
            for (char c : row.toCharArray()) {
                if (c != ANY && !legend.containsKey(c)) {
                    throw new IllegalArgumentException("Circle pattern uses unknown symbol '" + c + "'");
                }
            }
            grid[i] = row.toCharArray();
        }

        this.legend = Collections.unmodifiableMap(new HashMap<>(legend));
        this.radius = size / 2;
    }

    public int radius() {
        return radius;
    }

    /**
     * @param lookup returns the glyph id at an offset from the altar, or null for none
     * @return the number of clockwise quarter turns that matched, or -1 if none did
     */
    public int match(@Nonnull BiFunction<Integer, Integer, String> lookup) {
        for (int rotation = 0; rotation < 4; rotation++) {
            if (missing(lookup, rotation).isEmpty()) {
                return rotation;
            }
        }
        return -1;
    }

    /**
     * Offsets {dx, dz} whose glyph is wrong for the given rotation.
     * Useful for showing players which parts of their circle are incomplete.
     */
    @Nonnull
    public List<int[]> missing(@Nonnull BiFunction<Integer, Integer, String> lookup, int rotation) {
        List<int[]> wrong = new ArrayList<>();
        for (int row = 0; row < grid.length; row++) {
            for (int col = 0; col < grid.length; col++) {
                char symbol = grid[row][col];
                if (symbol == ANY) {
                    continue;
                }
                int[] offset = rotate(col - radius, row - radius, rotation);
                String actual = lookup.apply(offset[0], offset[1]);
                if (!Objects.equals(legend.get(symbol), actual)) {
                    wrong.add(offset);
                }
            }
        }
        return wrong;
    }

    @Nullable
    public String glyphAt(int dx, int dz) {
        if (Math.abs(dx) > radius || Math.abs(dz) > radius) {
            return null;
        }
        char symbol = grid[dz + radius][dx + radius];
        return symbol == ANY ? null : legend.get(symbol);
    }

    private static int[] rotate(int dx, int dz, int quarterTurns) {
        for (int i = 0; i < quarterTurns; i++) {
            int tmp = dx;
            dx = -dz;
            dz = tmp;
        }
        return new int[] { dx, dz };
    }
}
