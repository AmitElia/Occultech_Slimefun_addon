package io.github.amitelia.occultech.integration.mythic;

import java.io.File;
import java.util.Locale;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.entity.Entity;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.FloorDecals;
import io.lumine.mythic.api.adapters.AbstractEntity;
import io.lumine.mythic.api.adapters.AbstractLocation;
import io.lumine.mythic.api.config.MythicLineConfig;
import io.lumine.mythic.api.skills.ITargetedEntitySkill;
import io.lumine.mythic.api.skills.ITargetedLocationSkill;
import io.lumine.mythic.api.skills.SkillMetadata;
import io.lumine.mythic.api.skills.SkillResult;
import io.lumine.mythic.bukkit.BukkitAdapter;
import io.lumine.mythic.bukkit.MythicBukkit;
import io.lumine.mythic.bukkit.events.MythicMechanicLoadEvent;
import io.lumine.mythic.core.skills.SkillExecutor;
import io.lumine.mythic.core.skills.SkillMechanic;
import io.lumine.mythic.core.utils.annotations.MythicMechanic;

/**
 * A floor warning from a Mythic skill, drawn by the fight's own telegraphs (FloorDecals). It is only a warning: any
 * damage still comes from the boss's behavior through BossFight.hit, so the two must share their geometry.
 * {@code occultechTelegraph{shape=circle|wedge|lane;r=2;length=6;width=2;t=20;color=#c08cff;mark=target}}. The wedge
 * and lane run from the caster towards the target.
 */
@MythicMechanic(author = "Occultech", name = "occultechTelegraph", description = "A fight floor warning")
public final class OccultechTelegraph extends SkillMechanic implements ITargetedLocationSkill, ITargetedEntitySkill {
    private static final java.util.concurrent.atomic.AtomicInteger CASTS = new java.util.concurrent.atomic.AtomicInteger();

    /** How many warnings this mechanic has drawn since the server started (self-test). */
    public static int casts() {
        return CASTS.get();
    }
    private final String shape;
    private final double radius;
    private final double length;
    private final double width;
    private final int ticks;
    private final Color color;
    private final FloorDecals.Mark mark;

    public OccultechTelegraph(MythicMechanicLoadEvent event) {
        this(MythicBukkit.inst().getSkillManager(), null, event.getMechanicName(), event.getConfig());
    }

    public OccultechTelegraph(SkillExecutor manager, File file, String line, MythicLineConfig config) {
        super(manager, file, line, config);
        shape = config.getString(new String[] {"shape", "s"}, "circle").toLowerCase(Locale.ROOT);
        radius = config.getDouble(new String[] {"radius", "r"}, 2);
        length = config.getDouble(new String[] {"length", "l"}, 6);
        width = config.getDouble(new String[] {"width", "w"}, 2);
        ticks = config.getInteger(new String[] {"ticks", "t"}, 20);
        color = parse(config.getString(new String[] {"color", "c"}, "#c08cff"));
        FloorDecals.Mark parsed;
        try {
            parsed = FloorDecals.Mark.valueOf(config.getString(new String[] {"mark", "m"}, "danger").toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            parsed = FloorDecals.Mark.DANGER;
        }
        mark = parsed;
    }

    private static Color parse(String hex) {
        try {
            return Color.fromRGB(Integer.parseInt(hex.replace("#", ""), 16));
        } catch (IllegalArgumentException e) {
            return Color.fromRGB(0xc08cff);
        }
    }

    @Override
    public SkillResult castAtEntity(SkillMetadata data, AbstractEntity target) {
        return castAtLocation(data, target.getLocation());
    }

    @Override
    public SkillResult castAtLocation(SkillMetadata data, AbstractLocation target) {
        Entity caster = data.getCaster().getEntity().getBukkitEntity();
        BossFight fight = Occultech.instance().bosses().fightFor(caster);
        if (fight == null) {
            return SkillResult.INVALID_TARGET;
        }
        Location at = BukkitAdapter.adapt(target);
        switch (shape) {
            case "wedge", "lane" -> {
                Location from = caster.getLocation();
                Vector direction = at.toVector().subtract(from.toVector()).setY(0);
                if (direction.lengthSquared() < 1e-6) {
                    direction = from.getDirection().setY(0);
                }
                direction.normalize();
                if (shape.equals("wedge")) {
                    FloorDecals.wedge(fight, from, direction, length, ticks, color);
                } else {
                    FloorDecals.lane(fight, from, direction, length, width, ticks, color);
                }
            }
            default -> fight.telegraph(at, radius, ticks, color, mark);
        }
        CASTS.incrementAndGet();
        return SkillResult.SUCCESS;
    }
}
