package io.github.amitelia.occultech.boss.tier0;

import java.util.List;

import io.github.amitelia.occultech.boss.BossBlueprint;

/**
 * Tier-0 boss behaviors, keyed by their recipes.yml ids.
 */
public final class Tier0Bosses {

    private Tier0Bosses() {}

    public static List<BossBlueprint> all() {
        return List.of(
            new BossBlueprint("BROOD_MOTHER", BroodMother::new),
            new BossBlueprint("VOLLEY", Volley::new),
            new BossBlueprint("WITCH_COVEN", WitchCoven::new),
            new BossBlueprint("GELATINOUS_SOVEREIGN", GelatinousSovereign::new)
        );
    }
}
