package io.github.amitelia.occultech.debug;

import javax.annotation.Nullable;

import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.inventory.ItemStack;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.items.OfferingBowl;
import io.github.amitelia.occultech.items.RitualAltar;
import io.github.amitelia.occultech.ritual.CirclePattern;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * Shared helpers for the self-test and the showcase: placing Slimefun blocks and filling circle menus.
 */
final class DebugWorld {

    interface Recorder {
        void record(Block block);
    }

    private DebugWorld() {}

    /** Places a registered Slimefun block (type + block storage). Returns false if the id isn't registered. */
    static boolean placeSlimefun(Block block, String id, Recorder recorder) {
        SlimefunItem item = SlimefunItem.getById(id);
        if (item == null) {
            return false;
        }
        recorder.record(block);
        block.setType(item.getItem().getType());
        BlockStorage.store(block, id);
        return true;
    }

    /** Builds the tier's circle centered on {@code altar} (all on the altar's layer). */
    static void buildCircle(Block altar, int tier, Recorder recorder) {
        CirclePattern pattern = Circles.forTier(tier);
        int r = pattern.radius();
        for (int dz = -r; dz <= r; dz++) {
            for (int dx = -r; dx <= r; dx++) {
                String glyph = pattern.glyphAt(dx, dz);
                if (glyph != null) {
                    placeSlimefun(altar.getRelative(dx, 0, dz), glyph, recorder);
                }
            }
        }
    }

    /** An item from an {@code ItemKeys} key (vanilla {@code mc:X} or a Slimefun id). */
    @Nullable
    static ItemStack item(String key, int amount) {
        ItemStack stack;
        if (ItemKeys.isVanilla(key)) {
            Material material = Material.matchMaterial(key.substring(ItemKeys.VANILLA.length()));
            if (material == null) {
                return null;
            }
            stack = new ItemStack(material);
        } else {
            SlimefunItem item = SlimefunItem.getById(key);
            if (item == null) {
                return null;
            }
            stack = item.getItem().clone();
        }
        stack.setAmount(amount);
        return stack;
    }

    static void setAltarCenter(Block altar, @Nullable ItemStack item) {
        BlockMenu menu = BlockStorage.getInventory(altar);
        if (menu != null) {
            menu.replaceExistingItem(RitualAltar.CENTER_SLOT, item);
        }
    }

    static void setBowl(Block bowl, @Nullable ItemStack item) {
        BlockMenu menu = BlockStorage.getInventory(bowl);
        if (menu != null) {
            menu.replaceExistingItem(OfferingBowl.SLOT, item);
        }
    }

    /** Empties the menu of a circle block before it is removed, so nothing drops. */
    static void emptyMenu(Block block) {
        String id = BlockStorage.checkID(block);
        if (Circles.OFFERING_BOWL.equals(id)) {
            setBowl(block, null);
        } else if (Circles.INITIATE_ALTAR.equals(id)) {
            setAltarCenter(block, null);
        }
    }
}
