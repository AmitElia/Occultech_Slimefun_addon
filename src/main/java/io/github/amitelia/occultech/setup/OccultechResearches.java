package io.github.amitelia.occultech.setup;

import io.github.amitelia.occultech.Occultech;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.researches.Research;

/**
 * Slimefun researches. Ids start at {@link #BASE_ID} and must never change once
 * released, since player unlock data is stored by id.
 */
public final class OccultechResearches {

    private static final int BASE_ID = 262_000;

    private OccultechResearches() {}

    public static void setup() {
        register("ritual_chalk", 0, "Chalk and Circles", 8, OccultechStacks.RITUAL_CHALK.getItemId());
    }

    private static void register(String key, int offset, String name, int cost, String... itemIds) {
        Research research = new Research(Occultech.key(key), BASE_ID + offset, name, cost);
        for (String id : itemIds) {
            SlimefunItem item = SlimefunItem.getById(id);
            if (item != null) {
                research.addItems(item);
            }
        }
        research.register();
    }
}
