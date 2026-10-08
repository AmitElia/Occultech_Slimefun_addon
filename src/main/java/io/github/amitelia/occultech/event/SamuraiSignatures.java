package io.github.amitelia.occultech.event;

import javax.annotation.Nullable;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * S4MURAI's signatures (Session E4).
 * <ul>
 * <li><b>enderstep</b>: arrows and other projectiles never land - S4MURAI steps away like an enderman, 8-16 blocks,
 * staying in the fight. Close in instead.</li>
 * <li><b>swap</b>: a melee hit on S4MURAI trades your places (once every 4 s, only between two safe spots).</li>
 * <li><b>katana</b>: a red and black katana (boss-only; its model comes in the art pass, a netherite sword until then).
 * Takes turns between an iai slash - a red line warns, then S4MURAI flashes to its end and cuts everyone on
 * it - and a crescent sweep in front.</li>
 * </ul>
 */
final class SamuraiSignatures {

    static final String ID = "RAID_S4MURAI";
    private static final Mechanic IAI = Mechanic.of(ID, "Iai slash", 30, Mechanic.Kind.AREA, true);
    private static final Mechanic CRESCENT = Mechanic.of(ID, "Crescent sweep", 28, Mechanic.Kind.MELEE, true);
    private static final Color RED = Color.fromRGB(220, 20, 30);

    private SamuraiSignatures() {}

    /** Projectiles pass; S4MURAI steps away. */
    static final class Enderstep extends Signature {

        Enderstep(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // passive
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        @Override
        boolean deflect(Projectile projectile) {
            if (!kit.alive()) {
                return false;
            }
            Location from = kit.body.getLocation();
            Location to = safeSpot(from, 8, 16);
            from.getWorld().spawnParticle(Particle.PORTAL, from.clone().add(0, 1, 0), 40, 0.4, 0.8, 0.4, 0.4);
            if (to != null) {
                kit.body.teleport(to);
                to.getWorld().spawnParticle(Particle.PORTAL, to.clone().add(0, 1, 0), 40, 0.4, 0.8, 0.4, 0.4);
                to.getWorld().playSound(to, Sound.ENTITY_ENDERMAN_TELEPORT, 1F, 1F);
            }
            from.getWorld().playSound(from, Sound.ENTITY_ENDERMAN_TELEPORT, 1F, 1F);
            return true;
        }
    }

    /** Melee hits trade places. */
    static final class Swap extends Signature {

        private static final int COOLDOWN = 80;
        private static final double MELEE_REACH = 4.5;
        @Nullable private Player pending;
        private int ready;

        Swap(StaffKit kit) {
            super(kit, 0);
            next = Integer.MAX_VALUE;   // passive
        }

        @Override
        boolean cast(int now) {
            return false;
        }

        @Override
        void onHitBy(Player player, double damage) {
            int now = kit.fight.elapsed();
            if (now >= ready && pending == null && kit.alive() && kit.within(player, MELEE_REACH) && player.isOnGround()) {
                pending = player;   // done next tick, outside the damage event
            }
        }

        @Override
        void move() {
            Player player = pending;
            pending = null;
            if (player == null || !kit.alive() || !kit.fighting(player)) {
                return;
            }
            Location own = kit.body.getLocation();
            Location theirs = player.getLocation();
            if (!standable(own) || !standable(theirs)) {
                return;
            }
            ready = kit.fight.elapsed() + COOLDOWN;
            Location playerTo = own.clone();
            playerTo.setYaw(theirs.getYaw());
            playerTo.setPitch(theirs.getPitch());
            Location bodyTo = theirs.clone();
            bodyTo.setDirection(own.toVector().subtract(theirs.toVector()));
            player.teleport(playerTo);
            kit.body.teleport(bodyTo);
            for (Location at : new Location[] { own, theirs }) {
                at.getWorld().spawnParticle(Particle.REVERSE_PORTAL, at.clone().add(0, 1, 0), 25, 0.3, 0.7, 0.3, 0.05);
            }
            own.getWorld().playSound(own, Sound.ENTITY_ENDERMAN_TELEPORT, 1F, 1.5F);
            player.sendActionBar(Component.text("Swapped!", NamedTextColor.RED));
        }

        /** Two free blocks over a solid one. */
        private static boolean standable(Location at) {
            Block feet = at.getBlock();
            return feet.isPassable() && feet.getRelative(0, 1, 0).isPassable() && !feet.getRelative(0, -1, 0).isPassable();
        }
    }

    /** The katana: iai slash and crescent sweep. */
    static final class Katana extends Signature {

        private static final int IAI_WARNING = 25;
        private static final double IAI_LENGTH = 10;
        private static final int CRESCENT_WARNING = 20;
        private static final double CRESCENT_REACH = 5;
        private boolean crescent;

        Katana(StaffKit kit) {
            super(kit, 60);
            ItemStack katana = new ItemStack(Material.NETHERITE_SWORD);
            ItemMeta meta = katana.getItemMeta();
            meta.setDisplayName(ChatColor.DARK_RED + kit.member.display() + "'s Katana");
            katana.setItemMeta(meta);
            kit.body.getEquipment().setItemInMainHand(katana);
        }

        @Override
        boolean cast(int now) {
            Player target = kit.target;
            if (target == null || !kit.within(target, crescent ? CRESCENT_REACH + 1 : 14)) {
                next = now + 20;
                return false;
            }
            next = now + 120;
            if (crescent) {
                crescent(target);
            } else {
                iai(target);
            }
            crescent = !crescent;
            return true;
        }

        private void iai(Player target) {
            Location from = kit.body.getLocation();
            Location to = StaffKit.lane(from, target.getLocation(), IAI_LENGTH);
            kit.claim(IAI_WARNING + 5);
            from.getWorld().playSound(from, Sound.ITEM_ARMOR_EQUIP_NETHERITE, 1.5F, 0.6F);
            for (int t = 0; t < IAI_WARNING; t += 5) {
                kit.later(t, () -> kit.drawLine(from.clone().add(0, 0.15, 0), to.clone().add(0, 0.15, 0), RED, 0.35));
            }
            kit.later(IAI_WARNING, () -> {
                if (!kit.alive()) {
                    return;
                }
                Vector step = to.toVector().subtract(from.toVector()).multiply(1 / 8.0);
                for (int i = 0; i <= 8; i++) {
                    from.getWorld().spawnParticle(Particle.SWEEP_ATTACK, from.clone().add(step.clone().multiply(i)).add(0, 1, 0), 1, 0, 0, 0, 0);
                }
                for (Player player : kit.playersAlong(from, to, 1.3)) {
                    kit.fight.hit(player, IAI, kit.body);
                }
                // the flash: S4MURAI ends up at the far end of the cut
                Block feet = to.getBlock();
                if (feet.isPassable() && feet.getRelative(0, 1, 0).isPassable()) {
                    Location end = to.clone();
                    end.setDirection(to.toVector().subtract(from.toVector()));
                    kit.body.teleport(end);
                }
                kit.body.swingMainHand();
                from.getWorld().playSound(to, Sound.ENTITY_PLAYER_ATTACK_STRONG, 1.5F, 0.7F);
            });
        }

        private void crescent(Player target) {
            Abyss.face(kit.body, target.getLocation());
            Location at = kit.body.getLocation();
            Vector facing = target.getLocation().toVector().subtract(at.toVector()).setY(0);
            if (facing.lengthSquared() < 0.01) {
                facing = at.getDirection().setY(0);
            }
            double aim = Math.atan2(facing.getZ(), facing.getX());
            kit.claim(CRESCENT_WARNING + 5);
            at.getWorld().playSound(at, Sound.ITEM_TRIDENT_RETURN, 1.5F, 0.5F);
            Particle.DustOptions dust = new Particle.DustOptions(RED, 1.3F);
            for (int t = 0; t < CRESCENT_WARNING; t += 5) {
                kit.later(t, () -> {
                    for (double a = aim - Math.PI / 2; a <= aim + Math.PI / 2; a += 0.12) {
                        for (double r : new double[] { 2.5, CRESCENT_REACH }) {
                            at.getWorld().spawnParticle(Particle.DUST, at.clone().add(Math.cos(a) * r, 0.15, Math.sin(a) * r), 1, 0, 0, 0, 0, dust);
                        }
                    }
                });
            }
            kit.later(CRESCENT_WARNING, () -> {
                if (!kit.alive()) {
                    return;
                }
                kit.body.swingMainHand();
                Location now = kit.body.getLocation();
                now.getWorld().playSound(now, Sound.ENTITY_PLAYER_ATTACK_SWEEP, 1.5F, 0.6F);
                for (double a = aim - Math.PI / 2; a <= aim + Math.PI / 2; a += 0.4) {
                    now.getWorld().spawnParticle(Particle.SWEEP_ATTACK, now.clone().add(Math.cos(a) * 3, 1, Math.sin(a) * 3), 1, 0, 0, 0, 0);
                }
                for (Player player : kit.playersNear(now, CRESCENT_REACH)) {
                    Vector to = player.getLocation().toVector().subtract(now.toVector());
                    if (Math.abs(RaidGeometry.angleBetween(Math.atan2(to.getZ(), to.getX()), aim)) <= Math.PI / 2) {
                        kit.fight.hit(player, CRESCENT, kit.body);
                    }
                }
            });
        }
    }
}
