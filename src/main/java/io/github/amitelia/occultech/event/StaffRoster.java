package io.github.amitelia.occultech.event;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * The raid roster, read from config {@code raid.roster} (a list of maps, as Bukkit's {@code getMapList} gives it).
 * Staff join, change rank and retire: all of that is config, never code. A member with {@code with: <name>} shares
 * one slot with that partner, and the partner isn't picked on their own. Bad entries are skipped and reported in
 * {@link #problems()}. Pure Java, unit tested.
 */
public final class StaffRoster {

    private final Map<String, StaffMember> members = new LinkedHashMap<>();
    private final List<List<StaffMember>> slots = new ArrayList<>();
    private final List<String> problems = new ArrayList<>();

    private StaffRoster() {}

    @Nonnull
    public static StaffRoster parse(@Nullable List<? extends Map<?, ?>> entries) {
        StaffRoster roster = new StaffRoster();
        if (entries == null) {
            return roster;
        }
        for (Map<?, ?> entry : entries) {
            StaffMember member = roster.member(entry);
            if (member != null) {
                roster.members.put(member.name().toLowerCase(Locale.ROOT), member);
            }
        }
        roster.pair();
        return roster;
    }

    @Nullable
    private StaffMember member(Map<?, ?> entry) {
        String name = text(entry.get("name"));
        if (name == null) {
            problems.add("A roster entry has no name: " + entry);
            return null;
        }
        if (members.containsKey(name.toLowerCase(Locale.ROOT))) {
            problems.add(name + " is on the roster twice; the second entry is ignored");
            return null;
        }
        Archetype archetype = Archetype.parse(text(entry.get("archetype")));
        if (archetype == null) {
            problems.add(name + " has no valid archetype (" + entry.get("archetype") + ")");
            return null;
        }
        List<String> signatures = new ArrayList<>();
        if (entry.get("signatures") instanceof List<?> list) {
            for (Object signature : list) {
                if (text(signature) != null) {
                    signatures.add(text(signature).toLowerCase(Locale.ROOT));
                }
            }
        }
        String display = text(entry.get("display"));
        String title = text(entry.get("title"));
        String skin = text(entry.get("skin"));
        double scale = entry.get("scale") instanceof Number number ? number.doubleValue() : 1;
        return new StaffMember(name, display == null ? name : display, title == null ? "" : title, skin == null ? name : skin,
            archetype, signatures, text(entry.get("with")), scale);
    }

    /** Builds the slots: a member alone, or a member with their partner. */
    private void pair() {
        Set<String> partners = new HashSet<>();
        for (StaffMember member : members.values()) {
            if (member.partner() == null) {
                continue;
            }
            StaffMember partner = members.get(member.partner().toLowerCase(Locale.ROOT));
            if (partner == null || partner == member) {
                problems.add(member.name() + " fights with " + member.partner() + ", who isn't on the roster");
            } else if (partner.partner() != null) {
                problems.add(member.name() + " and " + partner.name() + " both name a partner; only one of a pair may");
            } else if (!partners.add(partner.name().toLowerCase(Locale.ROOT))) {
                problems.add(partner.name() + " is the partner of two members");
            }
        }
        for (StaffMember member : members.values()) {
            String key = member.name().toLowerCase(Locale.ROOT);
            if (partners.contains(key)) {
                continue;   // fights in their partner's slot
            }
            StaffMember partner = member.partner() == null ? null : members.get(member.partner().toLowerCase(Locale.ROOT));
            if (partner != null && partners.contains(partner.name().toLowerCase(Locale.ROOT))) {
                slots.add(List.of(member, partner));
            } else {
                slots.add(List.of(member));
            }
        }
    }

    @Nullable
    private static String text(@Nullable Object value) {
        if (value == null) {
            return null;
        }
        String text = value.toString().trim();
        return text.isEmpty() ? null : text;
    }

    /** Every member by lower-case name. */
    @Nonnull
    public Map<String, StaffMember> members() {
        return Collections.unmodifiableMap(members);
    }

    /** What a raid picks from: one member, or a pair who fight together. */
    @Nonnull
    public List<List<StaffMember>> slots() {
        return Collections.unmodifiableList(slots);
    }

    @Nonnull
    public List<String> problems() {
        return Collections.unmodifiableList(problems);
    }
}
