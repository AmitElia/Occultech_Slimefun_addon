package io.github.amitelia.occultech.boss;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import javax.annotation.Nonnull;
import org.bukkit.configuration.file.YamlConfiguration;

/**
 * What happened in one fight, for balancing (Session B1): how long it took and how much of that time the boss was
 * actually being hurt; per player, the damage taken from each mechanic (raw, and after their armor) and their deaths;
 * the damage each player dealt to the boss, per weapon (raw, and what the boss's own armor let through). Written to
 * {@code plugins/Occultech/combat-log/} when the fight ends; {@code tools/balance.py} reads those files.
 */
public final class CombatLog {

    /** Damage of one kind: hits, raw total, total after armor. */
    private static final class Tally {
        int hits;
        double raw;
        double after;
    }

    private static final class Fighter {
        String name;
        final Map<String, Tally> taken = new LinkedHashMap<>();
        final Map<String, Tally> dealt = new LinkedHashMap<>();
        int deaths;
    }

    private static final int WINDOW = 100;

    private final String bossId;
    private final int tier;
    private final LocalDateTime started = LocalDateTime.now();
    private final Map<UUID, Fighter> fighters = new LinkedHashMap<>();
    private final Set<Integer> hurtWindows = new HashSet<>();

    CombatLog(String bossId, int tier) {
        this.bossId = bossId;
        this.tier = tier;
    }

    private Fighter fighter(UUID id, String name) {
        Fighter fighter = fighters.computeIfAbsent(id, k -> new Fighter());
        fighter.name = name;
        return fighter;
    }

    void taken(UUID player, String name, String mechanic, double raw, double after) {
        Tally tally = fighter(player, name).taken.computeIfAbsent(mechanic, k -> new Tally());
        tally.hits++;
        tally.raw += raw;
        tally.after += after;
    }

    void dealt(UUID player, String name, String weapon, double raw, double after, int elapsed) {
        Tally tally = fighter(player, name).dealt.computeIfAbsent(weapon, k -> new Tally());
        tally.hits++;
        tally.raw += raw;
        tally.after += after;
        if (after > 0) {
            hurtWindows.add(elapsed / WINDOW);
        }
    }

    void died(UUID player, String name) {
        fighter(player, name).deaths++;
    }

    /** Share of the fight's 5-second windows in which the boss took damage. */
    double uptime(int elapsed) {
        int windows = Math.max(1, (elapsed + WINDOW - 1) / WINDOW);
        return Math.min(1, hurtWindows.size() / (double) windows);
    }

    /** A few lines for {@code /occultech fights stats}. */
    @Nonnull
    List<String> summary(int elapsed) {
        double seconds = Math.max(1, elapsed / 20.0);
        List<String> out = new ArrayList<>();
        out.add(String.format(java.util.Locale.ROOT, "%s: %.0fs, boss hurt in %.0f%% of it", bossId, seconds, uptime(elapsed) * 100));
        for (Fighter f : fighters.values()) {
            double took = f.taken.values().stream().mapToDouble(t -> t.after).sum();
            double dealt = f.dealt.values().stream().mapToDouble(t -> t.raw).sum();
            out.add(String.format(java.util.Locale.ROOT, "  %s: took %.1f (%.2f/s), dealt %.0f raw (%.1f/s), %d death(s)", f.name, took,
                took / seconds, dealt, dealt / seconds, f.deaths));
            f.taken.entrySet().stream().sorted((a, b) -> Double.compare(b.getValue().after, a.getValue().after)).limit(4).forEach(e ->
                out.add(String.format(java.util.Locale.ROOT, "    %s: %d hit(s), %.1f after armor", e.getKey(), e.getValue().hits, e.getValue().after)));
        }
        return out;
    }

    /** Writes the log; {@code result} and {@code playersAtStart} describe the fight. */
    void write(File folder, String result, int elapsed, int playersAtStart, double healthMultiplier) {
        YamlConfiguration yaml = new YamlConfiguration();
        yaml.set("boss", bossId);
        yaml.set("tier", tier);
        yaml.set("started", started.toString());
        yaml.set("result", result);
        yaml.set("seconds", elapsed / 20.0);
        yaml.set("players-at-start", playersAtStart);
        yaml.set("health-multiplier", healthMultiplier);
        yaml.set("uptime", uptime(elapsed));
        for (Map.Entry<UUID, Fighter> entry : fighters.entrySet()) {
            String base = "players." + entry.getKey();
            Fighter f = entry.getValue();
            yaml.set(base + ".name", f.name);
            yaml.set(base + ".deaths", f.deaths);
            f.taken.forEach((mechanic, t) -> tally(yaml, base + ".taken." + key(mechanic), t));
            f.dealt.forEach((weapon, t) -> tally(yaml, base + ".dealt." + key(weapon), t));
        }
        folder.mkdirs();
        String file = started.format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss")) + "_" + bossId.toLowerCase() + ".yml";
        try {
            yaml.save(new File(folder, file));
        } catch (IOException ignored) {
            // a missing log never breaks a fight
        }
    }

    private static void tally(YamlConfiguration yaml, String path, Tally t) {
        yaml.set(path + ".hits", t.hits);
        yaml.set(path + ".raw", Math.round(t.raw * 10) / 10.0);
        yaml.set(path + ".after", Math.round(t.after * 10) / 10.0);
    }

    private static String key(String label) {
        return label.replace('.', '_').replace(':', '-');
    }
}
