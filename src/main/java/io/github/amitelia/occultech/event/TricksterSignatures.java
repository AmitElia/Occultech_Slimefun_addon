package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.entity.TextDisplay;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.papermc.paper.datacomponent.item.ResolvableProfile;

/**
 * Signatures that trick rather than hurt (Session E5).
 * <ul>
 * <li><b>decoys</b> (Kon, the Jester): three copies of Kon wander the floor. The real one gives off a faint sparkle.
 * Hitting a decoy pops it, makes you glow for 3 s and lets Kon slip away to a new spot.</li>
 * <li><b>denied</b> (Nick, Spleen): the Hexer's mark shows a red DENIED over the marked player, stamped on the floor when
 * it bursts.</li>
 * </ul>
 */
final class TricksterSignatures {

    private static final Color DENIED_RED = Color.fromRGB(230, 30, 30);

    private TricksterSignatures() {}

    /** Kon's decoys. */
    static final class Decoys extends Signature {

        private static final int COUNT = 3;
        private static final int LIFE = 300;
        private final List<Mannequin> decoys = new ArrayList<>();
        private int age;
        private int bornAt;

        Decoys(StaffKit kit) {
            super(kit, 80);
        }

        @Override
        boolean cast(int now) {
            if (kit.target == null) {
                next = now + 20;
                return false;
            }
            next = now + 300;
            kit.claim(10);
            clear();
            for (int i = 0; i < COUNT; i++) {
                Location at = safeSpot(kit.fight.center(), 2, kit.fight.radius() - 3);
                if (at == null) {
                    continue;
                }
                Mannequin decoy = kit.fight.spawnAdd(Mannequin.class, at, m -> {
                    m.setProfile(ResolvableProfile.resolvableProfile().name(kit.member.skin()).build());
                    m.setCustomName(kit.body.getCustomName());
                    m.setCustomNameVisible(true);
                    m.setDescription(kit.body.getDescription());
                    BossFight.setAttribute(m, Attribute.MAX_HEALTH, 1);
                    m.setHealth(1);
                });
                if (decoy != null) {
                    decoys.add(decoy);
                    at.getWorld().spawnParticle(Particle.CLOUD, at.clone().add(0, 1, 0), 10, 0.3, 0.6, 0.3, 0.02);
                }
            }
            bornAt = age;
            kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_ILLUSIONER_PREPARE_MIRROR, 1.5F, 1.2F);
            blink();
            return true;
        }

        private void clear() {
            decoys.forEach(Entity::remove);
            decoys.clear();
        }

        /** Kon slips away: trades places with a decoy, or to a new spot. */
        private void blink() {
            if (!kit.alive()) {
                return;
            }
            decoys.removeIf(d -> !d.isValid() || d.isDead());
            Location from = kit.body.getLocation();
            Location to;
            if (!decoys.isEmpty()) {
                Mannequin decoy = decoys.get(ThreadLocalRandom.current().nextInt(decoys.size()));
                to = decoy.getLocation();
                decoy.teleport(from);
            } else {
                to = safeSpot(kit.fight.center(), 2, kit.fight.radius() - 3);
            }
            if (to == null) {
                return;
            }
            from.getWorld().spawnParticle(Particle.CLOUD, from.clone().add(0, 1, 0), 15, 0.3, 0.6, 0.3, 0.02);
            kit.body.teleport(to);
            to.getWorld().playSound(to, Sound.ENTITY_ILLUSIONER_MIRROR_MOVE, 1F, 1.2F);
        }

        @Override
        void onAddDeath(Entity entity, @Nullable Player killer) {
            if (!decoys.remove(entity)) {
                return;
            }
            Location at = entity.getLocation().add(0, 1, 0);
            at.getWorld().spawnParticle(Particle.TOTEM_OF_UNDYING, at, 30, 0.3, 0.6, 0.3, 0.3);
            at.getWorld().playSound(at, Sound.ENTITY_FIREWORK_ROCKET_TWINKLE, 1.2F, 1.2F);
            if (killer != null) {
                killer.addPotionEffect(new PotionEffect(PotionEffectType.GLOWING, 60, 0, false, false));
                killer.sendActionBar(Component.text("Fooled! That was a decoy - " + kit.member.display() + " sees you!", NamedTextColor.YELLOW));
                blink();
            }
        }

        @Override
        void move() {
            age++;
            decoys.removeIf(d -> !d.isValid() || d.isDead());
            if (age - bornAt > LIFE) {
                clear();
            }
            // the decoys act like Kon, but never attack
            for (Mannequin decoy : decoys) {
                Player near = kit.fight.nearestPlayer(decoy.getLocation());
                if (near != null) {
                    Abyss.walk(decoy, near.getLocation(), 0.24, 7);
                }
            }
            if (age % 10 == 0 && kit.alive() && !decoys.isEmpty()) {
                // the tell: only the real one sparkles
                kit.body.getWorld().spawnParticle(Particle.END_ROD, kit.body.getLocation().add(0, 2.1, 0), 1, 0.2, 0.1, 0.2, 0);
            }
        }
    }

    /** Nick's and Spleen's DENIED on the Hexer's mark. */
    static final class Denied extends Signature {

        private record Stamp(TextDisplay word, Player player, int until) {}

        private final List<Stamp> stamps = new ArrayList<>();
        private int age;

        Denied(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // passive: it dresses the Hexer's mark
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        /** The Hexer marked {@code player} for {@code ticks}. */
        void mark(Player player, int ticks) {
            TextDisplay word = text(player.getLocation().add(0, 2.6, 0), "DENIED", DENIED_RED, 1.6F, false);
            word.setTeleportDuration(1);
            stamps.add(new Stamp(word, player, age + ticks));
            player.playSound(player.getLocation(), Sound.BLOCK_NOTE_BLOCK_BASS, 1F, 0.5F);
        }

        @Override
        void move() {
            age++;
            for (Iterator<Stamp> it = stamps.iterator(); it.hasNext();) {
                Stamp stamp = it.next();
                if (!stamp.player().isOnline() || age >= stamp.until()) {
                    stamp.word().remove();
                    it.remove();
                    if (stamp.player().isOnline() && kit.alive()) {
                        // the burst stamps it on the floor
                        Location floor = stamp.player().getLocation().add(0, 0.05, 0);
                        TextDisplay flat = text(floor, "DENIED", DENIED_RED, 2.4F, true);
                        floor.getWorld().playSound(floor, Sound.BLOCK_ANVIL_LAND, 0.8F, 1.4F);
                        kit.later(20, flat::remove);
                    }
                    continue;
                }
                stamp.word().teleport(stamp.player().getLocation().add(0, 2.6, 0));
            }
        }
    }
}
