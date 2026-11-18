# Hollow Warlord, the Headsman: session 2 (design lock)

Script: `tools/art/bosses/headsman_s2.py <client folder>`. The approved blockout ([s1_blockout](../s1_blockout/README.md))
rebuilt as a rig: [design.png](design.png) (idle), [poses_1.png](poses_1.png), [poses_2.png](poses_2.png),
[hitbox.png](hitbox.png), [parts.md](parts.md), the model in `design/occultech_hollow_warlord_blockout.bbmodel`.

## The rig

- **Bind pose:** upright, arms hanging, the sword held level ahead in the right fist. Limbs are whole-texel boxes along
  the axes; every pose is rotations from here (plus the hips sinking and the skulls moving, which are position keys).
- **Bones (BetterModel names):** `hips` > `torso` > `hi_head` > `hat`; `pauldron_left/right`; `arm_*` > `forearm_*`
  (gauntlet and hand) > `sword` in the right fist; `leg_*` > `shin_*` > `foot_*`; `tabard_front`, `tabard_back`.
- **The taken skulls:** `skull_c`, `skull_l`, `skull_r` hang off the model's root, not the body, so they never lean
  with him: they follow his head's position, turn with his twist, and bob on their own.
- **Glow bones:** `glow_eyes` (his eyes), `glow_brand` (the brand down the fuller), `glow_skull_c/l/r` (each taken
  skull's eyes and soul fire). A skull goes dark when its guard dies by hiding or tinting its glow bone.
- **The hat on its own bone:** the enraged phase hides it (or throws it in the animation).
- **Counts:** 134 cubes, 27 bones. The skull faces are drawn over the renders as decals; in the model each skull is
  one 16-unit cube that session 4 maps to the vanilla wither skeleton skin at 2x.
- **Size:** 4.75 blocks wide at the pauldrons in the bind pose, 5.5 to the hat, 7.5 to the top skull in idle.

## Hitbox

One `ob_hitbox`, 4.9 x 5.5 x 2.5 blocks: his body, pauldrons and arms, floor to hat. The skulls, the sword and the
tabard stay outside it.

## Key poses (from the rig)

Arms and legs are posed by two-bone IK at fixed bone lengths, so the feet land on the floor in every pose (the hips sink
on their own in the wide stances); the sword is aimed in world space from the right fist.

| Pose | Moment |
|---|---|
| idle | the point on the floor ahead, the skulls lit |
| walk | dragging the sword behind him |
| windup | the soul sweep's warning: twisted back, the blade trailing low behind his right side |
| sweep | level at hip height, two hands |
| enraged | below 35%: the hat gone, the sword cocked over his shoulder |
| death | on one knee, the sword driven into the floor; the skulls fallen and dark round him |

Notes: the soul fire under each taken skull is two glowing blocks for now; it reads as a lamp, and gets its real
shape in painting (and particles in game).
