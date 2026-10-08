package io.github.amitelia.occultech.event;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.configuration.file.YamlConfiguration;

/**
 * The preset place where the Staff Raid runs: a center (the block an admin stood on) and a radius. Saved in
 * {@code raid-arena.yml}. The sky above it must be open, since players get thrown up in Act 2.
 */
public record RaidArena(@Nonnull String world, int x, int y, int z, double radius) {

    public static final double MIN_RADIUS = 20;
    /** How high above the floor the sky must be clear. */
    public static final int CLEAR_SKY = 30;

    @Nullable
    public World bukkitWorld() {
        return Bukkit.getWorld(world);
    }

    /** The middle of the arena at foot height. */
    @Nonnull
    public Location center() {
        return new Location(bukkitWorld(), x + 0.5, y, z + 0.5);
    }

    /** Whether {@code at} is inside the arena (by distance across the ground). */
    public boolean contains(@Nullable Location at) {
        if (at == null || at.getWorld() == null || !at.getWorld().getName().equals(world)) {
            return false;
        }
        double dx = at.getX() - (x + 0.5);
        double dz = at.getZ() - (z + 0.5);
        return dx * dx + dz * dz <= radius * radius;
    }

    /** The floor block (the highest block) at an offset from the center. */
    @Nonnull
    public Block floor(double dx, double dz) {
        return bukkitWorld().getHighestBlockAt((int) Math.floor(x + 0.5 + dx), (int) Math.floor(z + 0.5 + dz));
    }

    /** Where fighters who die in the arena come back: on the floor at its south edge. */
    @Nonnull
    public Location edge() {
        Block floor = floor(0, radius - 3);
        Location spot = floor.getLocation().add(0.5, 1, 0.5);
        spot.setDirection(center().toVector().subtract(spot.toVector()));
        return spot;
    }

    /**
     * What keeps this arena from hosting a raid: a missing world, too small, or blocks overhead (anything more than 2
     * blocks above the center's floor, checked every 3 blocks). Empty when it's fine.
     */
    @Nonnull
    public List<String> problems() {
        List<String> problems = new ArrayList<>();
        World bukkit = bukkitWorld();
        if (bukkit == null) {
            problems.add("world " + world + " isn't loaded");
            return problems;
        }
        if (radius < MIN_RADIUS) {
            problems.add("radius " + radius + " is under " + MIN_RADIUS);
        }
        int blocked = 0;
        String first = null;
        for (int dx = (int) -radius; dx <= radius; dx += 3) {
            for (int dz = (int) -radius; dz <= radius; dz += 3) {
                if (dx * dx + dz * dz > radius * radius) {
                    continue;
                }
                int top = bukkit.getHighestBlockYAt(x + dx, z + dz);
                if (top > y + 1) {
                    blocked++;
                    if (first == null) {
                        first = (x + dx) + " " + top + " " + (z + dz);
                    }
                }
            }
        }
        if (blocked > 0) {
            problems.add(blocked + " spots have blocks above the floor (first at " + first + "); the sky must be open "
                + CLEAR_SKY + " blocks up");
        }
        return problems;
    }

    // ------------------------------------------------------------------ raid-arena.yml

    @Nullable
    public static RaidArena load(@Nonnull File file) {
        if (!file.exists()) {
            return null;
        }
        YamlConfiguration yaml = YamlConfiguration.loadConfiguration(file);
        String world = yaml.getString("world");
        if (world == null) {
            return null;
        }
        return new RaidArena(world, yaml.getInt("x"), yaml.getInt("y"), yaml.getInt("z"), yaml.getDouble("radius", 45));
    }

    public void save(@Nonnull File file) throws IOException {
        YamlConfiguration yaml = new YamlConfiguration();
        yaml.set("world", world);
        yaml.set("x", x);
        yaml.set("y", y);
        yaml.set("z", z);
        yaml.set("radius", radius);
        yaml.save(file);
    }
}
