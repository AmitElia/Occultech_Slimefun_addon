# Drowned Elder, session 4: UV and material zones

Script: `tools/art/bosses/drowned_s4.py <client assets folder>`. Output: [sheet.png](sheet.png) (the idle pose, colour and
grey), the atlas `occultech_drowned_elder_rig.png` (+ `_grey`), the review model `occultech_drowned_elder_rig.bbmodel`
(copied to `run/` and `run-mythic-b`, so `/bm test occultech_drowned_elder_rig idle` now shows these flat zones),
[uv_report.json](uv_report.json).

## Atlas

- **512 x 512** (386 rows used, 71% fill), one texel per model unit everywhere except the vanilla skin.
- 720 faces drawn as 708 islands; 24 faces buried inside other cubes are left out. 0 half-clear texels.
- **Vanilla Elder Guardian skin** (`guardian_elder.png`, 26.2 client) on the head's core, its four plates and the eye's
  face. The head is vanilla's GuardianModel at exactly 3x, so the skin goes on at 3 pixels per texel, the same
  deliberate upscale as the Tempest's breeze head and the Choir's blaze heads. Vanilla paints only one side plate and
  mirrors it for the other; the model does the same.

## Zones (value = CIE L*)

| Zone | Colour | L* | Where |
|---|---|---|---|
| skin | vanilla elder skin (mean 173,165,148) | 68 | the head, its plates |
| plate | the elder's stone-cream, sampled from the skin's plate (161,153,134) | 65 | the shingles (top and sides), the tail |
| belly | lighter cream (226,220,196) | 88 | the bottom shingles: what players see from below |
| seam | dark grey-mauve (96,88,92) | 38 | the soft body showing between the shingles, so each segment reads |
| spike | the elder's violet-navy, sampled from its spikes | 35 | head, hood and back spikes |
| membrane | violet-grey (128,112,144) | 50 | the hood's webs |
| fin | vanilla's brown fin (120,86,64) | 40 | the pectoral fins and the fluke |
| glow | tier 2 sea glow (110,232,206) | 85 | the beam eyes: full-bright |

**Value check: passes** (no two touching zones within 12 L*). The first pass failed on the hood's webs against the head
(11), so the webs went darker.

## Fixed in self-review

- The head's second side plate came out black: vanilla's skin leaves that plate's rectangle empty (it mirrors the
  first plate). Faces whose skin rectangle is empty now take the opposite face's.
- The view from below was blocked by the floor; it's now a low angle looking up at the belly.

## Notes for session 5 (painting)

- The head keeps vanilla's skin untouched, the strongest tie to the Elder Guardian. The body's zones are flat now;
  session 5 paints the shingles to match the skin's cracked-stone look, without noise.
- The beam eyes sit under the side shingles, so they're only visible in the aim pose (`/bm test ... aim`).
