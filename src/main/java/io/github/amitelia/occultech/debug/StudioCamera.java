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
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.scheduler.BukkitTask;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

/**
 * {@code /occultech studio <kind> [next|prev|N]}: steps through the showcase studios of one kind, putting the camera at
 * the same spot in each (spectator mode: no gravity, no hand drawn; F1 hides the HUD). {@code /occultech studio stop}
 * gives back the game mode and position from before.
 * <ul>
 * <li>armor: a slow orbit round the mannequin. The player watches through an invisible display entity that the server
 * glides round the circle (its teleports are interpolated by the client), so the turn is smooth, not tick-stepped.</li>
 * <li>weapons: a close-up of the mannequin's right hand and the weapon in it.</li>
 * <li>machines, cosmetics: an isometric view (45 degrees round, 35 down) of the block on the white backdrop.</li>
 * <li>rituals: the same from higher (45 down), the whole circle in shot.</li>
 * </ul>
 * The studios come from {@code showcase.yml} ({@code studios}: "kind;x;y;z;size;ID", the subject block and its size).
 */
final class StudioCamera {

    /** One full turn of the armor orbit, in ticks, and how often the camera moves (its interpolation spans the gap). */
    private static final int ORBIT_TICKS = 320;
    private static final int ORBIT_STEP = 2;
    private static final double ORBIT_RADIUS = 3.2;
    private static final double ISO_YAW = 45;
    private static final double ISO_PITCH = 35.26;
    private static final double RITUAL_PITCH = 45;
    private static final double EYE = 1.62;

    private record Shot(String kind, World world, int x, int y, int z, int size, String id) {}

    private static final class Session {
        GameMode previousMode;
        Location previousSpot;
        String kind;
        int index;
        ItemDisplay rig;
        BukkitTask orbit;
    }

    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    private StudioCamera() {}

    static void command(Occultech plugin, Player player, String kind, String which) {
        kind = kind.toLowerCase(java.util.Locale.ROOT);
        Session session = SESSIONS.get(player.getUniqueId());
        if (kind.equals("stop")) {
            if (session != null) {
                stopOrbit(session);
                player.setSpectatorTarget(null);
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

        stopOrbit(session);
        player.setSpectatorTarget(null);
        player.setGameMode(GameMode.SPECTATOR);
        Location subject = new Location(shot.world(), shot.x() + 0.5, shot.y(), shot.z() + 0.5);
        switch (kind) {
            case "armor" -> orbit(plugin, player, session, subject);
            case "weapons" -> place(player, rightHand(subject));
            case "rituals" -> place(player, aim(subject.clone().add(0, 0.3, 0), 2.6 + shot.size() * 1.15, ISO_YAW, RITUAL_PITCH));
            default -> place(player, aim(subject.clone().add(0, 0.5, 0), 3.4 + shot.size() * 1.1, ISO_YAW, ISO_PITCH));
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

    /** The mannequin faces south, so its right hand is on its west side, a little below the shoulder. */
    private static Location rightHand(Location feet) {
        Location hand = feet.clone().add(-0.4, 0.8, 0.25);
        return lookAt(hand.clone().add(-0.75, 0.35, 1.25), hand);
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

    private static void orbit(Occultech plugin, Player player, Session session, Location feet) {
        Location target = feet.clone().add(0, 1.05, 0);
        double height = 0.55;
        Location start = lookAt(target.clone().add(0, height, ORBIT_RADIUS), target);
        place(player, start);
        session.rig = feet.getWorld().spawn(start, ItemDisplay.class, rig -> {
            rig.setPersistent(false);
            rig.setTeleportDuration(ORBIT_STEP);
        });
        int[] tick = { 0 };
        session.orbit = Bukkit.getScheduler().runTaskTimer(plugin, () -> {
            if (!player.isOnline() || session.rig == null || !session.rig.isValid()) {
                stopOrbit(session);
                return;
            }
            if (tick[0] == 2) {
                player.setSpectatorTarget(session.rig);   // once the rig is known to the client
            }
            tick[0] += ORBIT_STEP;
            double angle = 2 * Math.PI * tick[0] / ORBIT_TICKS;
            Location at = lookAt(target.clone().add(ORBIT_RADIUS * Math.sin(angle), height, ORBIT_RADIUS * Math.cos(angle)), target);
            session.rig.teleport(at);
        }, ORBIT_STEP, ORBIT_STEP);
    }

    private static void stopOrbit(Session session) {
        if (session.orbit != null) {
            session.orbit.cancel();
            session.orbit = null;
        }
        if (session.rig != null) {
            session.rig.remove();
            session.rig = null;
        }
    }
}
