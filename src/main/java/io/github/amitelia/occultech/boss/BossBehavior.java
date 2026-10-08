package io.github.amitelia.occultech.boss;

import javax.annotation.Nullable;

import org.bukkit.Location;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;

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

    /**
     * Called every tick for scripted movement (puppets, dives, charges). Setting a velocity once per tick keeps the
     * motion smooth; setting it once per step makes creatures lurch and stall. Keep it cheap: no searches here.
     */
    public void move() {}

    /** A player's hit landed on a boss entity (after {@link #modifyIncomingDamage}); e.g. to reflect damage. */
    public void onDamagedBy(LivingEntity boss, Player player, double damage) {}

    /**
     * A player's projectile is about to hit a boss entity: true makes it pass harmlessly (it's removed), e.g. a boss that
     * steps away from arrows like an enderman.
     */
    public boolean deflectProjectile(LivingEntity boss, org.bukkit.entity.Projectile projectile) {
        return false;
    }

    /** Adjust damage a boss entity takes from a player (e.g. shields). */
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        return damage;
    }

    /** Whether the engine may teleport the boss next to a player who can't be reached. Off for ranged bosses. */
    /**
     * The least time (ticks) between two vanilla melee hits from one of this fight's creatures; 0 = vanilla pace (about
     * one a second). A boss that swings too fast for most players gets a longer one.
     */
    public int meleeCooldownTicks() {
        return 0;
    }

    public boolean usesAntiPillar() {
        return true;
    }

    /** How far above/below the altar the boss may be before it's pulled back. Flying bosses need more. */
    public double verticalLeash() {
        return 8;
    }

    /** An extra mob of this fight died ({@code killer} is the player responsible, if any). */
    public void onAddDeath(Entity entity, @Nullable Player killer) {}

    /** True every {@code interval} ticks (interval must be a multiple of the step). */
    protected boolean every(int interval) {
        return fight.elapsed() % interval == 0;
    }
}
