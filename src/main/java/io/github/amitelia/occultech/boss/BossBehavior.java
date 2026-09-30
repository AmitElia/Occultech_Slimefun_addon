package io.github.amitelia.occultech.boss;

import org.bukkit.Location;
import org.bukkit.entity.LivingEntity;

/**
 * One boss's behavior for one fight. Created per fight, so it can hold fight state in plain fields.
 * All timing is in ticks via {@link BossFight#elapsed()}, which advances by {@link BossService#STEP} per {@link #tick()}.
 */
public abstract class BossBehavior {

    protected final BossFight fight;

    protected BossBehavior(BossFight fight) {
        this.fight = fight;
    }

    /** Spawn the boss entities with {@link BossFight#spawnBoss}. */
    public abstract void spawn(Location at);

    /** Called every {@link BossService#STEP} ticks while the fight runs. */
    public abstract void tick();

    /** Adjust damage a boss entity takes from a player (e.g. shields). */
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage;
    }

    /** Whether the engine may teleport the boss next to a player who can't be reached. Off for ranged bosses. */
    public boolean usesAntiPillar() {
        return true;
    }

    /** True every {@code interval} ticks (interval must be a multiple of the step). */
    protected boolean every(int interval) {
        return fight.elapsed() % interval == 0;
    }
}
