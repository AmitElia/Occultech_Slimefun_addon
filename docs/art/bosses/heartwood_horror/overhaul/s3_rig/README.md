# Heartwood Horror, session 3: rig and pose test

Script: `tools/art/bosses/heartwood_s3.py [--no-server]`. Built on top of the approved session 2 design lock
([s2_design](../s2_design/README.md)); the look is unchanged.

## Review rig

- **The file:** `occultech_heartwood_horror_rig.bbmodel`, here and in `run/plugins/BetterModel/models`. It's a review
  model only and is never shipped.
- **Colours:** one flat colour per material. The glows (lantern eye, eyeblossom eyes) are full-bright.
- **Poses as animations:** idle, walk, swipe, lunge, eruption, sap, slam and death. To see one in game:

  ```
  /bm reload
  /bm test occultech_heartwood_horror_rig <pose>
  ```

  The lunge, eruption, sap, slam and death poses also move the hips down or forward with position keys.
- **Fight-code switches, not poses:** some states are set by the fight code in session 8, not by animation channels.
  `/bm test` doesn't show these:
  - the sleeper's eyes opening;
  - the eyeblossoms closing for the creak;
  - the hanging moss swinging back to straight down after each pose.

  In the poses, the moss is held to its parent bone's bind angle.

## Counts and checks

| Check | Result |
|---|---|
| Cubes | 303 |
| Bones with cubes | 89 |
| Displays (BetterModel item displays) | **93** (Drowned Elder 90, Tempest 215) |
| Faces that would flicker | 0, after 56 nudges of at most a fifth of a texel |
| Longest cube | 36 units (the hump's trunk segment); the limit is 48 |
| BetterModel tags | only the intended ones: `hi_lantern`, the `glow_` bones, `ob_hitbox` |
| Pivots flagged | only the glow bones (they never turn on their own, so a pivot away from their cubes is fine) |
| Hitbox | 2.94 x 8.06 x 5 blocks |

Where the displays go: one per bone. The extras are the hands: the crutch's four fingers fan on two axes, and so do
the thin arm's two (5 displays between them).

## Load test

On test server b (2026-11-18), BetterModel 3.5.0 built the rig clean: 183 files, no warnings or errors. The rig was
then taken off b again, because b's models folder must hold only shipped models for pack builds.

Report: [summary.json](summary.json), [report.json](report.json), [pivots.md](pivots.md),
[material_atlas.png](material_atlas.png).

## Not checked yet

- **The poses in a real client.** They come straight from the session 2 rig, but nobody has watched them in game. In
  particular: the lantern turning with its target (`hi_lantern`) while it hangs, and the crutch fingers.
