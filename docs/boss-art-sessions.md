# Boss art: how one boss model is made

Status: **active**, restarted 2026-10-10 with Volley. Concepts per boss: [boss-visual-overhaul.md](boss-visual-overhaul.md).
The user-reviewed direction and lessons from Volley are in [art/BOSS_STYLE.md](art/BOSS_STYLE.md); read it before
starting the next boss. A textured offline draft is not final art approval.
Engine notes: [bettermodel.md](bettermodel.md). The MythicMobs hookup ([mythic-integration-plan.md](mythic-integration-plan.md))
comes after the visual overhaul.

Decisions (2026-10-10): the Occultech resource pack is **required**; BetterModel's boss models are merged into it and
published through the pack repo (`occultech_texture_pack_v1.0`, built by `tools/art/build_pack.py`). MythicMobs is the
free version.

## Why it's split this way

A good-looking model fails in a fixed order: a weak silhouette can't be saved by texture, broken joints can't be saved
by animation, and stretched or uneven pixels look cheap no matter how they're painted. So each session locks one
layer and the user reviews it before the next layer is built on top. Nothing is painted until the shape and the joints
are approved, and nothing is animated until the textures are approved.

## Sessions (per boss)

| # | Session | Delivers | User gate |
|---|---|---|---|
| 1 | **Concept and silhouette** | 2-3 directions as real cuboid blockouts, rendered as silhouettes (front, side, top, player's eye) and clay next to a player | pick a direction, list changes |
| 2 | **Design lock and blockout** | the chosen direction refined: final proportions, every part, cubes snapped to the texel grid, the hitbox, poses for the boss's key moments as silhouettes, a parts list | approve shape and proportions |
| 3 | **Rig and pose test** | bone hierarchy with pivots inside the joints, BetterModel names (`h_` head, `glow_` light, hitbox), 6 key poses; the model loads in BetterModel on the test server. First time only: the pack-merge pipeline, so the model can be seen in game | approve poses (and an in-game look) |
| 4 | **UV and material blocking** | per-face UVs at one texel density, packed atlas, flat colour per material zone; grayscale value check; first in-game check of pixel size | approve the material map |
| 5 | **Texture painting** | full paint: hue-shifted ramps, form shading, wear, small detail; emissive parts | approve close up and at 10 blocks |
| 6 | **Texture polish and variants** | fixes from review, phase/damage variants (part swaps, tints), readability at night and under the hit tint | approve final textures |
| 7 | **Animation** | idle, walk, spawn (the ritual arrival), one clip per attack timed to its mechanic (prepare, commit, contact, recover), phase change, death; preview GIFs, `/bm test` in game | approve motion |
| 8 | **Pack and in-game review** | model built into the Occultech pack, pack published (with the user's go-ahead), screenshots/video in the real client | sign-off |

The user takes in-game screenshots for sessions 3-8; Blender renders are previews, not proof of how it looks in game.

## Rules for a tasteful, properly textured model

**Pixel density.** One texel is one model unit (16 pixels per block, the vanilla density) at the scale the boss is shown
in game. Every cube face maps to a whole number of texels: cube sizes snap to the unit grid in session 2, and textures
are never stretched or squashed. If a boss is shown scaled up in game, its density is set for that scale, never
mixed. A different density is a deliberate, documented decision for the whole boss.

**Shape first, detail second.** Big forms are geometry; seams, cracks, hairs, weave and engraving are texture. Tiny
cubes that blur at combat distance are cut.

**No double shading.** The game already shades faces by direction. Textures carry *form* (ambient occlusion where
parts meet, a soft top-to-bottom gradient on large faces, lit edges on plates), not a painted light direction.

**Palette.** Ramps from `tools/art/palettes.py`, hue-shifted (shadows to violet/blue, lights warm); the tier family plus
one accent ([STYLE.md](art/STYLE.md)). The body is dark and calm; the magic is the only saturated thing and it glows
(`glow_` parts: eyes, cracks, cocoon light), kept small.

**Clusters, not noise.** Pixels sit in readable clusters of 2-4 tones; no single-pixel speckle, no pillow shading, no
outlines painted on a 3D model.

**Atlas.** One power-of-two atlas per boss (256x256 at most unless the review says otherwise), plus small separate
textures for effect models. Mirrored parts share UV space only when they are truly identical.

**Readability.** Floor warnings stay visible under and around the model; decorative parts never look like weak spots.

## Tooling (`tools/art/bosskit/`)

- `bbmodel.py`: builds a Generic Blockbench model from cuboids in a bone hierarchy (rest-space coordinates, ZYX
  rotations like Blockbench), with helpers for jointed legs and stepped rounded masses (`blob`).
- `blender_render.py`: Blender 3.6 renders of the real geometry: silhouettes, clay and flat materials, with a player
  for scale (`C:\Program Files\Blender Foundation\Blender 3.6`).
- `sheet.py`: review sheets.
- Per boss: `tools/art/bosses/<boss>_s<N>.py`; output in `docs/art/bosses/<boss>/overhaul/s<N>_*/`.

## Progress

| Boss | Session | Status |
|---|---|---|
| Volley | 8 pack and in-game review (redesign: the Amethyst Crone) | shipped with its geode-spire wards: [s8_ship](art/bosses/volley/overhaul/s8_ship/README.md); the in-game sign-off is pending |
| Brood Mother | 5 texture painting | vanilla spider head and eyes at 3x, hair strips with alpha, wax and candles painted; ready for review: [s5_paint](art/bosses/brood_mother/overhaul/s5_paint/README.md) |
