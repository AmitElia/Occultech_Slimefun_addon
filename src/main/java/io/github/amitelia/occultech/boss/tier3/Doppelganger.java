package io.github.amitelia.occultech.boss.tier3;

import io.github.amitelia.occultech.boss.FloorDecals;

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
 * <li>Echo: it remembers where its target walked for 5s. The path is marked on the floor, then a dark copy of the
 * Doppelganger runs it and strikes whoever is on it as it passes. Standing still or retracing your steps is
 * punished (Session R5: it used to be a particle cloud that had to meet you exactly at a sampled point).</li>
 * <li>Reflection: it glows white for 3s; hits taken then do nothing and are partly thrown back. Stop attacking.</li>
 * <li>Shattered mirror at half health: one reflection per player, each wearing that player's face. Only its owner can
 * break it, and the Doppelganger can't be hurt until every reflection is gone.</li>
 * </ul>
 * It carries the copied player's exact name, so nothing tells it apart from the real one. A Mannequin has no AI, so
 * this script moves it. Takes a tenth of the damage dealt.
 */
public final class Doppelganger extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic REFLECT = io.github.amitelia.occultech.boss.Mechanic.of("DOPPELGANGER", "Reflected damage", 22, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, false);
    private static final io.github.amitelia.occultech.boss.Mechanic REFLECTION = io.github.amitelia.occultech.boss.Mechanic.of("DOPPELGANGER", "Reflection's blow", 41, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);

    private static final double HEALTH = 260;
    private static final double ARMOR = 0.1;
    private static final io.github.amitelia.occultech.boss.Mechanic MELEE_HIT = io.github.amitelia.occultech.boss.Mechanic.of("DOPPELGANGER", "Mirrored blow", 39, io.github.amitelia.occultech.boss.Mechanic.Kind.MELEE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic ARROW_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DOPPELGANGER", "Mirrored arrow", 38, io.github.amitelia.occultech.boss.Mechanic.Kind.PROJECTILE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic FIRE_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.piercing("DOPPELGANGER", "Mirrored fire", 10, io.github.amitelia.occultech.boss.Mechanic.Kind.ZONE, false);
    private static final io.github.amitelia.occultech.boss.Mechanic ECHO_DAMAGE = io.github.amitelia.occultech.boss.Mechanic.of("DOPPELGANGER", "Echo", 34, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);
    private static final double REFLECT_SHARE = 0.3;
    private static final double REFLECTION_HEALTH = 60;
    private static final int ECHO_SAMPLES = 20;
    private static final Color SHADOW = Color.fromRGB(30, 20, 40);
    /** The marked path shows this long before the dark copy runs it. */
    private static final int ECHO_WARNING = 30;
    private static final double ECHO_REACH = 1.6;
    private static final double ECHO_SPEED = 0.45;
    /** The dark copy skips ahead to a point it hasn't reached in this many ticks (blocked, or a point taken mid-jump). */
    private static final int ECHO_POINT_TICKS = 20;

    private enum Stance { MELEE, RANGED, FIRE }

    private static final org.bukkit.NamespacedKey SLIMEFUN_ID = new org.bukkit.NamespacedKey("slimefun", "slimefun_item");

    private Mannequin body;
    private Player target;
    private Stance stance = Stance.MELEE;
    private int nextMelee;
    private final Deque<Location> trail = new ArrayDeque<>();
    private List<Location> echo = List.of();
    private int echoIndex = -1;
    /** Ticks the dark copy has spent heading for its current point, and the tick its run must be over by. */
    private int shadeStepTicks;
    private int shadeDeadline;
    private int echoStart = -1;
    @javax.annotation.Nullable private Mannequin shade;
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
            fight.hit(player, REFLECT, Math.min(REFLECT.damage(), lastIncoming * REFLECT_SHARE), body);
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
        runShade();
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

        if (every(300) && echoIndex < 0 && echoStart < 0 && trail.size() >= ECHO_SAMPLES / 2) {
            echo = new ArrayList<>(trail);
            echoStart = now + ECHO_WARNING;
            for (int i = 0; i < echo.size(); i += 2) {
                FloorDecals.patch(fight, echo.get(i), 0.9, ECHO_WARNING + echo.size() * 3 + 20, FloorDecals.Zone.SHADOW);
            }
            echoHit.clear();
            fight.broadcast("&8Your echo is about to walk again - &fget off the dark path.");
        }
        if (echoStart >= 0 && now >= echoStart) {
            echoStart = -1;
            summonShade(target);
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
                    fight.hit(target, MELEE_HIT, body);
                }
            }
            case RANGED -> {
                if (every(30)) {
                    Vector aim = target.getEyeLocation().toVector().subtract(body.getEyeLocation().toVector()).normalize().multiply(2.4);
                    Arrow arrow = body.launchProjectile(Arrow.class, aim);
                    arrow.getPersistentDataContainer().set(Keys.DAMAGE, PersistentDataType.DOUBLE, ARROW_DAMAGE.damage());
            fight.label(arrow, ARROW_DAMAGE);
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
                            fight.hit(player, FIRE_DAMAGE, body);
                            player.setFireTicks(Math.max(player.getFireTicks(), 60));
                        }
                    }
                }
            }
        }
    }

    /**
     * The echo: a dark copy of the Doppelganger - the same face, in black, with a dark outline and trailing smoke -
     * appears at the start of the marked path and runs it. It can't be hurt, and it's gone at the end of the path.
     */
    private void summonShade(@javax.annotation.Nullable Player copied) {
        if (echo.isEmpty()) {
            return;
        }
        Location start = echo.get(0).clone();
        shade = fight.spawnExtra(Mannequin.class, start, m -> {
            m.setCustomNameVisible(false);
            m.setDescription(net.kyori.adventure.text.Component.empty());
            if (copied != null) {
                m.setProfile(ResolvableProfile.resolvableProfile(copied.getPlayerProfile()));
            }
            EntityEquipment gear = m.getEquipment();
            gear.setChestplate(dark(Material.LEATHER_CHESTPLATE));
            gear.setLeggings(dark(Material.LEATHER_LEGGINGS));
            gear.setBoots(dark(Material.LEATHER_BOOTS));
            m.setInvulnerable(true);
            Keys.setUnhittable(m, true);
            m.setGlowing(true);
            shadeTeam().addEntity(m);
        });
        echoIndex = 1;
        shadeStepTicks = 0;
        shadeDeadline = fight.elapsed() + echo.size() * ECHO_POINT_TICKS + 40;   // it never outstays its path
        start.getWorld().playSound(start, Sound.ENTITY_WARDEN_SONIC_CHARGE, 1.5F, 1.6F);
    }

    /** Self-test: the dark copy runs this path now. */
    public void echoForTest(List<Location> path) {
        echo = new ArrayList<>(path);
        echoHit.clear();
        summonShade(null);
    }

    /** Self-test: whether the dark copy is out. */
    public boolean shadeActive() {
        return shade != null;
    }

    /** Every tick: the dark copy runs the path, striking whoever it passes (once each). */
    private void runShade() {
        if (shade == null) {
            return;
        }
        if (!shade.isValid() || echoIndex < 0 || echoIndex >= echo.size() || fight.elapsed() > shadeDeadline) {
            if (shade.isValid()) {
                shade.getWorld().spawnParticle(Particle.LARGE_SMOKE, shade.getLocation().add(0, 1, 0), 20, 0.3, 0.6, 0.3, 0.02);
                shade.remove();
            }
            shade = null;
            echoIndex = -1;
            return;
        }
        Location next = echo.get(echoIndex);
        Location here = shade.getLocation();
        double dx = next.getX() - here.getX();
        double dz = next.getZ() - here.getZ();
        if (dx * dx + dz * dz < 0.8) {   // reached, by its feet on the floor: the point may be from mid-jump, or a step up
            echoIndex++;
            shadeStepTicks = 0;
        } else if (++shadeStepTicks > ECHO_POINT_TICKS) {
            // stuck on the way (a wall, a ledge): on to the point, so the run always finishes
            shade.teleport(next);
            echoIndex++;
            shadeStepTicks = 0;
        } else {
            Abyss.walk(shade, next, ECHO_SPEED, 0);
        }
        Location at = shade.getLocation();
        at.getWorld().spawnParticle(Particle.SQUID_INK, at.clone().add(0, 0.3, 0), 2, 0.2, 0.1, 0.2, 0.01);
        at.getWorld().spawnParticle(Particle.LARGE_SMOKE, at.clone().add(0, 1.2, 0), 1, 0.2, 0.4, 0.2, 0.01);
        for (Player player : fight.players()) {
            if (!echoHit.contains(player.getUniqueId()) && player.getLocation().distanceSquared(at) <= ECHO_REACH * ECHO_REACH) {
                echoHit.add(player.getUniqueId());
                shade.swingMainHand();
                fight.hit(player, ECHO_DAMAGE, body);
            }
        }
    }

    private static ItemStack dark(Material leather) {
        ItemStack item = new ItemStack(leather);
        org.bukkit.inventory.meta.LeatherArmorMeta meta = (org.bukkit.inventory.meta.LeatherArmorMeta) item.getItemMeta();
        meta.setColor(Color.fromRGB(16, 12, 22));
        item.setItemMeta(meta);
        return item;
    }

    /** A scoreboard team only for the outline colour of the dark copy. */
    private static org.bukkit.scoreboard.Team shadeTeam() {
        org.bukkit.scoreboard.Scoreboard board = org.bukkit.Bukkit.getScoreboardManager().getMainScoreboard();
        org.bukkit.scoreboard.Team team = board.getTeam("occultech_shade");
        if (team == null) {
            team = board.registerNewTeam("occultech_shade");
            team.color(net.kyori.adventure.text.format.NamedTextColor.DARK_PURPLE);
        }
        return team;
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
                fight.hit(owner, REFLECTION, reflection);
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
        // exactly the player's name, like their own name tag: nothing tells the copy from the real one
        body.customName(net.kyori.adventure.text.Component.text(player.getName()));
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
