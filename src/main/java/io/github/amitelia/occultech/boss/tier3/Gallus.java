package io.github.amitelia.occultech.boss.tier3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Chicken;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Evoker;
import org.bukkit.entity.Guardian;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Slime;
import org.bukkit.entity.Snowball;
import org.bukkit.entity.Zombie;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-3 gate and the final boss (Infinity gear): Gallus, a chicken the size of a ghast, ridden by a baby-zombie knight.
 * <ol>
 * <li><b>The Joust (100-66%)</b>: it runs players down while the rider jabs; wing leap with a warned landing ring
 * (it never takes fall damage); egg barrage - custom eggs (never real chicken eggs) leave splat zones, and some crack
 * into small chick jockeys (capped).</li>
 * <li><b>Unhorsed (66-33%)</b>: the rider falls off and fights on foot - tiny, fast and hard-hitting. Every 20s it
 * runs back to remount; a successful remount heals Gallus, so knock it away. Killing the rider here is optional.</li>
 * <li><b>The Hollowing (33-0%)</b>: Gallus turns undead and flies over the arena, swooping low and climbing high. It
 * lays Hollow Eggs around the circle; any egg not broken in time hatches a weak echo of an earlier gate boss.
 * If the rider survived phase 2 it rides again and dives at players breaking eggs; if it was killed, Gallus is alone
 * and can no longer be healed. At 10% it shrinks to a normal chicken and bolts - the last chase.</li>
 * </ol>
 * Gallus takes a twentieth of the damage dealt (health attributes cap at 1024).
 */
public final class Gallus extends BossBehavior {

    private static final double HEALTH = 500;
    private static final double ARMOR = 0.05;
    private static final double SCALE = 6;
    private static final double RIDER_HEALTH = 120;
    private static final double JAB = 45;
    private static final double SLAM = 55;
    private static final double EGG_HIT = 20;
    private static final double RIDER_MELEE = 35;
    private static final int LEAP_INTERVAL = 200;
    private static final int REMOUNT_INTERVAL = 400;
    private static final int REMOUNT_TIME = 80;
    private static final int HOLLOW_EGG_INTERVAL = 300;
    private static final int HATCH_TICKS = 200;
    private static final Color YOLK = Color.fromRGB(250, 220, 90);
    private static final Color HOLLOW = Color.fromRGB(80, 230, 230);

    private Chicken gallus;
    private Zombie rider;
    private int phase = 1;
    private boolean riderDead;
    private Player target;

    // phase 1-2: leaping
    private boolean leaping;
    private int leapStartedAt;
    private Location leapSpot;
    private int leapAt = -1;
    // eggs in flight -> last known position
    private final Map<Snowball, Location> eggs = new HashMap<>();
    // phase 2: remounting
    private int remountUntil = -1;
    private int nextRemount;
    private int dismountAt = -1;
    // phase 3: hollow eggs, echoes, the rider's dives
    private final Map<BossFight.FightObject, Integer> hollowEggs = new HashMap<>();
    private final List<Guardian> guardianEchoes = new ArrayList<>();
    private final List<Abyss.Beam> beams = new ArrayList<>();
    private int echoKind;
    private double flightAngle;
    private int diveUntil = -1;

    public Gallus(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        gallus = fight.spawnBoss(Chicken.class, at.clone().add(0, 1, 0), c -> {
            c.setCustomName(ChatColor.GOLD + "Gallus" + ChatColor.GRAY + ", the Hollow Jockey");
            c.setCustomNameVisible(true);
            Abyss.puppet(c);
            c.setGravity(true);
            c.setAdult();
            c.setEggLayTime(Integer.MAX_VALUE);
            BossFight.setAttribute(c, Attribute.MAX_HEALTH, HEALTH);
            BossFight.setAttribute(c, Attribute.SCALE, SCALE);
            BossFight.setAttribute(c, Attribute.KNOCKBACK_RESISTANCE, 1);
            BossFight.setAttribute(c, Attribute.SAFE_FALL_DISTANCE, 1024);
        });
        rider = fight.spawnAdd(Zombie.class, at.clone().add(0, 5, 0), z -> {
            z.setCustomName(ChatColor.DARK_GRAY + "Hollow Knight");
            z.setCustomNameVisible(true);
            z.setBaby();
            z.setShouldBurnInDay(false);
            z.getEquipment().setItemInMainHand(new ItemStack(Material.NETHERITE_SPEAR));
            z.getEquipment().setHelmet(new ItemStack(Material.NETHERITE_HELMET));
            z.getEquipment().setChestplate(new ItemStack(Material.NETHERITE_CHESTPLATE));
            BossFight.setAttribute(z, Attribute.MAX_HEALTH, RIDER_HEALTH);
            z.setHealth(RIDER_HEALTH);
            BossFight.setAttribute(z, Attribute.ATTACK_DAMAGE, RIDER_MELEE);
            BossFight.setAttribute(z, Attribute.SCALE, 2.6);
            // it can't be killed while mounted in phase 1: the split in phase 2 is where it can fall
            Keys.setUnhittable(z, true);
        });
        if (rider != null) {
            gallus.addPassenger(rider);
        }
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR;
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double verticalLeash() {
        return 20;
    }

    @Override
    public void onAddDeath(Entity entity, @Nullable Player killer) {
        if (entity == rider && !riderDead) {
            riderDead = true;
            fight.broadcast(phase < 3 ? "&6The Hollow Knight is slain - &fGallus will face the Hollowing alone, and can't be healed!"
                : "&6The Hollow Knight is slain!");
        }
    }

    // ------------------------------------------------------------------ every tick: movement

    @Override
    public void move() {
        if (!gallus.isValid()) {
            return;
        }
        int now = fight.elapsed();
        eggs.replaceAll((egg, last) -> egg.isValid() ? egg.getLocation() : last);
        guardianEchoes.removeIf(g -> !g.isValid() || g.isDead());
        for (Guardian echo : guardianEchoes) {
            Player near = fight.nearestPlayer(echo.getLocation());
            if (near != null) {
                Abyss.glide(echo, near.getLocation(), 0.14, 1.5, 5);
            }
        }

        if (phase == 4) {
            // the last chase: run away from the nearest player
            Player near = fight.nearestPlayer(gallus.getLocation());
            if (near != null) {
                Vector away = gallus.getLocation().toVector().subtract(near.getLocation().toVector()).setY(0);
                Location flee = gallus.getLocation().add(away.normalize().multiply(4));
                Abyss.walk(gallus, keepInside(flee), 0.42, 0);
            }
            return;
        }
        if (phase == 3) {
            // fly in a wide circle, swooping low (hittable) and climbing high (break eggs then)
            flightAngle += 0.012;
            double hover = 3.5 + 3 * Math.sin(now * 0.03);
            Location spot = fight.center().clone().add(Math.cos(flightAngle) * 9, 0, Math.sin(flightAngle) * 9);
            Abyss.glide(gallus, spot, 0.2, Math.max(0.5, hover), 0);
            return;
        }
        if (leaping) {
            return; // ballistic: physics carries the leap
        }
        if (alive(target)) {
            Abyss.walk(gallus, target.getLocation(), phase == 1 ? 0.24 : 0.15, 3);
        }
    }

    // ------------------------------------------------------------------ every step: phases and attacks

    @Override
    public void tick() {
        if (!gallus.isValid()) {
            return;
        }
        int now = fight.elapsed();
        double health = fight.healthFraction();
        if (phase == 1 && health < 0.66) {
            unhorse();
        } else if (phase == 2 && health < 0.33) {
            hollowing();
        } else if (phase == 3 && health < 0.10) {
            lastCluck();
        }
        if (!alive(target) || every(100)) {
            target = phase == 1 ? fight.nearestPlayer(gallus.getLocation()) : fight.randomPlayer();
        }

        landEggs();
        switch (phase) {
            case 1 -> joust(now);
            case 2 -> unhorsed(now);
            case 3 -> hollowed(now);
            default -> { }
        }
    }

    private void joust(int now) {
        if (alive(target) && riderMounted() && every(20) && target.getLocation().distanceSquared(gallus.getLocation()) <= 30) {
            rider.swingMainHand();
            target.damage(JAB, rider);
        }
        leap(now);
        if (every(140)) {
            eggBarrage(5);
        }
    }

    private void unhorsed(int now) {
        leap(now);
        if (every(100)) {
            eggBarrage(6);
        }
        if (riderDead || rider == null || !rider.isValid()) {
            return;
        }
        if (riderMounted()) {
            if (dismountAt >= 0 && now >= dismountAt) {
                dismountAt = -1;
                gallus.removePassenger(rider);
                rider.setVelocity(new Vector(0, 0.6, 0));
                rider.setTarget(fight.randomPlayer());
            }
            return;
        }
        if (remountUntil < 0 && now >= nextRemount) {
            remountUntil = now + REMOUNT_TIME;
            nextRemount = now + REMOUNT_INTERVAL;
            fight.broadcast("&6The Hollow Knight runs for its mount - &fknock it away!");
        }
        if (remountUntil >= 0) {
            rider.setTarget(null);
            rider.getPathfinder().moveTo(gallus.getLocation(), 1.8);
            Abyss.line(rider.getLocation().add(0, 0.6, 0), gallus.getLocation().add(0, 2, 0), new Particle.DustOptions(YOLK, 0.7F), 0.8);
            if (rider.getLocation().distanceSquared(gallus.getLocation()) <= 12) {
                remountUntil = -1;
                gallus.addPassenger(rider);
                fight.healBoss(gallus, 0.08);
                dismountAt = now + 100;
                fight.broadcast("&6The knight is back in the saddle - &fGallus is healed.");
                gallus.getWorld().playSound(gallus.getLocation(), Sound.ENTITY_CHICKEN_AMBIENT, 2F, 0.5F);
            } else if (now >= remountUntil) {
                remountUntil = -1;
                rider.setTarget(fight.randomPlayer());
            }
        }
    }

    private void hollowed(int now) {
        if (every(5)) {
            gallus.getWorld().spawnParticle(Particle.SOUL, gallus.getLocation().add(0, 2, 0), 3, 1, 1.2, 1, 0.02);
            gallus.getWorld().spawnParticle(Particle.LARGE_SMOKE, gallus.getLocation().add(0, 1, 0), 2, 0.8, 0.5, 0.8, 0.01);
        }
        if (every(HOLLOW_EGG_INTERVAL)) {
            layHollowEggs(now);
        }
        for (Iterator<Map.Entry<BossFight.FightObject, Integer>> it = hollowEggs.entrySet().iterator(); it.hasNext();) {
            Map.Entry<BossFight.FightObject, Integer> egg = it.next();
            if (!egg.getKey().isAlive()) {
                it.remove();
            } else if (now >= egg.getValue()) {
                Location at = egg.getKey().location().clone();
                egg.getKey().remove();
                it.remove();
                hatchEcho(at);
            }
        }
        if (every(160)) {
            eggBarrage(4);
        }
        // guardian echoes fire small beams
        if (every(80)) {
            for (Guardian echo : guardianEchoes) {
                Player near = fight.nearestPlayer(echo.getLocation());
                if (near != null) {
                    beams.add(new Abyss.Beam(echo, near, now, 30, 15, HOLLOW));
                }
            }
        }
        beams.forEach(beam -> beam.step(fight, now));
        beams.removeIf(Abyss.Beam::done);

        // the rider's dives
        if (riderDead || rider == null || !rider.isValid()) {
            return;
        }
        if (diveUntil < 0 && every(240)) {
            Player victim = nearestToAnEgg();
            if (victim != null) {
                diveUntil = now + 100;
                gallus.removePassenger(rider);
                Vector toward = victim.getLocation().toVector().subtract(rider.getLocation().toVector());
                rider.setVelocity(toward.multiply(0.12).setY(0.2));
                rider.setTarget(victim);
                fight.broadcast("&6The Hollow Knight dives at you!");
            }
        } else if (diveUntil >= 0 && now >= diveUntil) {
            diveUntil = -1;
            rider.teleport(gallus.getLocation().add(0, 3, 0));
            gallus.addPassenger(rider);
        }
    }

    // ------------------------------------------------------------------ phase changes

    private void unhorse() {
        phase = 2;
        if (rider != null) {
            Keys.setUnhittable(rider, false);
        }
        nextRemount = fight.elapsed() + 300;
        if (riderMounted()) {
            gallus.removePassenger(rider);
            rider.setVelocity(new Vector(0.3, 0.6, 0));
            rider.setTarget(fight.randomPlayer());
        }
        gallus.getWorld().playSound(gallus.getLocation(), Sound.ENTITY_CHICKEN_HURT, 2F, 0.4F);
        fight.broadcast("&6Gallus throws its rider! &fTwo of them now - keep the knight away from its mount.");
    }

    private void hollowing() {
        phase = 3;
        leaping = false;
        gallus.setGravity(false);
        gallus.getWorld().playSound(gallus.getLocation(), Sound.ENTITY_WITHER_SPAWN, 1F, 1.6F);
        fight.broadcast("&3&lThe Hollowing! &fGallus takes to the air - break its Hollow Eggs before they hatch!");
        if (!riderDead && rider != null && rider.isValid()) {
            rider.teleport(gallus.getLocation().add(0, 3, 0));
            gallus.addPassenger(rider);
        }
    }

    private void lastCluck() {
        phase = 4;
        if (riderMounted()) {
            gallus.removePassenger(rider);
        }
        gallus.setGravity(true);
        BossFight.setAttribute(gallus, Attribute.SCALE, 1.2);
        gallus.getWorld().playSound(gallus.getLocation(), Sound.ENTITY_CHICKEN_HURT, 2F, 1.8F);
        fight.broadcast("&eGallus shrinks to a frantic little chicken - &fcatch it!");
    }

    // ------------------------------------------------------------------ attacks

    private void leap(int now) {
        if (leaping) {
            boolean landed = gallus.isOnGround() && now - leapStartedAt >= 10;
            if (landed || now - leapStartedAt > 80) {
                leaping = false;
                slam(gallus.getLocation());
            }
            return;
        }
        if (leapAt < 0 && every(phase == 1 ? LEAP_INTERVAL : 260) && alive(target)) {
            leapSpot = target.getLocation();
            leapSpot.setY(Abyss.groundY(leapSpot));
            leapAt = now + 20;
            fight.telegraph(leapSpot, 5, 60, YOLK);
            gallus.getWorld().playSound(gallus.getLocation(), Sound.ENTITY_CHICKEN_AMBIENT, 2F, 0.4F);
        }
        if (leapAt >= 0 && now >= leapAt) {
            leapAt = -1;
            leaping = true;
            leapStartedAt = now;
            Vector toward = leapSpot.toVector().subtract(gallus.getLocation().toVector()).setY(0);
            gallus.setVelocity(toward.multiply(1.0 / 22).setY(1.25));
            gallus.getWorld().spawnParticle(Particle.CLOUD, gallus.getLocation(), 30, 1.5, 0.3, 1.5, 0.05);
        }
    }

    private void slam(Location at) {
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_BIG_FALL, 2F, 0.5F);
        at.getWorld().spawnParticle(Particle.EXPLOSION, at.clone().add(0, 0.5, 0), 2, 1.5, 0.2, 1.5);
        at.getWorld().spawnParticle(Particle.CLOUD, at.clone().add(0, 0.3, 0), 60, 3, 0.2, 3, 0.05);
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 25) {
                player.damage(SLAM, gallus);
                player.setVelocity(player.getVelocity().setY(0.8));
            }
        }
    }

    /** Custom eggs: snowballs that look like eggs, so they can never hatch real chickens. */
    private void eggBarrage(int count) {
        List<Player> players = fight.players();
        if (players.isEmpty()) {
            return;
        }
        ThreadLocalRandom random = ThreadLocalRandom.current();
        Location from = gallus.getLocation().add(0, 3, 0);
        for (int i = 0; i < count; i++) {
            Location aim = players.get(random.nextInt(players.size())).getLocation().add(random.nextDouble(-4, 4), 0, random.nextDouble(-4, 4));
            Vector flat = aim.toVector().subtract(from.toVector()).setY(0);
            double distance = flat.length();
            Vector velocity = flat.normalize().multiply(Math.min(1.6, distance / 14)).setY(0.55);
            Snowball egg = fight.spawnExtra(Snowball.class, from, s -> {
                s.setItem(new ItemStack(Material.EGG));
                s.setShooter(gallus);
                s.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, EGG_HIT);
            });
            egg.setVelocity(velocity);
            eggs.put(egg, egg.getLocation());
        }
        gallus.getWorld().playSound(from, Sound.ENTITY_CHICKEN_EGG, 2F, 0.5F);
    }

    /** Eggs that landed leave a sticky splat; some crack into chick jockeys. */
    private void landEggs() {
        for (Iterator<Map.Entry<Snowball, Location>> it = eggs.entrySet().iterator(); it.hasNext();) {
            Map.Entry<Snowball, Location> egg = it.next();
            if (egg.getKey().isValid()) {
                continue;
            }
            it.remove();
            Location at = egg.getValue().clone();
            at.setY(Abyss.groundY(at));
            fight.addHazard(at, 2, 80, YOLK, player -> {
                Abyss.magic(player, 6, gallus);
                player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 30, 1));
            });
            at.getWorld().spawnParticle(Particle.ITEM, at.clone().add(0, 0.3, 0), 12, 0.3, 0.1, 0.3, 0.05, new ItemStack(Material.EGG));
            if (ThreadLocalRandom.current().nextInt(3) == 0) {
                chickJockey(at.add(0, 0.5, 0));
            }
        }
    }

    private void chickJockey(Location at) {
        Chicken chick = fight.spawnAdd(Chicken.class, at, c -> {
            c.setBaby();
            c.setEggLayTime(Integer.MAX_VALUE);
            BossFight.setAttribute(c, Attribute.MAX_HEALTH, 10);
            c.setHealth(10);
        });
        if (chick == null) {
            return;
        }
        Zombie jockey = fight.spawnAdd(Zombie.class, at, z -> {
            z.setBaby();
            z.setShouldBurnInDay(false);
            BossFight.setAttribute(z, Attribute.MAX_HEALTH, 16);
            z.setHealth(16);
            BossFight.setAttribute(z, Attribute.ATTACK_DAMAGE, 20);
        });
        if (jockey != null) {
            chick.addPassenger(jockey);
            jockey.setTarget(fight.nearestPlayer(at));
        }
    }

    private void layHollowEggs(int now) {
        for (int i = 0; i < 3; i++) {
            Location at = fight.randomPoint(5, Math.min(fight.radius() - 3, 15));
            Abyss.line(gallus.getLocation(), at.clone().add(0, 0.5, 0), new Particle.DustOptions(HOLLOW, 1F), 0.8);
            hollowEggs.put(fight.spawnObject(at, Material.SNIFFER_EGG, 1.2F, 4, () ->
                at.getWorld().playSound(at, Sound.BLOCK_SNIFFER_EGG_CRACK, 1.5F, 0.6F)), now + HATCH_TICKS);
        }
        fight.broadcast("&3Hollow Eggs fall around the circle - &fbreak them before they hatch!");
    }

    /** An unbroken Hollow Egg hatches a weak echo of an earlier gate boss. */
    private void hatchEcho(Location at) {
        at.getWorld().playSound(at, Sound.BLOCK_SNIFFER_EGG_HATCH, 2F, 0.5F);
        at.getWorld().spawnParticle(Particle.SOUL, at.clone().add(0, 1, 0), 30, 0.5, 0.6, 0.5, 0.05);
        Location spawn = at.clone().add(0, 1, 0);
        switch (echoKind++ % 3) {
            case 0 -> fight.spawnAdd(Slime.class, spawn, s -> {
                s.setSize(3);
                s.setCustomName(ChatColor.GREEN + "Echo of the Sovereign");
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 50);
                s.setHealth(50);
            });
            case 1 -> fight.spawnAdd(Evoker.class, spawn, e -> {
                e.setCustomName(ChatColor.DARK_GREEN + "Echo of the Archevoker");
                BossFight.setAttribute(e, Attribute.MAX_HEALTH, 50);
                e.setHealth(50);
            });
            default -> {
                Guardian echo = fight.spawnAdd(Guardian.class, spawn, g -> {
                    g.setCustomName(ChatColor.DARK_AQUA + "Echo of the Drowned Elder");
                    Abyss.puppet(g);
                    BossFight.setAttribute(g, Attribute.MAX_HEALTH, 50);
                    g.setHealth(50);
                });
                if (echo != null) {
                    guardianEchoes.add(echo);
                }
            }
        }
    }

    // ------------------------------------------------------------------ helpers

    @Nullable
    private Player nearestToAnEgg() {
        Player best = null;
        double bestDistance = Double.MAX_VALUE;
        for (Player player : fight.players()) {
            for (BossFight.FightObject egg : hollowEggs.keySet()) {
                double d = player.getLocation().distanceSquared(egg.location());
                if (d < bestDistance) {
                    best = player;
                    bestDistance = d;
                }
            }
        }
        return best != null ? best : fight.randomPlayer();
    }

    private Location keepInside(Location spot) {
        Vector offset = spot.toVector().subtract(fight.center().toVector()).setY(0);
        double max = fight.radius() - 3;
        if (offset.length() > max) {
            offset.normalize().multiply(max);
        }
        return fight.center().clone().add(offset);
    }

    private boolean riderMounted() {
        return rider != null && rider.isValid() && gallus.getPassengers().contains(rider);
    }

    private static boolean alive(Player player) {
        return player != null && player.isValid() && !player.isDead();
    }
}
