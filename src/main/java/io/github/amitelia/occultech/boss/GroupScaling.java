package io.github.amitelia.occultech.boss;

/**
 * How much tankier a boss is for a group (Session B2): health x {@code 1 + scaling * (n - 1)^exponent}, counting at most
 * {@code cap} players. The curve flattens, so every player added helps the group more than the boss: a group always
 * kills faster than a solo player, and a large group stops making the boss any tankier. Pure Java, unit tested.
 * Defaults (the chosen "tougher" curve): x1.45 / 1.76 / 2.03 / 2.27 for 2-5 players.
 */
public record GroupScaling(double scaling, double exponent, int cap) {

    public static final GroupScaling DEFAULT = new GroupScaling(0.45, 0.75, 5);

    public GroupScaling {
        scaling = Math.max(0, scaling);
        exponent = Math.max(0.1, Math.min(1, exponent));
        cap = Math.max(1, cap);
    }

    /** The health factor for {@code players} at the summon (1 for a solo player). */
    public double factor(int players) {
        int counted = Math.max(1, Math.min(cap, players));
        return 1 + scaling * Math.pow(counted - 1, exponent);
    }
}
