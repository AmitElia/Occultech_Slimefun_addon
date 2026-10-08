package io.github.amitelia.occultech.debug;

import io.github.amitelia.occultech.Occultech;
import io.github.amitelia.occultech.boss.ArmorModel;
import io.github.amitelia.occultech.boss.BossBlueprint;
import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import io.github.thebusybiscuit.slimefun4.implementation.Slimefun;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.bukkit.Bukkit;
import org.bukkit.Difficulty;
import org.bukkit.Material;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

/**
 * Session B1 balancing tools: the benchmark kits ({@code /occultech kit <tier>}) and the mechanics report
 * ({@code /occultech balance}), which grades every boss attack against its tier's benchmark armor.
 */
final class Balance {

    private Balance() {}

    // ------------------------------------------------------------------ report

    /** One graded attack. */
    record Grade(Mechanic mechanic, int tier, double share, ArmorModel.Band band) {
        boolean ok() {
            return band.contains(share);
        }
    }

    /** Every declared attack of every registered boss, graded (bosses in tier order). */
    static List<Grade> grades(Occultech plugin, double difficulty) {
        var bosses = plugin.rituals().bosses();
        bosses.blueprints().forEach(BossBlueprint::load);
        io.github.amitelia.occultech.event.RaidService.loadMechanics();
        List<Grade> out = new ArrayList<>();
        for (Mechanic mechanic : Mechanic.all()) {
            BossSpec spec = plugin.rituals().spec(mechanic.bossId()).orElse(null);
            int tier;
            if (spec != null) {
                tier = spec.tier();
            } else if (io.github.amitelia.occultech.event.RaidService.isRaid(mechanic.bossId())) {
                tier = io.github.amitelia.occultech.event.RaidService.BENCHMARK_TIER;   // the Staff Raid: max-enchanted netherite
            } else {
                continue;
            }
            ArmorModel.Kit kit = ArmorModel.kit(tier);
            out.add(new Grade(mechanic, tier, ArmorModel.share(mechanic, kit, difficulty), ArmorModel.band(mechanic, tier)));
        }
        out.sort((a, b) -> a.tier() != b.tier() ? Integer.compare(a.tier(), b.tier()) : a.mechanic().bossId().compareTo(b.mechanic().bossId()));
        return out;
    }

    static double difficulty() {
        Difficulty difficulty = Bukkit.getWorlds().get(0).getDifficulty();
        return switch (difficulty) {
            case PEACEFUL -> 0;
            case EASY -> 0.5;
            case NORMAL -> 1;
            case HARD -> 1.5;
        };
    }

    /** Writes {@code balance-report.md} in the plugin folder; returns the number of attacks outside their band. */
    static int report(Occultech plugin, List<String> lines) {
        double difficulty = difficulty();
        List<Grade> grades = grades(plugin, difficulty);
        StringBuilder md = new StringBuilder("# Boss attacks against benchmark gear\n\n");
        md.append(String.format(Locale.ROOT, "Difficulty factor %.1f. Share = health one hit takes after armor (20 HP).%n%n", difficulty));
        md.append("| Tier | Boss | Attack | Kind | Telegraphed | Raw | Share | Band | |\n|---|---|---|---|---|---|---|---|---|\n");
        int off = 0;
        for (Grade g : grades) {
            Mechanic m = g.mechanic();
            if (!g.ok()) {
                off++;
            }
            md.append(String.format(Locale.ROOT, "| %d | %s | %s | %s%s | %s | %.1f | %.0f%% | %.0f-%.0f%% | %s |%n", g.tier(), m.bossId(), m.name(),
                m.kind().name().toLowerCase(), m.ignoresArmor() ? " (pierces armor)" : "", m.telegraphed() ? "yes" : "no", m.damage(),
                g.share() * 100, g.band().min() * 100, g.band().max() * 100, g.ok() ? "ok" : (g.share() > g.band().max() ? "TOO HIGH" : "too low")));
        }
        File file = new File(plugin.getDataFolder(), "balance-report.md");
        try {
            Files.writeString(file.toPath(), md.toString(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            lines.add("Could not write " + file + ": " + e);
        }
        lines.add(grades.size() + " boss attacks graded, " + off + " outside their band. Full table: " + file.getPath());
        for (Grade g : grades) {
            if (!g.ok()) {
                lines.add(String.format(Locale.ROOT, "  T%d %s - %s: %.0f%% (want %.0f-%.0f%%)", g.tier(), g.mechanic().bossId(), g.mechanic().name(),
                    g.share() * 100, g.band().min() * 100, g.band().max() * 100));
            }
        }
        return off;
    }

    // ------------------------------------------------------------------ benchmark kits

    /** Gives {@code player} the benchmark kit of {@code tier} (see docs/balance-plan.md). */
    static void kit(Player player, int tier) {
        List<ItemStack> items = new ArrayList<>();
        switch (tier) {
            case 0 -> {
                armor(items, "IRON", 2);
                items.add(weapon(Material.IRON_SWORD, Enchantment.SHARPNESS, 2));
                items.add(weapon(Material.BOW, Enchantment.POWER, 2));
                items.add(new ItemStack(Material.GOLDEN_APPLE, 2));
            }
            case 1 -> {
                armor(items, "DIAMOND", 4);
                items.add(weapon(Material.DIAMOND_SWORD, Enchantment.SHARPNESS, 5));
                items.add(weapon(Material.BOW, Enchantment.POWER, 4));
                items.add(new ItemStack(Material.GOLDEN_APPLE, 4));
            }
            case 2 -> {
                armor(items, "NETHERITE", 4);
                items.add(weapon(Material.NETHERITE_SWORD, Enchantment.SHARPNESS, 5));
                items.add(weapon(Material.BOW, Enchantment.POWER, 5));
                items.add(new ItemStack(Material.GOLDEN_APPLE, 6));
                items.add(new ItemStack(Material.ENCHANTED_GOLDEN_APPLE, 1));
            }
            default -> {
                for (String piece : List.of("INFINITY_HELMET", "INFINITY_CHESTPLATE", "INFINITY_LEGGINGS", "INFINITY_BOOTS", "INFINITY_SWORD", "INFINITY_BOW")) {
                    ItemStack infinity = infinity(piece);
                    if (infinity == null) {
                        player.sendMessage("InfinityExpansion2's " + piece + " isn't installed - giving no stand-in for it.");
                    } else {
                        items.add(infinity);
                    }
                }
                items.add(new ItemStack(Material.GOLDEN_APPLE, 8));
                items.add(new ItemStack(Material.ENCHANTED_GOLDEN_APPLE, 2));
            }
        }
        items.add(new ItemStack(Material.SHIELD));
        items.add(new ItemStack(Material.ARROW, 64));
        items.add(new ItemStack(Material.COOKED_BEEF, 32));
        for (ItemStack rest : player.getInventory().addItem(items.toArray(new ItemStack[0])).values()) {
            player.getWorld().dropItem(player.getLocation(), rest);
        }
        player.sendMessage("Benchmark kit for tier " + tier + " given (docs/balance-plan.md).");
    }

    private static void armor(List<ItemStack> items, String material, int protection) {
        for (String piece : List.of("HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS")) {
            ItemStack item = new ItemStack(Material.valueOf(material + "_" + piece));
            item.addUnsafeEnchantment(Enchantment.PROTECTION, protection);
            item.addUnsafeEnchantment(Enchantment.UNBREAKING, 3);
            items.add(item);
        }
    }

    private static ItemStack weapon(Material type, Enchantment enchantment, int level) {
        ItemStack item = new ItemStack(type);
        ItemMeta meta = item.getItemMeta();
        meta.addEnchant(enchantment, level, true);
        meta.addEnchant(Enchantment.UNBREAKING, 3, true);
        item.setItemMeta(meta);
        return item;
    }

    /** An InfinityExpansion2 item by the end of its Slimefun id (the addon may prefix its ids). */
    private static ItemStack infinity(String id) {
        SlimefunItem exact = SlimefunItem.getById(id);
        if (exact != null) {
            return exact.getItem().clone();
        }
        for (SlimefunItem item : Slimefun.getRegistry().getEnabledSlimefunItems()) {
            if (item.getId().endsWith("_" + id) || item.getId().endsWith(id)) {
                return item.getItem().clone();
            }
        }
        return null;
    }
}
