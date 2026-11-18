# Tempest, session 5: texture painting

Script: `tools/art/bosses/tempest_s5.py <client assets folder>` (run after `tempest_s3.py` and `tempest_s4.py`; it paints
session 4's islands). Output: [sheet.png](sheet.png) (the idle pose: hero, about 10 blocks away, a player's eye, and close-ups of
the face, the heart and a seal shard), the painted atlas `occultech_tempest_rig.png` (512 x 512), the review model
(copied to `run/` and `run-mythic-b`: `/bm test occultech_tempest_rig idle`).

## What is painted

- **The seal:** pale carved stone. Both broad faces of every tile carry:
  - two engraved rings framing the glyph circle, with lit lips;
  - a tick cut at every 9-degree step between the rings;
  - a few hairline cracks running outwards.

  The inner lip sits in the core's shadow. The broken edges show paler, fresh-break flecks. The rim is darker stone with a
  worn outer lip.
- **The circlet:** dark weathered stone, its lower edge in shadow.
- **The heavy core:** vanilla's own look. Each face of each block is a raised frame (a lit bevel with a dark groove inside
  it) round a recessed plate, smooth dark steel with one soft diagonal highlight. There's no noise, because noisy metal
  read as cork on the Choir.
- **The wind:** streaks running along every band, lightest down its middle and thinning to its edges.
- **Glows:** the heart, glyphs, brows and eyes have hot centres fading to their colour.
- **The breeze skin:** vanilla's, untouched (head and rods).
- Every texel is opaque. Ambient occlusion is baked from the real geometry.

## Fixed in self-review

- **The vanilla face.** In `breeze.png`, vanilla's 10x3x4 band is almost entirely clear: only its white V brows show. The
  blue band you see is painted on the skull itself, with the yellow eyes just under it. Session 4 had made the band's
  clear texels solid, which put a black strip across the face. **The band cube is gone.** Its white brows stay as glowing
  cubes, and the yellow eyes are now glowing cubes too, wrapping each corner of the head like vanilla's. The longest cube
  is now 32 units, and the display count is unchanged at 215.
- **The stone was noisy** (the camo lesson). Seal and circlet now use larger, rarer mottle clusters.
