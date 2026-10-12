package io.github.amitelia.occultech.boss.tier0;

import io.github.amitelia.occultech.boss.AirEffects;
import io.github.amitelia.occultech.boss.FloorDecals;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import org.bukkit.ChatColor;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import org.bukkit.entity.ThrownPotion;
import org.bukkit.entity.Witch;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.PotionMeta;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossFight;
import io.papermc.paper.datacomponent.DataComponentTypes;
import io.papermc.paper.datacomponent.item.DyedItemColor;

/**
 * Tier-0 mini-boss (iron gear). Three hedge witches whose roles rotate every 15 seconds, shown by the colour of their
 * brew (docs/art/bosses/witch_coven/overhaul). Each sister has her own body and vessel: the cauldron witch, the bottle
 * witch and the pot witch, each a Mythic carrier with its own model when MythicMobs and BetterModel are installed.
 * <ul>
 * <li>Healer (green): heals the most wounded sister every 4s.</li>
 * <li>Curser (purple): marks the nearest player's spot for 1s, then weakens and slows whoever is still on it.</li>
 * <li>Bomber (red): throws a harming potion every 4s (each sister throws her own thing: a glob, a bottle, a wave).</li>
 * </ul>
 * Each action starts its clip early enough that the clip's release lands on the real moment, and a witch's cast is
 * dropped if she dies or loses the role before it lands. Kill the healer first. Ranged, so the anti-pillar teleport is
 * off.
 */
public final class WitchCoven extends BossBehavior {

    private static final io.github.amitelia.occultech.boss.Mechanic HARMING = io.github.amitelia.occultech.boss.Mechanic.of("WITCH_COVEN", "Potion of Harming", 6, io.github.amitelia.occultech.boss.Mechanic.Kind.MAGIC, true);

    private enum Role {
        HEALER("Healer", ChatColor.GREEN, Color.fromRGB(150, 214, 108)),
        CURSER("Curser", ChatColor.DARK_PURPLE, Color.fromRGB(176, 124, 212)),
        BOMBER("Bomber", ChatColor.RED, Color.fromRGB(220, 112, 88));

        final String title;
        final ChatColor chat;
        final Color color;
        final Particle.DustOptions aura;

        Role(String title, ChatColor chat, Color color) {
            this.title = title;
            this.chat = chat;
            this.color = color;
            this.aura = new Particle.DustOptions(color, 1.3F);
        }
    }

    /** The three sisters: each one's body (the Mythic carrier OCCULTECH_WITCH_COVEN_<SISTER>) and her throwable. */
    private enum Sister {
        CAULDRON("coven_fx_glob"), BOTTLES("coven_fx_bottle"), POT("coven_fx_wave");

        final String throwable;

        Sister(String throwable) {
            this.throwable = throwable;
        }
    }

    private static final int ROTATE_INTERVAL = 300;
    private static final int HEAL_INTERVAL = 80;
    private static final int CURSE_INTERVAL = 100;
    private static final int CURSE_WARNING = 20;
    private static final double CURSE_RADIUS = 1.4;
    private static final int BOMB_INTERVAL = 80;
    /** How long before its moment each clip starts: its release (the strike, the pour, the throw) lands on it. */
    private static final int ROTATE_LEAD = 10;
    private static final int HEAL_LEAD = 15;
    private static final int THROW_LEAD = 15;
    private static final Color GLASS = Color.fromRGB(190, 226, 232);
    private static final Color SPENT = Color.fromRGB(96, 96, 100);

    private final List<Witch> witches = new ArrayList<>();
    private final Map<Witch, Sister> sisters = new HashMap<>();
    /** Harming potions in flight: where each was last seen, and who threw it. */
    private final Map<ThrownPotion, Location> potions = new HashMap<>();
    private final Map<ThrownPotion, Sister> thrownBy = new HashMap<>();
    private int rotation;
    /** Ticks until a witch may start another clip (a glance or a cackle waits for her attacks). */
    private final Map<Witch, Integer> busyUntil = new HashMap<>();

    private Witch healer;
    private LivingEntity patient;
    private int healAt = -1;
    private Witch curser;
    private Location curseMark;
    private int curseAt = -1;
    private Witch bomber;
    private Player throwTarget;
    private int throwAt = -1;

    public WitchCoven(BossFight fight) {
        super(fight);
    }

    @Override
    public void spawn(Location at) {
        Sister[] all = Sister.values();
        for (int i = 0; i < 3; i++) {
            double angle = Math.PI * 2 * i / 3;
            Location spot = at.clone().add(Math.cos(angle) * 2.5, 0, Math.sin(angle) * 2.5);
            Witch witch = fight.spawnBoss(all[i].name(), Witch.class, spot, w -> {
                BossFight.setAttribute(w, Attribute.MAX_HEALTH, 80);
                BossFight.setAttribute(w, Attribute.KNOCKBACK_RESISTANCE, 0.4);
                BossFight.setAttribute(w, Attribute.FOLLOW_RANGE, 24);
                w.setCustomNameVisible(true);
            });
            witches.add(witch);
            sisters.put(witch, all[i]);
        }
        applyRoles(false);
    }

    @Override
    public boolean usesAntiPillar() {
        return false;
    }

    @Override
    public void tick() {
        int now = fight.elapsed();
        List<Witch> fallen = new ArrayList<>();
        witches.removeIf(w -> {
            boolean gone = w.isDead() || !w.isValid();
            if (gone) {
                fallen.add(w);
            }
            return gone;
        });
        for (Witch dead : fallen) {
            sisterFell(dead, now);
        }
        if (witches.isEmpty()) {
            return;
        }
        if (!fallen.isEmpty()) {
            // roles are assigned by position, so a death reshuffles them: keep the names and brews truthful
            applyRoles(false);
        }

        // the role rotation: the strike clip starts ROTATE_LEAD ticks early, the roles change on the strike
        if (now > 0 && (now + ROTATE_LEAD) % ROTATE_INTERVAL == 0) {
            Role[] roles = Role.values();
            for (int i = 0; i < witches.size(); i++) {
                Witch witch = witches.get(i);
                act(witch, "BECOMES_" + roles[(i + rotation + 1) % roles.length].name(), null, now, 30);
            }
            swapStreaks();
        }
        if (now > 0 && now % ROTATE_INTERVAL == 0) {
            rotation++;
            applyRoles(true);
            fight.broadcast("&5The coven shifts its roles!");
        }

        boolean modelled = witches.stream().anyMatch(w -> fight.usesMythicBody(sisters.get(w).name()));
        for (Witch witch : witches) {
            Role role = roleOf(witch);
            if (!fight.usesMythicBody(sisters.get(witch).name())) {
                // without the model the role shows as an aura over her head
                witch.getWorld().spawnParticle(Particle.DUST, witch.getLocation().add(0, 2.4, 0), 4, 0.3, 0.2, 0.3, 0, role.aura);
            } else if (every(20)) {
                AirEffects.burst(fight, vesselSpot(witch), AirEffects.Burst.BUBBLE, role.color, 0.45F);   // her brew bubbles
            }
        }

        heal(now);
        curse(now);
        bomb(now);
        trackPotions();

        // now and then an idle sister cackles
        if (modelled && every(100)) {
            for (Witch witch : witches) {
                if (idle(witch, now) && ThreadLocalRandom.current().nextInt(7) == 0) {
                    act(witch, "CACKLE", null, now, 32);
                }
            }
        }
    }

    // ------------------------------------------------------------------ the three roles

    private void heal(int now) {
        Witch h = withRole(Role.HEALER);
        if (h != null && healAt < 0 && every(HEAL_INTERVAL)) {
            witches.stream()
                .filter(w -> w != h)
                .min(Comparator.comparingDouble(w -> w.getHealth() / w.getAttribute(Attribute.MAX_HEALTH).getValue()))
                .ifPresent(target -> {
                    healer = h;
                    patient = target;
                    healAt = now + HEAL_LEAD;
                    act(h, "HEAL", target, now, 30);
                });
        }
        if (healAt >= 0 && now >= healAt) {
            healAt = -1;
            if (stillHas(healer, Role.HEALER) && patient.isValid() && !patient.isDead()) {
                fight.healBoss(patient, 0.1);
                patient.getWorld().spawnParticle(Particle.HEART, patient.getLocation().add(0, 2.2, 0), 4, 0.3, 0.2, 0.3, 0);
                patient.getWorld().playSound(patient.getLocation(), Sound.ENTITY_WITCH_DRINK, 1F, 1.3F);
                AirEffects.burst(fight, patient.getLocation().add(0, 1.8, 0), AirEffects.Burst.BUBBLE, Role.HEALER.color, 1.2F);
            }
        }
    }

    private void curse(int now) {
        Witch c = withRole(Role.CURSER);
        if (c != null && curseAt < 0 && every(CURSE_INTERVAL)) {
            Player target = fight.nearestPlayer(c.getLocation());
            if (target != null && target.getLocation().distance(c.getLocation()) < 12) {
                // the mark is the ground the player stood on: only whoever is still on it when it lands is cursed
                curser = c;
                curseMark = target.getLocation().clone();
                curseAt = now + CURSE_WARNING;
                fight.telegraph(curseMark, CURSE_RADIUS, CURSE_WARNING, Role.CURSER.color, FloorDecals.Mark.CURSE);
                act(c, "CURSE", target, now, 30);
                if (!fight.usesMythicBody(sisters.get(c).name())) {
                    target.getWorld().spawnParticle(Particle.WITCH, curseMark.clone().add(0, 1, 0), 30, 0.4, 0.8, 0.4, 0);
                    target.playSound(target.getLocation(), Sound.ENTITY_EVOKER_PREPARE_ATTACK, 1F, 1.4F);
                }
            }
        }
        if (curseAt >= 0 && now >= curseAt) {
            curseAt = -1;
            if (!stillHas(curser, Role.CURSER)) {
                return;                                           // she fell or lost the role: the curse fizzles
            }
            Sister sister = sisters.get(curser);
            switch (sister) {
                case CAULDRON -> FloorDecals.splash(fight, curseMark, 1.8, Role.CURSER.color);   // the spill lands
                case BOTTLES -> {
                    AirEffects.burst(fight, curseMark.clone().add(0, 0.6, 0), AirEffects.Burst.SHARDS, GLASS, 1.4F);
                    AirEffects.burst(fight, curseMark.clone().add(0, 0.4, 0), AirEffects.Burst.DROPLETS, Role.CURSER.color, 1.6F);
                }
                case POT -> FloorDecals.splash(fight, curseMark, 2.0, Role.CURSER.color);        // the poured puddle
            }
            double reach = CURSE_RADIUS + 0.3;
            for (Player player : fight.players()) {
                Location at = player.getLocation();
                if (at.getWorld() == curseMark.getWorld() && Math.abs(at.getY() - curseMark.getY()) < 2
                    && Math.hypot(at.getX() - curseMark.getX(), at.getZ() - curseMark.getZ()) <= reach) {
                    player.addPotionEffect(new PotionEffect(PotionEffectType.WEAKNESS, 100, 0));
                    player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 60, 0));
                }
            }
        }
    }

    private void bomb(int now) {
        Witch b = withRole(Role.BOMBER);
        if (b != null && throwAt < 0 && every(BOMB_INTERVAL)) {
            Player target = fight.nearestPlayer(b.getLocation());
            if (target != null) {
                bomber = b;
                throwTarget = target;
                throwAt = now + THROW_LEAD;
                act(b, "THROW", target, now, 30);
            }
        }
        if (throwAt >= 0 && now >= throwAt) {
            throwAt = -1;
            if (stillHas(bomber, Role.BOMBER) && throwTarget.isValid() && fight.players().contains(throwTarget)) {
                lob(bomber, throwTarget);
            }
        }
    }

    /** Each potion's burst where it broke, in the look of whatever she threw. */
    private void trackPotions() {
        potions.entrySet().removeIf(entry -> {
            if (entry.getKey().isValid()) {
                entry.setValue(entry.getKey().getLocation());
                return false;
            }
            Location at = entry.getValue();
            Sister sister = thrownBy.remove(entry.getKey());
            FloorDecals.splash(fight, at, sister == Sister.POT ? 3.2 : 2.5, Role.BOMBER.color);
            Location air = at.clone().add(0, 0.4, 0);
            if (sister == Sister.BOTTLES) {
                AirEffects.burst(fight, air, AirEffects.Burst.SHARDS, GLASS, 1.8F);
                AirEffects.burst(fight, air, AirEffects.Burst.DROPLETS, Role.BOMBER.color, 2.0F);
            } else if (sister == Sister.POT) {
                AirEffects.burst(fight, air, AirEffects.Burst.SPLASH, Role.BOMBER.color, 2.8F);
                AirEffects.burst(fight, air, AirEffects.Burst.DROPLETS, Role.BOMBER.color, 2.4F);
            } else {
                AirEffects.burst(fight, air, AirEffects.Burst.DROPLETS, Role.BOMBER.color, 2.2F);
            }
            return true;
        });
    }

    private void lob(Witch thrower, Player target) {
        ItemStack potion = new ItemStack(Material.SPLASH_POTION);
        PotionMeta meta = (PotionMeta) potion.getItemMeta();
        meta.addCustomEffect(new PotionEffect(PotionEffectType.INSTANT_DAMAGE, 1, 0), true);
        Sister sister = sisters.get(thrower);
        if (AirEffects.enabled() && sister != null) {
            // still a real splash potion; it only looks like what she throws (her glob, bottle or wave, dyed red)
            meta.setItemModel(new NamespacedKey("occultech", sister.throwable));
        }
        potion.setItemMeta(meta);
        if (AirEffects.enabled() && sister != null) {
            potion.setData(DataComponentTypes.DYED_COLOR, DyedItemColor.dyedItemColor(Role.BOMBER.color));
        }

        Vector velocity = target.getLocation().toVector().subtract(thrower.getLocation().toVector());
        double distance = velocity.length();
        velocity.normalize().multiply(Math.min(1.1, 0.35 + distance * 0.06)).setY(0.35 + distance * 0.02);
        ThrownPotion thrown = thrower.launchProjectile(ThrownPotion.class, velocity);
        thrown.setItem(potion);
        fight.label(thrown, HARMING);
        potions.put(thrown, thrown.getLocation());
        if (sister != null) {
            thrownBy.put(thrown, sister);
        }
        if (!fight.usesMythicBody(sister == null ? "" : sister.name())) {
            thrower.getWorld().playSound(thrower.getLocation(), Sound.ENTITY_WITCH_THROW, 1F, 1F);
        }
    }

    // ------------------------------------------------------------------ the coven's moments

    @Override
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {
        if (boss instanceof Witch witch && sisters.containsKey(witch)) {
            act(witch, "FLINCH", null, fight.elapsed(), 0);
        }
    }

    /** A sister falls: her brew spills and goes dull, her hat drops beside her, the others turn and look. */
    private void sisterFell(Witch dead, int now) {
        Sister sister = sisters.remove(dead);
        Location at = dead.getLocation();
        if (sister == null) {
            return;
        }
        FloorDecals.splash(fight, at, 1.6, SPENT);
        if (AirEffects.enabled()) {
            ItemStack hat = new ItemStack(Material.PAPER);
            org.bukkit.inventory.meta.ItemMeta meta = hat.getItemMeta();
            meta.setItemModel(new NamespacedKey("occultech", "coven_fx_hat"));
            hat.setItemMeta(meta);
            float yaw = ThreadLocalRandom.current().nextFloat() * 6.28F;
            Vector side = new Vector(Math.cos(yaw), 0, Math.sin(yaw)).multiply(1.1);
            fight.spawnExtra(ItemDisplay.class, at.clone().add(side).add(0, 0.35, 0), d -> {
                d.setItemStack(hat);
                d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
                d.setShadowRadius(0F);
                d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(yaw, 0F, 1F, 0F),
                    new Vector3f(1F, 1F, 1F), new AxisAngle4f(1.2F, 0F, 0F, 1F)));   // lying on its side
                d.setBrightness(new Display.Brightness(10, 12));
            });
        }
        if (dead == healer) {
            healAt = -1;
        }
        if (dead == curser) {
            curseAt = -1;
        }
        if (dead == bomber) {
            throwAt = -1;
        }
        for (Witch survivor : witches) {
            if (idle(survivor, now)) {
                Vector look = at.toVector().subtract(survivor.getLocation().toVector());
                Location face = survivor.getLocation().setDirection(look);
                survivor.setRotation(face.getYaw(), 0F);
                act(survivor, "GLANCE", null, now, 30);
            }
        }
    }

    /** The streak of the new colours that runs from each sister to the next as the roles swap. */
    private void swapStreaks() {
        if (!AirEffects.enabled() || witches.size() < 2) {
            return;
        }
        Role[] roles = Role.values();
        for (int i = 0; i < witches.size(); i++) {
            Location from = witches.get(i).getLocation().add(0, 2.0, 0);
            Location to = witches.get((i + 1) % witches.size()).getLocation().add(0, 2.0, 0);
            Role next = roles[(i + rotation + 1) % roles.length];
            AirEffects.Streak streak = AirEffects.Streak.create(fight, "air_beam", from, to, next.color, 0.18F);
            org.bukkit.Bukkit.getScheduler().runTaskLater(org.bukkit.Bukkit.getPluginManager().getPlugin("Occultech"),
                () -> streak.fire(from, to), 8L);
        }
    }

    // ------------------------------------------------------------------ helpers

    /** Plays her clip and its look (the Mythic skill WITCH_COVEN_<SISTER>_<ACTION>), keeping her busy a while. */
    private void act(Witch witch, String action, LivingEntity target, int now, int busyTicks) {
        Sister sister = sisters.get(witch);
        if (sister == null) {
            return;
        }
        fight.playAction(witch, sister.name() + "_" + action, target);
        if (busyTicks > 0) {
            busyUntil.put(witch, now + busyTicks);
        }
    }

    private boolean idle(Witch witch, int now) {
        return busyUntil.getOrDefault(witch, -1) < now;
    }

    /** Above her vessel: the cauldron on her back, the bottles at her chest, the pot held out in front. */
    private Location vesselSpot(Witch witch) {
        Location at = witch.getLocation();
        Vector facing = at.getDirection().setY(0);
        if (facing.lengthSquared() < 1e-4) {
            facing = new Vector(0, 0, 1);
        }
        facing.normalize();
        return switch (sisters.get(witch)) {
            case CAULDRON -> at.clone().add(facing.multiply(-0.9)).add(0, 2.5, 0);
            case BOTTLES -> at.clone().add(facing.multiply(0.4)).add(0, 1.9, 0);
            case POT -> at.clone().add(facing.multiply(0.9)).add(0, 1.6, 0);
        };
    }

    private boolean stillHas(Witch witch, Role role) {
        return witch != null && witch.isValid() && !witch.isDead() && witches.contains(witch) && roleOf(witch) == role;
    }

    /** Names (and, on a death or a resume, the brews at once) follow the roles. {@code rotated}: the strike clip has
     * already tinted the brews. */
    private void applyRoles(boolean rotated) {
        Role[] roles = Role.values();
        for (int i = 0; i < witches.size(); i++) {
            Witch witch = witches.get(i);
            Role role = roles[(i + rotation) % roles.length];
            witch.setCustomName(role.chat + "Coven " + role.title);
            if (!rotated) {
                Sister sister = sisters.get(witch);
                if (sister != null) {
                    fight.playAction(witch, sister.name() + "_IS_" + role.name());
                }
            }
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
}
