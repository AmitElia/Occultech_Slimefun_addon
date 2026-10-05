package io.github.amitelia.occultech.boss;

import javax.annotation.Nonnull;

/**
 * What a hit does to a player in a tier's benchmark kit (Session B1), by the 26.2 game's own rules (read from its
 * {@code CombatRules}): armor cuts {@code clamp(armor - damage / (2 + toughness / 4), armor / 5, 20) / 25}, Protection
 * cuts {@code min(points, 20) / 25} (four Protection V pieces are already at the cap), Resistance 20% per level. Mob
 * damage is also scaled by the world's difficulty (Hard x1.5). Pure Java, unit tested.
 */
public final class ArmorModel {

    /** A tier's benchmark gear. {@code protection} is the sum of Protection levels over the four pieces. */
    public record Kit(String name, double armor, double toughness, int protection, int resistance, double health) {}

    public static final Kit TIER_0 = new Kit("iron, Protection II", 15, 0, 8, 0, 20);
    public static final Kit TIER_1 = new Kit("diamond, Protection IV", 20, 8, 16, 0, 20);
    public static final Kit TIER_2 = new Kit("netherite, Protection IV", 20, 12, 16, 0, 20);
    public static final Kit TIER_3 = new Kit("Infinity (netherite, Protection XX, Resistance I)", 20, 12, 80, 1, 20);

    /** Share of health a hit should take, by kind: difficult but manageable for every player, not only the best (Session B2). */
    public record Band(double min, double max) {
        public boolean contains(double share) {
            return share >= min && share <= max;
        }
    }

    private ArmorModel() {}

    @Nonnull
    public static Kit kit(int tier) {
        return switch (tier) {
            case 0 -> TIER_0;
            case 1 -> TIER_1;
            case 2 -> TIER_2;
            default -> TIER_3;
        };
    }

    /** Damage left after armor, Protection, Resistance and difficulty. */
    public static double after(double raw, boolean ignoresArmor, @Nonnull Kit kit, double difficulty) {
        double damage = raw * difficulty;
        if (!ignoresArmor) {
            double toughness = 2 + kit.toughness() / 4;
            double cut = Math.max(kit.armor() * 0.2, Math.min(20, kit.armor() - damage / toughness)) / 25;
            damage *= 1 - cut;
        }
        damage *= 1 - Math.min(20, kit.protection()) / 25.0;
        damage *= Math.max(0, 1 - 0.2 * kit.resistance());
        return damage;
    }

    /** The share of the kit's health one hit of {@code mechanic} takes. */
    public static double share(@Nonnull Mechanic mechanic, @Nonnull Kit kit, double difficulty) {
        return after(mechanic.damage(), mechanic.ignoresArmor(), kit, difficulty) / kit.health();
    }

    /** The band a mechanic should land in. */
    @Nonnull
    public static Band band(@Nonnull Mechanic mechanic) {
        return switch (mechanic.kind()) {
            case ADD -> new Band(0.03, 0.10);
            case ZONE -> new Band(0.02, 0.08);
            default -> mechanic.telegraphed() ? new Band(0.12, 0.30) : new Band(0.08, 0.18);
        };
    }
}
