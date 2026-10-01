package io.github.amitelia.occultech.boss.tier3;

import java.util.List;

import io.github.amitelia.occultech.boss.BossBlueprint;

/**
 * Tier-3 boss behaviors, keyed by their recipes.yml ids. Gallus is the tier's gate and the final boss.
 */
public final class Tier3Bosses {

    private Tier3Bosses() {}

    public static List<BossBlueprint> all() {
        return List.of(
            new BossBlueprint("HOLLOW_WARLORD", HollowWarlord::new),
            new BossBlueprint("HEARTWOOD_HORROR", HeartwoodHorror::new),
            new BossBlueprint("DREAD_RIDERS", DreadRiders::new),
            new BossBlueprint("CORRUPTED_COLOSSUS", CorruptedColossus::new),
            new BossBlueprint("DOPPELGANGER", Doppelganger::new),
            new BossBlueprint("GALLUS", Gallus::new)
        );
    }
}
