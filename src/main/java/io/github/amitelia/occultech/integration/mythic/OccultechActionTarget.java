package io.github.amitelia.occultech.integration.mythic;

import java.util.Collection;
import java.util.List;

import org.bukkit.entity.Entity;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.config.MythicLineConfig;
import io.lumine.mythic.api.skills.SkillMetadata;
import io.lumine.mythic.bukkit.BukkitAdapter;
import io.lumine.mythic.bukkit.MythicBukkit;
import io.lumine.mythic.bukkit.events.MythicTargeterLoadEvent;
import io.lumine.mythic.core.skills.SkillExecutor;
import io.lumine.mythic.core.skills.targeters.IEntitySelector;
import io.lumine.mythic.core.utils.annotations.MythicTargeter;

/** The target the caster's current action locked (BossFight.playAction with a target), if still in the fight. */
@MythicTargeter(author = "Occultech", name = "OccultechActionTarget", description = "The current action's target")
public final class OccultechActionTarget extends IEntitySelector {
    public OccultechActionTarget(MythicTargeterLoadEvent event) {
        this(MythicBukkit.inst().getSkillManager(), event.getConfig());
    }

    public OccultechActionTarget(SkillExecutor manager, MythicLineConfig config) {
        super(manager, config);
    }

    @Override
    public Collection<AbstractEntity> getEntities(SkillMetadata data) {
        BossFight fight = Occultech.instance().bosses().fightFor(data.getCaster().getEntity().getBukkitEntity());
        Entity target = fight == null ? null : fight.actionTarget();
        return target == null ? List.of() : List.of(BukkitAdapter.adapt(target));
    }
}
