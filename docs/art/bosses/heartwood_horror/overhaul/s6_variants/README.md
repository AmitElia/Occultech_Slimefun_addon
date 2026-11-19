# Heartwood Horror, session 6: variants and readability

Script: `tools/art/bosses/heartwood_s6.py <client folder>`. It repaints session 5 with neutral glows, then renders
every state, and copies the review rig to `run/plugins/BetterModel/models`.

Sheets:
- [states.png](states.png): every state, whole body and chest.
- [womb_states.png](womb_states.png): the sleeper, calm and vulnerable, by day and at night.
- [readability.png](readability.png): night and the red hit flash.

## One model, tinted per state

The glows are painted neutral (white to grey) and tinted per state with BetterModel's per-bone tint. Each glow sits
on `glow_` bones that hold nothing else.

| State | Eyeblossom eyes (`glow_blooms_*`, `glow_hump_blooms`) | Lantern cracks (`glow_lantern`) | Sleeper's eyes (`glow_sleeper`) | Womb's glow (`glow_womb`) | When |
|---|---|---|---|---|---|
| calm | ember orange | ember | shut (dark) | soft honey | the hearts stand: it can't be hurt |
| vulnerable | angry red | flaring, near white | **open, orange** | full | the hearts are down: the 20 s window |
| creak | shut (dark) | out | shut | dim | the vanish-and-strike: every light goes out at once |
| dead | out | out | out | dark | death |

The tint colours for session 8's Mythic skills are in `heartwood_s6.py`: `BLOOM`, `LANTERN`, `SLEEPER` and `WOMB`.

## Changes from session 5

- **The lantern can really go out.**
  - Its block now wears the *dormant* creaking heart (`creaking_heart` / `_top`).
  - Its glow overlay carries the awake heart's cracks, painted neutral.
  - Tinting the overlay dark leaves a dead, dark heart. Before, the awake texture on the block itself stayed orange.
- **The womb glows from inside.**
  - The amber chamber behind the sleeper is now a glow bone (`glow_womb`).
  - At night the womb still reads, with the sleeper as a dark silhouette in it, like a fossil held up to a lamp.
  - Unlit, the amber went black at night.
- **The shell lost its inner chamfer layer.** Through the translucent shell its rims showed as a bar down the middle
  of the window, over the sleeper's face. The womb is now one clean box of resin with its rim lumps.

## Readability

- **Night (light about 4):**
  - Calm: the body goes dark, and the eyeblossoms, the lantern and the womb carry it.
  - Vulnerable: the lantern flares and the sleeper's eyes burn in the amber.
  - The creak: only a dim womb is left, which is the point (it has vanished).
- **The red hit flash:** the whole body reddens, and the glows stay the brightest parts.

## Not checked yet

- **In a real client:** the translucent resin (sorting; see the session 5 notes), and the tints applied by Mythic.
  Session 8 wires the states; `/bm test` shows the untinted, neutral glows.
