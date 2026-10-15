package io.github.amitelia.occultech.boss;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class FightStateTest {

    @Test
    void roundTrips() {
        UUID a = UUID.randomUUID();
        UUID b = UUID.randomUUID();
        FightState state = new FightState("GALLUS", 1240, List.of(0.4321, 0.0), 3, a, Map.of(a, 812.5), Map.of(a, 1200, b, 60));
        FightState back = FightState.parse(state.format());
        assertEquals("GALLUS", back.bossId());
        assertEquals(1240, back.elapsed());
        assertEquals(List.of(0.4321, 0.0), back.health());
        assertEquals(3, back.playersAtStart());
        assertEquals(a, back.summoner());
        assertEquals(812.5, back.damage().get(a), 0.01);
        assertNull(back.damage().get(b));
        assertEquals(60, back.presence().get(b));
    }

    @Test
    void noSummonerAndNoPlayers() {
        FightState back = FightState.parse(new FightState("VOLLEY", 0, List.of(1.0), 1, null, Map.of(), Map.of()).format());
        assertNull(back.summoner());
        assertEquals(List.of(1.0), back.health());
    }

    @Test
    void behaviorDataRoundTrips() {
        FightState state = new FightState("ARCHEVOKER", 300, List.of(0.4), 2, null, Map.of(), Map.of(),
            "revived=1;cyan=0;purple=1");
        FightState back = FightState.parse(state.format());
        assertEquals("revived=1;cyan=0;purple=1", back.data());
        assertEquals(List.of(0.4), back.health());
    }

    @Test
    void savedBeforeBehaviorDataStillReads() {
        FightState back = FightState.parse("1|VOLLEY|20|1.0000|1|-|");
        assertEquals("VOLLEY", back.bossId());
        assertEquals("", back.data());
    }

    @Test
    void unreadableIsNull() {
        assertNull(FightState.parse(null));
        assertNull(FightState.parse(""));
        assertNull(FightState.parse("2|GALLUS|0|1|1|-|"));
        assertNull(FightState.parse("1|GALLUS|x|1|1|-|"));
    }
}
