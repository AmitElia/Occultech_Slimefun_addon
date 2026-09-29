package io.github.amitelia.occultech;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.NamespacedKey;
import org.bukkit.plugin.java.JavaPlugin;

import io.github.amitelia.occultech.setup.OccultechItems;
import io.github.amitelia.occultech.setup.OccultechResearches;
import io.github.thebusybiscuit.slimefun4.api.SlimefunAddon;

public final class Occultech extends JavaPlugin implements SlimefunAddon {

    private static Occultech instance;

    @Override
    public void onEnable() {
        instance = this;
        saveDefaultConfig();

        OccultechItems.setup(this);
        OccultechResearches.setup();

        getLogger().info("Occultech enabled - the circles are listening.");
    }

    @Override
    public void onDisable() {
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
