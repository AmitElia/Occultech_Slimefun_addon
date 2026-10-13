package io.github.amitelia.occultech.boss.tier1;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Husk;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.Vindicator;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 mini-boss (diamond gear, solo 2-4 min). A berserk vindicator ("Johnny") that broke out of a ritual binding:
 * bull horns, a red band over his eyes with one cyan eye burning through, restraints and chains, a burning chest piece,
 * the Frenzy Cleaver dragged behind him.
 * <ul>
 * <li>Speeds up as it loses health; the fire in his chest grows with him (embers, burning, inferno).</li>
 * <li>Cleave: a red wedge marks the area in front of it for 1.25s while he winds the cleaver up over his shoulder, then
 * the sweep hits everything inside. The wedge's origin and facing are locked when it appears and he holds still
 * through the wind-up, so the hit lands exactly where the warning showed.</li>
 * <li>Thralls: every 14s husk thralls rise to his roar. He attacks thralls near him; when he kills one himself he
 * devours it and is <b>sated</b> for 3s - down on one knee and taking 50% more damage. Bait him into his thralls.
 * Thralls the cleave cuts down, or anything else kills, don't count.</li>
 * </ul>
 * The look comes from the Mythic body (Mobs/Skills TheUnbound.yml, model occultech_the_unbound): its clips are
 * started early enough to land on the server's moments (the cleave's sweep reaches contact 1.3s in, the warning is
 * 1.25s). Without Mythic the fight plays as before, with vanilla particles and sounds.
 */
public final class TheUnbound extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic SWING = io.github.amitelia.occultech.boss.Mechanic.of("THE_UNBOUND", "Axe swing", 16, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic CLEAVE = io.github.amitelia.occultech.boss.Mechanic.of("THE_UNBOUND", "Cleave", 22, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final io.github.amitelia.occultech.boss.Mechanic THRALL = io.github.amitelia.occultech.boss.Mechanic.of("THE_UNBOUND", "Thrall", 9, io.github.amitelia.occultech.boss.Mechanic.Kind.ADD, false);

    private static final Particle.DustOptions WEDGE = new Particle.DustOptions(Color.fromRGB(220, 30, 30), 1.3F);
    private static final int CLEAVE_INTERVAL = 160;
    private static final int CLEAVE_WARNING = 25;
    private static final int THRALL_INTERVAL = 280;
    /** The thralls rise at the top of his roar (the call clip roars 0.9s in). */
    private static final int CALL_LEAD = 18;
    private static final int SATED_TICKS = 60;
    private static final double BASE_SPEED = 0.30;
    /** At most one axe swing every 1.2s: vanilla's pace (one a second) was too fast for most players, 1.5s too easy for groups. */
    private static final int SWING_COOLDOWN = 24;
    private static final double CLEAVE_RANGE = 4.5;

    /** The fire's stages: above 2/3 health, below 2/3, below 1/3 (enraged). */
    private enum Stage { EMBERS, BURNING, INFERNO }

    private final List<Husk> thralls = new ArrayList<>();
    /** Thralls the cleave cut: their deaths are not a devour. */
    private final Set<Entity> cleaved = new HashSet<>();
    /** Thralls he has already lunged at (the devour clip plays once per thrall). */
    private final Set<Entity> lunged = new HashSet<>();
    private Vindicator unbound;
    private Location cleaveOrigin;
    private Vector cleaveDirection;
    private int cleaveAt = -1;
    private int thrallsAt = -1;
    private int satedUntil = -1;
    private Stage stage = Stage.EMBERS;

    public TheUnbound(BossFight fight) {
        super(fight);
    }

    @Override
    public int meleeCooldownTicks() {
        return SWING_COOLDOWN;
    }

    @Override
    public void spawn(Location at) {
        unbound = fight.spawnBoss(Vindicator.class, at, v -> {
            v.setJohnny(true);
            v.setCustomName(ChatColor.RED + "The Unbound");
            v.setCustomNameVisible(true);
            BossFight.setAttribute(v, Attribute.MAX_HEALTH, 320);
            fight.label(v, SWING);
            BossFight.setAttribute(v, Attribute.MOVEMENT_SPEED, BASE_SPEED);
            BossFight.setAttribute(v, Attribute.KNOCKBACK_RESISTANCE, 0.5);
            BossFight.setAttribute(v, Attribute.FOLLOW_RANGE, 32);
        });
        if (mythic()) {
            // the model draws him and his cleaver: the invisible carrier holds nothing, and stays unscaled under it
            unbound.getEquipment().setItemInMainHand(new ItemStack(Material.AIR));
            act("STAGE_EMBERS", null);
        } else {
            unbound.getEquipment().setItemInMainHand(new ItemStack(Material.IRON_AXE));
            BossFight.setAttribute(unbound, Attribute.SCALE, 1.3);
        }
    }

    private boolean mythic() {
        return fight.usesMythicBody();
    }

    private void act(String action, @Nullable Entity target) {
        if (mythic()) {
            fight.playAction(unbound, action, target);
        }
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return isSated() ? damage * 1.5 : damage;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (!isSated() && cleaveAt < 0) {
            act("FLINCH", null);
        }
    }

    /** Holds him still and facing the locked wedge through the cleave's wind-up (every tick). */
    @Override
    public void move() {
        if (unbound == null || !unbound.isValid() || cleaveAt < 0 || cleaveOrigin == null) {
            return;
        }
        Location hold = cleaveOrigin.clone();
        hold.setDirection(cleaveDirection);
        unbound.teleport(hold);
        unbound.setVelocity(new Vector(0, unbound.getVelocity().getY(), 0));
    }

    @Override
    public void tick() {
        if (!unbound.isValid()) {
            return;
        }
        int now = fight.elapsed();
        thralls.removeIf(t -> t.isDead() || !t.isValid());

        // stunned while sated
        boolean sated = isSated();
        unbound.setAI(!sated && cleaveAt < 0);
        if (sated) {
            if (!mythic()) {
                unbound.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, unbound.getLocation().add(0, 2.4, 0), 2, 0.3, 0.2, 0.3, 0);
            }
            return;
        }
        if (satedUntil >= 0 && now >= satedUntil) {
            satedUntil = -1;
            act("STAGE_" + stage.name(), null);              // the fire comes back up from the coals
        }

        // enrage: up to 30% faster at low health, and the fire grows with him
        BossFight.setAttribute(unbound, Attribute.MOVEMENT_SPEED, BASE_SPEED * (1 + 0.2 * (1 - fight.healthFraction())));
        Stage now_ = fight.healthFraction() < 1 / 3.0 ? Stage.INFERNO : fight.healthFraction() < 2 / 3.0 ? Stage.BURNING : Stage.EMBERS;
        if (now_.ordinal() > stage.ordinal()) {
            stage = now_;
            act("ENRAGE_" + stage.name(), null);
        }
        embers();

        if (every(THRALL_INTERVAL)) {
            act("CALL", null);
            thrallsAt = now + CALL_LEAD;
        }
        if (thrallsAt >= 0 && now >= thrallsAt) {
            thrallsAt = -1;
            // 2 thralls, one more per extra player (up to 4): a group gets more to bait it with, and more to deal with
            for (int i = 0; i < Math.min(4, 1 + fight.playersAtStart()); i++) {
                Husk thrall = fight.spawnAdd(Husk.class, fight.randomPoint(5, fight.radius() - 2), h -> {
                    h.setCustomName(ChatColor.GRAY + "Unbound Thrall");
                    BossFight.setAttribute(h, Attribute.MAX_HEALTH, 30);
                    h.setHealth(30);
                    fight.label(h, THRALL);
                });
                if (thrall != null) {
                    thralls.add(thrall);
                }
            }
            fight.broadcast("&7Thralls rise. &fLure the Unbound into them!");
        }

        // it can't resist a thrall within reach
        for (Husk thrall : thralls) {
            if (thrall.getLocation().distanceSquared(unbound.getLocation()) < 9) {
                unbound.setTarget(thrall);
                if (lunged.add(thrall)) {
                    act("DEVOUR", thrall);
                }
                break;
            }
        }

        if (cleaveAt < 0 && every(CLEAVE_INTERVAL)) {
            Player target = fight.nearestPlayer(unbound.getLocation());
            if (target != null) {
                // the wedge's origin and facing are locked now, and he holds them through the wind-up
                cleaveOrigin = unbound.getLocation();
                cleaveDirection = target.getLocation().toVector().subtract(cleaveOrigin.toVector()).setY(0);
                if (cleaveDirection.lengthSquared() < 0.01) {
                    cleaveDirection = cleaveOrigin.getDirection().setY(0);
                }
                cleaveDirection.normalize();
                cleaveAt = now + CLEAVE_WARNING;
                act("CLEAVE", target);
                unbound.getWorld().playSound(cleaveOrigin, Sound.ENTITY_VINDICATOR_CELEBRATE, 1.5F, 0.6F);
                FloorDecals.wedge(fight, cleaveOrigin, cleaveDirection, CLEAVE_RANGE, CLEAVE_WARNING, WEDGE.getColor());
            }
        }
        if (cleaveAt > now && cleaveDirection != null && !FloorDecals.enabled()) {
            drawWedge();
        }
        if (cleaveAt >= 0 && now >= cleaveAt) {
            cleaveAt = -1;
            cleave();
        }
    }

    /** Embers streaming off his chest, more at each stage. */
    private void embers() {
        Vector facing = unbound.getLocation().getDirection().setY(0);
        if (facing.lengthSquared() < 1e-4) {
            facing = new Vector(0, 0, 1);
        }
        Location chest = unbound.getLocation().add(facing.normalize().multiply(0.6)).add(0, 2.0, 0);
        int count = stage == Stage.EMBERS ? 1 : stage == Stage.BURNING ? 3 : 6;
        unbound.getWorld().spawnParticle(Particle.SMALL_FLAME, chest, count, 0.25, 0.2, 0.25, 0.01);
        if (stage != Stage.EMBERS) {
            unbound.getWorld().spawnParticle(Particle.LAVA, chest, stage == Stage.INFERNO ? 2 : 1, 0.2, 0.1, 0.2, 0);
        }
    }

    @Override
    public void onAddDeath(Entity entity, @Nullable Player killer) {
        if (!thralls.contains(entity) || cleaved.remove(entity)) {
            return;
        }
        // only a thrall he killed himself, with his own blow, is devoured (not a fall, a fire, or a player's kill)
        EntityDamageEvent last = entity.getLastDamageCause();
        if (killer == null && last instanceof EntityDamageByEntityEvent byEntity && byEntity.getDamager().equals(unbound)) {
            satedUntil = fight.elapsed() + SATED_TICKS;
            cleaveAt = -1;                                   // sated: an unfinished cleave never lands
            act("SATED", null);
            unbound.getWorld().playSound(unbound.getLocation(), Sound.ENTITY_PLAYER_BURP, 2F, 0.5F);
            fight.broadcast("&7The Unbound gorges on its thrall - &fstrike now!");
        }
    }

    @Override
    public void onBossDeath(LivingEntity boss) {
        io.github.amitelia.occultech.boss.Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(Color.fromRGB(52, 40, 38).asRGB(), "chest");           // the fire goes out
        }
    }

    private boolean isSated() {
        return fight.elapsed() < satedUntil;
    }

    private void drawWedge() {
        Location origin = cleaveOrigin.clone().add(0, 0.2, 0);
        for (double distance = 1; distance <= CLEAVE_RANGE; distance += 0.7) {
            for (double angle = -45; angle <= 45; angle += 15) {
                Vector v = cleaveDirection.clone().rotateAroundY(Math.toRadians(angle)).multiply(distance);
                origin.getWorld().spawnParticle(Particle.DUST, origin.clone().add(v), 1, 0, 0, 0, 0, WEDGE);
            }
        }
    }

    private void cleave() {
        Location origin = cleaveOrigin;
        origin.getWorld().playSound(origin, Sound.ENTITY_PLAYER_ATTACK_SWEEP, 2F, 0.6F);
        origin.getWorld().spawnParticle(Particle.SWEEP_ATTACK, origin.clone().add(cleaveDirection.clone().multiply(2)).add(0, 1, 0), 6, 1, 0.3, 1, 0);
        io.github.amitelia.occultech.boss.AirEffects.burst(fight, origin.clone().add(cleaveDirection.clone().multiply(2.2)).add(0, 1.2, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.SLASH,
            WEDGE.getColor(), 4.5F);
        List<LivingEntity> victims = new ArrayList<>(fight.players());
        victims.addAll(thralls);
        for (LivingEntity victim : victims) {
            Vector to = victim.getLocation().toVector().subtract(origin.toVector()).setY(0);
            if (to.length() <= CLEAVE_RANGE && to.lengthSquared() > 0.01 && Math.toDegrees(to.angle(cleaveDirection)) <= 45) {
                if (victim instanceof Player) {
                    fight.hit(victim, CLEAVE, unbound);
                } else {
                    cleaved.add(victim);                    // cut down, not devoured
                    victim.damage(40, unbound);
                }
                victim.setVelocity(to.normalize().multiply(0.8).setY(0.35));
            }
        }
        cleaveOrigin = null;
    }
}
