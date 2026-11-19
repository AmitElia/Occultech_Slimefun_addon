# Heartwood Horror, session 2: design lock

Script: `tools/art/bosses/heartwood_s2.py` (run from the repository root; pose names to re-render only those). Take C,
the Crutch ([s1_blockout](../s1_blockout/README.md)), rebuilt as a rig:
- [design.png](design.png): the stalk;
- [womb.png](womb.png): the sleeper;
- [poses_1.png](poses_1.png), [poses_2.png](poses_2.png), [poses_3.png](poses_3.png);
- [hitbox.png](hitbox.png), [parts.md](parts.md), [stats.json](stats.json);
- the model: `design/occultech_heartwood_horror_blockout.bbmodel`.

**Your changes:**
- **From session 1:** the sleeper is no longer half out. It sleeps whole inside the resin, curled like a foetus: knees
  drawn up, head bowed onto them, eyes shut, the creaking's leaves at its temples, its long arms wrapped round its
  shins. The script refuses to build if any part of it pokes out of the shell. It sits at least 1.2 units inside.
- **From the first session 2 review:** the upright resin block was too big, merged with the lantern, and lost the
  silhouette. Now:
  - the body is the Stoop's: straight (no twist), bent over nearly level, with a heavier trunk, hump and brow;
  - the womb is a compact bulge tipped forward with the chest, about 1.5 x 1.6 x 1.5 blocks, with the sleeper at
    vanilla size;
  - the lantern hangs from the brow's tip, with clear air between it and the womb;
  - the crutch is planted further ahead, so from the side the lantern hangs inside its arch.

## The rig

- **Chains:** every limb is a chain of bones, laid out straight in the rest pose and bent by its bones' rotations.
  The bind pose is the stalk.
  - Cubes sit square in their bone, or turned 45 degrees on one axis, so each bone is one BetterModel display.
  - Estimate: **97 displays**. For comparison: Drowned Elder 90, Tempest 215.
- **Trunk:**
  - `hips` > `trunk0`..`trunk4`: up from the hips, over the hump, down to the brow. It's straight, as in the
    Stoop.
  - Two broken branches stand on the hump (`stub_left`, `stub_right`, two bones each).
- **Five arms** grow out of the trunk, each a chain ending in a hand bone with root fingers:
  - `arm_crutch` (7 bones): left, planted ahead, knuckles down.
  - `arm_great` (7): right, the high spidery elbow.
  - `arm_lesser` (6): right, drooping.
  - `arm_thin` (5): right, over the shoulder, hanging.
  - `arm_back` (7): grows out of the hump, arches over and trails.
- **Legs:** `thigh` > `shin` > `cannon` > `foot` on each side. They bend backward, and the foot bone holds the root
  toes.
- **The womb:**
  - `womb` (the resin bulge, about 1.5 x 1.6 x 1.5 blocks) sits up in the chest under the hump, tipped forward with
    it.
  - `sleeper` is the curled creaking inside, built from vanilla creaking parts at 1x.
  - `glow_sleeper` holds its shut eyes. They're dark now; the vulnerable window can tint them lit.
- **The face:**
  - `lantern_root0..2` is the root it hangs from, below the brow.
  - `hi_lantern` is the creaking heart in its cage of roots. It turns towards its target as the head bone.
  - `glow_lantern` is its eye.
  - It hangs at about 2.4 blocks, at a player's head height, half a block below the womb and in front of it.
- **Eyeblossoms** grow on the arms and the hump (white petals crossed, orange eye). Their eyes sit on `glow_blooms_*`
  bones, so the creak can tint every one shut at once.
- **Pale hanging moss:** `moss_*` bones (11 strands) on the belly and arms. They hang straight down in every pose and
  can sway. Most of the moss will be texture.
- **Size:** about 8 blocks to the top of the branches (6.5 to the hump), 7.4 across, 12 long with the crutch ahead and
  the arms trailing.

## Hitbox

One `ob_hitbox`, 2.94 x 8.06 x 5 blocks: the trunk, the womb, the legs and the lantern. The trailing arms stay
outside it, so they never read as a weak spot.

## Key poses (from the rig)

The poses are set from world targets:
- **Arms:** each is fitted along a curve through control points, at its fixed bone lengths, then pulled onto its end
  point.
- **Legs:** two-bone IK onto the floor.
- **Arms a pose doesn't set** keep their hands where they lay, so they drag.
- **The floor:** no joint goes under it. The only parts below it are fingers dug into it (at most 0.3 blocks, in the
  eruption and the slam).

| Pose | Moment |
|---|---|
| idle | the stalk: hunched, the crutch planted ahead, four arms trailing, the lantern hanging |
| walk | the crutch swung ahead, the legs striding, the arms dragging |
| swipe | the wind-up: rears and coils, the great arm raised over its head |
| lunge | thrown forward onto the crutch, the great arm reaching low, the lantern swinging ahead |
| eruption | every hand driven into the floor (the root lanes burst from the hands) |
| sap | rears up, the womb lifted, the arms flung wide (the sap rain) |
| slam | the crutch and the great arm brought down together ahead |
| death | the legs give, it folds onto its crutch and topples, the lantern on the floor on its side |

## Notes for the next sessions

- **Resin (session 4):** half-clear texels flicker in game, so the resin can't simply be see-through. The plan is
  Bayer-dithered amber (fully clear and fully opaque texels mixed) with opaque rims and bubbles, so the sleeper shows
  through. The textured test checks it at fighting distance.
- **The creak:** the fight's vanish could tint every bloom eye shut and the lantern dark for a beat.
- **The vulnerable window:** the hearts falling could crack the resin (a tint) and light `glow_sleeper`.
- The sap and eruption poses are the roughest. Session 7 times them properly.
