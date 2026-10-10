# BetterModel test-server setup and modeling crash course

Research and installation: 2026-10-09. The comprehensive revised implementation brief is [boss-rework-plan.md](boss-rework-plan.md); modeling references live in [boss-model-direction.md](boss-model-direction.md).

## Installed and verified

- Paper **26.2 build 129**, local **JDK 25**, Slimefun Legacy **4.1.61**.
- BetterModel **3.5.0**, the latest stable compatible Paper release at installation; intentionally pinned rather than following snapshots.
- Jar: `run/plugins/bettermodel-3.5.0-paper.jar`.
- Repeatable installation: `./scripts/setup-bettermodel.ps1`. Downloads to a temporary file, checks Modrinth's SHA-512, then installs. It refuses duplicate BetterModel versions and checks an existing jar before skipping it.
- Official [release metadata](https://api.modrinth.com/v2/version/QTU9HP83) and [project page](https://modrinth.com/plugin/bettermodel).
- The existing server was stopped through its console with **zero players online** and restarted. No worlds or Slimefun databases were reset.
- Startup reports `Plugin is loaded`, `Minecraft version: 26.2.0, NMS version: V26_R2`, and `Platform: Paper`. Occultech loaded 127 items, 45 rituals and 23 researches.
- `bettermodel version` confirmed 3.5.0. `bettermodel reload` successfully loaded **2 bundled models**, rebuilt/checked a **2.180 MiB** pack, and completed in **1,006 ms** in this run. These are smoke-test observations, not performance guarantees.
- Generated file: `run/plugins/BetterModel/build.zip` (2,285,473 bytes, 6,087 ZIP entries at verification).
- No additional gameplay plugin was needed. MythicMobs, Citizens, Nexo and SkinsRestorer are optional in the installed jar's descriptor.

Installation is complete; **Occultech boss attachment, custom boss assets and automatic delivery of the BetterModel pack are not implemented by installing the jar**. Client rendering has not been visually verified. Paper logged a Windows performance-counter warning during startup; BetterModel subsequently loaded and reloaded successfully.

## First model test

Use a Minecraft 26.2 client and an op account. For an immediate local preview, copy `run/plugins/BetterModel/build.zip` into the client's resourcepacks folder and enable it alongside Occultech's pack. Then, in an empty test area:

```text
/bettermodel spawn demon_knight
/bm test demon_knight hammer_attack_1
```

These are the documented spawn and animation-preview commands; preview lifecycle and hitboxes still need checking in the client. Test outside real boss encounters and remove preview entities afterward.

New source models are Generic Blockbench `.bbmodel` projects, placed in `run/plugins/BetterModel/models/`; `/bettermodel reload` rebuilds the pack. Refresh the client pack after changes. Player animation templates belong in `players/`. See the [official model tutorial](https://github.com/toxicity188/BetterModel/wiki/Create-your-own-model-using-BlockBench) and [animation tutorial](https://github.com/toxicity188/BetterModel/wiki/Animating-your-own-model).

The two installed examples are useful hands-on references:

| Bundled source | Observed geometry | Observed clips | Study task |
|---|---|---|---|
| `blue_wizard.bbmodel` | 211 elements, 2 textures | idle, walk, death | Inspect robe hierarchy, texture placement, and how a readable silhouette survives movement. |
| `demon_knight.bbmodel` | 323 elements, 3 textures | idle, death, walk, run, guard; three hammer and two shield attacks | Inspect attack preparation, weapon pivots, recovery and separation between locomotion and attacks. |

Counts above come from the installed JSON files. Elements are **not** the same as independently rendered bones. Do not adopt the example element counts as budgets or redistribute third-party samples as Occultech originals.

The knight's outliner contains 30 groups for its 323 elements, illustrating why one bone per cube would be wasteful. Its walk loop lasts 1.5 seconds, run about 0.92 seconds, and authored attacks 1.25 or 2.25 seconds. These are observed clip lengths, not inferred damage timings; copying them into Occultech would misalign some existing mechanics. Outliner group count also includes control/hitbox structure and is not a measured display count.

## What the crash course changes about our approach

### Geometry, textures and silhouettes

A cube is a shape; a bone/group is a transform hierarchy; a pivot is its joint; UV coordinates map faces onto the texture. Put pivots where the anatomy bends before animation starts. Keep things that always move together in the same group. Model large contour changes and overlapping plates; paint seams, grain, cracks and engraving into textures.

The useful lesson from the [Blockbench style guide](https://blockbench.net/wiki/guides/minecraft-style-guide/) is to make geometry carry shape and textures carry detail. Occultech can be richer than vanilla while retaining broad angular forms, deliberate pixel density and coherent palettes. A 512-pixel atlas does not automatically look better than a disciplined 128-pixel one. Avoid tiny protrusions that disappear at combat distance.

The restored art direction permits substantial changes to carrier anatomy: vanilla-esque means Minecraft construction and rendering language, not enlarged vanilla mobs. Preserve the defining original concept features and review concepts before model execution. Begin with a black silhouette at player eye height, viewed from the front, side and rear at 8–20 blocks. A strong boss should be identifiable without particles, nameplates, dramatic lighting or a close-up camera. Then choose three material families and one accent: for example pale bark, dead moss, amber resin and a warm heart glow.

The [Blockbench overview](https://blockbench.net/wiki/guides/blockbench-overview-tips/) provides the practical editor foundation: outliner, pivots, UV tools, animation timeline and interpolation. Work in this order: blockout → pivots → pose test → UV/texture → animation → in-game test. A texture polish pass cannot repair an unreadable silhouette or a shoulder joint in the wrong place.

### Expressiveness comes from posing and timing

Our animation recipe is **prepare → commit → contact → recover**. Lead with intention: an eye turns before the head, the head before the chest, and a heavy weapon before the body catches up. Offset trailing robes, antennae and chains after the main movement. Alternate stillness with force; constant movement removes emphasis.

Use asymmetric idle poses, breathing, recoil and gaze as personality. Design expressions through jaw, lids, crest, shoulder line and hand shape; a faceless helmet can still look proud, cautious or exhausted. For slime, fake soft deformation with a few scaled rigid masses, delayed lobes and a moving crown. Do not assume BetterModel is a soft-body simulator.

For an illustrative 1.2-second warning at 20 TPS: ticks 0–14 load the pose, 15–23 hold the readable commitment, tick 24 is contact, and subsequent ticks recover. **Actual clips must match each existing mechanic's timing**, including shorter tells and special melee windows. This example does not retune combat. Use stepped keyframes for deliberate snaps, linear motion for a projectile, smooth curves for follow-through; avoid overshoot that sends a blade outside its announced region.

Hawkon's [Learn to Animate in Blockbench](https://www.youtube.com/watch?v=HY_wjAnSy4I) is a compact practical syllabus covering keyframes, pivots, interpolation, movement/scale and math animation. Video playback was unavailable to the research tool; the linked lesson and creator-listed chapters are further study material, not a claim of frame-by-frame review.

### BetterModel capabilities and limits

The [support matrix](https://github.com/toxicity188/BetterModel/wiki/BlockBench-support-range) lists cubes, locators, null objects, IK and keyframe interpolation, with limits for meshes and no support for several other element types. Its model tutorial says meshes need BetterModel 3+ and Minecraft clients 26.1+. Our native 26.2 target qualifies; older-client proxies still require a separate compatibility test.

Use cube-first rigs for the initial production set. A group with geometry normally becomes an item-display packet representation; cost depends on moving bones, viewers, animation changes and effects as well as geometric complexity. Start with authored FK clips, then trial IK or Molang on a single asset. Editor support alone is not evidence that an elaborate rig exports exactly as intended.

BetterModel automatically recognizes clips such as `idle`, `spawn`, `death`, `walk`, `idle_fly`, `walk_fly` and `jump`. Our custom `attack_*`, `stagger`, `phase_*` and `recover_*` names need explicit integration. [Animation scripts](https://github.com/toxicity188/BetterModel/wiki/Animation-Script) support part visibility, tint, brightness and part changes; keep these cosmetic. Bedrock particle definitions or arbitrary Blockbench effect tracks are not automatically a Java-server effects system.

Use [glow groups](https://github.com/toxicity188/BetterModel/wiki/Glow-part) for selectively bright eyes, seams and cores. Treat this as emissive appearance; do not promise dynamic world lighting or shader bloom. Glass/refraction, cloth simulation and liquid simulation are visual approximations unless separately proven.

### Effects are assets too

Give each attack a small family of reusable assets: charge focus, projectile, trail, impact and lingering zone. Use short-lived model instances for shaped jaws, roots, ribbons or bells; use particles for fine sparks and dust. Most persistent warning geometry should continue through Occultech's existing `FloorDecals` so the visible danger matches the actual arena geometry.

Reserve the strongest contrast for actionable warnings. Ground boundaries remain visible beneath a large creature. Represent role changes with shapes or symbols plus sound as well as color. Limit smoke coverage, rapid flashes and large transparent layers. Make decorative trails thinner and dimmer than attack boundaries, and terminate them immediately if the attack is cancelled.

## Proposed integration boundary

This is a plan, not code already added:

1. Add an optional rendering bridge outside `boss/`, e.g. `model/BetterModelVisuals`. Keep the engine-facing interface dependent on Bukkit and Occultech only. Use a provided API dependency and optional plugin ordering, with a fallback that loads without BetterModel.
2. Attach model instances to the existing authoritative boss entities. `BossFight`, its PDC identity, health, contribution, arena checks, loot and `Mechanic` damage stay authoritative. Cosmetic animation events must never duplicate damage.
3. Drive movement from the existing per-tick `move()` path and start attack clips from behavior decisions. Keep translation in server movement; in-place animations avoid double movement. Anchor cosmetic projectiles to the real projectile and terminate on its actual collision.
4. Give each model a broad, predictable torso target. BetterModel supports [animated and multiple hitboxes](https://github.com/toxicity188/BetterModel/wiki/Configuring-custom-hitbox); route hits once into the existing fight entity and prove no double-hit path before enabling them. Decorative cloth, tails and crown tips should not become surprise weak points.
5. Preserve rider/mount identities: Tidebreaker only takes damage through its rider; Dread Riders each have their own pool; Gallus can separate and lose its rider. A combined visual rig must not silently change these rules.
6. On pause, victory, banishment, chunk unload and shutdown, stop trackers and effect instances. Extend `FightState` with backward-compatible behavior state before restoring phases and one-use flags; health alone cannot reconstruct them. Rebuild current-state visuals; do not serialize live tracker objects or replay a spawning attack on resume. Add generation tokens so a delayed animation callback cannot affect a later fight.
7. Tag any real auxiliary entities for Occultech cleanup and ClearLag protection. Packet-only displays need explicit tracker cleanup; they do not magically inherit PDC. Re-check restart restoration and no-duplicate loot with models active.

The [official API examples](https://github.com/toxicity188/BetterModel/wiki/API-example) describe model renderers, entity trackers, dummy trackers and platform adapters. Validate the exact API against pinned 3.5.0 before implementation; the live wiki can move ahead of that release.

## Resource-pack delivery decision

The actual test configuration has an `external-url` pointing to the published Occultech pack. `ResourcePackService` sends it as an additional pack with a fixed UUID. BetterModel generated a **separate** `build.zip`; that file is not in the published pack and the existing service does not send it.

First prototype: manually enable both local packs and verify namespace overlap. Next: choose one distribution owner. Prefer an explicit build merge into the delivered Occultech pack, or a second versioned pack sender with its own UUID and acceptance tracking. A merge must handle JSON collisions, supported pack metadata and hashes; copying one ZIP over the other loses assets. Inspect BetterModel's generated vanilla item entries as well as namespaces. Never overwrite Occultech's allocated blockstates blindly.

If the test/production server later uses Nexo, BetterModel documents [automatic Nexo merging](https://github.com/toxicity188/BetterModel/wiki/Merge-with-Nexo); validate that alongside Occultech's existing Nexo external-pack handoff. No Nexo install or external publication was performed here.

`scope.md` currently excludes a required pack, and `boss-ideas.md` predates this request with a vanilla-only visual rule. The user's explicit BetterModel request authorizes this optional modeling track. Retain vanilla boss visuals for packless play until a later scope decision changes that policy. Per-player fallback must be proven before hiding entities globally; it is not implemented by this installation.

## Production checks and first milestones

- **Milestone 1 — Colossus blockout:** one model, one torso target, idle/walk/slam/recovery and one pylon. Proves bone pivots, weight, gameplay timing and shaped effects.
- **Milestone 2 — Sovereign deformation:** squash/stretch, crown lag, phase scaling and split-shard ownership. Tests a completely different animation problem.
- **Milestone 3 — Night Matriarch flight:** bank, dive, landing, 30-tick (1.5-second) exposed recovery and late-viewer sync.
- **Milestone 4 — mixed encounter:** Coven or Choir verifies multi-body clarity; Dread Riders then verifies mounts; Doppelganger and Gallus come last.

Initial **art targets, not engine limits**: 20–35 rendered bones for a solo mini-boss, 35–55 for a gate, 12–20 per member of a trio; try to keep the visible boss cast under roughly 60 rendered bones before effects. Budget each simultaneously visible phase, not all hidden phase assets added together. Use 128² atlases initially and 256² only when UV occupancy and screen size justify it. Large wings or exceptional hero assets may need more; measure before expanding.

Validate at 1/4/8 players, multiple simultaneous arenas and maximum adds. Record MSPT against baseline, client frame time, network traffic, pack size and time to become visible. Provisional acceptance goal: stable 20 TPS with headroom, no persistent packet/display leak, and readable gameplay on a normal unshaded client. Also test pack refusal, late joining, reconnect, attack cancellation, phase changes, banishment, death, unload and restart. Runtime smoke tests above do not establish these future acceptance results.
