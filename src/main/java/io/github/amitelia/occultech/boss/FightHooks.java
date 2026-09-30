package io.github.amitelia.occultech.boss;

import javax.annotation.Nullable;

import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

/**
 * What the boss engine needs from the rest of the addon (items, storage), kept behind an interface so the engine
 * doesn't depend on Slimefun.
 */
public interface FightHooks {

    /** Give a contributor their loot: into the inventory, or dropped at their feet for them only. */
    void giveLoot(Player player, String itemId, int amount);

    /** Return a consumed catalyst after a fight ended through no fault of the players (unload, shutdown). */
    void refund(Block altar, ItemStack item);

    /** Persist "a fight is running here" so a crash can refund the catalyst on the next start. */
    void markActive(Block altar, @Nullable ItemStack refund);

    void clearActive(Block altar);
}
