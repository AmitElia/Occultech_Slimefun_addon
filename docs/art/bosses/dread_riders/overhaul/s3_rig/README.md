# Dread Riders, session 3: rig and pose test

Script: `tools/art/bosses/dread_s3.py [--no-server]`, on top of the approved session 2 design lock
([s2_design](../s2_design/README.md)); the look is unchanged.

## Review rigs

Four review models, here and in `run/plugins/BetterModel/models` (never shipped):

| Model | Worn by |
|---|---|
| `occultech_dread_vanguard_mount_rig` | the zombie horse |
| `occultech_dread_vanguard_rig` | the zombie lancer (origin at the seat) |
| `occultech_dread_outrider_mount_rig` | the skeleton horse |
| `occultech_dread_outrider_rig` | the skeleton archer (origin at the seat) |

- **Colours:** one flat colour per material; the glows (crimson eyes and chest sigil, cyan eyes and arrow tip) are
  full-bright.
- **Poses as animations,** with the same names on a pair's mount and rider:
  - the Vanguard: `idle`, `charge`, `rear`, `stunned`, `sweep`, `throw`;
  - the Outrider: `idle`, `gallop`, `draw`, `rain`, `loose`.

  The mounts' gallop and rear lift the body off the floor with a position key on `base`. The drawn bowstring stretches
  with scale keys. To see a pose in game:

  ```
  /bm reload
  /bm test occultech_dread_vanguard_mount_rig charge
  /bm test occultech_dread_vanguard_rig charge
  ```

- **Not shown by `/bm test`, set by the fight code in session 8:**
  - The rider sits on the mount at the game's passenger seat. A test spawns the two apart, each on its own spot.
  - The rider follows the mount's tilt in the rear.
  - The nocked arrow appears for the draw (it's a hidden bone).

## Counts and checks

| Check | Vanguard horse | Vanguard | Outrider horse | Outrider |
|---|---|---|---|---|
| Cubes | 289 | 67 | 165 | 108 |
| Displays | 142 | 33 | 94 | 69 |
| Faces that would flicker | 0 (89 nudges) | 0 (11) | 0 (6) | 0 (34) |
| Longest cube (limit 48) | 38 | 35 | 35 | 39 |
| Split for length | the banner pole (60 into 2) | the lance shaft (70 into 2) | - | - |
| BetterModel tags | only `glow_` | `hi_head`, `ob_hitbox` | only `glow_` | `hi_head`, `glow_arrow`, `ob_hitbox` |
| Hitbox | none (it can't be hurt) | 2.5 x 7.44 x 2.5 | none | 2.5 x 8.19 x 2.5 |

The nudges move a face by at most a fifth of a texel.

**Where the displays go:** one per bone, plus one for every distinct cube angle BetterModel can't keep in a bone's item
model.
- **The horses' bodies (`base`: 77 and 59 displays):** every chamfered mass is a set of angled cubes.
- **The steppe helm (`hi_head`: 45):** its cone is 32 plates, each at its own angle.

Together the two pairs come to 338, against the Tempest's 215. Under the plan, draw cost is cut in the M6 pass across
every boss, not per boss now.

**Pivots flagged:**
- the glow bones, which never turn on their own;
- the skeleton horse's `base`, whose pivot sits in the barrel inside the ribcage, which is where it should be.

## Load test

On test server b (2026-11-20), BetterModel built all four rigs clean, with no warnings or errors. File counts in
build.zip: 163, 50, 113 and 85. The rigs were then taken off b again, because b's models folder must hold only shipped
models for pack builds. b's build.zip keeps them until its next boot.

Reports: `*_report.json`, `*_pivots.md`, [summary.json](summary.json).

## Not checked yet

- **The poses in a real client.** They come straight from the session 2 rigs, but nobody has watched them in game.
- **The pair together:** the rider on the mount at the real passenger seat (session 8).
