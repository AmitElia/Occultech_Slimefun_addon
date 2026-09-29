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
Occultech.java   plugin entry point, SlimefunAddon, key() helper
setup/           ALL Slimefun registration: groups, stacks, items, researches, recipes
ritual/          circle patterns + matching (pure Java, unit tested), ritual state machine
boss/            (planned) BossDefinition: base mob, stat multipliers, HP-threshold phases, abilities
ability/         (planned) reusable abilities shared by bosses and weapons
items/           (planned) custom SlimefunItem subclasses: machines, circle blocks, weapons
```

Rules:
- Only `setup/` and `items/` import Slimefun API. `ritual/`, `boss/`, `ability/` should depend on Bukkit/Paper
  at most, and on pure Java where possible, so they survive Slimefun ports and can be unit tested.
- Content should be data-like: adding a boss or ritual = new definition, not edits to core logic.
- Slimefun item ids are prefixed `OCCULTECH_`. Research ids start at 262000 and must never change once released.
- Track boss entities and ritual state with the PDC so they survive restarts and chunk unloads.

## Commands
- `./scripts/setup-dev.ps1` - fetch Slimefun + Paper
- `./scripts/run-server.ps1` - build, deploy to `run/plugins`, start server (debug on 5005)
- `./mvnw.cmd test` - unit tests. The user's system JAVA_HOME is JDK 17, so dot-source
  `scripts/java-env.ps1` first (or in bash: `JAVA_HOME="$(cygpath -w "$PWD/.jdk/jdk-25.0.4.1+1")" ./mvnw.cmd ...`).
- Server defaults live in `scripts/server-template/server.properties` (copied into `run/` on first start).
