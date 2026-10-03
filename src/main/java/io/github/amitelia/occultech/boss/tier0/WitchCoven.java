package io.github.amitelia.occultech.boss.tier0;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.entity.ThrownPotion;
import org.bukkit.entity.Witch;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.PotionMeta;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;

/**
 * Tier-0 mini-boss (iron gear). Three witches whose roles rotate every 15 seconds, shown by their name and aura color.
 * <ul>
 * <li>Healer (green): heals the most wounded sister every 4s.</li>
 * <li>Curser (purple): marks the nearest player for 1s, then weakens and slows them.</li>
 * <li>Bomber (red): lobs harming potions every 4s.</li>
 * </ul>
 * Kill the healer first. Ranged, so the engine's anti-pillar teleport is off.
 */
public final class WitchCoven extends BossBehavior {

    private enum Role {
        HEALER("Healer", ChatColor.GREEN, Color.fromRGB(90, 220, 90)),
        CURSER("Curser", ChatColor.DARK_PURPLE, Color.fromRGB(150, 50, 200)),
        BOMBER("Bomber", ChatColor.RED, Color.fromRGB(220, 60, 60));

        final String title;
        final ChatColor chat;
        final Particle.DustOptions aura;

        Role(String title, ChatColor chat, Color color) {
            this.title = title;
            this.chat = chat;
            this.aura = new Particle.DustOptions(color, 1.3F);
        }
    }

    private static final int ROTATE_INTERVAL = 300;
    private static final int HEAL_INTERVAL = 80;
    private static final int CURSE_INTERVAL = 100;
    private static final int CURSE_WARNING = 20;
    private static final int BOMB_INTERVAL = 80;

    private final List<Witch> witches = new ArrayList<>();
    /** Harming potions in flight, with where each was last seen. */
    private final java.util.Map<ThrownPotion, org.bukkit.Location> potions = new java.util.HashMap<>();
    private int rotation;
    private Player curseTarget;
    private int curseAt = -1;

    public WitchCoven(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        for (int i = 0; i < 3; i++) {
            double angle = Math.PI * 2 * i / 3;
            Location spot = at.clone().add(Math.cos(angle) * 2.5, 0, Math.sin(angle) * 2.5);
            witches.add(fight.spawnBoss(Witch.class, spot, w -> {
                BossFight.setAttribute(w, Attribute.MAX_HEALTH, 80);
                BossFight.setAttribute(w, Attribute.KNOCKBACK_RESISTANCE, 0.4);
                BossFight.setAttribute(w, Attribute.FOLLOW_RANGE, 24);
                w.setCustomNameVisible(true);
            }));
        }
        applyRoles();
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public void tick() {
        int now = fight.elapsed();
        if (witches.removeIf(w -> w.isDead() || !w.isValid())) {
            if (witches.isEmpty()) {
                return;
            }
            // roles are assigned by position, so a death reshuffles them: keep the name tags truthful
            applyRoles();
        }

        if (every(ROTATE_INTERVAL)) {
            rotation++;
            applyRoles();
            fight.broadcast("&5The coven shifts its roles!");
        }

        for (Witch witch : witches) {
            Role role = roleOf(witch);
            witch.getWorld().spawnParticle(Particle.DUST, witch.getLocation().add(0, 2.4, 0), 4, 0.3, 0.2, 0.3, 0, role.aura);
        }

        Witch healer = withRole(Role.HEALER);
        if (healer != null && every(HEAL_INTERVAL)) {
            witches.stream()
                .filter(w -> w != healer)
                .min(Comparator.comparingDouble(w -> w.getHealth() / w.getAttribute(Attribute.MAX_HEALTH).getValue()))
                .ifPresent(patient -> {
                    fight.healBoss(patient, 0.1);
                    patient.getWorld().spawnParticle(Particle.HEART, patient.getLocation().add(0, 2.2, 0), 4, 0.3, 0.2, 0.3, 0);
                    patient.getWorld().playSound(patient.getLocation(), Sound.ENTITY_WITCH_DRINK, 1F, 1.3F);
                });
        }

        Witch curser = withRole(Role.CURSER);
        if (curser != null && every(CURSE_INTERVAL)) {
            Player target = fight.nearestPlayer(curser.getLocation());
            if (target != null && target.getLocation().distance(curser.getLocation()) < 12) {
                curseTarget = target;
                curseAt = now + CURSE_WARNING;
                fight.telegraph(target.getLocation(), 1.4, CURSE_WARNING, Role.CURSER.aura.getColor(), FloorDecals.Mark.CURSE);
                target.getWorld().spawnParticle(Particle.WITCH, target.getLocation().add(0, 1, 0), 30, 0.4, 0.8, 0.4, 0);
                target.playSound(target.getLocation(), Sound.ENTITY_EVOKER_PREPARE_ATTACK, 1F, 1.4F);
            }
        }
        if (now == curseAt && curseTarget != null && curseTarget.isValid()) {
            curseTarget.addPotionEffect(new PotionEffect(PotionEffectType.WEAKNESS, 100, 0));
            curseTarget.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 60, 0));
        }

        // a splash on the floor where each harming potion burst (checked each step; a thrown potion is gone once it hits)
        potions.entrySet().removeIf(entry -> {
            if (entry.getKey().isValid()) {
                entry.setValue(entry.getKey().getLocation());
                return false;
            }
            FloorDecals.splash(fight, entry.getValue(), 2.5, org.bukkit.Color.fromRGB(200, 40, 90));
            return true;
        });

        Witch bomber = withRole(Role.BOMBER);
        if (bomber != null && every(BOMB_INTERVAL)) {
            Player target = fight.nearestPlayer(bomber.getLocation());
            if (target != null) {
                lob(bomber, target);
            }
        }
    }

    private void applyRoles() {
        Role[] roles = Role.values();
        for (int i = 0; i < witches.size(); i++) {
            Witch witch = witches.get(i);
            Role role = roles[(i + rotation) % roles.length];
            witch.setCustomName(role.chat + "Coven " + role.title);
        }
    }

    private Role roleOf(Witch witch) {
        int index = witches.indexOf(witch);
        return Role.values()[(index + rotation) % Role.values().length];
    }

    private Witch withRole(Role role) {
        for (Witch witch : witches) {
            if (roleOf(witch) == role) {
                return witch;
            }
        }
        return null;
    }

    private void lob(Witch bomber, Player target) {
        ItemStack potion = new ItemStack(Material.SPLASH_POTION);
        PotionMeta meta = (PotionMeta) potion.getItemMeta();
        meta.addCustomEffect(new PotionEffect(PotionEffectType.INSTANT_DAMAGE, 1, 0), true);
        potion.setItemMeta(meta);

        Vector velocity = target.getLocation().toVector().subtract(bomber.getLocation().toVector());
        double distance = velocity.length();
        velocity.normalize().multiply(Math.min(1.1, 0.35 + distance * 0.06)).setY(0.35 + distance * 0.02);
        ThrownPotion thrown = bomber.launchProjectile(ThrownPotion.class, velocity);
        thrown.setItem(potion);
        potions.put(thrown, thrown.getLocation());
        bomber.getWorld().playSound(bomber.getLocation(), Sound.ENTITY_WITCH_THROW, 1F, 1F);
    }
}
