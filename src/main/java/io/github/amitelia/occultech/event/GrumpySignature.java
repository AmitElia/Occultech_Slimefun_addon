package io.github.amitelia.occultech.event;

import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import net.kyori.adventure.title.Title;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.BlockDisplay;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.entity.Pose;
import org.bukkit.entity.TextDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * OldeGrumpy's signature, <b>lawn</b> (an old man monster - Session E10): hunched over a cane, OldeGrumpy plants a
 * lawn - mowed grass ringed by little fence posts, a "KEEP OFF THE GRASS!" sign - and guards it. Anyone who steps on it
 * gets <b>GET OFF MY LAWN!</b> across their screen, and OldeGrumpy hobbles over and whacks them off it with the cane (a
 * warned cone). And the more OldeGrumpy is hit, the grumpier - and faster - OldeGrumpy gets.
 */
final class GrumpySignature extends Signature {

    static final String ID = "RAID_GRUMPY";
    private static final Mechanic CANE = Mechanic.of(ID, "Cane whack", 26, Mechanic.Kind.AREA, true);
    private static final double LAWN = 5;
    private static final int LAWN_TICKS = 320;
    private static final int WHACK_WARNING = 15;
    private static final double WHACK_REACH = 3.5;
    private static final double MAX_GRUMP = 10;
    private static final Color CANE_COLOR = Color.fromRGB(200, 150, 80);

    @Nullable private Location lawn;
    private int lawnLeft;
    private final List<Entity> props = new ArrayList<>();
    private final Map<UUID, Integer> shouted = new HashMap<>();
    private double grump;
    private int nextWhack;
    private int age;

    GrumpySignature(StaffKit kit) {
        super(kit, 40);
        kit.body.setPose(Pose.SNEAKING, true);                              // hunched over the cane
        kit.body.getEquipment().setItemInMainHand(new ItemStack(Material.STICK));
    }

    @Override
    boolean cast(int now) {
        if (lawn != null || kit.target == null) {
            next = now + 20;
            return false;
        }
        next = now + LAWN_TICKS + 120;
        kit.claim(10);
        plant(kit.body.getLocation());
        return true;
    }

    private void plant(Location at) {
        lawn = at.clone();
        lawn.setY(at.getWorld().getHighestBlockYAt(at) + 1);
        lawnLeft = LAWN_TICKS;
        Location floor = lawn.clone();
        floor.setYaw(0F);
        floor.setPitch(0F);
        props.add(FloorDecals.flat(kit.fight, floor, "floor_lawn", Color.WHITE, LAWN * 2));
        // a ring of little fence posts (displays, not blocks) and the sign
        for (int i = 0; i < 20; i++) {
            double a = Math.PI * 2 * i / 20;
            Location post = lawn.clone().add(Math.cos(a) * (LAWN + 0.2), 0, Math.sin(a) * (LAWN + 0.2));
            props.add(kit.fight.spawnExtra(BlockDisplay.class, post, d -> {
                d.setBlock(Material.BIRCH_FENCE.createBlockData());
                d.setTransformation(new Transformation(new Vector3f(-0.5F, 0, -0.5F), new AxisAngle4f(), new Vector3f(1, 0.7F, 1),
                    new AxisAngle4f()));
            }));
        }
        Location sign = lawn.clone().add(LAWN + 0.6, 1.4, 0);
        props.add(kit.fight.spawnExtra(TextDisplay.class, sign, t -> {
            t.text(Component.text("KEEP OFF", NamedTextColor.DARK_RED).decorate(TextDecoration.BOLD).append(Component.newline())
                .append(Component.text("THE GRASS!", NamedTextColor.DARK_RED).decorate(TextDecoration.BOLD)));
            t.setBackgroundColor(Color.fromARGB(230, 214, 186, 140));
            t.setBillboard(org.bukkit.entity.Display.Billboard.CENTER);
        }));
        lawn.getWorld().playSound(lawn, Sound.BLOCK_GRASS_PLACE, 2F, 0.7F);
        kit.fight.broadcast("&2" + kit.member.display() + " &aplants a lawn. &7Stay off it.");
    }

    private void clearLawn() {
        props.forEach(Entity::remove);
        props.clear();
        lawn = null;
        shouted.clear();
    }

    @Override
    boolean steering() {
        return lawn != null;   // guarding the lawn: OldeGrumpy moves and whacks on their own
    }

    @Override
    double pace() {
        return 1 - 0.04 * grump;   // up to 40% faster when furious
    }

    @Override
    void onHitBy(Player player, double damage) {
        grump = Math.min(MAX_GRUMP, grump + 1);
    }

    private boolean onLawn(Player player) {
        Location at = player.getLocation();
        double dx = at.getX() - lawn.getX();
        double dz = at.getZ() - lawn.getZ();
        return dx * dx + dz * dz <= LAWN * LAWN && Math.abs(at.getY() - lawn.getY()) < 2.5;
    }

    @Override
    void move() {
        age++;
        if (age % 20 == 0) {
            grump = Math.max(0, grump - 1);                                 // calms down, slowly
            if (grump >= 5 && kit.alive()) {
                kit.body.getWorld().spawnParticle(Particle.ANGRY_VILLAGER, kit.body.getLocation().add(0, 2, 0), 2, 0.3, 0.2, 0.3, 0);
            }
        }
        if (lawn == null) {
            return;
        }
        if (--lawnLeft <= 0 || !kit.alive()) {
            clearLawn();
            return;
        }
        Player intruder = null;
        double best = Double.MAX_VALUE;
        for (Player player : kit.fight.players()) {
            if (!onLawn(player)) {
                continue;
            }
            Integer last = shouted.get(player.getUniqueId());
            if (last == null || age - last > 60) {
                shouted.put(player.getUniqueId(), age);
                player.showTitle(Title.title(Component.text("GET OFF MY LAWN!", NamedTextColor.RED).decorate(TextDecoration.BOLD),
                    Component.text("- " + kit.member.display(), NamedTextColor.GRAY),
                    Title.Times.times(Duration.ofMillis(100), Duration.ofMillis(1200), Duration.ofMillis(300))));
                player.playSound(kit.body.getLocation(), Sound.ENTITY_VILLAGER_NO, 2F, 0.6F);
            }
            double d = player.getLocation().distanceSquared(kit.body.getLocation());
            if (d < best) {
                best = d;
                intruder = player;
            }
        }
        if (kit.holding()) {
            kit.stayHeld();   // the whack winds up where it warned
            return;
        }
        // hobble to the nearest trespasser, or back to the middle of the lawn
        double speed = 0.2 / pace();
        Abyss.walk(kit.body, intruder != null ? intruder.getLocation() : lawn, speed, intruder != null ? 2 : 0.5);
        int now = kit.fight.elapsed();
        if (intruder != null && now >= nextWhack && kit.within(intruder, WHACK_REACH)) {
            nextWhack = now + (int) Math.round(30 * pace());
            whack(intruder);
        }
    }

    private void whack(Player toward) {
        Location at = kit.body.getLocation();
        Vector aimAt = toward.getLocation().toVector().subtract(at.toVector()).setY(0);
        double aim = Math.atan2(aimAt.getZ(), aimAt.getX());
        kit.warnFan(at, aim, Math.PI / 2, WHACK_REACH, WHACK_WARNING, CANE_COLOR);
        kit.body.getWorld().playSound(at, Sound.ENTITY_VILLAGER_HURT, 1.5F, 0.5F);
        Location from = lawn.clone();
        kit.later(WHACK_WARNING, () -> {
            if (!kit.alive()) {
                return;
            }
            kit.body.swingMainHand();
            at.getWorld().playSound(at, Sound.ENTITY_PLAYER_ATTACK_KNOCKBACK, 1.5F, 0.6F);
            for (Player player : kit.playersNear(at, WHACK_REACH)) {
                Vector to = player.getLocation().toVector().subtract(at.toVector());
                if (Math.abs(RaidGeometry.angleBetween(Math.atan2(to.getZ(), to.getX()), aim)) <= Math.PI / 4) {
                    kit.fight.hit(player, CANE, kit.body);
                    StaffKit.knock(player, from, 1.4, 0.5);                // right off the lawn
                }
            }
        });
    }
}
