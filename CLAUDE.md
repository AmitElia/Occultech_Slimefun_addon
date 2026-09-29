# Occultech - project notes

Slimefun addon: occult summoning circles, ritual machines, custom bosses, special weapons.
Maven project, Java release 21, package root `io.github.amitelia.occultech`.

## Target platform
- Now: Paper 1.21.1 + Slimefun experimental `3ea21da` (from blob.build, installed into `./libs` by `scripts/setup-dev.ps1`).
- Goal: MC 26.2 with a custom Slimefun port. Expect API drift; keep it contained (see below).
- Experimental Slimefun API note: `SlimefunItemStack` does NOT extend `ItemStack`; use `.item()` for recipes/outputs.

## Scope
`docs/scope.md` is the locked v1.0 scope (tiers, boss gates, item budget, raw-cost targets). Check new content against it.
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
  `scripts/java-env.ps1` first (or in bash: `JAVA_HOME="C:\\Program Files\\Java\\jdk-24" ./mvnw.cmd ...`).
- Server defaults live in `scripts/server-template/server.properties` (copied into `run/` on first start).
