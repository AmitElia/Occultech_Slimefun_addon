package io.github.amitelia.occultech.boss.tier2;

import java.util.List;

import io.github.amitelia.occultech.boss.BossBlueprint;

/**
 * Tier-2 boss behaviors, keyed by their recipes.yml ids. The sea creatures glide over land (no ponds needed).
 */
public final class Tier2Bosses {

    private Tier2Bosses() {}

    public static List<BossBlueprint> all() {
        return List.of(
            new BossBlueprint("ABYSSAL_WARDEN", AbyssalWarden.class, AbyssalWarden::new),
            new BossBlueprint("TIDEBREAKER", Tidebreaker.class, Tidebreaker::new),
            new BossBlueprint("BLAZE_CHOIR", BlazeChoir.class, BlazeChoir::new),
            new BossBlueprint("TEMPEST", Tempest.class, Tempest::new),
            new BossBlueprint("DROWNED_ELDER", DrownedElder.class, DrownedElder::new)
        );
    }
}
