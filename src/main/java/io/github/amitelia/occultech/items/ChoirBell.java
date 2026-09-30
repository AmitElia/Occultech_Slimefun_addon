package io.github.amitelia.occultech.items;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import io.github.amitelia.occultech.core.Keys;
import io.github.thebusybiscuit.slimefun4.api.items.ItemGroup;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItemStack;
import io.github.thebusybiscuit.slimefun4.api.recipes.RecipeType;
import io.github.thebusybiscuit.slimefun4.core.handlers.ItemUseHandler;

/**
 * Choir Bell (talisman): ring it for a burning shockwave around you (7 blocks). Summoned creatures and hostile mobs are
 * burned, hurt and knocked back; bosses shrug off the knockback but are slowed. Never affects players, pets or minions.
 * 20s cooldown, 1 durability per ring.
 */
public class ChoirBell extends OccultItem {

    private static final double RADIUS = 7;
    private static final long COOLDOWN_MS = 20_000;

    private final Map<UUID, Long> cooldowns = new HashMap<>();

    public ChoirBell(ItemGroup group, SlimefunItemStack item, RecipeType type, ItemStack[] recipe, ItemStack output) {
        super(group, item, type, recipe, output);

        addItemHandler((ItemUseHandler) e -> {
            e.cancel();
            Player player = e.getPlayer();
            long now = System.currentTimeMillis();
            long ready = cooldowns.getOrDefault(player.getUniqueId(), 0L);
            if (now < ready) {
                player.sendMessage(ChatColor.GRAY + "The bell still hums (" + ((ready - now) / 1000 + 1) + "s).");
                return;
            }
            if (!BoneScepter.useDurability(e.getItem())) {
                player.sendMessage(ChatColor.RED + "The bell is cracked. Repair it with a ritual.");
                return;
            }
            cooldowns.put(player.getUniqueId(), now + COOLDOWN_MS);
            ring(player);
        });
    }

    private static void ring(Player player) {
        Location center = player.getLocation();
        player.getWorld().playSound(center, Sound.BLOCK_BELL_USE, 2F, 0.8F);
        player.getWorld().playSound(center, Sound.BLOCK_BELL_RESONATE, 1F, 1F);
        for (double r = 1; r <= RADIUS; r += 1.5) {
            for (int i = 0; i < 24; i++) {
                double angle = Math.PI * 2 * i / 24;
                player.getWorld().spawnParticle(Particle.FLAME, center.clone().add(Math.cos(angle) * r, 0.3, Math.sin(angle) * r), 1, 0, 0.05, 0, 0.01);
            }
        }
        for (Entity entity : player.getNearbyEntities(RADIUS, 4, RADIUS)) {
            if (!(entity instanceof LivingEntity target) || entity instanceof Player || Keys.minionOwner(entity) != null) {
                continue;
            }
            boolean summoned = Keys.isSummoned(entity);
            if (!summoned && !(entity instanceof Monster)) {
                continue;
            }
            target.damage(6, player);
            target.setFireTicks(Math.max(target.getFireTicks(), 60));
            boolean boss = summoned && target.getAttribute(org.bukkit.attribute.Attribute.MAX_HEALTH).getValue() >= 150;
            if (boss) {
                target.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 40, 2));
            } else {
                Vector push = target.getLocation().toVector().subtract(center.toVector()).setY(0);
                if (push.lengthSquared() > 0.01) {
                    target.setVelocity(push.normalize().multiply(1.2).setY(0.4));
                }
            }
        }
    }
}
