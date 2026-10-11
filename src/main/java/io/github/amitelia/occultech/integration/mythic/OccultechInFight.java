package io.github.amitelia.occultech.integration.mythic;

import io.github.amitelia.occultech.Occultech;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.skills.conditions.IEntityCondition;
import io.lumine.mythic.bukkit.events.MythicConditionLoadEvent;
import io.lumine.mythic.core.skills.SkillCondition;
import io.lumine.mythic.core.utils.annotations.MythicCondition;

/** {@code occultechInFight}: the entity belongs to a running Occultech fight (a boss, an add, an object). */
@MythicCondition(author = "Occultech", name = "occultechInFight", description = "Part of an Occultech boss fight")
public final class OccultechInFight extends SkillCondition implements IEntityCondition {
    public OccultechInFight(MythicConditionLoadEvent event) {
        super(event.getConditionName());
    }

    @Override
    public boolean check(AbstractEntity entity) {
        return Occultech.instance().bosses().fightFor(entity.getBukkitEntity()) != null;
    }
}
