# The Blaze Choir, session 7: animation

Made by `python tools/art/bosses/choir_s7.py <folder holding assets/ from the 26.2 client>` (after `choir_s6.py`).

Key frames: [Soprano](keyframes_soprano.png), [Alto](keyframes_alto.png), [Bass](keyframes_bass.png). Motion previews: `gifs/`.
In game: `/bm test occultech_blaze_choir_<singer>_rig <clip>`.

All three singers carry the same clip names, so the fight plays one name on whichever singer acts.

| Clip | Length | Plays | What happens |
|---|---|---|---|
| `idle` | 3.0 s | loop | the chime's pipes sway out of step, the cymbals bob, the bell rocks with its wheel, the Alto's tower turns like a blaze's rods |
| `spawn` | 2.0 s | once | rising out of the circle, the instrument unfolding |
| `strike` | 0.8 s | once | the fireball on the beat: a wind-up, the strike at 0.5 s |
| `shield` | 0.6 s | hold | the instrument closes and stays closed (the Bass's wheel goes up and over its head) |
| `unshield` | 0.6 s | once | it opens again |
| `chorus` | 2.0 s | once | gathering through the 1.5 s warning, the full chorus at 1.5 s, then back |
| `last` | 1.0 s | loop | the last singer's idle: its instrument flailing |
| `flinch` | 0.4 s | once | hit |
| `death` | 2.5 s | hold | a last spasm, then the instrument falls apart and sinks |

## For session 8

- The fireball must leave 0.5 s into `strike` (10 ticks after the clip starts). It is instant in the fight today.
- The eruption already lands 1.5 s after the warning, which is where `chorus` peaks.
- `shield` holds its last frame; the fight plays `unshield` when the shield moves on, and `last` replaces `idle` for the
  last singer.
- The fire tints (session 6) go with the clips: banked during `shield`, hotter after a death, last for the last singer.

## Checked

Previews only. The review rigs with these clips are in `run/plugins/BetterModel/models`, but they could not be
load-tested: test server b was running for other work, so it was left alone. The same bones built clean in session 3.
