package io.github.amitelia.occultech.event;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.Test;

class RaidScalingTest {

    private final RaidScaling raid = RaidScaling.DEFAULT;

    @Test
    void targetsFollowThePlayers() {
        assertEquals(2, raid.targets(1));
        assertEquals(2, raid.targets(5));
        assertEquals(4, raid.targets(10));
        assertEquals(10, raid.targets(25));
        assertEquals(10, raid.targets(60));
    }

    @Test
    void healthGrowsJustUnderLinear() {
        assertEquals(1, raid.factor(1), 1e-9);
        assertEquals(1, raid.factor(0.4), 1e-9);
        assertEquals(18.1, raid.factor(25), 0.05);
        for (int n = 2; n <= 40; n++) {
            assertTrue(raid.factor(n) > raid.factor(n - 1), "every player adds health");
            assertTrue(raid.factor(n) / n < raid.factor(n - 1) / (n - 1), "and every player kills faster");
        }
    }

    @Test
    void bodiesStayUnderTheHealthCap() {
        RaidScaling.Body small = RaidScaling.body(600);
        assertEquals(600, small.maxHealth(), 1e-9);
        assertEquals(1, small.damageTaken(), 1e-9);
        RaidScaling.Body big = RaidScaling.body(4000);
        assertEquals(RaidScaling.MAX_BODY_HEALTH, big.maxHealth(), 1e-9);
        // it lasts as long as 4000 health would
        assertEquals(4000, big.maxHealth() / big.damageTaken(), 1e-6);
    }

    @Test
    void spotsSpreadInsideTheArena() {
        for (int count = 1; count <= 10; count++) {
            List<double[]> spots = RaidScaling.spots(count, 45);
            assertEquals(count, spots.size());
            for (int i = 0; i < spots.size(); i++) {
                double[] a = spots.get(i);
                assertTrue(Math.hypot(a[0], a[1]) <= 45 - StaffRaid.SLOT_RADIUS, "a slot's fight fits in the arena");
                for (int j = i + 1; j < spots.size(); j++) {
                    double[] b = spots.get(j);
                    assertTrue(Math.hypot(a[0] - b[0], a[1] - b[1]) >= 15, count + " targets: slots " + i + " and " + j + " too close");
                }
            }
        }
    }
}
