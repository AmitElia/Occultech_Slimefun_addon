package io.github.amitelia.occultech.boss;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;
import java.nio.file.Files;
import java.util.UUID;
import org.bukkit.configuration.file.YamlConfiguration;
import org.junit.jupiter.api.Test;

class CombatLogTest {

    @Test
    void writesWhatHappened() throws Exception {
        UUID alex = UUID.randomUUID();
        CombatLog log = new CombatLog("GALLUS", 3);
        log.taken(alex, "Alex", "Leap slam", 55, 7.5);
        log.taken(alex, "Alex", "Leap slam", 55, 7.5);
        log.taken(alex, "Alex", "Zone: yolk", 6, 1.2);
        log.dealt(alex, "Alex", "infinity blade", 39, 1.95, 40);
        log.dealt(alex, "Alex", "infinity blade", 39, 1.95, 250);
        log.died(alex, "Alex");

        File folder = Files.createTempDirectory("combat-log").toFile();
        log.write(folder, "VICTORY", 400, 1, 1.0);
        File[] files = folder.listFiles();
        assertEquals(1, files.length);
        YamlConfiguration yaml = YamlConfiguration.loadConfiguration(files[0]);
        assertEquals("GALLUS", yaml.getString("boss"));
        assertEquals(20.0, yaml.getDouble("seconds"), 1e-9);
        String base = "players." + alex;
        assertEquals(2, yaml.getInt(base + ".taken.Leap slam.hits"));
        assertEquals(15.0, yaml.getDouble(base + ".taken.Leap slam.after"), 1e-9);
        assertEquals(1, yaml.getInt(base + ".taken.Zone- yolk.hits"));
        assertEquals(1, yaml.getInt(base + ".deaths"));
        // 2 of 4 five-second windows had the boss taking damage
        assertEquals(0.5, yaml.getDouble("uptime"), 1e-9);
        assertTrue(log.summary(400).get(0).contains("GALLUS"));
    }
}
