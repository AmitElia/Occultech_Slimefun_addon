package io.github.amitelia.occultech.integration.mythic;

import java.io.File;

import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.config.MythicLineConfig;
import io.lumine.mythic.api.skills.ITargetedEntitySkill;
import io.lumine.mythic.api.skills.SkillMetadata;
import io.lumine.mythic.api.skills.SkillResult;
import io.lumine.mythic.core.skills.SkillExecutor;
import io.lumine.mythic.core.skills.SkillMechanic;
import io.lumine.mythic.core.utils.annotations.MythicMechanic;
import io.lumine.mythic.bukkit.MythicBukkit;
import io.lumine.mythic.bukkit.events.MythicMechanicLoadEvent;

/** The sole permitted Mythic skill damage path for an Occultech fight. */
@MythicMechanic(author = "Occultech", name = "occultechHit", description = "Labelled arena-only fight damage")
public final class OccultechHit extends SkillMechanic implements ITargetedEntitySkill {
    private final String mechanicName;

    public OccultechHit(MythicMechanicLoadEvent event) {
        this(MythicBukkit.inst().getSkillManager(), null, event.getMechanicName(), event.getConfig());
    }

    public OccultechHit(SkillExecutor manager, File file, String line, MythicLineConfig config) {
        super(manager, file, line, config);
        mechanicName = config.getString(new String[] {"mechanic", "m"}, "");
    }

    @Override
    public SkillResult castAtEntity(SkillMetadata data, AbstractEntity target) {
        Entity source = data.getCaster().getEntity().getBukkitEntity();
        if (!(source instanceof LivingEntity living) || !(target.getBukkitEntity() instanceof Player player)) {
            return SkillResult.INVALID_TARGET;
        }
        BossFight fight = Occultech.instance().bosses().fightFor(source);
        if (fight == null || !fight.players().contains(player)) {
            return SkillResult.INVALID_TARGET;
        }
        for (Mechanic mechanic : Mechanic.all()) {
            if (mechanic.bossId().equals(fight.spec().id()) && mechanic.name().equalsIgnoreCase(mechanicName)) {
                fight.hit(player, mechanic, living);
                return SkillResult.SUCCESS;
            }
        }
        return SkillResult.ERROR;
    }
}
