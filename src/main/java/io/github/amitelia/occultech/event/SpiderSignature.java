package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.CaveSpider;
import org.bukkit.entity.Player;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Raven's signature, <b>spiders</b> (Session E5): the Brood Mother's three abilities, tuned for netherite, taken in
 * turn.
 * <ul>
 * <li>Egg sacs: two sacs that hatch two cave spiders each after 6 s unless smashed (3 hits).</li>
 * <li>Web zone: a player's spot warns for 1.5 s, then slows anyone inside for 8 s.</li>
 * <li>Pounce: a ring warns under a distant player while he hisses, then he leaps onto it.</li>
 * </ul>
 */
final class SpiderSignature extends Signature {

    static final String ID = "RAID_RAVEN";
    private static final Mechanic SPIDERLING = Mechanic.of(ID, "Spiderling bite", 10, Mechanic.Kind.ADD, false);
    private static final Mechanic POUNCE = Mechanic.of(ID, "Pounce", 26, Mechanic.Kind.AREA, true);
    private static final int HATCH = 120;
    private static final int WEB_WARNING = 30;
    private static final int POUNCE_WARNING = 30;
    private static final double POUNCE_RADIUS = 2.5;
    private static final Color WEB = Color.fromRGB(235, 235, 235);
    private static final Color DIVE = Color.fromRGB(150, 30, 30);

    private record Sac(BossFight.FightObject object, int hatchAt) {}

    private final List<Sac> sacs = new ArrayList<>();
    private int turn;
    private int age;

    SpiderSignature(StaffKit kit) {
        super(kit, 60);
    }

    @Override
    boolean cast(int now) {
        if (kit.target == null) {
            next = now + 20;
            return false;
        }
        next = now + 120;
        switch (turn++ % 3) {
            case 0 -> layEggs();
            case 1 -> web(kit.target.getLocation());
            default -> {
                Player far = null;
                for (Player player : kit.fight.players()) {
                    if (!kit.within(player, 5) && (far == null || kit.body.getLocation().distanceSquared(player.getLocation())
                        < kit.body.getLocation().distanceSquared(far.getLocation()))) {
                        far = player;
                    }
                }
                if (far == null) {
                    web(kit.target.getLocation());
                } else {
                    pounce(far);
                }
            }
        }
        return true;
    }

    private void layEggs() {
        kit.claim(10);
        for (int i = 0; i < 2; i++) {
            Location at = safeSpot(kit.body.getLocation(), 2, 6);
            if (at != null) {
                sacs.add(new Sac(kit.fight.spawnObject(at, Material.SNIFFER_EGG, 1.3F, 3, () -> {}), age + HATCH));
            }
        }
        kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_SPIDER_AMBIENT, 1.5F, 0.6F);
        kit.fight.broadcast("&7" + kit.member.display() + " lays egg sacs. &fSmash them before they hatch!");
    }

    private void web(Location at) {
        kit.claim(WEB_WARNING);
        kit.fight.telegraph(at, 3, WEB_WARNING, WEB, FloorDecals.Mark.WEB);
        kit.later(WEB_WARNING, () -> {
            if (kit.alive()) {
                kit.fight.addHazard(at, 3, 160, WEB, FloorDecals.Zone.WEB,
                    player -> player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 1, false, true)));
                at.getWorld().spawnParticle(Particle.BLOCK, at, 30, 1.5, 0.1, 1.5, Material.COBWEB.createBlockData());
            }
        });
    }

    private void pounce(Player target) {
        Location spot = target.getLocation();
        kit.claim(POUNCE_WARNING + 20);
        kit.fight.telegraph(spot, POUNCE_RADIUS, POUNCE_WARNING + 15, DIVE, FloorDecals.Mark.DIVE);
        kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_SPIDER_AMBIENT, 2F, 0.5F);
        kit.body.getWorld().spawnParticle(Particle.CRIT, kit.body.getLocation().add(0, 1, 0), 25, 0.6, 0.4, 0.6, 0.1);
        kit.later(POUNCE_WARNING, () -> {
            if (!kit.alive()) {
                return;
            }
            Vector jump = spot.toVector().subtract(kit.body.getLocation().toVector());
            kit.body.setVelocity(jump.setY(0).multiply(0.14).setY(0.75));
            kit.later(15, () -> {
                if (!kit.alive()) {
                    return;
                }
                Location landed = kit.body.getLocation();
                landed.getWorld().spawnParticle(Particle.BLOCK, landed, 20, 1, 0.1, 1, Material.COBWEB.createBlockData());
                for (Player player : kit.playersNear(spot, POUNCE_RADIUS)) {
                    kit.fight.hit(player, POUNCE, kit.body);
                }
            });
        });
    }

    @Override
    void move() {
        age++;
        sacs.removeIf(sac -> {
            if (!sac.object().isAlive()) {
                return true;
            }
            if (age >= sac.hatchAt()) {
                hatch(sac.object().location());
                sac.object().remove();
                return true;
            }
            if (age % 10 == 0) {
                sac.object().location().getWorld().spawnParticle(Particle.ITEM_SLIME, sac.object().location(), 1, 0.2, 0.2, 0.2, 0);
            }
            return false;
        });
    }

    private void hatch(Location at) {
        at.getWorld().playSound(at, Sound.ENTITY_TURTLE_EGG_HATCH, 1F, 0.8F);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 20, 0.3, 0.3, 0.3, Material.COBWEB.createBlockData());
        for (int i = 0; i < 2; i++) {
            CaveSpider spider = kit.fight.spawnAdd(CaveSpider.class, at, s -> {
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 12);
                s.setHealth(12);
            });
            if (spider != null) {
                kit.fight.label(spider, SPIDERLING);
            }
        }
    }
}
