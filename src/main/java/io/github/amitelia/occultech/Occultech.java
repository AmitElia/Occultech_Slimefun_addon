package io.github.amitelia.occultech;

import java.io.IOException;
import java.io.InputStream;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.NamespacedKey;
import org.bukkit.plugin.java.JavaPlugin;

import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.tier0.Tier0Bosses;
import io.github.amitelia.occultech.boss.tier1.Tier1Bosses;
import io.github.amitelia.occultech.boss.tier2.Tier2Bosses;
import io.github.amitelia.occultech.boss.tier3.Tier3Bosses;
import io.github.amitelia.occultech.content.ItemCatalog;
import io.github.amitelia.occultech.debug.OccultechCommand;
import io.github.amitelia.occultech.items.DecorationService;
import io.github.amitelia.occultech.items.GearListener;
import io.github.amitelia.occultech.items.HeldWeapons;
import io.github.amitelia.occultech.items.MinionService;
import io.github.amitelia.occultech.items.OccultechFightHooks;
import io.github.amitelia.occultech.items.RitualService;
import io.github.amitelia.occultech.items.ServitorService;
import io.github.amitelia.occultech.items.WeaponListener;
import io.github.amitelia.occultech.setup.ContentRegistrar;
import io.github.thebusybiscuit.slimefun4.api.SlimefunAddon;

public final class Occultech extends JavaPlugin implements SlimefunAddon {

    private static Occultech instance;

    private ItemCatalog catalog;
    private BossService bosses;
    private io.github.amitelia.occultech.event.RaidService raids;
    private RitualService rituals;
    private ServitorService servitors;
    private MinionService minions;
    private DecorationService decorations;
    private io.github.amitelia.occultech.items.TalismanService talismans;
    private ContentRegistrar registrar;
    private io.github.amitelia.occultech.pack.ResourcePackService resourcePack;
    private io.github.amitelia.occultech.items.BlockSkinService skins;
    private io.github.amitelia.occultech.items.CustomBlockService customBlocks;

    @Override
    public void onEnable() {
        instance = this;
        saveDefaultConfig();
        // add settings introduced by newer versions to an existing config.yml
        getConfig().options().copyDefaults(true);
        saveConfig();

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
        bosses.setHealthScaling(getConfig().getDouble("bosses.health-multiplier", 1.0), new io.github.amitelia.occultech.boss.GroupScaling(
            getConfig().getDouble("bosses.group-scaling", 0.45), getConfig().getDouble("bosses.group-exponent", 0.75),
            getConfig().getInt("bosses.group-cap", 5)));
        bosses.setMinFightDistance(getConfig().getDouble("bosses.min-fight-distance", 96));
        bosses.setAwaySeconds(getConfig().getInt("bosses.away-seconds", 180));
        Tier0Bosses.all().forEach(bosses::register);
        Tier1Bosses.all().forEach(bosses::register);
        Tier2Bosses.all().forEach(bosses::register);
        Tier3Bosses.all().forEach(bosses::register);
        rituals = new RitualService(this, bosses, hooks);
        servitors = new ServitorService(this);
        minions = new MinionService(this);
        decorations = new DecorationService(this);
        talismans = new io.github.amitelia.occultech.items.TalismanService(this);
        servitors.setRituals(rituals);
        resourcePack = new io.github.amitelia.occultech.pack.ResourcePackService(this);
        resourcePack.load();
        io.github.amitelia.occultech.boss.FloorDecals.enable(this, resourcePack.hasSigils());   // boss-fight floor markings
        // custom blocks before the items: a custom block's item is made of the block state it places (no blink)
        customBlocks = new io.github.amitelia.occultech.items.CustomBlockService(this, resourcePack);
        customBlocks.start();
        registrar = new ContentRegistrar(this, catalog, rituals);
        registrar.registerAll();
        registrar.problems().forEach(problem -> getLogger().warning("Content problem: " + problem));

        bosses.start();
        raids = new io.github.amitelia.occultech.event.RaidService(this, bosses);
        raids.start();
        resourcePack.start();
        skins = new io.github.amitelia.occultech.items.BlockSkinService(this, resourcePack, customBlocks);
        skins.start();
        getServer().getPluginManager().registerEvents(new io.github.amitelia.occultech.core.ClearLagGuard(), this);
        getServer().getPluginManager().registerEvents(new io.github.amitelia.occultech.items.CircleGuard(rituals), this);
        getServer().getPluginManager().registerEvents(new WeaponListener(this), this);
        getServer().getPluginManager().registerEvents(new GearListener(this), this);
        getServer().getPluginManager().registerEvents(new HeldWeapons(this), this);
        getServer().getPluginManager().registerEvents(new io.github.amitelia.occultech.items.HollowGearListener(this), this);
        getServer().getPluginManager().registerEvents(new io.github.amitelia.occultech.items.CosmeticListener(decorations), this);
        getCommand("occultech").setExecutor(new OccultechCommand(this));
        io.github.amitelia.occultech.debug.OccultechCommand.startShowcaseLoop(this);

        getLogger().info("Occultech enabled: " + registrar.stacks().size() + " items, " + rituals.recipes().size()
            + " rituals, " + registrar.researchCount() + " researches - the circles are listening.");
    }

    @Override
    public void onDisable() {
        if (rituals != null) {
            rituals.shutdown();
        }
        if (raids != null) {
            raids.shutdown();   // before the bosses: its fights end as dismissed, not as a shutdown to resume
        }
        if (bosses != null) {
            bosses.shutdown();
        }
        if (servitors != null) {
            servitors.shutdown();
        }
        if (minions != null) {
            minions.shutdown();
        }
        if (decorations != null) {
            decorations.shutdown();
        }
        if (talismans != null) {
            talismans.shutdown();
        }
        if (resourcePack != null) {
            resourcePack.shutdown();
        }
        if (registrar != null && registrar.arcaneAltar() != null) {
            registrar.arcaneAltar().shutdown();
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

    /** The Staff Raid (server-wide event). */
    public io.github.amitelia.occultech.event.RaidService raids() {
        return raids;
    }

    @Nonnull
    public ServitorService servitors() {
        return servitors;
    }

    @Nonnull
    public MinionService minions() {
        return minions;
    }

    @Nonnull
    public DecorationService decorations() {
        return decorations;
    }

    @Nonnull
    @javax.annotation.Nullable
    public io.github.amitelia.occultech.items.CustomBlockService customBlocks() {
        return customBlocks;
    }

    public io.github.amitelia.occultech.items.BlockSkinService skins() {
        return skins;
    }

    public io.github.amitelia.occultech.pack.ResourcePackService resourcePack() {
        return resourcePack;
    }

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
