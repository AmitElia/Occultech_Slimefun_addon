package io.github.amitelia.occultech.boss.tier1;

import java.util.List;

import io.github.amitelia.occultech.boss.BossBlueprint;

/**
 * Tier-1 boss behaviors, keyed by their recipes.yml ids.
 */
public final class Tier1Bosses {

    private Tier1Bosses() {}

    public static List<BossBlueprint> all() {
        return List.of(
            new BossBlueprint("THE_UNBOUND", TheUnbound.class, TheUnbound::new),
            new BossBlueprint("NIGHT_MATRIARCH", NightMatriarch.class, NightMatriarch::new),
            new BossBlueprint("MIRRORED_MAGUS", MirroredMagus.class, MirroredMagus::new),
            new BossBlueprint("ARCHEVOKER", Archevoker.class, Archevoker::new)
        );
    }
}
