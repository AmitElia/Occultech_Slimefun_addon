package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.annotation.Nonnull;

import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mannequin;

import io.github.amitelia.occultech.boss.BossBehavior;
import io.github.amitelia.occultech.boss.BossBlueprint;
import io.github.amitelia.occultech.boss.BossFight;
import io.github.amitelia.occultech.boss.BossSpec;
import io.papermc.paper.datacomponent.item.ResolvableProfile;

/**
 * A staff member on the raid floor (Act 1): a Mannequin wearing their skin, with their name and role above it, fighting
 * with their archetype's kit ({@link StaffKit}). A pair (Earl + Sam) is one slot with two bodies; the slot is cleared
 * when both are down. Signatures (E3-E5) come on top of the kits.
 */
public final class StaffBehavior extends BossBehavior {

    public static final String ID = "RAID_STAFF";
    /** Each body of a pair has this share of a single member's health. */
    static final double PAIR_SHARE = 0.6;

    private final List<StaffMember> members;
    private final List<StaffKit> kits = new ArrayList<>();
    private RaidScaling.Body scale;

    /** {@code effective}: the health the slot should have for its group (before the pair split). */
    public StaffBehavior(BossFight fight, List<StaffMember> members, double effective) {
        super(fight);
        this.members = List.copyOf(members);
        setEffective(effective);
    }

    /** The fight data for a slot holding {@code members}, {@code radius} blocks around its spot. */
    @Nonnull
    public static BossSpec spec(List<StaffMember> members, double radius) {
        String name = members.size() == 1 ? members.get(0).display() : members.get(0).display() + " & " + members.get(1).display();
        return new BossSpec(ID, name, RaidService.BENCHMARK_TIER, false, "", 0, radius, 3600, Map.of(), Map.of(), 0);
    }

    /** A blueprint that puts {@code members} on the floor with {@code effective} health. */
    @Nonnull
    public static BossBlueprint blueprint(List<StaffMember> members, double effective) {
        return new BossBlueprint(ID, StaffBehavior.class, fight -> new StaffBehavior(fight, members, effective));
    }

    private void setEffective(double effective) {
        this.scale = RaidScaling.body(effective * (members.size() > 1 ? PAIR_SHARE : 1));
    }

    @Override
    public void spawn(Location at) {
        for (int i = 0; i < members.size(); i++) {
            StaffMember member = members.get(i);
            Location spot = at.clone().add(members.size() > 1 ? (i == 0 ? -1.5 : 1.5) : 0, 0.2, 0);
            Mannequin body = fight.spawnBoss(Mannequin.class, spot, m -> {
                m.setCustomName(ChatColor.WHITE + member.display());
                m.setCustomNameVisible(true);
                m.setDescription(net.kyori.adventure.text.Component.text(member.title(), net.kyori.adventure.text.format.NamedTextColor.AQUA));
                // their skin, looked up by name (the game fetches it from Mojang, as for player heads)
                m.setProfile(ResolvableProfile.resolvableProfile().name(member.skin()).build());
                BossFight.setAttribute(m, Attribute.MAX_HEALTH, scale.maxHealth());
            });
            if (member.scale() != 1) {
                BossFight.setAttribute(body, Attribute.SCALE, member.scale());
            }
            kits.add(StaffKit.of(member.archetype(), fight, body, member, spot));
        }
        if (kits.size() == 2) {
            kits.get(0).partner = kits.get(1);
            kits.get(1).partner = kits.get(0);
        }
        // signatures last: a pair's need to know their partner
        kits.forEach(StaffKit::setup);
    }

    private StaffKit kitOf(LivingEntity body) {
        for (StaffKit kit : kits) {
            if (kit.body == body) {
                return kit;
            }
        }
        return null;
    }

    @Override
    public void onDamagedBy(LivingEntity boss, org.bukkit.entity.Player player, double damage) {
        StaffKit kit = kitOf(boss);
        if (kit != null) {
            kit.onHitBy(player, damage);
        }
    }

    @Override
    public void onAddDeath(org.bukkit.entity.Entity entity, @javax.annotation.Nullable org.bukkit.entity.Player killer) {
        kits.forEach(kit -> kit.onAddDeath(entity, killer));
    }

    @Override
    public boolean deflectProjectile(LivingEntity boss, org.bukkit.entity.Projectile projectile) {
        StaffKit kit = kitOf(boss);
        return kit != null && kit.deflect(projectile);
    }

    /** The signatures each body carries that are built (self-test). */
    public List<String> signatureIds() {
        List<String> ids = new ArrayList<>();
        for (StaffKit kit : kits) {
            for (Signature signature : kit.signatures()) {
                ids.add(signature.getClass().getSimpleName());
            }
        }
        return ids;
    }

    /** The members in this slot. */
    public List<StaffMember> members() {
        return members;
    }

    /** A new effective health (the admin changed {@code event hp}): every body keeps its share of health left. */
    public void rescale(double effective) {
        setEffective(effective);
        for (StaffKit kit : kits) {
            AttributeInstance max = kit.body.getAttribute(Attribute.MAX_HEALTH);
            if (!kit.alive() || max == null) {
                continue;
            }
            double fraction = kit.body.getHealth() / max.getValue();
            max.setBaseValue(scale.maxHealth());
            kit.body.setHealth(Math.max(1, fraction * max.getValue()));
        }
    }

    @Override
    public double modifyIncomingDamage(LivingEntity boss, double damage) {
        StaffKit kit = kitOf(boss);
        return damage * scale.damageTaken() * (kit == null ? 1 : kit.incomingFactor());
    }

    @Override
    public void move() {
        kits.forEach(StaffKit::move);
        kits.forEach(StaffKit::moveSignatures);
    }

    @Override
    public void tick() {
        int now = fight.elapsed();
        kits.forEach(kit -> kit.tick(now));
    }

    @Override
    public double verticalLeash() {
        return 6;
    }
}
