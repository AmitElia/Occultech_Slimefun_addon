package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;

import io.github.amitelia.occultech.boss.Mechanic;

/**
 * FM's radio waves (Session E3): rings of sound spread out from FM, and their pitch says what they are. A high
 * chime: three fast, low rings - jump each one. A deep bass note: one slow ring too tall to jump, with a gap - walk
 * through the gap.
 */
final class RadioSignature extends Signature {

    static final String ID = "RAID_FM";
    private static final Mechanic TREBLE = Mechanic.of(ID, "Treble wave", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic BASS = Mechanic.of(ID, "Bass wave", 26, Mechanic.Kind.AREA, true);
    private static final int WARNING = 20;
    private static final double REACH = 12;
    private static final Color TREBLE_COLOR = Color.fromRGB(255, 220, 80);
    private static final Color BASS_COLOR = Color.fromRGB(150, 80, 255);

    private final List<RaidRing> rings = new ArrayList<>();
    private boolean bass;

    RadioSignature(StaffKit kit) {
        super(kit, 60);
    }

    @Override
    boolean cast(int now) {
        if (kit.target == null || !rings.isEmpty()) {
            next = now + 20;
            return false;
        }
        next = now + 120;
        bass = !bass;
        Location at = kit.body.getLocation();
        at.getWorld().spawnParticle(Particle.NOTE, at.clone().add(0, 2.2, 0), 8, 0.6, 0.3, 0.6, 1);
        if (bass) {
            kit.claim(WARNING + 10);
            at.getWorld().playSound(at, Sound.BLOCK_NOTE_BLOCK_BASS, 2F, 0.5F);
            double gap = ThreadLocalRandom.current().nextDouble(Math.PI * 2);
            kit.later(WARNING, () -> {
                if (kit.alive()) {
                    rings.add(new RaidRing(kit.fight, kit.body.getLocation(), 0.2, REACH, RaidRing.TALL, gap, BASS_COLOR, BASS, kit.body));
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_NOTE_BLOCK_BASS, 2F, 0.5F);
                }
            });
        } else {
            kit.claim(WARNING + 30);
            for (int i = 0; i < 3; i++) {
                int delay = i * 12;
                kit.later(delay, () -> at.getWorld().playSound(kit.body.getLocation(), Sound.BLOCK_NOTE_BLOCK_BELL, 2F, 2F));
                kit.later(WARNING + delay, () -> {
                    if (kit.alive()) {
                        rings.add(new RaidRing(kit.fight, kit.body.getLocation(), 0.45, REACH, RaidRing.LOW, Double.NaN, TREBLE_COLOR, TREBLE,
                            kit.body));
                    }
                });
            }
        }
        return true;
    }

    @Override
    void move() {
        rings.removeIf(ring -> !ring.step());
    }
}
