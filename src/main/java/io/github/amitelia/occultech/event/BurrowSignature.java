package io.github.amitelia.occultech.event;

import java.util.List;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.block.data.BlockData;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * mrlonelydwarf's signature, <b>burrow</b> (mining theme, a pickaxe in hand - Session E5): he digs down into the floor
 * and comes up behind the most isolated player (the one farthest from any teammate). He sinks over 1 s with digging
 * particles and sounds - no block is broken - stays under for 2 s, then rises the same way behind his target, which is
 * the warning, and swings a heavy pickaxe blow. From the moment he starts digging until he's out, nothing hurts, knocks
 * back or stops him.
 */
final class BurrowSignature extends Signature {

    static final String ID = "RAID_DWARF";
    private static final Mechanic STRIKE = Mechanic.of(ID, "Pickaxe strike", 32, Mechanic.Kind.MELEE, true);
    private static final int SINK = 20;
    private static final int UNDER = 40;
    private static final int RISE = 20;
    private static final int SWING = 6;
    private static final double DEPTH = 2.2;
    private static final double REACH = 3.5;
    private static final Color WARNING = Color.fromRGB(150, 110, 60);

    private enum Phase { NONE, SINKING, UNDER, RISING, SWINGING }

    private Phase phase = Phase.NONE;
    private int ticks;
    @Nullable private Player prey;
    private Location surface;
    private Component description;

    BurrowSignature(StaffKit kit) {
        super(kit, 100);
        kit.body.getEquipment().setItemInMainHand(new ItemStack(Material.DIAMOND_PICKAXE));
    }

    /** The player farthest from any teammate (a lone player is the most isolated of all). */
    @Nullable
    private Player loneliest() {
        List<Player> players = kit.fight.players();
        Player best = null;
        double bestGap = -1;
        for (Player player : players) {
            double gap = Double.MAX_VALUE;
            for (Player other : players) {
                if (other != player) {
                    gap = Math.min(gap, other.getLocation().distanceSquared(player.getLocation()));
                }
            }
            if (gap > bestGap) {
                best = player;
                bestGap = gap;
            }
        }
        return best;
    }

    @Override
    boolean cast(int now) {
        Player lonely = loneliest();
        if (lonely == null || phase != Phase.NONE || !kit.body.isOnGround()) {
            next = now + 20;
            return false;
        }
        next = now + 240;
        kit.claim(SINK + UNDER + RISE + SWING);
        prey = lonely;
        surface = kit.body.getLocation();
        phase = Phase.SINKING;
        ticks = 0;
        kit.body.setGravity(false);
        kit.body.setVelocity(new Vector());
        return true;
    }

    @Override
    boolean steering() {
        return phase != Phase.NONE;
    }

    @Override
    double incoming() {
        return phase == Phase.NONE ? 1 : 0;   // can't be interrupted
    }

    @Override
    boolean deflect(Projectile projectile) {
        return phase != Phase.NONE;
    }

    @Override
    void move() {
        if (phase == Phase.NONE) {
            return;
        }
        if (!kit.alive()) {
            phase = Phase.NONE;
            return;
        }
        ticks++;
        kit.body.setVelocity(new Vector());
        switch (phase) {
            case SINKING -> {
                kit.body.teleport(surface.clone().subtract(0, DEPTH * ticks / SINK, 0));
                dig(surface);
                if (ticks >= SINK) {
                    // fully under: hide the name, which would show through the floor
                    description = kit.body.getDescription();
                    kit.body.setCustomNameVisible(false);
                    kit.body.setDescription(Component.empty());
                    phase = Phase.UNDER;
                    ticks = 0;
                }
            }
            case UNDER -> {
                if (ticks >= UNDER) {
                    surface = riseSpot();
                    kit.body.teleport(surface.clone().subtract(0, DEPTH, 0));
                    kit.fight.telegraph(surface, 1.6, RISE + SWING, WARNING);
                    phase = Phase.RISING;
                    ticks = 0;
                }
            }
            case RISING -> {
                Location at = surface.clone().subtract(0, DEPTH * (1 - ticks / (double) RISE), 0);
                if (prey != null) {
                    at.setDirection(prey.getLocation().toVector().subtract(at.toVector()));
                }
                kit.body.teleport(at);
                dig(surface);
                if (ticks == RISE / 2) {
                    kit.body.setCustomNameVisible(true);
                    if (description != null) {
                        kit.body.setDescription(description);
                    }
                }
                if (ticks >= RISE) {
                    phase = Phase.SWINGING;
                    ticks = 0;
                }
            }
            case SWINGING -> {
                if (prey != null) {
                    Abyss.face(kit.body, prey.getLocation());
                }
                if (ticks >= SWING) {
                    if (prey != null && kit.fighting(prey) && kit.within(prey, REACH)) {
                        kit.body.swingMainHand();
                        kit.fight.hit(prey, STRIKE, kit.body);
                        StaffKit.knock(prey, kit.body.getLocation(), 0.7, 0.35);
                        prey.getWorld().playSound(prey.getLocation(), Sound.BLOCK_STONE_BREAK, 1.5F, 0.6F);
                    }
                    kit.body.setGravity(true);
                    phase = Phase.NONE;
                    prey = null;
                }
            }
            default -> { }
        }
    }

    /** Behind his target on solid ground, or wherever is safe near them. */
    private Location riseSpot() {
        if (prey == null || !kit.fighting(prey)) {
            return surface;
        }
        Location at = prey.getLocation();
        Location behind = at.clone().subtract(at.getDirection().setY(0).normalize().multiply(1.4));
        Block feet = behind.getBlock();
        if (feet.isPassable() && feet.getRelative(0, 1, 0).isPassable() && !feet.getRelative(0, -1, 0).isPassable()) {
            behind.setY(feet.getY());
            return behind;
        }
        Location near = safeSpot(at, 1, 2.5);
        return near != null ? near : surface;
    }

    /** Digging particles and sounds at {@code at}'s floor - nothing is broken. */
    private void dig(Location at) {
        Block floor = at.getBlock().getRelative(0, -1, 0);
        BlockData look = floor.getType().isAir() ? Material.DIRT.createBlockData() : floor.getBlockData();
        at.getWorld().spawnParticle(Particle.BLOCK, at.clone().add(0, 0.1, 0), 8, 0.4, 0.1, 0.4, look);
        if (ticks % 4 == 0) {
            at.getWorld().playSound(at, look.getSoundGroup().getBreakSound(), 1F, 0.8F);
        }
    }
}
