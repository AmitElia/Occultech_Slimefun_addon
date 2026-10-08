package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.Mechanic;

/**
 * Jolly's signatures: a very fast archer who's mostly here to annoy (Session E5).
 * <ul>
 * <li><b>trick_arrows</b>: he keeps his distance and shoots; every arrow carries a random short annoying effect (nausea,
 * wither, slowness, blindness, hunger, a little levitation hop, glowing).</li>
 * <li><b>fart_jump</b>: a loud fart and a brown-green cloud launch him into a long jump away from whoever is closest;
 * where he lands, a small stink cloud gives nausea for a moment.</li>
 * <li><b>whoopee_cushions</b>: he drops pink whoopee cushions near players; stepping on one sets off a fart, pops you up
 * a couple of blocks and makes you queasy.</li>
 * </ul>
 * The fart is a vanilla stand-in sound until the art pass gives the pack a real one. Nothing here hurts besides the arrows.
 */
final class JollySignatures {

    static final String ID = "RAID_JOLLY";
    private static final Mechanic TRICK_ARROW = Mechanic.of(ID, "Trick arrow", 18, Mechanic.Kind.PROJECTILE, false);
    /** Entity data on a trick arrow: which effect it carries. */
    private static final NamespacedKey TRICK = new NamespacedKey("occultech", "trick_effect");
    private static final Color FART = Color.fromRGB(120, 140, 50);
    private static final Color STINK = Color.fromRGB(110, 150, 40);

    /** What a trick arrow can do, and for how long (ticks, amplifier). */
    private record Trick(PotionEffectType type, int ticks, int amplifier, String line) {}

    private static final List<Trick> TRICKS = List.of(
        new Trick(PotionEffectType.NAUSEA, 120, 0, "Woozy!"),
        new Trick(PotionEffectType.WITHER, 60, 0, "Withered!"),
        new Trick(PotionEffectType.SLOWNESS, 60, 1, "Sluggish!"),
        new Trick(PotionEffectType.BLINDNESS, 40, 0, "Lights out!"),
        new Trick(PotionEffectType.HUNGER, 120, 1, "Suddenly starving!"),
        new Trick(PotionEffectType.LEVITATION, 12, 1, "Wheee!"),
        new Trick(PotionEffectType.GLOWING, 100, 0, "Spotted!"));

    private JollySignatures() {}

    /** If {@code damager} is a trick arrow, its effect lands on {@code player}. */
    static void applyTrick(Player player, Entity damager) {
        Integer index = damager.getPersistentDataContainer().get(TRICK, PersistentDataType.INTEGER);
        if (index == null || index < 0 || index >= TRICKS.size()) {
            return;
        }
        Trick trick = TRICKS.get(index);
        player.addPotionEffect(new PotionEffect(trick.type(), trick.ticks(), trick.amplifier()));
        player.sendActionBar(Component.text(trick.line(), NamedTextColor.GOLD));
    }

    /** The fart: two vanilla sounds layered until the pack has a real one. */
    private static void fart(Location at, float volume) {
        at.getWorld().playSound(at, Sound.BLOCK_NOTE_BLOCK_DIDGERIDOO, volume, 0.5F);
        at.getWorld().playSound(at, Sound.ENTITY_SLIME_SQUISH, volume, 0.5F);
    }

    /** A puff of brown-green cloud. */
    private static void cloud(Location at, int count, double spread) {
        at.getWorld().spawnParticle(Particle.DUST, at, count, spread, spread / 2, spread, 0, new Particle.DustOptions(FART, 2F));
        at.getWorld().spawnParticle(Particle.SNEEZE, at, count / 3, spread, spread / 2, spread, 0.02);
    }

    /** Keeps his distance and shoots arrows that each do something annoying. */
    static final class TrickArrows extends Signature {

        private static final double RANGE = 9;
        private static final int EVERY = 30;
        private int nextShot;

        TrickArrows(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // shoots on its own clock, see move()
            kit.body.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        @Override
        double range() {
            return RANGE;
        }

        @Override
        double pace() {
            return 0.7;   // very fast on his feet
        }

        @Override
        void move() {
            int now = kit.fight.elapsed();
            Player target = kit.target;
            if (now < nextShot || target == null || !kit.alive() || !kit.fighting(target) || !kit.within(target, 22)
                || kit.steered() || !kit.body.hasLineOfSight(target)) {
                return;
            }
            nextShot = now + EVERY;
            Vector aim = target.getEyeLocation().toVector().subtract(kit.body.getEyeLocation().toVector());
            double distance = aim.length();
            aim.normalize().multiply(2.2).add(new Vector(0, distance * 0.006, 0));
            int index = ThreadLocalRandom.current().nextInt(TRICKS.size());
            Arrow arrow = kit.body.launchProjectile(Arrow.class, aim);
            kit.fight.label(arrow, TRICK_ARROW);
            arrow.getPersistentDataContainer().set(TRICK, PersistentDataType.INTEGER, index);
            arrow.setColor(Color.fromRGB(TRICKS.get(index).type().getColor().asRGB()));
            kit.body.swingMainHand();
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_ARROW_SHOOT, 1F, 1.3F);
        }
    }

    /** A fart-powered long jump away from the closest player. */
    static final class FartJump extends Signature {

        private static final double STINK_RADIUS = 2.5;
        private int airborne = -1;

        FartJump(StaffKit kit) {
            super(kit, 60);
        }

        @Override
        boolean cast(int now) {
            Player close = kit.target;
            boolean pressed = close != null && kit.within(close, 4);
            if (close == null || airborne >= 0 || !kit.body.isOnGround() || (!pressed && ThreadLocalRandom.current().nextInt(3) > 0)) {
                next = now + 20;   // mostly when someone gets close; now and then just for fun
                return false;
            }
            Location landing = farthestSpot();
            if (landing == null) {
                next = now + 20;
                return false;
            }
            next = now + 120;
            kit.claim(10);
            Location from = kit.body.getLocation();
            Vector flat = landing.toVector().subtract(from.toVector()).setY(0);
            kit.body.setVelocity(flat.multiply(1 / 17.0).setY(0.85));
            fart(from, 2F);
            cloud(from.clone().add(0, 0.4, 0), 30, 0.6);
            airborne = 0;
            return true;
        }

        /** A safe spot 9-13 blocks off, as far from every player as can be found. */
        @Nullable
        private Location farthestSpot() {
            Location best = null;
            double bestGap = -1;
            for (int i = 0; i < 6; i++) {
                Location spot = safeSpot(kit.body.getLocation(), 9, 13);
                if (spot == null) {
                    continue;
                }
                double gap = Double.MAX_VALUE;
                for (Player player : kit.fight.players()) {
                    gap = Math.min(gap, player.getLocation().distanceSquared(spot));
                }
                if (gap > bestGap) {
                    best = spot;
                    bestGap = gap;
                }
            }
            return best;
        }

        @Override
        boolean steering() {
            return airborne >= 0;
        }

        @Override
        void move() {
            if (airborne < 0) {
                return;
            }
            airborne++;
            if (!kit.alive()) {
                airborne = -1;
                return;
            }
            if (airborne % 2 == 0) {
                cloud(kit.body.getLocation(), 3, 0.15);
            }
            if (airborne > 5 && kit.body.isOnGround() || airborne > 60) {
                airborne = -1;
                Location at = kit.body.getLocation();
                fart(at, 1.2F);
                cloud(at.clone().add(0, 0.4, 0), 40, STINK_RADIUS / 2);
                kit.fight.addHazard(at, STINK_RADIUS, 60, STINK,
                    player -> player.addPotionEffect(new PotionEffect(PotionEffectType.NAUSEA, 80, 0, false, true)));
            }
        }
    }

    /** Pink whoopee cushions on the floor. */
    static final class WhoopeeCushions extends Signature {

        private static final int LIFE = 300;
        private static final int MAX = 6;
        private static final double TRIGGER = 0.8;

        private record Cushion(BlockDisplay display, Location at, int until) {}

        private final List<Cushion> cushions = new ArrayList<>();
        private int age;

        WhoopeeCushions(StaffKit kit) {
            super(kit, 120);
        }

        @Override
        boolean cast(int now) {
            List<Player> players = new ArrayList<>(kit.fight.players());
            if (players.isEmpty() || cushions.size() >= MAX) {
                next = now + 40;
                return false;
            }
            next = now + 240;
            kit.claim(10);
            kit.body.swingMainHand();
            java.util.Collections.shuffle(players);
            ThreadLocalRandom random = ThreadLocalRandom.current();
            for (int i = 0; i < 3 && cushions.size() < MAX; i++) {
                // near a player, never right under them: it's a trap to walk into, not a hit
                Location around = players.get(i % players.size()).getLocation();
                Location spot = safeSpot(around, 2, 4);
                if (spot == null) {
                    continue;
                }
                BlockDisplay display = kit.fight.spawnExtra(BlockDisplay.class, spot, d -> {
                    d.setBlock(Material.PINK_WOOL.createBlockData());
                    d.setTransformation(new Transformation(new Vector3f(-0.45F, 0, -0.45F),
                        new AxisAngle4f((float) random.nextDouble(Math.PI), 0, 1, 0), new Vector3f(0.9F, 0.22F, 0.9F), new AxisAngle4f()));
                });
                cushions.add(new Cushion(display, spot, age + LIFE));
            }
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_ITEM_PICKUP, 1.5F, 0.6F);
            return true;
        }

        @Override
        void move() {
            age++;
            for (Iterator<Cushion> it = cushions.iterator(); it.hasNext();) {
                Cushion cushion = it.next();
                if (age >= cushion.until() || !cushion.display().isValid()) {
                    cushion.display().remove();
                    it.remove();
                    continue;
                }
                for (Player player : kit.fight.players()) {
                    Location p = player.getLocation();
                    double dx = p.getX() - cushion.at().getX();
                    double dz = p.getZ() - cushion.at().getZ();
                    if (dx * dx + dz * dz <= TRIGGER * TRIGGER && Math.abs(p.getY() - cushion.at().getY()) < 0.6) {
                        fart(cushion.at(), 2F);
                        cloud(cushion.at().clone().add(0, 0.3, 0), 30, 0.6);
                        player.setVelocity(player.getVelocity().setY(0.7));
                        player.addPotionEffect(new PotionEffect(PotionEffectType.NAUSEA, 60, 0, false, true));
                        player.sendActionBar(Component.text("*pfffrrt*", NamedTextColor.LIGHT_PURPLE));
                        cushion.display().remove();
                        it.remove();
                        break;
                    }
                }
            }
        }
    }
}
