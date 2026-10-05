package io.github.amitelia.occultech.boss.tier1;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Evoker;
import org.bukkit.entity.EvokerFangs;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 gate boss (diamond gear, 4-6 min). A scaled-up evoker.
 * <ul>
 * <li>Fangs erupt in circle-shaped patterns - a ring around you, a line towards you, a spiral from the Archevoker -
 * each drawn in purple on the ground 1s before it strikes. Faster below half health.</li>
 * <li>Its vexes (vanilla summons) belong to the fight: capped and kept inside the arena.</li>
 * <li>Three phylacteries (5 hits each) stand around the circle. While any stands, the Archevoker cheats death once
 * and returns at 40% health. Break them first.</li>
 * </ul>
 */
public final class Archevoker extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic FANGS = io.github.amitelia.occultech.boss.Mechanic.of("ARCHEVOKER", "Fangs", 12, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic VEX = io.github.amitelia.occultech.boss.Mechanic.of("ARCHEVOKER", "Vex", 9, io.github.amitelia.occultech.boss.Mechanic.Kind.ADD, false);

    private static final Particle.DustOptions RUNE = new Particle.DustOptions(Color.fromRGB(160, 60, 220), 1.4F);
    private static final int PATTERN_INTERVAL = 160;
    private static final int PATTERN_INTERVAL_ENRAGED = 110;
    private static final int PATTERN_WARNING = 20;

    private enum Pattern { RING, LINE, SPIRAL }

    private final List<BossFight.FightObject> phylacteries = new ArrayList<>();
    private Evoker archevoker;
    private List<Location> pending = List.of();
    private int strikeAt = -1;
    private int nextPattern = 80;
    private int patternIndex;
    private boolean revived;

    public Archevoker(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        archevoker = fight.spawnBoss(Evoker.class, at, e -> {
            e.setCustomName(ChatColor.DARK_PURPLE + "Archevoker");
            e.setCustomNameVisible(true);
            BossFight.setAttribute(e, Attribute.MAX_HEALTH, 700);
            fight.labelSpawns(e, org.bukkit.entity.EntityType.VEX, VEX);
            fight.labelSpawns(e, org.bukkit.entity.EntityType.EVOKER_FANGS, FANGS);
            BossFight.setAttribute(e, Attribute.SCALE, 1.6);
            BossFight.setAttribute(e, Attribute.KNOCKBACK_RESISTANCE, 0.6);
            BossFight.setAttribute(e, Attribute.FOLLOW_RANGE, 32);
        });
        for (int i = 0; i < 3; i++) {
            double angle = Math.PI * 2 * i / 3;
            Location spot = fight.center().add(Math.cos(angle) * 7, 0, Math.sin(angle) * 7);
            phylacteries.add(fight.spawnObject(spot, Material.TOTEM_OF_UNDYING, 1.3F, 5, () -> {
                if (phylacteries.stream().noneMatch(BossFight.FightObject::isAlive)) {
                    fight.broadcast("&dThe last phylactery shatters - the Archevoker is mortal!");
                }
            }));
        }
        fight.broadcast("&5Phylacteries bind the Archevoker's life. &fBreak them first!");
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        boolean anchored = phylacteries.stream().anyMatch(BossFight.FightObject::isAlive);
        if (!revived && anchored && damage >= boss.getHealth()) {
            revived = true;
            double max = boss.getAttribute(Attribute.MAX_HEALTH).getValue();
            boss.setHealth(max * 0.4);
            boss.getWorld().spawnParticle(Particle.TOTEM_OF_UNDYING, boss.getLocation().add(0, 1.5, 0), 80, 0.6, 1, 0.6, 0.4);
            boss.getWorld().playSound(boss.getLocation(), Sound.ITEM_TOTEM_USE, 1.5F, 0.8F);
            fight.broadcast("&5The Archevoker cheats death through its phylacteries!");
            return 0;
        }
        return damage;
    }

    @Override
    public void tick() {
        if (!archevoker.isValid()) {
            return;
        }
        int now = fight.elapsed();

        if (now >= nextPattern && strikeAt < 0) {
            Player target = fight.randomPlayer();
            nextPattern = now + (fight.healthFraction() < 0.5 ? PATTERN_INTERVAL_ENRAGED : PATTERN_INTERVAL);
            if (target != null) {
                pending = pattern(Pattern.values()[patternIndex++ % Pattern.values().length], target.getLocation());
                strikeAt = now + PATTERN_WARNING;
                for (Location point : pending) {
                    fight.telegraph(point, 0.6, PATTERN_WARNING, RUNE.getColor(), null);
                }
                archevoker.getWorld().playSound(archevoker.getLocation(), Sound.ENTITY_EVOKER_PREPARE_ATTACK, 2F, 0.8F);
            }
        }
        if (strikeAt > now && !FloorDecals.enabled()) {
            for (Location point : pending) {
                point.getWorld().spawnParticle(Particle.DUST, point.clone().add(0, 0.15, 0), 2, 0.15, 0, 0.15, 0, RUNE);
            }
        }
        if (now == strikeAt) {
            strikeAt = -1;
            for (Location point : pending) {
                point.getWorld().spawn(point, EvokerFangs.class, fangs -> {
                    fangs.setOwner(archevoker);
                    fight.label(fangs, FANGS);
                });
            }
            archevoker.getWorld().playSound(archevoker.getLocation(), Sound.ENTITY_EVOKER_CAST_SPELL, 2F, 1F);
        }
    }

    private List<Location> pattern(Pattern pattern, Location target) {
        List<Location> points = new ArrayList<>();
        Location origin = archevoker.getLocation();
        double y = fight.center().getY();
        switch (pattern) {
            case RING -> {
                for (int i = 0; i < 14; i++) {
                    double angle = Math.PI * 2 * i / 14;
                    points.add(floor(target.clone().add(Math.cos(angle) * 3, 0, Math.sin(angle) * 3), y));
                }
            }
            case LINE -> {
                Vector step = target.toVector().subtract(origin.toVector()).setY(0);
                if (step.lengthSquared() < 0.01) {
                    step = new Vector(1, 0, 0);
                }
                step.normalize();
                for (int i = 1; i <= 16; i++) {
                    points.add(floor(origin.clone().add(step.clone().multiply(i)), y));
                }
            }
            case SPIRAL -> {
                for (int i = 0; i < 24; i++) {
                    double angle = i * 0.55;
                    double radius = 1.5 + i * 0.45;
                    points.add(floor(origin.clone().add(Math.cos(angle) * radius, 0, Math.sin(angle) * radius), y));
                }
            }
        }
        points.removeIf(p -> p.distanceSquared(fight.center()) > fight.radius() * fight.radius());
        return points;
    }

    private static Location floor(Location at, double y) {
        Location out = at.clone();
        out.setY(y);
        return out;
    }
}
