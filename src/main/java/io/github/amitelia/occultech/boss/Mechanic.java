package io.github.amitelia.occultech.boss;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nonnull;

/**
 * One way a boss hurts players (Session B1): its name, raw damage, kind, and whether players see it coming. Every boss
 * declares its attacks as these, deals them through {@link BossFight#hit}, and so every point of damage it does is
 * attributed in the combat log; the balance report grades each one against its tier's benchmark armor
 * ({@link ArmorModel}). Pure Java.
 */
public record Mechanic(String bossId, String name, double damage, Kind kind, boolean telegraphed, boolean ignoresArmor) {

    public enum Kind {
        /** A melee blow (vanilla attack or scripted). Physical: armor counts. */
        MELEE,
        /** An arrow, trident, fireball... Physical. */
        PROJECTILE,
        /** An area attack on the ground (slam, wave, rain). Physical. */
        AREA,
        /** A beam or other magic: ignores armor points, Protection still counts. */
        MAGIC,
        /** Damage each second while standing in it (a zone). Physical. */
        ZONE,
        /** An add's attack: small by design. Physical. */
        ADD
    }

    private static final List<Mechanic> ALL = new ArrayList<>();

    /** A mechanic; {@link Kind#MAGIC} ignores armor points. */
    @Nonnull
    public static Mechanic of(String bossId, String name, double damage, Kind kind, boolean telegraphed) {
        return register(new Mechanic(bossId, name, damage, kind, telegraphed, kind == Kind.MAGIC));
    }

    /** A mechanic of any kind that cuts through armor points (Protection still counts), like a squall ring. */
    @Nonnull
    public static Mechanic piercing(String bossId, String name, double damage, Kind kind, boolean telegraphed) {
        return register(new Mechanic(bossId, name, damage, kind, telegraphed, true));
    }

    private static synchronized Mechanic register(Mechanic mechanic) {
        ALL.add(mechanic);
        return mechanic;
    }

    /** Every declared mechanic of the boss classes loaded so far (load them with {@link BossBlueprint#load()}). */
    @Nonnull
    public static synchronized List<Mechanic> all() {
        return Collections.unmodifiableList(new ArrayList<>(ALL));
    }

    /** The same attack with another damage (a night-time or enraged variant), not registered again. */
    @Nonnull
    public Mechanic scaled(double factor) {
        return new Mechanic(bossId, name, damage * factor, kind, telegraphed, ignoresArmor);
    }
}
