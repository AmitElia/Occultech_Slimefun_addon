package io.github.amitelia.occultech.ritual;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

class CirclePatternTest {

    // Asymmetric on purpose so each rotation is distinguishable
    private final CirclePattern pattern = new CirclePattern(
        List.of(
            "c c",
            " A ",
            "ccw"
        ),
        Map.of('c', "CHALK", 'A', "ALTAR", 'w', "WARD")
    );

    @Test
    void matchesUnrotated() {
        assertEquals(0, pattern.match(world(0)));
    }

    @Test
    void matchesEveryRotation() {
        for (int r = 0; r < 4; r++) {
            assertEquals(r, pattern.match(world(r)));
        }
    }

    @Test
    void failsWhenGlyphMissing() {
        Map<String, String> blocks = build(0);
        blocks.remove("1,1");
        assertEquals(-1, pattern.match((dx, dz) -> blocks.get(dx + "," + dz)));
        assertEquals(1, pattern.missing((dx, dz) -> blocks.get(dx + "," + dz), 0).size());
    }

    @Test
    void rejectsEvenSizedPatterns() {
        assertThrows(IllegalArgumentException.class, () -> new CirclePattern(List.of("cc", "cc"), Map.of('c', "CHALK")));
    }

    private java.util.function.BiFunction<Integer, Integer, String> world(int rotation) {
        Map<String, String> blocks = build(rotation);
        return (dx, dz) -> blocks.get(dx + "," + dz);
    }

    /** Places the pattern's glyphs in a fake world, rotated clockwise by quarter turns. */
    private Map<String, String> build(int rotation) {
        Map<String, String> blocks = new HashMap<>();
        for (int dz = -1; dz <= 1; dz++) {
            for (int dx = -1; dx <= 1; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                if (glyph != null) {
                    int x = dx;
                    int z = dz;
                    for (int i = 0; i < rotation; i++) {
                        int tmp = x;
                        x = -z;
                        z = tmp;
                    }
                    blocks.put(x + "," + z, glyph);
                }
            }
        }
        return blocks;
    }
}
