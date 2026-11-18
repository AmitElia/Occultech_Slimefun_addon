# Drowned Elder, session 5: texture painting

Script: `tools/art/bosses/drowned_s5.py <client assets folder>` (after `drowned_s4.py`). Output: [sheet.png](sheet.png)
(idle from six views, the aim pose's eyes), the painted atlas `occultech_drowned_elder_rig.png` and the review model
(copied to `run/` and `run-mythic-b`: `/bm test occultech_drowned_elder_rig idle`, `... aim` for the eyes).

## How it's painted

- **The head keeps vanilla's Elder Guardian skin**, untouched, shown at 3 pixels per texel.
- **The body is painted in 3 x 3 clusters**, one of the head's texels, so the whole serpent reads at one pixel size and
  the body looks like it belongs to that head.
- Ramps run from a cool violet dark through the zone's colour to a warm light. They paint form only (no light
  direction), with ambient occlusion baked from the real geometry where parts meet. Detail is calm clusters, never
  speckle. Every texel is fully opaque.

| Zone | Painted as |
|---|---|
| plate (shingles, tail) | the elder's cracked stone, after vanilla's plates: a darker frame round each shingle with a lit lip, one or two jagged cracks stepping across it |
| belly | bands across the body (the gap between two scales dark, the next one's lip lit), like a serpent's belly |
| seam | dark folds of soft hide between the shingles |
| spike | the elder's violet-navy, lighter on the tip piece, one lit edge |
| membrane, fin | soft violet-grey membrane with a thin darker ray every few texels |
| glow (beam eyes) | a hot sea-glow centre with a dark vertical slit pupil, so each reads as an eye |

## Fixed in self-review

- **The fins read as wooden planks**, first in vanilla's brown, then as pink cherry planks. Close, even stripes on a
  flat board look like wood, and planks are Tidebreaker's material. The fins are now the same family as the hood's webs
  (a soft violet-grey with a hint of rose), with sparse rays over calm membrane.
