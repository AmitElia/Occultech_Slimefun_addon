package io.github.amitelia.occultech.event;

import java.util.Locale;

import javax.annotation.Nullable;

/**
 * The six Staff Raid kits (docs/staff-raid.md): each sets a staff member's base movement, melee and one generic move;
 * their signature abilities come on top. Every staff member has the same stats whatever their kit. Pure Java.
 */
public enum Archetype {
    /** Slow, heavy melee, high knockback resistance; a telegraphed ground slam. */
    BRUISER,
    /** Medium pace, keeps mid range; zone denial. */
    CONTROLLER,
    /** Fast, hit and run; a telegraphed dash through a line. */
    SKIRMISHER,
    /** Keeps its distance; a few weak adds (capped). */
    SUMMONER,
    /** Mid range; beams and traps. */
    GADGETEER,
    /** Mid range; marks a player, and the mark bursts after 3 s. */
    HEXER;

    /** The archetype named {@code name} (any case), or null. */
    @Nullable
    public static Archetype parse(@Nullable String name) {
        if (name == null) {
            return null;
        }
        try {
            return valueOf(name.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
