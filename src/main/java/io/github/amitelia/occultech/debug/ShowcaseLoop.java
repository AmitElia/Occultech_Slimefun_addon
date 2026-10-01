package io.github.amitelia.occultech.debug;

import java.io.File;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BrewingStand;
import org.bukkit.block.data.Ageable;
import org.bukkit.block.data.type.Beehive;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Item;
import org.bukkit.entity.Sheep;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.PotionMeta;
import org.bukkit.potion.PotionType;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.items.OccultMachine;
import io.github.amitelia.occultech.items.ServitorShrine;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.core.attributes.EnergyNetComponent;
import me.mrCookieSlime.Slimefun.Objects.SlimefunItem.abstractItems.MachineRecipe;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * Keeps the showcase demos running: every 10s it refills the demo machines' inputs and empties their outputs, and resets
 * each contract demo (ripe wart to harvest, items to gather, wool to shear, honey to collect, water bottles to brew,
 * bowls for the Acolyte to restock). Only touches blocks listed under {@code loops} in showcase.yml, and only in loaded
 * chunks; does nothing when there is no showcase.
 */
final class ShowcaseLoop {

    private static final String FILE = "showcase.yml";

    private final Occultech plugin;
    private long loadedAt = -1;
    private List<String> loops = List.of();
    private World world;

    ShowcaseLoop(Occultech plugin) {
        this.plugin = plugin;
        Bukkit.getScheduler().runTaskTimer(plugin, this::tick, 200L, 200L);
    }

    private void tick() {
        File file = new File(plugin.getDataFolder(), FILE);
        if (!file.exists()) {
            loops = List.of();
            loadedAt = -1;
            return;
        }
        if (file.lastModified() != loadedAt) {
            YamlConfiguration data = YamlConfiguration.loadConfiguration(file);
            world = Bukkit.getWorld(data.getString("world", Bukkit.getWorlds().get(0).getName()));
            loops = data.getStringList("loops");
            loadedAt = file.lastModified();
        }
        if (world == null) {
            return;
        }
        for (String entry : loops) {
            String[] parts = entry.split(";");
            int x = Integer.parseInt(parts[1]);
            int y = Integer.parseInt(parts[2]);
            int z = Integer.parseInt(parts[3]);
            if (!world.isChunkLoaded(x >> 4, z >> 4)) {
                continue;
            }
            Block block = world.getBlockAt(x, y, z);
            try {
                switch (parts[0]) {
                    case "MACHINE" -> machine(block);
                    case "CHARGE" -> charge(block);
                    case "HARVEST" -> ripen(block);
                    case "GATHER" -> scatter(block);
                    case "BREWER" -> refillStands(block);
                    case "SHEPHERD" -> regrowWool(block);
                    case "BEEKEEPER" -> fillHives(block);
                    case "ACOLYTE" -> emptyABowl(block, world.getBlockAt(Integer.parseInt(parts[4]), Integer.parseInt(parts[5]), Integer.parseInt(parts[6])));
                    default -> { }
                }
            } catch (RuntimeException e) {
                plugin.getLogger().fine("Showcase loop skipped " + entry + ": " + e);
            }
        }
    }

    /** Empties outputs and tops up the inputs of the machine's first recipe. */
    private static void machine(Block block) {
        if (!(BlockStorage.check(block) instanceof OccultMachine machine) || machine.getMachineRecipes().isEmpty()) {
            return;
        }
        BlockMenu menu = BlockStorage.getInventory(block);
        if (menu == null) {
            return;
        }
        for (int slot : machine.getOutputSlots()) {
            menu.replaceExistingItem(slot, null);
        }
        // top up any ingredient that ran short, so the machine never stalls on one used-up input
        MachineRecipe recipe = machine.getMachineRecipes().get(0);
        int[] inputs = machine.getInputSlots();
        ItemStack[] needed = recipe.getInput();
        for (int i = 0; i < needed.length && i < inputs.length; i++) {
            ItemStack have = menu.getItemInSlot(inputs[i]);
            if (have == null || have.getType().isAir() || have.getAmount() < needed[i].getAmount()) {
                ItemStack load = needed[i].clone();
                load.setAmount(Math.min(load.getMaxStackSize(), load.getAmount() * 3));
                menu.replaceExistingItem(inputs[i], load);
            }
        }
    }

    /** Without a generator in the showcase, the machines are kept charged directly. */
    private static void charge(Block block) {
        if (BlockStorage.check(block) instanceof EnergyNetComponent component && component.getCapacity() > 0) {
            component.setCharge(block.getLocation(), component.getCapacity());
        }
    }

    private static void ripen(Block shrine) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        for (int i = 0; i < 4; i++) {
            Block crop = shrine.getRelative(random.nextInt(-4, 5), 0, random.nextInt(-4, 5));
            if (crop.getBlockData() instanceof Ageable age && crop.getType() == Material.NETHER_WART) {
                age.setAge(age.getMaximumAge());
                crop.setBlockData(age, false);
            }
        }
    }

    private static void scatter(Block shrine) {
        boolean items = !shrine.getWorld().getNearbyEntities(shrine.getLocation(), 5, 3, 5, e -> e instanceof Item).isEmpty();
        if (!items) {
            ThreadLocalRandom random = ThreadLocalRandom.current();
            for (int i = 0; i < 3; i++) {
                Item item = shrine.getWorld().dropItem(shrine.getLocation().add(random.nextDouble(-3, 3) + 0.5, 0.6, random.nextDouble(-3, 3) + 0.5),
                    new ItemStack(Material.BONE, 2));
                item.setPickupDelay(0);
            }
        }
    }

    private static void refillStands(Block shrine) {
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                if (shrine.getRelative(dx, 0, dz).getState() instanceof BrewingStand stand) {
                    for (int slot = 0; slot < 3; slot++) {
                        ItemStack bottle = stand.getInventory().getItem(slot);
                        boolean water = bottle != null && bottle.getItemMeta() instanceof PotionMeta meta && meta.getBasePotionType() == PotionType.WATER;
                        if (!water && stand.getBrewingTime() == 0) {
                            stand.getInventory().setItem(slot, waterBottle());
                        }
                    }
                }
            }
        }
        BlockMenu menu = BlockStorage.getInventory(shrine);
        if (menu != null) {
            menu.pushItem(new ItemStack(Material.NETHER_WART, 2), ServitorShrine.STORE);
            menu.pushItem(new ItemStack(Material.BLAZE_POWDER, 1), ServitorShrine.STORE);
        }
    }

    private static ItemStack waterBottle() {
        ItemStack water = new ItemStack(Material.POTION);
        PotionMeta meta = (PotionMeta) water.getItemMeta();
        meta.setBasePotionType(PotionType.WATER);
        water.setItemMeta(meta);
        return water;
    }

    private static void regrowWool(Block shrine) {
        for (Entity entity : shrine.getWorld().getNearbyEntities(shrine.getLocation(), 5, 3, 5, e -> e instanceof Sheep)) {
            ((Sheep) entity).setSheared(false);
        }
    }

    private static void fillHives(Block shrine) {
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                Block block = shrine.getRelative(dx, 0, dz);
                if (block.getBlockData() instanceof Beehive hive && hive.getHoneyLevel() < hive.getMaximumHoneyLevel()) {
                    hive.setHoneyLevel(hive.getMaximumHoneyLevel());
                    block.setBlockData(hive, false);
                }
            }
        }
    }

    /** Moves one bowl's offering back into the Acolyte's store, so it always has something to restock. */
    private void emptyABowl(Block acolyte, Block altar) {
        BlockMenu store = BlockStorage.getInventory(acolyte);
        if (store == null) {
            return;
        }
        plugin.rituals().checkCircle(altar).ifPresent(check -> {
            List<int[]> bowls = check.pattern().positionsOf(io.github.amitelia.occultech.ritual.Circles.OFFERING_BOWL, check.rotation());
            for (int[] offset : bowls) {
                BlockMenu bowl = BlockStorage.getInventory(altar.getRelative(offset[0], 0, offset[1]));
                ItemStack offering = bowl == null ? null : bowl.getItemInSlot(io.github.amitelia.occultech.items.OfferingBowl.SLOT);
                if (offering != null && !offering.getType().isAir()) {
                    if (store.pushItem(offering.clone(), ServitorShrine.STORE) == null) {
                        bowl.replaceExistingItem(io.github.amitelia.occultech.items.OfferingBowl.SLOT, null);
                    }
                    return;
                }
            }
        });
    }

    /** Is this a power-network block that needs a Slimefun item placed (used by the showcase when building). */
    static boolean exists(String id) {
        return SlimefunItem.getById(id) != null;
    }
}
