package io.github.amitelia.occultech.integration.mythic;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.skills.conditions.IEntityCondition;
import io.lumine.mythic.bukkit.events.MythicConditionLoadEvent;
import io.lumine.mythic.core.skills.SkillCondition;
import io.lumine.mythic.core.utils.annotations.MythicCondition;

/** {@code occultechPhase{p=2}}: the entity's fight is in that phase (or a range, with {@code min=} and {@code max=}). */
@MythicCondition(author = "Occultech", name = "occultechPhase", description = "The boss fight's phase")
public final class OccultechPhase extends SkillCondition implements IEntityCondition {
    private final int exact;
    private final int min;
    private final int max;

    public OccultechPhase(MythicConditionLoadEvent event) {
        super(event.getConditionName());
        exact = event.getConfig().getInteger(new String[] {"phase", "p"}, 0);
        min = event.getConfig().getInteger(new String[] {"min"}, Integer.MIN_VALUE);
        max = event.getConfig().getInteger(new String[] {"max"}, Integer.MAX_VALUE);
    }

    @Override
    public boolean check(AbstractEntity entity) {
        BossFight fight = Occultech.instance().bosses().fightFor(entity.getBukkitEntity());
        if (fight == null) {
            return false;
        }
        int phase = fight.phase();
        return (exact == 0 || phase == exact) && phase >= min && phase <= max;
    }
}
