package io.github.amitelia.occultech.boss.tier0;

import java.util.ArrayList;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.entity.Slime;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-0 gate boss (iron gear, 4-6 minutes). A huge slime in three phases.
 * <ul>
 * <li>Phase 1: every 8s marks a player's spot with a lime ring (1.5s), leaps onto it and sends out a shockwave that
 * only hurts players standing on the ground - jump to dodge.</li>
 * <li>Phase 2 (66%): splits off shards that crawl back to the altar; each one that arrives heals the Sovereign by 10%.</li>
 * <li>Phase 3 (33%): shrinks and speeds up, leaving acid puddles that hurt anyone standing in them.</li>
 * </ul>
 */
public final class GelatinousSovereign extends BossBehavior {

    private static final Color LIME = Color.fromRGB(120, 230, 60);
    private static final Color ACID = Color.fromRGB(160, 255, 40);
    private static final int SLAM_INTERVAL = 160;
    private static final int SLAM_WARNING = 30;
    private static final int PUDDLE_INTERVAL = 100;
    private static final double BASE_HEALTH = 600;

    private final List<Slime> shards = new ArrayList<>();
    private Slime sovereign;
    private Location slamTarget;
    private int leapAt = -1;
    private int landingCheckUntil = -1;
    private boolean airborne;
    private boolean split;
    private boolean enraged;

    public GelatinousSovereign(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        sovereign = fight.spawnBoss(Slime.class, at, s -> {
            s.setSize(7);
            s.setCustomName(ChatColor.GREEN + "Gelatinous Sovereign");
            s.setCustomNameVisible(true);
            BossFight.setAttribute(s, Attribute.MAX_HEALTH, BASE_HEALTH);
            BossFight.setAttribute(s, Attribute.ATTACK_DAMAGE, 7);
            BossFight.setAttribute(s, Attribute.KNOCKBACK_RESISTANCE, 0.8);
            BossFight.setAttribute(s, Attribute.FOLLOW_RANGE, 32);
            s.setHealth(BASE_HEALTH);
        });
    }

    @Override
    public void tick() {
        if (!sovereign.isValid()) {
            return;
        }
        int now = fight.elapsed();
        double health = fight.healthFraction();

        if (!split && health <= 0.66) {
            split = true;
            splitShards();
        }
        if (!enraged && health <= 0.33) {
            enraged = true;
            enrage();
        }

        slam(now);
        tendShards();

        if (enraged && every(PUDDLE_INTERVAL)) {
            Location at = sovereign.getLocation();
            fight.addHazard(at, 2.5, 200, ACID, player -> player.damage(2, sovereign));
            at.getWorld().playSound(at, Sound.BLOCK_SLIME_BLOCK_FALL, 1F, 0.6F);
        }
    }

    private void slam(int now) {
        if (every(SLAM_INTERVAL)) {
            Player target = fight.randomPlayer();
            if (target != null) {
                slamTarget = target.getLocation();
                leapAt = now + SLAM_WARNING;
                fight.telegraph(slamTarget, 3.5, SLAM_WARNING + 10, LIME);
                sovereign.getWorld().playSound(sovereign.getLocation(), Sound.ENTITY_SLIME_SQUISH, 2F, 0.5F);
            }
        }
        if (now == leapAt && slamTarget != null) {
            Vector jump = slamTarget.toVector().subtract(sovereign.getLocation().toVector()).setY(0).multiply(0.12);
            sovereign.setVelocity(jump.setY(0.95));
            airborne = true;
            landingCheckUntil = now + 60;
        }
        if (airborne && now > leapAt + 5 && (sovereign.isOnGround() || now >= landingCheckUntil)) {
            airborne = false;
            shockwave();
        }
    }

    private void shockwave() {
        Location at = sovereign.getLocation();
        at.getWorld().playSound(at, Sound.ENTITY_GENERIC_EXPLODE, 0.8F, 0.6F);
        at.getWorld().spawnParticle(Particle.BLOCK, at, 60, 2.5, 0.2, 2.5, Material.SLIME_BLOCK.createBlockData());
        for (Player player : fight.players()) {
            if (player.getLocation().distanceSquared(at) <= 16 && player.isOnGround()) {
                player.damage(6, sovereign);
                Vector push = player.getLocation().toVector().subtract(at.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    player.setVelocity(push.normalize().multiply(0.9).setY(0.4));
                }
            }
        }
    }

    private void splitShards() {
        int count = 2 + fight.playersAtStart();
        for (int i = 0; i < count; i++) {
            double angle = Math.PI * 2 * i / count;
            Location at = fight.center().add(Math.cos(angle) * (fight.radius() - 3), 0.5, Math.sin(angle) * (fight.radius() - 3));
            Slime shard = fight.spawnAdd(Slime.class, at, s -> {
                s.setSize(3);
                s.setCustomName(ChatColor.GREEN + "Sovereign Shard");
                BossFight.setAttribute(s, Attribute.MAX_HEALTH, 40);
                s.setHealth(40);
            });
            if (shard != null) {
                shards.add(shard);
            }
        }
        fight.broadcast("&aThe Sovereign splits! &fStop the shards before they crawl back to the altar!");
        sovereign.getWorld().playSound(sovereign.getLocation(), Sound.ENTITY_SLIME_DEATH, 2F, 0.5F);
    }

    private void tendShards() {
        Location altar = fight.center();
        shards.removeIf(shard -> {
            if (shard.isDead() || !shard.isValid()) {
                return true;
            }
            Vector toAltar = altar.toVector().subtract(shard.getLocation().toVector()).setY(0);
            if (toAltar.lengthSquared() < 4) {
                fight.healBoss(sovereign, 0.10);
                shard.getWorld().spawnParticle(Particle.ITEM_SLIME, shard.getLocation(), 30, 0.5, 0.5, 0.5, 0);
                shard.getWorld().playSound(shard.getLocation(), Sound.ENTITY_SLIME_SQUISH, 1.5F, 1.5F);
                fight.broadcast("&aA shard rejoins its Sovereign.");
                shard.remove();
                return true;
            }
            shard.setTarget(null);
            if (shard.isOnGround()) {
                shard.setVelocity(toAltar.normalize().multiply(0.35).setY(0.3));
            }
            return false;
        });
    }

    private void enrage() {
        double fraction = sovereign.getHealth() / sovereign.getAttribute(Attribute.MAX_HEALTH).getValue();
        double max = sovereign.getAttribute(Attribute.MAX_HEALTH).getValue();
        // setSize resets size-based attributes, so re-apply ours afterwards and keep the health fraction
        sovereign.setSize(4);
        BossFight.setAttribute(sovereign, Attribute.MAX_HEALTH, max);
        BossFight.setAttribute(sovereign, Attribute.ATTACK_DAMAGE, 7);
        BossFight.setAttribute(sovereign, Attribute.KNOCKBACK_RESISTANCE, 0.8);
        BossFight.setAttribute(sovereign, Attribute.MOVEMENT_SPEED, 0.5);
        sovereign.setHealth(Math.max(1, max * fraction));
        fight.broadcast("&aThe Sovereign condenses into its acidic core!");
        sovereign.getWorld().playSound(sovereign.getLocation(), Sound.ENTITY_SLIME_ATTACK, 2F, 0.4F);
    }
}
