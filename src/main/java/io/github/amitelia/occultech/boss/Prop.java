package io.github.amitelia.occultech.boss;

/**
 * A model standing in for a fight object's look (a BetterModel prop at a location). It is cosmetic: hits still land on
 * the object's own hitbox, and nothing about it is saved; a resumed fight spawns fresh objects with fresh props.
 * A prop that shows hits names its breakable pieces {@code shard_0}, {@code shard_1}, ... and has the clips
 * {@code hit} and {@code shatter}.
 */
public interface Prop {
    void animate(String clip);

    void hidePart(String part);

    void remove();

    /** Tints the named bones (BetterModel names, tag prefix dropped: {@code glow_brew} is {@code brew}). */
    default void tint(int rgb, String... parts) {}

    /** Called every fight step: shows the model to players who have come near since it appeared. */
    default void refresh() {}
}
