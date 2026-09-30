package io.github.amitelia.occultech.items;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitTask;

import io.github.amitelia.occultech.boss.BossService;
import io.github.amitelia.occultech.boss.BossSpec;
import io.github.amitelia.occultech.ritual.CirclePattern;
import io.github.amitelia.occultech.ritual.Circles;
import io.github.amitelia.occultech.ritual.RitualMatcher;
import io.github.amitelia.occultech.ritual.RitualMatcher.Bowl;
import io.github.amitelia.occultech.ritual.RitualRecipe;
import io.github.thebusybiscuit.slimefun4.api.items.SlimefunItem;
import me.mrCookieSlime.Slimefun.api.BlockStorage;
import me.mrCookieSlime.Slimefun.api.inventory.BlockMenu;

/**
 * Runs rituals at altars: checks the circle, matches the offerings, consumes them up front (so nothing can be
 * pulled back out mid-ritual), locks the involved menus, plays the ritual, then either delivers the crafted item or
 * summons the boss.
 * <p>
 * If the circle is broken mid-ritual the offerings are lost. If the plugin shuts down mid-ritual, a crafting ritual
 * delivers its result and a summoning ritual returns everything it took, so a restart never eats items.
 */
public final class RitualService {

    public static final int DURATION_TICKS = 100;
    private static final int STEP_TICKS = 5;
    private static final Particle.DustOptions RITUAL_DUST = new Particle.DustOptions(Color.fromRGB(150, 60, 210), 1.2F);
    private static final Particle.DustOptions SUMMON_DUST = new Particle.DustOptions(Color.fromRGB(200, 30, 50), 1.4F);

    public enum Outcome { STARTED, BUSY, NOT_AN_ALTAR, INCOMPLETE_CIRCLE, NO_MATCH, ARENA_OCCUPIED }

    public record CircleCheck(int tier, @Nonnull CirclePattern pattern, int rotation, @Nonnull List<int[]> missing) {

        public boolean complete() {
            return missing.isEmpty();
        }
    }

    private record Taken(@Nullable BlockMenu menu, int slot, ItemStack item) {}

    private final Plugin plugin;
    private final BossService bosses;
    private final OccultechFightHooks hooks;
    private final Holograms holograms;
    private final List<RitualRecipe> recipes = new ArrayList<>();
    private final Map<String, BossSpec> specs = new HashMap<>();
    private final Map<Location, Session> sessions = new HashMap<>();
    private final Set<Location> locked = new HashSet<>();

    public RitualService(Plugin plugin, BossService bosses, OccultechFightHooks hooks) {
        this.plugin = plugin;
        this.bosses = bosses;
        this.hooks = hooks;
        this.holograms = new Holograms(plugin);
    }

    @Nonnull
    public Holograms holograms() {
        return holograms;
    }

    /** Label for an altar's hologram: what the altar is doing right now, or null when idle. */
    @Nullable
    String altarStatus(@Nonnull Block altar) {
        if (sessions.containsKey(altar.getLocation())) {
            return sessions.get(altar.getLocation()).recipe.isSummon() ? "&cA summoning is underway..." : "&dThe ritual is underway...";
        }
        return bosses.fightAt(altar).map(fight -> "&c" + fight.spec().name() + " &7walks this circle").orElse(null);
    }

    public void addRecipe(@Nonnull RitualRecipe recipe) {
        recipes.add(recipe);
    }

    public void addSummon(@Nonnull RitualRecipe recipe, @Nonnull BossSpec spec) {
        recipes.add(recipe);
        specs.put(recipe.bossId(), spec);
    }

    @Nonnull
    public List<RitualRecipe> recipes() {
        return Collections.unmodifiableList(recipes);
    }

    @Nonnull
    public Optional<BossSpec> spec(@Nonnull String bossId) {
        return Optional.ofNullable(specs.get(bossId));
    }

    @Nonnull
    public BossService bosses() {
        return bosses;
    }

    public boolean isLocked(@Nonnull Location location) {
        return locked.contains(location.getBlock().getLocation());
    }

    /** Called when an altar's menu is created (e.g. chunk load): returns the catalyst of a fight lost to a crash. */
    public void recoverAltar(@Nonnull Block altar) {
        if (bosses.fightAt(altar).isEmpty()) {
            hooks.recover(altar);
        }
    }

    /** Checks the circle around an altar, choosing the rotation closest to complete. */
    @Nonnull
    public Optional<CircleCheck> checkCircle(@Nonnull Block altar) {
        String id = BlockStorage.checkID(altar);
        OptionalInt tier = id == null ? OptionalInt.empty() : Circles.tierOfAltar(id);
        if (tier.isEmpty()) {
            return Optional.empty();
        }
        CirclePattern pattern = Circles.forTier(tier.getAsInt());
        var lookup = lookupAround(altar);
        int rotation = pattern.match(lookup);
        if (rotation < 0) {
            rotation = pattern.closestRotation(lookup);
        }
        return Optional.of(new CircleCheck(tier.getAsInt(), pattern, rotation, pattern.missing(lookup, rotation)));
    }

    @Nonnull
    public Outcome begin(@Nullable Player player, @Nonnull Block altar) {
        if (sessions.containsKey(altar.getLocation())) {
            tell(player, "&7A ritual is already in progress here.");
            return Outcome.BUSY;
        }
        if (bosses.fightAt(altar).isPresent()) {
            tell(player, "&7A summoned creature still walks this circle.");
            return Outcome.BUSY;
        }

        Optional<CircleCheck> check = checkCircle(altar);
        BlockMenu altarMenu = BlockStorage.getInventory(altar);
        if (check.isEmpty() || altarMenu == null) {
            return Outcome.NOT_AN_ALTAR;
        }
        if (!check.get().complete()) {
            tell(player, "&cThe circle is incomplete: " + check.get().missing().size()
                + " marks are missing or wrong. &7Right-click the altar with an &dOccult Codex &7to see where.");
            return Outcome.INCOMPLETE_CIRCLE;
        }

        List<BlockMenu> bowlMenus = new ArrayList<>();
        List<Bowl> bowls = new ArrayList<>();
        for (int[] offset : check.get().pattern().positionsOf(Circles.OFFERING_BOWL, check.get().rotation())) {
            BlockMenu menu = BlockStorage.getInventory(altar.getRelative(offset[0], 0, offset[1]));
            ItemStack content = menu == null ? null : menu.getItemInSlot(OfferingBowl.SLOT);
            bowlMenus.add(menu);
            bowls.add(MenuUtils.isEmpty(content) ? Bowl.EMPTY : new Bowl(MenuUtils.keyOf(content), content.getAmount()));
        }

        ItemStack centerItem = altarMenu.getItemInSlot(RitualAltar.CENTER_SLOT);
        Optional<RitualMatcher.Match> match = RitualMatcher.match(recipes, MenuUtils.keyOf(centerItem), bowls, check.get().tier());
        if (match.isEmpty()) {
            tell(player, "&7The circle stays silent: nothing answers to these offerings.");
            return Outcome.NO_MATCH;
        }
        RitualRecipe recipe = match.get().recipe();
        if (recipe.isSummon()) {
            BossSpec spec = specs.get(recipe.bossId());
            if (spec == null || !bosses.canSummon(altar.getLocation(), spec.arenaRadius())) {
                tell(player, "&cAnother summoning is too close. Arenas may not overlap.");
                return Outcome.ARENA_OCCUPIED;
            }
        }

        // Take everything before anything else happens, so the inputs can never be taken back out.
        List<Taken> taken = new ArrayList<>();
        if (recipe.center() != null) {
            taken.add(new Taken(altarMenu, RitualAltar.CENTER_SLOT, one(centerItem)));
            altarMenu.consumeItem(RitualAltar.CENTER_SLOT, 1);
        }
        int[] take = match.get().bowlAmounts();
        for (int i = 0; i < take.length; i++) {
            if (take[i] > 0) {
                ItemStack item = bowlMenus.get(i).getItemInSlot(OfferingBowl.SLOT).clone();
                item.setAmount(take[i]);
                taken.add(new Taken(bowlMenus.get(i), OfferingBowl.SLOT, item));
                bowlMenus.get(i).consumeItem(OfferingBowl.SLOT, take[i]);
            }
        }

        List<Location> bowlLocations = new ArrayList<>();
        for (BlockMenu menu : bowlMenus) {
            if (menu != null) {
                bowlLocations.add(menu.getLocation().getBlock().getLocation());
            }
        }

        Session session = new Session(altar, recipe, check.get().rotation(), bowlLocations, taken, player == null ? null : player.getUniqueId());
        sessions.put(altar.getLocation(), session);
        locked.add(altar.getLocation());
        locked.addAll(bowlLocations);
        session.start();
        return Outcome.STARTED;
    }

    /** Called on plugin disable: crafting rituals finish, summoning rituals give everything back. */
    public void shutdown() {
        holograms.clearAll();
        for (Session session : new ArrayList<>(sessions.values())) {
            if (session.recipe.isSummon()) {
                session.returnOfferings();
            } else {
                session.finish(false);
            }
        }
    }

    private static ItemStack one(ItemStack item) {
        ItemStack copy = item.clone();
        copy.setAmount(1);
        return copy;
    }

    private static java.util.function.BiFunction<Integer, Integer, String> lookupAround(Block altar) {
        return (dx, dz) -> BlockStorage.checkID(altar.getRelative(dx, 0, dz));
    }

    private static void tell(@Nullable Player player, String message) {
        if (player != null) {
            player.sendMessage(MenuUtils.color(message));
        }
    }

    private final class Session {

        private final Block altar;
        private final RitualRecipe recipe;
        private final int rotation;
        private final List<Location> bowls;
        private final List<Taken> taken;
        private final UUID playerId;
        private BukkitTask task;
        private int elapsed;

        Session(Block altar, RitualRecipe recipe, int rotation, List<Location> bowls, List<Taken> taken, @Nullable UUID playerId) {
            this.altar = altar;
            this.recipe = recipe;
            this.rotation = rotation;
            this.bowls = bowls;
            this.taken = taken;
            this.playerId = playerId;
        }

        void start() {
            altar.getWorld().playSound(center(), recipe.isSummon() ? Sound.ENTITY_EVOKER_PREPARE_SUMMON : Sound.BLOCK_BEACON_ACTIVATE, 1F, 0.8F);
            task = Bukkit.getScheduler().runTaskTimer(plugin, this::tick, STEP_TICKS, STEP_TICKS);
        }

        private void tick() {
            elapsed += STEP_TICKS;
            if (elapsed % 20 == 0 && !intact()) {
                fail();
                return;
            }
            if (elapsed >= DURATION_TICKS) {
                finish(true);
                return;
            }
            effects();
        }

        private boolean intact() {
            Optional<CircleCheck> check = checkCircle(altar);
            return check.isPresent() && check.get().rotation() == rotation && check.get().complete();
        }

        private void effects() {
            ThreadLocalRandom random = ThreadLocalRandom.current();
            Location top = center();
            Particle.DustOptions dust = recipe.isSummon() ? SUMMON_DUST : RITUAL_DUST;
            for (Location bowl : bowls) {
                Location from = bowl.clone().add(0.5, 1.1, 0.5);
                for (int i = 0; i < 4; i++) {
                    double t = random.nextDouble();
                    Location point = from.clone().add(top.clone().subtract(from).toVector().multiply(t));
                    altar.getWorld().spawnParticle(Particle.DUST, point, 1, 0, 0, 0, 0, dust);
                }
            }
            altar.getWorld().spawnParticle(recipe.isSummon() ? Particle.SOUL : Particle.ENCHANT, top, 12, 0.4, 0.3, 0.4, 0.05);
            if (elapsed % 20 == 0) {
                altar.getWorld().playSound(top, Sound.BLOCK_AMETHYST_BLOCK_CHIME, 1F, 0.6F + elapsed / (float) DURATION_TICKS);
            }
        }

        void finish(boolean withEffects) {
            end();
            if (recipe.isSummon()) {
                BossSpec spec = specs.get(recipe.bossId());
                ItemStack refund = recipe.center() == null || taken.isEmpty() ? null : taken.get(0).item().clone();
                bosses.summon(recipe.bossId(), spec, altar, refund);
                return;
            }

            SlimefunItem output = recipe.outputId() == null ? null : SlimefunItem.getById(recipe.outputId());
            if (output == null) {
                return;
            }
            ItemStack result = output.getItem().clone();
            result.setAmount(recipe.outputAmount());

            BlockMenu menu = BlockStorage.getInventory(altar);
            if (menu != null && MenuUtils.isEmpty(menu.getItemInSlot(RitualAltar.CENTER_SLOT))) {
                menu.replaceExistingItem(RitualAltar.CENTER_SLOT, result);
            } else {
                altar.getWorld().dropItemNaturally(center(), result);
            }

            if (withEffects) {
                altar.getWorld().spawnParticle(Particle.SOUL_FIRE_FLAME, center(), 40, 0.3, 0.4, 0.3, 0.05);
                altar.getWorld().spawnParticle(Particle.END_ROD, center(), 20, 0.2, 0.6, 0.2, 0.02);
                altar.getWorld().playSound(center(), Sound.ENTITY_EVOKER_CAST_SPELL, 1F, 1F);
                tell(player(), "&dThe ritual is complete.");
            }
        }

        /** Put back everything this ritual took (used when the server stops mid-summon). */
        void returnOfferings() {
            end();
            for (Taken t : taken) {
                if (t.menu() != null && MenuUtils.isEmpty(t.menu().getItemInSlot(t.slot()))) {
                    t.menu().replaceExistingItem(t.slot(), t.item());
                } else if (t.menu() != null) {
                    ItemStack rest = t.menu().pushItem(t.item(), t.slot());
                    if (rest != null) {
                        altar.getWorld().dropItemNaturally(center(), rest);
                    }
                }
            }
        }

        private void fail() {
            end();
            altar.getWorld().spawnParticle(Particle.LARGE_SMOKE, center(), 30, 0.4, 0.4, 0.4, 0.02);
            altar.getWorld().playSound(center(), Sound.BLOCK_FIRE_EXTINGUISH, 1F, 0.6F);
            tell(player(), "&cThe circle was broken. The offerings are lost.");
        }

        private void end() {
            if (task != null) {
                task.cancel();
            }
            sessions.remove(altar.getLocation());
            locked.remove(altar.getLocation());
            bowls.forEach(locked::remove);
        }

        private Location center() {
            return altar.getLocation().add(0.5, 1.3, 0.5);
        }

        @Nullable
        private Player player() {
            return playerId == null ? null : Bukkit.getPlayer(playerId);
        }
    }
}
