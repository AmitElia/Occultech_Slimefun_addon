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
import org.bukkit.DyeColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.OfflinePlayer;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.block.BrewingStand;
import org.bukkit.block.data.Ageable;
import org.bukkit.block.data.type.Beehive;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Item;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Sheep;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.CreatureSpawnEvent;
import org.bukkit.inventory.BrewerInventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.PotionMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.potion.PotionType;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.thebusybiscuit.slimefun4.implementation.Slimefun;
import io.github.thebusybiscuit.slimefun4.libraries.dough.protection.Interaction;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * Runs the work of every loaded Servitor Shrine: the contract's job, the floating spirit, speed-ups, the Ward
 * contract's spawn blocking, and the placement cap.
 * <p>
 * Rules: shrines only work in loaded chunks, only where their owner may build, and never simulate unloaded time.
 * Speed: one action every 2s; a Frenzy Idol within 8 blocks makes it 1.5x faster (idols don't stack); empowering
 * with a Spirit Essence doubles the speed for an hour (stacks with the idol, so 3x at most).
 * At most {@value #MAX_NEARBY} shrines may stand within {@value #CAP_RADIUS} blocks of each other.
 */
public final class ServitorService implements Listener {

    /** The jobs a shrine can do, by contract item. */
    public enum Contract {
        HARVEST("HARVEST_CONTRACT", "Harvesting", 4),
        GATHER("GATHER_CONTRACT", "Gathering", 4),
        WARD("WARD_CONTRACT", "Warding", 8),
        BREWER("BREWER_CONTRACT", "Tending brews", 4),
        SHEPHERD("SHEPHERD_CONTRACT", "Shearing", 4),
        BEEKEEPER("BEEKEEPER_CONTRACT", "Keeping bees", 4),
        ACOLYTE("ACOLYTE_CONTRACT", "Serving the altar", 8);

        public final String itemId;
        public final String label;
        public final int radius;

        Contract(String id, String label, int radius) {
            this.itemId = ItemKeys.slimefunId(id);
            this.label = label;
            this.radius = radius;
        }

        @Nullable
        public static Contract of(@Nullable String itemId) {
            for (Contract contract : values()) {
                if (contract.itemId.equals(itemId)) {
                    return contract;
                }
            }
            return null;
        }
    }

    static final String OWNER_KEY = "occultech_owner";
    static final String EMPOWERED_KEY = "occultech_empowered_until";
    public static final int MAX_NEARBY = 4;
    public static final int CAP_RADIUS = 12;
    public static final long ACTION_MS = 2000;
    public static final long EMPOWER_MS = 60 * 60 * 1000L;
    private static final double IDOL_SPEEDUP = 1.5;
    private static final double EMPOWER_SPEEDUP = 2;
    private static final double IDOL_RANGE = 8;
    private static final long SEEN_TIMEOUT_MS = 5000;

    private static final Map<Material, Material> SEEDS = Map.of(Material.WHEAT, Material.WHEAT_SEEDS, Material.CARROTS, Material.CARROT,
        Material.POTATOES, Material.POTATO, Material.BEETROOTS, Material.BEETROOT_SEEDS, Material.NETHER_WART, Material.NETHER_WART,
        Material.COCOA, Material.COCOA_BEANS);

    private static final class Shrine {
        long lastSeen;
        long nextAction;
        Contract contract;
        ItemDisplay spirit;
    }

    private final Map<Location, Shrine> shrines = new HashMap<>();
    private final Map<Location, Long> idols = new HashMap<>();
    private RitualService rituals;

    public ServitorService(Plugin plugin) {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::sweep, 100L, 100L);
    }

    /** The Acolyte contract needs the ritual service (set after both exist). */
    public void setRituals(RitualService rituals) {
        this.rituals = rituals;
    }

    // ------------------------------------------------------------------ shrine lifecycle

    /** Called by the shrine's ticker. Returns a status line for its hologram. */
    String tick(Block block, BlockMenu menu, int[] store, int contractSlot) {
        Shrine shrine = register(block.getLocation());
        long now = System.currentTimeMillis();
        shrine.contract = Contract.of(MenuUtils.keyOf(menu.getItemInSlot(contractSlot)));
        ensureSpirit(block, shrine);

        String boost = speedLabel(block);
        if (shrine.contract == null) {
            return "&7Idle &8- &7insert a contract";
        }
        if (shrine.contract == Contract.WARD) {
            return "&aWarding &7(no hostile spawns within " + Contract.WARD.radius + ")";
        }
        boolean producer = shrine.contract != Contract.BREWER && shrine.contract != Contract.ACOLYTE;
        if (producer && !hasRoom(menu, store)) {
            return "&cStore full";
        }
        if (now < shrine.nextAction) {
            return "&a" + shrine.contract.label + boost;
        }
        shrine.nextAction = now + intervalMs(block);

        OfflinePlayer owner = owner(block);
        switch (shrine.contract) {
            case HARVEST -> harvest(block, menu, store, shrine, owner);
            case GATHER -> gather(block, menu, store, shrine, owner);
            case BREWER -> brew(block, menu, store, shrine, owner);
            case SHEPHERD -> shear(block, menu, store, shrine, owner);
            case BEEKEEPER -> keepBees(block, menu, store, shrine, owner);
            case ACOLYTE -> serveAltar(block, menu, store, shrine, owner);
            default -> { }
        }
        return "&a" + shrine.contract.label + boost;
    }

    private Shrine register(Location at) {
        Shrine shrine = shrines.computeIfAbsent(at, l -> new Shrine());
        shrine.lastSeen = System.currentTimeMillis();
        return shrine;
    }

    /** Registers a shrine the moment it is placed, so quick placements can't slip past the cap. */
    void onPlaced(Block block) {
        register(block.getLocation());
    }

    /** False if {@value #MAX_NEARBY} shrines already stand within {@value #CAP_RADIUS} blocks. */
    public boolean canPlace(Location at) {
        return nearbyShrines(at) < MAX_NEARBY;
    }

    public int nearbyShrines(Location at) {
        int count = 0;
        for (Location shrine : shrines.keySet()) {
            if (shrine.getWorld() == at.getWorld() && shrine.distanceSquared(at) <= CAP_RADIUS * CAP_RADIUS) {
                count++;
            }
        }
        return count;
    }

    void removeShrine(Location at) {
        Shrine shrine = shrines.remove(at);
        if (shrine != null && shrine.spirit != null) {
            shrine.spirit.remove();
        }
    }

    /** Self-test: counts a location as a shrine for the placement cap. */
    public void registerForTest(Location at) {
        register(at);
    }

    public void unregisterForTest(Location at) {
        shrines.remove(at);
    }

    // ------------------------------------------------------------------ speed: idols and empowering

    void registerIdol(Location at) {
        idols.put(at, System.currentTimeMillis());
    }

    void removeIdol(Location at) {
        idols.remove(at);
    }

    /** Milliseconds between actions for a shrine: 2000, /1.5 near a Frenzy Idol (never stacks), /2 when empowered. */
    public long intervalMs(Block shrine) {
        double speed = 1;
        if (idolNearby(shrine.getLocation())) {
            speed *= IDOL_SPEEDUP;
        }
        if (empoweredFor(shrine) > 0) {
            speed *= EMPOWER_SPEEDUP;
        }
        return (long) (ACTION_MS / speed);
    }

    /** Adds an hour of double speed (stacks up to 24 hours). */
    public void empower(Block shrine) {
        long now = System.currentTimeMillis();
        long until = Math.max(now, now + empoweredFor(shrine));
        until = Math.min(now + 24 * EMPOWER_MS, until + EMPOWER_MS);
        BlockStorage.addBlockInfo(shrine, EMPOWERED_KEY, String.valueOf(until));
    }

    /** Remaining empowered time in ms (0 if none). */
    public long empoweredFor(Block shrine) {
        String until = BlockStorage.getLocationInfo(shrine.getLocation(), EMPOWERED_KEY);
        if (until == null) {
            return 0;
        }
        try {
            return Math.max(0, Long.parseLong(until) - System.currentTimeMillis());
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private String speedLabel(Block block) {
        StringBuilder label = new StringBuilder();
        long empowered = empoweredFor(block);
        if (empowered > 0) {
            label.append(" &d(empowered ").append(empowered / 60000 + 1).append("m)");
        }
        if (idolNearby(block.getLocation())) {
            label.append(" &6(frenzied)");
        }
        return label.toString();
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

    // ------------------------------------------------------------------ ward

    /** True if a working Ward contract covers this spot. */
    public boolean isWarded(Location at) {
        long now = System.currentTimeMillis();
        int radius = Contract.WARD.radius;
        for (Map.Entry<Location, Shrine> entry : shrines.entrySet()) {
            Location shrine = entry.getKey();
            Shrine state = entry.getValue();
            if (state.contract == Contract.WARD && now - state.lastSeen < SEEN_TIMEOUT_MS && shrine.getWorld() == at.getWorld()
                && Math.abs(shrine.getX() - at.getX()) <= radius + 0.5 && Math.abs(shrine.getZ() - at.getZ()) <= radius + 0.5
                && Math.abs(shrine.getY() - at.getY()) <= radius) {
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
        for (Block crop : area(shrineBlock, Contract.HARVEST.radius, 1)) {
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
            storeAll(menu, store, drops, crop.getLocation());
            work(shrine, crop.getLocation(), Sound.BLOCK_CROP_BREAK);
            return;
        }
        rest(shrine, shrineBlock);
    }

    private void gather(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        Location center = shrineBlock.getLocation().add(0.5, 0.5, 0.5);
        int radius = Contract.GATHER.radius;
        Collection<Entity> nearby = center.getWorld().getNearbyEntities(center, radius + 0.5, 2, radius + 0.5, e -> e instanceof Item);
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
            work(shrine, item.getLocation().getBlock().getLocation(), Sound.ENTITY_ITEM_PICKUP);
            return;
        }
        rest(shrine, shrineBlock);
    }

    /** Brewer's Aid: fuel with blaze powder; add nether wart to stands holding only water bottles. From the store. */
    private void brew(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        for (Block block : area(shrineBlock, Contract.BREWER.radius, 1)) {
            if (block.getType() != Material.BREWING_STAND || !mayWork(owner, block) || !(block.getState() instanceof BrewingStand stand)) {
                continue;
            }
            BrewerInventory inventory = stand.getInventory();
            if ((inventory.getFuel() == null || inventory.getFuel().getType().isAir()) && stand.getFuelLevel() <= 0
                && takeFromStore(menu, store, Material.BLAZE_POWDER)) {
                inventory.setFuel(new ItemStack(Material.BLAZE_POWDER));
                work(shrine, block.getLocation(), Sound.BLOCK_BREWING_STAND_BREW);
                return;
            }
            boolean empty = inventory.getIngredient() == null || inventory.getIngredient().getType().isAir();
            if (empty && onlyWaterBottles(inventory) && takeFromStore(menu, store, Material.NETHER_WART)) {
                inventory.setIngredient(new ItemStack(Material.NETHER_WART));
                work(shrine, block.getLocation(), Sound.BLOCK_BREWING_STAND_BREW);
                return;
            }
        }
        rest(shrine, shrineBlock);
    }

    private void shear(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        Location center = shrineBlock.getLocation().add(0.5, 0.5, 0.5);
        int radius = Contract.SHEPHERD.radius;
        for (Entity entity : center.getWorld().getNearbyEntities(center, radius + 0.5, 2, radius + 0.5, e -> e instanceof Sheep)) {
            Sheep sheep = (Sheep) entity;
            if (sheep.isSheared() || !sheep.isAdult() || !mayWork(owner, sheep.getLocation().getBlock())) {
                continue;
            }
            sheep.setSheared(true);
            DyeColor color = sheep.getColor() == null ? DyeColor.WHITE : sheep.getColor();
            Material wool = Material.matchMaterial(color.name() + "_WOOL");
            storeAll(menu, store, List.of(new ItemStack(wool == null ? Material.WHITE_WOOL : wool, 1 + (int) (Math.random() * 3))), sheep.getLocation());
            work(shrine, sheep.getLocation().getBlock().getLocation(), Sound.ENTITY_SHEEP_SHEAR);
            return;
        }
        rest(shrine, shrineBlock);
    }

    /** Beekeeper: honeycomb from full hives and nests; no player action, so bees never get angry. */
    private void keepBees(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        for (Block block : area(shrineBlock, Contract.BEEKEEPER.radius, 1)) {
            if (!(block.getBlockData() instanceof Beehive hive) || hive.getHoneyLevel() < hive.getMaximumHoneyLevel() || !mayWork(owner, block)) {
                continue;
            }
            hive.setHoneyLevel(0);
            block.setBlockData(hive);
            storeAll(menu, store, List.of(new ItemStack(Material.HONEYCOMB, 3)), block.getLocation());
            work(shrine, block.getLocation(), Sound.BLOCK_BEEHIVE_SHEAR);
            return;
        }
        rest(shrine, shrineBlock);
    }

    /**
     * Acolyte: for each altar within 8 blocks, restock its bowls with the offerings of the last ritual done there, from
     * the shrine's store. Tops up bowls already holding the right item, else fills an empty bowl. Never starts a ritual,
     * and never touches a circle that is running a ritual or a fight.
     */
    private void serveAltar(Block shrineBlock, BlockMenu menu, int[] store, Shrine shrine, @Nullable OfflinePlayer owner) {
        if (rituals == null) {
            return;
        }
        int radius = Contract.ACOLYTE.radius;
        for (Block altar : area(shrineBlock, radius, 2)) {
            String id = BlockStorage.checkID(altar);
            if (id == null || Circles.tierOfAltar(id).isEmpty() || !mayWork(owner, altar) || rituals.isLocked(altar.getLocation())
                || rituals.bosses().fightAt(altar).isPresent()) {
                continue;
            }
            RitualRecipe last = rituals.lastRitual(altar);
            var check = rituals.checkCircle(altar);
            if (last == null || check.isEmpty() || !check.get().complete()) {
                continue;
            }
            List<Block> bowls = new ArrayList<>();
            for (int[] offset : check.get().pattern().positionsOf(Circles.OFFERING_BOWL, check.get().rotation())) {
                bowls.add(altar.getRelative(offset[0], 0, offset[1]));
            }
            for (Map.Entry<String, Integer> offering : last.offerings().entrySet()) {
                if (restock(menu, store, bowls, offering.getKey(), offering.getValue())) {
                    work(shrine, altar.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_CHIME);
                    return;
                }
            }
        }
        rest(shrine, shrineBlock);
    }

    /** Moves up to what one bowl still needs of {@code key} from the store into that bowl. True if anything moved. */
    private static boolean restock(BlockMenu store, int[] storeSlots, List<Block> bowls, String key, int needed) {
        BlockMenu target = null;
        int have = 0;
        for (Block bowl : bowls) {
            BlockMenu menu = BlockStorage.getInventory(bowl);
            ItemStack content = menu == null ? null : menu.getItemInSlot(OfferingBowl.SLOT);
            if (menu != null && !MenuUtils.isEmpty(content) && key.equals(MenuUtils.keyOf(content))) {
                target = menu;
                have = content.getAmount();
                break;
            }
        }
        if (target == null) {
            for (Block bowl : bowls) {
                BlockMenu menu = BlockStorage.getInventory(bowl);
                if (menu != null && MenuUtils.isEmpty(menu.getItemInSlot(OfferingBowl.SLOT))) {
                    target = menu;
                    break;
                }
            }
        }
        if (target == null || have >= needed) {
            return false;
        }
        int moved = 0;
        for (int slot : storeSlots) {
            ItemStack item = store.getItemInSlot(slot);
            if (MenuUtils.isEmpty(item) || !key.equals(MenuUtils.keyOf(item))) {
                continue;
            }
            int take = Math.min(item.getAmount(), needed - have - moved);
            ItemStack current = target.getItemInSlot(OfferingBowl.SLOT);
            ItemStack placed = MenuUtils.isEmpty(current) ? item.clone() : current.clone();
            placed.setAmount((MenuUtils.isEmpty(current) ? 0 : current.getAmount()) + take);
            target.replaceExistingItem(OfferingBowl.SLOT, placed);
            store.consumeItem(slot, take);
            moved += take;
            if (have + moved >= needed) {
                break;
            }
        }
        return moved > 0;
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

    private static boolean onlyWaterBottles(BrewerInventory inventory) {
        boolean any = false;
        for (int slot = 0; slot < 3; slot++) {
            ItemStack bottle = inventory.getItem(slot);
            if (bottle == null || bottle.getType().isAir()) {
                continue;
            }
            if (bottle.getType() != Material.POTION || !(bottle.getItemMeta() instanceof PotionMeta meta) || meta.getBasePotionType() != PotionType.WATER) {
                return false;
            }
            any = true;
        }
        return any;
    }

    private static boolean takeFromStore(BlockMenu menu, int[] store, Material type) {
        for (int slot : store) {
            ItemStack item = menu.getItemInSlot(slot);
            if (!MenuUtils.isEmpty(item) && item.getType() == type && io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem.getByItem(item) == null) {
                menu.consumeItem(slot, 1);
                return true;
            }
        }
        return false;
    }

    private static void storeAll(BlockMenu menu, int[] store, List<ItemStack> items, Location near) {
        for (ItemStack drop : items) {
            ItemStack rest = menu.pushItem(drop, store);
            if (rest != null) {
                near.getWorld().dropItemNaturally(near.clone().add(0.5, 0.5, 0.5), rest);
            }
        }
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

    private void work(Shrine shrine, Location at, Sound sound) {
        moveSpirit(shrine, at);
        at.getWorld().spawnParticle(Particle.SOUL, at.clone().add(0.5, 0.8, 0.5), 4, 0.2, 0.2, 0.2, 0.01);
        at.getWorld().playSound(at, sound, 0.6F, 1.3F);
    }

    private static void rest(Shrine shrine, Block shrineBlock) {
        moveSpirit(shrine, shrineBlock.getLocation());
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
