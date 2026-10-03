package io.github.amitelia.occultech.items;

import java.util.Comparator;
import java.util.List;

import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.BlockUseHandler;

/**
 * A floor tile with an effect when walked on (see {@link CosmeticListener}). Tiles are meant to be laid in numbers, so
 * they have no ticker: nothing runs until someone steps on one. With more than one look, right-click cycles it.
 */
public class StepTile extends SlimefunItem {

    private final List<Material> looks;

    public StepTile(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, List<Material> looks) {
        super(group, item, type, recipe, output);
        this.looks = looks;

        if (looks.size() > 1) {
            addItemHandler((BlockUseHandler) e -> e.getClickedBlock().ifPresent(block -> {
                if (e.getPlayer().isSneaking()) {
                    return; // let players place blocks against tiles while sneaking
                }
                e.cancel();
                var skins = io.github.amitelia.occultech.Occultech.instance().skins();
                Material next;
                if (skins != null && skins.blocks().isCustom(getId())) {
                    // a custom block: the look is its state
                    CustomBlockService.Look now = skins.blocks().lookOf(block);
                    int look = ((now == null ? 0 : now.look()) + 1) % looks.size();
                    skins.blocks().place(block, getId(), look, null);
                    next = lookMaterial(look);
                } else {
                    int current = looks.indexOf(block.getType());
                    next = looks.get((current + 1) % looks.size());
                    // no physics: coral out of water must not be updated into dead coral
                    block.setBlockData(next.createBlockData(), false);
                    if (skins != null) {
                        skins.ensure(block);   // the skin follows the look
                    }
                }
                e.getPlayer().sendActionBar(MenuUtils.color("&d" + getItemName() + "&7: " + MenuUtils.pretty(next)));
            }));
        }
    }

    /**
     * The block skin variant for a look: 0 for the item's own block, then the other looks by name (the art pipeline
     * draws them in that order); -1 if the type isn't one of this tile's looks.
     */
    /** The look's material (its name in messages): the reverse of {@link #lookVariant}. */
    public Material lookMaterial(int variant) {
        Material own = getItem().getType();
        if (variant <= 0) {
            return own;
        }
        List<Material> others = looks.stream().filter(m -> m != own).sorted(Comparator.comparing(Material::name)).toList();
        return variant - 1 < others.size() ? others.get(variant - 1) : own;
    }

    public int lookVariant(Material type) {
        Material own = getItem().getType();
        if (type == own) {
            return 0;
        }
        List<Material> others = looks.stream().filter(m -> m != own).sorted(Comparator.comparing(Material::name)).toList();
        int index = others.indexOf(type);
        return index < 0 ? -1 : index + 1;
    }
}
