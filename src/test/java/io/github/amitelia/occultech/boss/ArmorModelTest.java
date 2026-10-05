package io.github.amitelia.occultech.boss;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ArmorModelTest {

    @Test
    void netheriteProtectionFour() {
        // 20 damage on 20 armor / 12 toughness: armor cut clamp(20 - 20/5, 4, 20) = 16 -> 64%; Protection 16 -> 64%
        assertEquals(20 * 0.36 * 0.36, ArmorModel.after(20, false, ArmorModel.TIER_2, 1), 1e-6);
    }

    @Test
    void protectionIsCapped() {
        assertEquals(ArmorModel.after(30, true, new ArmorModel.Kit("x", 0, 0, 20, 0, 20), 1),
            ArmorModel.after(30, true, new ArmorModel.Kit("y", 0, 0, 40, 0, 20), 1), 1e-9);
    }

    @Test
    void bigHitsBreakThroughArmor() {
        // 60 on netherite: 20 - 60/5 = 8 points -> 32% cut, the floor is 4 (16%)
        assertEquals(60 * 0.68, ArmorModel.after(60, false, new ArmorModel.Kit("n", 20, 12, 0, 0, 20), 1), 1e-6);
    }

    @Test
    void magicIgnoresArmorButNotProtectionOrResistance() {
        assertEquals(10 * 0.2 * 0.8, ArmorModel.after(10, true, ArmorModel.TIER_3, 1), 1e-6);
    }

    @Test
    void hardDifficultyScales() {
        assertEquals(1.5 * ArmorModel.after(10, true, ArmorModel.TIER_0, 1), ArmorModel.after(10, true, ArmorModel.TIER_0, 1.5), 1e-6);
    }
}
