package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;

import io.github.amitelia.occultech.content.ItemKeys;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;

/**
 * The final talismans. Each works while it's anywhere in the carrier's inventory and only ever affects its carrier;
 * right-click cycles its style (the choice is stored on the item). Only one of each kind counts.
 * <ul>
 * <li>Hollow Halo: a slowly turning ring of light over the head (gold, white, violet, cyan, or off).</li>
 * <li>Wishbone Talisman: half size (on/off). A transient modifier, so it is never saved onto the player.</li>
 * <li>Aura Talisman: a light trail while walking (prismatic sparks, petals, soul wisps, or off).</li>
 * </ul>
 * Inventories are scanned once a second; effects are drawn every 4 ticks from that.
 */
public final class TalismanService implements Listener {

    public enum Kind {
        HALO("HOLLOW_HALO", "&6Gold", "&fWhite", "&5Violet", "&bCyan", "&8Off"),
        WISHBONE("WISHBONE_TALISMAN", "&aOn", "&8Off"),
        AURA("AURA_TALISMAN", "&dPrismatic sparks", "&dPetals", "&3Soul wisps", "&8Off");

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
    private static final NamespacedKey WISHBONE = new NamespacedKey("occultech", "wishbone");
    private static final Color[] HALO_COLORS = { Color.fromRGB(255, 210, 90), Color.fromRGB(245, 245, 255), Color.fromRGB(180, 110, 255),
        Color.fromRGB(110, 230, 255) };

    /** Per player: the active style of each kind, or -1 if none is carried (or it's off). */
    private final Map<UUID, int[]> active = new HashMap<>();
    private final Map<UUID, Location> lastPosition = new HashMap<>();
    private long ticks;

    public TalismanService(Plugin plugin) {
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::scan, 20L, 20L);
        Bukkit.getScheduler().runTaskTimer(plugin, this::draw, 4L, 4L);
    }

    /** The style stored on a talisman item (0 if never set). */
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

    private void scan() {
        for (Player player : Bukkit.getOnlinePlayers()) {
            int[] styles = { -1, -1, -1 };
            for (ItemStack item : player.getInventory().getContents()) {
                if (item == null || item.getType().isAir()) {
                    continue;
                }
                SlimefunItem sfItem = SlimefunItem.getByItem(item);
                if (sfItem == null) {
                    continue;
                }
                for (Kind kind : Kind.values()) {
                    if (kind.id.equals(sfItem.getId()) && styles[kind.ordinal()] < 0) {
                        int style = styleOf(item);
                        styles[kind.ordinal()] = kind.isOff(style) ? -1 : style;
                    }
                }
            }
            active.put(player.getUniqueId(), styles);
            setSmall(player, styles[Kind.WISHBONE.ordinal()] >= 0);
        }
    }

    private void draw() {
        ticks += 4;
        for (Player player : Bukkit.getOnlinePlayers()) {
            int[] styles = active.get(player.getUniqueId());
            if (styles == null || player.isDead()) {
                continue;
            }
            if (styles[Kind.HALO.ordinal()] >= 0) {
                halo(player, HALO_COLORS[styles[Kind.HALO.ordinal()] % HALO_COLORS.length]);
            }
            Location here = player.getLocation();
            Location before = lastPosition.put(player.getUniqueId(), here);
            boolean moving = before != null && before.getWorld() == here.getWorld() && before.distanceSquared(here) > 0.01;
            if (styles[Kind.AURA.ordinal()] >= 0 && moving) {
                trail(player, styles[Kind.AURA.ordinal()]);
            }
        }
    }

    private void halo(Player player, Color color) {
        Particle.DustOptions dust = new Particle.DustOptions(color, 0.55F);
        double scale = player.getAttribute(Attribute.SCALE) == null ? 1 : player.getAttribute(Attribute.SCALE).getValue();
        Location top = player.getEyeLocation().add(0, 0.55 * scale, 0);
        double spin = ticks * 0.08;
        for (int i = 0; i < 10; i++) {
            double angle = spin + Math.PI * 2 * i / 10;
            player.getWorld().spawnParticle(Particle.DUST, top.clone().add(Math.cos(angle) * 0.32 * scale, 0, Math.sin(angle) * 0.32 * scale), 1, 0, 0, 0, 0, dust);
        }
    }

    private void trail(Player player, int style) {
        Location feet = player.getLocation().add(0, 0.1, 0);
        switch (style) {
            case 0 -> {
                java.awt.Color rgb = java.awt.Color.getHSBColor((ticks % 120) / 120F, 0.8F, 1F);
                player.getWorld().spawnParticle(Particle.DUST, feet, 2, 0.15, 0.05, 0.15, 0,
                    new Particle.DustOptions(Color.fromRGB(rgb.getRed(), rgb.getGreen(), rgb.getBlue()), 0.7F));
            }
            case 1 -> player.getWorld().spawnParticle(Particle.CHERRY_LEAVES, feet.clone().add(0, 0.4, 0), 1, 0.2, 0.1, 0.2, 0);
            default -> player.getWorld().spawnParticle(Particle.SOUL, feet, 1, 0.15, 0.05, 0.15, 0.01);
        }
    }

    /** Half size via a transient modifier: never written into the player file. */
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

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        setSmall(e.getPlayer(), false);
        active.remove(e.getPlayer().getUniqueId());
        lastPosition.remove(e.getPlayer().getUniqueId());
    }

    /** Plugin disable: nobody stays small. */
    public void shutdown() {
        Bukkit.getOnlinePlayers().forEach(player -> setSmall(player, false));
    }
}
