# MythicMobs + BetterModel integration plan

Status: **IN PROGRESS: M0-M3 done in code and self-test; Volley still needs the in-game look check (see Progress).**
The art lessons from Volley are in [art/BOSS_STYLE.md](art/BOSS_STYLE.md). Drafted 2026-10-10. Builds on [bettermodel.md](bettermodel.md) (installed engine, pack
notes) and [boss-rework-plan.md](boss-rework-plan.md) (per-boss engineering briefs). Visual concepts live in
[boss-visual-overhaul.md](boss-visual-overhaul.md).

## 1. What each plugin is good at, and who owns what

The target server runs **MythicMobs** and **BetterModel**. MythicMobs 5.13.0 added Minecraft 26.2 support; BetterModel
3.5.0 is already on the test server. BetterModel ships MythicMobs mechanics with ModelEngine-style syntax (`model`,
`state`, `tint`, `partvisibility`, `bindhitbox`, `mountmodel`, `glow`, `bodyrotation`, the `@modelpart` targeter and the
`modelhaspassenger` condition), so in practice **MythicMobs drives BetterModel**.

Occultech already has a fight engine that does things neither plugin does: ritual summoning, arena leash, anti-pillar,
contribution shares, fair loot for every fighter, crash-safe `FightState`, `CircleGuard`, pending rewards, combat logs
and `ArmorModel` grading. Those are the addon's anti-abuse guarantees ([boss-ideas.md](boss-ideas.md)). They stay.

**Split of authority:**

| Concern | Owner | Why |
|---|---|---|
| Summoning, catalysts, offerings, circles | Occultech | Slimefun items, crash ledgers, research gates |
| Fight lifecycle: start, pause, away rules, banish, victory, save/resume | Occultech (`BossFight`) | crash safety and no duplicate loot |
| Who is a valid fighter, arena bounds, anti-pillar | Occultech | anti-abuse rules |
| **Body**: entity type, base stats, armor, knockback resistance, equipment, nameplate | **MythicMobs** mob file | data instead of Java, editable by server staff |
| **Look**: model, animations, tints, glow, part swaps, hitboxes | **BetterModel**, triggered by Mythic skills | real animated models |
| **Flourish**: particles, sounds, camera shake, cinematic intros | **Mythic skills** | rich effect library, quick to iterate |
| **Telegraphs** (the warning that shows where damage lands) | Occultech `FloorDecals` / `Abyss` | warning and damage must come from one geometry snapshot |
| **Attack decisions and damage** | Occultech `BossBehavior` + `Mechanic` via `fight.hit` | combat logs, balance grading, solo scaling |
| Adds, minions, summoned helpers | **MythicMobs** definitions, spawned through `fight.spawnAdd` | stat/AI variety for free, still capped and tagged |
| Loot pool contents | **MythicMobs DropTables** (as data) | staff can tune drops in YAML |
| Who receives loot | Occultech distributor | contribution shares, offline rewards, no item theft |
| Health bar shown to players | Occultech boss bar | shared pools, pause state, multi-body fights |
| Slimefun items (weapons, armor, materials) | Slimefun / Occultech | research, recipes, IDs never change |

The rule of thumb: **Mythic and BetterModel decide how a boss looks, sounds and what its body is; Occultech decides when it
hits, who it hits, and who gets paid.**

## 2. What gets replaced, wrapped or kept

| Existing component | Verdict | Change |
|---|---|---|
| `BossFight.spawnBoss` / `spawnAdd` / `spawnExtra` (vanilla entities + attributes set in Java) | **Wrap** | Go through a new `BossBody` factory. With Mythic present it spawns the Mythic mob (`MobManager.getMythicMob(id).spawn(...)`) and then tags the PDC exactly as today; without it, today's vanilla spawn. |
| Stats in Java (health, armor, speed, knockback) | **Replace** | Move into Mythic mob files (`Health`, `Armor`, `Options.MovementSpeed`, `KnockbackResistance`, `FollowRange`). `GroupScaling` still multiplies health after spawn (math in Mythic attributes is Premium). |
| `modifyIncomingDamage` "armor" for bosses over the 1024 health cap | **Keep, partly replace** | Simple per-type resistances become Mythic `DamageModifiers` (`PROJECTILE 0.8`, `FIRE 0`); the big-pool scaling stays in Java. Verify Mythic's health cap before relying on it. |
| Vanilla AI clearing / scripted `move()` | **Mixed** | Bosses with scripted movement (Abyss gliders, Riders, Gallus, Matriarch) keep `move()`; set `AIGoalSelectors: [clear]` so Mythic AI never fights it. Simple walkers and all adds use Mythic AI goals. |
| `BossBehavior` attack logic | **Keep** | Stays the conductor. Each action now also fires a named Mythic skill for the look (see section 3). |
| `FloorDecals`, `Abyss` beams, `AirEffects` links/tethers | **Keep** | Gameplay truth. Re-anchor to model parts (`@modelpart`) for origins once models exist. |
| Particles/sounds sprinkled in behaviors | **Replace** | Move into Mythic skills (`<BOSS>_<ACTION>_FX`) so they can be iterated without a rebuild. |
| Boss bar | **Keep** | Mythic `BossBar` left off. |
| Loot rolling in Java from `recipes.yml` drops | **Wrap** | `recipes.yml` keeps Slimefun drops and the guarantees. Optional Mythic DropTable per boss (`OCCULTECH_<BOSS>_EXTRAS`) supplies vanilla and cosmetic extras; Occultech rolls it **per fighter** through the API and hands the results out itself. Mythic `Drops:` on the mob stays empty and `PreventOtherDrops: true`, so nothing ever lands on the floor to be stolen. |
| Mob levels | **New** | Mythic `Level` = party-size bracket (1 = solo ... 5 = 13+), with linear `LevelModifiers` (free) for damage and health scaling, as an alternative to `GroupScaling` for adds. Bosses keep `GroupScaling` so balance stays identical. |
| Doppelganger / Staff Raid Mannequins | **Keep** | Mannequin copies the real skin best. BetterModel's player-animation templates (`players/`) are an optional extra for the reveal and staff signatures. No LibsDisguises. |
| `combat-log`, `ArmorModel`, `/occultech balance` | **Keep** | Works unchanged because all damage still flows through `Mechanic`. |
| Self-test | **Extend** | Runs every boss twice: vanilla bodies and Mythic bodies, when Mythic is installed. |

### Things deliberately NOT moved into MythicMobs

- **Damage-dealing skills** (`damage`, `projectile`, `missile` with on-hit damage). They would bypass contribution,
  combat logs, the arena-only target rule and solo scaling. If a Mythic skill must deal damage it goes through the
  custom `occultechHit` mechanic below.
- **Mythic spawners / RandomSpawns** for bosses. Bosses only exist through rituals.
- **Mythic/Crucible items** for anything players keep. Rewards are Slimefun items.
- **Mythic persistence** for boss bodies. Occultech rebuilds bodies from `FightState`; the Mythic mob is spawned
  `Despawn: true`-style and never restored by Mythic, so a restart cannot produce a duplicate boss.

## 3. The bridge (code shape)

New package **`integration/mythic`** (allowed to import Mythic and BetterModel API; like `setup/`, it is a plugin-API
layer). `boss/` stays Bukkit-only and talks to it through interfaces it defines:

```
boss/BossBody.java          interface: spawn(spec, location) -> Entity, playAction(entity, action), playState(entity, state), stop(entity)
boss/VanillaBody.java       today's behavior, extracted
integration/mythic/MythicBody.java            spawns Mythic mobs, casts skills by convention
integration/mythic/OccultechMythicComponents  registered with CustomComponentRegistry:
    mechanic  occultechHit{mechanic=SLAM}       -> BossFight.hit with the Mechanic of that name (the only damage path)
    mechanic  occultechTelegraph{shape=...}     -> FloorDecals, for skills that want a real warning
    targeter  @OccultechFighters                -> players alive inside this fight's arena
    targeter  @OccultechActionTarget            -> the target the current action locked
    condition occultechPhase{p=2}, occultechInFight, occultechSolo
    trigger   ~onOccultechAction (custom SkillTrigger) with the action name as metadata
integration/mythic/MythicPackInstaller        copies bundled configs into plugins/MythicMobs/Packs/Occultech/ (version-stamped,
                                              never overwrites files staff edited unless the stamp is older and untouched)
integration/mythic/MythicLoot                 rolls a DropTable per fighter, hands results to the existing reward code
```

**Action events.** `BossBehavior` already has decision points. They become named actions with phases
`prepare -> lock -> contact -> recover` (the server-owned action model from boss-rework-plan section 2). Each phase change
calls `body.playAction(entity, "BURST_PREPARE")`. `MythicBody` maps that to the skill `VOLLEY_BURST_PREPARE` if
it exists (missing skill = silent no-op), which typically does `state{s=burst_prepare}`, a sound and particles.
Animation is cosmetic only: a keyframe never deals damage.

**Configs ship with the jar** under `src/main/mythic/` (Mobs, Skills, DropTables) and `src/main/models/` (`.bbmodel`), built
and copied like the resource pack. Model ids are prefixed `occultech_`; Mythic ids `OCCULTECH_`.

**Dependencies.** `softdepend: [MythicMobs, BetterModel]`, Maven `provided` scope:
`io.lumine:Mythic-Dist` (repo `https://mvn.lumine.io/repository/maven-public/`, check for a 5.13.x artifact) and the
BetterModel API pinned to 3.5.0. Config `bosses.bodies: auto | vanilla | mythic`.

## 4. Free vs Premium

MythicMobs Premium gates math/placeholders in attributes and drop amounts, custom damage types and modifiers, `raytrace`,
`chainmissile`, conditional AI goals and skill parameters. **The plan is designed to work on the free version**: all
scaling math stays in Java, damage goes through our own mechanic, beams stay in `Abyss`. If the server has Premium,
skill parameters make the FX library tidier but are not required. *Open question for the server owner.*

## 5. Resource pack

BetterModel builds its own `build.zip`; Occultech sends its own pack. Options from [bettermodel.md](bettermodel.md) still
apply. Recommended: one merged pack built by `tools/art/build_pack.py` that pulls BetterModel's generated output, keeps
Occultech's block states and held-item models, and checks for namespace collisions; then rebuild the
plugin jar so the pack hash matches, as today. Without the pack, players see the Mythic carrier entity
(the vanilla look). Whether that fallback is acceptable decides whether the pack becomes required (see open questions).

## 6. Milestones

| # | Milestone | Done when |
|---|---|---|
| M0 | Install MythicMobs 5.13.x on the test server (`scripts/setup-mythic.ps1`, SHA-checked like BetterModel); confirm free/Premium on production | server boots with Slimefun Legacy + both plugins, no errors |
| M1 | Extract `BossBody`/`VanillaBody`; no behavior change | self-test passes unchanged |
| M2 | `integration/mythic` skeleton: components registered, pack installer, `MythicBody` spawning one test mob | `occultechHit` deals labelled damage that appears in the combat log; `@OccultechFighters` ignores players outside the arena |
| M3 | Vertical slice: **Volley** fully on Mythic + BetterModel (approved model, burst action, ward objects) | self-test passes in both body modes; restart mid-fight resumes with one boss and one model; no floor drops |
| M4 | Loot bridge: DropTable extras per fighter | self-test reward check passes with extras; offline fighter receives them on join |
| M5 | Tier 0 and 1 rollout (one boss per session), then tier 2, tier 3, Gallus last | each boss: both body modes pass self-test, combat log matches the old damage profile |
| M6 | Pack merge, performance: 1/4/8 players, three arenas at once, max adds | stable 20 TPS, no leaked displays after banish/unload/restart |
| M7 | Optional: Staff Raid bodies on BetterModel player templates | event demo runs with models |

### Progress (2026-10-10)

| # | State |
|---|---|
| M0 | Done. MythicMobs 5.13.0 (free) + BetterModel 3.5.0 + Slimefun Legacy boot together; `scripts/setup-mythic.ps1`. Production still to confirm. |
| M1 | Done. `BossBody` / `VanillaBody`; `BossFight.spawnBoss`/`spawnAdd` go through it. |
| M2 | Done. `MythicBody`, `MythicPackInstaller`, `occultechHit`, `@OccultechFighters`, the `OCCULTECHACTION` trigger. Not built yet: `occultechTelegraph`, `@OccultechActionTarget`, the conditions, `MythicReloadedEvent` handling. `occultechHit` is not yet used by a skill, so no combat-log check exists for it. |
| M3 | Self-test passes in both modes: Mythic `530/0`, vanilla `525/0`. Mythic mode checks: carrier, persistence, one BetterModel tracker, resume with one carrier and one model, per-fighter extras. **Still to do:** look at it in the client (pack + model scale + base mob hidden), and the animations (art session 7). The model has no clips yet, so it slides without moving its limbs. |
| M4 | Partly done. `MythicLoot` rolls `OCCULTECH_<BOSS>_EXTRAS` per fighter into the reward list (`item:` entries), so offline fighters get them through `pending-rewards.yml`. No self-test yet for an offline fighter getting an extra. |

Lessons from M3:
- `MythicMob.spawn(..., Consumer)` runs the callback **before** Mythic applies the mob file (health, despawn,
  persistence). `MythicBody` runs Occultech's setup after the spawn, or group health scaling and chunk persistence are lost.
- BetterModel's `model` mechanic scales the model by the carrier's `SCALE` attribute times `s`. Volley's carrier has
  `Scale: 2.0` (a 4-block hitbox for the 4.3-block model) and the model uses `s=0.5`, so it is drawn at its authored size.
  In vanilla mode Volley keeps its old 1.4 scale. The bigger hitbox is a small gameplay change: an easier target, and arrows leave from higher up.
- Boss models ship in the jar (`src/main/models/`, written by the boss's texture script) and are installed into
  `plugins/BetterModel/models/` with the same staff-edit-preserving stamp as the Mythic pack. BetterModel loads models
  after every plugin is enabled, so no reload is needed at startup.
- Test servers: `run-mythic-b` (port 25568) is a clean copy with Mythic + BetterModel and `bosses.bodies: mythic`.
  `run-mythic-test` (port 25567) has `Mobs/Volley.yml` hand-edited (the installer keeps it as a staff edit). Delete
  `plugins/MythicMobs/Packs/Occultech/` there to get the bundled files back.

## 7. Risks

- **Two sources of stats.** A staff member edits Mythic `Health` and the balance grading no longer matches. Mitigation:
  `/occultech balance` reads the live Mythic values and warns on drift from `recipes.yml` targets.
- **Mythic AI vs scripted movement.** Must `clear` goals on scripted bosses or they jitter. Self-test checks positions.
- **Reloads.** `/mm reload` while a fight runs must not orphan bodies. Listen to `MythicReloadedEvent` and re-resolve.
- **API drift.** Mythic-Dist on the wiki still lists 5.12.1; pin and test the exact jar on the server.
- **Slimefun Legacy + three heavy plugins**: startup order and the 26.2 version check of each.
