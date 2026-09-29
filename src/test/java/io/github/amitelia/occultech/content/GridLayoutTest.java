package io.github.amitelia.occultech.content;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.LinkedHashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;

class GridLayoutTest {

    @Test
    void fourFourOneIsEdgesCornersCenter() {
        Map<String, Integer> in = new LinkedHashMap<>();
        in.put("A", 4);
        in.put("B", 4);
        in.put("C", 1);
        assertArrayEquals(new String[] { "B", "A", "B", "A", "C", "A", "B", "A", "B" }, GridLayout.layout(in, null));
    }

    @Test
    void explicitCenterIsHonoured() {
        Map<String, Integer> in = new LinkedHashMap<>();
        in.put("SIGIL", 2);
        in.put("ASH", 2);
        String[] grid = GridLayout.layout(in, "SIGIL");
        assertEquals("SIGIL", grid[4]);
        assertEquals(2, count(grid, "SIGIL"));
        assertEquals(2, count(grid, "ASH"));
    }

    @Test
    void layoutIsDeterministicAndComplete() {
        Map<String, Integer> in = new LinkedHashMap<>();
        in.put("SALT", 6);
        in.put("BONE", 2);
        in.put("LUMP", 1);
        String[] first = GridLayout.layout(in, null);
        assertArrayEquals(first, GridLayout.layout(in, null));
        assertEquals(6, count(first, "SALT"));
        assertEquals(2, count(first, "BONE"));
        assertEquals("LUMP", first[4]);
    }

    @Test
    void rejectsMoreThanNineItems() {
        assertThrows(IllegalArgumentException.class, () -> GridLayout.layout(Map.of("A", 10), null));
    }

    private static int count(String[] grid, String key) {
        int n = 0;
        for (String slot : grid) {
            if (key.equals(slot)) {
                n++;
            }
        }
        return n;
    }
}
