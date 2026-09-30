package io.github.amitelia.occultech.items;

import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.block.Block;
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
    protected void tick(Block block) {
        super.tick(block);
        if (getMachineProcessor().getOperation(block) != null) {
            workingParticles(block);
        }
    }

    /** Only while a recipe is running: forge fire for the Occult Forge, drifting souls for the Soul Condenser. */
    private void workingParticles(Block block) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        Location top = block.getLocation().add(0.5, 1.05, 0.5);
        if (progressIcon == Material.SOUL_SAND) {
            block.getWorld().spawnParticle(Particle.SOUL, top, 2, 0.25, 0.1, 0.25, 0.02);
            if (random.nextInt(3) == 0) {
                block.getWorld().spawnParticle(Particle.SCULK_SOUL, top.clone().add(0, 0.3, 0), 1, 0.2, 0.2, 0.2, 0.01);
            }
            block.getWorld().spawnParticle(Particle.DUST, top.clone().add(random.nextDouble(-0.5, 0.5), random.nextDouble(-0.9, 0), 0.52), 1,
                0, 0, 0, 0, new Particle.DustOptions(Color.fromRGB(90, 200, 230), 0.7F));
        } else {
            block.getWorld().spawnParticle(Particle.FLAME, top, 2, 0.2, 0.05, 0.2, 0.01);
            block.getWorld().spawnParticle(Particle.SMOKE, top.clone().add(0, 0.2, 0), 1, 0.15, 0.1, 0.15, 0.01);
            if (random.nextInt(4) == 0) {
                block.getWorld().spawnParticle(Particle.LAVA, top, 1);
            }
        }
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
