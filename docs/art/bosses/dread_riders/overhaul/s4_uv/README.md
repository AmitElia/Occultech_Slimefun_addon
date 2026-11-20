# Dread Riders, session 4: UV and material zones

Script: `tools/art/bosses/dread_s4.py <client folder> [--server]`, on the session 3 rigs (`dread_s3.build_pair`).

What's here:
- **Sheets:** [vanguard/sheet.png](vanguard/sheet.png) and [outrider/sheet.png](outrider/sheet.png). Each shows the pair
  together in colour and in grey, plus close-ups of the rider's head and the horse's head.
- **Atlases:** one per model, each with a grey copy: `occultech_dread_*_rig.png`.
- **Textured review rigs:** the four `occultech_dread_*_rig.bbmodel` files, with session 3's poses. They replace the
  flat-colour rigs in `run/plugins/BetterModel/models`.

## The atlases

One texel per model unit, every face whole texels, no half-clear texels.

| Model | Atlas | Islands | Vanilla islands | Fill |
|---|---|---|---|---|
| the Vanguard's horse | 512 x 512 | 1703 | 10 | 65% |
| the Vanguard | 512 x 128 | 395 | 12 | 59% |
| the Outrider's horse | 512 x 256 | 985 | 12 | 61% |
| the Outrider | 512 x 64 | 648 | 60 | 49% |

The Vanguard's horse fills 512 x 512 because its barding is hundreds of separate plates and spikes.

## Vanilla pixels, at 2 pixels per skin texel

These parts are vanilla's at 2x, so the 2 pixels per skin texel are still one texel per unit:
- **The riders' heads** wear `zombie.png` and `skeleton.png`: the vanilla faces, with no painted decals.
- **The riders' bodies** wear the vanilla body box.
- **The skeleton's bare arms and legs** take the vanilla limb strips: the upper half on the upper arm and thigh, the
  lower half on the forearm and shin.
- **The horses' heads** wear `horse_zombie.png` and `horse_skeleton.png` on the cranium (6 x 5 x 7) and the muzzle
  (4 x 5 x 5). The skeleton's muzzle is split from its hanging jaw, so it takes the muzzle box's upper half. Its dark
  vanilla eye sits under the cyan glow.

The box layouts were read from the 26.2 client (`AbstractEquineModel`: the head at 0,13, the muzzle at 0,25).

## Zones

Tier 3: netherite-dark plate with crimson on the Vanguard; old bone, iron, gold and hollow cyan on the Outrider. The
zombie horse keeps vanilla's rotting green.

**The Vanguard and his horse**

| Zone | Where | Value (L*) |
|---|---|---|
| zhorse | the zombie horse's hide (vanilla's rotting green) | 39 |
| hair / hoof | mane and tail / hooves | 11 / 19 |
| plate / plate_edge / plate_dark | netherite-dark barding and armour / lit rims, spikes, the chest boss / deep plates, gauntlets | 26 / 47 / 12 |
| crimson (glow) | the horse's eyes, the chest sigil | 51 |
| cloth / trim | the saddle cloth and banner / their crimson trim and sigil | 10 / 33 |
| leather / wood | saddle, grip, reins / the lance, the banner pole | 31 / 43 |
| horn / horn_tip | the armet's horns | 14 / 68 |
| zskin | the zombie (vanilla `zombie.png` on the head and body) | 53 |

**The Outrider and his horse**

| Zone | Where | Value (L*) |
|---|---|---|
| bone / bone_dark | the horse's bones / spine processes, hooves, the breastbone | 86 / 61 |
| cyan (glow) | the horse's eyes, the arrow's head | 86 |
| rope / blanket | red rope lashings, the halter / the saddle blanket | 30 / 52 |
| iron / gold / mail | the helm's band and cone / its brow rim and ribs / the aventail | 71 / 55 / 45 |
| plume | the horsehair plume | 37 |
| skel | the skeleton (vanilla `skeleton.png` on the head, body and bare limbs) | 79 |
| leather / coat_dark | jerkin, quiver, bow grip / the cape | 31 / 19 |

**Value check:** every pair of neighbouring zones is at least 12 L* apart. The first pass failed five pairs, all now
fixed:
- cloth / plate: the cloth is darker;
- wood / plate: the wood is lighter;
- blanket / rope: the rope is a deeper red;
- iron / gold: the iron is brighter and the gold darker brass;
- bone / cyan: no fix needed. The glows are judged by hue and full-bright emission, not value, and the skeleton
  horse's eye sits on vanilla's dark socket.

In grey, both pairs still read: the dark plate horse against the pale bone horse, and each rider apart from his mount.

## For session 5

- **The bodies are flat zones.** The zombie horse's hide is lofted geometry, so vanilla's body box can't map onto it.
  Session 5 paints it in vanilla's manner: rot, the exposed ribs and the dark green.
- **The plates:** bevel lighting, rivets, scratches.
- **The bones:** cracks and joint shading.
- **The rope:** twist.
- **The mail:** rings.
- **The helm:** ribs and a hammered cone.
