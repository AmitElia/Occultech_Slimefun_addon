package io.github.amitelia.occultech.event;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * An AoE marker on a player (Act 2, Session E6): a ring follows them for a while, then locks where they stand, then
 * bursts on everyone inside it - the marked player included. The counter is to spread out: whoever is marked walks away
 * from the others before it locks.
 */
final class PlayerMarker implements RaidHazard {

    private static final Color FOLLOW = Color.fromRGB(200, 60, 230);
    private static final Color LOCKED = Color.fromRGB(255, 40, 40);

    private final BossFight fight;
    private final Player marked;
    private final int followTicks;
    private final int lockTicks;
    private final double radius;
    private final Mechanic mechanic;
    private final LivingEntity source;
    private Location spot;
    private int age;
    @javax.annotation.Nullable private org.bukkit.entity.ItemDisplay ring;
    @javax.annotation.Nullable private org.bukkit.entity.ItemDisplay reticle;

    PlayerMarker(BossFight fight, Player marked, int followTicks, int lockTicks, double radius, Mechanic mechanic, LivingEntity source) {
        this.fight = fight;
        this.marked = marked;
        this.followTicks = followTicks;
        this.lockTicks = lockTicks;
        this.radius = radius;
        this.mechanic = mechanic;
        this.source = source;
        marked.sendActionBar(Component.text("You're marked - get away from the others!", NamedTextColor.LIGHT_PURPLE));
        marked.playSound(marked.getLocation(), Sound.BLOCK_NOTE_BLOCK_PLING, 1F, 0.5F);
    }

    @Override
    public boolean step() {
        age++;
        boolean following = age < followTicks;
        if (following) {
            if (!marked.isOnline() || marked.isDead()) {
                removeDecals();
                return false;
            }
            spot = marked.getLocation();
        } else if (age == followTicks) {
            spot.getWorld().playSound(spot, Sound.BLOCK_NOTE_BLOCK_BASEDRUM, 1.5F, 0.6F);
            if (ring != null) {
                io.github.amitelia.occultech.boss.FloorDecals.tint(ring, LOCKED);   // locked: it turns red
                io.github.amitelia.occultech.boss.FloorDecals.tint(reticle, LOCKED);
            }
        }
        if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            if (ring == null) {
                ring = io.github.amitelia.occultech.boss.FloorDecals.flat(fight, spot, "floor_warning_ring", FOLLOW, radius * 2);
                reticle = io.github.amitelia.occultech.boss.FloorDecals.flat(fight, spot, "floor_mark_target", FOLLOW, 1.4);
                ring.setTeleportDuration(1);
                reticle.setTeleportDuration(1);
            } else if (following) {
                Location floor = spot.clone();
                floor.setY(ring.getLocation().getY());
                floor.setYaw(0F);
                floor.setPitch(0F);
                ring.teleport(floor);
                reticle.teleport(floor.clone().add(0, 0.01, 0));
            }
        } else if (age % 2 == 0) {
            Particle.DustOptions dust = new Particle.DustOptions(following ? FOLLOW : LOCKED, following ? 1.2F : 1.7F);
            int points = (int) Math.ceil(Math.PI * 2 * radius / 0.45);
            for (int i = 0; i < points; i++) {
                double a = Math.PI * 2 * i / points + age * 0.05;
                spot.getWorld().spawnParticle(Particle.DUST, spot.getX() + Math.cos(a) * radius, spot.getY() + 0.15,
                    spot.getZ() + Math.sin(a) * radius, 1, 0, 0, 0, 0, dust);
            }
        }
        if (age < followTicks + lockTicks) {
            return true;
        }
        removeDecals();
        spot.getWorld().spawnParticle(Particle.WITCH, spot.clone().add(0, 1, 0), 50, radius / 2, 0.6, radius / 2, 0.05);
        spot.getWorld().playSound(spot, Sound.ENTITY_EVOKER_CAST_SPELL, 1.5F, 0.6F);
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            double dx = at.getX() - spot.getX();
            double dz = at.getZ() - spot.getZ();
            if (dx * dx + dz * dz <= radius * radius && Math.abs(at.getY() - spot.getY()) < 2.5) {
                fight.hit(player, mechanic, source);
            }
        }
        return false;
    }

    private void removeDecals() {
        if (ring != null) {
            ring.remove();
        }
        if (reticle != null) {
            reticle.remove();
        }
    }
}
