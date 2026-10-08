# Staff Raid - server-wide event boss (plan, locked 2026-10-07)

A raid for 25+ players against the server's own staff. **It sits outside the tier progression.** Admins run it
at a preset arena; nobody summons it with a ritual. It reuses the boss engine (`BossFight`, `Mechanic`, `fight.hit`,
combat log, the no-griefing rules) but has its own package (`event/`), config section and scaling.
Staff have agreed to the idea. Rewards are not designed yet.

## Ground rules
- **The roster lives in config**, never in code. Each entry has a username, a skin (a player name or texture), an
  archetype and up to three signature abilities (ids of ability classes). Staff changes only mean config edits.
- **Benchmark gear: max-enchanted netherite** (`ArmorModel.TIER_2`). Every attack is a `Mechanic`, graded by
  `/occultech balance` against that kit: a normal hit costs 8-18% of a player's HP and a big telegraphed one 12-30%.
  Nothing one-shots. A failed raid mechanic is capped at 40%.
- **Bodies are Mannequins** that wear the staff skin. An invisible driver mob handles the AI and melee, as in
  `Doppelganger`. No world blocks change. Walls, TNT, meteors and lasers are display entities, and the plugin deals
  the damage.
- **Exceptions to the "never move players" rule.** Chlo, Pancake and S4MURAI move players. This is allowed only
  inside the event arena, under the safety rules at the end.

## Arena and commands
- `/occultech event arena set <radius>` saves the arena center and radius (about 45). Setup refuses a roofed arena:
  the sky has to be open 30 blocks above the floor, because players get thrown up.
- `/occultech event start [targets] [players]` starts Act 1 (the numbers override the staff on the floor and the player count it scales for), `event skip` goes on to Act 2, and `event stop` ends the event
  and cleans up. `event hp <multiplier>` changes boss health during the event, for tuning live on the first runs.
- Participants are everyone inside the arena, and players can join mid-event. A player who dies respawns at the arena
  edge (`PlayerRespawnEvent`, only while the event runs) and can run back in. Elytra gliding is off inside the arena.

## Act 1 - the Staff Floor
- **Number of targets:** `N = clamp(round(players / 2.5), 2, 10)`, or the `[targets]` given in the command. Each
  target stands in its own part of the arena with a small leash (about 10 blocks), so the crowd splits up into
  groups of about 2-3.
- **Who appears is random each run,** with no repeats until the roster runs out. Earl + Sam take up one target
  between the two of them.
- **Refill:** when a target dies, a new random staff member spawns in its spot. Act 1 ends after `2 × N` kills, or
  after 8 minutes. Then the remaining minis leave in a puff of smoke.
- **Every staff member has the same stats.** Health per mini: `staff-health × (players / N)^0.9`, fixed when it spawns (`event hp` changes it live).

### Six archetypes
Each one sets the base movement and melee and one generic move. The signature abilities below are added on top.

| Archetype | Base | Melee | Generic move |
|---|---|---|---|
| Bruiser | slow (0.22), can't be knocked back | Heavy blow, every 1.5 s (15%) | **Ground slam**: a 4-block ring warns for 1.5 s, then hits and throws back (24%) |
| Controller | medium (0.24), keeps 6 blocks off | Shove that pushes you back (11%) | **Zone denial**: patches under up to 2 players warn for 1.5 s, then hurt every second for 5 s (4%/s) |
| Skirmisher | fast (0.34), backs off 1 s after each hit | Quick cut, every 0.75 s (9%) | **Dash**: a red lane warns for 1.25 s, then it dashes 10 blocks down it (19%) |
| Summoner | slow (0.22), keeps 8 blocks off | Swipe (9%) | **Helpers**: 2 weak zombies at a time, at most 3 (6% a hit) |
| Gadgeteer | medium (0.24), keeps 7 blocks off | Wrench (11%) | Takes turns: **Beam** (the lane warns for 1.5 s and fires where aimed, 18%, ignores armor), **Trap** (a marked circle that snaps on the first player in, 17% + slowness; up to 3) |
| Hexer | medium (0.26), keeps 7 blocks off | Hex touch (9%) | **Mark**: a player glows for 3 s, then the mark bursts on everyone within 3 blocks of them (16%, ignores armor) |

Shares are what one hit takes from a player in the benchmark kit (`/occultech balance` grades them, Session E2).
Act 1 also calls out each beaten staff member with the kill count, says who steps into an emptied slot, and gives a one-minute warning.
A staff member's moves take turns: while a warned move is under way, nothing else starts, and a signature that's due goes before the archetype's move.

### Signatures
| Staff | Archetype | Signature |
|---|---|---|
| MrTroxy, Dj | Gadgeteer | **hotfix** takes turns between three moves. **Beam**: a lane warns for 1.5 s, then the word HOTFIX fires down it (18%, ignores armor). **Stamp**: HOTFIX appears on the floor inside a ring, then lands (19%). **Sweep**: a 150° fan warns, then a beam of HOTFIX words swings through it (16%, ignores armor). **system_bug**: glowing endermites and silverfish named `SYSTEM BUG`, 2 per call, at most 4, 6 health each (5% a bite). They can't burrow into blocks. **rollback**: the spot each nearby player stood on 4 s ago is marked ROLLBACK, then it breaks (14%, ignores armor) |
| Abusing | Bruiser | His skin is a creeper. **replicas**: half-size Mannequins of his skin, 2 per call and at most 6, that run at players. Next to one, a replica stops, swells and hisses inside a 3-block ring for 1.5 s, then bursts (17%). One hit kills a replica. **big_fuse**: he swells inside a 5-block ring for 2 s, then blasts everyone near him away (26%) |
| S4MURAI | Skirmisher | **enderstep**: projectiles never land; he steps 8-16 blocks away like an enderman, staying in his fight. **swap**: a melee hit trades places with the attacker (once every 4 s, only between two safe spots, never with someone in the air). **katana**: a red and black katana (boss-only; a netherite sword until the art pass). Takes turns between an **iai slash** (a red line warns, then he flashes to its end and cuts everyone on it, 24%) and a **crescent sweep** (a half ring in front of him, 21%) |
| Charles | Controller | Space theme. **meteors**: shadows grow under up to 3 players and 2 nearby spots, then magma meteors fall into them (19%). **moons**: 3 moons orbit him for 10 s and hurt on contact (13%, once a second). **black_hole**: it grows over him for 2 s, pulls everyone within 9 blocks in for 2 s (a sprint beats the pull), then collapses on whoever is within 3 (18%, ignores armor). **low_gravity**: a 7-block field of slow falling and high jumps for 6 s, now and then and whenever the black hole charges (potion effects only) |
| pyr0 | Bruiser | Cow theme. **stampede**: a wide lane warns, then he and 3 cows charge 12 blocks down it (21%). **moo**: a deep moo knocks back everyone in a 70° cone in front of him (15%). **milk**: below 75% health he stops to drink milk for 2 s and heals 12% unless 8% of his health in damage interrupts him ("spilled the milk!"). **hay**: shadows under up to 3 players, then hay bales drop (17%, slows) |
| Earl + Sam | Bruiser + Skirmisher (one slot) | A couple who fight together. **bond**: a tether between them hurts anyone crossing it (13%, ignores armor) and sweeps as they move. **together**: each takes half damage within 6 blocks of the other, so split them. When one falls the other is furious: 30% faster for the rest of the fight. **rescue**: once a fight, when one drops below 30% the healthier one dashes over and their health evens out. Earl is small (`scale: 0.7`) and slams. Sam's **daggers** poison for 3 s |
| mrlonelydwarf | Skirmisher | Mining theme with a diamond pickaxe. **burrow**: he digs down into the floor and comes up behind the most isolated player (the one farthest from any teammate). No blocks are broken. He sinks over 1 s with digging particles and the floor's own break sound, stays under for 2 s, then rises the same way behind his target. A ring marks the spot and his rise is the warning; then comes a pickaxe strike (26%). From the first dig until he's out, nothing hurts, knocks back or stops him, and arrows pass through. His name tag hides while he's underground |
| FM | Controller | **radio**: rings spread from him, and the pitch tells you which kind. **High chime**: three fast low rings; jump each one (15%). **Deep bass**: one slow ring too tall to jump, with a 3-block gap to walk through (19%) |
| Proxy, Atlas | Controller | Same kit. **walls**: two crossing walls rise through the group for 8 s (a line warns first). Touching one pushes you back to your side and shocks you (4%, at most once a second). **tnt**: takes turns between throwing TNT at up to 3 players and laying a line of 5 TNT down a lane that goes off one after another. Each TNT flashes for 2 s inside its ring (21%). The walls and TNT are displays; no real blocks |
| Kon | Hexer | **decoys**: 3 copies of him (same skin and name) wander the floor without attacking. Only the real Kon gives off a faint sparkle. Hitting a decoy pops it: you glow for 3 s and Kon slips to a new spot, often trading places with a decoy |
| bee_grand | Summoner | **bees**: 3 angry bees per call, at most 5 (4% a sting plus vanilla poison); vanilla bees die after stinging |
| Bat | Summoner | **bats**: 6 bats circle him for 2 s while he takes half damage, then a player's spot is marked for 1.5 s and the swarm dives on it (17%) |
| Griffon | Skirmisher | **mount**: he starts on a white horse (40 health, can't be ridden or kept) and charges down warned lanes (19%) instead of dashing. Kill the horse and he's on foot |
| Jenn | Summoner | **foxes**: 2 per call, at most 3. They dart in, bite (5%) and dart away for 1.5 s, then come back |
| Nick, Spleen | Hexer | **denied**: their hex mark shows a red DENIED over the marked player, stamped on the floor when it bursts |
| Jolly | Skirmisher | A funny, very fast archer (30% faster than a skirmisher, and he holds a bow). He keeps 9 blocks off and shoots instead of swinging: no melee and no dash. **trick_arrows**: an arrow every 1.5 s (11%), each carrying a random short annoying effect, its colour on the arrow and a line in your action bar: nausea, wither, slowness, blindness, hunger, a little levitation hop or glowing. **fart_jump**: when someone gets within 4 blocks (and now and then anyway), a loud fart and a brown-green cloud launch him 9-13 blocks to the spot farthest from everyone. Where he lands, a stink cloud gives nausea for 3 s (no damage). **whoopee_cushions**: 3 pink cushions dropped 2-4 blocks from players (never under them), at most 6, each lasting 15 s. Stepping on one gives a fart, a pop up of about 2.5 blocks and nausea. The fart is a vanilla stand-in (didgeridoo + slime) until the art pass adds a real sound to the pack |
| Raven | Summoner | **spiders**, the Brood Mother's (tier 0) abilities tuned for netherite and taken in turn. **Egg sacs**: 2 sacs that hatch 2 cave spiders each after 6 s unless smashed (3 hits; 5% a bite). **Web zone**: a player's spot warns for 1.5 s, then slows anyone inside for 8 s. **Pounce**: a ring warns under the nearest player more than 5 blocks off while he hisses, then he leaps onto it (19%) |
| goob, Amya, maka, OldeGrumpy, SuckedBean, YahooFlop, justafable | by role | Archetype only. A signature can be added later in config once one is written |

## Act 2 - The Council
X, Chlo and Pancake fight together and **share one health bar**. Damage on any of them counts. Their bodies can't
die until the bar is empty, and then all three fall together. Health:
`council-hp × players^0.9`, set when Act 2 starts. The engine's normal group scaling (capped at 5 players, ×2.27)
is far too low for a raid, so the event has its own curve. Health above 1024 goes through `modifyIncomingDamage`.

### Raid mechanics (the core of the act)
- **Soak circles.** Each circle's damage is split between the players standing in it. A circle needs about
  `players / 5`. Too few players inside → a capped hit on each of them. An empty circle → a capped hit on the whole raid.
- **AoE markers.** A marker follows a player for 3 s, then locks in place and bursts, so players spread out.
- **Moving barriers.** Walls sweep across the arena from one edge with a gap; you walk through the gap.
- **Spinning lasers.** Beams turn around a boss. Low beams you jump over, full-height beams have gaps.
- **Expanding rings.** Shockwaves you jump over.

### The toolkit (Session E6)
Each piece is built once and used by the Council's attacks. `/occultech event demo [soak|marker|barrier|laser|ring|all] [band 1-3]`
runs them on their own around an invulnerable dummy at the arena's middle (or where you stand), so you can try them before the Council exists.

| Piece | How it works | Default numbers (netherite) |
|---|---|---|
| Soak circle | A ring with a live `inside/needed` count and seconds left over it. It turns green when enough players stand in it. When it goes off, `needed x share` damage is split between those inside, at most about 40% each. An empty circle hits the whole raid | 2.5-block radius, 5 s warning. A share of 13% when the circle is soaked exactly. Each circle needs about players/5, with up to 3 circles at once |
| Player marker | A ring follows a marked player for 3 s, locks for 0.6 s, then bursts on everyone in it, the marked player included | 3-block radius, 16% (ignores armor) |
| Moving barrier | A wall across the whole floor, too tall to jump, with one 3.6-block gap. It shows at an edge for 2 s, then sweeps across. Touching it hurts once and shoves you along | 5 blocks/s, 15% |
| Spinning laser | Beams turning around a boss. They show still for 2 s first. A low beam is jumped; a full-height beam has a 2.5-block gap along it that you stand in as it passes. At the last band they reverse halfway | about 9 s a turn, for 10 s; 16% (ignores armor), at most once per 0.75 s |
| Expanding ring | `RaidRing` from E3. Low rings are jumped; tall ones have a gap | 7 blocks/s; 15% |

**Pace** (`RaidPace`, unit tested), from the shared bar:

| Bar | Mechanics at once | Cooldowns | Laser beams | Rings per stomp | Lasers reverse |
|---|---|---|---|---|---|
| 100-66% | 1 | x1 | 2 | 1 | no |
| 66-33% | 2 | x0.8 | 3 | 2 | no |
| 33-0% | 3 | x0.65 | 4 | 2 | yes |
| soft enrage (15 min) | the last band whatever the health, plus 5% more damage every 30 s | | | | |

### X - the Founder (giant)
A Mannequin scaled to about ×8.
- **Stomp**: rings spread out from his feet and you jump over them.
- **Founder's Sweep**: spinning lasers around him.
- **Foundation Stones**: he marks soak circles.
- **Kick**: a cone of forward knockback.
- **Stagger**: enough damage on his ankles and he kneels for a few seconds, and hits on his head do bonus damage.

### Chlo - aerial archer
Glides above the arena (the Abyss / Night Matriarch movement).
- **Arrow rain**: AoE markers on players.
- **Arrow wall**: a moving barrier with a gap.
- **Kidnap**: the full design is below.
- **Grounded windows**: after a kidnap or a dive she lands for a few seconds and takes bonus damage.

**Kidnap:**
1. She marks a player (2 s telegraph) and swoops in.
2. The player rides an invisible seat under her, and sneaking can't dismount it.
3. She climbs to about 15 blocks and lands 2-3 melee hits, each about 7% HP.
4. Then she drops them. Enough damage on her during the carry makes her drop them early, from lower.

### Pancake - the COO (brewer)
- **Splash potions**: they land on marked circles.
- **Syrup**: lingering puddles that slow and cover more of the floor as the fight goes on.
- **Taste test**: she brews a big potion and soak circles appear; if they aren't covered, it bursts.
- **Updraft**: she interrupts players. A marked player (2 s of swirling bubbles) is sent straight up about 12
  blocks and takes the fall. She aims at players standing in soak circles or attacking her, so others have to cover.
- **Drink**: she drinks for 3 s (loud sound + particles) and heals the shared bar unless enough damage on her
  interrupts it.

### Pace
The pace rises with the shared bar, not with separate phases.

| Bar | Pace |
|---|---|
| 100-66% | one raid mechanic at a time, slow lasers, single rings |
| 66-33% | two mechanics overlap, cooldowns ×0.8, lasers faster, 3 beams, double rings, more soak circles |
| 33-0% | three overlap, cooldowns ×0.65, 4 beams that reverse direction, rings from both feet, kidnap + updraft can coincide |
| soft enrage (15 min) | the last band, plus +5% damage every 30 s |

## Safety rules for moving players
- **Straight up only:** launches keep the player's x/z, so they land where they took off. The arena has open sky
  (checked at setup).
- **Real fall damage:** landing deals ordinary vanilla fall damage. Feather Falling, water buckets and slime blocks
  work as usual, and that's a skill reward. The heights are what get balanced. In the benchmark kit (Protection IV x4,
  no Feather Falling), fall damage is `(height - 3) x 0.36`:
  - Updraft at 12 blocks costs about 16% HP.
  - A kidnap drop from 15 blocks costs about 22%. With 3 kidnap hits of about 7% each, the whole kidnap stays under
    45%. An early drop (from about 10 blocks) costs about 13%.
  - The combat log records the fall as the mechanic that caused it. It records only, the damage is unchanged.
- **Clearing the flag:** the state ends when the player lands, dies or quits, or after 10 s. A player who quits
  while carried or launched comes back on the ground at the same x/z. Ender pearls and chorus fruit don't work while
  carried.
- **Swap checks (S4MURAI):** both spots must be inside the arena, and the destination can't be inside an active
  hazard or wall. There's a 4 s cooldown, and he never swaps with a player who is airborne from a launch or carry.
- **Repeat targets:** the same player is never kidnapped or launched twice in a row.

## Performance budget
- Act 1: at most 10 targets (2 entities each), at most 30 adds across the arena.
- Act 2: 3 bodies, the beams (about 20 text/block displays per beam), and markers with a fixed particle budget.
- One scheduler task for the whole event. Hazard checks go over arena players once per tick.

## Testing
- The self-test spawns every roster signature and the council, ticks them, and checks cleanup.
- `event start <targets> <players>` with a fake player count shows how dense the mechanics get at 25 on the test server.
- `/occultech balance` grades every mechanic against `TIER_2`.
- Health can't be tested without a real crowd. Run the first live event with `event hp` at hand, then tune
  `staff-health` / `council-hp` from the combat logs (`tools/balance.py`).

## Decided
- Act 1 has nothing to do with Act 2's bar: Act 1 kills don't change the council's health, so it's tuned on its own.
- Pancake's updraft is her way of interrupting players: she aims at players in soak circles or attacking her.
- **Art comes last, as its own pass:** the katana (boss-only held model) and the new ground and visual effects (HOTFIX
  beams and stamps, soak circles, markers, rings, walls, meteors, the DENIED stamp) go through the art pipeline
  (`docs/art/STYLE.md`, `REFERENCES.md`) after everything else works. Until then everything uses placeholders
  (vanilla particles, plain text and block displays, a netherite sword).
- Rewards aren't part of this plan.

## Sessions
Each session ends with a build, the unit tests and a self-test run.

| Session | Work |
|---|---|
| **E1 - Foundation** | `event/` package. Arena (`event arena set`, open-sky check, saved in `raid-arena.yml`). Commands `event start [targets] [players]`, `stop`, `skip`, `hp`, `status`. Roster in config (validated, pure Java). Raid scaling and target count (pure Java). A random picker with no repeats where a pair is one slot. Boss engine support for event fights (no altar, loot or saved state; their own health). Act 1 loop: slots, refill, `2 × N` kills or 8 minutes, event boss bar. Placeholder staff (skinned Mannequin that walks and strikes). Respawn at the arena edge, elytra off. Self-test: a raid starts, fills its slots, refills and cleans up |
| E2 - Archetypes | The six archetypes (movement, melee, generic move) with their `Mechanic`s. The balance report grades raid mechanics against `TIER_2` |
| E3 - Signatures I | Devs (HOTFIX beams and stamps, SYSTEM BUG, Rollback), Abusing (replicas, big fuse), FM (radio rings), Proxy/Atlas (walls + TNT). The wall and ring tech is shared with Act 2 |
| E4 - Signatures II | S4MURAI (enderstep, swap, katana moves), Charles (meteors, moons, black hole, low gravity), pyr0 (stampede, MOO, milk, hay), Earl + Sam (bond, together, rescue, enrage), mrlonelydwarf (lonely) |
| E5 - Signatures III | Kon (decoys), bee_grand (bees), Bat (bats), Griffon (mount), Jenn (foxes), Nick/Spleen (DENIED), Jolly (config reload), Raven (spiders: egg sacs, web zone, pounce, from the Brood Mother). mrlonelydwarf's rework: *lonely* becomes **burrow** (mining, pickaxe, can't be interrupted). Act 1 polish Then Jolly's rework (done): config_reload became trick arrows, fart jumps and whoopee cushions, with him as a very fast archer |
| E6 - Raid toolkit | Act 2 building blocks: soak circles, player markers, moving barriers, spinning lasers, expanding rings, the pace bands |
| E7 - The Council | X, Chlo (flight, kidnap), Pancake (potions, syrup, taste test, updraft, drink), the shared bar, pace and soft enrage, the rules for moving players |
| E8 - Test and tune | Self-test for every signature and the council, mechanic density with a fake count of 25 players, balance report, performance budget, fall damage in the combat log |
| E9 - Art pass | Katana model and the new ground and visual effects through the art pipeline |
