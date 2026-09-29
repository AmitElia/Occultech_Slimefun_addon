package io.github.amitelia.occultech.setup;

import java.util.List;
import java.util.Locale;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.content.ItemKeys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.researches.Research;

/**
 * Registers the researches defined in recipes.yml. Research ids are {@link #BASE_ID} + the file's id and must
 * never change once released, since player unlock data is stored by id.
 */
public final class OccultechResearches {

    private static final int BASE_ID = 262_000;

    private OccultechResearches() {}

    public static int register(ItemCatalog catalog, List<String> problems) {
        int count = 0;
        for (ItemCatalog.ResearchDef def : catalog.researches()) {
            Research research = new Research(Occultech.key(def.key().toLowerCase(Locale.ROOT)), BASE_ID + def.id(), def.name(), def.cost());
            int added = 0;
            for (String id : def.items()) {
                SlimefunItem item = SlimefunItem.getById(ItemKeys.slimefunId(id));
                if (item != null) {
                    research.addItems(item);
                    added++;
                } else if (catalog.item(id).isEmpty()) {
                    problems.add("Research " + def.key() + " lists unknown item " + id);
                }
            }
            if (added > 0) {
                research.register();
                count++;
            }
        }
        return count;
    }
}
