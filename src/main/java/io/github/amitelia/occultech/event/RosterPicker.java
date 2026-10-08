package io.github.amitelia.occultech.event;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.List;
import java.util.Random;
import java.util.Set;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Who steps onto the floor next: a shuffled deck of roster slots, so nobody repeats until everyone has been out, and
 * never someone already on the floor. A new raid gets a new picker, so the line-up is random each run. Pure Java.
 */
public final class RosterPicker {

    private final List<List<StaffMember>> slots;
    private final Random random;
    private final Deque<List<StaffMember>> deck = new ArrayDeque<>();

    public RosterPicker(@Nonnull List<List<StaffMember>> slots, @Nonnull Random random) {
        this.slots = List.copyOf(slots);
        this.random = random;
    }

    /**
     * The next slot whose lead isn't in {@code onField} (lead names, any case), or null if every slot is on the floor.
     */
    @Nullable
    public List<StaffMember> next(@Nonnull Set<String> onField) {
        for (int pass = 0; pass < 2; pass++) {
            if (deck.isEmpty()) {
                List<List<StaffMember>> shuffled = new ArrayList<>(slots);
                Collections.shuffle(shuffled, random);
                deck.addAll(shuffled);
            }
            for (List<StaffMember> slot : List.copyOf(deck)) {
                if (!onField.contains(slot.get(0).name().toLowerCase(java.util.Locale.ROOT))) {
                    deck.remove(slot);
                    return slot;
                }
            }
            // everyone left in this deck is on the floor: deal a fresh deck and look once more
            deck.clear();
        }
        return null;
    }
}
