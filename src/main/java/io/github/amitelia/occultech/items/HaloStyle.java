package io.github.amitelia.occultech.items;

import java.util.List;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.entity.Player;
import org.bukkit.persistence.PersistentDataType;

import io.github.amitelia.occultech.core.Keys;

/**
 * The Hollow Halo's styles. The plain Halo is always available; every other style is unlocked by defeating its boss
 * {@value #WINS_TO_UNLOCK} times (operators have them all, and {@code /occultech unlockhalos} grants them all).
 * Each style is a few display entities circling above the head (smooth, client-animated) plus an optional particle.
 */
public enum HaloStyle {

    HALO("&6Halo", null, Material.GOLD_NUGGET, null,
        List.of(Part.ring(Material.GOLD_NUGGET, 8, 0.32, 0.18, 1))),
    WEB_CROWN("&fSilk Crown", "BROOD_MOTHER", Material.COBWEB, null,
        List.of(Part.ring(Material.STRING, 6, 0.3, 0.22, 0.6))),
    ARROW_CROWN("&fQuill Crown", "VOLLEY", Material.ARROW, null,
        List.of(Part.ring(Material.ARROW, 6, 0.3, 0.26, 1.2))),
    POTION_CROWN("&5Coven Crown", "WITCH_COVEN", Material.POTION, Particle.WITCH,
        List.of(Part.ring(Material.POTION, 3, 0.32, 0.24, 0.8))),
    SLIME_CROWN("&aSlime Crown", "GELATINOUS_SOVEREIGN", Material.SLIME_BALL, Particle.ITEM_SLIME,
        List.of(Part.ring(Material.SLIME_BALL, 5, 0.3, 0.22, 0.7))),
    AXE_CROWN("&cFrenzy Crown", "THE_UNBOUND", Material.IRON_AXE, null,
        List.of(Part.ring(Material.IRON_AXE, 4, 0.34, 0.26, 2))),
    MOON_AND_STARS("&9Moon and Stars", "NIGHT_MATRIARCH", Material.PHANTOM_MEMBRANE, Particle.END_ROD,
        List.of(Part.text("&e☽", 1, 0.0, 1.2, 0), Part.ring(Material.GLOWSTONE_DUST, 4, 0.38, 0.14, -0.8))),
    MIRROR_HALO("&bMirror Halo", "MIRRORED_MAGUS", Material.GLASS_PANE, Particle.END_ROD,
        List.of(Part.ring(Material.GLASS_PANE, 6, 0.34, 0.24, 2.4))),
    SOUL_CROWN("&3Soul Crown", "ARCHEVOKER", Material.SOUL_LANTERN, Particle.SOUL_FIRE_FLAME,
        List.of(Part.ring(Material.SOUL_LANTERN, 4, 0.34, 0.2, 0.6))),
    WARDEN_EYE("&3Watcher's Halo", "ABYSSAL_WARDEN", Material.HEART_OF_THE_SEA, null,
        List.of(Part.center(Material.HEART_OF_THE_SEA, 0.22), Part.ring(Material.PRISMARINE_SHARD, 6, 0.36, 0.16, 1))),
    SHELL_CROWN("&9Tide Crown", "TIDEBREAKER", Material.NAUTILUS_SHELL, Particle.BUBBLE_POP,
        List.of(Part.ring(Material.NAUTILUS_SHELL, 4, 0.32, 0.22, 0.8))),
    SOLAR_SYSTEM("&6Solar System", "BLAZE_CHOIR", Material.SHROOMLIGHT, null,
        List.of(Part.center(Material.SHROOMLIGHT, 0.16), Part.orbit(Material.PRISMARINE, 0.3, 0.08, 2.2),
            Part.orbit(Material.MAGMA_BLOCK, 0.44, 0.1, 1.4), Part.orbit(Material.AMETHYST_BLOCK, 0.58, 0.12, 0.9))),
    STORM_HALO("&bStorm Halo", "TEMPEST", Material.WIND_CHARGE, Particle.CLOUD,
        List.of(Part.ring(Material.WIND_CHARGE, 4, 0.34, 0.22, 3))),
    TIDAL_CROWN("&3Tidal Crown", "DROWNED_ELDER", Material.PRISMARINE_CRYSTALS, Particle.BUBBLE_POP,
        List.of(Part.ring(Material.PRISMARINE_CRYSTALS, 6, 0.34, 0.2, -1))),
    DARK_RUNE_CROWN("&5Dark Rune Crown", "HOLLOW_WARLORD", Material.WITHER_ROSE, Particle.SMOKE,
        List.of(Part.text("&5ᚠ", 1, 0.36, 0.7, 0.8), Part.text("&5ᚢ", 1, 0.36, 0.7, 0.8), Part.text("&5ᚦ", 1, 0.36, 0.7, 0.8),
            Part.text("&5ᚨ", 1, 0.36, 0.7, 0.8), Part.text("&5ᚱ", 1, 0.36, 0.7, 0.8), Part.text("&5ᚲ", 1, 0.36, 0.7, 0.8))),
    THORN_CROWN("&6Thorn Crown", "HEARTWOOD_HORROR", Material.RESIN_CLUMP, Particle.FALLING_HONEY,
        List.of(Part.ring(Material.RESIN_CLUMP, 6, 0.32, 0.18, 0.5))),
    STORM_RIDER("&bLightning Crown", "DREAD_RIDERS", Material.LIGHTNING_ROD, Particle.ELECTRIC_SPARK,
        List.of(Part.ring(Material.LIGHTNING_ROD, 5, 0.32, 0.22, 1.6))),
    GEAR_CROWN("&dCorrupted Crown", "CORRUPTED_COLOSSUS", Material.COMPARATOR, Particle.ELECTRIC_SPARK,
        List.of(Part.ring(Material.COMPARATOR, 5, 0.32, 0.22, -1.2))),
    TWIN("&fLittle Twin", "DOPPELGANGER", Material.PLAYER_HEAD, null,
        List.of(Part.orbit(Material.PLAYER_HEAD, 0.45, 0.22, 1.2))),
    PENTAGRAM("&4Hollow Pentagram", "GALLUS", Material.NETHER_STAR, null,
        List.of(Part.text("&4ᛟ", 1, 0.0, 1.0, 0))),
    ;

    public static final int WINS_TO_UNLOCK = 5;
    public static final NamespacedKey ALL_UNLOCKED = new NamespacedKey("occultech", "halos_unlocked");

    /** One element of a halo: a ring of copies, a single orbiting piece, or a centred piece. */
    public record Part(@Nullable Material item, @Nullable String text, int count, double radius, double scale, double speed) {
        static Part ring(Material item, int count, double radius, double scale, double speed) {
            return new Part(item, null, count, radius, scale, speed);
        }

        static Part orbit(Material item, double radius, double scale, double speed) {
            return new Part(item, null, 1, radius, scale, speed);
        }

        static Part center(Material item, double scale) {
            return new Part(item, null, 1, 0, scale, 0);
        }

        static Part text(String text, int count, double radius, double scale, double speed) {
            return new Part(null, text, count, radius, scale, speed);
        }
    }

    final String label;
    @Nullable final String boss;
    final Material icon;
    @Nullable final Particle particle;
    final List<Part> parts;

    HaloStyle(String label, @Nullable String boss, Material icon, @Nullable Particle particle, List<Part> parts) {
        this.label = label;
        this.boss = boss;
        this.icon = icon;
        this.particle = particle;
        this.parts = parts;
    }

    public boolean unlockedFor(Player player) {
        return boss == null || player.isOp() || player.getPersistentDataContainer().has(ALL_UNLOCKED, PersistentDataType.BYTE)
            || Keys.winsOf(player, boss) >= WINS_TO_UNLOCK;
    }

    /** The Pentagram's extra particle star (drawn in particles: too many lines for display entities). */
    boolean drawsStar() {
        return this == PENTAGRAM;
    }

    static HaloStyle byName(@Nullable String name) {
        if (name != null) {
            for (HaloStyle style : values()) {
                if (style.name().equals(name)) {
                    return style;
                }
            }
        }
        return HALO;
    }

    static Color starColor() {
        return Color.fromRGB(200, 20, 40);
    }
}
