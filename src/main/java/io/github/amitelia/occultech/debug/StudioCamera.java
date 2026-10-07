package io.github.amitelia.occultech.debug;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.bukkit.Bukkit;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.scheduler.BukkitTask;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.core.Keys;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

/**
 * {@code /occultech studio <kind> [next|prev|N]}: steps through the showcase studios of one kind, putting the camera at
 * exactly the same spot relative to each studio's subject, so cutting between them looks like the subject swapping in
 * place (spectator mode: no gravity, no hand drawn; F1 hides the HUD). {@code /occultech studio stop} gives back the
 * game mode and position from before.
 * <ul>
 * <li>armor: a turntable - the camera stays still in front and the mannequin turns. (Moving the camera round it
 * jittered: the game sends an entity's facing in 1.4-degree steps; a mannequin's body eases towards its facing, which
 * smooths those steps out.)</li>
 * <li>weapons: a close-up of the mannequin's right hand and the weapon in it.</li>
 * <li>machines, cosmetics, rituals: one isometric view (45 degrees round, 35 down) at one distance from the subject
 * block (the altar, for a ritual), whatever its size.</li>
 * </ul>
 * Distances and the turn speed are in config.yml ({@code showcase.camera}). The studios come from {@code showcase.yml}
 * ({@code studios}: "kind;x;y;z;size;ID", the subject block).
 */
final class StudioCamera {

    private static final double ISO_YAW = 45;
    private static final double ISO_PITCH = 35.26;
    private static final double EYE = 1.62;

    private record Shot(String kind, World world, int x, int y, int z, int size, String id) {}

    private static final class Session {
        GameMode previousMode;
        Location previousSpot;
        String kind;
        int index;
        Mannequin turning;
        BukkitTask turntable;
    }

    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    private StudioCamera() {}

    static void command(Occultech plugin, Player player, String kind, String which) {
        kind = kind.toLowerCase(java.util.Locale.ROOT);
        Session session = SESSIONS.get(player.getUniqueId());
        if (kind.equals("stop")) {
            if (session != null) {
                stopTurntable(session);
                player.setGameMode(session.previousMode);
                player.teleport(session.previousSpot);
                SESSIONS.remove(player.getUniqueId());
            }
            player.sendActionBar(Component.text("Studio camera off", NamedTextColor.GRAY));
            return;
        }
        List<Shot> shots = shots(plugin, kind);
        if (shots.isEmpty()) {
            player.sendMessage("No " + kind + " studios - build the showcase first (/occultech showcase). Kinds: armor, weapons, machines, cosmetics, rituals.");
            return;
        }
        if (session == null) {
            session = new Session();
            session.previousMode = player.getGameMode();
            session.previousSpot = player.getLocation();
            session.index = -1;
            SESSIONS.put(player.getUniqueId(), session);
        }
        int index;
        if (which == null || which.equalsIgnoreCase("next")) {
            index = kind.equals(session.kind) ? session.index + 1 : 0;
        } else if (which.equalsIgnoreCase("prev")) {
            index = kind.equals(session.kind) ? session.index - 1 : shots.size() - 1;
        } else {
            try {
                index = Integer.parseInt(which) - 1;
            } catch (NumberFormatException e) {
                player.sendMessage("Use next, prev or a studio number (1-" + shots.size() + ").");
                return;
            }
        }
        index = Math.floorMod(index, shots.size());
        session.kind = kind;
        session.index = index;
        Shot shot = shots.get(index);

        stopTurntable(session);
        player.setGameMode(GameMode.SPECTATOR);
        Location subject = new Location(shot.world(), shot.x() + 0.5, shot.y(), shot.z() + 0.5);
        var camera = plugin.getConfig().getConfigurationSection("showcase.camera");
        double blockDistance = camera == null ? 2.6 : camera.getDouble("block-distance", 2.6);
        double handDistance = camera == null ? 1.1 : camera.getDouble("hand-distance", 1.1);
        double armorDistance = camera == null ? 3.0 : camera.getDouble("armor-distance", 3.0);
        double turnSeconds = camera == null ? 16 : camera.getDouble("turn-seconds", 16);
        switch (kind) {
            case "armor" -> {
                Location chest = subject.clone().add(0, 1.0, 0);
                place(player, lookAt(chest.clone().add(0, 0.45, armorDistance), chest));
                turntable(plugin, player, session, subject, turnSeconds);
            }
            case "weapons" -> place(player, rightHand(subject, handDistance));
            default -> place(player, aim(subject.clone().add(0, 0.5, 0), blockDistance, ISO_YAW, ISO_PITCH));
        }
        player.sendActionBar(Component.text(kind + " " + (index + 1) + "/" + shots.size() + ": " + ContentRegistrar.title(shot.id())
            + "   (F1 hides the HUD)", NamedTextColor.GRAY));
    }

    /** The studios of a kind, in build order. */
    private static List<Shot> shots(Occultech plugin, String kind) {
        List<Shot> shots = new ArrayList<>();
        File file = new File(plugin.getDataFolder(), "showcase.yml");
        if (!file.exists()) {
            return shots;
        }
        YamlConfiguration data = YamlConfiguration.loadConfiguration(file);
        World world = Bukkit.getWorld(data.getString("world", Bukkit.getWorlds().get(0).getName()));
        for (String entry : data.getStringList("studios")) {
            String[] p = entry.split(";");
            if (p.length == 6 && p[0].equals(kind) && world != null) {
                shots.add(new Shot(p[0], world, Integer.parseInt(p[1]), Integer.parseInt(p[2]), Integer.parseInt(p[3]), Integer.parseInt(p[4]), p[5]));
            }
        }
        return shots;
    }

    /**
     * A camera looking at {@code target} from {@code distance} away, {@code yaw} degrees round from the front (south)
     * towards the east and {@code pitch} degrees above it.
     */
    private static Location aim(Location target, double distance, double yaw, double pitch) {
        double horizontal = distance * Math.cos(Math.toRadians(pitch));
        Vector offset = new Vector(horizontal * Math.sin(Math.toRadians(yaw)), distance * Math.sin(Math.toRadians(pitch)),
            horizontal * Math.cos(Math.toRadians(yaw)));
        return lookAt(target.clone().add(offset), target);
    }

    /** The mannequin faces south, so its right hand is on its west side, a little below the shoulder; seen from front-right. */
    private static Location rightHand(Location feet, double distance) {
        Location hand = feet.clone().add(-0.4, 0.8, 0.25);
        Vector from = new Vector(-0.5, 0.25, 0.83).normalize().multiply(distance);
        return lookAt(hand.clone().add(from), hand);
    }

    private static Location lookAt(Location eye, Location target) {
        Vector v = target.toVector().subtract(eye.toVector());
        Location at = eye.clone();
        at.setYaw((float) Math.toDegrees(Math.atan2(-v.getX(), v.getZ())));
        at.setPitch((float) Math.toDegrees(-Math.atan2(v.getY(), Math.hypot(v.getX(), v.getZ()))));
        return at;
    }

    /** Puts the player's eyes at a camera spot (spectators' eyes are 1.62 above their feet). */
    private static void place(Player player, Location eye) {
        player.teleport(eye.clone().subtract(0, EYE, 0));
    }

    /** Turns the studio's mannequin a full turn every {@code seconds}, every tick, until the camera moves on. */
    private static void turntable(Occultech plugin, Player player, Session session, Location feet, double seconds) {
        session.turning = feet.getWorld().getNearbyEntities(feet, 1, 2, 1, e -> e instanceof Mannequin
            && e.getPersistentDataContainer().has(Keys.SHOWCASE, PersistentDataType.BYTE)).stream()
            .map(Mannequin.class::cast).findFirst().orElse(null);
        if (session.turning == null) {
            return;
        }
        double step = 360.0 / Math.max(1, seconds * 20);
        double[] yaw = { 0 };
        session.turntable = Bukkit.getScheduler().runTaskTimer(plugin, () -> {
            if (session.turning == null || !session.turning.isValid() || !player.isOnline()) {
                stopTurntable(session);
                return;
            }
            yaw[0] = (yaw[0] + step) % 360;
            session.turning.setRotation((float) yaw[0], 0);
        }, 1L, 1L);
    }

    private static void stopTurntable(Session session) {
        if (session.turntable != null) {
            session.turntable.cancel();
            session.turntable = null;
        }
        if (session.turning != null && session.turning.isValid()) {
            session.turning.setRotation(0, 0);   // back to facing the front
        }
        session.turning = null;
    }
}
