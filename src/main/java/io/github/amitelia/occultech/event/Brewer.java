package io.github.amitelia.occultech.event;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.BooleanSupplier;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * Pancake, the brewer (Council seat, Session E7): keeps away from the crowd and brews.
 * <ul>
 * <li><b>Splash potions</b>: potions arc onto marked circles under a few players - step out - and slow and weaken.</li>
 * <li><b>Syrup</b>: sticky puddles that slow; more of them as the bar falls.</li>
 * <li><b>Taste test</b> (raid mechanic): a big brew - soak circles.</li>
 * <li><b>Updraft</b>: interrupts players. A marked player (2 s of swirling bubbles) is sent about 12 blocks straight up and
 * takes the fall (ordinary fall damage). It goes for players standing in soak circles or hitting Pancake, so others have
 * to cover. Never the same player twice in a row, never someone already in the air.</li>
 * <li><b>Drink</b>: 3 s of loud drinking heals the shared bar, unless enough damage on Pancake interrupts it.</li>
 * </ul>
 */
final class Brewer extends CouncilMember {

    private static final Mechanic SPLASH = Mechanic.of(CouncilBehavior.ID, "Splash potion (Brewer)", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic TASTE = Mechanic.of(CouncilBehavior.ID, "Taste test (Brewer)", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic SPOILED = Mechanic.of(CouncilBehavior.ID, "Spoiled brew (Brewer)", 30, Mechanic.Kind.AREA, true);
    private static final int SPLASH_WARNING = 30;
    private static final double SPLASH_RADIUS = 2.2;
    private static final int UPDRAFT_WARNING = 40;
    private static final double UPDRAFT_SPEED = 1.6;
    private static final int DRINK = 60;
    private static final double DRINK_HEAL = 0.04;
    /** Damage on Pancake during the drink, as a share of the pool, that interrupts it. */
    private static final double INTERRUPT_SHARE = 0.015;
    private static final Color SYRUP = Color.fromRGB(190, 120, 30);

    private int nextSplash = 100;
    private int nextSyrup = 200;
    private int nextUpdraft = 160;
    private int nextDrink = 400;
    private int drinking = -1;
    private double takenWhileDrinking;
    @Nullable private Player lastLaunched;
    /** Who hit Pancake lately, and when. */
    private final Map<UUID, Integer> attackers = new HashMap<>();

    Brewer(CouncilBehavior council, Location at, CouncilBehavior.Seat seat) {
        super(council, at, seat);
        body.getEquipment().setItemInMainHand(new ItemStack(Material.SPLASH_POTION));
    }

    @Override
    List<BooleanSupplier> majors() {
        return List.of(this::tasteTest);
    }

    @Override
    void onHitBy(Player player, double damage) {
        attackers.put(player.getUniqueId(), fight.elapsed());
        if (drinking >= 0) {
            takenWhileDrinking += damage;
        }
    }

    @Override
    void tick(int now) {
        if (drinking >= 0) {
            return;
        }
        RaidPace pace = council.pace();
        if (now >= nextSplash) {
            nextSplash = now + pace.cooldown(180);
            splash();
        }
        if (now >= nextSyrup) {
            nextSyrup = now + pace.cooldown(300);
            syrup(pace.band() + 1);
        }
        if (now >= nextUpdraft) {
            nextUpdraft = now + 20;
            if (updraft()) {
                nextUpdraft = now + pace.cooldown(260);
            }
        }
        if (now >= nextDrink && council.poolFraction() < 0.9) {
            nextDrink = now + pace.cooldown(500);
            drink();
        }
    }

    @Override
    void move() {
        if (drinking >= 0) {
            drinkTick();
            return;
        }
        Player close = nearest();
        if (close != null) {
            walk(close.getLocation(), 0.22, 9, fight.radius() * 0.7);
        }
    }

    // ------------------------------------------------------------------ splash potions

    private void splash() {
        List<Player> players = shuffledPlayers();
        if (players.isEmpty()) {
            return;
        }
        body.swingMainHand();
        body.getWorld().playSound(body.getLocation(), Sound.ENTITY_WITCH_THROW, 1.5F, 1F);
        Location hand = body.getLocation().add(0, 1.6, 0);
        for (Player player : players.subList(0, Math.min(3, players.size()))) {
            Location spot = player.getLocation();
            fight.telegraph(spot, SPLASH_RADIUS, SPLASH_WARNING, Color.fromRGB(170, 70, 200));
            ItemDisplay bottle = fight.spawnExtra(ItemDisplay.class, hand, d -> {
                d.setItemStack(new ItemStack(Material.SPLASH_POTION));
                d.setTeleportDuration(1);
            });
            for (int t = 1; t <= SPLASH_WARNING; t++) {
                double progress = t / (double) SPLASH_WARNING;
                Location at = hand.clone().add(spot.toVector().subtract(hand.toVector()).multiply(progress)).add(0, Math.sin(Math.PI * progress) * 4, 0);
                council.later(t, () -> {
                    if (bottle.isValid()) {
                        bottle.teleport(at);
                    }
                });
            }
            council.later(SPLASH_WARNING, () -> {
                bottle.remove();
                spot.getWorld().spawnParticle(Particle.ENTITY_EFFECT, spot.clone().add(0, 0.5, 0), 60, SPLASH_RADIUS / 2, 0.4, SPLASH_RADIUS / 2, 1,
                    Color.fromRGB(170, 70, 200));
                spot.getWorld().playSound(spot, Sound.ENTITY_SPLASH_POTION_BREAK, 1.5F, 1F);
                if (!alive()) {
                    return;
                }
                for (Player hit : fight.players()) {
                    if (hit.getLocation().distanceSquared(spot) <= SPLASH_RADIUS * SPLASH_RADIUS) {
                        council.hit(hit, SPLASH, body);
                        hit.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 0));
                        hit.addPotionEffect(new PotionEffect(PotionEffectType.WEAKNESS, 60, 0));
                    }
                }
            });
        }
    }

    // ------------------------------------------------------------------ syrup

    private void syrup(int puddles) {
        List<Player> players = shuffledPlayers();
        if (players.isEmpty()) {
            return;
        }
        for (int i = 0; i < puddles; i++) {
            Location near = players.get(i % players.size()).getLocation();
            Location spot = near.clone().add((Math.random() - 0.5) * 6, 0, (Math.random() - 0.5) * 6);
            spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
            fight.addHazard(spot, 3, 300, SYRUP, p -> p.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 1, false, true)));
            spot.getWorld().playSound(spot, Sound.BLOCK_HONEY_BLOCK_PLACE, 1.5F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ updraft

    private boolean updraft() {
        int now = fight.elapsed();
        Player chosen = null;
        int best = -1;
        for (Player player : shuffledPlayers()) {
            if (player == lastLaunched || !player.isOnGround() || council.isAirborne(player) || player.getVehicle() != null) {
                continue;
            }
            // the ones holding a soak circle or hitting Pancake come first
            int weight = council.soaking(player) ? 2 : now - attackers.getOrDefault(player.getUniqueId(), -1000) < 100 ? 1 : 0;
            if (weight > best) {
                chosen = player;
                best = weight;
            }
        }
        if (chosen == null) {
            return false;
        }
        Player target = chosen;
        lastLaunched = target;
        council.airborne(target, UPDRAFT_WARNING + 100);
        target.sendActionBar(Component.text(seat.display() + " is brewing an updraft under you!", NamedTextColor.AQUA));
        target.playSound(target.getLocation(), Sound.BLOCK_BUBBLE_COLUMN_UPWARDS_INSIDE, 2F, 1F);
        body.swingMainHand();
        for (int t = 0; t < UPDRAFT_WARNING; t += 2) {
            int tick = t;
            council.later(t, () -> {
                if (target.isOnline()) {
                    double a = tick * 0.4;
                    Location at = target.getLocation();
                    for (int i = 0; i < 3; i++) {
                        double angle = a + i * Math.PI * 2 / 3;
                        at.getWorld().spawnParticle(Particle.BUBBLE_POP, at.clone().add(Math.cos(angle) * 0.8, tick * 0.04, Math.sin(angle) * 0.8), 2,
                            0.05, 0.05, 0.05, 0.01);
                    }
                }
            });
        }
        council.later(UPDRAFT_WARNING, () -> {
            if (!alive() || !fighting(target) || target.getVehicle() != null) {
                return;
            }
            target.setVelocity(new Vector(0, UPDRAFT_SPEED, 0));   // straight up: they land where they stood
            fight.expectFall(target, "Updraft (Brewer)");
            target.getWorld().spawnParticle(Particle.CLOUD, target.getLocation(), 30, 0.4, 0.2, 0.4, 0.1);
            target.getWorld().playSound(target.getLocation(), Sound.ENTITY_BREEZE_JUMP, 2F, 0.8F);
        });
        return true;
    }

    // ------------------------------------------------------------------ drink

    private void drink() {
        drinking = 0;
        takenWhileDrinking = 0;
        body.getEquipment().setItemInMainHand(new ItemStack(Material.POTION));
        fight.broadcast("&6" + seat.display() + " &estarts drinking a brew - &finterrupt it!");
    }

    private void drinkTick() {
        body.setVelocity(new Vector(0, body.getVelocity().getY(), 0));   // stands still to drink
        if (drinking % 8 == 0) {
            body.getWorld().playSound(body.getLocation(), Sound.ENTITY_GENERIC_DRINK, 2F, 0.8F);
            body.getWorld().spawnParticle(Particle.ENTITY_EFFECT, body.getLocation().add(0, 2, 0), 10, 0.3, 0.3, 0.3, 1, Color.fromRGB(240, 90, 160));
        }
        if (takenWhileDrinking >= council.poolMax() * INTERRUPT_SHARE) {
            drinking = -1;
            body.getEquipment().setItemInMainHand(new ItemStack(Material.SPLASH_POTION));
            body.getWorld().playSound(body.getLocation(), Sound.BLOCK_GLASS_BREAK, 1.5F, 1F);
            fight.broadcast("&eInterrupted! &6" + seat.display() + " &edrops the brew.");
            return;
        }
        if (++drinking >= DRINK) {
            drinking = -1;
            body.getEquipment().setItemInMainHand(new ItemStack(Material.SPLASH_POTION));
            council.heal(DRINK_HEAL);
            body.getWorld().spawnParticle(Particle.HEART, body.getLocation().add(0, 2.2, 0), 8, 0.5, 0.3, 0.5, 0);
            fight.broadcast("&6" + seat.display() + " &efinishes the brew - &cthe Council heals.");
        }
    }

    // ------------------------------------------------------------------ raid mechanic

    private boolean tasteTest() {
        if (!alive()) {
            return false;
        }
        council.soakCircles(TASTE, SPOILED, body);
        body.getWorld().playSound(body.getLocation(), Sound.BLOCK_BREWING_STAND_BREW, 2F, 0.8F);
        fight.broadcast("&6" + seat.display() + " &ebrews a big one - &ftaste test! Fill the circles!");
        return true;
    }
}
