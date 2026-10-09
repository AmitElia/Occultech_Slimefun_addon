package io.github.amitelia.occultech.event;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.logging.Logger;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;

import com.destroystokyo.paper.profile.ProfileProperty;

import io.papermc.paper.datacomponent.item.ResolvableProfile;

/**
 * The skins the raid's bodies wear. By default a staff member's skin is looked up by their username, which gives their
 * Mojang account's skin - not the one a skin plugin (SkinsRestorer and the like) shows on the server. An admin copies the
 * skin a player wears right now with {@code /occultech event skin <staff> <player>}; it's kept in {@code raid-skins.yml}
 * (the signed texture, keyed by the staff member's username) and used from then on. A roster {@code skin:} can also be a
 * texture URL ({@code http://textures.minecraft.net/texture/...}) or its hash.
 */
public final class RaidSkins {

    private static final String TEXTURE_URL = "http://textures.minecraft.net/texture/";
    /** username (lower case) -> {texture value, signature or null} */
    private static final Map<String, String[]> SAVED = new HashMap<>();
    @Nullable private static File file;

    private RaidSkins() {}

    static void load(@Nonnull File from, @Nonnull Logger log) {
        file = from;
        SAVED.clear();
        if (!from.exists()) {
            return;
        }
        ConfigurationSection skins = YamlConfiguration.loadConfiguration(from).getConfigurationSection("skins");
        if (skins == null) {
            return;
        }
        for (String name : skins.getKeys(false)) {
            String value = skins.getString(name + ".value");
            if (value != null) {
                SAVED.put(name.toLowerCase(Locale.ROOT), new String[] { value, skins.getString(name + ".signature") });
            }
        }
        log.info("Staff Raid: " + SAVED.size() + " saved skin(s) from " + from.getName());
    }

    /** The profile a body wearing {@code skin} (a username, a texture URL or a texture hash) shows. */
    @Nonnull
    public static ResolvableProfile profile(@Nonnull String skin) {
        String[] saved = SAVED.get(skin.toLowerCase(Locale.ROOT));
        if (saved != null) {
            return ResolvableProfile.resolvableProfile().name(skin).addProperty(new ProfileProperty("textures", saved[0], saved[1])).build();
        }
        String url = skin.startsWith("http") ? skin : skin.matches("[0-9a-f]{40,80}") ? TEXTURE_URL + skin : null;
        if (url != null) {
            String json = "{\"textures\":{\"SKIN\":{\"url\":\"" + url + "\"}}}";
            String value = Base64.getEncoder().encodeToString(json.getBytes(StandardCharsets.UTF_8));
            return ResolvableProfile.resolvableProfile().addProperty(new ProfileProperty("textures", value)).build();
        }
        return ResolvableProfile.resolvableProfile().name(skin).build();
    }

    /** Saves the skin {@code from} wears right now as {@code skin}'s; false if they have none (an offline-mode server). */
    static boolean copy(@Nonnull String skin, @Nonnull Player from) {
        for (ProfileProperty property : from.getPlayerProfile().getProperties()) {
            if (property.getName().equals("textures")) {
                SAVED.put(skin.toLowerCase(Locale.ROOT), new String[] { property.getValue(), property.getSignature() });
                save();
                return true;
            }
        }
        return false;
    }

    /** Forgets a saved skin: {@code skin} is looked up by name again. */
    static boolean reset(@Nonnull String skin) {
        boolean had = SAVED.remove(skin.toLowerCase(Locale.ROOT)) != null;
        save();
        return had;
    }

    private static void save() {
        if (file == null) {
            return;
        }
        YamlConfiguration yaml = new YamlConfiguration();
        yaml.options().setHeader(java.util.List.of("Staff Raid skins copied in game (/occultech event skin <staff> <player>)."));
        SAVED.forEach((name, texture) -> {
            yaml.set("skins." + name + ".value", texture[0]);
            if (texture[1] != null) {
                yaml.set("skins." + name + ".signature", texture[1]);
            }
        });
        try {
            yaml.save(file);
        } catch (IOException e) {
            throw new java.io.UncheckedIOException("Couldn't save " + file.getName(), e);
        }
    }
}
