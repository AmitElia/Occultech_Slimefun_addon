package io.github.amitelia.occultech.integration.mythic;

import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.function.Consumer;

import org.bukkit.Location;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.plugin.java.JavaPlugin;

import io.github.amitelia.occultech.boss.BossBody;
import io.github.amitelia.occultech.boss.VanillaBody;
import io.lumine.mythic.api.mobs.MythicMob;
import io.lumine.mythic.api.mobs.entities.SpawnReason;
import io.lumine.mythic.api.skills.SkillTrigger;
import io.lumine.mythic.bukkit.BukkitAdapter;
import io.lumine.mythic.bukkit.MythicBukkit;
import io.lumine.mythic.core.mobs.ActiveMob;

/** Mythic owns configured carrier stats; Occultech still owns damage, targeting and lifecycle. */
public final class MythicBody implements BossBody {
    private static final SkillTrigger ACTION = SkillTrigger.create("OCCULTECHACTION");

    private final JavaPlugin plugin;
    private final String mode;
    private final VanillaBody vanilla = new VanillaBody();
    private final Set<String> warned = new HashSet<>();

    public MythicBody(JavaPlugin plugin, String mode) {
        this.plugin = plugin;
        this.mode = mode.toLowerCase(Locale.ROOT);
        ACTION.register();
    }

    @Override
    public boolean isMythic(String id) {
        return !"vanilla".equals(mode) && !id.isEmpty()
            && MythicBukkit.inst().getMobManager().getMythicMob("OCCULTECH_" + id).isPresent();
    }

    /** Whether Mythic still tracks this entity as one of its mobs. */
    public static boolean isActive(java.util.UUID id) {
        return MythicBukkit.inst().getMobManager().isActiveMob(id);
    }

    @Override
    public boolean isCarrier(LivingEntity entity) {
        return MythicBukkit.inst().getMobManager().isActiveMob(entity.getUniqueId());
    }

    @Override
    public <T extends LivingEntity> T spawn(String id, Class<T> type, Location at, Consumer<T> setup) {
        if (!isMythic(id)) {
            if ("mythic".equals(mode) && !id.isEmpty() && warned.add(id)) {
                plugin.getLogger().warning("Mythic definition OCCULTECH_" + id + " missing; using vanilla carriers for it");
            }
            return vanilla.spawn(id, type, at, setup);
        }
        MythicMob definition = MythicBukkit.inst().getMobManager().getMythicMob("OCCULTECH_" + id).orElseThrow();
        // Mythic runs a spawn callback before it applies the mob file (health, despawn, persistence), so Occultech's
        // setup runs after the spawn: the fight tags, group health scaling and chunk persistence must win
        ActiveMob active = definition.spawn(BukkitAdapter.adapt(at), 1, SpawnReason.SUMMON);
        Entity carrier = active == null ? null : active.getEntity().getBukkitEntity();
        if (!type.isInstance(carrier)) {
            if (carrier != null) {
                carrier.remove();
            }
            throw new IllegalStateException("OCCULTECH_" + id + " must spawn a " + type.getSimpleName());
        }
        T entity = type.cast(carrier);
        setup.accept(entity);
        return entity;
    }

    @Override
    public void playAction(LivingEntity entity, String bossId, String action) {
        MythicBukkit.inst().getMobManager().getMythicMob("OCCULTECH_" + bossId).ifPresent(mob -> {
            MythicBukkit.inst().getMobManager().getActiveMob(entity.getUniqueId()).ifPresent(active ->
                MythicBukkit.inst().getSkillManager().getSkill(bossId + "_" + action).ifPresent(skill ->
                    skill.execute(ACTION, active, BukkitAdapter.adapt(entity), BukkitAdapter.adapt(entity.getLocation()),
                        new HashSet<>(), new HashSet<>(), 1F)));
        });
    }

    @Override
    public void stop(LivingEntity entity) {
        MythicBukkit.inst().getMobManager().getActiveMob(entity.getUniqueId()).ifPresent(ActiveMob::remove);
    }

    @Override
    public io.github.amitelia.occultech.boss.Prop prop(String modelId, Location at) {
        if (!plugin.getServer().getPluginManager().isPluginEnabled("BetterModel")) {
            return null;
        }
        return BetterModelVisuals.prop(modelId, at);
    }

    @Override
    public List<String> extraRewards(String id) {
        return MythicLoot.roll(id, plugin.getLogger());
    }
}
