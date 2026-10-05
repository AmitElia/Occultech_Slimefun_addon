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
- **Look, from the Frenzy Idol:**
  - deep purple, grey and orange;
  - large ram horns curling back from the helm, drawn as flat silhouette planes like the warden's tendrils;
  - the face open, like the Abyssal and Hollow sets;
  - fiery effects: embers glowing along the plate seams (animated, sparse and bold), and a faint heat shimmer of orange
    sparks off the horns and pauldrons now and then.
- **Follows the G6 lessons:**
  - vanilla netherite's coverage;
  - all 3D in the helm;
  - clean bevelled plates;
  - accents placed on the structure and mirrored;
  - no back pieces;
  - every model element inside −16..32.
- **Recipe:** tier-1 boss drops (Frenzied Edge, Dusk Membrane, Mirror Dust) plus diamond armor, at the Bound circle.
  Researches get new ids.
- **Work:** inventory icons, worn layers, the 3D helm, and the item, recipe, set bonus and effects in code. Several
  review rounds, as with G6.
