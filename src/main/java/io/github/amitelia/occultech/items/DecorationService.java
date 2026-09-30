package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.TextDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.core.Keys;
import me.mrCookieSlime.Slimefun.api.BlockStorage;

/**
 * Draws every decoration's visual effect. Decorations only animate while a player is within {@value #VIEW_RANGE}
 * blocks, never change blocks, and keep their particle counts small. Orbiting parts are display entities moved a few
 * times a second with client-side interpolation, so the motion looks smooth without a packet every tick.
 * Right-click cycles a decoration's palette (stored in its block data).
 */
public final class DecorationService {

    public static final String PALETTE_KEY = "occultech_palette";
    private static final double VIEW_RANGE = 24;
    private static final int PERIOD = 4;
    private static final int ORBIT_STEP_TICKS = 8;
    private static final long SEEN_TIMEOUT_MS = 5000;

    /** One palette: a display name, colors for particles, and materials/glyphs for display parts. */
    private record Palette(String name, Color[] colors, Material[] parts, String[] glyphs) {
        static Palette colors(String name, Color... colors) {
            return new Palette(name, colors, new Material[0], new String[0]);
        }
    }

    public enum Kind {
        WISP_JAR(
            Palette.colors("&eFireflies"),
            Palette.colors("&bAzure", Color.fromRGB(120, 200, 255)),
            Palette.colors("&dRose", Color.fromRGB(255, 140, 200)),
            Palette.colors("&aVerdant", Color.fromRGB(150, 255, 140))),
        ABYSSAL_LANTERN(
            Palette.colors("&3Teal", Color.fromRGB(80, 220, 200)),
            Palette.colors("&9Deep blue", Color.fromRGB(60, 110, 255)),
            Palette.colors("&5Violet", Color.fromRGB(170, 90, 255)),
            Palette.colors("&6Pale gold", Color.fromRGB(255, 220, 130))),
        RUNE_OBELISK(
            new Palette("&5Futhark", new Color[] { Color.fromRGB(190, 110, 255) }, new Material[0], new String[] { "&5ᚠ", "&5ᚱ", "&5ᛟ" }),
            new Palette("&6Celestial", new Color[] { Color.fromRGB(255, 210, 90) }, new Material[0], new String[] { "&6☽", "&e✦", "&6☉" }),
            new Palette("&3Abyssal", new Color[] { Color.fromRGB(80, 220, 200) }, new Material[0], new String[] { "&3≈", "&b◈", "&3∿" })),
        OCCULT_ORRERY(
            new Palette("&bSea, fire and void", new Color[0], new Material[] { Material.SHROOMLIGHT, Material.PRISMARINE, Material.MAGMA_BLOCK,
                Material.CRYING_OBSIDIAN }, new String[0]),
            new Palette("&aGems", new Color[0], new Material[] { Material.GLOWSTONE, Material.DIAMOND_BLOCK, Material.EMERALD_BLOCK,
                Material.AMETHYST_BLOCK }, new String[0]),
            new Palette("&fMoons", new Color[0], new Material[] { Material.OCHRE_FROGLIGHT, Material.CALCITE, Material.END_STONE,
                Material.BONE_BLOCK }, new String[0])),
        SOULFIRE_BRAZIER(
            Palette.colors("&bSoul flames"),
            Palette.colors("&6Ember flames")),
        BOTTLED_GALE(
            Palette.colors("&fWhite", Color.fromRGB(235, 240, 245)),
            Palette.colors("&bSky", Color.fromRGB(150, 210, 255)),
            Palette.colors("&aMint", Color.fromRGB(160, 255, 210)),
            Palette.colors("&dLilac", Color.fromRGB(210, 170, 255)));

        private final Palette[] palettes;

        Kind(Palette... palettes) {
            this.palettes = palettes;
        }

        public int paletteCount() {
            return palettes.length;
        }
    }

    private static final class Decoration {
        final Kind kind;
        long lastSeen;
        int palette = -1;
        final List<Display> parts = new ArrayList<>();

        Decoration(Kind kind) {
            this.kind = kind;
        }
    }

    private final Map<Location, Decoration> decorations = new HashMap<>();
    private long ticks;

    public DecorationService(Plugin plugin) {
        Bukkit.getScheduler().runTaskTimer(plugin, this::render, PERIOD, PERIOD);
    }

    /** Called by the decoration's ticker to keep it registered. */
    void register(Block block, Kind kind) {
        Decoration decoration = decorations.computeIfAbsent(block.getLocation(), l -> new Decoration(kind));
        decoration.lastSeen = System.currentTimeMillis();
    }

    /** Right-click: next palette. Returns its name. */
    public String cyclePalette(Block block, Kind kind) {
        int next = (paletteOf(block) + 1) % kind.palettes.length;
        BlockStorage.addBlockInfo(block, PALETTE_KEY, String.valueOf(next));
        Decoration decoration = decorations.get(block.getLocation());
        if (decoration != null) {
            clearParts(decoration);
        }
        return kind.palettes[next].name();
    }

    public int paletteOf(Block block) {
        try {
            String value = BlockStorage.getLocationInfo(block.getLocation(), PALETTE_KEY);
            return value == null ? 0 : Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    /** Number of display parts currently shown for a decoration (self-test). */
    public int partCount(Block block) {
        Decoration decoration = decorations.get(block.getLocation());
        return decoration == null ? 0 : (int) decoration.parts.stream().filter(Display::isValid).count();
    }

    void remove(Block block) {
        Decoration decoration = decorations.remove(block.getLocation());
        if (decoration != null) {
            clearParts(decoration);
        }
    }

    public void shutdown() {
        decorations.values().forEach(DecorationService::clearParts);
        decorations.clear();
    }

    // ------------------------------------------------------------------ rendering

    private void render() {
        ticks += PERIOD;
        long now = System.currentTimeMillis();
        decorations.entrySet().removeIf(entry -> {
            Location at = entry.getKey();
            Decoration decoration = entry.getValue();
            if (now - decoration.lastSeen > SEEN_TIMEOUT_MS || !at.isChunkLoaded() || BlockStorage.checkID(at) == null) {
                clearParts(decoration);
                return true;
            }
            Location center = at.clone().add(0.5, 0.5, 0.5);
            if (center.getWorld().getNearbyPlayers(center, VIEW_RANGE).isEmpty()) {
                clearParts(decoration);
                return false;
            }
            int index = Math.floorMod(paletteOf(at.getBlock()), decoration.kind.palettes.length);
            if (index != decoration.palette) {
                clearParts(decoration);
                decoration.palette = index;
            }
            Palette palette = decoration.kind.palettes[index];
            switch (decoration.kind) {
                case WISP_JAR -> wisps(center, palette, index == 0);
                case ABYSSAL_LANTERN -> lantern(center, palette);
                case RUNE_OBELISK -> obelisk(center, decoration, palette);
                case OCCULT_ORRERY -> orrery(center, decoration, palette);
                case SOULFIRE_BRAZIER -> brazier(center, index == 0);
                case BOTTLED_GALE -> gale(center, palette);
            }
            return false;
        });
    }

    /** Firefly-bush style: a few wisps pop up anywhere within 10 blocks, more at night. */
    private static void wisps(Location center, Palette palette, boolean fireflies) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        World world = center.getWorld();
        long time = world.getTime();
        boolean night = time > 12500 && time < 23500;
        if (random.nextDouble() > (night ? 0.9 : 0.35)) {
            return;
        }
        double angle = random.nextDouble(Math.PI * 2);
        double distance = 1 + random.nextDouble(9);
        Location at = center.clone().add(Math.cos(angle) * distance, random.nextDouble(0.3, 3), Math.sin(angle) * distance);
        if (fireflies) {
            world.spawnParticle(Particle.FIREFLY, at, 1, 0.1, 0.1, 0.1, 0);
        } else {
            world.spawnParticle(Particle.DUST_COLOR_TRANSITION, at, 1, 0.05, 0.05, 0.05, 0,
                new Particle.DustTransition(palette.colors()[0], Color.fromRGB(30, 30, 40), 0.8F));
        }
        center.getWorld().spawnParticle(Particle.END_ROD, center.clone().add(0, 0.2, 0), 0, 0, 0.02, 0, 1);
    }

    /** Rising bubbles and a slowly turning ring of light. */
    private void lantern(Location center, Palette palette) {
        World world = center.getWorld();
        ThreadLocalRandom random = ThreadLocalRandom.current();
        world.spawnParticle(Particle.BUBBLE_POP, center.clone().add(random.nextDouble(-0.2, 0.2), 0.6 + random.nextDouble(1.5),
            random.nextDouble(-0.2, 0.2)), 1, 0, 0, 0, 0.02);
        Particle.DustOptions dust = new Particle.DustOptions(palette.colors()[0], 0.7F);
        double base = ticks * 0.05;
        for (int i = 0; i < 6; i++) {
            double angle = base + Math.PI * 2 * i / 6;
            world.spawnParticle(Particle.DUST, center.clone().add(Math.cos(angle) * 0.9, 0.1, Math.sin(angle) * 0.9), 1, 0, 0, 0, 0, dust);
        }
    }

    /** Three rune glyphs orbiting the stone, with a spark now and then. */
    private void obelisk(Location center, Decoration decoration, Palette palette) {
        if (decoration.parts.isEmpty()) {
            for (String glyph : palette.glyphs()) {
                decoration.parts.add(center.getWorld().spawn(center, TextDisplay.class, d -> {
                    prepare(d);
                    d.setText(MenuUtils.color(glyph));
                    d.setBillboard(Display.Billboard.CENTER);
                    d.setBackgroundColor(Color.fromARGB(0, 0, 0, 0));
                    d.setBrightness(new Display.Brightness(15, 15));
                    d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(1.4F, 1.4F, 1.4F), new AxisAngle4f()));
                }));
            }
        }
        if (ticks % ORBIT_STEP_TICKS == 0) {
            double base = ticks / (double) ORBIT_STEP_TICKS * (Math.PI / 8);
            for (int i = 0; i < decoration.parts.size(); i++) {
                double angle = base + Math.PI * 2 * i / decoration.parts.size();
                double bob = Math.sin(base + i) * 0.15;
                decoration.parts.get(i).teleport(center.clone().add(Math.cos(angle) * 0.9, 0.4 + bob, Math.sin(angle) * 0.9));
            }
        }
        if (ThreadLocalRandom.current().nextInt(10) == 0) {
            center.getWorld().spawnParticle(Particle.ENCHANT, center.clone().add(0, 0.8, 0), 6, 0.3, 0.3, 0.3, 0.4);
        }
    }

    /** A glowing sun with three worlds circling at their own radius and speed. */
    private void orrery(Location center, Decoration decoration, Palette palette) {
        Material[] parts = palette.parts();
        Location sun = center.clone().add(0, 1.2, 0);
        if (decoration.parts.isEmpty()) {
            for (int i = 0; i < parts.length; i++) {
                float scale = i == 0 ? 0.3F : 0.14F;
                Material part = parts[i];
                decoration.parts.add(center.getWorld().spawn(sun, ItemDisplay.class, d -> {
                    prepare(d);
                    d.setItemStack(new ItemStack(part));
                    d.setBrightness(new Display.Brightness(15, 15));
                    d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(scale, scale, scale), new AxisAngle4f()));
                }));
            }
        }
        if (ticks % ORBIT_STEP_TICKS == 0) {
            double step = ticks / (double) ORBIT_STEP_TICKS;
            for (int i = 1; i < decoration.parts.size(); i++) {
                double radius = 0.35 + 0.22 * i;
                double angle = step * (Math.PI / (6 + 3 * i)) + i * 2.1;
                decoration.parts.get(i).teleport(sun.clone().add(Math.cos(angle) * radius, Math.sin(angle * 0.5) * 0.08 * i, Math.sin(angle) * radius));
            }
        }
    }

    /** A crackling bowl of flame particles with drifting embers. Particles only: nothing is ever set on fire. */
    private static void brazier(Location center, boolean soul) {
        World world = center.getWorld();
        ThreadLocalRandom random = ThreadLocalRandom.current();
        Location bowl = center.clone().add(0, 0.2, 0);
        world.spawnParticle(soul ? Particle.SOUL_FIRE_FLAME : Particle.FLAME, bowl, 2, 0.12, 0.05, 0.12, 0.01);
        if (random.nextInt(3) == 0) {
            world.spawnParticle(Particle.SMALL_FLAME, bowl.clone().add(0, 0.4, 0), 1, 0.15, 0.2, 0.15, 0.02);
        }
        if (random.nextInt(6) == 0) {
            world.spawnParticle(Particle.DUST, bowl.clone().add(random.nextDouble(-0.4, 0.4), 0.8 + random.nextDouble(0.8), random.nextDouble(-0.4, 0.4)),
                1, 0, 0, 0, 0, new Particle.DustOptions(soul ? Color.fromRGB(90, 210, 255) : Color.fromRGB(255, 140, 40), 0.6F));
        }
        if (random.nextInt(8) == 0) {
            world.spawnParticle(Particle.SMOKE, bowl.clone().add(0, 0.9, 0), 1, 0.1, 0.1, 0.1, 0.01);
        }
    }

    /** A tiny tornado spinning above the jar. */
    private void gale(Location center, Palette palette) {
        World world = center.getWorld();
        Particle.DustOptions dust = new Particle.DustOptions(palette.colors()[0], 0.5F);
        double spin = ticks * 0.6;
        for (int i = 0; i < 7; i++) {
            double height = i * 0.12;
            double radius = 0.05 + height * 0.35;
            double angle = spin + i * 1.1;
            world.spawnParticle(Particle.DUST, center.clone().add(Math.cos(angle) * radius, 0.55 + height, Math.sin(angle) * radius), 1, 0, 0, 0, 0, dust);
        }
    }

    // ------------------------------------------------------------------ helpers

    private static void prepare(Display display) {
        display.setPersistent(false);
        display.setTeleportDuration(ORBIT_STEP_TICKS);
        display.getPersistentDataContainer().set(Keys.HOLOGRAM, PersistentDataType.BYTE, (byte) 1);
    }

    private static void clearParts(Decoration decoration) {
        decoration.parts.forEach(Display::remove);
        decoration.parts.clear();
    }
}
