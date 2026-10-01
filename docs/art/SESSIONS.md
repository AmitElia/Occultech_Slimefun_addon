# Art sessions: tracker

Each session finishes completely (assets + review sheet + self-critique + fixes) before the next starts.
Style rules and the checklist: [STYLE.md](STYLE.md). Plan: [../visual-overhaul.md](../visual-overhaul.md).

| Session | Content | Status |
|---|---|---|
| **A** | Style guide, toolkit, 3 test icons (Ritual Chalk, Spirit Essence, Hollow Sigil) | **Done** - reviewed |
| **B** | Sigils, runes, gems/crown/halo, animated soul flame and sparkle, step marks, paw | **Done** - approved, cleaned up |
| **C** | Tier-0 item icons (15 + bow states; the 8 placed blocks move to G) | **Done** - codex redone after review |
| **D** | Tier-1 item icons (23; the 6 placed blocks move to G) | **Done** - awaiting review |
| E | Tier-2 item icons | - |
| F | Tier-3 item icons | - |
| G | Block faces and floor decals (incl. tier-0 blocks: altars, pedestal, bowl, glyph, trophy board, tile, Brood Egg; tier-1 blocks: Bound Glyph, Bound Altar, Phantom Roost, Frenzy Idol, Servitor Shrine, Floor Sigil) **and held 3D models** (first: the Occult Codex as a 3D book - see *Notes for G*) | - |
| H | Menu backgrounds | - |
| I | Effect sprites (motes, embers, shards, shockwave rings, beams) | - |
| - | Pack pipeline (assets in the jar -> Nexo external pack or Occultech's own pack) | before D (so C can be seen in game) |

## Session A - style and toolkit (2026-10-01)
**Delivered:** `tools/art/` (palettes, pixelkit, review), [STYLE.md](STYLE.md), and three icons in
[session-a/](session-a/) with the review sheet `review.png` (the user's final pick; iteration sheets deleted).

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
Essence (round little ghost); take the v4 Ritual Chalk. Final set: `review.png`.

**Lessons carried forward**
- A bold, simple silhouette beats a "correct" symbol: the badge-like star was preferred over the literal pentacle
  (circle across the arms). Favour striking shapes over symbolic accuracy.
- My own checklist judged v3/v4 better than the user did - when two versions both pass, show both and let the user pick.
- Build the silhouette first, then shade; check it in the silhouette column before adding detail.
- Avoid accessories that change what an object *is* (the twine made chalk into a scroll).
- Outlines must never cross other parts.

## Session B - sigils and## Session B - sigils and glyphs (2026-10-01)

### Round 1 - rejected
Built a separate glyph toolkit (`glyphkit.py`) that made everything **flat grayscale** so the game's text colour could
tint one glyph for every tier. Sigils (2 versions), 24 runes (3 versions), footprints and crown pieces (4 versions).
Its outputs were deleted after the review.

**User review:** the runes are nice and the paw prints are liked; everything else failed - sigils "lack volume and
are very flat" (the very first 64 px sample was nicer), soul flame and sparkle "boring", gem/halo/crown "nowhere near a
finished item texture", boot and bare prints disliked. Redo the session and relearn Session A's style.

**What went wrong (my diagnosis)**
- I let a technical convenience (tintable grayscale) override every rule in STYLE.md: no ramps, no light, no volume,
  no accent. Session A's icons worked precisely because of those rules.
- My self-critique only checked *readability and symmetry* (rules 1, 2, 8) - so it passed assets that ignored rules 3-6.
  Checking a subset of the checklist is not checking.
- The first sample was liked for things I then dropped: colour, a value hierarchy (bright figure over a darker ring),
  small marks in the circle's band, a glowing core.

### Round 2 - rebuilt in the Session A style
**Toolkit:** `pixelkit.py` gained `tubes` (line art as shaded tubes - raised, glowing inlay), `facet` (flat gem faces),
`ellipse_ring` (a torus seen at an angle), `glow` (soft bloom) and non-square canvases; `review.big_sheet` shows large
assets at 1x/2x and on dark, light and a stone floor. `session_b.py` = sigils, pieces, particles;
`session_b_glyphs.py` = runes and footprints (kept glyph style - those were liked).

Iteration names below (r2v1, r3v2...) are the versions as reviewed; only the final sheets are kept (see *Final files*).

**Iterations and self-critique**
- **Sigils r2v1** - six sigils (pentagram, hexagram, one per tier) each in its tier ramp: tube-shaded rings with marks
  in the band, the figure layered above with dark separation only where it crosses the ring, a shaded core, glow.
  Failed: glow too strong (the inside became haze, dirty on light); hexagram's wood ring muddy; Initiate's candles read
  as bottles; Bound's bottom chain made an orb-on-a-stand; Hollow's spike crown barely cleared the ring.
  **r2v2** fixed all five. Silhouette asymmetry 0 on all six (shading follows the light, so only coverage is mirrored).
- **Pieces r2v1** - gem facets lit by normals were too close in value (mush, nubs at the girdle); the crown's bevel
  striped the points into flames; the halo's glow filled the hole (a plate). **r2v2**: facet tones art-directed (lit
  top-left, dark right, refracted light bottom-right), crown shows the inside of its back band between solid points,
  the halo's hole stays empty. **r2v3**: T1 gem violet (spirit cyan was too close to T2 seaglow).
- **Particles r2v1** - animated now (soul flame 4 frames, sparkle 5-frame life). The flame's open mouth was cute, its
  body squat; the sparkle's peak frame filled into a diamond. **r2v2/3**: taller flame with a sharp swaying tip, tall
  hollow eye slits (a stare, not a smile); peak sparkle without glow and with diagonals detached from the centre.
- **Prints r2v1** - hand-drawn pixel maps now (geometry fails at this size). The boot's tread holes made a skull;
  the bare foot's deep arch read as a sock. **r2v2/3**: boot = lugged sole edges + separate heel; bare foot = gentle
  inner arch, toes arcing up to the big toe. Paw unchanged.

**Honest remaining weaknesses**
- Footprints and runes are still flat glyphs (by choice, they were liked) - they don't share the sigils' volume.
- The crown's side points are a little post-like; the Bound chains are subtle.
- Sigils are coloured per tier now, so a recolour means a new texture (no free tinting) - acceptable, there are few.

**Lessons carried forward**
- Every asset passes the *whole* checklist, including palette, light and volume - no shortcut is worth flat art.
- When the user liked an earlier sample, list what exactly made it work and keep those things.
- Art-direct values by hand (facet tones) when computed lighting gives mush; hand-draw pixels when geometry fails (prints).
- Particles are worth animating; emissive things get heat-coloured ramps, no outline, little glow.
- At 16 px, round features under ~3 px across become `+` shapes; mirrored asymmetric details double up.

### Round 2 review (user)
"So much better." Pentagrams liked a lot; gems liked but want more defined edges, more 3D and little magic sparkles;
**the animations are the favourite**. Footprints were the worst part: scratch the footprint shapes for something cooler
and unique, keep the paw. Develop a unique style drawing on other arcane mods and keep references for future sessions.

### Round 3
**References:** [REFERENCES.md](REFERENCES.md) - nine arcane mods (Malum, Eidolon, Occultism, Ars Nouveau, Botania,
Thaumcraft, Blood Magic, Iron's Spells, Forbidden & Arcanus): their look, what we take, and the synthesis *the
Occultech look* (dark vessel, living light; chromatic ramps; glowing inlay; the twinkle; hard facets; everything
magical moves). STYLE.md now points to it and has rule 11. Toolkit: `Icon.twinkle` (the signature motif), palettes
frost/ink/ash/blossom/pollen.

**Gems** (`review-pieces.png`, `preview-gems.gif`)
- r3v1: hard seams (bright girdle line on the lit half, dark below), light/dark facets alternating round the pavilion,
  8-frame animation (a glint sweeps the table, then twinkles take turns). Failed: twinkles touched the outline and
  merged into the silhouette; two reflection pixels drew a scribble on the left.
- r3v2: stone moved down 1 px, twinkles clear of it, scribble removed. Still a small "S" in the left pavilion: 2 px
  wedge facets are too thin to read as faces. r3v3: four wide pavilion facets (light, dark, light, dark). Pass.

**Step marks replace footprints** (`session_b_steps.py`, `review-steps.png`, `preview-steps.gif`): one per Aura
Talisman step style, 4 frames each (appear, peak, decay, trace - the game swaps glyphs as the mark ages).
- Ember: a charred ash patch whose cracks glow, flames lick, then cool to dark scars and smoke.
- Frost: an ice crystal blooms on an icy sheen, glints, then melts into pieces and droplets.
- Rune: a violet circle flares around a rune (ascend / bind, any rune can be used), breaks up, the rune lingers as motes.
- Ink: a flat glossy splat; **an eye opens in it**, stares, closes; the ink dries matte.
- Blossom: a closed flower opens (domed petals, pollen centre), petals spin outward, three loose petals drift away.
- v1 critique: ember frame 0 read as a yellow tile; the eye rune became a checkerboard; ink was a purple ball with
  tendrils that didn't read; the bud read as a bow tie. v2 fixed all four; v3 kept the dried ink's splat shape. Pass.
- The paw print stays (`review-prints.png`); boot and bare prints are dropped.

**Honest remaining weaknesses**
- Ember's first frame is still busy (bright cracks over a small patch); fine for a 3-second mark, could be calmer.
- Rune step uses 5x5 rune maps, not the 16 px runes - a few runes won't survive that size (the eye didn't).
- The step marks are animated by swapping glyphs (4 frames over 3 s), so motion is coarse compared to the particles.

**Lessons carried forward**
- Animation is what the user loves most - plan motion from the start for anything magical.
- Twinkles and other accents must never touch an object's outline (they merge into its silhouette).
- Facets narrower than ~3 px don't read as faces; fewer, wider facets with alternating values do.
- "Something unique" came from giving a mark a story (the ink eye opening) rather than a better shape.

### Final files (cleanup after round 3)
Iteration sheets, round 1, the dropped prints and the first `docs/art-samples/` were deleted; every file left is
regenerated by the scripts (`python tools/art/session_b.py sigils|pieces|particles`, `session_b_glyphs.py
runes|prints`, `session_b_steps.py`; a version argument such as `v2` writes `review-*-v2.png` for iterating).

| Files in `session-b/` | What |
|---|---|
| `sigil_{pentagram,hexagram,initiate,bound,abyssal,hollow}.png` | 64 px ritual sigils (floor decals / glyphs) |
| `gem_t{0..3}_{ember,violet,seaglow,crimson}_{0..7}.png` | animated gems, 8 frames (frame 0 = static icon) |
| `crown.png`, `halo.png` | 16 px item textures |
| `soul_flame_{spirit,crimson}_{0..3}.png`, `sparkle_{gold,hollow}_{0..4}.png` | animated particles |
| `{ember,frost,ink,blossom}_step_{0..3}.png`, `rune_step_{ascend,bind}_{0..3}.png` | step marks, 4 life frames |
| `footprint_paw.png`, `rune_*.png` (24) | flat glyphs (kept from round 1) |
| `review-*.png`, `preview-*.gif` | review sheets and animated previews |

## Session C - tier-0 item icons (2026-10-01)
**Scope:** the 15 tier-0 items that live in inventories (Ritual Chalk was done in Session A) plus the Quillshot Bow's
four draw textures. The 8 tier-0 *placed blocks* (Arcane Altar, Arcane Pedestal, Offering Bowl, Chalk Glyph, Initiate's
Altar, Trophy Board, Chiming Tile, Brood Egg) need block faces and move to Session G. Worked in three batches.
Script: `tools/art/session_c.py c1|c2|c3|set`; outputs in [session-c/](session-c/).

**Tier-0 look:** humble materials (chalk, bone, wax, iron, wood, ash, leather) with an ember accent; magic glows and
moves. New ramps: gel, leather, brew. New review view: `review.inventory` (a tier's icons together in slots).

| Item | Design | Frames |
|---|---|---|
| Grave Salt | a wooden scoop heaped with coarse salt, grains falling | 1 |
| Soul Ash | an ash mound with embers breathing in it, a curl of smoke | 4 |
| Occult Ink | a squat inkwell, near-black ink with a violet sheen, a drip | 1 |
| Warded Silver | a long silver bar in 3/4 view, a ward groove inlaid in ember | 4 |
| Binding Thread | a wooden spool of red binding thread, the end trailing to a knot | 1 |
| Tallow Candle | a stubby cream candle, wax runs, a swaying flame | 4 |
| Brood Silk | a spindle cocoon hanging from its strand, criss-cross wraps, web | 1 |
| Fletcher's Quill | a barred hawk quill, ember-dyed tip, iron nib | 1 |
| Coven Brew Base | a three-legged iron cauldron of sickly glowing brew, bubbles and vapour | 4 |
| Sovereign Gel | a glossy drop of royal slime, bubbles and a gold fleck inside, wobbles | 4 |
| Sovereign's Catalyst | a cube of gel with a gold crown suspended inside, a glint and a twinkle | 4 |
| Initiate's Sigil | a diamond plaque of carved bone, the sigil cut in and glowing ember | 4 |
| Occult Codex | a spellbook in the vanilla book pose: overhanging leather covers, iron corner guards, an ember jewel in an iron bezel, a clasp over the pages (redone after review) | 4 |
| Warding Charm | a silver amulet on a beaded cord loop, a warding eye that glows and blinks | 4 |
| Quillshot Bow | dark wood, silver recurve tips, ember in the grip; vanilla bow layout; full draw shows three arrows | 4 states |

**Iterations and self-critique** (the recurring failure: *what does it read as?*)
- **C1 v1:** Soul Ash too low with invisible smoke; Occult Ink read as plum jam; Warded Silver as bread/a cap; Binding
  Thread as a **mug** (thin flanges + looped end); Tallow Candle too orange. **v2:** taller mound + pale smoke; near-black
  ink, glass only at its edges; 3/4 ingot; wide flanges, red thread trailing to a knot; creamy tallow. New problems:
  symmetric embers made a **smiling face** in the ash; the short ingot read as a stone. **v3/v4:** embers in uneven
  clusters; a long bar; the rune inlay (a checkerboard at first) became a glowing groove with a crossbar.
- **C2 v1:** silk read as an egg/garlic; the cauldron of yellow brew read as a **pot of gold**; the gel as a cabbage;
  the crown inside the cube was two orange pixels that read as **eyes**; the sigil medallion as a **cookie**. **v2:**
  spindle cocoon, witch-green brew with swirl and vapour, a 7 px crown with three points, a dark medallion with solid
  glowing lines. Still: faint wraps, a halo of glow round the iron pot, the gel still a cabbage. **v3/v4:** darker wraps,
  no glow on the pot, the gel became a glossy drop (white highlight, reflected-light crescent, bubbles) - whose bubbles
  then made a face again, moved to one side.
- **C3 v1:** the codex cover circle was a waffle; the charm's eye a fried egg on "horn" cords; the bow's three arrows a
  streaky mess. **v2-v5:** clean ring with a hot centre; a closed cord loop, an almond eye with iris and pupil (blinks);
  the burst became three parallel arrows (a fan doesn't fit in 16 px - side heads landed on the main one).
- **Set check** (`review-tier0-inventory.png`): Brood Silk vanished on the grey slot -> bone-cream silk; Initiate's Sigil
  and Warding Charm were twins at 1x (round iron, orange centre) -> the sigil became a **diamond** bone plaque.

**Honest remaining weaknesses**
- Grave Salt, Binding Thread and Brood Silk are pale; they read, but they are the quietest icons in the set.
- The Codex fills its whole slot - the heaviest icon of the tier.
- Animated items need the pack pipeline (an `.mcmeta` per texture); until then, frame 0 is the icon.

**Lessons carried forward**
- Ask of every icon "what does it read as?" - mug, pot of gold, cookie, cabbage were all real readings.
- Symmetric pairs of bright dots on a round shape read as a face. Break the symmetry or avoid pairs.
- Check the whole tier together in slots: twins and low-contrast icons only show up side by side.
- When a shape doesn't fit 16 px (a fan of arrows), find a simpler sign for the same idea (parallel arrows).

### Session C follow-up: books (user review)
"The codex and other books should have a very similar silhouette to Minecraft books (an isometric view of the book).
Items that can be held, like the Occult Codex, need a rendering texture in the shape of a book. Draw inspiration from
Iron's Spells 'n Spellbooks for the codex. Focus on item icons for now; keep note of it for the block texture sessions."

- **Icon redone:** the codex now lies in the vanilla book's pose (cover a tilted parallelogram, white page block along
  the front edge, spine on the left) via `BookFrame` in `session_c.py`, which maps cover coordinates to the screen so
  everything on the cover sits in its perspective. Iron's Spells traits: thick covers overhanging the page block, iron
  corner guards, a jewel (ember gem in an iron bezel) as the emblem, a strap and clasp over the page edge.
- Iterations: v1 too steep and short (a blob) with a huge emblem (read as a sun); v2 vanilla proportions, clean pages
  with one page line, but the small emblem ring read as a "P" and the leather was pink; v3 jewel in a bezel, darker
  leather, twinkle moved clear of the cover. Pass.
- Rule for every future book (tier 1-3 tomes, grimoires...): use `BookFrame` - same pose and silhouette as vanilla
  books, only cover material, fittings and emblem change.

### Notes for G (block and model sessions)
- **Held book model for the Occult Codex** (and any later held book): a 3D model in Iron's Spells' manner - two thick
  cover cuboids overhanging a page-block cuboid, a rounded spine, raised corner guards, the jewel and the clasp as small
  elements - with its own texture sheet in the codex's palette (leather, iron, bone pages, ember jewel). The item model
  definition picks by display context (`minecraft:select` on `minecraft:display_context`): `gui` (and `ground`) show
  the 2D icon, hands/head/fixed show the 3D book. Same pattern for any other held item that needs a real shape.

## Session D - tier-1 item icons (2026-10-01)
**Scope:** 23 icons - every tier-1 item that lives in an inventory (Spirit Essence was done in Session A). The 6 placed
blocks (Bound Glyph, Bound Altar, Phantom Roost, Frenzy Idol, Servitor Shrine, Floor Sigil) move to Session G.
Script: `tools/art/session_d.py d1|d2|d3|d4|set`; outputs in [session-d/](session-d/).

**Tier-1 look:** violet, smoky glass, silver; spirit cyan is the magic accent; the theme is *binding* (bands, clamps,
spirits held in place). Boss drops keep their boss's colour (frenzy crimson, dusk, evoker emerald). New ramps:
boundsteel, parchment, emerald, dusk.

| Batch | Icons (* animated) |
|---|---|
| D1 materials | Bound Steel* (dark violet steel bar, two spirit bands pulse), Bound Chalk* (violet chalk in a silver band, cyan stroke - the Ritual Chalk's family shape), Resonant Crystal* (shard cluster on a rock, ripples round the tip), Bound Sigil* (silver triangle plaque, violet cut, a bound spirit at its heart) |
| D2 boss drops | Frenzied Edge* (serrated blade shard, frenzy-red teeth beat), Dusk Membrane (bat wing: arched arm, scalloped skin, claws, dusk gradient), Mirror Dust* (silver glitter heap, mirror flakes, moving twinkles), Evoker's Sigil* (gold fangs clamped on an emerald), Archevoker's Effigy* (illager effigy mid-spell, glowing eyes) |
| D3 gear | Frenzy Cleaver* (vanilla axe layout, cleaver blade, frenzy edge), Bone Scepter* (vertebrae staff, skull with burning sockets, wisp), Duskwing Charm* (winged violet gem, wings beat), Mirror Ward* (mirror-glass heater shield, the decoy ghost in it, glint sweep), Scrying Mirror* (black oval mirror on a stand, an eye opens in the mist) |
| D4 contracts and decor | 7 contracts as one family - a tilted scroll, the duty's emblem, a wax seal in the duty's colour (Harvest wheat/gold, Gather chest/wood, Brewer's Aid potion/pink, Shepherd shears/white, Beekeeper honeycomb/amber, Acolyte offering bowl/ember, Ward eye-shield/cyan); Moonlit Lily* (lily bells under a crescent moon, stars twinkle), Witchcap* (crimson toadstool with bubbling brew spots) |

**Iterations and self-critique**
- **D1:** Bound Steel as pale as Warded Silver -> darker tones; Resonant Crystal read as a castle/crown (blocky shards,
  flat base) -> narrow shards leaning out of a rock; then as antlers/coral with the sound rings crossing the side
  shards -> wider side shards, ripples moved round the tip; the ripples were lopsided from rounding -> mirrored exactly.
- **D2:** Frenzied Edge read as a kitchen knife -> broader shard, deep teeth; Dusk Membrane read as a heart/leaf, then
  as a **flag on a pole** (straight top edge + knob) -> rebuilt as a wing (arched arm, fanned fingers, scallops,
  thumb claw); Evoker's fangs too small -> big interlocking fangs.
- **D3:** Bone Scepter's skull was cute (small cyan dots) -> deep dark sockets with a burning point, cheekbones,
  vertebra joints; Duskwing Charm's loop + round gem read as a potion bottle -> loop removed.
- **D4:** square scroll filling the slot read as a **door/cabinet** -> tilted scroll with rolls; the sheep emblem was
  a white blob with two dark dots (a face, again) -> shears; harvest/beekeeper emblems vanished on parchment (set
  check) -> darker amber.

**Honest remaining weaknesses**
- Moonlit Lily's bells cluster at 1x; it reads as "white flowers + moon" rather than lily of the valley specifically.
- Evoker's Sigil reads first as a golden eye, second as jaws - a striking icon, but not literal.
- Contract emblems are 5 px; they're told apart mostly by the seal colour at 1x.
- Moonlit Lily and Witchcap are placed decorations too: their item icons are done, but how they look *placed* (they
  use vanilla flower/fungus blocks) belongs to Session G.

**Lessons carried forward**
- New wrong readings this time: castle, antlers, kitchen knife, flag on a pole, potion bottle, door. Keep asking.
- Families help: same shape, different emblem/colour (contracts; Bound Chalk with Ritual Chalk; Bound Steel with
  Warded Silver) - players learn the shape once.
- Low-contrast emblems on light materials disappear at 1x; check them in the set view.

### Session D review round (user)
"The flowers are fantastic, the contracts are incredible." Fix list, all done:
- **Bound Chalk** - a sharpened cone tip at the drawing end; the stroke is the chalk's own violet (a fresh glint runs
  along it, 4 frames).
- **Archevoker's Effigy** - now a reskin of the totem's familiar shape (big head, arms out, body narrowing to a point;
  our own pixels): grey-green illager face, heavy brow, long nose, emerald eyes, dark robe, gold collar, trim and cuffs.
- **Resonant Crystal** - one double-pointed crystal, exactly symmetric (no more crown): lit, front and shadow faces,
  ridges, a humming spirit core, mirrored ripples.
- **Bone Scepter** - the big round skull looked comical; now a hand-drawn angular skull (dark sockets with a spark,
  nose, teeth) on a jointed rod with a bone collar.
- **Mirror Ward** - exactly symmetric heater shield, a centred ghost in the glass, a shine band sliding down.
- **Scrying Mirror** - now a scrying orb: a glass ball of turning violet mist with an eye opening, a glass highlight,
  on a silver claw stand.
- **Bound Sigil** - a silver medallion carrying the Bound sigil (ring, clamped triangle, spirit at its heart), exactly
  symmetric. The first try filled the small triangle in (thick lines merging); crisp 1 px mirrored lines fixed it.

**Lessons:** match a familiar vanilla shape when the item replaces one (the totem); everything symmetric by nature
(shields, crystals, medallions) must be *exactly* symmetric - `mirror_silhouette` enforces it; at 16 px a small shape
drawn with thick lines fills in - use 1 px lines; look at the 16x zoom when the review sheet and the pixel data
disagree (the sheet is downscaled when viewed).

