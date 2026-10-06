# Boss review round 2: plan (Sessions R1-R5)

From the user's playtest of all 19 bosses (2026-10-05). Each session ends with the self-test, the balance report and a
short list of what to try in game.

| Session | Bosses | Main work |
|---|---|---|
| **R1** | Brood Mother, The Unbound, Night Matriarch, Mirrored Magus, Archevoker | Numbers, plus small attack additions |
| **R2** | Abyssal Warden, Blaze Choir, Tempest, Drowned Elder | Solo balance, the last singer's shield, slowing the Tempest, smoother Elder movement |
| **R3** | Hollow Warlord, Corrupted Colossus, Dread Riders, plus tier-3 damage | Hits strong enough for Infinity armor, which keeps regenerating; target switching; health |
| **R4** | Heartwood Horror | Rework: always attacks, many more area attacks, heavier hits |
| **R5** | Doppelganger | Less tanky, ground attacks that work, a dark copy of the player, the player's exact name |

Tidebreaker, Volley, the Witch Coven and the Sovereign stay as they are: they were judged balanced or perfect.

## R1: tier 0-1 - DONE (self-test 351/351)

- **Brood Mother:** too easy. More health (220 → 320) and faster (movement 0.32 → 0.37).
- **The Unbound:** too easy in a group.
  - Swings a little faster: one swing every 1.2 s (it was every 1.5 s).
  - Thralls rise more often: every 14 s (it was every 20 s). Each wave has 2 thralls, +1 for each extra player
    (up to 4).
- **Night Matriarch:** too easy, slow, weak, not tanky. Vanilla phantom AI swoops only now and then.
  - Health 260 → 380.
  - A scripted **rake**: whenever it passes within reach of a player, it bites, at most once a second.
  - Dives come more often: every 5 s by day, 4 s at night (it was 8 s / 6 s). It stays stunned for 1.5 s after a dive
    (it was 2 s).
  - Phantom swarms come every 12 s (it was 20 s), more of them in a group.
- **Mirrored Magus:** does no damage, only evades. The illusioner prefers casting spells over shooting.
  - A scripted **mirror volley**: 3 arrows at its target every 3 s.
  - A **prism burst**: a telegraphed ring under a player every 10 s, magic damage.
- **Archevoker:** fun, but the vexes out-damage it, and it keeps running away.
  - The evoker's flee-from-players goal is removed. Instead it holds about 6 blocks from its target.
  - Fang patterns come faster: every 6 s, 4 s when enraged (it was 8 s / 5.5 s). Fangs hit harder (10 → 12).
  - Getting close is answered with a **fang burst**: a quick ring of fangs around it.
  - Vexes hit softer (9 → 7).

## R2: tier 2 - DONE (self-test 352/352)

- **Abyssal Warden:** pretty hard, and very hard solo. Fewer beams for a solo player, and a longer gap between beams
  and spikes. Health a little lower.
- **Blaze Choir:** the last singer always keeps the shield. The shield only passes while two or more singers are
  alive; the last one is never shielded.
- **Tempest:** too fast, attacks too fast, too hard to hit.
  - Slower movement.
  - Longer gaps between wind-charge volleys and bursts.
  - It holds still for a moment after each burst, so it can be hit.
  - A slightly bigger hitbox.
- **Drowned Elder:** jittery movement.
  - It turns at a capped rate, so no fast spins.
  - It glides instead of snapping around its target.
  - It keeps a target for at least 8 s.

## R3: tier 3, part 1 - DONE (self-test 352/352)

- **Tier-3 hits must matter against Infinity armor**, which carries Regeneration and Resistance. The model gets
  Regeneration, and the tier-3 bands get a higher floor. Small chip hits are dropped in favour of fewer, heavier blows.
- **Hollow Warlord:**
  - Bug: it locks onto one target forever. It will re-pick its target every 6-10 s, the top damager or the nearest
    player.
  - Higher damage, less health.
- **Corrupted Colossus:** underwhelming. More frequent slams and pylon beams, and a faster melee.
- **Dread Riders:**
  - The Outrider stops now and then to aim and shoot, a window to hit it.
  - Its horse gets a smaller hitbox.
  - Both riders hit harder.
- **Health** for the tier-3 bosses called too tanky comes from the playtest logs.

## R4: Heartwood Horror rework - DONE (self-test 353/353)

- **Always attacks.** The creaking freezes while looked at (vanilla). That's replaced by our own movement and attacks,
  which keep going whether you look or not.
- **Area attacks:**
  - root eruptions in lines;
  - a sap rain over several marked spots;
  - a ground slam ring;
  - thorn pulses around its hearts.
- **Hits:** fewer but much stronger.

## R5: Doppelganger

- **Health:** less tanky.
- **Ground attacks:** fixed. The echo and fire stances currently show effects without reliably dealing damage. They'll
  get telegraphed markings that land their hit.
- **The copy:** a dark version of the Doppelganger itself (the same player skin, darkened and translucent), instead of
  the shadow cloud.
- **Name:** exactly the copied player's name (it gets the same name tag colour), so nothing tells the real one apart.
