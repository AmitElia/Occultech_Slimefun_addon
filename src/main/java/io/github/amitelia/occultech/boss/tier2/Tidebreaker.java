package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Prop;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Drowned;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Pig;
import org.bukkit.entity.Player;
import org.bukkit.entity.Trident;
import org.bukkit.entity.ZombieNautilus;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-2 mini-boss (max netherite): a drowned Viking standing in a longship's bow nailed onto a colossal nautilus, which
 * "swims" through the air over land, throwing a bow wave.
 * <ul>
 * <li>Ram charge: a line warns for 1s, then the nautilus charges along it, hurting and throwing anyone in the way.
 * After a charge it is <b>winded for 2s</b> - the melee window.</li>
 * <li>Trident volley: three tridents in a fan (they can't be picked up).</li>
 * <li>Melee: the rider's spear strikes anyone close.</li>
 * </ul>
 * The nautilus can't be hurt; only the rider counts. Takes a third of the damage dealt. With MythicMobs and BetterModel
 * the drowned wears occultech_tidebreaker and the nautilus occultech_tidebreaker_mount (Session 8). They are two
 * models on two entities, so the rider keeps the nautilus's yaw and only his head follows the target.
 */
public final class Tidebreaker extends BossBehavior {

    private static final double HEALTH = 300;
    private static final double ARMOR = 0.33;
    private static final Color WARNING = Color.fromRGB(40, 110, 200);
    private static final int CHARGE_INTERVAL = 160;
    private static final int CHARGE_WARNING = 20;
    private static final int CHARGE_TICKS = 25;
    private static final int WINDED_TICKS = 40;
    private static final int VOLLEY_INTERVAL = 200;
    /** The model's clips: the volley leaves his hand 0.7s in, the jab lands 0.25s in. */
    private static final int VOLLEY_RELEASE = 14;
    private static final int THRUST_CONTACT = 5;
    private static final double MELEE_RANGE = 4;
    /** Where his hand is at the release, from the carrier in blocks (tide_ship.py prints it from the posed rig). */
    private static final double HAND_UP = 3.3;
    private static final double HAND_AHEAD = 2.86;
    private static final double HAND_RIGHT = 0.31;
    /** How far the turning head may look away from the way the ship faces. */
    private static final float HEAD_LIMIT = 55F;
    /** Moving slower than this (blocks a tick) throws no bow wave. */
    private static final double WAKE_MIN_SPEED = 0.05;
    private static final double RAM_SPEED = 0.7;
    private static final double HOVER = 0.4;
    private static final io.github.amitelia.occultech.boss.Mechanic RAM_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TIDEBREAKER", "Ram", 33.5, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic MELEE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TIDEBREAKER", "Trident thrust", 23, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic TRIDENT_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("TIDEBREAKER", "Trident volley", 24, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);

    private Drowned rider;
    private Mob mount;
    private Vector chargeDirection;
    private int chargeAt = -1;
    private int chargeEnd = -1;
    private int windedUntil = -1;
    private int nextCharge = 80;
    private int nextMelee;
    private int thrustAt = -1;
    private int volleyAt = -1;
    @Nullable private Player struck;
    @Nullable private Player volleyTarget;
    private int lastFlinch = -100;
    private final java.util.Set<java.util.UUID> rammed = new java.util.HashSet<>();
    /** Who the nautilus swims after (chosen each step, followed every tick). */
    private Player chase;
    @Nullable private Location lastAt;

    public Tidebreaker(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        Location start = at.clone().add(0, 1, 0);
        java.util.function.Consumer<Mob> setup = n -> {
            Abyss.puppet(n);
            n.setInvulnerable(true);
            io.github.amitelia.occultech.core.Keys.setUnhittable(n, true);
            n.setRemoveWhenFarAway(false);
        };
        // with the model the carrier is an invisible pig, which draws nothing under it
        Class<? extends Mob> carrier = fight.usesMythicBody("MOUNT") ? Pig.class : ZombieNautilus.class;
        mount = fight.spawnLookalike("MOUNT", carrier, start, setup::accept);
        rider = fight.spawnBoss(Drowned.class, start, d -> {
            d.setCustomName(ChatColor.BLUE + "Tidebreaker");
            d.setCustomNameVisible(true);
            Abyss.puppet(d);
            d.setGravity(true);
            d.setAdult();
            d.setShouldBurnInDay(false);
            BossFight.setAttribute(d, Attribute.MAX_HEALTH, HEALTH);
        });
        if (!fight.usesMythicBody()) {
            BossFight.setAttribute(mount, Attribute.SCALE, 1.6);
            BossFight.setAttribute(rider, Attribute.SCALE, 1.3);
            rider.getEquipment().setItemInMainHand(new ItemStack(Material.TRIDENT));
            rider.getEquipment().setHelmet(new ItemStack(Material.TURTLE_HELMET));
        }
        mount.addPassenger(rider);
    }

    /** Plays a clip on both models: {@code RAM} on the rider, {@code MOUNT_RAM} on the nautilus. */
    private void both(String action) {
        riderOnly(action, null);
        if (fight.usesMythicBody() && mount.isValid()) {
            fight.playAction(mount, "MOUNT_" + action);
        }
    }

    private void riderOnly(String action, @Nullable Entity target) {
        if (fight.usesMythicBody() && rider.isValid()) {
            fight.playAction(rider, action, target);
        }
    }

    private void lantern(String state) {
        if (fight.usesMythicBody() && mount.isValid()) {
            fight.playAction(mount, "MOUNT_STATE_" + state);
        }
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR;
    }

    @Override
    public void tick() {
        if (!rider.isValid()) {
            return;
        }
        int now = fight.elapsed();
        remount();
        mount.setFireTicks(0);
        resolvePending(now);

        if (now < windedUntil) {
            rider.getWorld().spawnParticle(Particle.SPLASH, rider.getLocation().add(0, 1.5, 0), 6, 0.4, 0.3, 0.4, 0);
            return;
        }
        if (windedUntil > 0) {
            windedUntil = 0;
            lantern("CALM");
        }
        if (chargeEnd >= 0) {
            return; // move() drives the charge
        }
        if (chargeAt >= 0) {
            if (now >= chargeAt) {
                chargeAt = -1;
                chargeEnd = now + CHARGE_TICKS;
                rammed.clear();
                both("RAM");
                mount.getWorld().playSound(mount.getLocation(), Sound.ENTITY_DOLPHIN_JUMP, 2F, 0.5F);
            }
            return;
        }

        Player target = fight.nearestPlayer(mount.getLocation());
        chase = target;
        if (target == null) {
            return;
        }

        if (now >= nextMelee && thrustAt < 0 && volleyAt < 0 && target.getLocation().distanceSquared(rider.getLocation()) <= MELEE_RANGE * MELEE_RANGE) {
            nextMelee = now + 20;
            thrustAt = now + THRUST_CONTACT;
            struck = target;
            rider.swingMainHand();
            riderOnly("THRUST", target);
        }
        if (every(VOLLEY_INTERVAL) && volleyAt < 0) {
            volleyAt = now + VOLLEY_RELEASE;
            volleyTarget = target;
            riderOnly("THROW", target);
        }
        if (now >= nextCharge && volleyAt < 0) {
            nextCharge = now + CHARGE_INTERVAL;
            Player victim = fight.randomPlayer();
            if (victim != null) {
                chargeDirection = victim.getLocation().toVector().subtract(mount.getLocation().toVector()).setY(0);
                if (chargeDirection.lengthSquared() < 1) {
                    chargeDirection = new Vector(1, 0, 0);
                }
                chargeDirection.normalize();
                chargeAt = now + CHARGE_WARNING;
                both("RAM_TELL");
                lantern("RAM");
                if (FloorDecals.enabled()) {
                    FloorDecals.lane(fight, mount.getLocation(), chargeDirection, 16, 3, CHARGE_WARNING, WARNING);
                } else {
                    warnLine();
                }
            }
        }
    }

    /** The jab and the volley land when the clip gets there. */
    private void resolvePending(int now) {
        if (thrustAt >= 0 && now >= thrustAt) {
            thrustAt = -1;
            if (struck != null && struck.isValid() && struck.getWorld() == rider.getWorld()
                && struck.getLocation().distanceSquared(rider.getLocation()) <= MELEE_RANGE * MELEE_RANGE) {
                fight.hit(struck, MELEE_DAMAGE, rider);
            }
        }
        if (volleyAt >= 0 && now >= volleyAt) {
            volleyAt = -1;
            if (volleyTarget != null && volleyTarget.isValid() && volleyTarget.getWorld() == rider.getWorld()) {
                volley(volleyTarget);
            }
        }
    }

    @Override
    public void move() {
        if (!rider.isValid() || !mount.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (now < windedUntil) {
            mount.setVelocity(new Vector());
        } else if (chargeAt >= 0) {
            mount.setVelocity(new Vector());
            faceAlong(chargeDirection);
        } else if (chargeEnd >= 0) {
            faceAlong(chargeDirection);
            charge(now);
        } else {
            // the slow bob of a thing afloat: the entity moves, so the rider and the ship bob together
            double hover = HOVER + 0.08 * Math.sin(now * 0.1);
            if (chase != null && chase.isValid() && chase.getWorld() == mount.getWorld()) {
                Abyss.glide(mount, chase.getLocation(), 0.2, hover, 2.5);
            } else {
                Abyss.glide(mount, fight.center(), 0.12, hover, 0);
            }
        }
        keepRiderOnDeck();
        wake(now);
    }

    private void faceAlong(Vector direction) {
        Location look = mount.getLocation().setDirection(direction);
        mount.setRotation(look.getYaw(), 0);
        mount.setBodyYaw(look.getYaw());
    }

    /** His body keeps the ship's yaw, or he'd spin on the deck; only his head turns to the target, within limits. */
    private void keepRiderOnDeck() {
        float yaw = mount.getBodyYaw();
        float headYaw = yaw;
        float pitch = 0;
        if (chase != null && chase.isValid() && chase.getWorld() == rider.getWorld()) {
            Location look = rider.getEyeLocation().setDirection(chase.getEyeLocation().toVector().subtract(rider.getEyeLocation().toVector()));
            float delta = ((look.getYaw() - yaw) % 360 + 540) % 360 - 180;
            headYaw = yaw + Math.max(-HEAD_LIMIT, Math.min(HEAD_LIMIT, delta));
            pitch = look.getPitch();
        }
        rider.setRotation(headYaw, pitch);
        rider.setBodyYaw(yaw);
    }

    /** One tick of the ram charge. */
    private void charge(int now) {
        Location at = mount.getLocation();
        boolean blocked = !at.clone().add(chargeDirection.clone().multiply(1.5)).add(0, 0.5, 0).getBlock().isPassable();
        boolean outside = at.distanceSquared(fight.center()) > fight.radius() * fight.radius();
        if (now >= chargeEnd || blocked || outside) {
            chargeEnd = -1;
            windedUntil = now + WINDED_TICKS;
            mount.setVelocity(new Vector());
            fight.broadcast("&9The Tidebreaker is winded - &fstrike now!");
            both("WINDED");
            lantern("WINDED");
            crash(at);
            return;
        }
        Vector velocity = chargeDirection.clone().multiply(RAM_SPEED);
        velocity.setY((Abyss.groundY(at) + HOVER - at.getY()) * 0.3);
        mount.setVelocity(velocity);
        for (Player player : fight.players()) {
            if (!rammed.contains(player.getUniqueId()) && player.getLocation().distanceSquared(at) <= 4.5) {
                rammed.add(player.getUniqueId());
                fight.hit(player, RAM_DAMAGE, rider);
                player.setVelocity(chargeDirection.clone().multiply(1.1).setY(0.5));
            }
        }
    }

    // ------------------------------------------------------------------ the bow wave

    /**
     * Water peeling off both sides of the prow, a V that opens back along the hull: foam low on the ground, spray over it
     * and steam at the stem. It grows with speed; the ram throws a wall of it.
     */
    private void wake(int now) {
        Location at = mount.getLocation();
        double speed = lastAt == null || lastAt.getWorld() != at.getWorld() ? 0
            : Math.hypot(at.getX() - lastAt.getX(), at.getZ() - lastAt.getZ());
        lastAt = at;
        boolean ramming = chargeEnd >= 0;
        if (speed < WAKE_MIN_SPEED || (!ramming && now % 2 != 0)) {
            return;
        }
        double strength = Math.min(1, speed / RAM_SPEED);
        World world = at.getWorld();
        Vector ahead = yawDirection(mount.getBodyYaw());
        Vector right = new Vector(-ahead.getZ(), 0, ahead.getX());
        double ground = Abyss.groundY(at) + 0.2;
        int steps = ramming ? 7 : 5;
        for (int side = -1; side <= 1; side += 2) {
            for (int i = 0; i < steps; i++) {
                double t = i / (steps - 1.0);
                // the bow's own curve: from the stem at 2.3 blocks ahead, widening back along the planks
                Location point = at.clone().add(ahead.clone().multiply(2.3 - 3.8 * t))
                    .add(right.clone().multiply(side * (0.15 + 1.35 * Math.sqrt(t))));
                point.setY(ground + 0.15 * t);
                Vector flow = right.clone().multiply(side * (0.1 + 0.16 * strength)).add(ahead.clone().multiply(-0.06));
                world.spawnParticle(Particle.FISHING, point, 0, flow.getX(), 0.01, flow.getZ(), 1);
                world.spawnParticle(Particle.SPLASH, point.clone().add(0, 0.3, 0), ramming ? 5 : 2, 0.2, 0.15, 0.2, 0.05);
                world.spawnParticle(Particle.CLOUD, point, 0, flow.getX() * 0.7, 0.03 + 0.05 * strength, flow.getZ() * 0.7,
                    ramming ? 0.8 : 0.4);
            }
        }
        // steam off the stem, and in the ram a crest thrown up over the prow
        Location stem = at.clone().add(ahead.clone().multiply(2.3));
        stem.setY(ground + 0.5);
        world.spawnParticle(Particle.WHITE_SMOKE, stem, ramming ? 8 : 2, 0.25, 0.2, 0.25, 0.02);
        if (ramming) {
            world.spawnParticle(Particle.SPLASH, stem.clone().add(0, 0.8, 0), 22, 0.5, 0.5, 0.5, 0.25);
            world.spawnParticle(Particle.CLOUD, stem, 6, 0.4, 0.3, 0.4, 0.08);
            if (now % 4 == 0) {
                world.playSound(stem, Sound.ENTITY_PLAYER_SPLASH_HIGH_SPEED, 1.2F, 0.7F);
            }
        } else if (now % 16 == 0) {
            world.playSound(stem, Sound.ENTITY_GENERIC_SPLASH, 0.5F, 0.7F);
        }
    }

    /** The ram ends: the wave it was pushing runs on and breaks over the bow. */
    private void crash(Location at) {
        World world = at.getWorld();
        Vector ahead = yawDirection(mount.getBodyYaw());
        Location stem = at.clone().add(ahead.multiply(2.3)).add(0, 0.8, 0);
        world.spawnParticle(Particle.SPLASH, stem, 90, 1.2, 0.8, 1.2, 0.4);
        world.spawnParticle(Particle.CLOUD, stem, 30, 1, 0.5, 1, 0.1);
        world.playSound(stem, Sound.ENTITY_PLAYER_SPLASH_HIGH_SPEED, 2F, 0.5F);
    }

    /** Which way a yaw faces, flat (Minecraft: yaw 0 faces +z, 90 faces -x). */
    private static Vector yawDirection(float yaw) {
        double r = Math.toRadians(yaw);
        return new Vector(-Math.sin(r), 0, Math.cos(r));
    }

    private void warnLine() {
        Location from = mount.getLocation().add(0, 0.2, 0);
        Particle.DustOptions dust = new Particle.DustOptions(WARNING, 1.6F);
        for (double d = 0; d < 16; d += 0.5) {
            Location point = from.clone().add(chargeDirection.clone().multiply(d));
            point.getWorld().spawnParticle(Particle.DUST, point, 1, 0.3, 0, 0.3, 0, dust);
        }
        mount.getWorld().playSound(from, Sound.ENTITY_DROWNED_AMBIENT, 2F, 0.6F);
    }

    /** His hand at the release, or the carrier's eye without the model. */
    private Location launchPoint() {
        if (!fight.usesMythicBody()) {
            return rider.getEyeLocation();
        }
        Vector ahead = yawDirection(rider.getBodyYaw());
        Vector right = new Vector(-ahead.getZ(), 0, ahead.getX());
        return rider.getLocation().add(0, HAND_UP, 0).add(ahead.multiply(HAND_AHEAD)).add(right.multiply(HAND_RIGHT));
    }

    private void volley(Player target) {
        Location from = launchPoint();
        Vector aim = target.getEyeLocation().toVector().subtract(from.toVector()).normalize();
        rider.swingMainHand();
        for (int i = -1; i <= 1; i++) {
            Vector direction = aim.clone().rotateAroundY(Math.toRadians(12 * i)).multiply(1.8).add(new Vector(0, 0.12, 0));
            Trident trident = rider.launchProjectile(Trident.class, direction);
            trident.teleport(from);
            trident.setVelocity(direction);
            trident.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, TRIDENT_DAMAGE.damage());
            fight.label(trident, TRIDENT_DAMAGE);
        }
        from.getWorld().playSound(from, Sound.ITEM_TRIDENT_THROW, 1.5F, 0.8F);
    }

    /** The engine may teleport the rider (leash, anti-pillar), which dismounts it: bring the nautilus along. */
    private void remount() {
        if (!mount.isValid() || mount.getPassengers().contains(rider)) {
            return;
        }
        mount.teleport(rider.getLocation());
        mount.addPassenger(rider);
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        int now = fight.elapsed();
        if (now - lastFlinch > 12 && chargeAt < 0 && chargeEnd < 0 && now >= windedUntil && volleyAt < 0 && thrustAt < 0) {
            lastFlinch = now;
            riderOnly("FLINCH", null);
        }
    }

    @Override
    public void onBossDeath(LivingEntity boss) {
        fight.corpse(boss);
        Prop ship = mount.isValid() ? fight.corpse(mount) : null;
        if (ship != null) {
            ship.tint(Color.fromRGB(44, 42, 46).asRGB(), "lantern");
        }
    }
}
