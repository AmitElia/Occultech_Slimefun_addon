package io.github.amitelia.occultech.event;

import javax.annotation.Nullable;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.entity.Pose;
import org.bukkit.inventory.ItemStack;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.FloorDecals;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * goob's signature, <b>flight</b> (goob's skin is the Duolingo owl - Session E10): goob flies like a bird, lying flat in
 * the swimming pose, circling above the fight out of melee reach. Now and then a landing circle warns under a player,
 * goob dives on it like a bird of prey and strikes there, then stays low for a moment - the window to hit back - before
 * climbing again. In between, goob drops <b>cigarette towers</b>: one falls onto a warned spot under a player and
 * stands there, lit and smoking, wrapping the floor around it in second-hand smoke that hurts every second. A tower
 * goes out by itself after a while, or players stub it out (a few hits). At most 3 at once.
 */
final class OwlSignature extends Signature {

    static final String ID = "RAID_GOOB";
    private static final Mechanic DIVE = Mechanic.of(ID, "Talon dive", 28, Mechanic.Kind.AREA, true);
    private static final double HOVER = 5;
    private static final double ORBIT = 6;
    private static final int MARK = 25;
    private static final int DIVE_TICKS = 25;
    private static final int PERCH = 40;
    private static final double RADIUS = 2.5;
    private static final Color WARNING = Color.fromRGB(120, 200, 70);
    private static final Mechanic SMOKE = Mechanic.of(ID, "Second-hand smoke", 8, Mechanic.Kind.ZONE, true);
    private static final int CIG_FALL = 15;
    private static final int CIG_LIFE = 240;
    private static final double SMOKE_RADIUS = 3.5;
    private static final float CIG_SCALE = 2.2F;
    private static final int MAX_TOWERS = 3;
    private static final Color SMOKE_COLOR = Color.fromRGB(150, 150, 150);

    /** A standing tower, its smoke on the floor, and when it goes out. */
    private static final class Tower {
        final BossFight.FightObject object;
        final org.bukkit.entity.ItemDisplay haze;
        final Location at;
        final int until;
        boolean out;

        Tower(BossFight.FightObject object, org.bukkit.entity.ItemDisplay haze, Location at, int until) {
            this.object = object;
            this.haze = haze;
            this.at = at;
            this.until = until;
        }
    }

    private final java.util.List<Tower> towers = new java.util.ArrayList<>();
    private int nextCig = 100;
    private int nextDive;

    private enum Phase { CIRCLE, MARK, DIVE, PERCH }

    private Phase phase = Phase.CIRCLE;
    private int ticks;
    private double orbit = Math.random() * Math.PI * 2;
    @Nullable private Location spot;

    OwlSignature(StaffKit kit) {
        super(kit, 60);
        kit.body.setGravity(false);
        kit.body.setPose(Pose.SWIMMING, true);
    }

    @Override
    boolean steering() {
        return true;   // goob flies: the kit neither walks nor swings
    }

    @Override
    boolean cast(int now) {
        Player target = kit.target;
        if (target == null || phase != Phase.CIRCLE) {
            next = now + 20;
            return false;
        }
        towers.removeIf(t -> t.out);
        if (now >= nextCig && towers.size() < MAX_TOWERS) {
            nextCig = now + 260;
            next = now + 60;
            dropCigarette(target);
            return true;
        }
        if (now < nextDive) {
            next = now + 20;
            return false;
        }
        nextDive = now + 130;
        next = now + 60;
        kit.claim(MARK + DIVE_TICKS + PERCH);
        spot = target.getLocation();
        spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
        kit.fight.telegraph(spot, RADIUS, MARK + 10, WARNING, FloorDecals.Mark.DIVE);
        kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PARROT_IMITATE_PHANTOM, 2F, 0.8F);
        phase = Phase.MARK;
        ticks = 0;
        return true;
    }

    @Override
    void move() {
        ticks++;
        smoke();
        if (!kit.alive()) {
            return;
        }
        switch (phase) {
            case CIRCLE, MARK -> {
                // circle above whoever it hunts (or its spot), lying flat, facing where it flies
                Location over = kit.target != null && kit.fighting(kit.target) ? kit.target.getLocation() : kit.home;
                orbit += 0.04;
                Location point = over.clone().add(Math.cos(orbit) * ORBIT, 0, Math.sin(orbit) * ORBIT);
                Abyss.glide(kit.body, point, 0.32, HOVER, 0.3);
                if (phase == Phase.MARK && ticks >= MARK) {
                    phase = Phase.DIVE;
                    ticks = 0;
                    kit.body.getWorld().playSound(kit.body.getLocation(), Sound.ENTITY_PHANTOM_SWOOP, 2F, 1.2F);
                }
            }
            case DIVE -> {
                Vector to = spot.toVector().add(new Vector(0, 0.3, 0)).subtract(kit.body.getLocation().toVector());
                Abyss.face(kit.body, spot);
                if (to.lengthSquared() < 1.2 || ticks >= DIVE_TICKS) {
                    strike();
                    phase = Phase.PERCH;
                    ticks = 0;
                } else {
                    kit.body.setVelocity(to.normalize().multiply(Math.min(1.3, to.length())));
                }
            }
            case PERCH -> {
                kit.body.setVelocity(new Vector());
                if (ticks >= PERCH) {
                    phase = Phase.CIRCLE;
                    ticks = 0;
                }
            }
        }
    }

    /** A lit cigarette falls from goob onto a warned spot under {@code target} and stands there, smoking. */
    private void dropCigarette(Player target) {
        Location spot = target.getLocation();
        spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
        spot.setYaw(0F);
        spot.setPitch(0F);
        kit.fight.telegraph(spot, 1.2, CIG_FALL, SMOKE_COLOR);
        ItemStack look = cigarette();
        Location from = kit.body.getLocation();
        from.setYaw(0F);
        from.setPitch(0F);
        org.bukkit.entity.ItemDisplay falling = kit.fight.spawnExtra(org.bukkit.entity.ItemDisplay.class, from, d -> {
            d.setItemStack(look);
            d.setItemDisplayTransform(org.bukkit.entity.ItemDisplay.ItemDisplayTransform.NONE);
            d.setTransformation(new org.bukkit.util.Transformation(new org.joml.Vector3f(), new org.joml.AxisAngle4f(),
                new org.joml.Vector3f(CIG_SCALE, CIG_SCALE, CIG_SCALE), new org.joml.AxisAngle4f()));
            d.setTeleportDuration(CIG_FALL);
        });
        kit.later(1, () -> falling.teleport(spot.clone().add(0, CIG_SCALE / 2, 0)));
        kit.body.getWorld().playSound(from, Sound.ITEM_FLINTANDSTEEL_USE, 1.5F, 0.8F);
        kit.later(CIG_FALL, () -> {
            falling.remove();
            spot.getWorld().playSound(spot, Sound.BLOCK_WOOD_PLACE, 1.5F, 0.6F);
            org.bukkit.entity.ItemDisplay haze = FloorDecals.enabled()
                ? FloorDecals.flat(kit.fight, spot, "floor_zone_shadow", Color.WHITE, SMOKE_RADIUS * 2) : null;
            Tower[] made = new Tower[1];
            BossFight.FightObject object = kit.fight.spawnObject(spot, look, CIG_SCALE, 0.6F, CIG_SCALE, 4, () -> {
                if (made[0] != null) {
                    putOut(made[0]);
                    kit.fight.broadcast("&7Someone stubbed out " + kit.member.display() + "'s cigarette.");
                }
            });
            made[0] = new Tower(object, haze, spot, kit.fight.elapsed() + CIG_LIFE);
            towers.add(made[0]);
        });
    }

    private static ItemStack cigarette() {
        ItemStack stack = new ItemStack(FloorDecals.enabled() ? Material.PAPER : Material.END_ROD);
        if (FloorDecals.enabled()) {
            org.bukkit.inventory.meta.ItemMeta meta = stack.getItemMeta();
            meta.setItemModel(new org.bukkit.NamespacedKey("occultech", "raid_cigarette"));
            stack.setItemMeta(meta);
        }
        return stack;
    }

    private void putOut(Tower tower) {
        tower.out = true;
        if (tower.haze != null) {
            tower.haze.remove();
        }
        if (tower.object.isAlive()) {
            tower.object.remove();
        }
        tower.at.getWorld().spawnParticle(Particle.LARGE_SMOKE, tower.at.clone().add(0, 1, 0), 15, 0.3, 0.6, 0.3, 0.02);
    }

    /** Every tick: the towers smoke, their haze hurts once a second, and they burn down. */
    private void smoke() {
        int now = kit.fight.elapsed();
        for (Tower tower : towers) {
            if (tower.out) {
                continue;
            }
            if (now >= tower.until || !tower.object.isAlive()) {
                putOut(tower);
                continue;
            }
            Location tip = tower.at.clone().add(0, CIG_SCALE - 0.05, 0);
            if (ticks % 3 == 0) {
                tip.getWorld().spawnParticle(Particle.CAMPFIRE_COSY_SMOKE, tip, 1, 0.05, 0.05, 0.05, 0.01);
            }
            if (ticks % 20 == 0 && kit.alive()) {
                for (Player player : kit.playersNear(tower.at, SMOKE_RADIUS)) {
                    kit.fight.hit(player, SMOKE, kit.body);
                }
            }
        }
    }

    private void strike() {
        kit.body.setVelocity(new Vector());
        spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.2, 0), 30, 1.2, 0.2, 1.2, Material.WHITE_WOOL.createBlockData());
        spot.getWorld().playSound(spot, Sound.ENTITY_PLAYER_ATTACK_KNOCKBACK, 1.5F, 0.8F);
        for (Player player : kit.playersNear(spot, RADIUS)) {
            kit.fight.hit(player, DIVE, kit.body);
            StaffKit.knock(player, spot, 0.8, 0.4);
        }
    }
}
