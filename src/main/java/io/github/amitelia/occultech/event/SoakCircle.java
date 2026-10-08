package io.github.amitelia.occultech.event;

import java.util.List;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Display;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.TextDisplay;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;

/**
 * A soak circle (Act 2, Session E6): a ring on the floor with a live count over it, "inside / needed". When it goes off,
 * its damage ({@code needed x share}) is split between the players standing in it, never more than {@link #CAP} each:
 * the more who share it, the less it hurts. If nobody stands in it, it hits the whole raid instead.
 */
final class SoakCircle implements RaidHazard {

    /** Most a single player takes from one circle: about 40% of a benchmark player's health. */
    static final double CAP = 42;
    private static final Color SHORT = Color.fromRGB(240, 170, 40);
    private static final Color ENOUGH = Color.fromRGB(80, 220, 110);

    private final BossFight fight;
    private final Location center;
    private final double radius;
    private final int warnTicks;
    private final int needed;
    private final Mechanic share;
    private final Mechanic empty;
    private final LivingEntity source;
    private final TextDisplay count;
    private int age;

    /**
     * @param share the hit each of {@code needed} players takes when exactly that many share it
     * @param empty the hit everyone in the raid takes if nobody stands in it
     */
    SoakCircle(BossFight fight, Location center, double radius, int warnTicks, int needed, Mechanic share, Mechanic empty, LivingEntity source) {
        this.fight = fight;
        this.center = center.clone();
        this.radius = radius;
        this.warnTicks = warnTicks;
        this.needed = Math.max(1, needed);
        this.share = share;
        this.empty = empty;
        this.source = source;
        this.count = fight.spawnExtra(TextDisplay.class, center.clone().add(0, 1.6, 0), t -> {
            t.setBillboard(Display.Billboard.CENTER);
            t.setBackgroundColor(Color.fromARGB(90, 0, 0, 0));
            t.setBrightness(new Display.Brightness(15, 15));
        });
        fight.telegraph(center, radius, warnTicks, SHORT);
        center.getWorld().playSound(center, Sound.BLOCK_BELL_USE, 1.5F, 0.8F);
    }

    private List<Player> inside() {
        List<Player> out = new java.util.ArrayList<>();
        for (Player player : fight.players()) {
            Location at = player.getLocation();
            double dx = at.getX() - center.getX();
            double dz = at.getZ() - center.getZ();
            if (dx * dx + dz * dz <= radius * radius && Math.abs(at.getY() - center.getY()) < 2.5) {
                out.add(player);
            }
        }
        return out;
    }

    @Override
    public boolean step() {
        age++;
        List<Player> inside = inside();
        boolean enough = inside.size() >= needed;
        if (age % 4 == 1) {
            int seconds = Math.max(0, (warnTicks - age) / 20 + 1);
            count.text(Component.text(inside.size() + "/" + needed, enough ? NamedTextColor.GREEN : NamedTextColor.GOLD)
                .decorate(TextDecoration.BOLD).append(Component.text("  " + seconds + "s", NamedTextColor.GRAY)));
            Particle.DustOptions dust = new Particle.DustOptions(enough ? ENOUGH : SHORT, 1.5F);
            int points = (int) Math.ceil(Math.PI * 2 * radius / 0.5);
            for (int i = 0; i < points; i++) {
                double a = Math.PI * 2 * i / points;
                center.getWorld().spawnParticle(Particle.DUST, center.getX() + Math.cos(a) * radius, center.getY() + 0.2,
                    center.getZ() + Math.sin(a) * radius, 1, 0, 0, 0, 0, dust);
            }
        }
        if (age < warnTicks) {
            return true;
        }
        count.remove();
        center.getWorld().spawnParticle(Particle.EXPLOSION, center.clone().add(0, 0.5, 0), 3, radius / 2, 0.2, radius / 2, 0);
        center.getWorld().playSound(center, Sound.ENTITY_GENERIC_EXPLODE, 1.5F, 0.9F);
        if (inside.isEmpty()) {
            for (Player player : fight.players()) {
                fight.hit(player, empty, source);
            }
            fight.broadcast("&cNobody stood in the circle - &fit hits everyone!");
        } else {
            double each = RaidGeometry.soakShare(needed, inside.size(), share.damage(), CAP);
            for (Player player : inside) {
                fight.hit(player, share, each, source);
            }
        }
        return false;
    }
}
