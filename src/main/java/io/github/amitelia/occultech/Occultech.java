package io.github.amitelia.occultech;

import java.io.IOException;
import java.io.InputStream;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.NamespacedKey;
import org.bukkit.plugin.java.JavaPlugin;

import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.tier0.Tier0Bosses;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.debug.OccultechCommand;
import io.github.amitelia.occultech.items.OccultechFightHooks;
import io.github.amitelia.occultech.items.RitualService;
import io.github.amitelia.occultech.items.WeaponListener;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.SlimefunAddon;

public final class Occultech extends JavaPlugin implements SlimefunAddon {

    private static Occultech instance;

    private ItemCatalog catalog;
    private BossService bosses;
    private RitualService rituals;
    private ContentRegistrar registrar;

    @Override
    public void onEnable() {
        instance = this;
        saveDefaultConfig();

        try (InputStream in = getResource("recipes.yml")) {
            if (in == null) {
                throw new IllegalStateException("recipes.yml is missing from the jar");
            }
            catalog = ItemCatalog.load(in);
        } catch (IOException e) {
            throw new IllegalStateException("Could not read recipes.yml", e);
        }

        OccultechFightHooks hooks = new OccultechFightHooks();
        bosses = new BossService(this, hooks);
        Tier0Bosses.all().forEach(bosses::register);
        rituals = new RitualService(this, bosses, hooks);
        registrar = new ContentRegistrar(this, catalog, rituals);
        registrar.registerAll();
        registrar.problems().forEach(problem -> getLogger().warning("Content problem: " + problem));

        bosses.start();
        getServer().getPluginManager().registerEvents(new WeaponListener(this), this);
        getCommand("occultech").setExecutor(new OccultechCommand(this));

        getLogger().info("Occultech enabled: " + registrar.stacks().size() + " items, " + rituals.recipes().size()
            + " rituals, " + registrar.researchCount() + " researches - the circles are listening.");
    }

    @Override
    public void onDisable() {
        if (rituals != null) {
            rituals.shutdown();
        }
        if (bosses != null) {
            bosses.shutdown();
        }
        instance = null;
    }

    @Nonnull
    public static Occultech instance() {
        return instance;
    }

    @Nonnull
    public static NamespacedKey key(@Nonnull String id) {
        return new NamespacedKey(instance, id);
    }

    @Nonnull
    public ItemCatalog catalog() {
        return catalog;
    }

    @Nonnull
    public RitualService rituals() {
        return rituals;
    }

    @Nonnull
    public ContentRegistrar registrar() {
        return registrar;
    }

    @Nonnull
    @Override
    public JavaPlugin getJavaPlugin() {
        return this;
    }

    @Nullable
    @Override
    public String getBugTrackerURL() {
        return null;
    }
}
