package io.github.amitelia.occultech.ritual;

import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Finds the ritual matching what is on the altar and in the bowls. Pure Java so it can be unit tested.
 * <p>
 * Rules: the center item must match exactly (one item), or the altar must be empty for rituals without a center
 * (mini-boss summons). Every offering needs its own bowl holding at least the required amount, and every bowl not
 * used by the recipe must be empty (so nothing is consumed by surprise).
 */
public final class RitualMatcher {

    /** What one bowl holds; key is null for an empty bowl. */
    public record Bowl(@Nullable String key, int amount) {

        public static final Bowl EMPTY = new Bowl(null, 0);

        public boolean isEmpty() {
            return key == null || amount <= 0;
        }
    }

    /**
     * @param bowlAmounts how much to take from each bowl, same order as the input bowls
     */
    public record Match(@Nonnull RitualRecipe recipe, @Nonnull int[] bowlAmounts) {}

    private RitualMatcher() {}

    @Nonnull
    public static Optional<Match> match(@Nonnull Collection<RitualRecipe> recipes, @Nullable String centerKey, @Nonnull List<Bowl> bowls, int circleTier) {
        return match(recipes, centerKey, null, bowls, circleTier);
    }

    /**
     * @param altarId the altar block's own id, for in-place upgrade rituals (which need an empty altar slot)
     */
    @Nonnull
    public static Optional<Match> match(@Nonnull Collection<RitualRecipe> recipes, @Nullable String centerKey, @Nullable String altarId,
        @Nonnull List<Bowl> bowls, int circleTier) {
        for (RitualRecipe recipe : recipes) {
            boolean centerMatches;
            if (recipe.inPlace()) {
                centerMatches = centerKey == null && recipe.center() != null && recipe.center().equals(altarId);
            } else {
                centerMatches = recipe.center() == null ? centerKey == null : recipe.center().equals(centerKey);
            }
            if (recipe.circle() <= circleTier && centerMatches) {
                int[] take = assign(recipe, bowls);
                if (take != null) {
                    return Optional.of(new Match(recipe, take));
                }
            }
        }
        return Optional.empty();
    }

    @Nullable
    private static int[] assign(RitualRecipe recipe, List<Bowl> bowls) {
        int[] take = new int[bowls.size()];
        boolean[] used = new boolean[bowls.size()];

        for (Map.Entry<String, Integer> offering : recipe.offerings().entrySet()) {
            int found = -1;
            for (int i = 0; i < bowls.size(); i++) {
                Bowl bowl = bowls.get(i);
                if (!used[i] && !bowl.isEmpty() && bowl.key().equals(offering.getKey()) && bowl.amount() >= offering.getValue()) {
                    found = i;
                    break;
                }
            }
            if (found < 0) {
                return null;
            }
            used[found] = true;
            take[found] = offering.getValue();
        }

        for (int i = 0; i < bowls.size(); i++) {
            if (!used[i] && !bowls.get(i).isEmpty()) {
                return null;
            }
        }
        return take;
    }
}
