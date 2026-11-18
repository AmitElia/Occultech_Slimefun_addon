# Drowned Elder, session 6: variants and readability

Script: `tools/art/bosses/drowned_s6.py <client assets folder>`. **Run it last**: it repaints with neutral eyes and writes
that review model to `run/` and `run-mythic-b`. Output: [states.png](states.png), [readability.png](readability.png), the
neutral-eye atlas and `occultech_drowned_elder_rig.bbmodel`.

## One model, tinted per state

Both kinds of eye are painted **neutral** (white to grey) and full-bright; the fight tints them with BetterModel's
per-bone tint. Each beam eye is its own bone, so each beam's eye can flare on its own (each beam has its own target).

**The three beam eyes** (`glow_eye2`, `glow_eye4`, `glow_eye6`, under the gill shingles):

| State | Tint | When (DrownedElder.java) |
|---|---|---|
| calm | sea glow (110,232,206) | between beams |
| lock | near-white (214,255,246) | the 0.5 s lock before that eye's beam fires |
| surged | cold abyss blue (110,160,255) | below half health, when the beams come faster |
| dead | (40,44,48) | death |

**The head's great eye** (`glow_eye`):

| State | Tint | When |
|---|---|---|
| calm | the elder's pale near-vanilla white (236,230,220) | always, except: |
| stare | cold sea glow (140,255,228) | the Mining Fatigue pulse |
| dead | (52,50,54) | death |

The head's eye stays plain like vanilla's; the beam eyes have a single dark slit pupil. No part swaps: the moments are
poses (session 2) and become clips in session 7.

## Readability ([readability.png](readability.png))

- **Night (light ~4):** the head's pale eye is the brightest point; the body sinks into the dark, so the face carries
  the silhouette. In the beam lock the three opened eyes are the only lights along the body, so players see where the
  beams come from. The stare's sea-glow eye is unmistakable.
- **The red hit flash:** the whole model takes the red tint, and the eye still reads.

## Fixed in self-review

- **The beam eyes read as a "pause" sign (‖):** rings of light and dark round the slit looked like two bars. They're now
  one bright field with a single dark slit.
- **The eye shots hid the eyes:** the curled aim pose put the body in front of them, and the stare camera ended up below
  the floor. The eye states are shot on the straight bind pose (gills open for the beam eyes), from behind the gills,
  which swing open from their front edge.
