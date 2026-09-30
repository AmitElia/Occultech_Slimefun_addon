package io.github.amitelia.occultech.ritual;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import io.github.amitelia.occultech.ritual.RitualMatcher.Bowl;

class RitualMatcherTest {

    private static final RitualRecipe CATALYST = RitualRecipe.crafting("OCCULTECH_SOVEREIGN_CATALYST", 1, "mc:SLIME_BLOCK",
        Map.of("OCCULTECH_BROOD_SILK", 1, "OCCULTECH_GRAVE_SALT", 4), 0);
    private static final RitualRecipe BROOD_SUMMON = RitualRecipe.summoning("BROOD_MOTHER", null,
        Map.of("mc:STRING", 8, "OCCULTECH_GRAVE_SALT", 2), 0);

    @Test
    void matchesAndTakesOnlyWhatIsNeeded() {
        List<Bowl> bowls = List.of(new Bowl("OCCULTECH_GRAVE_SALT", 10), Bowl.EMPTY, new Bowl("OCCULTECH_BROOD_SILK", 3), Bowl.EMPTY);
        var match = RitualMatcher.match(List.of(CATALYST), "mc:SLIME_BLOCK", bowls, 0);
        assertTrue(match.isPresent());
        assertArrayEquals(new int[] { 4, 0, 1, 0 }, match.get().bowlAmounts());
    }

    @Test
    void wrongCenterDoesNotMatch() {
        List<Bowl> bowls = List.of(new Bowl("OCCULTECH_GRAVE_SALT", 4), new Bowl("OCCULTECH_BROOD_SILK", 1));
        assertTrue(RitualMatcher.match(List.of(CATALYST), "mc:DIRT", bowls, 0).isEmpty());
        assertTrue(RitualMatcher.match(List.of(CATALYST), null, bowls, 0).isEmpty());
    }

    @Test
    void notEnoughInABowlDoesNotMatch() {
        List<Bowl> bowls = List.of(new Bowl("OCCULTECH_GRAVE_SALT", 3), new Bowl("OCCULTECH_BROOD_SILK", 1));
        assertTrue(RitualMatcher.match(List.of(CATALYST), "mc:SLIME_BLOCK", bowls, 0).isEmpty());
    }

    @Test
    void extraItemsInUnusedBowlsBlockTheRitual() {
        List<Bowl> bowls = List.of(new Bowl("OCCULTECH_GRAVE_SALT", 4), new Bowl("OCCULTECH_BROOD_SILK", 1), new Bowl("mc:DIRT", 1));
        assertTrue(RitualMatcher.match(List.of(CATALYST), "mc:SLIME_BLOCK", bowls, 0).isEmpty());
    }

    @Test
    void circleTierMustBeHighEnough() {
        RitualRecipe tierOne = RitualRecipe.crafting("X", 1, "mc:SLIME_BLOCK", Map.of("OCCULTECH_GRAVE_SALT", 1), 1);
        List<Bowl> bowls = List.of(new Bowl("OCCULTECH_GRAVE_SALT", 1));
        assertTrue(RitualMatcher.match(List.of(tierOne), "mc:SLIME_BLOCK", bowls, 0).isEmpty());
        assertTrue(RitualMatcher.match(List.of(tierOne), "mc:SLIME_BLOCK", bowls, 1).isPresent());
    }

    @Test
    void summonWithoutCenterNeedsAnEmptyAltar() {
        List<Bowl> bowls = List.of(new Bowl("mc:STRING", 8), new Bowl("OCCULTECH_GRAVE_SALT", 2));
        var match = RitualMatcher.match(List.of(CATALYST, BROOD_SUMMON), null, bowls, 0);
        assertTrue(match.isPresent());
        assertTrue(match.get().recipe().isSummon());
        assertTrue(RitualMatcher.match(List.of(BROOD_SUMMON), "mc:DIRT", bowls, 0).isEmpty());
    }
}
