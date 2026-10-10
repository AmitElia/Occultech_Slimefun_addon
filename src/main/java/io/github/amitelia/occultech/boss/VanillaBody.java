package io.github.amitelia.occultech.boss;

import java.util.function.Consumer;
import org.bukkit.Location;
import org.bukkit.entity.LivingEntity;

/** The original Bukkit spawn path, retained for servers without MythicMobs. */
public final class VanillaBody implements BossBody {
    @Override
    public <T extends LivingEntity> T spawn(String id, Class<T> type, Location at, Consumer<T> setup) {
        return at.getWorld().spawn(at, type, setup);
    }
}
