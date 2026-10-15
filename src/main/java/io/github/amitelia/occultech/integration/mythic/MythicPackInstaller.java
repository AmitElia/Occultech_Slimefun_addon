package io.github.amitelia.occultech.integration.mythic;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Properties;
import java.util.logging.Logger;

import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;

import io.github.amitelia.occultech.Occultech;

/** Installs versioned bundled Mythic definitions and BetterModel models without replacing staff edits. */
public final class MythicPackInstaller {
    private static final String[] MYTHIC_FILES = {
        "packinfo.yml", "Mobs/Volley.yml", "Skills/Volley.yml", "DropTables/Volley.yml",
        "Mobs/BroodMother.yml", "Skills/BroodMother.yml",
        "Mobs/WitchCoven.yml", "Skills/WitchCoven.yml",
        "Mobs/TheUnbound.yml", "Skills/TheUnbound.yml",
        "Mobs/NightMatriarch.yml", "Skills/NightMatriarch.yml",
        "Mobs/Masquerade.yml", "Skills/Masquerade.yml",
        "Mobs/MireMonarch.yml", "Skills/MireMonarch.yml"
    };
    private static final String[] MODELS = {
        "occultech_volley.bbmodel", "occultech_volley_ward.bbmodel", "occultech_brood_mother.bbmodel",
        "occultech_witch_coven_cauldron.bbmodel", "occultech_witch_coven_bottles.bbmodel", "occultech_witch_coven_pot.bbmodel",
        "occultech_the_unbound.bbmodel", "occultech_night_matriarch.bbmodel",
        "occultech_masquerade.bbmodel", "occultech_masquerade_jack.bbmodel",
        "occultech_mire_monarch.bbmodel"
    };
    private static final String STAMP = ".occultech-installed.properties";

    private MythicPackInstaller() {}

    /** @return true when Mythic must reload to see new definitions */
    public static boolean install(Occultech plugin) throws IOException {
        Plugin mythic = Bukkit.getPluginManager().getPlugin("MythicMobs");
        if (mythic == null || !mythic.isEnabled()) {
            return false;
        }
        return install(plugin, mythic.getDataFolder().toPath().resolve("Packs").resolve("Occultech"), "mythic/", MYTHIC_FILES);
    }

    /** Boss models into BetterModel's model folder; BetterModel builds them into its pack, which build_pack.py merges. */
    public static boolean installModels(Occultech plugin) throws IOException {
        Plugin betterModel = Bukkit.getPluginManager().getPlugin("BetterModel");
        if (betterModel == null || !betterModel.isEnabled()) {
            return false;
        }
        return install(plugin, betterModel.getDataFolder().toPath().resolve("models"), "models/", MODELS);
    }

    private static boolean install(Occultech plugin, Path folder, String resourceRoot, String[] files) throws IOException {
        Files.createDirectories(folder);
        Properties previous = new Properties();
        // the models folder is shared with other models, so its stamp names Occultech
        Path stamp = folder.resolve(STAMP);
        if (Files.exists(stamp)) {
            try (InputStream in = Files.newInputStream(stamp)) {
                previous.load(in);
            }
        }
        Properties next = new Properties();
        Logger log = plugin.getLogger();
        boolean changed = false;
        for (String name : files) {
            byte[] bundled;
            try (InputStream in = plugin.getResource(resourceRoot + name)) {
                if (in == null) throw new IOException("Missing bundled file " + resourceRoot + name);
                bundled = in.readAllBytes();
            }
            Path target = folder.resolve(name).normalize();
            if (!target.startsWith(folder)) throw new IOException("Unsafe bundled path " + name);
            String oldHash = previous.getProperty(name);
            String currentHash = Files.exists(target) ? sha256(Files.readAllBytes(target)) : null;
            // untouched since the last install, or already exactly the bundled file (a copy is not a staff edit)
            if (currentHash == null || currentHash.equals(oldHash) || currentHash.equals(sha256(bundled))) {
                if (!sha256(bundled).equals(currentHash)) {
                    Files.createDirectories(target.getParent());
                    Path temp = Files.createTempFile(target.getParent(), ".occultech-", ".tmp");
                    try {
                        Files.write(temp, bundled);
                        Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING);
                    } finally {
                        Files.deleteIfExists(temp);
                    }
                    changed = true;
                }
                next.setProperty(name, sha256(bundled));
            } else {
                log.info("Keeping staff-edited file " + target + " (delete it to get the bundled version back)");
                next.setProperty(name, oldHash == null ? "staff-managed" : oldHash);
            }
        }
        try (var out = Files.newOutputStream(stamp)) {
            next.store(out, "Last Occultech-installed SHA-256 per file; staff edits are preserved");
        }
        return changed;
    }

    private static String sha256(byte[] bytes) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
