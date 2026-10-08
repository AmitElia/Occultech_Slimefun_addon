package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.BooleanSupplier;

import javax.annotation.Nullable;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.tier2.Abyss;
import io.papermc.paper.datacomponent.item.ResolvableProfile;

/** One seat on the Council: a skinned body, its own attacks, and the raid mechanics it brings to the rotation. */
abstract class CouncilMember {

    protected final CouncilBehavior council;
    protected final BossFight fight;
    protected final CouncilBehavior.Seat seat;
    protected final Mannequin body;

    protected CouncilMember(CouncilBehavior council, Location at, CouncilBehavior.Seat seat) {
        this.council = council;
        this.fight = council.fight();
        this.seat = seat;
        this.body = fight.spawnBoss(Mannequin.class, at.clone().add(0, 0.2, 0), m -> {
            m.setCustomName(ChatColor.GOLD + "" + ChatColor.BOLD + seat.display());
            m.setCustomNameVisible(true);
            m.setDescription(net.kyori.adventure.text.Component.text(seat.title(), net.kyori.adventure.text.format.NamedTextColor.YELLOW));
            m.setProfile(ResolvableProfile.resolvableProfile().name(seat.name()).build());
            CouncilBehavior.prepare(m);
        });
    }

    boolean alive() {
        return body.isValid() && !body.isDead();
    }

    /** The raid mechanics this member brings: each returns true if it went off. */
    abstract List<BooleanSupplier> majors();

    /** Every boss step: this member's own attacks. */
    abstract void tick(int now);

    /** Every tick: movement. */
    abstract void move();

    /** The share of a hit on this body that comes off the pool (1 = all of it). */
    double incoming() {
        return 1;
    }

    void onHitBy(Player player, double damage) {}

    // ------------------------------------------------------------------ helpers

    @Nullable
    protected Player nearest() {
        return fight.nearestPlayer(body.getLocation());
    }

    protected List<Player> shuffledPlayers() {
        List<Player> players = new ArrayList<>(fight.players());
        java.util.Collections.shuffle(players, ThreadLocalRandom.current());
        return players;
    }

    protected boolean within(Player player, double blocks) {
        Location a = player.getLocation();
        Location b = body.getLocation();
        double dx = a.getX() - b.getX();
        double dz = a.getZ() - b.getZ();
        return a.getWorld() == b.getWorld() && dx * dx + dz * dz <= blocks * blocks;
    }

    protected boolean fighting(@Nullable Player player) {
        return player != null && player.isOnline() && !player.isDead() && fight.inArena(player);
    }

    /** Walks toward {@code toward}, but never far out from the middle of the arena. */
    protected void walk(Location toward, double speed, double keep, double maxFromCenter) {
        Location center = fight.center();
        if (body.getLocation().distanceSquared(center) > maxFromCenter * maxFromCenter) {
            Abyss.walk(body, center, speed, 1);
        } else {
            Abyss.walk(body, toward, speed, keep);
        }
    }
}
