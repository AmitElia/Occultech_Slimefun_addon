package io.github.amitelia.occultech.boss;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * What a running fight needs to come back after a restart or crash (Session P3): which boss, how far along, each main
 * boss's health (in spawn order; 0 = already dead), the group size it was scaled for, who summoned it, and who has fought
 * it so far (damage and presence, for loot). Adds, hazards and breakable objects are not kept: they come back fresh.
 * Stored as one line in the altar's block data; pure Java, so it is unit tested.
 */
public record FightState(String bossId, int elapsed, List<Double> health, int playersAtStart, @Nullable UUID summoner,
    Map<UUID, Double> damage, Map<UUID, Integer> presence) {

    private static final String VERSION = "1";

    @Nonnull
    public String format() {
        StringBuilder out = new StringBuilder(VERSION).append('|').append(bossId).append('|').append(elapsed).append('|');
        for (int i = 0; i < health.size(); i++) {
            out.append(i == 0 ? "" : ",").append(String.format(java.util.Locale.ROOT, "%.4f", health.get(i)));
        }
        out.append('|').append(playersAtStart).append('|').append(summoner == null ? "-" : summoner.toString()).append('|');
        boolean first = true;
        for (UUID player : union()) {
            out.append(first ? "" : ",").append(player).append('=')
                .append(String.format(java.util.Locale.ROOT, "%.2f", damage.getOrDefault(player, 0.0))).append(':')
                .append(presence.getOrDefault(player, 0));
            first = false;
        }
        return out.toString();
    }

    private List<UUID> union() {
        List<UUID> players = new ArrayList<>(damage.keySet());
        for (UUID player : presence.keySet()) {
            if (!players.contains(player)) {
                players.add(player);
            }
        }
        return players;
    }

    /** The state in {@code line}, or null if it is missing or unreadable (the caller falls back to a refund). */
    @Nullable
    public static FightState parse(@Nullable String line) {
        if (line == null || line.isEmpty()) {
            return null;
        }
        try {
            String[] parts = line.split("\\|", -1);
            if (parts.length != 7 || !VERSION.equals(parts[0]) || parts[1].isEmpty()) {
                return null;
            }
            List<Double> health = new ArrayList<>();
            for (String value : parts[3].split(",")) {
                if (!value.isEmpty()) {
                    health.add(Math.max(0, Math.min(1, Double.parseDouble(value))));
                }
            }
            UUID summoner = "-".equals(parts[5]) ? null : UUID.fromString(parts[5]);
            Map<UUID, Double> damage = new HashMap<>();
            Map<UUID, Integer> presence = new HashMap<>();
            for (String entry : parts[6].split(",")) {
                if (entry.isEmpty()) {
                    continue;
                }
                String[] kv = entry.split("[=:]");
                UUID player = UUID.fromString(kv[0]);
                double dealt = Double.parseDouble(kv[1]);
                if (dealt > 0) {
                    damage.put(player, dealt);
                }
                presence.put(player, Integer.parseInt(kv[2]));
            }
            return new FightState(parts[1], Math.max(0, Integer.parseInt(parts[2])), health, Math.max(1, Integer.parseInt(parts[4])),
                summoner, damage, presence);
        } catch (RuntimeException e) {
            return null;
        }
    }
}
