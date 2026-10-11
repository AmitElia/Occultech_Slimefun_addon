package io.github.amitelia.occultech.integration.mythic;

import java.util.Locale;

import org.bukkit.entity.LivingEntity;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.plugin.java.JavaPlugin;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossService;
import io.lumine.mythic.bukkit.events.MythicReloadedEvent;

/**
 * {@code /mm reload} during a fight: Occultech owns the fight, so nothing about it depends on Mythic, but each running
 * fight's bodies are checked afterwards. Mythic re-applies its mob file to running mobs, so Occultech's carrier rules
 * (no despawning, persistence, group-scaled health) are put back. A carrier Mythic no longer tracks only loses its
 * cosmetic skills (logged); a boss model that went missing is put back.
 */
public final class MythicReloadWatch implements Listener {
    private final JavaPlugin plugin;
    private final BossService bosses;

    public MythicReloadWatch(JavaPlugin plugin, BossService bosses) {
        this.plugin = plugin;
        this.bosses = bosses;
    }

    @EventHandler
    public void onReload(MythicReloadedEvent event) {
        plugin.getServer().getScheduler().runTask(plugin, this::check);
    }

    /** @return how many bodies needed their model put back */
    public int check() {
        int restored = 0;
        boolean models = plugin.getServer().getPluginManager().isPluginEnabled("BetterModel");
        for (BossFight fight : bosses.fights()) {
            if (!fight.usesMythicBody()) {
                continue;
            }
            String model = "occultech_" + fight.spec().id().toLowerCase(Locale.ROOT);
            for (LivingEntity body : fight.bosses()) {
                fight.reapplyCarrier(body);      // Mythic re-applied the mob file: despawning, persistence, health
                if (!MythicBody.isActive(body.getUniqueId())) {
                    plugin.getLogger().warning("After /mm reload, Mythic no longer tracks " + fight.spec().id()
                        + "'s body: the fight goes on, without its cosmetic skills");
                }
                if (models && BetterModelVisuals.available(model) && BetterModelVisuals.count(body, model) == 0) {
                    BetterModelVisuals.attach(body, model);
                    restored++;
                }
            }
        }
        if (restored > 0) {
            plugin.getLogger().info("After /mm reload: put back " + restored + " boss model(s)");
        }
        return restored;
    }
}
