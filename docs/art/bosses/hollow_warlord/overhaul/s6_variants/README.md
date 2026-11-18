# Hollow Warlord, the Headsman: session 6 (variants and readability)

Script: `tools/art/bosses/headsman_s6.py <client folder>` (run it last: it repaints session 5 with neutral glows and
writes that review rig to `run/plugins/BetterModel/models`). Sheets: [states.png](states.png),
[readability.png](readability.png).

The glows are painted neutral (white to light grey) and tinted per bone in game with BetterModel's tint, so one model
serves every moment. Three groups tint on their own:
- `glow_eyes` + `glow_brand`: his eyes and the sword's brand;
- `glow_skull_c`, `glow_skull_l`, `glow_skull_r`: each taken skull's eyes, lit while its guard lives.

| State | His eyes and brand | Taken skulls | Pose shown |
|---|---|---|---|
| calm | soul cyan (92, 232, 240) | all lit | idle |
| tell | near-white cyan (214, 255, 252): the soul sweep's warning | as they are | windup |
| broken | soul cyan | one dark per dead guard, (40, 44, 44); two dark = the shield is off | idle |
| enraged (below 35%) | white-hot cyan (200, 255, 255); the hat stays on (session 7 review) | as they are | enraged |
| dead | out (40, 44, 44) | all out | death |

No part swaps. Session 8's fight code drives these: the guard count tints each skull, the sweep's warning flares his
eyes, and below 35% his eyes and brand burn white-hot. (The first take hid the hat when he enraged; the session 7
review dropped the hat-tearing enrage, so the hat now stays on.) BetterModel restores the previous tint after a hit flash,
so it re-applies the state tint after hits (as the earlier bosses do).

**Readability:** at night (light ~4) the eyes, the brand and the lit skulls carry the read; the dark skulls go black,
which is the point. Under the red hit flash the shape and the glows still read.
