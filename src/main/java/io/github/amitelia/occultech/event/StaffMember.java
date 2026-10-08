package io.github.amitelia.occultech.event;

import java.util.List;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * One staff member on the raid roster (config {@code raid.roster}). Pure Java.
 *
 * @param name       Minecraft username: the roster key
 * @param display    the name shown above them
 * @param title      their role, shown under the name
 * @param skin       whose skin they wear (a username; usually their own)
 * @param archetype  their kit
 * @param signatures their signature abilities (ids, added session by session)
 * @param partner    the username of a partner who fights in the same slot (Earl + Sam), or null
 * @param scale      body size (1 = a player's size; Earl is small)
 */
public record StaffMember(@Nonnull String name, @Nonnull String display, @Nonnull String title, @Nonnull String skin,
    @Nonnull Archetype archetype, @Nonnull List<String> signatures, @Nullable String partner, double scale) {

    public StaffMember {
        signatures = List.copyOf(signatures);
        scale = scale <= 0 ? 1 : Math.max(0.4, Math.min(2, scale));
    }

    public boolean has(@Nonnull String signature) {
        return signatures.contains(signature);
    }
}
