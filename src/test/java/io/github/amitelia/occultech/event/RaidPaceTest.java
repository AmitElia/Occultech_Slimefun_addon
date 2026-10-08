package io.github.amitelia.occultech.event;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class RaidPaceTest {

    @Test
    void theBarSetsTheBand() {
        assertEquals(0, RaidPace.of(1, 0).band());
        assertEquals(0, RaidPace.of(0.7, 0).band());
        assertEquals(1, RaidPace.of(0.66, 0).band());
        assertEquals(1, RaidPace.of(0.34, 0).band());
        assertEquals(2, RaidPace.of(0.33, 0).band());
        assertEquals(2, RaidPace.of(0.01, 0).band());
    }

    @Test
    void eachBandIsHarder() {
        RaidPace a = RaidPace.of(0.9, 0);
        RaidPace b = RaidPace.of(0.5, 0);
        RaidPace c = RaidPace.of(0.2, 0);
        assertTrue(a.overlap() < b.overlap() && b.overlap() < c.overlap());
        assertTrue(a.beams() < b.beams() && b.beams() < c.beams());
        assertTrue(a.cooldown(140) > b.cooldown(140) && b.cooldown(140) > c.cooldown(140));
        assertFalse(a.reverse());
        assertTrue(c.reverse());
        assertEquals(1, c.damageFactor(), 1e-9, "no extra damage before the enrage");
        assertEquals(0, c.cooldown(140) % 5, "cooldowns stay whole boss steps");
    }

    @Test
    void theSoftEnrageGrowsEvery30Seconds() {
        int enrage = RaidPace.ENRAGE_TICKS;
        assertEquals(1, RaidPace.of(0.9, enrage - 1).damageFactor(), 1e-9);
        RaidPace start = RaidPace.of(0.9, enrage);
        assertEquals(2, start.band(), "an enraged Council is at the last band whatever its health");
        assertEquals(1.05, start.damageFactor(), 1e-9);
        assertEquals(1.10, RaidPace.of(0.9, enrage + RaidPace.ENRAGE_EVERY).damageFactor(), 1e-9);
        assertEquals(1.25, RaidPace.of(0.9, enrage + 4 * RaidPace.ENRAGE_EVERY + 10).damageFactor(), 1e-9);
    }
}
