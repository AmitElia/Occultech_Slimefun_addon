package io.github.amitelia.occultech.boss;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class GroupScalingTest {

    @Test
    void chosenCurve() {
        GroupScaling curve = GroupScaling.DEFAULT;
        assertEquals(1.0, curve.factor(1), 1e-9);
        assertEquals(1.45, curve.factor(2), 0.005);
        assertEquals(1.76, curve.factor(3), 0.005);
        assertEquals(2.03, curve.factor(4), 0.005);
        assertEquals(2.27, curve.factor(5), 0.005);
        assertEquals(curve.factor(5), curve.factor(12), 1e-9);
    }

    @Test
    void groupsAlwaysFasterAndFlattening() {
        GroupScaling curve = GroupScaling.DEFAULT;
        for (int n = 2; n <= 8; n++) {
            assertTrue(curve.factor(n) / n < curve.factor(n - 1) / (n - 1), "time to kill drops with each player");
            assertTrue(curve.factor(n) - curve.factor(n - 1) <= curve.factor(n - 1) - curve.factor(Math.max(1, n - 2)) + 1e-9 || n == 2);
        }
    }
}
