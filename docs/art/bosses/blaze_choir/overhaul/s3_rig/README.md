# The Blaze Choir, session 3: rig and pose test

Made by `python tools/art/bosses/choir_s3.py <folder holding assets/ from the 26.2 client>`.

Three review models with flat material colours (the fire and the mouths full-bright) and the six key poses as animations.
They are in `run/plugins/BetterModel/models` and are never shipped.

| Model | Cubes | Bones with cubes | Displays | Flicker pairs | Unintended tags |
|---|---|---|---|---|---|
| `occultech_blaze_choir_soprano_rig` | 89 | 14 | 15 | 0 | none |
| `occultech_blaze_choir_alto_rig` | 465 | 11 | 412 | 0 | none |
| `occultech_blaze_choir_bass_rig` | 154 | 6 | 90 | 0 | none |

**In game** (poses: `idle`, `strike`, `shielded`, `chorus`, `last`, `death`):

```
/bm test occultech_blaze_choir_soprano_rig shielded
/bm test occultech_blaze_choir_alto_rig strike
/bm test occultech_blaze_choir_bass_rig chorus
```

## Changes for the item-model limit

No cube may be longer than 48 units. The Soprano's longest pipe is two cubes, and the Bass's wheel has half-spokes.

## Checked

- All three built on test server b with no BetterModel errors (the build holds 29, 423 and 96 model files). The server had
  no player online, so **the animations have not been seen in game**.
- Pivots: only `cymbal_right` and `cymbal_left` are flagged. Their pivot is at the centre of the dish on purpose.

## Cost

517 displays together, where the Tidebreaker has 250. The Alto is 412 of them: each cone panel of its round cymbals sits
at its own angle and takes its own display. As agreed, the cost isn't cut per boss; that is the M6 pass.
