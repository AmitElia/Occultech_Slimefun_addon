package io.github.amitelia.occultech.integration.mythic;

import java.util.Collection;
import java.util.List;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.config.MythicLineConfig;
import io.lumine.mythic.api.skills.SkillMetadata;
import io.lumine.mythic.core.skills.SkillExecutor;
import io.lumine.mythic.core.skills.targeters.IEntitySelector;
import io.lumine.mythic.core.utils.annotations.MythicTargeter;
import io.lumine.mythic.bukkit.BukkitAdapter;
import io.lumine.mythic.bukkit.MythicBukkit;
import io.lumine.mythic.bukkit.events.MythicTargeterLoadEvent;

/** Living players inside the caster's own fight arena. */
@MythicTargeter(author = "Occultech", name = "OccultechFighters", description = "Arena-only fighters")
public final class OccultechFighters extends IEntitySelector {
    public OccultechFighters(MythicTargeterLoadEvent event) {
        this(MythicBukkit.inst().getSkillManager(), event.getConfig());
    }

    public OccultechFighters(SkillExecutor manager, MythicLineConfig config) {
        super(manager, config);
    }

    @Override
    public Collection<AbstractEntity> getEntities(SkillMetadata data) {
        BossFight fight = Occultech.instance().bosses().fightFor(data.getCaster().getEntity().getBukkitEntity());
        return fight == null ? List.of() : fight.players().stream().map(BukkitAdapter::adapt).map(e -> (AbstractEntity) e).toList();
    }
}
