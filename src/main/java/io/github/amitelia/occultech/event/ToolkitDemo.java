package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nonnull;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossBlueprint;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Act 2's raid toolkit on its own (Session E6), for trying the mechanics before the Council exists:
 * {@code /occultech event demo}. A dummy that can't be hurt stands in the middle and sets off soak circles, player
 * markers, sweeping barriers, spinning lasers and shockwave rings in turn, at the pace of a chosen band (1-3), as many
 * at once as that band allows. The Council (E7) uses the same pieces with its own attacks.
 */
public final class ToolkitDemo extends BossBehavior {

    public static final String ID = "RAID_TOOLKIT";
    private static final Mechanic SOAK = Mechanic.of(ID, "Soak share", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic UNSOAKED = Mechanic.of(ID, "Unsoaked circle", 30, Mechanic.Kind.AREA, true);
    private static final Mechanic MARKER = Mechanic.of(ID, "Marker burst", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic BARRIER = Mechanic.of(ID, "Sweeping barrier", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic LASER = Mechanic.of(ID, "Laser", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic RING = Mechanic.of(ID, "Shockwave", 22, Mechanic.Kind.AREA, true);

    /** The toolkit's pieces. */
    public enum Hazard { SOAK, MARKER, BARRIER, LASER, RING }

    private final List<Hazard> cycle;
    /** The Council's health a band stands for: band 1 = 90%, 2 = 50%, 3 = 20%. */
    private final double fraction;
    private final List<RaidHazard> live = new ArrayList<>();
    private Mannequin dummy;
    private int nextAt = 40;
    private int index;
    private int launched;
    private boolean fullBeam;

    ToolkitDemo(BossFight fight, List<Hazard> cycle, int band) {
        super(fight);
        this.cycle = List.copyOf(cycle);
        this.fraction = switch (Math.max(1, Math.min(3, band))) {
            case 1 -> 0.9;
            case 2 -> 0.5;
            default -> 0.2;
        };
    }

    /** The fight data for a demo spanning {@code radius}. */
    @Nonnull
    static BossSpec spec(double radius) {
        return new BossSpec(ID, "Raid toolkit", RaidService.BENCHMARK_TIER, false, "", 0, radius, 3600, Map.of(), Map.of(), 0);
    }

    @Nonnull
    static BossBlueprint blueprint(List<Hazard> cycle, int band) {
        return new BossBlueprint(ID, ToolkitDemo.class, fight -> new ToolkitDemo(fight, cycle, band));
    }

    /** How many hazards it has set off (self-test). */
    int launched() {
        return launched;
    }

    @Override
    public void spawn(Location at) {
        dummy = fight.spawnBoss(Mannequin.class, at.clone().add(0, 0.2, 0), m -> {
            m.setCustomName(ChatColor.YELLOW + "Toolkit dummy");
            m.setCustomNameVisible(true);
            m.setDescription(net.kyori.adventure.text.Component.text("/occultech event demo stop", net.kyori.adventure.text.format.NamedTextColor.GRAY));
            BossFight.setAttribute(m, Attribute.MAX_HEALTH, 1000);
        });
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return 0;
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public void tick() {
        int now = fight.elapsed();
        RaidPace pace = RaidPace.of(fraction, now);
        if (now < nextAt || live.size() >= pace.overlap()) {
            return;
        }
        Hazard next = cycle.get(index++ % cycle.size());
        if (launch(next, pace)) {
            launched++;
        }
        nextAt = now + pace.cooldown(140);
    }

    @Override
    public void move() {
        live.removeIf(hazard -> !hazard.step());
    }

    private boolean launch(Hazard hazard, RaidPace pace) {
        List<Player> players = new ArrayList<>(fight.players());
        Collections.shuffle(players);
        ThreadLocalRandom random = ThreadLocalRandom.current();
        double radius = fight.radius();
        switch (hazard) {
            case SOAK -> {
                // about one in five players to each circle: a crowd splits up into groups
                int circles = Math.max(1, Math.min(3, (players.size() + 7) / 8));
                int needed = Math.max(1, (int) Math.round(players.size() / 5.0));
                List<Location> spots = new ArrayList<>();
                for (int tries = 0; spots.size() < circles && tries < 30; tries++) {
                    Location spot = fight.randomPoint(4, radius * 0.6);
                    if (spots.stream().allMatch(s -> s.distanceSquared(spot) > 64)) {
                        spots.add(spot);
                    }
                }
                for (Location spot : spots) {
                    live.add(new SoakCircle(fight, spot, 2.5, 100, needed, SOAK, UNSOAKED, dummy));
                }
                return !spots.isEmpty();
            }
            case MARKER -> {
                if (players.isEmpty()) {
                    return false;
                }
                for (Player player : players.subList(0, Math.min(pace.overlap() + 1, players.size()))) {
                    live.add(new PlayerMarker(fight, player, 60, 12, 3, MARKER, dummy));
                }
                return true;
            }
            case BARRIER -> {
                live.add(new MovingBarrier(fight, fight.center(), random.nextDouble(Math.PI * 2), radius, 0.25, 1.8, 40,
                    Material.RED_STAINED_GLASS, BARRIER, dummy));
                return true;
            }
            case LASER -> {
                fullBeam = !fullBeam;
                double length = Math.min(14, radius - 1);
                double spin = (random.nextBoolean() ? 1 : -1) * 0.035;
                live.add(new SpinningLaser(fight, dummy, pace.beams(), length, spin, fullBeam ? SpinningLaser.FULL : SpinningLaser.LOW,
                    fullBeam ? length * 0.45 : Double.NaN, length * 0.45 + 2.5, 40, 200, pace.reverse(),
                    fullBeam ? Color.fromRGB(255, 60, 60) : Color.fromRGB(255, 200, 40), LASER));
                return true;
            }
            case RING -> {
                for (int i = 0; i < pace.ringWaves(); i++) {
                    int delay = i * 15;
                    live.add(new DelayedHazard(delay, new RaidRing(fight, dummy.getLocation(), 0.35, radius - 1, RaidRing.LOW, Double.NaN,
                        Color.fromRGB(230, 120, 40), RING, dummy)));
                }
                return true;
            }
            default -> {
                return false;
            }
        }
    }
}
