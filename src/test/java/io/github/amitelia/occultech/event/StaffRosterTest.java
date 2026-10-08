package io.github.amitelia.occultech.event;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import org.junit.jupiter.api.Test;

class StaffRosterTest {

    private static Map<String, Object> entry(Object... pairs) {
        java.util.LinkedHashMap<String, Object> map = new java.util.LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) {
            map.put((String) pairs[i], pairs[i + 1]);
        }
        return map;
    }

    @Test
    void readsMembersWithDefaults() {
        StaffRoster roster = StaffRoster.parse(List.of(
            entry("name", "KonTheJester", "display", "Kon", "title", "Moderator", "archetype", "hexer", "signatures", List.of("Decoys")),
            entry("name", "goobtbh", "archetype", "CONTROLLER")));
        assertTrue(roster.problems().isEmpty(), roster.problems().toString());
        StaffMember kon = roster.members().get("konthejester");
        assertEquals("Kon", kon.display());
        assertEquals("KonTheJester", kon.skin());
        assertEquals(Archetype.HEXER, kon.archetype());
        assertTrue(kon.has("decoys"));
        StaffMember goob = roster.members().get("goobtbh");
        assertEquals("goobtbh", goob.display());
        assertEquals("", goob.title());
        assertEquals(2, roster.slots().size());
    }

    @Test
    void badEntriesAreSkippedAndReported() {
        StaffRoster roster = StaffRoster.parse(List.of(
            entry("display", "Nobody", "archetype", "hexer"),
            entry("name", "a", "archetype", "wizard"),
            entry("name", "b", "archetype", "bruiser"),
            entry("name", "B", "archetype", "bruiser"),
            entry("name", "c", "archetype", "bruiser", "with", "ghost")));
        assertEquals(4, roster.problems().size(), roster.problems().toString());
        assertEquals(2, roster.members().size());
        assertEquals(2, roster.slots().size(), "c still fights, alone");
    }

    @Test
    void aPairIsOneSlot() {
        StaffRoster roster = StaffRoster.parse(List.of(
            entry("name", "EarlTheDwarf", "archetype", "bruiser", "with", "SneakySamInc"),
            entry("name", "SneakySamInc", "archetype", "skirmisher"),
            entry("name", "solo", "archetype", "hexer")));
        assertTrue(roster.problems().isEmpty(), roster.problems().toString());
        assertEquals(2, roster.slots().size());
        List<StaffMember> pair = roster.slots().get(0);
        assertEquals(List.of("EarlTheDwarf", "SneakySamInc"), pair.stream().map(StaffMember::name).toList());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shippedRosterIsClean() throws Exception {
        try (java.io.InputStream in = StaffRosterTest.class.getResourceAsStream("/config.yml")) {
            Map<String, Object> config = new org.yaml.snakeyaml.Yaml().load(in);
            Map<String, Object> raid = (Map<String, Object>) config.get("raid");
            StaffRoster roster = StaffRoster.parse((List<Map<?, ?>>) raid.get("roster"));
            assertTrue(roster.problems().isEmpty(), roster.problems().toString());
            assertEquals(28, roster.members().size());
            assertEquals(27, roster.slots().size(), "Earl and Sam share a slot");
            assertTrue(roster.slots().stream().anyMatch(slot -> slot.size() == 2 && slot.get(0).name().equals("EarlTheDwarf")));
            assertEquals(0.7, roster.members().get("earlthedwarf").scale(), 1e-9);
            assertEquals(1, roster.members().get("sneakysaminc").scale(), 1e-9);
        }
    }

    @Test
    void pickerNeverRepeatsBeforeEveryoneHasBeenOut() {
        StaffRoster roster = StaffRoster.parse(List.of(
            entry("name", "a", "archetype", "bruiser"), entry("name", "b", "archetype", "bruiser"),
            entry("name", "c", "archetype", "bruiser"), entry("name", "d", "archetype", "bruiser")));
        RosterPicker picker = new RosterPicker(roster.slots(), new Random(7));
        Set<String> seen = new HashSet<>();
        for (int i = 0; i < 4; i++) {
            assertTrue(seen.add(picker.next(Set.of()).get(0).name()), "a repeat within one deck");
        }
        assertEquals(4, seen.size());
    }

    @Test
    void pickerSkipsWhoIsOnTheFloor() {
        StaffRoster roster = StaffRoster.parse(List.of(
            entry("name", "a", "archetype", "bruiser"), entry("name", "b", "archetype", "bruiser")));
        RosterPicker picker = new RosterPicker(roster.slots(), new Random(1));
        List<StaffMember> first = picker.next(Set.of());
        // the other one is out; the deck has only the first left, who is on the floor: a fresh deck still avoids them
        List<StaffMember> second = picker.next(Set.of(first.get(0).name()));
        assertNotEquals(first.get(0).name(), second.get(0).name());
        assertNull(picker.next(Set.of("a", "b")), "everyone is on the floor");
    }
}
