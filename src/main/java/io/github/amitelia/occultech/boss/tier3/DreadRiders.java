package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Prop;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.AbstractHorse;
import org.bukkit.entity.AbstractArrow;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Pig;
import org.bukkit.entity.Player;
import org.bukkit.entity.Skeleton;
import org.bukkit.entity.SkeletonHorse;
import org.bukkit.entity.Trident;
import org.bukkit.entity.Zombie;
import org.bukkit.entity.ZombieHorse;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-3 mini-boss (Infinity gear): two fast horsemen. Each rider has its own health; the horses can't be hurt.
 * <ul>
 * <li><b>Outrider</b> (skeleton): fragile and evasive, circles its target 14 blocks out. Snipe: an aiming line locks
 * on and fires, ending in a lightning strike; arrow volleys; arrow rain on a warned circle. All its lightning is
 * visual only (flash and thunder, no fire, no mob changes); the damage is the plugin's.</li>
 * <li><b>Vanguard</b> (zombie with a spear): tanky and brutal up close; warned lance charges (stunned 2s if cut short);
 * intercepts anyone who gets within 8 blocks of the Outrider.</li>
 * <li>When one falls, the other enrages: the Vanguard starts throwing spears, or the Outrider fires faster and closer.</li>
 * </ul>
 * With MythicMobs and BetterModel (Session 8 of the redesign) the four are separate bodies: the riders are
 * {@code OCCULTECH_DREAD_RIDERS_VANGUARD} / {@code _OUTRIDER} (a zombie lancer under a horned armet, a skeleton horse
 * archer under a steppe helm), each riding an invisible pig wearing its horse ({@code _VANGUARD_MOUNT}, a spiked zombie
 * charger; {@code _OUTRIDER_MOUNT}, a bone courser). Clips and glow tints are cosmetic Mythic skills; every hit stays
 * here, and lands on the clip's contact: the volley 8 ticks into its draw, the sweep at 7, the thrown spear at 11. The
 * snipe's line, the arrows and the spear leave the model's hands, not the carrier's eyes.
 */
public final class DreadRiders extends BossBehavior {

    private static final double OUTRIDER_HEALTH = 200;
    private static final double VANGUARD_HEALTH = 260;
    private static final double OUTRIDER_ARMOR = 0.1;
    private static final double VANGUARD_ARMOR = 0.05;
    private static final io.github.amitelia.occultech.boss.Mechanic SNIPE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Storm snipe", 34, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final io.github.amitelia.occultech.boss.Mechanic ARROW_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Arrow", 38, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic RAIN_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Arrow rain", 52, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic MELEE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Vanguard blade", 46, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic RAM_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Charge", 60, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic SPEAR_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DREAD_RIDERS", "Thrown spear", 40, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final double ORBIT = 14;
    private static final double ORBIT_ENRAGED = 8;
    private static final int CHARGE_WARNING = 20;
    private static final int CHARGE_TICKS = 25;
    private static final int STUN_TICKS = 40;
    /** Every 10s the Outrider reins in for 3s to take aim: a window to hit it (Session R3). */
    private static final int HALT_EVERY = 200;
    private static final int HALT_TICKS = 60;
    private static final Color STORM = Color.fromRGB(170, 200, 255);
    private static final Color LANCE = Color.fromRGB(120, 20, 20);
    // the clips' contacts (dread_s7.py), in ticks after the clip starts
    private static final int VOLLEY_CONTACT = 8;
    private static final int SWEEP_CONTACT = 7;
    private static final int THROW_CONTACT = 11;
    /** BetterModel's hit flash puts back the tint it found; re-tint after it (as on the coven). */
    private static final int RETINT = 12;
    private static final float HEAD_LIMIT = 55;
    private static final int DEAD = Color.fromRGB(44, 38, 40).asRGB();
    // where the model's hands are, in blocks from the rider's feet: (right, up, ahead), from dread_s2/s7 at 0.75 scale
    private static final double[] BOW_TIP = {-0.375, 1.27, 1.4};
    private static final double[] SPEAR_HAND = {0.66, 1.92, -0.23};

    private Skeleton outrider;
    private Zombie vanguard;
    private Mob outriderHorse;
    private Mob vanguardHorse;
    private Player outriderTarget;
    private Player vanguardTarget;
    private boolean outriderDown;
    private boolean vanguardDown;
    private double orbitAngle;
    private int haltUntil = -1;
    private final List<Abyss.Beam> snipes = new ArrayList<>();
    private int rainAt = -1;
    private Location rainSpot;
    private Vector chargeDirection;
    private int chargeAt = -1;
    private int chargeEnd = -1;
    private int stunnedUntil = -1;
    private int nextCharge = 120;
    private int nextMelee;
    private final Set<UUID> rammed = new HashSet<>();
    // per tick (move): the clips' contacts and the tints
    private int frame;
    private int volleyAt = -1;
    private int meleeAt = -1;
    private Player meleeTarget;
    private int spearAt = -1;
    private String vanguardState = "CALM";
    private String outriderState = "CALM";
    private String vanguardBase = "CALM";
    private String outriderBase = "CALM";
    private int vanguardCalmAt = -1;
    private int outriderCalmAt = -1;
    private int vanguardRetintAt = -1;
    private int outriderRetintAt = -1;
    private int lastFlinchV = -100;
    private int lastFlinchO = -100;

    public DreadRiders(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        Location west = at.clone().add(-4, 1, 0);
        Location east = at.clone().add(4, 1, 0);
        // with the models the horses' carriers are invisible pigs, which draw nothing under them
        boolean outriderModel = fight.usesMythicBody("OUTRIDER_MOUNT");
        boolean vanguardModel = fight.usesMythicBody("VANGUARD_MOUNT");
        Class<? extends Mob> outriderCarrier = outriderModel ? Pig.class : SkeletonHorse.class;
        Class<? extends Mob> vanguardCarrier = vanguardModel ? Pig.class : ZombieHorse.class;
        outriderHorse = fight.spawnLookalike("OUTRIDER_MOUNT", outriderCarrier, west, h -> {
            mount(h, !outriderModel);
            if (!outriderModel) {
                BossFight.setAttribute(h, Attribute.SCALE, 0.85);   // a smaller horse: its rider is easier to reach
            }
        });
        vanguardHorse = fight.spawnLookalike("VANGUARD_MOUNT", vanguardCarrier, east, h -> mount(h, !vanguardModel));
        boolean outriderBody = fight.usesMythicBody("OUTRIDER");
        boolean vanguardBody = fight.usesMythicBody("VANGUARD");
        outrider = fight.spawnBoss("OUTRIDER", Skeleton.class, west, s -> {
            s.setCustomName(ChatColor.AQUA + "The Outrider");
            s.setCustomNameVisible(true);
            Abyss.puppet(s);
            s.setGravity(true);
            s.setShouldBurnInDay(false);
            if (!outriderBody) {
                s.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
                s.getEquipment().setHelmet(new ItemStack(Material.CHAINMAIL_HELMET));
            }
            BossFight.setAttribute(s, Attribute.MAX_HEALTH, OUTRIDER_HEALTH);
        });
        vanguard = fight.spawnBoss("VANGUARD", Zombie.class, east, z -> {
            z.setCustomName(ChatColor.DARK_RED + "The Vanguard");
            z.setCustomNameVisible(true);
            Abyss.puppet(z);
            z.setGravity(true);
            z.setAdult();
            z.setShouldBurnInDay(false);
            if (!vanguardBody) {
                z.getEquipment().setItemInMainHand(new ItemStack(Material.NETHERITE_SPEAR));
                z.getEquipment().setHelmet(new ItemStack(Material.NETHERITE_HELMET));
                z.getEquipment().setChestplate(new ItemStack(Material.NETHERITE_CHESTPLATE));
                BossFight.setAttribute(z, Attribute.SCALE, 1.2);
            }
            BossFight.setAttribute(z, Attribute.MAX_HEALTH, VANGUARD_HEALTH);
        });
        if (outriderHorse != null) {
            outriderHorse.addPassenger(outrider);
        }
        if (vanguardHorse != null) {
            vanguardHorse.addPassenger(vanguard);
        }
        both(true, "SPAWN");
        both(false, "SPAWN");
    }

    private static void mount(Mob horse, boolean vanillaLook) {
        Abyss.puppet(horse);
        horse.setGravity(true);
        horse.setInvulnerable(true);
        horse.setRemoveWhenFarAway(false);
        Keys.setUnhittable(horse, true);
        if (horse instanceof AbstractHorse h) {
            h.setTamed(true);
        }
        if (vanillaLook) {
            BossFight.setAttribute(horse, Attribute.SCALE, 1.2);
        }
    }

    // ------------------------------------------------------------------ the bodies' clips and tints (cosmetic)

    private void play(@Nullable LivingEntity entity, String part, String action) {
        if (entity != null && entity.isValid() && fight.usesMythicBody(part)) {
            fight.playAction(entity, part + "_" + action);
        }
    }

    /** A clip on a rider and its horse together (the same name on both models). */
    private void both(boolean vanguardPair, String action) {
        if (vanguardPair) {
            play(vanguard, "VANGUARD", action);
            play(vanguardHorse, "VANGUARD_MOUNT", action);
        } else {
            play(outrider, "OUTRIDER", action);
            play(outriderHorse, "OUTRIDER_MOUNT", action);
        }
    }

    private void tint(boolean vanguardPair, String state) {
        if (vanguardPair) {
            vanguardState = state;
        } else {
            outriderState = state;
        }
        both(vanguardPair, "STATE_" + state);
    }

    /** A point on the rider's model, (right, up, ahead) blocks from its feet, turned with the horse's facing. */
    private static Location modelPoint(LivingEntity rider, @Nullable LivingEntity horse, double[] offset) {
        float yaw = (horse != null ? horse : rider).getBodyYaw();
        double r = Math.toRadians(yaw);
        Vector ahead = new Vector(-Math.sin(r), 0, Math.cos(r));
        Vector right = new Vector(-Math.cos(r), 0, -Math.sin(r));
        return rider.getLocation().add(right.multiply(offset[0])).add(0, offset[1], 0).add(ahead.multiply(offset[2]));
    }

    private Location bowTip() {
        return fight.usesMythicBody("OUTRIDER") ? modelPoint(outrider, outriderHorse, BOW_TIP) : outrider.getEyeLocation();
    }

    /** The rider's body keeps its horse's yaw (or it would spin in the saddle); only its head follows the target. */
    private static void keepInSaddle(LivingEntity rider, @Nullable LivingEntity horse, @Nullable Player target) {
        if (horse == null || !horse.isValid() || !rider.isValid()) {
            return;
        }
        float yaw = horse.getBodyYaw();
        float headYaw = yaw;
        float pitch = 0;
        if (target != null && target.isValid() && target.getWorld() == rider.getWorld()) {
            Location look = rider.getEyeLocation().setDirection(target.getEyeLocation().toVector().subtract(rider.getEyeLocation().toVector()));
            float delta = ((look.getYaw() - yaw) % 360 + 540) % 360 - 180;
            headYaw = yaw + Math.max(-HEAD_LIMIT, Math.min(HEAD_LIMIT, delta));
            pitch = look.getPitch();
        }
        rider.setRotation(headYaw, pitch);
        rider.setBodyYaw(yaw);
    }

    private static void faceAlong(LivingEntity horse, Vector direction) {
        Location look = horse.getLocation().setDirection(direction);
        horse.setRotation(look.getYaw(), 0);
        horse.setBodyYaw(look.getYaw());
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * (boss == vanguard ? VANGUARD_ARMOR : OUTRIDER_ARMOR);
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    // ------------------------------------------------------------------ every tick: the horses ride

    @Override
    public void move() {
        frame++;
        int now = fight.elapsed();
        if (!outriderDown && outriderHorse != null && outriderHorse.isValid() && alive(outriderTarget) && now < haltUntil) {
            outriderHorse.setVelocity(new Vector(0, outriderHorse.getVelocity().getY(), 0));
            Abyss.face(outriderHorse, outriderTarget.getLocation());
        } else if (!outriderDown && outriderHorse != null && outriderHorse.isValid() && alive(outriderTarget)) {
            orbitAngle += 0.02;
            Location target = outriderTarget.getLocation();
            double radius = vanguardDown ? ORBIT_ENRAGED : ORBIT;
            double base = Math.atan2(outriderHorse.getLocation().getZ() - target.getZ(), outriderHorse.getLocation().getX() - target.getX());
            Location spot = target.clone().add(Math.cos(base + 0.35) * radius, 0, Math.sin(base + 0.35) * radius);
            Abyss.walk(outriderHorse, keepInside(spot), 0.34, 0);
        }
        if (!outriderDown && outrider.isValid()) {
            keepInSaddle(outrider, outriderHorse, outriderTarget);
        }
        if (!vanguardDown && vanguardHorse != null && vanguardHorse.isValid()) {
            if (now < stunnedUntil) {
                vanguardHorse.setVelocity(new Vector(0, vanguardHorse.getVelocity().getY(), 0));
            } else if (chargeAt >= 0) {
                vanguardHorse.setVelocity(new Vector(0, vanguardHorse.getVelocity().getY(), 0));
                faceAlong(vanguardHorse, chargeDirection);       // the rear faces down the lane it will charge
            } else if (chargeEnd >= 0) {
                charge(now);
                faceAlong(vanguardHorse, chargeDirection);
            } else if (alive(vanguardTarget)) {
                Abyss.walk(vanguardHorse, vanguardTarget.getLocation(), 0.3, 2);
            }
            keepInSaddle(vanguard, vanguardHorse, vanguardTarget);
        }
        contacts();
        tints();
    }

    /** The attacks land on their clips' contacts, a few ticks after the clip starts. */
    private void contacts() {
        if (volleyAt >= 0 && frame >= volleyAt) {
            volleyAt = -1;
            if (!outriderDown && outrider.isValid() && alive(outriderTarget)) {
                volley();
            }
        }
        if (meleeAt >= 0 && frame >= meleeAt) {
            meleeAt = -1;
            if (!vanguardDown && vanguard.isValid() && alive(meleeTarget)
                && meleeTarget.getLocation().distanceSquared(vanguard.getLocation()) <= 4.0 * 4.0) {
                vanguard.swingMainHand();
                fight.hit(meleeTarget, MELEE_DAMAGE, vanguard);
            }
        }
        if (spearAt >= 0 && frame >= spearAt) {
            spearAt = -1;
            if (!vanguardDown && vanguard.isValid() && vanguardTarget != null) {
                throwSpear();
            }
        }
    }

    private void tints() {
        if (vanguardCalmAt >= 0 && frame >= vanguardCalmAt) {
            vanguardCalmAt = -1;
            tint(true, vanguardBase);
        }
        if (outriderCalmAt >= 0 && frame >= outriderCalmAt) {
            outriderCalmAt = -1;
            tint(false, outriderBase);
        }
        if (vanguardRetintAt >= 0 && frame >= vanguardRetintAt) {
            vanguardRetintAt = -1;
            tint(true, vanguardState);
        }
        if (outriderRetintAt >= 0 && frame >= outriderRetintAt) {
            outriderRetintAt = -1;
            tint(false, outriderState);
        }
    }

    private Location keepInside(Location spot) {
        Location center = fight.center();
        Vector offset = spot.toVector().subtract(center.toVector()).setY(0);
        double max = fight.radius() - 3;
        if (offset.length() > max) {
            offset.normalize().multiply(max);
        }
        return center.clone().add(offset);
    }

    // ------------------------------------------------------------------ every step: decisions

    @Override
    public void tick() {
        int now = fight.elapsed();
        checkDeaths();
        remount(outrider, outriderHorse, outriderDown);
        remount(vanguard, vanguardHorse, vanguardDown);

        if (!outriderDown) {
            if (!alive(outriderTarget) || every(160)) {
                outriderTarget = fight.randomPlayer();
            }
            if (every(HALT_EVERY)) {
                haltUntil = now + HALT_TICKS;
                outrider.getWorld().playSound(outrider.getLocation(), Sound.ENTITY_SKELETON_HORSE_AMBIENT, 1.5F, 0.7F);
                if (alive(outriderTarget)) {
                    snipes.add(new Abyss.Beam(outrider, this::bowTip, outriderTarget, now, 40, SNIPE_DAMAGE, STORM));   // the aimed shot
                    play(outrider, "OUTRIDER", "DRAW");
                    play(outriderHorse, "OUTRIDER_MOUNT", "HALT");
                    tint(false, "LOCK");
                    outriderCalmAt = frame + 44;
                }
            }
            outriderAttacks(now);
        }
        if (!vanguardDown) {
            vanguardTarget = fight.nearestPlayer(vanguard.getLocation());
            vanguardAttacks(now);
        }
    }

    private void outriderAttacks(int now) {
        if (outriderTarget == null) {
            return;
        }
        int snipeEvery = vanguardDown ? 60 : 100;
        if (every(snipeEvery) && now >= haltUntil) {
            snipes.add(new Abyss.Beam(outrider, this::bowTip, outriderTarget, now, 30, SNIPE_DAMAGE, STORM));
            play(outrider, "OUTRIDER", "SNIPE");
        }
        for (Abyss.Beam snipe : snipes) {
            for (Player hit : snipe.step(fight, now)) {
                // visual lightning only: no fire, no transformed mobs - and a plasma bolt with it (Session O5)
                hit.getWorld().strikeLightningEffect(hit.getLocation());
                io.github.amitelia.occultech.boss.AirEffects.bolt(fight, hit.getLocation(), STORM);
            }
        }
        snipes.removeIf(Abyss.Beam::done);

        if (every(vanguardDown ? 30 : 60) && volleyAt < 0) {
            volleyAt = frame + VOLLEY_CONTACT;                    // the arrows leave the bow on the clip's loose
            play(outrider, "OUTRIDER", "VOLLEY");
        }

        if (every(240) && rainAt < 0) {
            Player victim = fight.randomPlayer();
            if (victim != null) {
                rainSpot = victim.getLocation();
                rainAt = now + 30;
                fight.telegraph(rainSpot, 3.5, 35, STORM, FloorDecals.Mark.STORM);
                outrider.getWorld().playSound(outrider.getLocation(), Sound.ITEM_CROSSBOW_LOADING_END, 2F, 0.6F);
                play(outrider, "OUTRIDER", "RAIN");
            }
        }
        if (rainAt >= 0 && now >= rainAt) {
            rainAt = -1;
            rainSpot.getWorld().strikeLightningEffect(rainSpot);
            io.github.amitelia.occultech.boss.AirEffects.bolt(fight, rainSpot, STORM);
            rainSpot.getWorld().spawnParticle(Particle.CRIT, rainSpot.clone().add(0, 2, 0), 80, 2, 2, 2, 0.4);
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(rainSpot) <= 3.5 * 3.5) {
                    fight.hit(player, RAIN_DAMAGE, outrider);
                }
            }
        }
    }

    /** Three arrows fanned at the target, from the bow. */
    private void volley() {
        Location from = bowTip();
        Vector aim = outriderTarget.getEyeLocation().toVector().subtract(from.toVector()).normalize();
        for (int i = -1; i <= 1; i++) {
            Vector v = aim.clone().rotateAroundY(Math.toRadians(8 * i));
            Arrow arrow = from.getWorld().spawnArrow(from, v, 2.4F, 0F);
            arrow.setShooter(outrider);
            arrow.setPickupStatus(AbstractArrow.PickupStatus.DISALLOWED);
            arrow.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, ARROW_DAMAGE.damage());
            fight.label(arrow, ARROW_DAMAGE);
        }
        from.getWorld().spawnParticle(Particle.ELECTRIC_SPARK, from, 10, 0.3, 0.3, 0.3, 0.1);
        from.getWorld().playSound(from, Sound.ENTITY_SKELETON_SHOOT, 1.5F, 0.7F);
    }

    private void throwSpear() {
        boolean model = fight.usesMythicBody("VANGUARD");
        Location from = model ? modelPoint(vanguard, vanguardHorse, SPEAR_HAND) : vanguard.getEyeLocation();
        Vector aim = vanguardTarget.getEyeLocation().toVector().subtract(from.toVector()).normalize();
        Trident spear;
        if (model) {
            spear = from.getWorld().spawn(from, Trident.class, t -> {
                t.setShooter(vanguard);
                t.setPickupStatus(AbstractArrow.PickupStatus.DISALLOWED);
            });
            spear.setVelocity(aim.multiply(2));
        } else {
            spear = vanguard.launchProjectile(Trident.class, aim.multiply(2));
        }
        spear.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, SPEAR_DAMAGE.damage());
        fight.label(spear, SPEAR_DAMAGE);
        vanguard.swingMainHand();
    }

    private void vanguardAttacks(int now) {
        if (now < stunnedUntil || chargeEnd >= 0) {
            if (now < stunnedUntil) {
                vanguard.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, vanguard.getLocation().add(0, 2.2, 0), 2, 0.3, 0.1, 0.3, 0);
            }
            return;
        }
        if (chargeAt >= 0) {
            if (now >= chargeAt) {
                chargeAt = -1;
                chargeEnd = now + CHARGE_TICKS;
                rammed.clear();
                vanguard.getWorld().playSound(vanguard.getLocation(), Sound.ENTITY_ZOMBIE_HORSE_ANGRY, 2F, 0.6F);
                both(true, "CHARGE");
            }
            return;
        }
        if (vanguardTarget != null && now >= nextMelee && meleeAt < 0
            && vanguardTarget.getLocation().distanceSquared(vanguard.getLocation()) <= 3.5 * 3.5) {
            nextMelee = now + 20;
            meleeAt = frame + SWEEP_CONTACT;                       // the lance lands on the sweep's contact
            meleeTarget = vanguardTarget;
            play(vanguard, "VANGUARD", "SWEEP");
        }
        // intercept: anyone closing in on the Outrider gets charged
        Player intercept = null;
        if (!outriderDown) {
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(outrider.getLocation()) <= 64) {
                    intercept = player;
                    break;
                }
            }
        }
        if (intercept != null && now >= nextCharge - 100) {
            startCharge(now, intercept, "&4The Vanguard intercepts!");
        } else if (now >= nextCharge) {
            Player victim = fight.randomPlayer();
            if (victim != null) {
                startCharge(now, victim, null);
            }
        }
        if (outriderDown && every(80) && vanguardTarget != null && spearAt < 0) {
            spearAt = frame + THROW_CONTACT;                       // the spear leaves the hand on the throw's contact
            play(vanguard, "VANGUARD", "THROW");
        }
    }

    private void startCharge(int now, Player victim, String message) {
        Location from0 = vanguardHorse != null ? vanguardHorse.getLocation() : vanguard.getLocation();
        chargeDirection = victim.getLocation().toVector().subtract(from0.toVector()).setY(0);
        if (chargeDirection.lengthSquared() < 1) {
            chargeDirection = new Vector(1, 0, 0);
        }
        chargeDirection.normalize();
        chargeAt = now + CHARGE_WARNING;
        nextCharge = now + 180;
        Location from = from0.clone().add(0, 0.2, 0);
        Particle.DustOptions dust = new Particle.DustOptions(LANCE, 1.6F);
        if (FloorDecals.enabled()) {
            FloorDecals.lane(fight, from0, chargeDirection, 18, 3, CHARGE_WARNING, LANCE);
        }
        for (double d = 0; d < 18 && !FloorDecals.enabled(); d += 0.5) {
            from.getWorld().spawnParticle(Particle.DUST, from.clone().add(chargeDirection.clone().multiply(d)), 1, 0.3, 0, 0.3, 0, dust);
        }
        both(true, "REAR");                                         // the 1 s warning: the horse rears
        tint(true, "TELL");
        if (message != null) {
            fight.broadcast(message);
        }
    }

    /** One tick of the lance charge. */
    private void charge(int now) {
        Location at = vanguardHorse.getLocation();
        boolean blocked = !at.clone().add(chargeDirection.clone().multiply(1.5)).add(0, 0.5, 0).getBlock().isPassable();
        boolean outside = at.distanceSquared(fight.center()) > fight.radius() * fight.radius();
        if (now >= chargeEnd || blocked || outside) {
            chargeEnd = -1;
            vanguardHorse.setVelocity(new Vector());
            if (blocked || outside) {
                stunnedUntil = now + STUN_TICKS;
                fight.broadcast("&4The Vanguard stumbles - &fstrike now!");
                both(true, "STUNNED");
                tint(true, "STUNNED");
                vanguardCalmAt = frame + STUN_TICKS;
            } else {
                tint(true, vanguardBase);
            }
            return;
        }
        vanguardHorse.setVelocity(chargeDirection.clone().multiply(0.8).setY(vanguardHorse.getVelocity().getY()));
        for (Player player : fight.players()) {
            if (!rammed.contains(player.getUniqueId()) && player.getLocation().distanceSquared(at) <= 5) {
                rammed.add(player.getUniqueId());
                fight.hit(player, RAM_DAMAGE, vanguard);
                player.setVelocity(chargeDirection.clone().multiply(1.2).setY(0.5));
            }
        }
    }

    // ------------------------------------------------------------------ hits and deaths

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        int now = fight.elapsed();
        if (boss == vanguard) {
            vanguardRetintAt = frame + RETINT;
            if (frame - lastFlinchV > 12 && chargeAt < 0 && chargeEnd < 0 && now >= stunnedUntil && meleeAt < 0 && spearAt < 0) {
                lastFlinchV = frame;
                both(true, "FLINCH");
            }
        } else if (boss == outrider) {
            outriderRetintAt = frame + RETINT;
            if (frame - lastFlinchO > 12 && now >= haltUntil && volleyAt < 0) {
                lastFlinchO = frame;
                both(false, "FLINCH");
            }
        }
    }

    /** The dying rider and its horse play their death clip on stand-ins, their glows out; the horse goes with it. */
    @Override
    public void onBossDeath(LivingEntity boss) {
        Prop rider = fight.corpse(boss);
        if (rider != null) {
            rider.tint(DEAD, "lance", "arrow", "rune");
        }
        Mob horse = boss == vanguard ? vanguardHorse : boss == outrider ? outriderHorse : null;
        if (horse != null && horse.isValid()) {
            Prop body = fight.corpse(horse);
            if (body != null) {
                body.tint(DEAD, "eyes", "sigil", "banner");
            }
            dismissHorse(horse);
        }
    }

    private void checkDeaths() {
        if (!outriderDown && (!outrider.isValid() || outrider.isDead())) {
            outriderDown = true;
            dismissHorse(outriderHorse);
            if (!vanguardDown) {
                fight.broadcast("&4The Outrider falls - &fthe Vanguard takes up spears in its rage!");
                vanguardBase = "ENRAGED";                           // the survivor takes the fallen one's colour
                tint(true, "ENRAGED");
            }
        }
        if (!vanguardDown && (!vanguard.isValid() || vanguard.isDead())) {
            vanguardDown = true;
            dismissHorse(vanguardHorse);
            if (!outriderDown) {
                fight.broadcast("&bThe Vanguard falls - &fthe Outrider rides closer and shoots faster!");
                outriderBase = "ENRAGED";
                tint(false, "ENRAGED");
            }
        }
    }

    private static void dismissHorse(@Nullable LivingEntity horse) {
        if (horse != null && horse.isValid()) {
            horse.getWorld().spawnParticle(Particle.SOUL, horse.getLocation().add(0, 1, 0), 30, 0.5, 0.6, 0.5, 0.03);
            horse.remove();
        }
    }

    /** The engine may teleport a rider (leash), which dismounts it: bring the horse along. */
    private static void remount(LivingEntity rider, @Nullable LivingEntity horse, boolean down) {
        if (down || horse == null || !rider.isValid() || !horse.isValid() || horse.getPassengers().contains(rider)) {
            return;
        }
        horse.teleport(rider.getLocation());
        horse.addPassenger(rider);
    }

    private static boolean alive(Player player) {
        return player != null && player.isValid() && !player.isDead();
    }
}
