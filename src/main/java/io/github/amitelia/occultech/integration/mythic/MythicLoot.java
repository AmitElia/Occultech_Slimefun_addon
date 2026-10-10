package io.github.amitelia.occultech.integration.mythic;

import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.logging.Logger;

import org.bukkit.inventory.ItemStack;

import io.lumine.mythic.api.drops.IItemDrop;
import io.lumine.mythic.bukkit.BukkitAdapter;
import io.lumine.mythic.bukkit.MythicBukkit;
import io.lumine.mythic.core.drops.Drop;
import io.lumine.mythic.core.drops.LootBag;

/** Rolls an extras table once per eligible fighter, without materializing any world drop. */
public final class MythicLoot {
    private MythicLoot() {}

    public static List<String> roll(String bossId, Logger log) {
        var table = MythicBukkit.inst().getDropManager().getDropTable("OCCULTECH_" + bossId + "_EXTRAS");
        if (table.isEmpty()) return List.of();
        LootBag bag = table.get().generate();
        List<String> rewards = new ArrayList<>();
        for (Drop drop : bag.getLootTable()) {
            if (!(drop instanceof IItemDrop itemDrop)) {
                log.warning("Unsupported non-item Mythic extra for " + bossId + ": " + drop.getClass().getSimpleName());
                continue;
            }
            var abstractItem = itemDrop.getDrop(bag.getMetadata(), drop.getAmount());
            if (abstractItem == null) continue;
            ItemStack item = BukkitAdapter.adapt(abstractItem);
            if (item == null || item.getType().isAir() || item.getAmount() <= 0) continue;
            rewards.add("item:" + Base64.getEncoder().encodeToString(item.serializeAsBytes()));
        }
        return rewards;
    }
}
