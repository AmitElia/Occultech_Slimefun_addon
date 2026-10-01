package io.github.amitelia.occultech.pack;

import com.sun.net.httpserver.HttpServer;
import net.kyori.adventure.resource.ResourcePackInfo;
import net.kyori.adventure.resource.ResourcePackRequest;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.NamespacedKey;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.plugin.java.JavaPlugin;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.logging.Logger;

/**
 * Occultech's resource pack: the textures and models of its items, all in its own {@code occultech} namespace (no
 * vanilla item is retextured). The pack is built from the art by {@code tools/art/build_pack.py} and packaged in the jar.
 *
 * <p>Delivery ({@code resource-pack.mode} in config.yml):
 * <ul>
 * <li>{@code nexo} - the pack is copied into Nexo's {@code pack/external_packs}; Nexo merges it into its own pack and
 * sends it. Run {@code /nexo reload pack} once after installing or updating Occultech.</li>
 * <li>{@code self-host} - Occultech serves the pack from a small built-in web server and sends it to players on join,
 * as an additional pack (it never replaces the server's own pack).</li>
 * <li>{@code auto} (default) - Nexo if it's installed, otherwise self-host.</li>
 * <li>{@code off} - nothing is sent; item models are still set, so another pack plugin can carry the pack.</li>
 * </ul>
 * Items get their model through the {@code item_model} component ({@link #modelFor}); only items that actually have a
 * model in the pack get one, the rest keep their vanilla look.
 */
public final class ResourcePackService implements Listener {

    public static final String NAMESPACE = "occultech";
    private static final String PACK = "occultech-pack.zip";
    private static final String ITEMS = "occultech-pack-items.txt";
    /** A fixed id, so a client replaces the old version of our pack instead of stacking a new one. */
    private static final UUID PACK_ID = UUID.nameUUIDFromBytes("occultech:resource-pack".getBytes(StandardCharsets.UTF_8));

    private final JavaPlugin plugin;
    private final Logger log;
    private final Set<String> modelled = new HashSet<>();
    private byte[] pack;
    private String sha1 = "";
    private boolean itemModels = true;
    private String mode = "off";
    @Nullable private HttpServer server;
    @Nullable private URI url;
    private boolean required;
    private String prompt = "";

    public ResourcePackService(@Nonnull JavaPlugin plugin) {
        this.plugin = plugin;
        this.log = plugin.getLogger();
    }

    /** Reads the pack and its item list from the jar. Call before items are registered (they need {@link #modelFor}). */
    public void load() {
        ConfigurationSection cfg = plugin.getConfig().getConfigurationSection("resource-pack");
        itemModels = cfg == null || cfg.getBoolean("item-models", true);
        try (InputStream in = plugin.getResource(PACK)) {
            if (in == null) {
                log.warning("Resource pack: " + PACK + " is missing from the jar - items keep their vanilla look.");
                return;
            }
            pack = in.readAllBytes();
        } catch (IOException e) {
            log.warning("Resource pack: could not read " + PACK + ": " + e.getMessage());
            return;
        }
        sha1 = sha1(pack);
        try (InputStream in = plugin.getResource(ITEMS)) {
            if (in != null) {
                new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8)).lines()
                    .map(String::trim).filter(line -> !line.isEmpty() && !line.startsWith("#")).forEach(modelled::add);
            }
        } catch (IOException e) {
            log.warning("Resource pack: could not read " + ITEMS + ": " + e.getMessage());
        }
    }

    /** The {@code item_model} key for a recipes.yml item id, or null if the pack has no model for it (or models are off). */
    @Nullable
    public NamespacedKey modelFor(@Nonnull String itemId) {
        if (!itemModels || pack == null || !modelled.contains(itemId)) {
            return null;
        }
        return new NamespacedKey(NAMESPACE, itemId.toLowerCase(Locale.ROOT));
    }

    /** Starts delivering the pack (Nexo hand-off or the built-in web server). */
    public void start() {
        if (pack == null) {
            return;
        }
        ConfigurationSection cfg = plugin.getConfig().getConfigurationSection("resource-pack");
        String wanted = cfg == null ? "auto" : cfg.getString("mode", "auto").toLowerCase(Locale.ROOT);
        boolean nexo = Bukkit.getPluginManager().getPlugin("Nexo") != null;
        mode = wanted.equals("auto") ? (nexo ? "nexo" : "self-host") : wanted;
        try {
            Path copy = plugin.getDataFolder().toPath().resolve(PACK);
            Files.createDirectories(copy.getParent());
            Files.write(copy, pack);
        } catch (IOException e) {
            log.warning("Resource pack: could not write " + PACK + " to the plugin folder: " + e.getMessage());
        }
        switch (mode) {
            case "nexo" -> handToNexo();
            case "self-host" -> selfHost(cfg);
            case "off" -> log.info("Resource pack: delivery is off (" + modelled.size() + " item models are still set).");
            default -> log.warning("Resource pack: unknown mode '" + mode + "' (auto, nexo, self-host or off).");
        }
    }

    private void handToNexo() {
        Path target = plugin.getDataFolder().toPath().getParent().resolve("Nexo").resolve("pack").resolve("external_packs").resolve(PACK);
        try {
            Files.createDirectories(target.getParent());
            boolean changed = !Files.exists(target) || !sha1(Files.readAllBytes(target)).equals(sha1);
            Files.write(target, pack);
            log.info("Resource pack: handed to Nexo (" + target + ")." + (changed ? " It changed - run /nexo reload pack." : ""));
        } catch (IOException e) {
            log.warning("Resource pack: could not copy the pack into Nexo's external_packs: " + e.getMessage());
        }
    }

    private void selfHost(@Nullable ConfigurationSection cfg) {
        int port = cfg == null ? 8164 : cfg.getInt("port", 8164);
        String host = cfg == null ? "" : cfg.getString("public-host", "");
        if (host == null || host.isBlank()) {
            host = Bukkit.getIp().isBlank() ? "localhost" : Bukkit.getIp();
        }
        required = cfg != null && cfg.getBoolean("required", false);
        prompt = cfg == null ? "" : cfg.getString("prompt", "");
        try {
            server = HttpServer.create(new InetSocketAddress(port), 0);
            server.createContext("/", exchange -> {
                try (exchange) {
                    if (!"GET".equals(exchange.getRequestMethod()) && !"HEAD".equals(exchange.getRequestMethod())) {
                        exchange.sendResponseHeaders(405, -1);
                        return;
                    }
                    exchange.getResponseHeaders().set("Content-Type", "application/zip");
                    boolean head = "HEAD".equals(exchange.getRequestMethod());
                    exchange.sendResponseHeaders(200, head ? -1 : pack.length);
                    if (!head) {
                        try (OutputStream out = exchange.getResponseBody()) {
                            out.write(pack);
                        }
                    }
                }
            });
            server.start();
        } catch (IOException e) {
            log.warning("Resource pack: could not start the web server on port " + port + ": " + e.getMessage()
                + " - set resource-pack.port, or use mode nexo/off.");
            server = null;
            return;
        }
        url = URI.create("http://" + host + ":" + port + "/" + PACK + "?" + sha1.substring(0, 12));
        Bukkit.getPluginManager().registerEvents(this, plugin);
        log.info("Resource pack: serving " + modelled.size() + " item models at " + url + (required ? " (required)" : ""));
        Bukkit.getOnlinePlayers().forEach(this::send);
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        send(event.getPlayer());
    }

    /** Sends the pack to a player as an additional pack (their server pack stays). */
    public void send(@Nonnull Player player) {
        if (url == null) {
            return;
        }
        ResourcePackRequest request = ResourcePackRequest.resourcePackRequest()
            .packs(ResourcePackInfo.resourcePackInfo(PACK_ID, url, sha1))
            .replace(false)
            .required(required)
            .prompt(prompt == null || prompt.isBlank() ? null : Component.text(prompt, NamedTextColor.LIGHT_PURPLE))
            .build();
        player.sendResourcePacks(request);
    }

    public void shutdown() {
        if (server != null) {
            server.stop(0);
            server = null;
        }
    }

    // ------------------------------------------------------------------ for the self-test and /occultech

    public String mode() {
        return mode;
    }

    @Nullable
    public URI url() {
        return url;
    }

    public String sha1() {
        return sha1;
    }

    public int modelCount() {
        return modelled.size();
    }

    public int packSize() {
        return pack == null ? 0 : pack.length;
    }

    private static String sha1(byte[] data) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-1").digest(data));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
