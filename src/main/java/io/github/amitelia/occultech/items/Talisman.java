package io.github.amitelia.occultech.items;

import org.bukkit.Sound;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/** A final talisman (see {@link TalismanService}): right-click cycles its style or turns it off. */
public class Talisman extends OccultItem {

    public Talisman(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, TalismanService.Kind kind) {
        super(group, item, type, recipe, output);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            var hand = e.getHand();
            ItemStack held = e.getPlayer().getInventory().getItem(hand);
            String style = TalismanService.cycle(held, kind);
            e.getPlayer().getInventory().setItem(hand, held);
            e.getPlayer().sendActionBar(MenuUtils.color("&d" + getItemName() + "&7: " + style));
            e.getPlayer().playSound(e.getPlayer().getLocation(), Sound.BLOCK_AMETHYST_BLOCK_CHIME, 0.8F, 1.4F);
        });
    }
}
