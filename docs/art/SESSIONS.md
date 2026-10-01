# Art sessions: tracker

Each session finishes completely (assets + review sheet + self-critique + fixes) before the next starts.
Style rules and the checklist: [STYLE.md](STYLE.md). Plan: [../visual-overhaul.md](../visual-overhaul.md).

| Session | Content | Status |
|---|---|---|
| **A** | Style guide, toolkit, 3 test icons (Ritual Chalk, Spirit Essence, Hollow Sigil) | **Done** - awaiting review |
| B | Sigils and glyphs: pentagram, hexagram, tier sigils, 24 runes, footprints, crown pieces (64/128 px, exactly symmetric) | Next |
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

**Lessons carried forward**
- Build the silhouette first, then shade; check it in the silhouette column before adding detail.
- Avoid accessories that change what an object *is* (the twine made chalk into a scroll).
- Outlines must never cross other parts.
