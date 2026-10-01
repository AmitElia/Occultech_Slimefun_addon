package io.github.amitelia.occultech.boss.tier3;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Arrow;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.inventory.EntityEquipment;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.github.amitelia.occultech.core.Keys;
import io.papermc.paper.datacomponent.item.ResolvableProfile;

/**
 * Tier-3 mini-boss (Infinity gear): a player model (Mannequin) that becomes whoever it fights.
 * <ul>
 * <li>It wears the skin of the player hurting it most (or its target) with cosmetic copies of their gear - never
 * their actual items - and fights like the weapon they hold: melee for blades, arrows for bows, a fire cone for the
 * flame weapons.</li>
 * <li>Echo: it remembers where its target walked for 5s; then a shadow replays that path and hurts whoever stands on
 * it. Standing still or retracing your steps is punished.</li>
 * <li>Reflection: it glows white for 3s; hits taken then do nothing and are partly thrown back. Stop attacking.</li>
 * <li>Shattered mirror at half health: one reflection per player, each wearing that player's face. Only its owner can
 * break it, and the Doppelganger can't be hurt until every reflection is gone.</li>
 * </ul>
 * A Mannequin has no AI, so this script moves it. Takes a tenth of the damage dealt.
 */
public final class Doppelganger extends BossBehavior {

    private static final double HEALTH = 360;
    private static final double ARMOR = 0.1;
    private static final double MELEE = 45;
    private static final double ARROW_DAMAGE = 30;
    private static final double FIRE_DAMAGE = 10;
    private static final double ECHO_DAMAGE = 30;
    private static final double REFLECT_SHARE = 0.3;
    private static final double REFLECTION_HEALTH = 60;
    private static final int ECHO_SAMPLES = 20;
    private static final Color SHADOW = Color.fromRGB(30, 20, 40);

    private enum Stance { MELEE, RANGED, FIRE }

    private static final org.bukkit.NamespacedKey SLIMEFUN_ID = new org.bukkit.NamespacedKey("slimefun", "slimefun_item");

    private Mannequin body;
    private Player target;
    private Stance stance = Stance.MELEE;
    private int nextMelee;
    private final Deque<Location> trail = new ArrayDeque<>();
    private List<Location> echo = List.of();
    private int echoIndex = -1;
    private final Set<UUID> echoHit = new HashSet<>();
    private int reflectingUntil = -1;
    private double lastIncoming;
    private boolean shattered;
    private final Map<Mannequin, Player> reflections = new HashMap<>();

    public Doppelganger(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        body = fight.spawnBoss(Mannequin.class, at.clone().add(0, 1, 0), m -> {
            m.setCustomName(ChatColor.WHITE + "The Doppelganger");
            m.setCustomNameVisible(true);
            m.setDescription(net.kyori.adventure.text.Component.empty());
            BossFight.setAttribute(m, Attribute.MAX_HEALTH, HEALTH);
        });
        target = fight.nearestPlayer(at);
        if (target != null) {
            become(target);
        }
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        if (boss != body) {
            return damage;
        }
        lastIncoming = damage;
        if (fight.elapsed() < reflectingUntil || liveReflections() > 0) {
            boss.getWorld().spawnParticle(Particle.END_ROD, boss.getLocation().add(0, 1.2, 0), 6, 0.3, 0.5, 0.3, 0.05);
            return 0;
        }
        return damage * ARMOR;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (boss == body && fight.elapsed() < reflectingUntil) {
            Abyss.magic(player, Math.min(40, lastIncoming * REFLECT_SHARE), body);
            player.getWorld().playSound(player.getLocation(), Sound.BLOCK_GLASS_BREAK, 1F, 1.6F);
        }
    }

    @Override
    public boolean usesAntiPillar() {
        return stance == Stance.MELEE;
    }

    // ------------------------------------------------------------------ every tick: it walks

    @Override
    public void move() {
        if (body.isValid() && alive(target)) {
            double keep = switch (stance) {
                case MELEE -> 1.5;
                case RANGED -> 10;
                case FIRE -> 4;
            };
            Abyss.walk(body, target.getLocation(), stance == Stance.MELEE ? 0.3 : 0.24, keep);
        }
        reflections.entrySet().removeIf(entry -> !entry.getKey().isValid() || entry.getKey().isDead());
        reflections.forEach((reflection, owner) -> {
            if (alive(owner)) {
                Abyss.walk(reflection, owner.getLocation(), 0.28, 1.5);
            }
        });
    }

    // ------------------------------------------------------------------ every step: it fights

    @Override
    public void tick() {
        if (!body.isValid()) {
            return;
        }
        int now = fight.elapsed();
        if (every(200) || !alive(target)) {
            Player top = fight.topDamager();
            Player next = top != null ? top : fight.nearestPlayer(body.getLocation());
            if (next != null && next != target) {
                target = next;
                become(target);
            } else if (next != null) {
                stance = stanceFor(next);
            }
        }
        if (!alive(target)) {
            return;
        }
        if (every(40)) {
            // the target may have changed armor or weapon mid-fight: keep copying it
            dress(body, target);
            stance = stanceFor(target);
        }
        if (every(5)) {
            trail.addLast(target.getLocation());
            while (trail.size() > ECHO_SAMPLES) {
                trail.removeFirst();
            }
        }

        attack(now);
        reflectionsAttack(now);

        if (every(300) && echoIndex < 0 && trail.size() >= ECHO_SAMPLES / 2) {
            echo = new ArrayList<>(trail);
            echoIndex = 0;
            echoHit.clear();
            fight.broadcast("&8Your echo walks again - &fdon't stand where you were.");
        }
        if (echoIndex >= 0) {
            replayEcho();
        }

        if (every(360) && now >= reflectingUntil && liveReflections() == 0) {
            reflectingUntil = now + 60;
            body.setGlowing(true);
            fight.broadcast("&fThe Doppelganger becomes a mirror - &7stop attacking!");
            body.getWorld().playSound(body.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 2F, 1.4F);
        }
        if (reflectingUntil >= 0 && now >= reflectingUntil && body.isGlowing() && liveReflections() == 0) {
            body.setGlowing(false);
        }

        if (!shattered && fight.healthFraction() < 0.5) {
            shattered = true;
            shatter();
        }
    }

    private void attack(int now) {
        switch (stance) {
            case MELEE -> {
                if (now >= nextMelee && target.getLocation().distanceSquared(body.getLocation()) <= 9) {
                    nextMelee = now + 20;
                    body.swingMainHand();
                    target.damage(MELEE, body);
                }
            }
            case RANGED -> {
                if (every(30)) {
                    Vector aim = target.getEyeLocation().toVector().subtract(body.getEyeLocation().toVector()).normalize().multiply(2.4);
                    Arrow arrow = body.launchProjectile(Arrow.class, aim);
                    arrow.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, ARROW_DAMAGE);
                    body.swingMainHand();
                }
            }
            case FIRE -> {
                Location eye = body.getEyeLocation();
                Vector look = target.getEyeLocation().toVector().subtract(eye.toVector()).normalize();
                for (int i = 0; i < 6; i++) {
                    Vector spread = look.clone().add(new Vector(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).multiply(0.25));
                    eye.getWorld().spawnParticle(Particle.FLAME, eye, 0, spread.getX(), spread.getY(), spread.getZ(), 0.5);
                }
                if (every(10)) {
                    for (Player player : fight.players()) {
                        Vector to = player.getEyeLocation().toVector().subtract(eye.toVector());
                        if (to.length() <= 6.5 && Math.toDegrees(to.angle(look)) <= 30) {
                            Abyss.magic(player, FIRE_DAMAGE, body);
                            player.setFireTicks(Math.max(player.getFireTicks(), 60));
                        }
                    }
                }
            }
        }
    }

    private void replayEcho() {
        if (echoIndex >= echo.size()) {
            echoIndex = -1;
            return;
        }
        Location at = echo.get(echoIndex++);
        at.getWorld().spawnParticle(Particle.DUST, at.clone().add(0, 1, 0), 20, 0.25, 0.6, 0.25, 0, new Particle.DustOptions(SHADOW, 1.5F));
        at.getWorld().spawnParticle(Particle.SQUID_INK, at.clone().add(0, 0.2, 0), 3, 0.2, 0.05, 0.2, 0.01);
        for (Player player : fight.players()) {
            if (!echoHit.contains(player.getUniqueId()) && player.getLocation().distanceSquared(at) <= 1.7) {
                echoHit.add(player.getUniqueId());
                Abyss.magic(player, ECHO_DAMAGE, body);
            }
        }
    }

    private void shatter() {
        body.setGlowing(true);
        body.getWorld().playSound(body.getLocation(), Sound.BLOCK_GLASS_BREAK, 2F, 0.5F);
        fight.broadcast("&fThe mirror shatters - &7a reflection hunts each of you. Only you can break your own!");
        for (Player player : fight.players()) {
            Mannequin reflection = fight.spawnAdd(Mannequin.class, player.getLocation().add(player.getLocation().getDirection().setY(0).normalize().multiply(-3)), m -> {
                m.setCustomName(ChatColor.GRAY + player.getName() + "'s reflection");
                m.setCustomNameVisible(true);
                m.setDescription(net.kyori.adventure.text.Component.empty());
                m.setProfile(ResolvableProfile.resolvableProfile(player.getPlayerProfile()));
                dress(m, player);
                BossFight.setAttribute(m, Attribute.MAX_HEALTH, REFLECTION_HEALTH);
                m.setHealth(REFLECTION_HEALTH);
                m.getPersistentDataContainer().set(Keys.OWNED_BY, PersistentDataType.STRING, player.getUniqueId().toString());
            });
            if (reflection != null) {
                reflections.put(reflection, player);
            }
        }
    }

    private void reflectionsAttack(int now) {
        if (now % 20 != 0) {
            return;
        }
        reflections.forEach((reflection, owner) -> {
            if (alive(owner) && reflection.isValid() && owner.getLocation().distanceSquared(reflection.getLocation()) <= 9) {
                reflection.swingMainHand();
                owner.damage(30, reflection);
            }
        });
        if (shattered && liveReflections() == 0 && body.isGlowing() && fight.elapsed() >= reflectingUntil) {
            body.setGlowing(false);
            fight.broadcast("&fEvery reflection is broken - &7the Doppelganger can be hurt again.");
            reflectingUntil = -1;
        }
    }

    /** Takes on a player's face, gear (cosmetic copies) and fighting style. */
    private void become(Player player) {
        body.setProfile(ResolvableProfile.resolvableProfile(player.getPlayerProfile()));
        body.setCustomName(ChatColor.WHITE + "Doppelganger " + ChatColor.GRAY + "(" + player.getName() + ")");
        dress(body, player);
        stance = stanceFor(player);
        body.getWorld().spawnParticle(Particle.REVERSE_PORTAL, body.getLocation().add(0, 1, 0), 30, 0.4, 0.8, 0.4, 0.05);
    }

    /** Same-looking copies (material only): never the player's actual items, enchantments or data. */
    private static void dress(Mannequin mannequin, Player player) {
        EntityEquipment from = player.getEquipment();
        EntityEquipment to = mannequin.getEquipment();
        to.setHelmet(copy(from.getHelmet()));
        to.setChestplate(copy(from.getChestplate()));
        to.setLeggings(copy(from.getLeggings()));
        to.setBoots(copy(from.getBoots()));
        to.setItemInMainHand(copy(from.getItemInMainHand()));
    }

    private static ItemStack copy(ItemStack item) {
        return item == null || item.getType().isAir() ? null : new ItemStack(item.getType());
    }

    private static Stance stanceFor(Player player) {
        ItemStack held = player.getInventory().getItemInMainHand();
        Material type = held.getType();
        if (type == Material.BOW || type == Material.CROSSBOW) {
            return Stance.RANGED;
        }
        // boss/ stays free of the Slimefun API: read the item id Slimefun keeps in the item's data
        String id = held.hasItemMeta() ? held.getItemMeta().getPersistentDataContainer().get(SLIMEFUN_ID, PersistentDataType.STRING) : null;
        if (id != null && (id.endsWith("WYRMBREATH") || id.endsWith("SOULFIRE_CENSER"))) {
            return Stance.FIRE;
        }
        return Stance.MELEE;
    }

    private int liveReflections() {
        int count = 0;
        for (Mannequin reflection : reflections.keySet()) {
            if (reflection.isValid() && !reflection.isDead()) {
                count++;
            }
        }
        return count;
    }

    private static boolean alive(Player player) {
        return player != null && player.isValid() && !player.isDead();
    }
}
