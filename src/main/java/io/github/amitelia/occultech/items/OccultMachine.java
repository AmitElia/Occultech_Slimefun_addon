package io.github.amitelia.occultech.items;

import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import me.mrCookieSlime.Slimefun.Objects.SlimefunItem.abstractItems.AContainer;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenuPreset;

/**
 * Occultech's electric machines (Occult Forge, Soul Condenser). Standard Slimefun machines - energy, progress bar,
 * cargo and recipe matching come from {@link AContainer} - with four input slots, since forge recipes combine up to four
 * ingredients. Recipes are registered from recipes.yml by the registrar.
 */
public class OccultMachine extends AContainer {

    private static final int[] INPUTS = { 19, 20, 28, 29 };
    private static final int[] OUTPUTS = { 24, 25 };
    private static final int PROGRESS_SLOT = 22;

    private final String identifier;
    private final Material progressIcon;

    public OccultMachine(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output, String identifier,
        Material progressIcon, int capacity, int energyPerTick, int speed) {
        super(group, item, type, recipe, output);
        this.identifier = identifier;
        this.progressIcon = progressIcon;
        setCapacity(capacity);
        setEnergyConsumption(energyPerTick);
        setProcessingSpeed(speed);
    }

    @Override
    protected void constructMenu(BlockMenuPreset preset) {
        for (int slot = 0; slot < 36; slot++) {
            if (!contains(INPUTS, slot) && !contains(OUTPUTS, slot) && slot != PROGRESS_SLOT) {
                preset.drawBackground(new int[] { slot });
            }
        }
        preset.addItem(PROGRESS_SLOT, MenuUtils.icon(Material.BLACK_STAINED_GLASS_PANE, " "), (p, s, i, a) -> false);
    }

    @Override
    public int[] getInputSlots() {
        return INPUTS;
    }

    @Override
    public int[] getOutputSlots() {
        return OUTPUTS;
    }

    @Override
    public ItemStack getProgressBar() {
        // AContainer's constructor asks for this before our fields are set
        return new ItemStack(progressIcon == null ? Material.BLAZE_POWDER : progressIcon);
    }

    @Override
    public String getMachineIdentifier() {
        return identifier == null ? getId() : identifier;
    }

    @Override
    protected void registerDefaultRecipes() {
        // recipes come from recipes.yml (see ContentRegistrar)
    }

    private static boolean contains(int[] slots, int slot) {
        for (int s : slots) {
            if (s == slot) {
                return true;
            }
        }
        return false;
    }
}
