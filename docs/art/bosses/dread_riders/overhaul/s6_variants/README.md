# Dread Riders, session 6: variants and readability

Script: `tools/art/bosses/dread_s6.py <client folder> [--server]`, after session 5. Run it last: it writes the
neutral-glow review rigs to `run/plugins/BetterModel/models`.

Sheets:
- **Glow states:** [states_vanguard.png](states_vanguard.png), [states_outrider.png](states_outrider.png).
- **Night and the hit flash:** [readability_vanguard.png](readability_vanguard.png),
  [readability_outrider.png](readability_outrider.png).

## One model, every moment: per-bone tints

The glows are painted neutral (near-white) and tinted in game with BetterModel's per-bone tint. The glow bones:

| Bone | Model | What it is |
|---|---|---|
| `glow_eyes` | both mounts | the horses' eyes |
| `glow_sigil` | the charger | its chest boss |
| `glow_banner` | the charger | the banner's sigil (new) |
| `glow_lance` | the Vanguard | two bands under the lance head (new) |
| `glow_arrow` | the Outrider | the nocked arrow's head |
| `glow_rune` | the Outrider | the mirror plate's rune (new bone) |

**The Vanguard** (crimson):

| State | Tint | When |
|---|---|---|
| calm | crimson (232, 48, 56) | riding, the lance sweep, the spear throw |
| tell | white-hot red (255, 176, 150) | the charge's wind-up (the rear) and the charge itself |
| stunned | a dull ember (96, 30, 30) | the 2 s after a charge cut short: "hit me now" |
| enraged | the Outrider's storm cyan (96, 236, 226) | the Outrider has fallen; the Vanguard takes up its storm and throws spears |
| dead | out (44, 36, 38) | |

**The Outrider** (hollow cyan):

| State | Tint | When |
|---|---|---|
| calm | cyan (96, 236, 226) | circling, volleys |
| lock | white-cyan (214, 255, 246) | the snipe's line has locked; the arrow is about to loose |
| enraged | the Vanguard's crimson (232, 48, 56) | the Vanguard has fallen; the archer fires faster and closer |
| dead | out (40, 44, 46) | |

The survivor taking the fallen rider's colour is the enrage's tell. There are no part swaps: the riders' moments are
poses (session 2) and clips (session 7).

## Readability

**The first pass failed for the Vanguard.** Its only glows were the horse's small eyes and the chest sigil, so at night
the pair was a dark blob, and the states barely changed anything on screen. Two glows were added, and both take the
tints:
- **Two bands under the lance head.** They are high and visible from every side, and they make the charge's tell
  readable from across the arena.
- **The banner's sigil.**

**At night** (light about 4: everything but the glows at 30%):
- **The Vanguard** reads as the lance bands, the eyes and the sigils.
- **The Outrider** reads as three points: the horse's eyes, the arrow and the mirror rune.
- **The enraged swap** (crimson to cyan, and cyan to crimson) reads at once in the dark.

**Under the red hit flash:**
- **The Outrider's pale bone** turns clearly red.
- **The Vanguard's dark plate** takes it more weakly but visibly.
- **The glows** stay distinct.

## Not checked yet

- **In a real client:** the tints themselves, and that the session 8 code re-tints 12 ticks after a hit flash
  (BetterModel's damage tint restores the previous tint, as on the coven).
