# Art sessions: tracker

Each session finishes completely (assets + review sheet + self-critique + fixes) before the next starts.
Style rules and the checklist: [STYLE.md](STYLE.md). Plan: [../visual-overhaul.md](../visual-overhaul.md).

| Session | Content | Status |
|---|---|---|
| **A** | Style guide, toolkit, 3 test icons (Ritual Chalk, Spirit Essence, Hollow Sigil) | **Done** - reviewed |
| **B** | Sigils and glyphs: pentagram, hexagram, tier sigils, 24 runes, footprints, crown pieces | **Done** - awaiting review (A vs B sigil style) |
| C | Tier-0 item icons | - |
| D | Tier-1 item icons | - |
| E | Tier-2 item icons | - |
| F | Tier-3 item icons | - |
| G | Block faces and floor decals | - |
| H | Menu backgrounds | - |
| I | Effect sprites (motes, embers, shards, shockwave rings, beams, footprints) | - |
| - | Pack pipeline (assets in the jar -> Nexo external pack or Occultech's own pack) | after B |

## Session A - style and toolkit (2026-10-01)
**Delivered:** `tools/art/` (palettes, pixelkit, review), [STYLE.md](STYLE.md), and three icons in
[session-a/](session-a/) with review sheets `review-v1..v4.png` (v4 is final).

**Iterations and self-critique**
- **v1** - big step up from the first samples (real volume, one light, coloured outlines). Failed: the chalk was a
  generic rod (read as a scroll or cigarette); the essence read as a vanilla potion with a thin "?" wisp; the sigil's
  dark ring hid the star, leaving a lumpy disc with almost no value contrast.
- **v2** - essence gained a unique silhouette (a ghost escaping the flask); the sigil became a clear star. Still failing:
  the chalk's round end cap and twine band read as a rolled scroll tied with string; the sigil read as a sheriff's badge
  (the cyan ring sat between the arms as loose triangles); the ghost was a plain ball.
- **v3** - ghost got a tapered tail (essence passes). Regression: the new ring's outline was drawn across the star and
  erased its silhouette - toolkit bug: outlines could paint over other parts.
- **v4** - toolkit fix (outlines only on empty pixels); chalk without twine, both ends cut flat, a facet edge and
  speckle -> reads as a chalk stick drawing a line; sigil is a true pentacle (circle across the arms, arms poking out),
  silhouette exactly symmetric (0 pixels off).

**Checklist (v4)**
| | Ritual Chalk | Spirit Essence | Hollow Sigil |
|---|---|---|---|
| Unique silhouette | yes (stick + stroke) | yes (flask + ghost) | yes (pentacle), roundish |
| Readable at 1x | yes | yes | mostly - at 1x it's a cyan ring with a red heart; the star shows at 2x |
| Tier palette / accent | chalk + bone / none needed | violet glass + spirit cyan | bone + sculk / hollow cyan + crimson |
| Light and volume | yes | yes | yes (bevelled plate) |
| Grayscale | yes | yes | yes |

**Honest remaining weaknesses**
- The chalk is the plainest of the three; a basic tier-0 material can stay simple, but its texture could still be richer.
- At 1x the sigil's star detail mostly disappears; for items that people must tell apart at 1x, the silhouette has to
  carry everything (lesson for sessions C-F).
- The ghost's face is two dark pixels; it works, but faces at this size are fragile.

**Review (user):** v2 was the best overall - keep the v2 Hollow Sigil (bold star on a glowing ring) and the v2 Spirit
Essence (round little ghost); take the v4 Ritual Chalk. Final set: `review-final.png`.

**Lessons carried forward**
- A bold, simple silhouette beats a "correct" symbol: the badge-like star was preferred over the literal pentacle
  (circle across the arms). Favour striking shapes over symbolic accuracy.
- My own checklist judged v3/v4 better than the user did - when two versions both pass, show both and let the user pick.
- Build the silhouette first, then shade; check it in the silhouette column before adding detail.
- Avoid accessories that change what an object *is* (the twine made chalk into a scroll).
- Outlines must never cross other parts.

## Session B - sigils and glyphs (2026-10-01)
**Delivered:** `tools/art/glyphkit.py` (8x supersampled masks -> crisp pixels by coverage, mirroring for exact symmetry,
grayscale styling so the game's text colour tints it), `session_b.py` (sigils) and `session_b_glyphs.py` (runes,
footprints, crown pieces). Outputs in [session-b/](session-b/): `review-sigils-v2.png`, `review-runes-v3.png`,
`review-pieces-v4.png` are final. Everything that should be symmetric measures 0 pixels off.

**Why grayscale:** a font glyph's colours are multiplied by the text colour, so one white glyph serves every tier
(ember / violet / teal / crimson columns on the sheets show the result).

**Iterations and self-critique**
- **Sigils v1** - pentagram A's thin inner ring was noise and its ticks merged; Initiate had a stray x in the centre;
  Bound didn't read; the Abyssal waves were thin; the Hollow spikes were tiny. **v2** fixed all of them.
- **Runes v1** - most read at 1x and as a line of text, but five looked like Latin letters or digits (bone `I`, twin
  `n`, bind `X`, chain `8`) and hook/thorn were near-twins. **v2**: bind -> hourglass, bone -> forked ends, chain ->
  two links, hook -> a real hook. New problem: twin now looked like gate. **v3**: twin -> open cup with a dot. Pass.
- **Pieces v1** - bare-foot and paw toes merged into a bar; crown band's gem holes were 1-px noise and its spikes read as
  candles; soul flame read as a light bulb; sparkle as a plus; the gem's hole made a donut. **v2** fixed crown, gem.
  **v3**: toes that are smaller than r~1.5 collapse into `+` shapes at 16 px - toes are now fewer and bigger (big toe +
  one blob; paw toes spread apart); the flame's mirrored side lick became cat ears, removed. **v4**: the sparkle went
  through two failed tries (thin diagonal rays fall under 50% coverage; 1-px rays + outlines = noise) and ended as a
  four-point star *without* the dark outline - it's a light sprite, the glow carries it.

**Honest remaining weaknesses**
- The boot print reads as a keyhole on its own; in a trail of alternating left/right prints it reads as steps.
- Some runes are still close to known glyphs (ascend/descend are arrows, crown is a `W`) - fine for meaning at a glance.
- The sparkle disappears on light backgrounds (in-world it is always over a scene and glows).

**Open choice for the user:** pentagram/hexagram **A (lines)** vs **B (bold)** - per Session A's lesson both are shown.

**Lessons carried forward**
- At 16 px, round features under ~3 px across become `+` shapes; use fewer, bigger blobs.
- Mirrored asymmetric details double up (the flame lick became two ears) - design the half, then look at the whole.
- Light sprites (sparkles, motes) skip the dark outline; objects keep it.
