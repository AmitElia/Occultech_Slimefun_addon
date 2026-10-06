# Balance and optimization plan (Sessions B1-B3, G8)

## Benchmark kits (what each tier is tuned against)

| Tier | Armor | Weapon | Raw sword DPS* |
|---|---|---|---|
| 0 | Iron, Protection II | Iron sword, Sharpness II | ~12 |
| 1 | Diamond, Protection IV (and later the new tier-1 set) | Diamond sword, Sharpness V | ~16 |
| 2 | Netherite, Protection IV (Abyssal armor matches this) | Netherite sword, Sharpness V | ~18 |
| 3 | Infinity: Protection XX, Strength II, Resistance I, Regeneration | Infinity sword (netherite, Sharpness XX) | ~39 |

\* Hits at full charge, 1.6 per second, no crits. The tier-3 figures were read from InfinityExpansion2's config on the test server.

**Protection is capped** (checked in the 26.2 game code: `CombatRules` clamps it at 20 points, an 80% cut).
- 4 × Protection IV = 16 points (64%).
- 4 × Protection V = 20 points, already at the cap.
- 4 × Protection X adds nothing over V. It only reaches the cap with fewer pieces: 2 Hollow pieces alone get there.

## What the numbers say today

Effective boss health = health ÷ the boss's damage multiplier (its "armor"), in raw player damage. Times are at
benchmark sword DPS with 100% uptime: real fights are slower (dodging, invulnerable phases, adds).

| Boss | Health | Damage taken | Effective HP | Solo, sword, no mechanics | Group of 3 (+50% HP) |
|---|---|---|---|---|---|
| Hollow Warlord | 400 | 0.18 (0.108 guarded) | 2,222 (3,700) | 57 s (95 s) | 29 s (47 s) |
| Heartwood Horror | 320 | 0.125, 0 while hearts stand | 2,560 | 66 s + heart phases | 33 s + phases |
| Dread Riders | 200 + 260 | 0.1 / 0.05 | **7,200** | 185 s | 92 s |
| Corrupted Colossus | 400 | 0.1 | 4,000 | 103 s | 51 s |
| Doppelganger | 360 | 0.1, reflections | 3,600 | 92 s + reflections | 46 s + |
| Gallus (gate) | 500 + rider 120 | 0.05 | **10,000+** | 256 s + phases, eggs | 128 s + |

Tier 3 is far tankier than tiers 0-2, and the Dread Riders and Gallus stand out. "Long in a group of 3" fits: half of
each fight is phases where damage doesn't land, and the group scaling still adds health per player with no limit.

**Held weapons** get a ×2.5 bonus against bosses, and their hits ignore invulnerability frames:

| Weapon | Hit | Interval | Bursts | Average raw DPS | Compared with |
|---|---|---|---|---|---|
| Soulfire Censer (tier 3) | 9 × 2.5 = 22.5 | 0.4 s | 5 s on, 3 s off | **~35** | ~0.9 of an Infinity sword |
| Wyrmbreath (tier 2) | 4 × 2.5 = 10 | 0.4 s | 3.3 s on, 3 s off | **~13** | ~0.7 of a netherite sword |

- **The Censer** also reaches 9 blocks, hits everything in its cone, and never has to stand in melee range. That is
  why it's too strong.
- **Wyrmbreath:**
  - Its 6-block, 25° cone often misses tier-2 bosses, which hover and fly.
  - Bosses never visibly burn: we cancel their burning.
  - A tier-2 boss loses about 1% health per hit, so nothing reads as damage.

## Group scaling: a curve with a cap (replaces the current +25% health per extra player)

**Decided (2026-10-04): the tougher curve.** Health × 1 + 0.45 × (n − 1)^0.75, counting at most 5 players: ×1.45 / 1.76 / 2.03 / 2.27. A group of 3 kills in about 60% of the solo time. The table below was the first proposal.

Boss health × **1 + 0.3 × (n − 1)^0.8**, counting at most 6 players. Boss damage doesn't scale: in a group the attacks
spread over more targets, so each player takes less.

| Players | Today | New | Time to kill vs solo (new) |
|---|---|---|---|
| 1 | 1.00 | 1.00 | 1.00 |
| 2 | 1.25 | 1.30 | 0.65 |
| 3 | 1.50 | 1.52 | 0.51 |
| 4 | 1.75 | 1.72 | 0.43 |
| 5 | 2.00 | 1.91 | 0.38 |
| 6+ | 2.25+ (no limit) | 2.08 (cap) | 0.35 and below |

A group is always faster than solo, a large group stops making the boss tankier, and the curve flattens as players
are added.

## Session B1: measure (the boss's damage includes every mechanic) - DONE (self-test 348/348)

1. **Every mechanic is declared.** Each boss lists its attacks: name, raw damage, kind (melee, projectile, ground,
   beam, magic), and whether it's telegraphed. Hits go through one call, `fight.hit(player, mechanic)`, so every point
   of damage is attributed.
2. **The self-test grades the numbers.** It runs each mechanic through the real damage formula for the tier's
   benchmark kit (armor points, toughness, protection cap, set bonuses, Resistance). Then it checks the share of 20 HP
   that's left after armor. It fails if a mechanic falls outside its band:
   - chip and adds: 5-12%;
   - normal hits: 15-25% (the scope rule);
   - big telegraphed hits: 25-40%;
   - nothing untelegraphed above 25%.
3. **Combat log.** Each fight writes a record to `plugins/Occultech/combat-log/`:
   - its length and how long the boss could actually be damaged (uptime);
   - damage taken by each player, per mechanic, raw and after armor;
   - deaths;
   - damage to the boss, per weapon;
   - group size.

   `/occultech fights stats` shows the record of a running fight.
4. **`/occultech kit <tier>`** hands out the tier's benchmark kit, so playtests use the same gear every time.
5. **`tools/balance.py`** reads the logs and, for each boss, reports:
   - time to kill, solo and grouped;
   - the boss's DPS on each player, including all mechanics;
   - health lost per minute;
   - the share of the fight the boss could be damaged.

   It compares all of that with the targets.
6. **Playtest protocol:** each tier-3 boss solo and in a group of 3, with the benchmark kit. The logs are the test that
   the numbers get judged against.

### B1 outcome and how to playtest

- **Attack grades:** `/occultech balance` grades all 59 declared attacks and writes `plugins/Occultech/balance-report.md`.
  A copy is in `docs/balance-report.md`. 22 attacks are outside their band at Normal difficulty:
  - **Tiers 0-1 are far too soft** against their benchmark armor: Protection IV diamond leaves the tier-1 bosses
    hitting for 1-6% of health.
  - **Tier 2:** the Drowned Elder's beam is a bit high (43%) and the Tempest's squall ring slightly high (11%).
  - **Tier 3:** close to the bands. The Colossus's Smash is high (28%), and a few small hits are low.
- **Playtest steps (per boss):**
  1. `/occultech kit <tier>` gives the benchmark gear. Tier 3 gives the real Infinity items.
  2. Fight it: solo once, then in a group of 3. Use the showcase circles and `/occultech restock`.
  3. Run `python tools/balance.py` (it reads `run/plugins/Occultech/combat-log/`). It writes `docs/balance-playtests.md`:
     - fight length against the target, and how much of the fight the boss could be damaged;
     - the boss's damage per second on each player, every attack included;
     - deaths, and which attacks did the damage.

## Session B2: tune

- **Fight-length targets:**
  - mini-bosses: 1-3 min solo;
  - gate bosses: 4-8 min solo;
  - a group of 3: about half of that, per the curve.

  Health is set from the target time, the benchmark DPS and the uptime measured in the logs.
- **Tier 3, first pass from the model:**
  - Dread Riders: about −55% effective HP.
  - Gallus: about −35%.
  - Colossus and Doppelganger: about −20%.
  - Then confirm with the logs.
- **Group scaling:** the curve above, in `config.yml` (`bosses.group-scaling`, `bosses.group-cap`).
- **Held weapons get fixed numbers instead of the ×2.5 bonus.**
  - **Damage:** single-target damage about 0.6 of the tier's benchmark sword, since they're ranged and hit several
    targets. Censer: ~23 raw/s on average. Wyrmbreath: ~11 raw/s, but wider (8 blocks, 35°).
  - **Visible hits:** a flame burst and a hurt sound on each target.
  - **Invulnerability:** they keep the target's invulnerability frames, so they no longer stack on top of melee.
- **Armor:**
  - **Abyssal:** Protection IV and Unbreaking III on every piece (max netherite). Its set bonus stays.
  - **Hollow:** Protection X, Unbreaking X, and Thorns X on the Cuirass.
  - **Note:** because of the cap, a full Hollow set protects exactly as much as Protection V. Level 10 only helps with
    a partial set, and with durability.
  - **Decided:** Protection X and also extra armor toughness on each piece, so a full set takes less from big hits
    (still a little under Infinity).

### B2 part 1 outcome (no playtest needed) - DONE (self-test 351/351)

- **Attack damage:** all tier 0-2 attacks are now inside their bands. That's checked by the self-test, and
  `docs/balance-report.md` has the table.
  - **Tier 1 roughly doubled** (raw damage): Night Matriarch bite 9→20, dive 7→26; Unbound axe 11→20, cleave 9→26;
    Magus arrows 4→16; Archevoker fangs 6→12, vexes 4→9; tier-1 adds 2-3→9.
  - **Tier 0:** spiderlings 2→4, the Sovereign's shockwave 6→11, Volley's arrows ~3→6 (now fixed, not speed-based).
  - **Tier 2:** the Drowned Elder's beam 24→16, the Tempest's squall ring 6→4.
  - **Tier 3:** only the Colossus's Smash, 55→42. The 7 tier-3 attacks below their band stay as they are until the
    playtests, since tier 3 felt too hard.
- **Vanilla attacks now use their declared damage:** evoker fangs and vexes, illusioner arrows, witch potions and
  boss arrows (`fight.labelSpawns`, `fight.label`).
- **Group scaling:** the chosen curve, `bosses.group-scaling` / `group-exponent` / `group-cap` (×1.45 / 1.76 /
  2.03 / 2.27, capped at 5). It's unit-tested, and groups always kill faster than a solo player.
- **Held weapons** hit every 0.5 s (before: every 0.2 s).
  - The Censer goes from ~56 to ~25 boss damage per second.
  - Wyrmbreath stays at ~18/s but reaches 8 blocks over 35° (from 6 over 25°), and shows a flame burst and a sound on
    each target.
  - They no longer stack on a hit from the last half second. The Stormstring Bow's lightning still does, on its own
    arrow.
- **Armor:**
  - **Abyssal:** Protection IV and Unbreaking III on every piece; Thorns V stays on the chestplate.
  - **Hollow:** Protection X, Unbreaking X, and Thorns X on the Cuirass, plus +2 armor toughness per piece (5 per
    piece, 20 for the set).
  - The new `toughness` field in recipes.yml provides this. Items crafted before keep their old enchantments.
- **Left for part 2, after the playtests:** tier-3 health and armor from fight lengths and uptime, and the 7 low
  tier-3 attacks.

### B2 review round 1 (user playtest, 2026-10-04)

**Feedback:**
- Brood Mother: a little too easy.
- Volley, Witch Coven and the Sovereign: balanced.
- The Unbound: far too much damage in tier-1 gear, and attacks too fast.
- In general: difficult but manageable for every player, not only the best.

**Changes:**
- **Gentler bands for every tier:**
  - normal hits 8-18%;
  - telegraphed 12-30%;
  - adds 3-10%;
  - zones 2-8%.
- **Tier 1 at mid-band:**
  - The Unbound: axe 20→16 (10%), cleave 26→22 (17%). It also swings at most every 1.5 s (a new per-boss melee
    cooldown, `BossBehavior.meleeCooldownTicks`), moves a little slower, speeds up less as it weakens, and cleaves
    every 8 s instead of every 6 s.
  - Night Matriarch: bite 17.5, dive 23.
  - Archevoker: fangs 10.
- **Brood Mother:** bite 7→8 (13→15%).
- **Tier 2 brought under the new caps:** Warden beam 15.5, lash 23; Elder wave 33.5; Tidebreaker ram 33.5, thrust 23.
- **Tier 3 (only lowered):**
  - every big melee 39 (Colossus, Doppelganger, Vanguard, Gallus jab, Horror, Warlord);
  - Dread Riders charge 55;
  - Doppelganger's reflection capped at 22.

## Session B3: optimization

- **Timing:** each system's time per tick is measured: fights, servitors, decorations, held weapons, custom blocks,
  holograms, auras. `/occultech perf` shows it, with a budget per system.
- **Known costs to check:**
  - Particle volume: held weapons, fights with several hazards.
  - Nearby-entity scans: Servitor stray sweep, Guardian Eye, minions.
  - Block-storage lookups in move and step listeners.
  - Display entities per fight: floor markings, auras, streaks.
- **Load test:** 3 fights + 20 shrines + 50 decorations on the test server. Target: under 2 ms per tick for Occultech
  in total.

## Session G8 (later): tier-1 worn armor, the Frenzied set

- **Role:** matches enchanted diamond (diamond base, Protection IV, Unbreaking III). Set bonus: −10% damage from
  summoned creatures. That makes the tier ladder −10 / −20 / −25%.
- **Look, from the Frenzy Idol** (design talk 2026-10-06):
  - **Colours:** dusk-violet plates as the base, grey-silver trims and horns, ember orange only where it glows.
  - **Helm:** an open-face violet skullcap; a heavy silver brow ridge carrying the Idol's ember sun; the face showing,
    like the Abyssal and Hollow sets.
  - **Horns (decided):** large **bull horns** sweeping out to the sides and then up and forward. They're built from
    **chunky 3D box segments** along the curve, like the Frenzy Idol's horns, so they have volume from every angle;
    the earlier flat-plane idea read as a thin edge from the front. Ember-glowing tips that breathe (the helm item
    model can animate).
  - **Chestplate:** layered rounded violet pauldrons; a silver ridge down the middle with a small ember sun; ember
    seams between the plates.
  - **Leggings:** violet tassets with silver edges and an ember seam at the belt.
  - **Boots:** violet greaves, silver toe caps, a thin ember line.
  - **Fire (decided):** glow plus a few sparks. Bright ember seams in the worn textures (worn layers can't animate),
    the breathing horn tips and emblem on the helm, and with the full set, occasional sparse sparks drifting off the
    horn tips and pauldrons. Like the Hollow set's soul wisps, but warmer.
- **References** (described from their mod pages; check the galleries):
  - L_Ender's Cataclysm, Ignitium armor: fire living in the seams between dark plates.
  - Cataclysm, Cursium armor: horns built into the helm's silhouette.
  - Iron's Spells 'n Spellbooks, Pyromancer set: copper-orange as an accent.
  - Minecraft Dungeons armors: bold, chunky shapes that read at pixel scale.
  - Immersive Armors: vanilla coverage with character pieces.
  - Goety: the occult mood.
- **Follows the G6 lessons:**
  - vanilla netherite's coverage;
  - all 3D in the helm (the horns are the one exception to "flat silhouette planes": chunky segments, decided);
  - clean bevelled plates;
  - accents placed on the structure and mirrored;
  - no back pieces;
  - every model element inside −16..32.
- **Recipe:** tier-1 boss drops (Frenzied Edge, Dusk Membrane, Mirror Dust) plus diamond armor, at the Bound circle.
  Researches get new ids.
- **Work:** inventory icons, worn layers, the 3D helm, and the item, recipe, set bonus and effects in code. Several
  review rounds, as with G6.
