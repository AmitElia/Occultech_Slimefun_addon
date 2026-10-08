package io.github.amitelia.occultech.event;

import java.util.List;
import java.util.function.BooleanSupplier;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.github.amitelia.occultech.core.Keys;
import io.papermc.paper.entity.TeleportFlag;

/**
 * Chlo, the archer (Council seat, Session E7): circles the arena in the air with a bow, out of melee reach.
 * <ul>
 * <li>Arrows at a random player now and then.</li>
 * <li><b>Arrow rain</b> (raid mechanic): markers on players - spread out.</li>
 * <li><b>Arrow wall</b> (raid mechanic): a barrier sweeps the floor - find its gap.</li>
 * <li><b>Kidnap</b>: a player is marked for 2 s, Chlo swoops in, carries them about 13 blocks up, strikes them three times
 * and drops them (ordinary fall damage). Enough damage on Chlo during the carry makes the drop come early, from lower.
 * Then Chlo is grounded for 4 s and takes half again as much: the melee players' window.</li>
 * </ul>
 * Rules for the carried player: no dismounting, no pearls or chorus out (RaidService), the same player is never taken
 * twice in a row, and quitting mid-carry puts them back on the ground.
 */
final class Archer extends CouncilMember {

    /** Entity data on the seat a kidnapped player rides. */
    static final NamespacedKey SEAT = new NamespacedKey("occultech", "kidnap_seat");
    private static final Mechanic ARROW = Mechanic.of(CouncilBehavior.ID, "Arrow (Archer)", 18, Mechanic.Kind.PROJECTILE, false);
    private static final Mechanic RAIN = Mechanic.of(CouncilBehavior.ID, "Arrow rain (Archer)", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic WALL = Mechanic.of(CouncilBehavior.ID, "Arrow wall (Archer)", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic TALON = Mechanic.of(CouncilBehavior.ID, "Talon strike (Archer)", 15, Mechanic.Kind.MELEE, false);
    private static final double HOVER = 8;
    private static final double CARRY_HEIGHT = 13;
    private static final int MARK = 40;
    private static final int SWOOP = 40;
    private static final int CARRY = 45;
    private static final int GROUNDED = 80;
    /** Damage on Chlo during a carry, as a share of the pool, that makes the drop come early. */
    private static final double DROP_SHARE = 0.01;

    private enum Kidnap { NONE, MARKING, SWOOPING, CARRYING }

    private double orbit = Math.random() * Math.PI * 2;
    private int nextArrow = 40;
    private int nextKidnap = 300;
    private int groundedUntil = -1;
    // the kidnap under way
    private Kidnap kidnap = Kidnap.NONE;
    private int kidnapTicks;
    @Nullable private Player prey;
    @Nullable private Player lastPrey;
    @Nullable private ArmorStand seatEntity;
    private double carriedFrom;
    private double takenDuringCarry;

    Archer(CouncilBehavior council, Location at, CouncilBehavior.Seat seat) {
        super(council, at.clone().add(0, HOVER, 0), seat);
        body.setGravity(false);
        body.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
    }

    @Override
    List<BooleanSupplier> majors() {
        return List.of(this::arrowRain, this::arrowWall);
    }

    private boolean grounded() {
        return fight.elapsed() < groundedUntil;
    }

    @Override
    double incoming() {
        return grounded() ? 1.5 : 1;
    }

    @Override
    void onHitBy(Player player, double damage) {
        if (kidnap == Kidnap.CARRYING) {
            takenDuringCarry += damage;
        }
    }

    @Override
    void tick(int now) {
        if (kidnap != Kidnap.NONE || grounded()) {
            return;
        }
        if (now >= nextArrow) {
            nextArrow = now + council.pace().cooldown(40);
            shoot();
        }
        if (now >= nextKidnap) {
            nextKidnap = now + 20;
            if (startKidnap()) {
                nextKidnap = now + council.pace().cooldown(400);
            }
        }
    }

    private void shoot() {
        for (Player player : shuffledPlayers()) {
            if (body.hasLineOfSight(player)) {
                Vector aim = player.getEyeLocation().toVector().subtract(body.getEyeLocation().toVector()).normalize().multiply(2.4);
                Arrow arrow = body.launchProjectile(Arrow.class, aim);
                fight.label(arrow, council.scaled(ARROW));
                body.swingMainHand();
                body.getWorld().playSound(body.getLocation(), Sound.ENTITY_SKELETON_SHOOT, 1.5F, 1.2F);
                return;
            }
        }
    }

    @Override
    void move() {
        switch (kidnap) {
            case MARKING, NONE -> {
                if (grounded()) {
                    Player close = nearest();
                    Abyss.glide(body, close != null ? close.getLocation() : fight.center(), 0.15, 0.2, 3);
                } else {
                    orbit += 0.006;
                    Location center = fight.center();
                    double radius = fight.radius() * 0.5;
                    Abyss.glide(body, center.clone().add(Math.cos(orbit) * radius, 0, Math.sin(orbit) * radius), 0.22, HOVER, 0.5);
                    Player close = nearest();
                    if (close != null) {
                        Abyss.face(body, close.getLocation());
                    }
                }
                if (kidnap == Kidnap.MARKING) {
                    marking();
                }
            }
            case SWOOPING -> swooping();
            case CARRYING -> carrying();
        }
    }

    // ------------------------------------------------------------------ kidnap

    private boolean startKidnap() {
        Player chosen = null;
        for (Player player : shuffledPlayers()) {
            if (player != lastPrey && player.isOnGround() && !council.isAirborne(player) && player.getVehicle() == null) {
                chosen = player;
                break;
            }
        }
        if (chosen == null) {   // a lone player is never taken twice in a row either
            return false;
        }
        prey = chosen;
        kidnap = Kidnap.MARKING;
        kidnapTicks = 0;
        council.airborne(prey, MARK + SWOOP + CARRY + 100);
        prey.sendActionBar(Component.text(seat.display() + " is eyeing you from above!", NamedTextColor.GOLD));
        prey.playSound(prey.getLocation(), Sound.ENTITY_PHANTOM_AMBIENT, 1.5F, 0.6F);
        fight.broadcast("&6" + seat.display() + " &eeyes &f" + prey.getName() + "&e...");
        return true;
    }

    private void marking() {
        kidnapTicks++;
        if (!fighting(prey)) {
            endKidnap(false);
            return;
        }
        if (kidnapTicks % 3 == 0) {
            Location at = prey.getLocation().add(0, 2.4, 0);
            at.getWorld().spawnParticle(Particle.DUST, at, 6, 0.3, 0.2, 0.3, 0, new Particle.DustOptions(Color.fromRGB(255, 120, 30), 1.5F));
        }
        if (kidnapTicks >= MARK) {
            kidnap = Kidnap.SWOOPING;
            kidnapTicks = 0;
            body.getWorld().playSound(body.getLocation(), Sound.ENTITY_PHANTOM_SWOOP, 2F, 1F);
        }
    }

    private void swooping() {
        kidnapTicks++;
        if (!fighting(prey) || !alive()) {
            endKidnap(false);
            return;
        }
        Location to = prey.getLocation().add(0, 1.8, 0);
        Vector step = to.toVector().subtract(body.getLocation().toVector());
        double distance = step.length();
        if (distance < 1.5 || kidnapTicks >= SWOOP) {
            grab();
            return;
        }
        body.setVelocity(step.normalize().multiply(Math.min(1.2, distance)));
        Abyss.face(body, prey.getLocation());
    }

    private void grab() {
        Location at = prey.getLocation();
        seatEntity = fight.spawnExtra(ArmorStand.class, at, stand -> {
            stand.setInvisible(true);
            stand.setGravity(false);
            stand.setSmall(true);
            stand.setInvulnerable(true);
            stand.getPersistentDataContainer().set(SEAT, PersistentDataType.BYTE, (byte) 1);
            Keys.setUnhittable(stand, true);
        });
        if (!seatEntity.addPassenger(prey)) {
            seatEntity.remove();
            endKidnap(false);
            return;
        }
        kidnap = Kidnap.CARRYING;
        kidnapTicks = 0;
        carriedFrom = at.getY();
        takenDuringCarry = 0;
        body.teleport(at.clone().add(0, 1.8, 0));
        at.getWorld().playSound(at, Sound.ENTITY_PHANTOM_BITE, 2F, 0.8F);
        prey.sendActionBar(Component.text("Taken!", NamedTextColor.RED));
    }

    private void carrying() {
        kidnapTicks++;
        if (prey == null || !prey.isOnline() || seatEntity == null || !seatEntity.isValid() || !alive()) {
            endKidnap(true);
            return;
        }
        Location now = body.getLocation();
        double top = carriedFrom + CARRY_HEIGHT + 1.8;
        if (now.getY() < top) {
            body.setVelocity(new Vector(0, Math.min(0.4, top - now.getY()), 0));
        } else {
            body.setVelocity(new Vector());
        }
        seatEntity.teleport(body.getLocation().subtract(0, 1.8, 0), TeleportFlag.EntityState.RETAIN_PASSENGERS);
        if (kidnapTicks == 12 || kidnapTicks == 24 || kidnapTicks == 36) {
            body.swingMainHand();
            council.hit(prey, TALON, body);
            prey.getWorld().spawnParticle(Particle.CRIT, prey.getLocation().add(0, 1, 0), 12, 0.3, 0.4, 0.3, 0.1);
        }
        if (takenDuringCarry >= council.poolMax() * DROP_SHARE) {
            fight.broadcast("&eHit hard enough, &6" + seat.display() + " &elets go early!");
            endKidnap(true);
            return;
        }
        if (kidnapTicks >= CARRY) {
            endKidnap(true);
        }
    }

    /** Ends the kidnap; {@code dropped}: the player was carried and now falls (ordinary fall damage). */
    private void endKidnap(boolean dropped) {
        if (seatEntity != null) {
            seatEntity.getPersistentDataContainer().remove(SEAT);   // lets the passenger off
            seatEntity.eject();
            seatEntity.remove();
            seatEntity = null;
        }
        if (dropped && prey != null && prey.isOnline()) {
            fight.expectFall(prey, "Kidnap (Archer)");
            prey.getWorld().playSound(prey.getLocation(), Sound.ENTITY_PHANTOM_FLAP, 1.5F, 0.8F);
            groundedUntil = fight.elapsed() + GROUNDED;
            fight.broadcast("&6" + seat.display() + " &eswoops down to land - &fhit now!");
        }
        lastPrey = prey;
        prey = null;
        kidnap = Kidnap.NONE;
    }

    /** Whether {@code entity} is a kidnap seat still holding its rider. */
    static boolean isSeat(@Nullable Entity entity) {
        return entity != null && entity.getPersistentDataContainer().has(SEAT, PersistentDataType.BYTE);
    }

    // ------------------------------------------------------------------ raid mechanics

    private boolean arrowRain() {
        List<Player> players = shuffledPlayers();
        if (!alive() || players.isEmpty()) {
            return false;
        }
        int count = Math.min(council.pace().overlap() + 1, players.size());
        for (Player player : players.subList(0, count)) {
            council.add(new PlayerMarker(fight, player, 60, 12, 3, council.scaled(RAIN), body), true);
        }
        body.getWorld().playSound(body.getLocation(), Sound.ITEM_CROSSBOW_LOADING_END, 2F, 0.7F);
        fight.broadcast("&6" + seat.display() + " &enocks a volley - &fmarked players, spread out!");
        return true;
    }

    private boolean arrowWall() {
        if (!alive()) {
            return false;
        }
        council.add(new MovingBarrier(fight, fight.center(), Math.random() * Math.PI * 2, fight.radius(), 0.25, 1.8, 40,
            Material.BROWN_STAINED_GLASS, council.scaled(WALL), body), true);
        fight.broadcast("&6" + seat.display() + " &elooses a wall of arrows - &ffind the gap!");
        return true;
    }
}
