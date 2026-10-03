# Occultech - project notes

Slimefun addon: occult summoning circles, ritual machines, custom bosses, special weapons.
Maven project, Java release 21, package root `io.github.amitelia.occultech`.

## Target platform
- Paper 26.2 + **Slimefun Legacy** 4.1.61 (github.com/wickidcow/Slimefun-Legacy; keeps the `io.github.thebusybiscuit.slimefun4` API).
  Installed into `./libs` and `run/plugins` by `scripts/setup-dev.ps1`. The production server very likely runs Slimefun Legacy (its
  maintained addons match the server: Supreme, InfinityExpansion2, Networks, FluffyMachines), but this isn't confirmed.
- Java: JDK 25 runtime (project-local in `./.jdk`), compiled to Java 21 bytecode.
- Use `SlimefunItemStack.item()` for recipe inputs/outputs (works on Legacy and on newer upstream Slimefun, where it's no longer an ItemStack).
- Test server addons: Supreme, InfinityExpansion2, Networks, FluffyMachines (`setup-dev.ps1 -Addons`); 41 other bundled addons sit in
  `run/addons-disabled`. The old 1.21.1 server is kept in `run-1.21.1/`.

## Scope
`docs/scope.md` is the v1.0 scope: positioning, size, power and rules are locked; tiers/bosses/progression are still DRAFT.
`docs/boss-ideas.md` holds the boss pool plus the design and anti-abuse rules every mechanic must pass. Check new content against both.
`docs/recipes.yml` is the source of truth for items/recipes/bosses; after editing it run `python tools/cost_model.py`
(regenerates `docs/items.md`, checks tier cost targets, slot limits, summon costs). `docs/mechanics.md` covers servitors,
necromancy and held-use weapons.
`docs/server-analysis.md` + `tools/analyze_guide.py` analyze the target server's other addons (from the guide CSV export).

## Architecture
```
Occultech.java   plugin entry point: loads recipes.yml -> registrar, ritual service, listeners, command
content/         ItemCatalog (parses recipes.yml), ItemKeys (item identity strings), GridLayout (counts -> 3x3) - pure Java
setup/           ALL Slimefun registration: ContentRegistrar (catalog -> SlimefunItems), groups per tier, recipe types, researches
items/           SlimefunItem subclasses + runtime: RitualAltar, OfferingBowl, RitualService (+Holograms), OccultCodex/CodexMenu,
                 ProducerBlock (Brood Egg, Phantom Roost), ServitorShrine + ServitorService (contracts, spirit, Ward),
                 FrenzyIdol, ScryingMirror, BoneScepter + MinionService (necromancy, minion kinds), WeaponListener
                 (tier 0 + Abyssal set bonus), GearListener (tier 1 gear, Abyssal armor effects, no Mending),
                 tier 2: OccultMachine (powered AContainer, recipes from recipes.yml), HeldWeapons (Wyrmbreath,
                 Guardian's Gaze, Soulfire Censer), AbyssalAnchor, ChoirBell, GuardianEye, WindChime, DecorationBlock +
                 DecorationService, cosmetics (StepTile, CosmeticListener, TrophyBoard),
                 tier 3: HollowGearListener (armor, Dreadlance, Stormstring Bow, Aegis), TalismanService + Talisman,
                 GallusEgg (steered mount), ServitorNexus (linked shrines; routing lives in ServitorService)
ritual/          CirclePattern, Circles (layout per tier), RitualMatcher/RitualRecipe - pure Java, unit tested
core/            Bukkit-only shared bits (PDC Keys: SUMMONED, FIGHT, SHOWCASE, DAMAGE for fight projectiles)
boss/            engine, Bukkit only: BossService (fights + all anti-abuse event rules), BossFight (one fight:
                 arena leash, anti-pillar, hazards, breakable objects, boss bar, contribution, loot), BossBehavior
                 (per-boss logic), FightHooks (Slimefun side implemented by items/OccultechFightHooks)
boss/tier0/      BroodMother, Volley, WitchCoven, GelatinousSovereign + Tier0Bosses registry
boss/tier1/      TheUnbound, NightMatriarch, MirroredMagus, Archevoker + Tier1Bosses registry
boss/tier2/      AbyssalWarden, Tidebreaker, BlazeChoir, Tempest, DrownedElder + Tier2Bosses; Abyss (public: land gliding,
                 walking, dodgeable beams, magic damage). Health attributes cap at 1024: big bosses use modifyIncomingDamage as armor
boss/tier3/      HollowWarlord, HeartwoodHorror, DreadRiders, CorruptedColossus, Doppelganger (Mannequin), Gallus (final
                 boss, 3 phases) + Tier3Bosses
debug/           /occultech command: selftest (in-game integration test), showcase [clear]
pack/            ResourcePackService: the resource pack built by tools/art/build_pack.py (src/main/pack, unfiltered),
                 item_model per item, Nexo hand-off or a self-hosted web server (config resource-pack.*)
items/CustomBlockService  Occultech's blocks as real custom blocks, Nexo-style (Session N): each block look owns a
                 note-block state (chorus plant for models smaller than a cube, tripwire for the flat glyphs) that the pack shows as its model; states never change
                 once given out (tools/art/block_states.json). Nexo hookup still to do: docs/nexo-migration.md
items/BlockSkinService  the older display-entity skins (custom-blocks.mode: skins, or auto with Nexo installed); with
                 custom blocks on it only converts old skins as their chunks load
```

**Bosses:** recipes.yml `bosses:` gives name/tier/drops/offerings; behavior is a `BossBehavior` subclass registered in
`TierNBosses` (id must match). `ContentRegistrar.registerSummons` turns each into a summoning ritual: offerings in the
bowls, the catalyst on the altar for gate bosses, an empty altar for mini-bosses. A crash mid-fight is recovered via the
`occultech_active_fight` block-storage marker on the altar (catalyst refunded on next load).

**Items come from data:** `docs/recipes.yml` is packaged into the jar and registered at startup by `ContentRegistrar`
(only tiers <= `ContentRegistrar.IMPLEMENTED_TIER`). Adding a plain item = edit recipes.yml (give it a `material`).
Items with behavior get a class in `items/` and a case in `ContentRegistrar.register`. Grid recipes list counts;
`GridLayout` places them symmetrically.

Rules:
- Only `setup/`, `items/` and `debug/` import Slimefun API. `content/`, `ritual/`, `boss/`, `ability/` depend on
  Bukkit/Paper at most (pure Java where possible) so they survive Slimefun ports and can be unit tested.
- Content should be data-like: adding a boss or ritual = new definition, not edits to core logic.
- Slimefun item ids are prefixed `OCCULTECH_`. Research ids start at 262000 and must never change once released.
- Track boss entities and ritual state with the PDC so they survive restarts and chunk unloads.

## Commands
- `./scripts/setup-dev.ps1` - fetch Slimefun + Paper
- `./scripts/run-server.ps1` - build, deploy to `run/plugins`, start server (debug on 5005)
- Custom blocks need `block-updates.disable-noteblock-updates`, `disable-chorus-plant-updates` and `disable-tripwire-updates: true` in the server's
  `config/paper-global.yml` (like Nexo); the plugin warns if they're off. Set in `run/` and the self-test copy.
- `./mvnw.cmd test` - unit tests. The user's system JAVA_HOME is JDK 17, so dot-source
  `scripts/java-env.ps1` first (or in bash: `JAVA_HOME="$(cygpath -w "$PWD/.jdk/jdk-25.0.4.1+1")" ./mvnw.cmd ...`).
- Server defaults live in `scripts/server-template/server.properties` (copied into `run/` on first start).
- **In-game validation:** `occultech selftest` (console or op) checks registration, builds a circle near spawn, runs a
  ritual end to end and cleans up. Headless run: pipe `occultech selftest` then `stop` into `scripts/run-server.ps1`
  after "Done (" appears in `run/logs/latest.log`; look for "Self-test finished: N passed, 0 failed".
  The self-test also spawns, ticks and kills every implemented boss and checks cleanup, refunds and crash recovery.
- `occultech showcase` builds an item wall (12 N of spawn) and ready-to-summon circles (16 S, 26 apart); every changed
  block is recorded in `run/plugins/Occultech/showcase.yml` and `occultech showcase clear` restores them.
- The test world is superflat, so wild slimes spawn everywhere - don't mistake them for boss leftovers.
- Showcase kits have a button (command block) running `occultech restock x y z BOSS_ID` to refill that circle.
  `occultech inspect x y z` / `inspect shrines` print Slimefun ids and menu contents; `setslot x y z slot ID [n]` edits one.
- Slimefun Legacy stores block data in a database and saves menus by slot: a `BlockMenuPreset` whose last slots hold no
  preset item must call `setSize(...)` in `init()`, or those slots are never saved (the Servitor Shrine store was lost).
- The test server's `run/spigot.yml` sets every `entity-activation-range` to 0 so mobs tick with nobody online; the
  self-test relies on it to check scripted boss movement. Production servers keep their own values.
- Scripted boss movement goes in `BossBehavior.move()` (every tick); decisions stay in `tick()` (every 5 ticks).
- Rebuilding Slimefun blocks at the same spot within seconds (self-test) can race the async storage; a single odd
  self-test failure that passes on rerun is that, not gameplay.
- A self-test killed mid-run (server stopped or timed out) leaves its circles and arenas in the world, and later runs
  restore to that dirty state - e.g. glyph carpets popping off as "vanilla loot" in every run. Reset the test world
  (delete `world` and `data-storage/Slimefun/block-storage.db` in that server folder) and rerun.
