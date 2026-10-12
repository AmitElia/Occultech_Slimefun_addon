# The Unbound redesign, session 6: variants and readability

His variants are **the fire's stages**. He speeds up as he loses health, and the fire in his chest grows with him.
The fire is painted near white (session 5), and in the fight BetterModel's per-bone tint multiplies the stage's
colour into it, so there is no texture swap. New this session: **flames licking up out of the grate**, on their own
bone `glow_flames`, which starts hidden and is shown as the fire grows (BetterModel's part visibility).

| Stage | When | Tint (RGB) | Flames |
|---|---|---|---|
| embers | above 2/3 health | 230, 96, 40: a low red-orange glow behind the grate | hidden |
| burning | below 2/3 | 255, 150, 60: orange | shown |
| inferno | below 1/3, enraged | 255, 236, 200: white-hot | shown |
| sated | the 3 s after he devours a thrall | 150, 60, 36: dull coals | hidden |
| dead | as he falls | 52, 40, 38: the fire goes out | hidden |

**The tinted bones** are `glow_chest` (the fire behind the grate) and `glow_flames`. The embers streaming off him
are particles from the fight (session 8), denser at each stage.

![The stages, close up](stages_chest.png)
![The stages, front](stages_front.png)

## How it works in BetterModel (as checked for the Witch Coven, 3.5.0)

- **The tint:** `tracker.update(TrackerUpdateAction.tint(rgb), bone -> name starts with "glow_chest" or
  "glow_flames")`, or MythicMobs' BetterModel `tint` mechanic with a part filter.
- **The flames:** `TrackerUpdateAction.togglePart(true/false)` on `glow_flames` (the Brood Mother's candles work the
  same way).
- **The hit flash** (`damageTint`) tints every bone red for about 10 ticks, then restores each bone's previous tint.
  If a stage change lands during a flash, the "previous" tint is the flash's red. So, as for the coven, session 8
  re-applies the stage tint about 12 ticks after every stage change.

## Readability

- **At night** (light level about 4), everything but the full-bright fire and eye dims to a dark silhouette. The cyan
  eye and the fire are what's left, and the stage still reads at a glance in the dark: a red-orange grate, or a
  white-hot one with flames.
- **Under the hit flash**, the whole body reddens and the fire stays the brightest thing on him.

![Night and the hit flash at a player's eye height](readability.png)

**One known limit:** the warm firelight painted on the skin round the chest piece (session 5) stays the same at
every stage, since it's in the texture. When sated or dead it reads as the skin's colour rather than light; the
fire itself carries the change.

He draws 22 displays now (one more, for the flames bone).

Regenerate with `python tools/art/bosses/unbound_s6.py` (after `unbound_s5.py`). Next, session 7: animation (idle,
the walk with the cleaver dragging, the cleave's wind-up and sweep timed to the fight, the thrall call, the devour,
the sated collapse, the charge, death).
