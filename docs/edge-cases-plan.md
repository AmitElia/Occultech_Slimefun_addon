# Bugs and edge cases: plan (Session P)

What the code does today, what goes wrong, and the fix. Four sessions, smallest risk first.

## What I found in the code

| # | Report | Cause found |
|---|---|---|
| 1 | Servitor orb copies in the air; a half circle with the Ward | `ServitorService.ensureSpirit` respawns the orb whenever the old one reports `!isValid()`. The Ward's orb patrols in a circle and crosses chunk borders; when it enters a chunk that's loaded but no longer entity-ticking (player far away), it turns "invalid" without being removed, so a new orb spawns at the shrine. Each patrol step leaves one behind: the half circle. When you come back, the stranded copies are visible again. |
| 3 | Duplicate fights | `BossService.canSummon` only checks fights already running. Two summons channeling at the same time near each other both pass, then both spawn. Also, "too close" today means only "arenas overlap", not a large area. |
| 7 | Cheese from outside the arena | Damage to the boss is never checked against where the player (or their arrow's shooter, or their pet or minion) stands. |
| 8 | Can't stack on cosmetic blocks | `DecorationBlock` cancels every right-click (even sneaking) to cycle the palette. `StepTile` cycles on plain right-click. |
| 2/6 | Death, leaving, stopping | Fights end as ABANDONED after 30 s with no one in the arena, with no refund. There's no way to give up early. |
| 4 | Restart or crash | A clean stop ends every fight with a catalyst refund; a crash refunds it on the next load. The fight itself is always lost, and so are the offerings. A summon still channeling when the server crashes loses its offerings. |
| 5 | ClearLaggEnhanced | Its clearer skips display entities, but not `Interaction` entities: those are the hitboxes of pylons, hearts and wards, so a clear makes a fight unwinnable. It can also clear adds and unnamed bosses, and its mob limiter can cancel a boss's spawn in a crowded chunk. It always spares entities with the scoreboard tag `CLE_PROTECTED`. |
| 5 | BeaconPlus 3 | Its *Flying* and *Immortality Field* effects let players fly over every floor attack or never die. *Slowdown*, *Gravity Well* and *Poison* may hit our bosses. It's paid, so I can't read it. I'll handle it by its effects, not its code. |
| 9 | Crafting and dupes | Rituals take inputs first, which is safe. Weak spots: <ul><li>An altar or bowl can be broken during a ritual or fight. Today that's caught at most a second later, or never.</li><li>A server stop within that second puts offerings back into a broken bowl's stale menu.</li><li>The Servitor and Arcane Altar flows have not been audited.</li></ul> |

## Session P1: quick fixes (low risk) - DONE (self-test 320/320)

- **#1 Orb copies:**
  - Each orb carries its shrine's position.
  - Before a new orb spawns, any old orb for that shrine is found and reused, or removed.
  - The orb only moves into chunks that are entity-ticking.
  - Leftover orbs are removed when their chunk loads.
  - The same sweep runs over every Occultech hologram: altar and bowl holograms, Guardian Eye, talismans, decorations.
- **#8 Cosmetics:** sneak + right-click changes the look (step tiles and decoration blocks). A plain right-click places blocks normally.
- **#3 One fight per area:**
  - Summons that are still channeling reserve their area too.
  - A new config value, `bosses.min-fight-distance` (default 96 blocks), applies on top of the no-overlap rule.
  - The check runs again when the summon finishes.
- **#5 ClearLaggEnhanced:**
  - Every entity Occultech spawns gets the `CLE_PROTECTED` tag, set before its spawn event fires. That covers bosses, adds, hitboxes, displays, minions and holograms.
  - Nothing to configure on the server.

## Session P2: who can fight, and leaving the fight (#2, #6, #7) - DONE (self-test 329/329)

- **#7 Outside the arena:**
  - Damage to anything in the fight counts only if the player stands inside the arena. That includes arrows, tridents, pets and minions.
  - Otherwise it's cancelled, with an action-bar hint.
  - Hitting from above is already handled by the anti-pillar rule.
- **Away timer (#6):** when no living player is in the arena, an away timer starts. The boss bar shows a countdown.
  - **Left on foot** (online, outside the arena): the boss regenerates while you're gone, so stepping out to heal doesn't pay.
  - **Died or disconnected:** the boss holds still and doesn't regenerate, so you can respawn or reconnect and walk back to the same fight.
  - When the timer runs out (3 minutes, decided), the fight ends as ABANDONED and the catalyst is lost.
- **#2 Giving up** (decided): three ways, and the catalyst is lost in each.
  - Sneak + right-click the altar with the Occult Codex.
  - A *Banishing* item, tier 0 and very cheap. It ends the nearest fight from a distance, for when walking up to the altar is too dangerous.
  - The away timer (below).
- **Flight and BeaconPlus:** skipped. The server's BeaconPlus has no Flying effect.

## Session P3: fights survive restarts and crashes (#4) - DONE (self-test 340/340; a real stop and a killed JVM both resumed the fight)

- **Saving:** every 5 s and on stop, the fight writes its state to the altar's block storage: boss, health of each boss, phase, elapsed time, the damage and presence counts, the catalyst.
- **Resuming:**
  - On load (or once its chunk loads), the fight spawns again at the same health, with fresh adds and objects.
  - Phases follow health in every boss.
  - Players see "the circle stirs; X returns".
  - The refund-on-crash path becomes the fallback, used only if a resume fails.
- **Summons still channeling** are saved the same way. On load they complete, or return their offerings.
- **Losses:** a crash loses at most the last 5 s. You can't gain anything by forcing a restart: health is restored, timers continue.

## Session P4: dupe audit and other edge cases (#9, #10) - DONE (self-test 347/347)

**Locking:**
- Altars, bowls and circle marks can't be broken during a ritual or fight (and they're immune to explosions and pistons).
- The `intact()` check stays as the fallback.
- Offerings go back only to blocks that still exist; otherwise they drop.

**Audits, each with a self-test:**
- every `OccultMachine` recipe (inputs consumed once, outputs delivered, and a full output slot never eats items);
- the Arcane Altar infusion when broken mid-infusion;
- Servitor contracts that move items;
- the Codex and Shrine menus (size and save rules);
- shift-click and hopper/cargo access to locked slots.

**Other edge cases to cover:**
- The world unloads, or a player changes dimension, mid-fight.
- A plugin `/reload`.
- A fight runs in the nether or end.
- Ender pearls thrown into the arena.
- Totems of undying.
- A boss pushed into lava or the void (already handled by the leash).
- A non-participant teleports in for loot (the presence share already blocks this; to be checked).
- Loot for a player who disconnects at the moment of victory: their share is kept and given on join.
- Boss bars after relog.
- Chunk tickets released on every end path.

**Crash rollback (not an addon bug):** player data and Slimefun's block database save at different moments, so a hard crash can roll one back and not the other. Server owners guard this with frequent saves. I'll note it in the docs.

### P4 outcome

| Area | Result |
|---|---|
| Circle lock | `CircleGuard`: while a ritual runs or a boss walks a circle, every Occultech block on the altar's level inside the circle, and the block under each, is safe from breaking (before Slimefun sees it, so nothing drops), explosions, Slimefun explosive tools, pistons, fire and flowing liquids. |
| Crash mid-ritual or mid-infusion | `CrashLedger` records what was taken and gives it back once when the block loads again. Rituals and Arcane Altar infusions both use it. |
| Rewards for absent fighters | A fighter who earned a share but isn't online at the victory gets it on their next join (`plugins/Occultech/pending-rewards.yml`). It's removed from the file before it's handed out, so it's never given twice. |
| Recipes | The self-test checks that no two crafting recipes (ours, or another addon's) share a grid on the same machine, so none is shadowed. It found none. |
| Audited, no change needed | <ul><li>Machine recipes: standard Slimefun `AContainer`.</li><li>Servitor item moves: take then give, same tick.</li><li>Altar, bowl and Arcane Altar menus: inputs are taken at the start, and locked slots refuse clicks.</li><li>Shutdown mid-infusion hands out the result.</li><li>Chunk tickets are released on every end path.</li><li>Boss bars re-attach after a relog.</li><li>The presence share keeps loot from players who only teleport in at the end.</li></ul> |

**Known limits:**
- **Reloading only Occultech** (`/reload`, PlugMan) saves running fights, but they resume only once their altar's chunk loads again. Slimefun doesn't rebuild menus that are already loaded. A full restart is the supported path.
- **Crash rollback:** Minecraft saves player data and Slimefun saves its block database at different moments. A hard crash can roll back one and not the other: a player's inventory from before they filled a bowl, next to a bowl that was saved full. That's server-wide and not specific to Occultech. Frequent autosaves keep the window small.
