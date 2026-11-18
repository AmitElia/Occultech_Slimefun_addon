package io.github.amitelia.occultech.boss.tier2;

import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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
import io.github.amitelia.occultech.boss.Prop;
import io.github.amitelia.occultech.core.Keys;

/**
 * Tier-2 mini-boss (max netherite). Three blazes circle the altar, singing (docs/art/bosses/blaze_choir/overhaul): the
 * Soprano a wind chime of organ pipes, the Alto a pair of great cymbals, the Bass a church bell under its bell wheel, each
 * a Mythic carrier with its own model when MythicMobs and BetterModel are installed.
 * <ul>
 * <li>The shield passes from singer to singer every 6s: the shielded one (its instrument closed, its fire banked down)
 * takes 90% less damage. Hit the others.</li>
 * <li>Each strikes its instrument on its own beat and a custom fireball leaves its mouth on the strike; fireballs burn
 * players but never light blocks.</li>
 * <li>Chorus: flame circles appear under players and erupt after 1.5s, when the choir's chorus peaks.</li>
 * <li>Each time a singer falls, the others sing faster and burn hotter; the last singer is never shielded.</li>
 * </ul>
 * Each blaze takes a third of the damage dealt.
 */
public final class BlazeChoir extends BossBehavior {

    private static final double HEALTH = 110;
    private static final double ARMOR = 0.33;
    private static final double SHIELD = 0.1;
    private static final double ORBIT_RADIUS = 5;
    /** Hover height: the vanilla blazes fly at 2.5; the instrument bodies hang down, so they fly at 1 to stay in reach. */
    private static final double HOVER = 2.5;
    private static final double HOVER_MODELLED = 1.0;
    private static final int SHIELD_INTERVAL = 120;
    private static final int CHORUS_INTERVAL = 300;
    private static final int CHORUS_WARNING = 30;
    /** The strike clip's contact: the fireball leaves 10 ticks after the clip starts. */
    private static final int STRIKE_LEAD = 10;
    private static final io.github.amitelia.occultech.boss.Mechanic FIREBALL_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("BLAZE_CHOIR", "Fireball", 20, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic CHORUS_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("BLAZE_CHOIR", "Chorus eruption", 32, io.github.amitelia.occultech.boss.Mechanic.Kind.AREA, true);
    private static final Color FLAME = Color.fromRGB(255, 120, 30);
    private static final int DEAD = Color.fromRGB(44, 40, 40).asRGB();

    /**
     * The three singers: each one's body (the Mythic carrier OCCULTECH_BLAZE_CHOIR_<VOICE>), its glow bones and its mouth.
     * The glow bones are named as BetterModel names them, tag prefix dropped ({@code glow_wisp} is {@code wisp}).
     */
    private enum Voice {
        SOPRANO("Soprano", 75 / 16.0, "wisp", "sail", "mouth"),
        ALTO("Alto", 62 / 16.0, "ember", "mouth"),
        BASS("Bass", 56 / 16.0, "wisp", "clapper", "mouth");

        final String title;
        /** The mouth's height over the carrier's feet in blocks: the fireball leaves it. */
        final double mouth;
        final String[] glows;

        Voice(String title, double mouth, String... glows) {
            this.title = title;
            this.mouth = mouth;
            this.glows = glows;
        }
    }

    private final List<Blaze> singers = new ArrayList<>();
    private final Map<Blaze, Voice> voices = new HashMap<>();
    private final List<Location> chorus = new ArrayList<>();
    /** Fireballs waiting for their strike's contact: who, at whom, at what fight tick. */
    private final List<Object[]> strikes = new ArrayList<>();
    private Blaze shielded;
    @javax.annotation.Nullable private io.github.amitelia.occultech.boss.AirEffects.Aura shieldRing;
    private int chorusAt = -1;
    private double spin;
    private boolean lastPlayed;

    public BlazeChoir(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        Voice[] all = Voice.values();
        for (int i = 0; i < 3; i++) {
            Voice voice = all[i];
            double angle = Math.PI * 2 * i / 3;
            boolean modelled = fight.usesMythicBody(voice.name());
            double hover = modelled ? HOVER_MODELLED : HOVER;
            Blaze blaze = fight.spawnBoss(voice.name(), Blaze.class,
                at.clone().add(Math.cos(angle) * ORBIT_RADIUS, hover, Math.sin(angle) * ORBIT_RADIUS), b -> {
                    b.setCustomName(ChatColor.GOLD + "Blaze Choir " + ChatColor.GRAY + "(" + voice.title + ")");
                    b.setCustomNameVisible(true);
                    Abyss.puppet(b);
                    BossFight.setAttribute(b, Attribute.MAX_HEALTH, HEALTH);
                    // the model is drawn at its own size; only the plain blaze is grown
                    BossFight.setAttribute(b, Attribute.SCALE, modelled ? 1.0 : 1.5);
                });
            singers.add(blaze);
            voices.put(blaze, voice);
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
        List<Blaze> fallen = new ArrayList<>();
        singers.removeIf(blaze -> {
            if (blaze.isValid() && !blaze.isDead()) {
                return false;
            }
            fallen.add(blaze);
            return true;
        });
        for (Blaze dead : fallen) {
            voices.remove(dead);
            strikes.removeIf(s -> s[0] == dead);
            fight.broadcast("&6A voice falls silent - &fthe others sing faster!");
            // the survivors burn hotter (the last one hottest, below)
            for (Blaze survivor : singers) {
                if (survivor != shielded) {
                    act(survivor, "STATE_HOTTER");
                }
            }
        }
        if (singers.isEmpty()) {
            return;
        }
        int now = fight.elapsed();
        int gone = 3 - singers.size();

        for (Blaze blaze : singers) {
            Player target = fight.nearestPlayer(blaze.getLocation());
            if (target != null) {
                Abyss.face(blaze, target.getEyeLocation());
            }
        }

        if (singers.size() <= 1) {
            dropShield();   // the last singer is never shielded: the end of the fight isn't a wall
            if (!lastPlayed) {
                lastPlayed = true;
                act(singers.get(0), "LAST");
                act(singers.get(0), "STATE_LAST");
            }
        } else if (every(SHIELD_INTERVAL) || shielded == null || !singers.contains(shielded)) {
            passShield();
        }
        drawShield();

        // each singer strikes on its own beat, faster as the choir shrinks; the fireball leaves on the strike
        int beat = Math.max(20, 60 - 15 * gone);
        for (int i = 0; i < singers.size(); i++) {
            Blaze blaze = singers.get(i);
            if ((now + i * 20) % beat == 0 && strikes.stream().noneMatch(s -> s[0] == blaze)) {
                Player target = fight.randomPlayer();
                if (target != null) {
                    act(blaze, "STRIKE");
                    strikes.add(new Object[] { blaze, target, now + (modelled(blaze) ? STRIKE_LEAD : 0) });
                }
            }
        }

        if (every(CHORUS_INTERVAL) && chorusAt < 0) {
            chorus.clear();
            for (Player player : fight.players()) {
                chorus.add(player.getLocation());
                fight.telegraph(player.getLocation(), 2.5, CHORUS_WARNING + 5, FLAME, FloorDecals.Mark.FLAME);
            }
            chorusAt = now + CHORUS_WARNING;
            for (Blaze blaze : singers) {
                act(blaze, "CHORUS");     // the clip peaks at the eruption, 1.5 s in
            }
            fight.center().getWorld().playSound(fight.center(), Sound.ENTITY_BLAZE_AMBIENT, 2F, 0.5F);
        }
        if (chorusAt >= 0 && now >= chorusAt) {
            chorusAt = -1;
            erupt();
        }
    }

    /** Every tick: the choir circles the altar, faster as it shrinks; fireballs leave on their strike's contact. */
    @Override
    public void move() {
        if (singers.isEmpty()) {
            return;
        }
        int now = fight.elapsed();
        strikes.removeIf(s -> {
            if (now < (int) s[2]) {
                return false;
            }
            Blaze blaze = (Blaze) s[0];
            Player target = (Player) s[1];
            if (blaze.isValid() && !blaze.isDead() && target.isValid() && fight.players().contains(target)) {
                fireball(blaze, target);
            }
            return true;
        });
        int gone = 3 - singers.size();
        spin += (0.08 + 0.03 * gone) / 5;
        for (int i = 0; i < singers.size(); i++) {
            Blaze blaze = singers.get(i);
            if (!blaze.isValid()) {
                continue;
            }
            double hover = modelled(blaze) ? HOVER_MODELLED : HOVER;
            double angle = spin + Math.PI * 2 * i / singers.size();
            Location spot = fight.center().clone().add(Math.cos(angle) * ORBIT_RADIUS, hover + Math.sin(spin * 2 + i) * 0.5, Math.sin(angle) * ORBIT_RADIUS);
            blaze.setVelocity(spot.toVector().subtract(blaze.getLocation().toVector()).multiply(0.3));
        }
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (boss instanceof Blaze blaze && voices.containsKey(blaze)) {
            act(blaze, "FLINCH");
        }
    }

    /** The fallen singer's model stays for its whole death clip, its fire out. */
    @Override
    public void onBossDeath(LivingEntity boss) {
        Voice voice = boss instanceof Blaze blaze ? voices.get(blaze) : null;
        if (voice == null) {
            return;
        }
        Prop corpse = fight.corpse(boss);
        if (corpse != null) {
            corpse.tint(DEAD, voice.glows);
        }
    }

    private void dropShield() {
        if (shielded == null && shieldRing == null) {
            return;
        }
        if (shielded != null) {
            shielded.setGlowing(false);
        }
        shielded = null;
        if (shieldRing != null) {
            shieldRing.end();
            shieldRing = null;
        }
        fight.broadcast("&6The last singer's shield breaks - &fit stands bare!");
    }

    private void passShield() {
        if (singers.isEmpty()) {
            shielded = null;
            return;
        }
        int next = shielded == null ? 0 : (singers.indexOf(shielded) + 1) % singers.size();
        Blaze old = shielded;
        if (old != null) {
            old.setGlowing(false);
            if (singers.contains(old)) {
                act(old, "UNSHIELD");
                act(old, singers.size() < 3 ? "STATE_HOTTER" : "STATE_CALM");
            }
        }
        shielded = singers.get(Math.max(0, next));
        // the instrument closes and its fire banks down; a plain blaze glows instead (an outline would show the
        // invisible carrier's shape under a model)
        if (modelled(shielded)) {
            act(shielded, "SHIELD");
        } else {
            shielded.setGlowing(true);
        }
        if (shieldRing != null) {
            shieldRing.end();
        }
        shieldRing = io.github.amitelia.occultech.boss.AirEffects.Aura.create(fight, shielded, "aura_flame", 0.45, 2.6);
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
        Voice voice = voices.get(blaze);
        Location mouth = modelled(blaze) && voice != null
            ? blaze.getLocation().add(blaze.getLocation().getDirection().setY(0).multiply(0.9)).add(0, voice.mouth, 0)
            : blaze.getEyeLocation();
        Vector aim = target.getEyeLocation().toVector().subtract(mouth.toVector()).normalize();
        SmallFireball fireball = blaze.launchProjectile(SmallFireball.class, aim.clone().multiply(0.9));
        fireball.teleport(mouth.setDirection(aim));
        fireball.setVelocity(aim.multiply(0.9));
        fireball.setIsIncendiary(false);
        fireball.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, FIREBALL_DAMAGE.damage());
        fight.label(fireball, FIREBALL_DAMAGE);
        blaze.getWorld().playSound(blaze.getLocation(), Sound.ENTITY_BLAZE_SHOOT, 1F, 1.2F);
    }

    private void erupt() {
        for (Location at : chorus) {
            at.getWorld().spawnParticle(Particle.FLAME, at.clone().add(0, 0.5, 0), 60, 1.2, 1, 1.2, 0.05);
            io.github.amitelia.occultech.boss.AirEffects.burst(fight, at.clone().add(0, 1, 0), io.github.amitelia.occultech.boss.AirEffects.Burst.IMPACT, FLAME, 3F);
            at.getWorld().spawnParticle(Particle.LAVA, at, 8, 1, 0.2, 1, 0);
            at.getWorld().playSound(at, Sound.ITEM_FIRECHARGE_USE, 1.5F, 0.7F);
            LivingEntity source = singers.isEmpty() ? null : singers.get(0);
            for (Player player : fight.players()) {
                if (player.getLocation().distanceSquared(at) <= 6.25) {
                    fight.hit(player, CHORUS_DAMAGE, source);
                    player.setFireTicks(Math.max(player.getFireTicks(), 60));
                }
            }
        }
        chorus.clear();
    }

    /** Plays the singer's clip, tint or sound (the Mythic skill BLAZE_CHOIR_<VOICE>_<ACTION>); nothing without a model. */
    private void act(Blaze blaze, String action) {
        Voice voice = voices.get(blaze);
        if (voice != null) {
            fight.playAction(blaze, voice.name() + "_" + action);
        }
    }

    private boolean modelled(Blaze blaze) {
        Voice voice = voices.get(blaze);
        return voice != null && fight.usesMythicBody(voice.name());
    }
}
