# Tempest, session 6: variants and readability

Script: `tools/art/bosses/tempest_s6.py <client assets folder>`. **Run it last**: it repaints with neutral glows and writes
that review model to `run/` and `run-mythic-b`. Output: [states.png](states.png), [readability.png](readability.png), the
neutral-glow atlas and `occultech_tempest_rig.bbmodel`.

## One model, tinted per state

The heart and the glyphs (`glow_heart`, `glow_shard0`..`6`, `glow_circlet`) are painted **neutral** (white to grey). The
fight tints them with BetterModel's per-bone tint:

| State | Tint | When (Tempest.java) |
|---|---|---|
| calm | sea teal (86,232,208) | between attacks |
| tell | near-white teal (214,255,246) | the wind-up of the gust volley and the wind burst: the seal flares as it locks |
| storm | cold electric blue (140,176,255) | below half, from the split on: the storm has broken loose |
| spent | dark sea-green (40,84,80) | the 1.5 s opening: the heart nearly out |
| dead | (44,40,40) | death |

The breeze's own eyes (`glow_eyes`: the white brows and the yellow eyes) keep vanilla's colours and stay full-bright like
vanilla's eyes layer. They only dim when spent (130,130,140) and go out when dead.

No part swaps: the seal's moments are poses (session 2) and become clips in session 7.

A first storm tint, a brighter cyan, was too close to calm teal at a distance. It's now a cold blue, so the change at half
health reads at once.

## Readability ([readability.png](readability.png))

- **Night (light ~4), calm:** the brows, yellow eyes and the ring of glyphs carry the silhouette. The face is readable,
  and so is the shape of the seal.
- **Night, spent:** almost everything goes dark except the dimmed eyes. That's the intent: the storm is out.
- **The red hit flash:** every zone keeps its value order under the tint, and the glyphs and eyes still read.

To carry over to session 8: tint the glows again about 12 ticks after a hit, since BetterModel's damage tint restores the
previous tint (the Witch Coven lesson).
