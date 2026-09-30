package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.OfflinePlayer;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.block.data.Ageable;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Item;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Monster;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.CreatureSpawnEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.implementation.Slimefun;
import io.github.thebusybiscuit.slimefun4.libraries.dough.protection.Interaction;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * Runs the work of every loaded Servitor Shrine: the contract's job, the floating spirit, the Frenzy Idol speed-up,
 * and the Ward contract's spawn blocking.
 * <p>
 * Shrines only work in loaded chunks, only where their owner may build, and stop when their store is full.
 * Nothing is simulated while unloaded.
 */
public final class ServitorService implements Listener {

    public static final String HARVEST = ItemKeys.slimefunId("HARVEST_CONTRACT");
    public static final String GATHER = ItemKeys.slimefunId("GATHER_CONTRACT");
    public static final String WARD = ItemKeys.slimefunId("WARD_CONTRACT");

    static final String OWNER_KEY = "occultech_owner";
    static final int MAX_PER_CHUNK = 4;
    private static final long ACTION_MS = 2000;
    private static final double IDOL_SPEEDUP = 1.5;
    private static final double IDOL_RANGE = 8;
    private static final int WORK_RADIUS = 4;
    private static final int WARD_RADIUS = 8;
    private static final long SEEN_TIMEOUT_MS = 5000;

    private static final Map<Material, Material> SEEDS = Map.of(Material.WHEAT, Material.WHEAT_SEEDS, Material.CARROTS, Material.CARROT,
        Material.POTATOES, Material.POTATO, Material.BEETROOTS, Material.BEETROOT_SEEDS, Material.NETHER_WART, Material.NETHER_WART,
        Material.COCOA, Material.COCOA_BEANS);

    private static final class Shrine {
        long lastSeen;
        long nextAction;
        String contract;
        ItemDisplay spirit;
    }

    private final Map<Location, Shrine> shrines = new HashMap<>();
    private final Map<Location, Long> idols = new HashMap<>();

    public ServitorService(Plugin plugin) {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::sweep, 100L, 100L);
    }

    /** Called by the shrine's ticker. Returns a status line for its hologram. */
    String tick(Block block, BlockMenu menu, int[] store, int contractSlot) {
        Shrine shrine = shrines.computeIfAbsent(block.getLocation(), l -> new Shrine());
        long now = System.currentTimeMillis();
        shrine.lastSeen = now;
        ItemStack contractItem = menu.getItemInSlot(contractSlot);
        shrine.contract = MenuUtils.keyOf(contractItem);
        ensureSpirit(block, shrine);

        if (shrine.contract == null || !(HARVEST.equals(shrine.contract) || GATHER.equals(shrine.contract) || WARD.equals(shrine.contract))) {
            return "&7Idle &8- &7insert a contract";
        }
        if (WARD.equals(shrine.contract)) {
            return "&aWarding &7(no hostile spawns within " + WARD_RADIUS + ")";
        }
        if (!hasRoom(menu, store)) {
            return "&cStore full";
        }
        if (now < shrine.nextAction) {
            return HARVEST.equals(shrine.contract) ? "&aHarvesting" : "&aGathering";
        }
        shrine.nextAction = now + (long) (ACTION_MS / (idolNearby(block.getLocation()) ? IDOL_SPEEDUP : 1));

        OfflinePlayer owner = owner(block);
        if (HARVEST.equals(shrine.contract)) {
            harvest(block, menu, store, shrine, owner);
            return "&aHarvesting";
        }
        gather(block, menu, store, shrine, owner);
        return "&aGathering";
    }

    void registerIdol(Location at) {
        idols.put(at, System.currentTimeMillis());
    }

    void removeIdol(Location at) {
        idols.remove(at);
    }

    void removeShrine(Location at) {
        Shrine shrine = shrines.remove(at);
        if (shrine != null && shrine.spirit != null) {
            shrine.spirit.remove();
        }
    }

    /** Shrines currently known in a chunk, for the per-chunk cap. */
    int countInChunk(Block block) {
        int count = 0;
        for (Location at : shrines.keySet()) {
            if (at.getWorld() == block.getWorld() && at.getBlockX() >> 4 == block.getX() >> 4 && at.getBlockZ() >> 4 == block.getZ() >> 4) {
                count++;
            }
        }
        return count;
    }

    /** True if a working Ward contract covers this spot. */
    public boolean isWarded(Location at) {
        long now = System.currentTimeMillis();
        for (Map.Entry<Location, Shrine> entry : shrines.entrySet()) {
            Location shrine = entry.getKey();
            Shrine state = entry.getValue();
            if (WARD.equals(state.contract) && now - state.lastSeen < SEEN_TIMEOUT_MS && shrine.getWorld() == at.getWorld()
                && Math.abs(shrine.getX() - at.getX()) <= WARD_RADIUS + 0.5 && Math.abs(shrine.getZ() - at.getZ()) <= WARD_RADIUS + 0.5
                && Math.abs(shrine.getY() - at.getY()) <= WARD_RADIUS) {
                return true;
            }
        }
        return false;
    }

    @EventHandler(ignoreCancelled = true)
    public void onSpawn(CreatureSpawnEvent e) {
        if (e.getSpawnReason() == CreatureSpawnEvent.SpawnReason.NATURAL && e.getEntity() instanceof Monster && isWarded(e.getLocation())) {
            e.setCancelled(true);
        }
    }

    // ------------------------------------------------------------------ jobs

    private void harvest(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        for (Block crop : area(shrineBlock, WORK_RADIUS, 1)) {
            if (!(crop.getBlockData() instanceof Ageable ageable)) {
                continue;
            }
            Material type = crop.getType();
            boolean berries = type == Material.SWEET_BERRY_BUSH;
            if ((!SEEDS.containsKey(type) && !berries) || ageable.getAge() < ageable.getMaximumAge() || !mayWork(owner, crop)) {
                continue;
            }

            List<ItemStack> drops = new ArrayList<>(crop.getDrops());
            if (berries) {
                drops = List.of(new ItemStack(Material.SWEET_BERRIES, 2 + (Math.random() < 0.5 ? 1 : 0)));
                ageable.setAge(1);
            } else {
                takeOne(drops, SEEDS.get(type));
                ageable.setAge(0);
            }
            crop.setBlockData(ageable);
            for (ItemStack drop : drops) {
                ItemStack rest = menu.pushItem(drop, store);
                if (rest != null) {
                    crop.getWorld().dropItemNaturally(crop.getLocation().add(0.5, 0.5, 0.5), rest);
                }
            }
            moveSpirit(shrine, crop.getLocation());
            crop.getWorld().spawnParticle(Particle.SOUL, crop.getLocation().add(0.5, 0.6, 0.5), 4, 0.2, 0.2, 0.2, 0.01);
            crop.getWorld().playSound(crop.getLocation(), Sound.BLOCK_CROP_BREAK, 0.6F, 1.4F);
            return;
        }
        moveSpirit(shrine, shrineBlock.getLocation());
    }

    private void gather(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        Location center = shrineBlock.getLocation().add(0.5, 0.5, 0.5);
        Collection<Entity> nearby = center.getWorld().getNearbyEntities(center, WORK_RADIUS + 0.5, 2, WORK_RADIUS + 0.5, e -> e instanceof Item);
        for (Entity entity : nearby) {
            Item item = (Item) entity;
            UUID itemOwner = item.getOwner();
            boolean ownedByOther = itemOwner != null && (owner == null || !itemOwner.equals(owner.getUniqueId()));
            if (item.getPickupDelay() > 0 || ownedByOther || !mayWork(owner, item.getLocation().getBlock())) {
                continue;
            }
            ItemStack rest = menu.pushItem(item.getItemStack().clone(), store);
            if (rest == null) {
                item.remove();
            } else {
                item.setItemStack(rest);
            }
            moveSpirit(shrine, item.getLocation().getBlock().getLocation());
            item.getWorld().spawnParticle(Particle.SOUL, item.getLocation(), 3, 0.1, 0.1, 0.1, 0.01);
            return;
        }
        moveSpirit(shrine, shrineBlock.getLocation());
    }

    // ------------------------------------------------------------------ helpers

    private boolean mayWork(@Nullable OfflinePlayer owner, Block block) {
        return owner != null && Slimefun.getProtectionManager().hasPermission(owner, block, Interaction.BREAK_BLOCK);
    }

    @Nullable
    private static OfflinePlayer owner(Block block) {
        String owner = BlockStorage.getLocationInfo(block.getLocation(), OWNER_KEY);
        try {
            return owner == null ? null : Bukkit.getOfflinePlayer(UUID.fromString(owner));
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    private boolean idolNearby(Location at) {
        long now = System.currentTimeMillis();
        for (Map.Entry<Location, Long> idol : idols.entrySet()) {
            if (now - idol.getValue() < SEEN_TIMEOUT_MS && idol.getKey().getWorld() == at.getWorld()
                && idol.getKey().distanceSquared(at) <= IDOL_RANGE * IDOL_RANGE) {
                return true;
            }
        }
        return false;
    }

    private static boolean hasRoom(BlockMenu menu, int[] store) {
        for (int slot : store) {
            ItemStack item = menu.getItemInSlot(slot);
            if (MenuUtils.isEmpty(item) || item.getAmount() < item.getMaxStackSize()) {
                return true;
            }
        }
        return false;
    }

    private static void takeOne(List<ItemStack> drops, Material seed) {
        for (Iterator<ItemStack> it = drops.iterator(); it.hasNext();) {
            ItemStack drop = it.next();
            if (drop.getType() == seed) {
                if (drop.getAmount() <= 1) {
                    it.remove();
                } else {
                    drop.setAmount(drop.getAmount() - 1);
                }
                return;
            }
        }
    }

    private static List<Block> area(Block center, int radius, int height) {
        List<Block> blocks = new ArrayList<>();
        for (int dy = -height; dy <= height; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    blocks.add(center.getRelative(dx, dy, dz));
                }
            }
        }
        return blocks;
    }

    private void ensureSpirit(Block block, Shrine shrine) {
        if (shrine.spirit != null && shrine.spirit.isValid()) {
            return;
        }
        shrine.spirit = block.getWorld().spawn(block.getLocation().add(0.5, 1.6, 0.5), ItemDisplay.class, d -> {
            d.setPersistent(false);
            d.setItemStack(new ItemStack(Material.HEART_OF_THE_SEA));
            d.setBillboard(Display.Billboard.CENTER);
            d.setTeleportDuration(20);
            d.setGlowing(true);
            d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(0.4F, 0.4F, 0.4F), new AxisAngle4f()));
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
        });
    }

    private static void moveSpirit(Shrine shrine, Location to) {
        if (shrine.spirit != null && shrine.spirit.isValid()) {
            shrine.spirit.teleport(to.clone().add(0.5, 1.6, 0.5));
        }
    }

    private void sweep() {
        long now = System.currentTimeMillis();
        shrines.entrySet().removeIf(entry -> {
            boolean gone = now - entry.getValue().lastSeen > SEEN_TIMEOUT_MS * 3
                || !entry.getKey().isChunkLoaded() || BlockStorage.checkID(entry.getKey()) == null;
            if (gone && entry.getValue().spirit != null) {
                entry.getValue().spirit.remove();
            }
            return gone;
        });
        idols.entrySet().removeIf(entry -> now - entry.getValue() > SEEN_TIMEOUT_MS * 3);
    }

    /** Removes every spirit display (plugin disable). */
    public void shutdown() {
        for (Shrine shrine : shrines.values()) {
            if (shrine.spirit != null) {
                shrine.spirit.remove();
            }
        }
        shrines.clear();
    }
}
