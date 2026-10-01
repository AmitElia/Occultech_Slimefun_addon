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
 * <li>Wishbone Talisman: half size (on/off). A transient modifier, never saved onto the player.</li>
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
    private long ticks;

    public TalismanService(Plugin plugin) {
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
            setSmall(player, styles[Kind.WISHBONE.ordinal()] >= 0);
        }
    }

    // ------------------------------------------------------------------ draw (every 2 ticks)

    private void draw() {
        ticks += 2;
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

    private static void setSmall(Player player, boolean small) {
        AttributeInstance scale = player.getAttribute(Attribute.SCALE);
        if (scale == null) {
            return;
        }
        boolean has = scale.getModifier(WISHBONE) != null;
        if (small && !has) {
            scale.addTransientModifier(new AttributeModifier(WISHBONE, -0.5, AttributeModifier.Operation.ADD_SCALAR, EquipmentSlotGroup.ANY));
        } else if (!small && has) {
            scale.removeModifier(WISHBONE);
        }
    }

    // ------------------------------------------------------------------ cleanup

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        UUID id = e.getPlayer().getUniqueId();
        setSmall(e.getPlayer(), false);
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
        Bukkit.getOnlinePlayers().forEach(player -> setSmall(player, false));
        new ArrayList<>(rigs.keySet()).forEach(this::removeRig);
        footprints.values().forEach(prints -> prints.forEach(p -> p.display().remove()));
        footprints.clear();
    }
}
