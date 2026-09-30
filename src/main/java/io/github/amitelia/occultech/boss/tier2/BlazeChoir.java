package io.github.amitelia.occultech.boss.tier2;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Blaze;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.SmallFireball;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-2 mini-boss (max netherite). Three blazes circle the altar, singing.
 * <ul>
 * <li>The shield passes from singer to singer every 6s: the shielded one (glowing, ringed by flames) takes 90% less
 * damage. Hit the others.</li>
 * <li>Each fires custom fireballs at players; they burn players but never light blocks.</li>
 * <li>Chorus: flame circles appear under players and erupt after 1.5s.</li>
 * <li>Each time a singer falls, the others sing faster.</li>
 * </ul>
 * Each blaze takes a third of the damage dealt.
 */
public final class BlazeChoir extends BossBehavior {

    private static final double HEALTH = 110;
    private static final double ARMOR = 0.33;
    private static final double SHIELD = 0.1;
    private static final double ORBIT_RADIUS = 5;
    private static final int SHIELD_INTERVAL = 120;
    private static final int CHORUS_INTERVAL = 300;
    private static final int CHORUS_WARNING = 30;
    private static final double FIREBALL_DAMAGE = 20;
    private static final double CHORUS_DAMAGE = 32;
    private static final Color FLAME = Color.fromRGB(255, 120, 30);
    private static final String[] NAMES = { "Soprano", "Alto", "Bass" };

    private final List<Blaze> singers = new ArrayList<>();
    private final List<Location> chorus = new ArrayList<>();
    private Blaze shielded;
    private int chorusAt = -1;
    private double spin;

    public BlazeChoir(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        for (int i = 0; i < 3; i++) {
            String name = NAMES[i];
            double angle = Math.PI * 2 * i / 3;
            Blaze blaze = fight.spawnBoss(Blaze.class, at.clone().add(Math.cos(angle) * ORBIT_RADIUS, 2.5, Math.sin(angle) * ORBIT_RADIUS), b -> {
                b.setCustomName(ChatColor.GOLD + "Blaze Choir " + ChatColor.GRAY + "(" + name + ")");
                b.setCustomNameVisible(true);
                Abyss.puppet(b);
                BossFight.setAttribute(b, Attribute.MAX_HEALTH, HEALTH);
                BossFight.setAttribute(b, Attribute.SCALE, 1.5);
            });
            singers.add(blaze);
        }
        passShield();
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage * ARMOR * (boss == shielded ? SHIELD : 1);
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public double verticalLeash() {
        return 12;
    }

    @Override
    public void tick() {
        singers.removeIf(blaze -> {
            if (blaze.isValid() && !blaze.isDead()) {
                return false;
            }
            fight.broadcast("&6A voice falls silent - &fthe others sing faster!");
            return true;
        });
        if (singers.isEmpty()) {
            return;
        }
        int now = fight.elapsed();
        int fallen = 3 - singers.size();

        spin += 0.08 + 0.03 * fallen;
        for (int i = 0; i < singers.size(); i++) {
            Blaze blaze = singers.get(i);
            double angle = spin + Math.PI * 2 * i / singers.size();
            Location spot = fight.center().clone().add(Math.cos(angle) * ORBIT_RADIUS, 2.5 + Math.sin(spin * 2 + i) * 0.5, Math.sin(angle) * ORBIT_RADIUS);
            blaze.setVelocity(spot.toVector().subtract(blaze.getLocation().toVector()).multiply(0.25));
            Player target = fight.nearestPlayer(blaze.getLocation());
            if (target != null) {
                Abyss.face(blaze, target.getEyeLocation());
            }
        }

        if (every(SHIELD_INTERVAL) || shielded == null || !singers.contains(shielded)) {
            passShield();
        }
        drawShield();

        // fireballs: each singer on its own beat, faster as the choir shrinks
        int beat = Math.max(20, 60 - 15 * fallen);
        for (int i = 0; i < singers.size(); i++) {
            if ((now + i * 20) % beat == 0) {
                Player target = fight.randomPlayer();
                if (target != null) {
                    fireball(singers.get(i), target);
                }
            }
        }

        if (every(CHORUS_INTERVAL) && chorusAt < 0) {
            chorus.clear();
            for (Player player : fight.players()) {
                chorus.add(player.getLocation());
                fight.telegraph(player.getLocation(), 2.5, CHORUS_WARNING + 5, FLAME);
            }
            chorusAt = now + CHORUS_WARNING;
            fight.center().getWorld().playSound(fight.center(), Sound.ENTITY_BLAZE_AMBIENT, 2F, 0.5F);
        }
        if (chorusAt >= 0 && now >= chorusAt) {
            chorusAt = -1;
            erupt();
        }
    }

    private void passShield() {
        if (singers.isEmpty()) {
            shielded = null;
            return;
        }
        int next = shielded == null ? 0 : (singers.indexOf(shielded) + 1) % singers.size();
        if (shielded != null) {
            shielded.setGlowing(false);
        }
        shielded = singers.get(Math.max(0, next));
        shielded.setGlowing(true);
        shielded.getWorld().playSound(shielded.getLocation(), Sound.BLOCK_BEACON_ACTIVATE, 1F, 1.6F);
    }

    private void drawShield() {
        if (shielded == null) {
            return;
        }
        Location at = shielded.getLocation().add(0, 1, 0);
        for (int i = 0; i < 8; i++) {
            double angle = spin * 3 + Math.PI * 2 * i / 8;
            at.getWorld().spawnParticle(Particle.FLAME, at.clone().add(Math.cos(angle) * 1.2, 0, Math.sin(angle) * 1.2), 1, 0, 0, 0, 0);
        }
    }

    private void fireball(Blaze blaze, Player target) {
        Vector aim = target.getEyeLocation().toVector().subtract(blaze.getEyeLocation().toVector()).normalize();
        SmallFireball fireball = blaze.launchProjectile(SmallFireball.class, aim.multiply(0.9));
        fireball.setIsIncendiary(false);
        fireball.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, FIREBALL_DAMAGE);
        blaze.getWorld().playSound(blaze.getLocation(), Sound.ENTITY_BLAZE_SHOOT, 1F, 1.2F);
    }

    private void erupt() {
        for (Location at : chorus) {
            at.getWorld().spawnParticle(Particle.FLAME, at.clone().add(0, 0.5, 0), 60, 1.2, 1, 1.2, 0.05);
            at.getWorld().spawnParticle(Particle.LAVA, at, 8, 1, 0.2, 1, 0);
            at.getWorld().playSound(at, Sound.ITEM_FIRECHARGE_USE, 1.5F, 0.7F);
            LivingEntity source = singers.isEmpty() ? null : singers.get(0);
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(at) <= 6.25) {
                    player.damage(CHORUS_DAMAGE, source);
                    player.setFireTicks(Math.max(player.getFireTicks(), 60));
                }
            }
        }
        chorus.clear();
    }
}
