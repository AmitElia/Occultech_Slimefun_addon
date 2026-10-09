package io.github.amitelia.occultech.event;

import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.TextColor;
import net.kyori.adventure.text.format.TextDecoration;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.block.Block;
import org.bukkit.entity.Display;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.entity.TextDisplay;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

/**
 * A staff member's own ability (config {@code raid.roster[].signatures}), on top of their archetype's kit (Sessions
 * E3-E5). Each has its own cooldown; it only starts when the body isn't busy with another warned move, and it marks the
 * body busy while it warns ({@link StaffKit#claim}). Ids not built yet are skipped.
 */
abstract class Signature {

    protected final StaffKit kit;
    /** The fight tick this signature may next be cast. */
    int next;

    protected Signature(StaffKit kit, int firstDelay) {
        this.kit = kit;
        this.next = kit.fight.elapsed() + firstDelay;
    }

    /** The signature for {@code id}, or null if it isn't built yet. */
    @Nullable
    static Signature create(String id, StaffKit kit) {
        return switch (id) {
            case "hotfix" -> new DevSignatures.Hotfix(kit);
            case "system_bug" -> new DevSignatures.SystemBug(kit);
            case "rollback" -> new DevSignatures.Rollback(kit);
            case "replicas" -> new AbusingSignatures.Replicas(kit);
            case "big_fuse" -> new AbusingSignatures.BigFuse(kit);
            case "radio" -> new RadioSignature(kit);
            case "walls" -> new BuilderSignatures.Walls(kit);
            case "tnt" -> new BuilderSignatures.Tnt(kit);
            case "enderstep" -> new SamuraiSignatures.Enderstep(kit);
            case "swap" -> new SamuraiSignatures.Swap(kit);
            case "katana" -> new SamuraiSignatures.Katana(kit);
            case "meteors" -> new SpaceSignatures.Meteors(kit);
            case "moons" -> new SpaceSignatures.Moons(kit);
            case "black_hole" -> new SpaceSignatures.BlackHole(kit);
            case "low_gravity" -> new SpaceSignatures.LowGravity(kit);
            case "stampede" -> new CowSignatures.Stampede(kit);
            case "moo" -> new CowSignatures.Moo(kit);
            case "milk" -> new CowSignatures.Milk(kit);
            case "hay" -> new CowSignatures.Hay(kit);
            case "bond" -> new PairSignatures.Bond(kit);
            case "together" -> new PairSignatures.Together(kit);
            case "rescue" -> new PairSignatures.Rescue(kit);
            case "daggers" -> new PairSignatures.Daggers(kit);
            case "burrow" -> new BurrowSignature(kit);
            case "decoys" -> new TricksterSignatures.Decoys(kit);
            case "denied" -> new TricksterSignatures.Denied(kit);
            case "trick_arrows" -> new JollySignatures.TrickArrows(kit);
            case "fart_jump" -> new JollySignatures.FartJump(kit);
            case "whoopee_cushions" -> new JollySignatures.WhoopeeCushions(kit);
            case "bees" -> new CreatureSignatures.Bees(kit);
            case "bats" -> new CreatureSignatures.Bats(kit);
            case "foxes" -> new CreatureSignatures.Foxes(kit);
            case "mount" -> new CreatureSignatures.Mount(kit);
            case "spiders" -> new SpiderSignature(kit);
            case "flight" -> new OwlSignature(kit);
            case "lawn" -> new GrumpySignature(kit);
            case "hammer" -> new LeapSignatures.Hammer(kit);
            case "flop" -> new LeapSignatures.Flop(kit);
            default -> null;
        };
    }

    /**
     * Tries to cast now: true if it did (and then it set {@link #next} and claimed the body), false if there was nothing
     * to do (no target in reach...), in which case it should push {@link #next} back a little.
     */
    abstract boolean cast(int now);

    /** Every tick: moving parts. Runs even after the body fell, until the fight ends. */
    void move() {}

    /** True while this signature moves the body itself (the kit then neither walks nor swings). */
    boolean steering() {
        return false;
    }

    /** The share of a hit the body takes (2 = double damage, 0.5 = half). */
    double incoming() {
        return 1;
    }

    /**
     * Above 0: this signature makes the staff member a ranged fighter who keeps this far from their target; the kit's
     * melee and archetype move are off (Jolly's bow).
     */
    double range() {
        return 0;
    }

    /** True if this signature brings its own creatures, so a Summoner calls no zombie helpers. */
    boolean replacesHelpers() {
        return false;
    }

    /** Below 1: the body moves and swings faster. */
    double pace() {
        return 1;
    }

    /** A player's hit landed on the body. */
    void onHitBy(Player player, double damage) {}

    /** The body's melee hit {@code player}. */
    void onMelee(Player player) {}

    /** One of the fight's extra creatures died ({@code killer}: the player responsible, if any). */
    void onAddDeath(org.bukkit.entity.Entity entity, @Nullable Player killer) {}

    /** True to sidestep a player's projectile (it passes harmlessly). */
    boolean deflect(Projectile projectile) {
        return false;
    }

    /**
     * A safe spot on the arena floor {@code min}-{@code max} blocks from {@code around}, inside this fight's reach, or null:
     * two free blocks to stand in over a solid one, at about the same height.
     */
    @Nullable
    protected Location safeSpot(Location around, double min, double max) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        Location center = kit.fight.center();
        double reach = kit.fight.radius() - 1.5;
        for (int i = 0; i < 16; i++) {
            double angle = random.nextDouble(Math.PI * 2);
            double distance = min + random.nextDouble(Math.max(0.01, max - min));
            Location spot = around.clone().add(Math.cos(angle) * distance, 0, Math.sin(angle) * distance);
            double dx = spot.getX() - center.getX();
            double dz = spot.getZ() - center.getZ();
            if (dx * dx + dz * dz > reach * reach) {
                continue;
            }
            Block floor = spot.getWorld().getHighestBlockAt(spot.getBlockX(), spot.getBlockZ());
            Block feet = floor.getRelative(0, 1, 0);
            if (floor.isPassable() || !feet.isPassable() || !feet.getRelative(0, 1, 0).isPassable() || Math.abs(feet.getY() - around.getY()) > 3) {
                continue;
            }
            Location found = feet.getLocation().add(0.5, 0, 0.5);
            found.setDirection(around.toVector().subtract(found.toVector()));
            return found;
        }
        return null;
    }

    // ------------------------------------------------------------------ helpers

    /**
     * Floating text for this fight (removed with it): {@code flat} lies on the floor facing up, otherwise it always
     * faces the viewer.
     */
    @Nonnull
    protected TextDisplay text(Location at, String text, Color color, float scale, boolean flat) {
        return kit.fight.spawnExtra(TextDisplay.class, at, t -> {
            t.text(Component.text(text, TextColor.color(color.asRGB())).decorate(TextDecoration.BOLD));
            t.setBackgroundColor(Color.fromARGB(0, 0, 0, 0));
            t.setShadowed(true);
            t.setBillboard(flat ? Display.Billboard.FIXED : Display.Billboard.CENTER);
            AxisAngle4f turn = flat ? new AxisAngle4f((float) (-Math.PI / 2), 1, 0, 0) : new AxisAngle4f();
            t.setTransformation(new Transformation(new Vector3f(), turn, new Vector3f(scale, scale, scale), new AxisAngle4f()));
            t.setBrightness(new Display.Brightness(15, 15));
        });
    }
}
