package io.github.amitelia.occultech.integration.mythic;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.skills.conditions.IEntityCondition;
import io.lumine.mythic.bukkit.events.MythicConditionLoadEvent;
import io.lumine.mythic.core.skills.SkillCondition;
import io.lumine.mythic.core.utils.annotations.MythicCondition;

/** {@code occultechSolo}: the entity's fight has exactly one fighter in the arena right now. */
@MythicCondition(author = "Occultech", name = "occultechSolo", description = "One fighter in the arena")
public final class OccultechSolo extends SkillCondition implements IEntityCondition {
    public OccultechSolo(MythicConditionLoadEvent event) {
        super(event.getConditionName());
    }

    @Override
    public boolean check(AbstractEntity entity) {
        BossFight fight = Occultech.instance().bosses().fightFor(entity.getBukkitEntity());
        return fight != null && fight.players().size() == 1;
    }
}
