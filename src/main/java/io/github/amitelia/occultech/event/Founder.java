package io.github.amitelia.occultech.event;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.BooleanSupplier;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Pose;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.Mechanic;
import io.github.amitelia.occultech.boss.tier2.Abyss;

/**
 * X, the Founder (Council seat, Session E7): a giant. Walks slowly near the middle and crushes whoever is at his feet.
 * <ul>
 * <li><b>Stomp</b> (raid mechanic): a ring warns at his feet, then rings spread across the floor - jump them (two waves from
 * the middle band on).</li>
 * <li><b>Founder's Sweep</b> (raid mechanic): lasers turn around him, low ones to jump and full-height ones with a gap.</li>
 * <li><b>Foundation Stones</b> (raid mechanic): soak circles.</li>
 * <li><b>Kick</b>: a cone in front of him warns, then everyone in it flies.</li>
 * <li><b>Stagger</b>: enough damage at his feet in a short time and he drops to a knee for 4 s, taking half again as much.</li>
 * <li><b>Beer mugs</b>: he lobs big foaming mugs at a few players; each lands upright on a warned circle with a splash
 * and stands there a while in a pool of spilled beer that slows and stings whoever wades through it.</li>
 * <li><b>Keg toss</b>: he heaves a huge keg onto a warned circle under a player; it smashes there and leaves a wide pool
 * of spilled beer.</li>
 * <li><b>Last Round</b> (raid mechanic): "Last round!" - he bowls huge beer kegs out from where he stands along warned
 * lanes, spread round him; a keg rolls over whoever is still in its lane and bursts into a pool at the arena's edge.
 * Stand between the lanes.</li>
 * </ul>
 */
final class Founder extends CouncilMember {

    private static final Mechanic CRUSH = Mechanic.of(CouncilBehavior.ID, "Crush (Founder)", 22, Mechanic.Kind.MELEE, false);
    private static final Mechanic STOMP = Mechanic.of(CouncilBehavior.ID, "Stomp (Founder)", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic SWEEP = Mechanic.of(CouncilBehavior.ID, "Founder's Sweep (Founder)", 9, Mechanic.Kind.MAGIC, true);
    private static final Mechanic STONE = Mechanic.of(CouncilBehavior.ID, "Foundation Stone (Founder)", 20, Mechanic.Kind.AREA, true);
    private static final Mechanic CRUMBLE = Mechanic.of(CouncilBehavior.ID, "Crumbling foundation (Founder)", 30, Mechanic.Kind.AREA, true);
    private static final Mechanic KICK = Mechanic.of(CouncilBehavior.ID, "Kick (Founder)", 26, Mechanic.Kind.AREA, true);
    private static final Mechanic MUG = Mechanic.of(CouncilBehavior.ID, "Beer mug (Founder)", 22, Mechanic.Kind.AREA, true);
    private static final Mechanic KEG = Mechanic.of(CouncilBehavior.ID, "Rolling keg (Founder)", 24, Mechanic.Kind.AREA, true);
    private static final Mechanic KEG_SMASH = Mechanic.of(CouncilBehavior.ID, "Keg toss (Founder)", 26, Mechanic.Kind.AREA, true);
    private static final Mechanic SPILL = Mechanic.of(CouncilBehavior.ID, "Spilled beer (Founder)", 6, Mechanic.Kind.ZONE, true);
    private static final Color BEER = Color.fromRGB(230, 160, 40);
    private static final int MUG_FLIGHT = 30;
    private static final double MUG_RADIUS = 2.8;
    private static final float MUG_SCALE = 3.2F;
    /** How long a landed mug stands in its pool. */
    private static final int PUDDLE = 140;
    private static final int KEG_WARNING = 35;
    private static final float KEG_SCALE = 4F;
    /** A keg's radius on its side (the model's belly is 12.4 of 16 across). */
    private static final double KEG_RADIUS = KEG_SCALE * 0.39;
    private static final double KEG_WIDTH = KEG_RADIUS * 2 + 0.8;
    private static final int TOSS_FLIGHT = 35;
    private static final double TOSS_RADIUS = 3.5;
    static final double SCALE = 6;
    private static final double REACH = 5;
    private static final double KICK_REACH = 8;
    private static final double KICK_HALF_ANGLE = Math.toRadians(30);
    /** Damage at his feet within 8 s, as a share of the pool, that drops him to a knee. */
    private static final double STAGGER_SHARE = 0.015;
    private static final int KNEEL = 80;

    private final Deque<double[]> footHits = new ArrayDeque<>();
    private int nextCrush;
    private int nextKick = 120;
    private int nextMugs = 80;
    private int nextToss = 200;
    /** The kick winding up: he stands still facing it. */
    private int kickUntil = -1;
    @javax.annotation.Nullable private Location kickFacing;
    private int kneelUntil = -1;
    private int staggerReady;
    private boolean fullBeam;

    Founder(CouncilBehavior council, Location at, CouncilBehavior.Seat seat) {
        super(council, at, seat);
        BossFight.setAttribute(body, Attribute.SCALE, SCALE);
        BossFight.setAttribute(body, Attribute.KNOCKBACK_RESISTANCE, 1);
    }

    @Override
    List<BooleanSupplier> majors() {
        return List.of(this::stomp, this::sweep, this::stones, this::lastRound);
    }

    @Override
    double incoming() {
        return kneeling() ? 1.5 : 1;
    }

    private boolean kneeling() {
        return fight.elapsed() < kneelUntil;
    }

    @Override
    void onHitBy(Player player, double damage) {
        if (!within(player, REACH + 1) || kneeling()) {
            return;
        }
        int now = fight.elapsed();
        footHits.addLast(new double[] { now, damage });
        double sum = 0;
        while (!footHits.isEmpty() && now - footHits.peekFirst()[0] > 160) {
            footHits.removeFirst();
        }
        for (double[] hit : footHits) {
            sum += hit[1];
        }
        if (now >= staggerReady && sum >= council.poolMax() * STAGGER_SHARE) {
            kneelUntil = now + KNEEL;
            staggerReady = now + KNEEL + 400;
            footHits.clear();
            body.setPose(Pose.SNEAKING, true);
            body.getWorld().playSound(body.getLocation(), Sound.ENTITY_IRON_GOLEM_DAMAGE, 2F, 0.5F);
            fight.broadcast("&6" + seat.display() + " &estumbles to a knee - &fhit hard now!");
        }
    }

    @Override
    void tick(int now) {
        if (kneelUntil >= 0 && now >= kneelUntil) {
            kneelUntil = -1;
            body.setPose(Pose.STANDING, false);
        }
        if (kneeling()) {
            return;
        }
        Player close = nearest();
        if (close != null && now >= nextCrush && within(close, REACH)) {
            nextCrush = now + 40;
            body.swingMainHand();
            council.hit(close, CRUSH, body);
            Abyss.face(body, close.getLocation());
        }
        if (close != null && now >= nextKick && within(close, KICK_REACH)) {
            nextKick = now + council.pace().cooldown(220);
            kick(close);
        } else if (now >= nextToss && !fight.players().isEmpty()) {
            nextToss = now + council.pace().cooldown(240);
            nextMugs = Math.max(nextMugs, now + 40);
            tossKeg();
        } else if (now >= nextMugs && !fight.players().isEmpty()) {
            nextMugs = now + council.pace().cooldown(160);
            throwMugs();
        }
    }

    // ------------------------------------------------------------------ beer

    private static ItemStack beer(String model, Material without) {
        boolean pack = io.github.amitelia.occultech.boss.FloorDecals.enabled();
        ItemStack stack = new ItemStack(pack ? Material.PAPER : without);
        if (pack) {
            ItemMeta meta = stack.getItemMeta();
            meta.setItemModel(new NamespacedKey("occultech", model));
            stack.setItemMeta(meta);
        }
        return stack;
    }

    /** {@code look} at {@code scale}, upright (turned {@code yaw} about the vertical) or tumbled {@code turn} about a tilted axis. */
    private static Transformation shaped(float scale, float turn, float yaw) {
        org.joml.Quaternionf q = new org.joml.Quaternionf().rotateY(yaw).rotateAxis(turn, 1F, 0F, 0.3F);
        return new Transformation(new Vector3f(), q, new Vector3f(scale, scale, scale), new org.joml.Quaternionf());
    }

    /**
     * Throws {@code look} from his hand onto {@code spot} in a high arc over {@code ticks}, tumbling, and lands it upright
     * (its base on the floor); then runs {@code landed} with the display, still standing there.
     */
    private void lob(ItemStack look, float scale, Location spot, int ticks, double peak, java.util.function.Consumer<ItemDisplay> landed) {
        Location hand = body.getLocation().add(0, SCALE * 1.15, 0);
        hand.setYaw(0F);
        hand.setPitch(0F);
        float yaw = (float) ThreadLocalRandom.current().nextDouble(Math.PI * 2);
        ItemDisplay thrown = fight.spawnExtra(ItemDisplay.class, hand, d -> {
            d.setItemStack(look);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setTransformation(shaped(scale, 0F, yaw));
        });
        Location rest = spot.clone().add(0, scale / 2, 0);   // the model is a cube centred on the display: its base on the floor
        Vector across = rest.toVector().subtract(hand.toVector());
        for (int t = 3; t <= ticks; t += 3) {
            double f = Math.min(1, (double) t / ticks);
            Location point = hand.clone().add(across.clone().multiply(f)).add(0, 4 * peak * f * (1 - f), 0);
            float turn = t + 3 > ticks ? (float) (Math.PI * 4) : (float) (f * Math.PI * 4);   // whole turns: lands upright
            council.later(t - 2, () -> {
                if (thrown.isValid()) {
                    thrown.setTeleportDuration(3);
                    thrown.teleport(point);
                    thrown.setInterpolationDelay(0);
                    thrown.setInterpolationDuration(3);
                    thrown.setTransformation(shaped(scale, turn, yaw));
                }
            });
        }
        council.later(ticks + 1, () -> {
            if (thrown.isValid()) {
                thrown.setTeleportDuration(0);
                thrown.teleport(rest);
                thrown.setInterpolationDuration(0);
                thrown.setTransformation(shaped(scale, 0F, yaw));
                landed.accept(thrown);
            }
        });
    }

    /** Big mugs lobbed at a few players: each lands upright on a warned circle and stands in its pool of beer a while. */
    private void throwMugs() {
        List<Player> players = shuffledPlayers();
        int count = Math.min(players.size(), 2 + council.pace().overlap());
        body.swingMainHand();
        body.getWorld().playSound(body.getLocation(), Sound.ENTITY_PLAYER_BURP, 2F, 0.5F);
        for (Player player : players.subList(0, count)) {
            Location spot = floorAt(player.getLocation());
            fight.telegraph(spot, MUG_RADIUS, MUG_FLIGHT, BEER);
            lob(beer("raid_beer_mug", Material.HONEY_BOTTLE), MUG_SCALE, spot, MUG_FLIGHT, 6, mug -> {
                spot.getWorld().playSound(spot, Sound.BLOCK_GLASS_HIT, 2F, 0.6F);
                spot.getWorld().playSound(spot, Sound.ENTITY_GENERIC_SPLASH, 1.2F, 1.3F);
                spot.getWorld().spawnParticle(Particle.DUST, spot.clone().add(0, 0.5, 0), 30, 1.2, 0.4, 1.2, 0,
                    new Particle.DustOptions(BEER, 1.4F));
                io.github.amitelia.occultech.boss.FloorDecals.splash(fight, spot, MUG_RADIUS, BEER);
                if (alive()) {
                    for (Player hit : fight.players()) {
                        if (hit.getLocation().distanceSquared(spot) <= MUG_RADIUS * MUG_RADIUS) {
                            council.hit(hit, MUG, body);
                        }
                    }
                }
                spill(spot, MUG_RADIUS, PUDDLE, mug);
            });
        }
    }

    /** Keg toss: a huge keg heaved onto a warned circle under a player; it smashes there and spills a wide pool. */
    private void tossKeg() {
        List<Player> players = shuffledPlayers();
        if (players.isEmpty()) {
            return;
        }
        Location spot = floorAt(players.get(0).getLocation());
        fight.telegraph(spot, TOSS_RADIUS, TOSS_FLIGHT, BEER, io.github.amitelia.occultech.boss.FloorDecals.Mark.SLAM);
        body.swingMainHand();
        body.getWorld().playSound(body.getLocation(), Sound.BLOCK_BARREL_OPEN, 2F, 0.4F);
        fight.broadcast("&6" + seat.display() + " &eheaves a keg!");
        lob(beer("raid_beer_keg", Material.BARREL), KEG_SCALE, spot, TOSS_FLIGHT, 9, keg -> {
            keg.remove();
            spot.getWorld().playSound(spot, Sound.ENTITY_ZOMBIE_BREAK_WOODEN_DOOR, 2F, 0.6F);
            spot.getWorld().playSound(spot, Sound.ENTITY_GENERIC_SPLASH, 2F, 0.8F);
            spot.getWorld().spawnParticle(Particle.BLOCK, spot.clone().add(0, 0.6, 0), 60, 1.5, 0.6, 1.5, Material.SPRUCE_PLANKS.createBlockData());
            spot.getWorld().spawnParticle(Particle.DUST, spot.clone().add(0, 0.6, 0), 40, 2, 0.5, 2, 0, new Particle.DustOptions(BEER, 1.6F));
            io.github.amitelia.occultech.boss.FloorDecals.splash(fight, spot, TOSS_RADIUS, BEER);
            if (alive()) {
                for (Player hit : fight.players()) {
                    if (hit.getLocation().distanceSquared(spot) <= TOSS_RADIUS * TOSS_RADIUS) {
                        council.hit(hit, KEG_SMASH, body);
                        StaffKit.knock(hit, spot, 0.9, 0.5);
                    }
                }
            }
            spill(spot, TOSS_RADIUS, PUDDLE, null);
        });
    }

    private static Location floorAt(Location at) {
        Location spot = at.clone();
        spot.setY(spot.getWorld().getHighestBlockYAt(spot) + 1);
        spot.setYaw(0F);
        spot.setPitch(0F);
        return spot;
    }

    /**
     * A pool of spilled beer, {@code radius} blocks, for {@code ticks}: it slows whoever wades through and stings them once
     * a second. {@code prop} (a landed mug) stands in it and goes with it.
     */
    private void spill(Location spot, double radius, int ticks, @javax.annotation.Nullable ItemDisplay prop) {
        boolean pack = io.github.amitelia.occultech.boss.FloorDecals.enabled();
        ItemDisplay pool = pack ? io.github.amitelia.occultech.boss.FloorDecals.flat(fight, spot, "floor_beer_puddle", Color.WHITE, radius * 2) : null;
        for (int t = 0; t < ticks; t += 10) {
            boolean sting = t % 20 == 10;
            council.later(t, () -> {
                if (!pack) {
                    spot.getWorld().spawnParticle(Particle.DUST, spot.clone().add(0, 0.1, 0), 10, radius / 2, 0, radius / 2, 0,
                        new Particle.DustOptions(BEER, 1.2F));
                }
                for (Player player : fight.players()) {
                    Location p = player.getLocation();
                    double dx = p.getX() - spot.getX();
                    double dz = p.getZ() - spot.getZ();
                    if (dx * dx + dz * dz <= radius * radius && Math.abs(p.getY() - spot.getY()) < 1.5) {
                        player.addPotionEffect(new PotionEffect(PotionEffectType.SLOWNESS, 25, 1, false, false, true));
                        if (sting && alive()) {
                            council.hit(player, SPILL, body);
                        }
                    }
                }
            });
        }
        council.later(ticks, () -> {
            if (pool != null) {
                pool.remove();
            }
            if (prop != null && prop.isValid()) {
                prop.getWorld().playSound(prop.getLocation(), Sound.BLOCK_GLASS_BREAK, 1F, 1.2F);
                prop.remove();
            }
        });
    }

    /** Last Round: kegs bowled out from him along warned lanes, spread round him with gaps between. */
    private boolean lastRound() {
        if (!alive() || kneeling()) {
            return false;
        }
        Location from = body.getLocation();
        from.setY(from.getWorld().getHighestBlockYAt(from) + 1);
        int kegs = 4 + council.pace().overlap();
        double start = ThreadLocalRandom.current().nextDouble(Math.PI * 2);
        double length = fight.radius() + 2;
        Particle.DustOptions dust = new Particle.DustOptions(BEER, 1.3F);
        for (int i = 0; i < kegs; i++) {
            double angle = start + Math.PI * 2 * i / kegs;
            Vector dir = new Vector(Math.cos(angle), 0, Math.sin(angle));
            if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
                io.github.amitelia.occultech.boss.FloorDecals.lane(fight, from, dir, length, KEG_WIDTH, KEG_WARNING, BEER);
            } else {
                for (int t = 0; t < KEG_WARNING; t += 7) {
                    council.later(t, () -> {
                        for (double r = 2; r <= length; r += 1) {
                            from.getWorld().spawnParticle(Particle.DUST, from.clone().add(dir.clone().multiply(r)).add(0, 0.2, 0), 1, 0, 0, 0, 0, dust);
                        }
                    });
                }
            }
            council.add(new DelayedHazard(KEG_WARNING, new KegRoll(from, dir, length)), true);
        }
        body.swingMainHand();
        body.getWorld().playSound(from, Sound.ENTITY_PLAYER_BURP, 2F, 0.4F);
        body.getWorld().playSound(from, Sound.BLOCK_BARREL_OPEN, 2F, 0.5F);
        fight.broadcast("&6" + seat.display() + "&e: &f\"Last round!\" &e- kegs incoming, &fstand between the lanes!");
        return true;
    }

    /** One keg rolling out along a lane: it flattens whoever is in its way, and bursts at the arena's edge. */
    private final class KegRoll implements RaidHazard {

        private static final double SPEED = 0.55;
        private final Location from;
        private final Vector dir;
        private final double length;
        private final java.util.Set<java.util.UUID> struck = new java.util.HashSet<>();
        private ItemDisplay keg;
        private double travelled = 3;   // out from his feet
        private int ticks;

        KegRoll(Location from, Vector dir, double length) {
            this.from = from;
            this.dir = dir;
            this.length = length;
        }

        private Location at() {
            Location at = from.clone().add(dir.clone().multiply(travelled)).add(0, KEG_RADIUS, 0);
            at.setDirection(dir);
            at.setPitch(0F);
            return at;
        }

        /** Laid on its side (its axis across the lane) and turned {@code roll} about that axis: it rolls forward. */
        private Transformation rolled(float roll) {
            org.joml.Quaternionf q = new org.joml.Quaternionf().rotateX(roll).rotateZ((float) Math.PI / 2);
            return new Transformation(new Vector3f(), q, new Vector3f(KEG_SCALE, KEG_SCALE, KEG_SCALE), new org.joml.Quaternionf());
        }

        @Override
        public boolean step() {
            ticks++;
            if (keg == null) {
                keg = fight.spawnExtra(ItemDisplay.class, at(), d -> {
                    d.setItemStack(beer("raid_beer_keg", Material.BARREL));
                    d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
                    d.setTransformation(rolled(0F));
                });
                from.getWorld().playSound(from, Sound.BLOCK_WOOD_BREAK, 1.5F, 0.5F);
                return true;
            }
            travelled += SPEED;
            if (ticks % 2 == 0 && keg.isValid()) {
                keg.setTeleportDuration(2);
                keg.teleport(at());
                keg.setInterpolationDelay(0);
                keg.setInterpolationDuration(2);
                keg.setTransformation(rolled((float) (travelled / KEG_RADIUS)));
            }
            if (ticks % 6 == 0) {
                from.getWorld().playSound(at(), Sound.BLOCK_WOOD_STEP, 1F, 0.6F);
            }
            Location here = from.clone().add(dir.clone().multiply(travelled));
            if (alive()) {
                for (Player player : fight.players()) {
                    Location p = player.getLocation();
                    double dx = p.getX() - here.getX();
                    double dz = p.getZ() - here.getZ();
                    if (dx * dx + dz * dz <= (KEG_RADIUS + 0.6) * (KEG_RADIUS + 0.6) && Math.abs(p.getY() - here.getY()) < KEG_RADIUS * 2
                        && struck.add(player.getUniqueId())) {
                        council.hit(player, KEG, body);
                        player.setVelocity(dir.clone().multiply(0.9).setY(0.5));
                    }
                }
            }
            if (travelled >= length) {
                Location end = at();
                keg.remove();
                end.getWorld().playSound(end, Sound.BLOCK_WOOD_BREAK, 1.5F, 0.6F);
                end.getWorld().playSound(end, Sound.ENTITY_GENERIC_SPLASH, 1F, 1F);
                end.getWorld().spawnParticle(Particle.DUST, end, 25, 0.8, 0.5, 0.8, 0, new Particle.DustOptions(BEER, 1.4F));
                io.github.amitelia.occultech.boss.FloorDecals.splash(fight, end, 2.5, BEER);
                spill(floorAt(end), 2.5, 80, null);
                return false;
            }
            return true;
        }
    }

    @Override
    void move() {
        if (kneeling()) {
            body.setVelocity(new Vector(0, body.getVelocity().getY(), 0));
            return;
        }
        if (fight.elapsed() < kickUntil && kickFacing != null) {
            body.setVelocity(new Vector(0, Math.min(0, body.getVelocity().getY()), 0));
            Abyss.face(body, kickFacing);
            return;
        }
        Player close = nearest();
        if (close != null) {
            walk(close.getLocation(), 0.12, REACH - 1, fight.radius() * 0.45);
        }
    }

    private void kick(Player toward) {
        Location at = body.getLocation();
        Vector aimAt = toward.getLocation().toVector().subtract(at.toVector());
        double aim = Math.atan2(aimAt.getZ(), aimAt.getX());
        Abyss.face(body, toward.getLocation());
        kickUntil = fight.elapsed() + 27;
        kickFacing = at.clone().add(aimAt.clone().setY(0).normalize().multiply(5)).add(0, 1.6, 0);
        Particle.DustOptions dust = new Particle.DustOptions(Color.fromRGB(230, 80, 40), 1.5F);
        if (io.github.amitelia.occultech.boss.FloorDecals.enabled()) {
            io.github.amitelia.occultech.boss.FloorDecals.sector(fight, at, aimAt, KICK_REACH, Math.toDegrees(KICK_HALF_ANGLE * 2), 25,
                Color.fromRGB(230, 80, 40));
        }
        for (int t = 0; t < 25 && !io.github.amitelia.occultech.boss.FloorDecals.enabled(); t += 5) {
            council.later(t, () -> {
                for (double a = aim - KICK_HALF_ANGLE; a <= aim + KICK_HALF_ANGLE; a += 0.08) {
                    for (double r = 2; r <= KICK_REACH; r += 1.5) {
                        at.getWorld().spawnParticle(Particle.DUST, at.clone().add(Math.cos(a) * r, 0.2, Math.sin(a) * r), 1, 0, 0, 0, 0, dust);
                    }
                }
            });
        }
        body.getWorld().playSound(at, Sound.ENTITY_RAVAGER_ROAR, 1.5F, 0.6F);
        council.later(25, () -> {
            if (!alive()) {
                return;
            }
            body.swingMainHand();
            Location now = at;   // where the cone warned
            now.getWorld().playSound(now, Sound.ENTITY_IRON_GOLEM_ATTACK, 2F, 0.5F);
            for (Player player : fight.players()) {
                Vector to = player.getLocation().toVector().subtract(now.toVector());
                double distance = Math.hypot(to.getX(), to.getZ());
                if (distance <= KICK_REACH && Math.abs(RaidGeometry.angleBetween(Math.atan2(to.getZ(), to.getX()), aim)) <= KICK_HALF_ANGLE) {
                    council.hit(player, KICK, body);
                    player.setVelocity(new Vector(Math.cos(aim), 0, Math.sin(aim)).multiply(1.6).setY(0.55));
                }
            }
        });
    }

    private boolean stomp() {
        if (!alive() || kneeling()) {
            return false;
        }
        Location at = body.getLocation();
        fight.telegraph(at, 3.5, 30, Color.fromRGB(230, 120, 40));
        at.getWorld().playSound(at, Sound.ENTITY_RAVAGER_STEP, 2F, 0.4F);
        RaidPace pace = council.pace();
        council.later(30, () -> {
            if (!alive()) {
                return;
            }
            Location feet = body.getLocation();
            feet.getWorld().spawnParticle(Particle.EXPLOSION, feet, 4, 2, 0.2, 2, 0);
            feet.getWorld().spawnParticle(Particle.BLOCK, feet, 80, 3, 0.1, 3, Material.DIRT.createBlockData());
            feet.getWorld().playSound(feet, Sound.ENTITY_GENERIC_EXPLODE, 2F, 0.5F);
            for (int i = 0; i < pace.ringWaves(); i++) {
                council.add(new DelayedHazard(i * 15, new RaidRing(fight, feet, 0.35, fight.radius() - 1, RaidRing.LOW, Double.NaN,
                    Color.fromRGB(230, 120, 40), council.scaled(STOMP), body)), true);
            }
        });
        return true;
    }

    private boolean sweep() {
        if (!alive()) {
            return false;
        }
        RaidPace pace = council.pace();
        fullBeam = !fullBeam;
        double length = Math.min(16, fight.radius() * 0.5);
        double spin = (ThreadLocalRandom.current().nextBoolean() ? 1 : -1) * 0.03;
        council.add(new SpinningLaser(fight, body, pace.beams(), length, spin, fullBeam ? SpinningLaser.FULL : SpinningLaser.LOW,
            fullBeam ? length * 0.45 : Double.NaN, length * 0.45 + 2.5, 40, 220, pace.reverse(),
            fullBeam ? Color.fromRGB(255, 60, 60) : Color.fromRGB(255, 200, 40), council.scaled(SWEEP)), true);
        fight.broadcast("&6" + seat.display() + "&e's gaze sweeps the floor - " + (fullBeam ? "&fstand in the gaps!" : "&fjump the beams!"));
        return true;
    }

    private boolean stones() {
        if (!alive()) {
            return false;
        }
        council.soakCircles(STONE, CRUMBLE, body);
        body.getWorld().playSound(body.getLocation(), Sound.BLOCK_ANVIL_PLACE, 2F, 0.5F);
        fight.broadcast("&6" + seat.display() + " &elays the Foundation Stones - &ffill the circles!");
        return true;
    }
}
