package io.github.amitelia.occultech.setup;

import org.bukkit.Material;

import io.github.amitelia.occultech.Occultech;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;

/**
 * Occultech's own recipe types, shown in the Slimefun guide.
 */
public final class OccultechRecipeTypes {

    public static final RecipeType RITUAL = new RecipeType(Occultech.key("ritual"),
        new SlimefunItemStack("OCCULTECH_RECIPE_RITUAL", Material.LODESTONE, "&5Occult Ritual",
            "", "&7Middle item: place it on the altar", "&7Others: one per Offering Bowl", "&7Then press &fBegin Ritual"));

    public static final RecipeType BOSS_DROP = new RecipeType(Occultech.key("boss_drop"),
        new SlimefunItemStack("OCCULTECH_RECIPE_BOSS_DROP", Material.WITHER_SKELETON_SKULL, "&4Boss Drop",
            "", "&7Dropped by the boss shown", "&7in the middle of the recipe"));

    private OccultechRecipeTypes() {}
}
