package io.github.amitelia.occultech.items;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.entity.TextDisplay;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.PlayerChangedWorldEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.SkullMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.BoundingBox;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.CSCoreLibPlugin.general.Inventory.ChestMenu;

/**
 * The final talismans. Each works while it's anywhere in the carrier's inventory and only ever affects its carrier.
 * <ul>
 * <li>Hollow Halo: a crown or halo of display entities circling above the head (smooth, client-animated). Right-click
 * opens the style menu: the plain Halo is always available, each other style unlocks after defeating its boss 5 times
 * (see {@link HaloStyle}). A locked style never shows, even on a traded talisman.</li>
 * <li>Wishbone Talisman: any size from a quarter to three times normal, chosen in its menu (right-click; sneak +
 * right-click turns it on or off). Size is otherwise cosmetic, with two perks: giants reach further (block and entity
 * reach grow with size), tiny carriers run faster. Step height follows size. The size eases in, never grows into a
 * ceiling, and is back to normal inside a boss fight's arena. Transient modifiers, never saved onto the player.</li>
 * <li>Aura Talisman: a light trail (prismatic sparks, petals, soul wisps) or footprints (ember, frost, rune, ink,
 * blossom) that fade away, or off. Right-click cycles.</li>
 * </ul>
 * Inventories are scanned once a second; effects are drawn from that.
 */
public final class TalismanService implements Listener {

    public enum Kind {
        HALO("HOLLOW_HALO"),
        WISHBONE("WISHBONE_TALISMAN", "&aOn", "&8Off"),
        AURA("AURA_TALISMAN", "&dPrismatic sparks", "&dPetals", "&3Soul wisps", "&6Ember steps", "&bFrost steps", "&5Rune steps",
            "&8Ink steps", "&dBlossom steps", "&8Off");

        final String id;
        final String[] styles;

        Kind(String id, String... styles) {
            this.id = ItemKeys.slimefunId(id);
            this.styles = styles;
        }

        boolean isOff(int style) {
            return style == styles.length - 1;
        }
    }

    public static final NamespacedKey STYLE = new NamespacedKey("occultech", "talisman_style");
    public static final NamespacedKey HALO_STYLE = new NamespacedKey("occultech", "halo_style");
    private static final NamespacedKey WISHBONE = new NamespacedKey("occultech", "wishbone");
    private static final NamespacedKey WISHBONE_STEP = new NamespacedKey("occultech", "wishbone_step");
    private static final NamespacedKey WISHBONE_BLOCK_REACH = new NamespacedKey("occultech", "wishbone_block_reach");
    private static final NamespacedKey WISHBONE_ENTITY_REACH = new NamespacedKey("occultech", "wishbone_entity_reach");
    private static final NamespacedKey WISHBONE_SPEED = new NamespacedKey("occultech", "wishbone_speed");
    /** On the talisman: the chosen size, and whether it's on. */
    public static final NamespacedKey WISHBONE_SIZE = new NamespacedKey("occultech", "wishbone_size");
    public static final NamespacedKey WISHBONE_ON = new NamespacedKey("occultech", "wishbone_on");
    public static final double MIN_SIZE = 0.25;
    public static final double MAX_SIZE = 3.0;
    /** The menu's sizes, tiny to colossal, and their names. */
    static final double[] SIZES = { 0.25, 0.33, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0 };
    private static final String[] SIZE_NAMES = { "Tiny", "Wee", "Half", "Small", "Normal", "Tall", "Big", "Giant", "Colossal" };
    private static final double SIZE_STEP = 0.05;
    /** Speed bonus per unit of size below normal: a quarter-size carrier runs 45% faster. */
    private static final double TINY_SPEED = 0.6;
    /** The talisman of a new or older (on/off) Wishbone: half size, as it always was. */
    private static final double DEFAULT_SIZE = 0.5;
    private static TalismanService instance;
    private static final int FIRST_FOOTPRINT = 3;
    private static final int FOOTPRINT_LIFE = 60;

    /** A halo being shown: its style and the display entities that make it. */
    private record Rig(HaloStyle style, List<Display> parts, List<HaloStyle.Part> partOf, List<Integer> indexOf) {}

    private record Footprint(Display display, long born, Color color, boolean rune) {}

    private final Map<UUID, int[]> active = new HashMap<>();
    private final Map<UUID, HaloStyle> haloOf = new HashMap<>();
    private final Map<UUID, Rig> rigs = new HashMap<>();
    private final Map<UUID, Location> lastPosition = new HashMap<>();
    private final Map<UUID, Location> lastStep = new HashMap<>();
    private final Map<UUID, Boolean> leftFoot = new HashMap<>();
    private final Map<UUID, Deque<Footprint>> footprints = new HashMap<>();
    /** Wishbone: each carrier's size now and the size it's easing towards. */
    private final Map<UUID, Double> sizeNow = new HashMap<>();
    private final Map<UUID, Double> sizeWanted = new HashMap<>();
    private long ticks;

    public TalismanService(Plugin plugin) {
        instance = this;
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::scan, 20L, 20L);
        Bukkit.getScheduler().runTaskTimer(plugin, this::draw, 2L, 2L);
    }

    public static int styleOf(ItemStack item) {
        return item.hasItemMeta() ? item.getItemMeta().getPersistentDataContainer().getOrDefault(STYLE, PersistentDataType.INTEGER, 0) : 0;
    }

    /** Right-click: next style. Returns its name. */
    static String cycle(ItemStack item, Kind kind) {
        int next = (styleOf(item) + 1) % kind.styles.length;
        var meta = item.getItemMeta();
        meta.getPersistentDataContainer().set(STYLE, PersistentDataType.INTEGER, next);
        item.setItemMeta(meta);
        return kind.styles[next];
    }

    // ------------------------------------------------------------------ halo style menu

    /** The style menu: unlocked styles to choose, locked ones with their progress. */
    static void openHaloMenu(Player player, ItemStack talisman) {
        ChestMenu menu = new ChestMenu(MenuUtils.color("&6Hollow Halo styles"));
        menu.setEmptySlotsClickable(false);
        menu.setPlayerInventoryClickable(true);
        HaloStyle[] styles = HaloStyle.values();
        String current = talisman.hasItemMeta() ? talisman.getItemMeta().getPersistentDataContainer().get(HALO_STYLE, PersistentDataType.STRING) : null;
        for (int i = 0; i < styles.length && i < 45; i++) {
            HaloStyle style = styles[i];
            boolean open = style.unlockedFor(player);
            ItemStack icon;
            if (open) {
                icon = MenuUtils.icon(style.icon, style.label, style.name().equals(current) ? "&aWearing" : "&eClick to wear");
            } else {
                int wins = io.github.amitelia.occultech.core.Keys.winsOf(player, style.boss);
                icon = MenuUtils.icon(Material.GRAY_DYE, "&8" + org.bukkit.ChatColor.stripColor(MenuUtils.color(style.label)),
                    "&7Locked: defeat " + io.github.amitelia.occultech.setup.ContentRegistrar.title(style.boss) + " "
                        + HaloStyle.WINS_TO_UNLOCK + " times", "&7Progress: &f" + Math.min(wins, HaloStyle.WINS_TO_UNLOCK) + "/" + HaloStyle.WINS_TO_UNLOCK);
            }
            menu.addItem(i, icon, (p, slot, item, action) -> {
                if (style.unlockedFor(p)) {
                    setHalo(p, style.name());
                    p.sendMessage(MenuUtils.color("&6Hollow Halo: " + style.label));
                    p.playSound(p.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_CHIME, 1F, 1.2F);
                    p.closeInventory();
                } else {
                    p.playSound(p.getLocation(), Sound.BLOCK_NOTE_BLOCK_BASS, 1F, 0.6F);
                }
                return false;
            });
        }
        menu.addItem(49, MenuUtils.icon(Material.BARRIER, "&8Off", "&7Hide the halo"), (p, slot, item, action) -> {
            setHalo(p, "OFF");
            p.closeInventory();
            return false;
        });
        menu.open(player);
    }

    // ------------------------------------------------------------------ wishbone size menu

    /** What a size does: ADD_SCALAR amounts for scale, step height, reach (giants only) and speed (tiny only). */
    public record SizePerks(double scale, double step, double reach, double speed) {}

    public static SizePerks perks(double size) {
        return new SizePerks(size - 1, size - 1, Math.max(0, size - 1), size < 1 ? (1 - size) * TINY_SPEED : 0);
    }

    /** A Wishbone Talisman's chosen size (half, for a new one or one from before the menu). */
    public static double sizeOf(ItemStack item) {
        Double size = item.hasItemMeta() ? item.getItemMeta().getPersistentDataContainer().get(WISHBONE_SIZE, PersistentDataType.DOUBLE) : null;
        return size == null ? DEFAULT_SIZE : Math.max(MIN_SIZE, Math.min(MAX_SIZE, size));
    }

    /** Whether a Wishbone Talisman is on (an older one: unless its on/off style was off). */
    public static boolean isOn(ItemStack item) {
        Byte on = item.hasItemMeta() ? item.getItemMeta().getPersistentDataContainer().get(WISHBONE_ON, PersistentDataType.BYTE) : null;
        return on == null ? !Kind.WISHBONE.isOff(styleOf(item)) : on == 1;
    }

    /** Stores a size and on/off on a Wishbone Talisman. */
    public static void setWishbone(ItemStack item, double size, boolean on) {
        var meta = item.getItemMeta();
        meta.getPersistentDataContainer().set(WISHBONE_SIZE, PersistentDataType.DOUBLE, Math.round(Math.max(MIN_SIZE, Math.min(MAX_SIZE, size)) * 100) / 100.0);
        meta.getPersistentDataContainer().set(WISHBONE_ON, PersistentDataType.BYTE, (byte) (on ? 1 : 0));
        item.setItemMeta(meta);
    }

    private static String sizeLabel(double size) {
        for (int i = 0; i < SIZES.length; i++) {
            if (Math.abs(SIZES[i] - size) < 0.005) {
                return SIZE_NAMES[i] + " (" + trim(size) + "x)";
            }
        }
        return trim(size) + "x";
    }

    private static String trim(double size) {
        return size == Math.rint(size) ? String.valueOf((int) size) : String.valueOf(Math.round(size * 100) / 100.0);
    }

    /** The first Wishbone Talisman in a player's inventory (the one that works), or null. */
    @Nullable
    private static ItemStack wishboneOf(Player player) {
        for (ItemStack item : player.getInventory().getContents()) {
            SlimefunItem sf = item == null || item.getType().isAir() ? null : SlimefunItem.getByItem(item);
            if (sf != null && sf.getId().equals(Kind.WISHBONE.id)) {
                return item;
            }
        }
        return null;
    }

    /** Sneak + right-click: on or off, keeping the chosen size. */
    static String toggleWishbone(Player player) {
        ItemStack talisman = wishboneOf(player);
        if (talisman == null) {
            return "&8no talisman";
        }
        boolean on = !isOn(talisman);
        setWishbone(talisman, sizeOf(talisman), on);
        refresh(player);
        return on ? "&a" + sizeLabel(sizeOf(talisman)) : "&8Off";
    }

    /** The size menu: the sizes tiny to colossal (you, at each), fine steps, normal, on/off. */
    static void openWishboneMenu(Player player) {
        ItemStack talisman = wishboneOf(player);
        if (talisman == null) {
            return;
        }
        double size = sizeOf(talisman);
        boolean on = isOn(talisman);
        ChestMenu menu = new ChestMenu(MenuUtils.color("&aWishbone Talisman &8- " + (on ? sizeLabel(size) : "off")));
        menu.setEmptySlotsClickable(false);
        menu.setPlayerInventoryClickable(true);
        for (int i = 0; i < SIZES.length; i++) {
            double choice = SIZES[i];
            boolean current = on && Math.abs(choice - size) < 0.005;
            ItemStack icon = new ItemStack(Material.PLAYER_HEAD, Math.max(1, Math.min(9, i + 1)));
            if (icon.getItemMeta() instanceof SkullMeta skull) {
                skull.setOwningPlayer(player);
                skull.setDisplayName(MenuUtils.color((current ? "&a" : "&f") + sizeLabel(choice)));
                skull.setLore(java.util.List.of(MenuUtils.color(current ? "&aYour size" : "&eClick to become this size"),
                    MenuUtils.color(choice > 1 ? "&7Reach x" + trim(choice) : choice < 1 ? "&7Runs " + Math.round(perks(choice).speed() * 100) + "% faster" : "&7As you are")));
                skull.setEnchantmentGlintOverride(current);
                icon.setItemMeta(skull);
            }
            menu.addItem(9 + i, icon, (p, slot, item, action) -> choose(p, choice, true));
        }
        menu.addItem(20, MenuUtils.icon(Material.RED_STAINED_GLASS_PANE, "&cSmaller", "&7-" + trim(SIZE_STEP) + "x"),
            (p, slot, item, action) -> choose(p, size - SIZE_STEP, true));
        menu.addItem(22, MenuUtils.icon(Material.RABBIT_FOOT, "&f" + (on ? sizeLabel(size) : "Off"),
            "&7Quarter size to three times normal.", "&7Giants reach further; tiny runs faster.", "&7Normal size inside boss fights.",
            "&8Sneak + right-click the talisman: on/off"), (p, slot, item, action) -> false);
        menu.addItem(24, MenuUtils.icon(Material.LIME_STAINED_GLASS_PANE, "&aBigger", "&7+" + trim(SIZE_STEP) + "x"),
            (p, slot, item, action) -> choose(p, size + SIZE_STEP, true));
        menu.addItem(26, MenuUtils.icon(on ? Material.LEVER : Material.BARRIER, on ? "&aOn" : "&8Off", "&7Click to turn " + (on ? "off" : "on")),
            (p, slot, item, action) -> choose(p, size, !on));
        menu.open(player);
    }

    private static boolean choose(Player player, double size, boolean on) {
        ItemStack talisman = wishboneOf(player);
        if (talisman != null) {
            setWishbone(talisman, size, on);
            refresh(player);
            player.playSound(player.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_CHIME, 0.8F, (float) Math.max(0.5, Math.min(2.0, 1.4 / Math.sqrt(sizeOf(talisman)))));
            // redraw with the new choice, a tick later (opening a menu from inside a click confuses the client)
            Bukkit.getScheduler().runTask(io.github.amitelia.occultech.Occultech.instance(), () -> openWishboneMenu(player));
        }
        return false;
    }

    /** Takes a menu choice now, not at the next scan. */
    private static void refresh(Player player) {
        if (instance != null) {
            instance.wantSize(player);
        }
    }

    /** Stores the chosen style on the carrier's Hollow Halo. */
    private static void setHalo(Player player, String style) {
        for (ItemStack item : player.getInventory().getContents()) {
            SlimefunItem sf = item == null || item.getType().isAir() ? null : SlimefunItem.getByItem(item);
            if (sf != null && sf.getId().equals(Kind.HALO.id)) {
                var meta = item.getItemMeta();
                meta.getPersistentDataContainer().set(HALO_STYLE, PersistentDataType.STRING, style);
                item.setItemMeta(meta);
                return;
            }
        }
    }

    // ------------------------------------------------------------------ scan

    private void scan() {
        for (Player player : Bukkit.getOnlinePlayers()) {
            int[] styles = { -1, -1, -1 };
            HaloStyle halo = null;
            for (ItemStack item : player.getInventory().getContents()) {
                if (item == null || item.getType().isAir()) {
                    continue;
                }
                SlimefunItem sfItem = SlimefunItem.getByItem(item);
                if (sfItem == null) {
                    continue;
                }
                if (sfItem.getId().equals(Kind.HALO.id) && styles[0] < 0) {
                    String chosen = item.hasItemMeta() ? item.getItemMeta().getPersistentDataContainer().get(HALO_STYLE, PersistentDataType.STRING) : null;
                    if (!"OFF".equals(chosen)) {
                        HaloStyle style = HaloStyle.byName(chosen);
                        // a locked style (e.g. a traded talisman) falls back to the plain Halo
                        halo = style.unlockedFor(player) ? style : HaloStyle.HALO;
                        styles[0] = 0;
                    }
                }
                for (Kind kind : new Kind[] { Kind.WISHBONE, Kind.AURA }) {
                    if (kind.id.equals(sfItem.getId()) && styles[kind.ordinal()] < 0) {
                        int style = styleOf(item);
                        styles[kind.ordinal()] = kind.isOff(style) ? -1 : style;
                    }
                }
            }
            active.put(player.getUniqueId(), styles);
            if (halo == null) {
                haloOf.remove(player.getUniqueId());
            } else {
                haloOf.put(player.getUniqueId(), halo);
            }
            wantSize(player);
        }
    }

    // ------------------------------------------------------------------ draw (every 2 ticks)

    private void draw() {
        ticks += 2;
        easeSizes();
        for (Player player : Bukkit.getOnlinePlayers()) {
            UUID id = player.getUniqueId();
            HaloStyle halo = player.isDead() || player.getGameMode() == org.bukkit.GameMode.SPECTATOR ? null : haloOf.get(id);
            drawHalo(player, halo);
            int[] styles = active.get(id);
            if (styles == null || player.isDead()) {
                continue;
            }
            Location here = player.getLocation();
            Location before = lastPosition.put(id, here);
            boolean moving = before != null && before.getWorld() == here.getWorld() && before.distanceSquared(here) > 0.004;
            int aura = styles[Kind.AURA.ordinal()];
            if (aura >= 0 && aura < FIRST_FOOTPRINT && moving && ticks % 4 == 0) {
                trail(player, aura);
            } else if (aura >= FIRST_FOOTPRINT && player.isOnGround()) {
                footstep(player, aura);
            }
        }
        fadeFootprints();
    }

    private void drawHalo(Player player, @Nullable HaloStyle style) {
        UUID id = player.getUniqueId();
        Rig rig = rigs.get(id);
        if (rig != null && (style != rig.style() || rig.parts().stream().anyMatch(d -> !d.isValid() || d.getWorld() != player.getWorld()))) {
            removeRig(id);
            rig = null;
        }
        if (style == null) {
            return;
        }
        if (rig == null) {
            rig = buildRig(player, style);
            rigs.put(id, rig);
        }
        double scale = player.getAttribute(Attribute.SCALE) == null ? 1 : player.getAttribute(Attribute.SCALE).getValue();
        Location top = player.getEyeLocation().add(0, 0.55 * scale, 0);
        top.setPitch(0);
        for (int i = 0; i < rig.parts().size(); i++) {
            HaloStyle.Part part = rig.partOf().get(i);
            int index = rig.indexOf().get(i);
            double angle = ticks * 0.05 * part.speed() + Math.PI * 2 * index / Math.max(1, part.count());
            double bob = Math.sin(ticks * 0.08 + index) * 0.02;
            Location spot = top.clone().add(Math.cos(angle) * part.radius() * scale, bob, Math.sin(angle) * part.radius() * scale);
            spot.setYaw((float) Math.toDegrees(angle) + 90);
            rig.parts().get(i).teleport(spot);
        }
        if (style.particle != null && ticks % 10 == 0) {
            player.getWorld().spawnParticle(style.particle, top, 1, 0.25 * scale, 0.05, 0.25 * scale, 0.01);
        }
        if (style.drawsStar() && ticks % 2 == 0) {
            pentagram(top.clone().add(0, 0.02, 0), 0.5 * scale, ticks * 0.04);
        }
    }

    private Rig buildRig(Player player, HaloStyle style) {
        List<Display> parts = new ArrayList<>();
        List<HaloStyle.Part> partOf = new ArrayList<>();
        List<Integer> indexOf = new ArrayList<>();
        Location at = player.getEyeLocation().add(0, 0.55, 0);
        for (HaloStyle.Part part : style.parts) {
            for (int i = 0; i < part.count(); i++) {
                Display display;
                if (part.text() != null) {
                    display = player.getWorld().spawn(at, TextDisplay.class, d -> {
                        d.setText(MenuUtils.color(part.text()));
                        d.setBillboard(Display.Billboard.CENTER);
                        d.setBackgroundColor(Color.fromARGB(0, 0, 0, 0));
                        d.setShadowed(false);
                    });
                } else {
                    ItemStack look = new ItemStack(part.item());
                    if (part.item() == Material.PLAYER_HEAD && look.getItemMeta() instanceof SkullMeta skull) {
                        skull.setOwningPlayer(player);
                        look.setItemMeta(skull);
                    }
                    display = player.getWorld().spawn(at, ItemDisplay.class, d -> {
                        d.setItemStack(look);
                        d.setBillboard(Display.Billboard.FIXED);
                    });
                }
                float s = (float) part.scale();
                display.setPersistent(false);
                display.setTeleportDuration(3);
                display.setBrightness(new Display.Brightness(15, 15));
                display.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(s, s, s), new AxisAngle4f()));
                display.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
                parts.add(display);
                partOf.add(part);
                indexOf.add(i);
            }
        }
        return new Rig(style, parts, partOf, indexOf);
    }

    /** Two circles and a turning five-pointed star, in particles, over the head. */
    private static void pentagram(Location center, double radius, double spin) {
        Particle.DustOptions red = new Particle.DustOptions(HaloStyle.starColor(), 0.45F);
        Particle.DustOptions dark = new Particle.DustOptions(Color.fromRGB(40, 0, 10), 0.4F);
        for (int i = 0; i < 16; i++) {
            double a = -spin + Math.PI * 2 * i / 16;
            center.getWorld().spawnParticle(Particle.DUST, center.clone().add(Math.cos(a) * radius, 0, Math.sin(a) * radius), 1, 0, 0, 0, 0, dark);
        }
        for (int i = 0; i < 5; i++) {
            double a1 = spin + Math.PI * 2 * i / 5;
            double a2 = spin + Math.PI * 2 * ((i + 2) % 5) / 5;
            for (double t = 0; t <= 1; t += 0.25) {
                double x = Math.cos(a1) * (1 - t) + Math.cos(a2) * t;
                double z = Math.sin(a1) * (1 - t) + Math.sin(a2) * t;
                center.getWorld().spawnParticle(Particle.DUST, center.clone().add(x * radius * 0.92, 0, z * radius * 0.92), 1, 0, 0, 0, 0, red);
            }
        }
    }

    private void removeRig(UUID id) {
        Rig rig = rigs.remove(id);
        if (rig != null) {
            rig.parts().forEach(Display::remove);
        }
    }

    // ------------------------------------------------------------------ aura: trails and footprints

    private void trail(Player player, int style) {
        Location feet = player.getLocation().add(0, 0.1, 0);
        switch (style) {
            case 0 -> {
                java.awt.Color rgb = java.awt.Color.getHSBColor((ticks % 120) / 120F, 0.8F, 1F);
                player.getWorld().spawnParticle(Particle.DUST, feet, 3, 0.15, 0.05, 0.15, 0,
                    new Particle.DustOptions(Color.fromRGB(rgb.getRed(), rgb.getGreen(), rgb.getBlue()), 0.9F));
            }
            case 1 -> player.getWorld().spawnParticle(Particle.CHERRY_LEAVES, feet.clone().add(0, 0.4, 0), 2, 0.2, 0.1, 0.2, 0);
            default -> player.getWorld().spawnParticle(Particle.SOUL, feet, 2, 0.15, 0.05, 0.15, 0.01);
        }
    }

    /** Every ~0.8 blocks walked, a footprint (alternating feet) that fades away, with a burst of particles. */
    private void footstep(Player player, int style) {
        UUID id = player.getUniqueId();
        Location here = player.getLocation();
        Location last = lastStep.get(id);
        if (last != null && last.getWorld() == here.getWorld() && last.distanceSquared(here) < 0.64) {
            return;
        }
        lastStep.put(id, here);
        boolean left = !leftFoot.getOrDefault(id, false);
        leftFoot.put(id, left);
        float yaw = here.getYaw();
        Vector side = new Vector(Math.cos(Math.toRadians(yaw)), 0, Math.sin(Math.toRadians(yaw))).multiply(left ? 0.16 : -0.16);
        Location spot = here.clone().add(side);
        spot.setY(Math.floor(here.getY() + 0.01) + 0.02);
        spot.setYaw(0);
        spot.setPitch(0);

        Color color;
        Particle particle;
        String rune = null;
        switch (style) {
            case 3 -> { color = Color.fromRGB(255, 120, 20); particle = Particle.FLAME; }
            case 4 -> { color = Color.fromRGB(170, 230, 255); particle = Particle.SNOWFLAKE; }
            case 5 -> { color = Color.fromRGB(170, 80, 255); particle = Particle.ENCHANT; rune = "ᚱᚠᛟᚨᚲᛉ".substring((int) (ticks / 2 % 6), (int) (ticks / 2 % 6) + 1); }
            case 6 -> { color = Color.fromRGB(15, 10, 20); particle = Particle.SQUID_INK; }
            default -> { color = Color.fromRGB(255, 150, 200); particle = Particle.CHERRY_LEAVES; }
        }
        String glyph = rune;
        Quaternionf flat = new Quaternionf().rotateY((float) Math.toRadians(-yaw)).rotateX((float) (-Math.PI / 2));
        TextDisplay print = player.getWorld().spawn(spot, TextDisplay.class, d -> {
            d.setPersistent(false);
            d.setBillboard(Display.Billboard.FIXED);
            d.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
            if (glyph != null) {
                d.setText(MenuUtils.color("&d") + glyph);
                d.setBackgroundColor(Color.fromARGB(0, 0, 0, 0));
                d.setBrightness(new Display.Brightness(15, 15));
                d.setTransformation(new Transformation(new Vector3f(), flat, new Vector3f(1.6F, 1.6F, 1.6F), new Quaternionf()));
            } else {
                d.setText(" ");
                d.setBackgroundColor(Color.fromARGB(210, color.getRed(), color.getGreen(), color.getBlue()));
                d.setTransformation(new Transformation(new Vector3f(), flat, new Vector3f(1.4F, 1.9F, 1F), new Quaternionf()));
            }
        });
        footprints.computeIfAbsent(id, k -> new ArrayDeque<>()).addLast(new Footprint(print, ticks, color, glyph != null));
        Deque<Footprint> mine = footprints.get(id);
        while (mine.size() > 10) {
            mine.removeFirst().display().remove();
        }
        ThreadLocalRandom random = ThreadLocalRandom.current();
        player.getWorld().spawnParticle(particle, spot.clone().add(0, 0.1, 0), 6, 0.12, 0.05, 0.12, particle == Particle.ENCHANT ? 0.6 : 0.01);
        if (style == 3 && random.nextBoolean()) {
            player.getWorld().spawnParticle(Particle.SMOKE, spot.clone().add(0, 0.2, 0), 2, 0.1, 0.05, 0.1, 0.01);
        }
    }

    /** Footprints fade over 3 seconds, then vanish. */
    private void fadeFootprints() {
        for (Iterator<Map.Entry<UUID, Deque<Footprint>>> it = footprints.entrySet().iterator(); it.hasNext();) {
            Deque<Footprint> prints = it.next().getValue();
            prints.removeIf(print -> {
                long age = ticks - print.born();
                if (age >= FOOTPRINT_LIFE || !print.display().isValid()) {
                    print.display().remove();
                    return true;
                }
                if (age % 10 == 0 && print.display() instanceof TextDisplay text) {
                    double left = 1 - age / (double) FOOTPRINT_LIFE;
                    if (print.rune()) {
                        text.setTextOpacity((byte) Math.max(20, (int) (255 * left)));
                    } else {
                        Color c = print.color();
                        text.setBackgroundColor(Color.fromARGB((int) (210 * left), c.getRed(), c.getGreen(), c.getBlue()));
                    }
                }
                return false;
            });
            if (prints.isEmpty()) {
                it.remove();
            }
        }
    }

    // ------------------------------------------------------------------ size

    /** The size a player should be: their talisman's, if it's on - normal inside a boss fight's arena. */
    private void wantSize(Player player) {
        ItemStack talisman = wishboneOf(player);
        double wanted = talisman == null || !isOn(talisman) || inFight(player) ? 1.0 : sizeOf(talisman);
        Double before = sizeWanted.put(player.getUniqueId(), wanted);
        if (before != null && Math.abs(before - wanted) > 0.005 && !player.isDead()) {
            // a change begins: a snap, and a puff of sparkles
            player.getWorld().playSound(player.getLocation(), Sound.ENTITY_ALLAY_ITEM_TAKEN, 0.7F, wanted < before ? 1.6F : 0.7F);
            player.getWorld().spawnParticle(Particle.END_ROD, player.getLocation().add(0, player.getHeight() / 2, 0), 12,
                0.3 * player.getWidth() / 0.6, player.getHeight() / 3, 0.3 * player.getWidth() / 0.6, 0.02);
        }
    }

    /** A size or reach advantage would bend a boss fight's balance: everyone fights at their own size. */
    private static boolean inFight(Player player) {
        var plugin = io.github.amitelia.occultech.Occultech.instance();
        if (plugin == null || plugin.rituals() == null) {
            return false;
        }
        for (var fight : plugin.rituals().bosses().fights()) {
            if (!fight.isOver() && fight.inArena(player)) {
                return true;
            }
        }
        return false;
    }

    /** Every 2 ticks: each carrier's size eases a step towards the wanted one (growing only where there's room). */
    private void easeSizes() {
        for (Player player : Bukkit.getOnlinePlayers()) {
            UUID id = player.getUniqueId();
            double wanted = sizeWanted.getOrDefault(id, 1.0);
            double now = sizeNow.getOrDefault(id, 1.0);
            double next = now;
            if (Math.abs(wanted - now) > 0.005) {
                double step = (wanted - now) * 0.3;
                next = Math.abs(step) < 0.02 ? (Math.abs(wanted - now) < 0.02 ? wanted : now + Math.signum(step) * 0.02) : now + step;
                if (next > now && !roomFor(player, next)) {
                    next = now;   // a ceiling or wall in the way: stay this size until there's room
                }
            }
            applySize(player, next);
            if (Math.abs(next - 1.0) < 0.005 && Math.abs(wanted - 1.0) < 0.005) {
                sizeNow.remove(id);
                sizeWanted.remove(id);
            } else {
                sizeNow.put(id, next);
            }
        }
    }

    /** Whether a player of this size fits where they stand. */
    private static boolean roomFor(Player player, double size) {
        Location at = player.getLocation();
        double half = 0.3 * size;
        double height = (player.isSneaking() ? 1.5 : 1.8) * size;
        return !player.getWorld().hasCollisionsIn(new BoundingBox(at.getX() - half, at.getY() + 0.01, at.getZ() - half,
            at.getX() + half, at.getY() + height, at.getZ() + half));
    }

    private static void applySize(Player player, double size) {
        SizePerks perks = perks(size);
        setModifier(player, Attribute.SCALE, WISHBONE, perks.scale());
        setModifier(player, Attribute.STEP_HEIGHT, WISHBONE_STEP, perks.step());
        setModifier(player, Attribute.BLOCK_INTERACTION_RANGE, WISHBONE_BLOCK_REACH, perks.reach());
        setModifier(player, Attribute.ENTITY_INTERACTION_RANGE, WISHBONE_ENTITY_REACH, perks.reach());
        setModifier(player, Attribute.MOVEMENT_SPEED, WISHBONE_SPEED, perks.speed());
    }

    /** Keeps one transient ADD_SCALAR modifier on an attribute at {@code amount} (none at 0). */
    private static void setModifier(Player player, Attribute attribute, NamespacedKey key, double amount) {
        AttributeInstance instance = player.getAttribute(attribute);
        if (instance == null) {
            return;
        }
        AttributeModifier current = instance.getModifier(key);
        if (current != null && Math.abs(current.getAmount() - amount) < 1e-4) {
            return;
        }
        if (current != null) {
            instance.removeModifier(key);
        }
        if (Math.abs(amount) >= 1e-4) {
            instance.addTransientModifier(new AttributeModifier(key, amount, AttributeModifier.Operation.ADD_SCALAR, EquipmentSlotGroup.ANY));
        }
    }

    // ------------------------------------------------------------------ cleanup

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        UUID id = e.getPlayer().getUniqueId();
        applySize(e.getPlayer(), 1.0);
        sizeNow.remove(id);
        sizeWanted.remove(id);
        removeRig(id);
        active.remove(id);
        haloOf.remove(id);
        lastPosition.remove(id);
        lastStep.remove(id);
        Deque<Footprint> prints = footprints.remove(id);
        if (prints != null) {
            prints.forEach(p -> p.display().remove());
        }
    }

    @EventHandler
    public void onDeath(PlayerDeathEvent e) {
        removeRig(e.getPlayer().getUniqueId());
    }

    @EventHandler
    public void onWorldChange(PlayerChangedWorldEvent e) {
        removeRig(e.getPlayer().getUniqueId());
    }

    /** Plugin disable: nobody stays small, no displays left behind. */
    public void shutdown() {
        Bukkit.getOnlinePlayers().forEach(player -> applySize(player, 1.0));
        new ArrayList<>(rigs.keySet()).forEach(this::removeRig);
        footprints.values().forEach(prints -> prints.forEach(p -> p.display().remove()));
        footprints.clear();
    }
}
