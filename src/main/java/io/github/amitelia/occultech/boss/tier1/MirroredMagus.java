package io.github.amitelia.occultech.boss.tier1;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Illusioner;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import com.destroystokyo.paper.entity.ai.GoalType;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-1 mini-boss (diamond gear). An Illusioner (a mob that never spawns in survival).
 * <ul>
 * <li>Every 15s it conjures 3 decoys that look just like it and blinks to a new spot among them.</li>
 * <li>The real Magus trails a faint white sparkle; decoys don't.</li>
 * <li>Hitting a decoy shatters it, makes you glow for 3s and lets the Magus blink again.</li>
 * </ul>
 * Decoys never target anyone, so they can't cast. Ranged, so the anti-pillar teleport is off.
 */
public final class MirroredMagus extends BossBehavior {

    private static final int DECOY_INTERVAL = 300;
    private static final int DECOY_COUNT = 3;

    private final List<Illusioner> decoys = new ArrayList<>();
    private Illusioner magus;

    public MirroredMagus(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        magus = fight.spawnBoss(Illusioner.class, at, m -> {
            dress(m);
            m.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));
            BossFight.setAttribute(m, Attribute.MAX_HEALTH, 220);
            BossFight.setAttribute(m, Attribute.KNOCKBACK_RESISTANCE, 0.3);
            BossFight.setAttribute(m, Attribute.FOLLOW_RANGE, 32);
        });
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public void tick() {
        if (!magus.isValid()) {
            return;
        }
        decoys.removeIf(d -> d.isDead() || !d.isValid());
        magus.getWorld().spawnParticle(Particle.END_ROD, magus.getLocation().add(0, 0.1, 0), 1, 0.2, 0, 0.2, 0);

        if (fight.elapsed() == 100 || every(DECOY_INTERVAL)) {
            for (int i = decoys.size(); i < DECOY_COUNT; i++) {
                Illusioner decoy = fight.spawnAdd(Illusioner.class, fight.randomPoint(3, fight.radius() - 3), d -> {
                    dress(d);
                    BossFight.setAttribute(d, Attribute.MAX_HEALTH, 1);
                    d.setHealth(1);
                });
                if (decoy != null) {
                    // decoys wander but never pick a target, so they can't cast spells
                    Bukkit.getMobGoals().removeAllGoals(decoy, GoalType.TARGET);
                    decoys.add(decoy);
                }
            }
            blink();
            fight.broadcast("&9The Magus splits into reflections. &7Find the one that sparkles.");
        }
    }

    @Override
    public void onAddDeath(Entity entity, @Nullable Player killer) {
        if (!decoys.remove(entity)) {
            return;
        }
        entity.getWorld().spawnParticle(Particle.BLOCK, entity.getLocation().add(0, 1, 0), 30, 0.3, 0.6, 0.3, Material.GLASS.createBlockData());
        entity.getWorld().playSound(entity.getLocation(), Sound.BLOCK_GLASS_BREAK, 1.2F, 1F);
        if (killer != null) {
            killer.addPotionEffect(new PotionEffect(PotionEffectType.GLOWING, 60, 0));
            killer.sendMessage(ChatColor.GRAY + "You shattered an illusion - the Magus sees you!");
            blink();
        }
    }

    private void blink() {
        Location from = magus.getLocation();
        Location to;
        if (!decoys.isEmpty() && ThreadLocalRandom.current().nextBoolean()) {
            // swap places with a decoy
            Illusioner decoy = decoys.get(ThreadLocalRandom.current().nextInt(decoys.size()));
            to = decoy.getLocation();
            decoy.teleport(from);
        } else {
            to = fight.randomPoint(3, fight.radius() - 3);
        }
        from.getWorld().spawnParticle(Particle.CLOUD, from.clone().add(0, 1, 0), 15, 0.3, 0.6, 0.3, 0.02);
        magus.teleport(to);
        to.getWorld().playSound(to, Sound.ENTITY_ILLUSIONER_MIRROR_MOVE, 1F, 1F);
    }

    private static void dress(Illusioner illusioner) {
        illusioner.setCustomName(ChatColor.BLUE + "Mirrored Magus");
        illusioner.setCustomNameVisible(true);
        BossFight.setAttribute(illusioner, Attribute.SCALE, 1.2);
    }
}
