# Art sessions: tracker

Each session finishes completely (assets + review sheet + self-critique + fixes) before the next starts.
Style rules and the checklist: [STYLE.md](STYLE.md). Plan: [../visual-overhaul.md](../visual-overhaul.md).

| Session | Content | Status |
|---|---|---|
| **A** | Style guide, toolkit, 3 test icons (Ritual Chalk, Spirit Essence, Hollow Sigil) | **Done** - reviewed |
| **B** | Sigils, runes, gems/crown/halo, animated soul flame and sparkle, step marks, paw | **Done** - approved, cleaned up |
| **C** | Tier-0 item icons (15 + bow states; the 8 placed blocks move to G) | **Done** - codex redone after review |
| **D** | Tier-1 item icons (23; the 6 placed blocks move to G) | **Done** - fixed after review |
| **E** | Tier-2 item icons (26: materials, drops, weapons, armor, decor objects) | **Done** - fixed after review |
| **F** | Tier-3 item icons (25 + bow states + the Aegis shield texture; Hollow Sigil from A) | **Done** - reworked after review |
| **G** | Blocks, held models, worn armor, placed decorations - split into G1-G7 (see *Session G*) | **Done** (G1-G7) |
| H | Menu backgrounds | later (moved after N) |
| ~~I~~ | ~~Effect sprites~~ - **dropped** (the user: retexturing particles would change other plugins' and vanilla effects) | - |
| **O1** | Block fixes: blue bottoms (smaller models -> chorus-plant states), stacking on custom blocks, Rune Obelisk (thinner base, less flat, clean edges), Soulfire Brazier (aligned textures, full rim), boss fights keep the turning sigil (no second pentagram) | **Done** |
| **O2** | Art retouch: the tier sigils and pentagrams crisp and finished; the armor inventory icons professional and symmetric | **Done** |
| **O3** | Trophy Board as a real pedestal with bosses shown at one size; the Arcane Altar reworked with the Session B pentagram | **Done** |
| **O4** | Floor markings for boss fights: attack warnings and ground zones (the user's picks) | **Done** |
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
- **Scepters (Wyrmbreath, Guardian's Gaze):** held 3D models following their icons - rod, collar, three claw prongs
  (one behind, two in front) round the orb/eye; the orb glows (emissive) and the eye can turn.
- **Tier-3 held models:** Dreadlance (shaft, ringed vamplate, leaf head), Soulfire Censer (orb on chains, swings),
  Heartwood Aegis (texture done in Session F: `heartwood_aegis_shield_*.png`, vanilla shield UV layout; for the rune
  to animate, build it as a regular item model with elements so the texture sits in an animatable atlas),
  Stormstring Bow (vanilla bow model + textures).
- **Hollow armor worn texture:** `equippable` layers in the reworked scheme - blackened violet steel plates, aged gold
  trim, bone crown spikes / ribcage / knee cops / toe caps, hollow-cyan seams, crimson gems (see the F4 icons).
- **Abyssal Anchor held model:** the icon is upright (an anchor only reads upright); in the hand it should be a 3D
  anchor held by its ring, flukes as the head, with the spectral chain - same display-context switch as the codex.
- **Abyssal armor worn texture:** the icons are done (Session E); the worn look needs an `equippable` asset layer
  (humanoid + leggings layers) in the same abyssal plates, fins and sea-glow trim.
- **Decorations placed in the world** (Moonlit Lily, Witchcap, Everliving Coral, Wisp Jar, Bottled Gale, Wind Chime,
  Orrery, Soulfire Brazier, Rune Obelisk): their item icons exist; how they look *placed* (vanilla blocks + display
  effects today) is a G decision.

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

## Session E - tier-2 item icons (2026-10-01)
**Scope:** 26 icons. Rule (as in D): full-cube blocks go to Session G; decorations that are *objects* (jars, chimes,
orrery, brazier, coral, obelisk) get icons. Script: `tools/art/session_e.py e1..e5|set`; outputs in
[session-e/](session-e/). Tier-2 look: abyss teal and prismarine, sea glow as the magic, iron and gold fittings; boss
drops keep their boss's colours. New ramp: wind.

| Batch | Icons (all animated) |
|---|---|
| E1 materials | Abyssal Alloy (the ingot family's teal bar, a wave of light running along its inlay), Tide Glass (hexagonal sea-glass tile, caustics wander), Abyssal Sigil (drop-shaped plaque - T0 diamond, T1 medallion, T2 drop - with a blinking eye), Tide Relic (a sea eye in a gold-bound prismarine cage, looking about), Abyssal Tether (a spectral chain: ring, links, hook) |
| E2 drops | Abyssal Lens (a magnifying lens, the beam point flares), Nautilus Core (nested whorls, a light pulsing in its opening), Choir Ember (a crystallised flame, sparks), Tempest Core (an orb in a turning whirlwind), Elder Scale (a great scale with growth lines, a glint) |
| E3 weapons | Wyrmbreath (gold rod, crimson dragon head breathing fire), Guardian's Gaze (a guardian eye on a wand, looking about), Grave Lantern (an iron lantern, a skull in its ghost flame), Abyssal Anchor (upright anchor, pulsing runes, spectral chain), Choir Bell (gold hand bell, burning shockwave) |
| E4 armor | Abyssal Helm, Chestplate, Greaves, Boots - vanilla armor-icon silhouettes, abyssal plates, prismarine fins (crest, shoulders, leg sides, heels), sea-glow trim that pulses |
| E5 decor | Bottled Gale (a twisting banded tornado in a bottle), Wisp Jar (round tinted jar, blinking wisps), Wind Chime (swaying tubes), Occult Orrery (sun, tilted dotted orbits, moving worlds), Soulfire Brazier (tripod, soul flames), Everliving Coral (tube coral, bubbles), Rune Obelisk (blackstone obelisk, eye rune, orbiting runes) |

**Wrong readings caught and fixed:** a candy (glass) - a hooded creature with teeth (sigil waves) - a tangle (coiled
chain) - a cracked egg, then a walnut (nautilus: a line spiral is mush at 16 px; nested whorls work) - a rune glyph
(scale ridges) - a golden club (dragon head too small) - a mace (spikes over the eye) - two eyes (a slit pupil splitting
the iris) - a bottle (lantern, twice) - a pickaxe, a curl, a ship's wheel (anchor; only upright works) - a robot face
(trim under the visor) - cracked ice and milk (tornado) - a purple chest (jar) - a trophy cup (orrery) - a grave (a
cross rune on an obelisk).

**Honest remaining weaknesses**
- Abyssal Sigil and Elder Scale are both teal rounded shapes; the eye tells them apart at 1x, but they're the closest
  pair in the tier.
- The orrery is busy at 1x (sun + dots + three worlds).
- The anchor is upright in the icon; held in the hand it will sit at 45 degrees until it gets a held model (G).

**Lessons carried forward**
- Some shapes only read in one orientation (anchor upright); for those, keep the icon readable and fix the hand pose
  with a model later.
- Spirals and coils: use nested shapes, not lines.
- A "familiar" silhouette must survive our recolour: a dark narrow-capped lantern stops being a lantern.

### Session E review round (user)
"Great work on the rest." Fixed:
- **Abyssal Sigil** - now the Abyssal sigil of Session B as a medallion: an abyssal ring, a dark face, a sea-glow eye
  (blinks), waves low beneath it; exactly symmetric. (So the core components are the three tier sigils: Initiate's
  diamond plaque, the Bound medallion, the Abyssal medallion.)
- **Choir Ember** - was flat; now a bevelled crystal flame shaded by the light, a gold spine ridge, a white-hot core
  showing through that pulses, a soft glow.
- **Wyrmbreath** - the dragon head looked goofy; now a fire scepter: a gold rod with ember bands and a collar, three
  gold dragon-claw prongs cradling a blazing red orb, flames rising. First try was one orange blob (ember orb in gold
  claws) - a crimson orb and dark edges where the front prongs cross it fixed that.
- **Guardian's Gaze** - drawn as its future 3D model would look: the same scepter build in prismarine and gold, the
  guardian's spikes become orange-tipped claw prongs cradling a glossy eyeball that looks about.
- Both scepters share `scepter()`: back prong behind the head, front prongs over it - the layering a 3D held model
  will have (noted for Session G with the codex and anchor).

**Lesson:** for held items, design the icon as a view of the 3D object (what's behind, what's in front) - it reads
as more solid, and the held model in G can follow it directly.

## Session F - tier-3 item icons (2026-10-01)
**Scope:** 26 icons + the Stormstring Bow's draw states; the Hollow Sigil is Session A's (the user's v2 pick). Blocks
(Hollow Assembler, Glyph, Altar, Servitor Nexus, Resin Tile) go to Session G. Script: `tools/art/session_f.py
f1..f5|set`; outputs in [session-f/](session-f/). Tier-3 look: sculk black-teal and old bone, hollow cyan as the
magic, crimson as the accent; boss drops keep their boss's colours (Heartwood amber, storm, corrupted crimson, Gallus
gold). New ramp: amber. Held items drawn as views of their 3D models.

| Batch | Icons (all animated) |
|---|---|
| F1 materials | Hollow Essence (Spirit Essence's dark sibling: void liquid, a black shade with cyan eyes escaping), Hollow Ingot (the ingot family's black bar with pulsing cyan veins), Hollow Crystal (a jagged dark shard with trapped light, echoes), Hollow Effigy (a sculk-dark jack-o'-lantern with a glowing face and Gallus's crimson comb) |
| F2 drops | Warlord's Brand (a branding iron, red-hot disc with the Hollow star), Heartwood Resin (amber with an eye that opens), Lancer's Pennant (a waving swallow-tail flag), Outrider's Fletching (three storm feathers, lightning between them), Corrupted Circuit (a chip glitching crimson), Mirror Visage (a mirror mask), Hollow Heart (a beating heartwood heart), Gallus Wishbone |
| F3 weapons | Dreadlance (lance: ringed vamplate, big blood-edged head, a drip), Soulfire Censer (pierced orb on chains, soul light), Lich's Phylactery (skull-stoppered bulb, a soul turning inside), Stormstring Bow (4 states: sculk and bone, lightning string) |
| F4 armor | Hollow Crown (bone crown on a sculk helm, visor of light), Cuirass (bone ribcage, crimson heart gem), Greaves (bone knee guards), Sabatons (bone toe caps) |
| F5 charms and decor | Hollow Halo (B's gold ring, travelling twinkles), Wishbone Talisman (a wishbone necklace, gold wrap, crimson gem), Aura Talisman (a crystal pendant cycling through colours), Gallus Egg (cracking with light, rocking), Heartwood Aegis (heartwood shield, regrowth rune), Watchful Eyeblossom (petals round an eye that opens) |

**Wrong readings caught and fixed:** sculk shading too light everywhere at first (a teal blob, not "Hollow") - Hollow
Essence too close to Spirit Essence - a teal blob with a flower on top (effigy) - a toy star wand (brand) - a trident,
then a tulip (fletching) - a spade (heart with a root) - an arrow (lance), a potion bottle (censer), a battery
(phylactery) - eyes on a box, a solid crown block, a mouth (helm) - a drawing compass / legs (talisman), a potion (aura
crystal), an onion (eyeblossom).

**Honest remaining weaknesses**
- The Soulfire Censer is still the busiest weapon at 1x (orb + chains + ring).
- Heartwood Aegis's grain is dotty rather than flowing.
- The Hollow Crown's helm is boxy; the crown carries it.

**Lessons carried forward**
- Check the base material's value first: "black" ramps drawn with mid indices come out mid-tone (sculk read teal).
- Outlines fill 1 px gaps (crown spikes): draw fine repeated details after outlining.
- The symmetry pass removes unevenly rounded lines - draw thin lines (cords) after it, mirrored by hand.

### Session F review round (user)
"Good job on the rest." Reworked:
- **Hollow Crystal** (weird shape) - now a crystal split in two, its halves floating apart with hollow light pouring
  out of the break, fragments orbiting; dark faces so the light reads. Exactly symmetric.
- **Hollow Effigy** (no pumpkin, be creative) - a ritual totem: a rooster's skull (Gallus is a rooster) with crimson
  comb and wattle, open beak, a burning eye socket, on a sculk stake bound with twine and black feathers. First try
  read as a cute chick - aged bone, a bigger socket and a crack fixed it.
- **Warlord's Brand** (looked like a downgrade) - forged like a weapon: a thick hexagonal iron head in 3/4 view with
  its depth showing, spiked corners, the Hollow star raised and white-hot, gold collar, leather grip, bone pommel,
  heat glow and embers.
- **Soulfire Censer** (needed an upgrade) - a gothic censer: a caged orb of dark iron with gold filigree, domed spire
  and finial, soul fire blazing inside the bars and venting, a smoke trail, a gold ring and chain.
- **Heartwood Resin** (flat) - lit volume, light glowing through its lower side, a specular streak, bubbles, a drip,
  the eye blurred in the amber's depth.
- **Hollow Heart** (odd shape) - anatomical: chambers, the aortic arch and great vessels with crimson cut ends, a
  tapering apex, cyan veins; it beats. Took two passes (a lumpy block first).
- **Dreadlance** (cooler, ominous) - a black barbed harpoon-blade with a crimson blood channel, smouldering runes on
  the shaft, a thorned bone vamplate, a tattered ribbon, dripping blood.
- **Hollow armor** (more detailed, cooler, nicer colours, think 3D) - hand-drawn plate by plate: blackened violet
  steel (each plate lit on its own), aged gold trim, bone (crown spikes, pauldron spikes, ribcage, knee cops, toe caps),
  hollow-cyan seams, crimson gems. First pass was too light (it matched tier-1 Bound Steel); darkened a full step.
- **Heartwood Aegis** (should be a Minecraft shield, a 3D texture) - now a 64x64 texture in the vanilla shield's UV
  layout (front 12x22 with heartwood grain, thin resin veins, bone rim, gold corner caps, amber boss, a tree-of-
  regrowth rune that pulses; plank back with leather straps and studs; bone edges; leather handle), 4 frames, with a
  3D preview (`review-heartwood-aegis.png`, `preview-heartwood-aegis.gif`). Its inventory look is the model itself.

**Lessons:** for hero items, hand-drawn letter maps beat geometry (the armor); a tier's materials must stay a step
apart in value from the tier below (tier-3 steel vs tier-1 steel); anything that is a vanilla model type (shield,
bow) is designed as that model's texture, not as an icon.

### Hollow Effigy redo (2026-10-04)
The user: the worst texture in the pack, unclear what it even is - it should hint that Gallus is a chicken but look
better. The rooster skull on a stake read as a vague bird blob at 1x (a skull in profile has no silhouette people know).
- **Now a rooster idol:** the weathervane rooster's profile (two peaks, tail and head, with a dip between - the most
  recognisable chicken silhouette) carved from black deepslate (Session G's ancient-city stone, the Hollow armour's
  material) on a plinth with sculk creeping up its front. Crimson comb and wattle and a gold beak are what make it a
  chicken; hollow cyan is the magic: a glowing eye, a crack in the breast, and **a tail of hollow soul-fire** - three
  sickle tongues curling back, heat-coloured like Session B's soul flame (white core at the rump, dark tips), no
  outline (emissive). Animated: the tongues flicker, sparks come off the tips, the eye and crack pulse. Hand-drawn
  letter maps (`EFFIGY_BODY`, `EFFIGY_TAIL` in session_f.py).
- Iterations: v1 scattered cyan specks (noise) and a stump tail; v2 one long crack read as a sash; v3 an arched stone
  tail with an inlay line read as a ring/magnet; v4 the fire tail (first clear chicken at 1x) but a big white wedge;
  v5 three tongues, small hot core; v6 a round breast and rump instead of a box. A variant with a gold saddle (hinting
  at the jockey) became a gold blob at 1x and broke "one accent" - dropped.
- **Lesson:** for a creature item, use the creature's best-known silhouette (here the weathervane rooster) and its
  signature colours (comb, beak); turn its *theme* into the magic part (the Hollowing becomes a soul-fire tail)
  instead of adding a symbol beside it.

## Session G8 - the Frenzied set, tier-1 worn armor (2026-10-06)
Design decided with the user first (docs/balance-plan.md, *Session G8*): Frenzy Idol colours (dusk-violet plates,
grey-silver trims and horns, ember only where it glows), big **bull horns** built from chunky 3D segments, glow plus a
few sparks. Inventory icons come only after the worn set is final in game. `python tools/art/session_g8.py <version>`
writes `docs/art/session-g8/review-g8-<version>.png` (worn from four sides with the helm on the head, the helm alone,
the flat layers) and a helm GIF; `final` saves into session-g for the pack.
- New review render: the mannequin wearing the layers **with the helm model on its head** (scaled 0.625 and turned
  half a turn about y, as CustomHeadLayer draws head items) - G6 never had the two together.
- v1: horns were long thin sticks almost 3 head-widths across, ridges read as beads, the body busy (pastel plate
  edges, many orange stripes); the preview showed the helm backwards.
- v3 (first shown to the user): six chunky horn segments - a fist-thick root at the temple, out, then up and forward,
  about 1.5 head-widths, a smooth grey-silver skin with two growth rings and an ember tip that breathes; a heavy silver
  brow lower at the middle with the ember sun, silver cheek guards, a violet domed shell. Body: darker plates, ember
  only under the pectorals, at the chest sun, belt buckle, knee studs and boot line; silver ridge, hem, belt, toe caps.

## Session G - blocks, held models, armor (2026-10-01)
**Split** (the user asked to split G where needed):

| Part | Content | Status |
|---|---|---|
| **G1** | The block-skin technique (block-model tools, 3D preview renderer, skin service in the plugin) + Initiate's Altar, Offering Bowl, Chalk Glyph (4 variants), Arcane Altar | **Done** |
| **G2** | Rest of tier 0 (Arcane Pedestal, Brood Egg, Trophy Board, Chiming Tile) + tier 1 (Bound Glyph, Bound Altar, Phantom Roost, Frenzy Idol, Servitor Shrine, Floor Sigil) | **Done** |
| **G3** | Tier-2 blocks (Occult Forge, Soul Condenser, Abyssal Glyph, Abyssal Altar, Guardian Eye, Pearl Bed, Ember Brazier, Abyssal Lantern, Tidal Tile, Prismatic Netherrack) | **Done** |
| **G4** | Tier-3 blocks (Hollow Assembler, Hollow Glyph, Hollow Altar, Servitor Nexus, Resin Tile) | **Done** |
| **G5** | Held 3D models: Occult Codex, Wyrmbreath, Guardian's Gaze, Abyssal Anchor, Dreadlance, Soulfire Censer, Heartwood Aegis (shield model) | **Done** |
| **G6** | Worn armor (`equippable` layers): Abyssal, Hollow | **Done - final, approved** (v10) |
| **G7** | Placed decorations: Wisp Jar, Bottled Gale, Wind Chime, Occult Orrery, Soulfire Brazier, Rune Obelisk (the plants stay vanilla) | **Done** (in-game check pending) |
| **N** | **Custom blocks the Nexo way** - Nexo-style without Nexo for now (see below; hookup: docs/nexo-migration.md) | **Done** (Nexo hookup on the server) |

**Direction (the user, 2026-10-01): the server runs Nexo, so Occultech's blocks are built for Nexo's custom-block
system.** Every block is authored as its final Nexo look: a block model (`occultech:block/<key>`) on a full-cube
note-block block - the hitbox is always a full block, but the model may show less than a block (bowls, egg, lantern,
glyphs...). The display-entity skins are the interim way to see them until Session N; while they last, a skin still
has to enclose its interim vanilla block.

**G4 blocks** (`python tools/art/session_g.py g4`) - the Hollow family: sculk black-teal, old bone, hollow cyan, a
crimson heart; glowing parts emit light (`light_emission`), as they will on Nexo blocks.
- Hollow Assembler - armoured sculk-black plate with slim bone corner ribs; a ribbed vent on each side where cyan light
  pulses upward round a crimson core eye; its top a 3x3 grid of glowing assembly cells (its nine inputs) lighting in
  turn. (v1's wide bone posts and bone grid read as a pale crate.)
- Hollow Glyph - glowing hollow-cyan runes on sculk slate, 4 variants. **Its vanilla block is now a gray carpet** (was
  sculk, a full cube): a flat tile like the other three glyphs.
- Hollow Altar - sculk-black masonry split by glowing cyan rifts, gripped at the corners by bone claws curling over its
  top; the Hollow Sigil's bold eight-pointed star glowing on top round a beating crimson heart.
- Servitor Nexus - a cage of bone posts and a crowning ring on a sculk plinth (the Hollow star carved in it), holding
  a churning heart of hollow-cyan light with the linked spirits circling in it; a small crest of light on top.
- Resin Tile - polished amber-resin bricks (`RESIN`, warm but not loud; v1 was loud orange, v2 read as wood), the
  same on every side and seamless as a floor; light pools in each brick, a fly caught in one, a glint slides across.

**G4 redo** (the user: "not sculky enough, a little flat and boring; the Hollow Altar looks like a major downgrade, the
Assembler too futuristic; the Nexus nice but the bones could be nicer - maybe a ribcage"). New materials:
`sculk()` - tileable sculk (torus Voronoi cells, dark crevices, soul spots pulsing in turn) with `soul_glow()` for an
emissive layer of just the spots; `DEEPSLATE` / `deepslate_tiles()` - ancient-city tiles with sculk creeping down
over them in a ragged edge; `bone_tex()` - grained, pitted bone instead of flat fills.
- Hollow Assembler - an ancient-city forge: deepslate tiles in reinforced-deepslate corners and foot, sculk
  overgrowing its upper half; a bone-barred arch on each side with soul fire burning behind it; nine bone sockets cut
  into sculk on top, a soul light in each.
- Hollow Altar - the summit of the altars: deepslate on a reinforced plinth, half swallowed by pulsing sculk; a
  catalyst's bone-rimmed dais on top with the Hollow star and its crimson heart; slim bone fangs at the corners rising
  and hooking inward like a shrieker's (v2's were chunky "bone towers"), sculk-sensor tendrils of light between them.
- Servitor Nexus - the heart of light now sits in a ribcage: a vertebral spine at the back, four ribs curving round
  and sloping down toward the front, falling short of meeting; the cage rooted in a mound of glowing sculk.
- Hollow Glyph - its slab is living sculk now, the rune burning in it.

**G5 held models** (`python tools/art/session_g.py g5`; folders `<key>_held`, wired by build_pack). In the inventory,
on the ground and in item frames these items keep their 2D icons; in the hand (and on the head) they are 3D - the item
definition selects on `display_context`, as vanilla's trident does. Glowing parts emit light.
- Held poses are vanilla's own: models are built upright and laid along the diagonal a sword sprite takes (every
  element turned 45 degrees about z), so vanilla's `handheld` transforms hold them like a sword; the codex lies in the
  x-y plane like a flat item and uses `generated`'s (held as a book); the Dreadlance is built in the trident's frame
  and uses `trident_in_hand`'s transforms, lifted 16 px to stay in bounds (`shifted_display` corrects each translation
  by the lift turned and scaled as that context turns it). **Not seen in game yet - check each pose.**
- Occult Codex - Iron's-Spells-style tome: thick leather covers with a tooled border overhanging bone pages, a rounded
  spine, iron corner guards, an iron clasp across the fore-edge, the ember jewel glowing on the cover.
- Wyrmbreath / Guardian's Gaze - scepters: pommel, wrapped grip, ringed collar, a cup with three claw prongs (one
  behind, two in front) hooking in over a glowing orb of dragon fire / a guardian's eye that glances side to side.
- Abyssal Anchor - held by its ring, the stock across above the hand, runes glowing down the shank, arms spreading at
  the top with the flukes turned down like a war hammer's head; a spectral chain trails from the ring.
- Dreadlance - black-violet shaft banded in crimson, violet pommel gem, a bone vamplate flaring over the hand, a silver
  leaf head with a pulsing crimson fuller.
- Soulfire Censer - a gold ring and handle, a short chain, a dark caged orb with soul fire behind cyan glass, gold band,
  cap and finial.
- Heartwood Aegis - vanilla's shield (plate 12x22x1, handle 2x6x6) rebuilt as a plain model where its entity renderer
  puts them, so Session F's 64x64 texture (vanilla shield UV layout, animated rune) maps on unchanged; held and blocking
  models with vanilla's shield / shield_blocking displays, switched on `using_item`. Its inventory look is the model.
  (The preview can't tell whether the design is mirrored; check the rune's side in game.)
- After review: Wyrmbreath and Guardian's Gaze have four claws at the orb's corners, hooking only over its top edges so
  the orb/eye stays in view; the eye looks out of the scepter's tip with one round pupil roaming in a wide circle
  (16 frames), veined sclera on its other faces. The Soulfire Censer hangs from the hand: held upright like a torch
  (item/generated's poses, slightly larger), the fist on a ringed handle, a chain dropping to the censer below. The
  Dreadlance's bone vamplate (odd in the hand) is now two slim steel rings. The Aegis is "not aligned correctly" in
  game - waiting on a screenshot to see how.
- Second review (with an in-game screenshot): the Aegis looks right in game (it was fine); its back was hard on the
  eye - repainted calm: dark vertical boards, soft grain, two bands. The screenshot also showed the hand's frame: with
  no display rotation a model's +y points forward along the arm's front and its -z runs down the arm (vanilla
  ItemInHandLayer), and where the fist really grips (`FIST`); `grip_display()` now poses models from that.
  - Soulfire Censer - turned 90 degrees so its chain hangs down the arm from the fist (in use, arm raised: no turn).
  - Guardian's Gaze - the eye is a ball (`eyeball_faces`): each face pixel is a point on it, iris or pupil by its angle
    to the gaze, so the one pupil darts round and slides across the faces to look every way (16 frames).
  - Wyrmbreath / Guardian's Gaze in use - right-click now uses the SPEAR pose (one arm raised forward) instead of the
    bow's draw, with an "in use" model (`<key>_held_using`, switched on `using_item`) pointing straight down the arm;
    flames and the beam now start at the staff's tip (`HeldWeapons.staffTip`), not the player's face.
  - Dreadlance - redone after fantasy-mod lances: a cruciform head of blackened steel (a broad leaf crossed by a
    narrower blade) with bright honed edges and a glowing crimson core, a gold socket with crimson gems and swept-back
    wings, a shaft wound with gold wire, a leather grip, gold ferrule and a butt spike with a violet gem.
  - Abyssal Anchor - a true anchor silhouette: round ring, ball-ended stock, runed shank, crown, arms in a smooth arc
    out and down to broad arrowhead flukes (held by the ring, swung upside down like a war hammer).
  - New: Frenzy Cleaver (wrapped haft, a heavy steel blade with a thick spine and pulsing frenzy-red serrated edge, a
    rivet) and Bone Scepter (stacked vertebrae with spurs, a skull with soul-green burning sockets looking forward,
    jaw hanging open, a wisp above).

**G6 worn armor - v3** (`python tools/art/session_g.py g6`). v1 was flat painted skins; v2 added 3D helms but its
textures were noise and checker patterns. The user's verdict on v2: "you forgot all lessons learned in Sessions A and
B" - with references (a clean-plated sea armor with layered fins, a crystal-spiked armor, a shaman set with a
carved mask, crystals and cloth).
- **Research:** those armors are mod models (GeckoLib/Blockbench geometry on every limb). A vanilla resource pack can
  add geometry in exactly two places: the helmet (any 3D item model, drawn on the head when its equippable has no
  asset) and the back (the equipment asset's `wings` layer = the elytra's two wings). Shoulder plates and the like
  need a client mod. So the sculpting goes into the helms and back pieces; the rest is texture, done properly.
- **The style, re-applied:** bold plate shapes, each a bevel lit from the top-left (`ArmorCanvas.plate`), dark gaps
  in the material's own tones, real value contrast (bright plates over a dark underlayer - v3a had plates and scales
  in the same values and nothing read), gems with hard facets (`gem`), glow only as inlay (`inlay`) - dark vessel,
  living light. No noise anywhere. Fins are clean silhouettes (`tex_fin_shape` on two-sided planes, `fin_plane`):
  three spines, smooth concave membrane, a glowing rim (the formula versions came out as specks - Session B's lesson:
  art-direct the shape). A mannequin preview (`mannequin`) shows the textures on a 3D body for review.
- **Abyssal** - a sea-monster mask helm: sculpted teal helm, the face behind a mask with a T visor (the wearer's eyes
  and mouth show through), fangs lining the mouth slit, a heavy brow with two small glowing eyes, glowing gill marks,
  three layered fan fins sweeping back from each temple, cheek fins, a tall dorsal crest from brow over the crown.
  Body: bright bevelled plates over dark scales - pectorals, narrowing abdominal bands, a sea-glow heart gem, a spine
  of stacked plates, layered pauldrons and bracers, belt and tassets, thigh plates and knee cops with sea-glow studs,
  plated boots with a glowing toe line and heel fin; back fins (wings layer).
- **Hollow** - a sculk shaman: a hood of dark violet cloth with a gold circlet, a carved old-bone mask (brow, nose
  ridge, cheekbones, carved teeth, eye holes the wearer's eyes show through) with glowing cyan markings and a faceted
  crimson gem; gold-ringed bone horns sweeping up and back; a cluster of faceted cyan crystals on the crown with
  lightning crackling between them and the horn tips; a rune-bead tassel behind. Body: dark violet robes with glowing
  cyan runes, bone plaques at the collar round a cut cyan crystal heart in gold, a bone spine down the back, bone
  pauldrons with crystal facets, wrapped sleeves and bone bracers, a gold sash with a crimson gem, a skirt of
  rune-marked panels with a gold hem, wrapped boots with bone toe caps; crystal vanes (wings layer).
- Not seen in game yet.

**G6 v4** (the user on v3: good direction, but it looks like a reskin - give it vanilla armor's 3D shape and
pauldrons, don't cover the whole body (the hands), make the back a layer of 3D detail on the chestplate rather than an
elytra, open the Abyssal mask up, angle its fins like the reference, real scales and cool leggings, blockier Hollow horns
thrusting forward, a mask closer to the Psi shaman's, better textures; the electric crystals were liked).
- **Coverage is vanilla netherite's** (`tools/art/vanilla_armor`, `CoveredCanvas`): vanilla armor reads as 3D because of
  where it covers - chest piece with a shaped edge, pauldrons on the upper arms only, bare forearms and hands, boots,
  leggings with a waist - with the body showing between. Painting every pixel made it a skin.
- **The back as a chestplate layer:** the elytra's wing geometry worked out (each wing hinges at a shoulder, x = +-5,
  crosses the back ~2 px behind it, tilted 15 degrees, flaring out lower down); `back_tex(shape(h, v, spine))` paints
  only each wing's own half, from the hinge to where it crosses the spine, so the halves meet at the spine as a raised
  plate across the shoulder blades and nothing hangs. Checked by projecting every painted pixel through the wings'
  transform onto a back view (hip fins tried first - they landed beside the arms: dropped).
- Abyssal: scales drawn as real scales (`SCALE_CELL`: a lit crown, body and the shadow cast on the row below, rows
  offset); a keel plate down the breastbone with a sea-glow gem, pectoral rims, pauldrons of three big layered scales,
  scale leggings with knee plates and hip fins, plated boots with a glowing toe line; back: a pair of spined fins fanning
  from the spine up to the shoulders (rays, lit membrane, glowing rim) over a spine ridge. Helm: open-faced (the whole
  face shows) - a crown of clean plates, a brow band with a sea-glow gem, cheek guards, two fan fins a side tilted up
  and out (22.5 and 45 degrees), a dorsal crest.
- Hollow: bone plaques carved with a dark groove, cloth in soft folds, a cyan crystal heart in gold, pauldrons ridged
  like vertebrae with a crystal each, a gold sash with a crimson gem over rune-marked skirt panels; back: a gold-edged
  carved bone plate and a fan of cut crystal shards from the spine with a few sparks. Helm: a tall Psi-style shaman mask
  of carved bone over a dark head-wrap - flat front, carved bands with glowing marks, a heavy brow, a long nose ridge,
  carved teeth, eye holes, a stepped crest above the head and a gold boss; blocky bone horns thrusting forward from the
  temples with a gold band; the crystal cluster with lightning, kept.

**G6 v5** (the user, with an in-game screenshot: "the abyssal armor looks really good" - but remove the back section,
players wear capes and elytras; the Hollow set needs a full rework).
- No back pieces on either set: the wings layer is gone (it took the cape/elytra slot and hung like one in game).
- Hollow reworked as a **sculk soul machine** - endgame armour in black, greys, sculk, light blue and purple, clean
  vanilla-style textures: heavy reinforced-steel plates (`DEEPSLATE`, bevelled) with sculk in the vents and gaps; soul
  power in light blue - a reactor core in the chest with conduits to the shoulders and down the spine, cores in the
  pauldrons, belt and knees, conduits down the legs, a glowing sole line; purple trim. Helm: open-faced - black-grey
  plates, sculk growing over the crown with its soul spots glowing, a brow band with a soul conduit and core, cheek
  guards, and two purple horns shaped like the warden's, climbing up and out and hooking over at the tips, conducting
  soul lightning: it crackles along each horn and arcs between them (animated, glowing).
- The Hollow item icons (Session F: violet steel, aged gold, bone) no longer match the worn set - to redo.

**G6 v6** (the user: the horns look like bunny ears - make them exactly like the warden's, purple, from the sides of
the helmet; both helmets' base texture is boring horizontal lines - make it look like a helmet; the body is good).
- `tex_helm`: three textures per helmet - a domed top with a raised crest and corner rivets, sides with a raised ear
  plate and a riveted rim band, a back with the crest running down to a flared neck rim; one light, no stripes. Both
  helms use it (Hollow's top stays grown over with sculk).
- Hollow horns = the warden's tendrils: vanilla's own 16x16 tendril artwork (`tools/art/vanilla_warden/warden.png`, as
  with the vanilla fire) recoloured into the violet ramp by brightness (`warden_tendrils`), set exactly as on the
  warden's head - flat planes at the helmet's sides, 16 px out, from 7 below the top to 9 above - softly glowing;
  soul lightning crackles over each (`tendril_lightning`, kept inside the shape) and arcs between their tips.
- The user: "I love both of these a lot more!" Last change: the Hollow helm's lightning is a thick bolt (white core,
  soul-blue body, purple glow, re-forking each frame) arcing from tendril tip to tendril tip up over the head; the
  sculk-grown top is gone (a steel dome with its crest); instead sculk creeps over the steel from the rim on the sides
  and back, along the brow band's lower edge and at the foot of the cheek guards.
- That arc's plane reached y 34 - past a model's -16..32 bounds - and the game rejected the whole helm (a black and
  purple missing model in game). build_pack now refuses any element outside -16..32. The arc is now plasma, lower,
  just above the tendril tips: a white core in a soul-blue sheath with three filaments splitting well off it,
  writhing and rejoining at the tips, a new pattern each of 8 frames, on two planes for depth.
- Then (the user): lightning as little cracks of plasma flying round each horn instead of an arc; creeping sculk
  infection in spots on the body with electricity running through it like cracks. Helm: ten small planes round each
  tendril, facing every way (x, z and turned 45 degrees), each showing one quadrant of an 8-frame spark texture in which
  each quadrant is a tiny zigzag bolt or nothing - so they flicker independently. Body (`infection`): ragged patches of
  raised sculk (lit cell crowns, dark crevices, a dark rim where they rise off the steel, a soul spot) on the abdomen,
  shoulder blade, a pauldron, a thigh, the back of a leg and a boot, each with a thin crack of soul light running
  through it and on across the plates (replacing the straight conduit lines); the cores and purple trim stay.
- Then (the user): the sparks were too small and looked like flying birds (tiny sideways zigzags read as wings);
  bigger, fewer, more sporadic; make the infection understandable with colour gradients; less random. Now: four bolts
  a horn on 6-unit planes, each a jagged downward stroke with a fork, alive 2-3 frames of a 16-frame cycle at its own
  moment; the infection is a radial gradient (glowing soul heart, bright sculk, darker sculk, veins reaching out over the
  plates, a shadow under its raised edge) placed on purpose - spreading from the chest reactor with a mirrored pair of
  cracks, climbing the spine behind, a matching patch on each pauldron and thigh - over a calm, gradient underlayer.
- **Locked in by the user as the final armour sets** ("that's great!!! lock these in"). What made them work, for any
  later armour: vanilla coverage (netherite's mask), all 3D in the helm (open face, horns/fins as flat silhouette planes
  as the warden does it), no back pieces (capes/elytras), clean bevelled plates and a calm underlayer, accents placed
  on the armour's structure and mirrored, gradients that explain a material (the infection), sporadic animated bolts.
  The Hollow icons (Session F) and the Abyssal Helm icon (Session E) were then redrawn to match the worn sets.

**Checked against the real 26.2 client** (the official client.jar, read with javap - unobfuscated since 26.1):
- Item displays turn their item half a turn about y (`DisplayRenderer$ItemDisplayRenderer`, `Axis.YP.rotation(pi)`):
  the Occult Forge's facing and the Guardian Eye's aim, which assume it, are right.
- Head items (`CustomHeadLayer.translateToHead`): head centre, turned 180 about y, scaled (0.625, -0.625, -0.625); an
  equippable with an asset is drawn as armour, without one the item model is drawn (`HumanoidArmorLayer.shouldRender`)
  - the helms sit on the head as built (head = model units 1.6..14.4, face toward -z).
- Display transforms: translate, rotate (`rotationXYZ`), scale, then -0.5 (`ItemTransform.apply`) - as `grip_display`
  and `shifted_display` assume. The hand's frame (`ItemInHandLayer`: x -90 then y 180) confirms the screenshot:
  model +y ahead out of the fist, -z down the arm.
- The SPEAR use pose raises the arm forward following the look (`SpearAnimations.thirdPersonHandUse`, x -90 deg) - as the
  staffs' in-use models assume.
- `light_emission` is applied to item quads too (`VertexConsumer` via `ItemFeatureRenderer`): the glows work.
- **Fixed:** the Bone Scepter's skull looked up, not ahead - in the sword pose a model's +x points up and its +y (the
  tip) ahead; the face is now on the skull's tip side. **Changed:** the Dreadlance (a netherite spear) now uses vanilla's
  own `spear_in_hand` transforms (its sprite runs head top-left to butt bottom-right: laid on the +45 diagonal; parts
  drawn twice as deep as wide because vanilla scales a spear 1.7 in-plane, 0.85 in depth). Held models' 2D icon cases
  now include 26.x's `on_shelf` context.
- **Dreadlance overhauled** (the user: darker, a new colour scheme, a nicer texture like the vanilla spear but upgraded,
  needn't be 3D): the 3D model is retired. It is now drawn like vanilla's spears - a 16 px icon (head top-right) and a
  32 px in-hand sprite in vanilla's layout (head top-left) shown through vanilla's own `minecraft:item/spear_in_hand`
  model (build_pack: `<slug>_in_hand_N.png` -> `<key>_in_hand`, selected outside the inventory) - in the Hollow armour's
  scheme: a leaf blade of blackened steel with a pulsing purple ridge, a sheen beside it and one honed soul-blue edge
  catching the light, a steel socket with swept lugs and a purple gem, a dark sculk shaft with soft soul bands, a
  violet-black wrapped grip, a steel pommel with a soul gem (`spear_sprite` in session_f.py).
  Then (the user): the 3D staff was better - keep it 3D and detailed, but in new colours, with the blade 2D like a
  vanilla spear's. Now: the 3D model is back on vanilla's spear transforms, in the dark scheme (steel butt spike and soul
  gem, ferrule, violet-black wrapped grip, steel collar, a dark sculk shaft with raised steel rings inlaid with soul
  light, a socket with glowing purple gems and swept lugs), and its blade is a flat sprite in the spear's plane
  (`dreadlance_blade`: a leaf of blackened steel, pulsing purple ridge, sheen, one honed soul-blue edge, outlined) -
  vanilla's 1.7x stretch makes it big and crisp like a vanilla spear head. The in-hand sprite is retired; the dark icon
  stays.
  Then (the user): no 2D head, and no purple down the middle ("doesn't make sense") - a 3D head one block thick with
  vanilla's spear-head shape. Now the head is `DREAD_HEAD`, vanilla's head traced from its 32 px in-hand sprite and stood
  upright (a triangle widening to 7 px with two barbs at its back corners, half a unit per pixel - vanilla's own size),
  built as voxels 1 unit deep (vanilla's 0.85 depth scale makes that as deep as a pixel is wide), one box per pixel run,
  shaded like vanilla's: a bright steel ridge, a lit half, a shadowed half, no accent colour.
  Then (the user): the staff shouldn't look wide, it should look round. Every staff part is now an octagonal section
  (two crossed boxes with the corners cut) and a little slimmer. Note: previews of spear models must squash depth by
  half (vanilla scales a spear 0.85 deep vs 1.7 in-plane); an unsquashed preview shows the staff twice as deep as it is.
- **Frenzy Cleaver re-skinned** (the user: a more realistic metal look, blood on it, not the glow): the glowing red teeth
  are gone. The blade's flat is plain forged steel (`CLEAVER_STEEL`, untinted): a bright honed bevel and dark grind
  line along the edge, a smooth gradient across the flat and one soft diagonal reflection; blood over it
  (`CLEAVER_BLOOD`: dried, fresh and a wet highlight - heaviest along the edge, runs inward, spatter), no light emission.
- **Lich's Phylactery -> Lich's Grimoire** (the user chose an open book over an orb of souls; the Occult Codex is a
  closed book with another job). Only the display name changed - the id stays `LICHS_PHYLACTERY` (items already made keep
  their old name). Icon `lichs_grimoire` (session_f): an open book, soul runes pulsing on both pages, souls rising.
  Held model `lichs_grimoire_held` (folder `lichs_phylactery_held`, keyed by id): held open on the palm - two
  sculk-leather halves tipped 22.5 degrees into a V (element rotations about y, checked in the 26.2 client:
  right-handed about the axis), bone-white pages with faded script and a printed rune, a glowing overlay where the runes
  pulse and a line writes itself, bone corner guards, a ridged spine with bone bands, a skull on the spine's far end, a
  crimson ribbon, four souls (blue, crimson) flickering out of step over the gutter. First person: tipped up toward
  the eye (the user: perfect). Third person, after the user's screenshot (tilted 30 degrees at scale 0.75 it stood up
  like a board showing its cover, half inside the hip): flat on the palm, pages up, scale 0.55, held by its inner half.
  Then (screenshot): flat, it looked like it came out of the hand - and it reached across the body, so in the
  third-person hand frame **+x points toward the body** (not outward). The user chose "open, held by its edge": the
  fist grips the near end of the spine and the open book hangs down beside the leg, pages facing outward (rotation
  0,-90,90; left hand 0,90,-90).
  Then (screenshot: hanging, it looked carried at the side): back to lying open and flat, pages up, but the fist
  grips the near end of the spine so the book reaches ahead from the hand (rotation 0,0,0, grip at the spine's end).
  Previews of rotated models: `tools/art/render3d.py` (true 3D, honours element rotations; blockkit's render_iso does not).

**G7 - placed decorations** (`python tools/art/session_g.py g7`; 3D preview [review-g7-3d.png](session-g/review-g7-3d.png)
from `tools/art/render3d.py`). Each model is the final Nexo look and, while skins last, encloses its interim vanilla
block; the effects (particles, orbiting runes and worlds) stay DecorationService's. The plants (Moonlit Lily, Witchcap,
Everliving Coral, Watchful Eyeblossom) stay vanilla blocks, as decided.
- Wisp Jar (flower pot) - a round jar of dark violet glass (octagonal sections: two crossed boxes), iron lid and knob,
  a curved highlight; three wisps blink inside on a glowing layer just over the glass.
- Bottled Gale (flower pot) - a tall round bottle of pale sea-green glass, long neck, cork; a white tornado funnel
  turning inside (animated); the gale's particles spill out above.
- Wind Chime (iron chain) - an iron chain from above to a thin octagonal wooden ring with cross-bars; six silver and
  gold tubes of different lengths on threads; the chain runs on through a wooden striker disc to a glowing sea-glass
  pendant. (v1's wide plank ring hid the tubes and read as a stool.)
- Occult Orrery (lightning rod) - abyss-stone foot ringed in gold with sea-glow gems, a fluted gold column, a slim rod
  to the sun's cup, and two gold armillary rings (level and upright) round the sun display, inside the worlds' orbits.
  `octagon_ring`: bars lie along the tangent - v1 laid the 90/270-degree bars the wrong way (a tangle, and one bar
  past y 32).
- Soulfire Brazier (soul lantern) - a bound-steel pedestal brazier: foot, riveted stem, a deep bowl ringed with soul
  runes that glow, a raised rim, glowing coals with heat in the cracks; the flames are the particles (soul or ember).
- Rune Obelisk (chiseled polished blackstone) - a full-cube plinth of dark dressed stone with a recessed panel on each
  face and a sea-glow inlay, a tapering obelisk above to a pyramidion with a glowing point, a sea-glow rune down each
  face (pulsing). Two blocks tall: the obelisk rises into the block above.
- **Upright interim blocks:** the skins are upright objects, so `BlockSkinService.upright` stands a sideways-placed
  chain (Wind Chime) or lightning rod (Orrery) up (neither needs support), and a Soulfire Brazier can't be hung from a
  ceiling (placement cancelled with a message). Self-test checks both, and that the six have skins.
- **Texture round** (the user: "crude... flat" - loved the shapes, and the jar and gale): new helpers `tone` (a ramp
  in clean steps), `bevel_grad` (a face lit from the top-left: vertical gradient, slight left-right falloff, bevelled
  frame) and `engraved_dial`. Obelisk: polished violet-black stone (`OBELISK_STONE`, 8 steps), bevelled plinth frames
  round recessed panels (upper/left walls in shadow, lower/right lips lit, floor fading down), one continuous gradient up
  the whole obelisk (each box maps its slice of one 16-tall texture), a bold stave-and-eye rune. Brazier: a rounded
  stem shaded as a cylinder with a collar and a rivet, the bowl brightening up to its lip, soul runes that truly glow
  (a glowing layer, small diamonds lighting in turn), overlapping shaded coal lumps over heat hottest at the heart.
  Orrery: the foot's tops are dials - abyss stone with a soft radial gradient in bevelled gold frames, an engraved gold
  ring and ticks - and the column is fluted (ridges lit, grooves dark, brighter toward the top).
  Preview note: render3d's painter sort can interleave a glowing layer with the face just under it; it's fine in game.
- **Bug (the user): an Occult Orrery lost its skin when its lightning rod oxidized** - lightning rods are copper and
  weather (exposed/weathered/oxidized), changing the block's type, so the skin was taken off. Fixed in
  BlockSkinService: weathering (`BlockFormEvent`) is cancelled on skinned Occultech blocks; a block already weathered
  or waxed is put back to its own type (state kept); and decoration tickers (DecorationBlock, WindChime) re-skin a
  block whose skin is missing (`ensureIfMissing`) - so old decorations also get their skins without
  `/occultech skins`. Self-test checks all three.
- **Wind Chime redone like a real one** (the user's screenshot: the middle - a thick chain stack, a disc, a glowing
  pendant - looked odd): the vanilla chain's two diagonal planes fit a 2.3-wide core (`CHIME_CORE`), not 3.2, so the
  middle is now a slim dark cord. A short iron chain to a round wooden top disc (radial shading), six round silver
  tubes graded long to short round the circle on strings, a wooden striker disc at their middle, and below them a
  wooden wind sail (one plaque, a carved swirl). `round_box` caps now sample one square by position (the octagon's two
  boxes showed seams).
- **Bug (the user): a skin under a block was pitch black.** A display is lit by the light where it stands, and every
  skin stood a block up (y+1) - inside the ceiling for a hung Wind Chime. Skins of blocks that let light through
  (chain, pot, lantern, carpet...) now stand inside their own block (y+0.5, no offset); solid cubes keep standing above.
  Old skins move on their next `ensure` (decoration tickers re-anchor theirs).

**Session N plan - Nexo note-block blocks** (N for Nexo - H is the menu-backgrounds session)
- Every Occultech block becomes a full-cube Nexo custom block (note-block mechanic, its own note-block state) showing
  its model: real blocks, so they appear and vanish instantly, render at full distance, cost no entities and can't be
  cleared by ClearLag. Animated textures keep working (they are textures in the model).
- Blocks that look smaller than a block (Offering Bowl, Brood Egg, Abyssal Lantern, glyphs, ...) keep a full hitbox
  and display as less than a full block.
- Offering Bowls sit a little higher above the ground than today's carpet-level plate (a full hitbox no longer
  forces them flat).
- Parts that move stay displays: the Guardian Eye's turning eye, Prismatic Netherrack's coloured fire, holograms.
- **Plants stay vanilla** (decided 2026-10-02): the Moonlit Lily (lily of the valley), Witchcap (crimson fungus),
  Everliving Coral and Watchful Eyeblossom keep their vanilla blocks and looks - no skins, no note blocks. A note block
  is a full solid cube; a plant must be walk-through and small, and the vanilla plants already look right (the
  eyeblossom even opens and closes natively). Their Occultech character is their effects (motes, spores, stars,
  bubbles). If a unique plant look is ever wanted, Nexo's string-block (tripwire) mechanic gives non-solid custom
  blocks - not note blocks.
- To work out: Slimefun + Nexo on the same block (placement through Nexo, Slimefun's block data and menus, breaking
  and drops, right-click), variants (glyphs, Tidal Tile corals, the Forge's facing), Nexo's item config generated
  from build_pack, a fallback to display skins when Nexo is absent.

**Session N - done Nexo-style, without Nexo (2026-10-03).** The test server has no Nexo, so (the user) the blocks are
built *like* Nexo's and move to Nexo easily later. Decisions (the user): glyphs are **string blocks** (walk-through,
flat - circles stay walkable); **no light** for lanterns/braziers (only their textures glow); the Nexo hookup is
**prepared now, finished on the server**.
- `build_pack` gives each block look a vanilla state of its own and records it in `tools/art/block_states.json`
  (append-only: placed blocks are stored as their state). Solid blocks: `note_block[instrument=<16 classic>,
  note=1..24, powered=true]` (384 states; vanilla note blocks never reach powered=true with Paper's noteblock updates
  off, and a fresh powered one is note 0). Glyphs: `tripwire[disarmed=true, ...]` (64 states). 54 states in use.
- The pack's `note_block.json` / `tripwire.json` are multipart: our states show `occultech:block/<model>`, every other
  state keeps vanilla's model. A skin's item display drew the model half a turn from a block, so plain blocks get
  `y: 180` and the Occult Forge a state per facing (north = as drawn) - the approved looks are kept exactly.
- Checked in the 26.2 client: block render layers come from the textures' transparency (`ChunkSectionLayer.
  byTransparency`), so cut-outs and glowing layers work on note blocks.
- Plugin: `CustomBlockService` places/reads/protects the states (no tuning, no note sound, no physics, water can't
  wash a glyph away; a plain note block that lands in one of our states is unpowered); `BlockSkinService` bridges and
  converts old skins as their chunks load (keeping the look: a tile's coral, a glyph's variant by position, a front).
  The Offering Bowl is raised 2.4 px on an iron stem (a full hitbox no longer forces it flat); its offering hovers at
  0.5. Paper's `disable-noteblock-updates` / `disable-tripwire-updates` are on in both test servers.
- With Nexo installed, `custom-blocks.mode: auto` keeps display skins and the pack handed to Nexo drops our
  blockstates (Nexo owns those states) until the hookup in docs/nexo-migration.md.

**Ritual sigils on the floor (2026-10-03, the user: "can the tier pentagrams from Session A/B be added to rituals as a
rotating hologram on the floor?").** Session B's tier sigils (Initiate, Bound, Abyssal, Hollow) became flat glowing
models (`ritual_sigil_t0..t3`, `python tools/art/session_g.py sigils`: one plane, the 64 px sigil, light 15). While a
ritual runs (`items/RitualSigil`), the altar's tier sigil unfolds across the circle (as wide as the circle), turns a
quarter turn a second, and folds away when the ritual ends or breaks; a summoning adds Session B's pentagram,
1.5 blocks wider and turning back at two thirds of the speed. The client does the turning (interpolated
transformations), the server sends one update a second; the displays are never saved. Self-test checks all three.

**Session O1 - block fixes (2026-10-03)**, from the user's list:
- **Blue at the bottom of blocks:** a note block is a solid cube to the client, so it hides the faces of every block
  touching it; under or beside a model smaller than its cube you saw through to the sky. Models that don't fill their
  cube (`is_full` in build_pack: an element spanning each whole face) now use chorus-plant states with neither up nor
  down (Nexo's CHORUSBLOCK type; natural chorus trees all but never make such a piece; 16 states, 14 used) - a chorus
  plant hides nothing. Paper's `disable-chorus-plant-updates` is on in both test servers. A look whose kind changed got
  a new state; its old one is *retired* in block_states.json (never given out again, still drawn with the model) and the
  plugin converts such blocks - decorations at once (their tickers), others when used or with `/occultech skins`.
- **Nothing could be stacked on an Occultech block, even sneaking:** the no-tuning guard denied every right-click on our
  note blocks, which made the click do nothing. Sneaking with an item now skips the block, as vanilla.
- **Rune Obelisk:** a thinner stepped base (a 14-wide foot, a 12-wide plinth with a recessed panel under a sea-glow
  inlay, a cap), laid stone courses up the shaft; every face drawn to its own size (`exact_box`: one texel per unit -
  the tapering faces had squeezed 8 texels into narrower boxes, the "edge problems").
- **Soulfire Brazier:** faces drawn to size; two runes centred on each side (they ran off-centre); the rim's top
  texture covers its short bars (they sampled past a 2-row texture - the missing pieces); collars round the stem.
- **Boss fights:** the summoning's second pentagram is gone; the circle's sigil stays on the floor through the fight,
  turning a quarter turn every 4 s, and folds away when the fight is over.

**Session O2 - art retouch (2026-10-03).**
- **Sigils** (`tools/art/session_o2.py`, replacing Session B's six in `session-b/sigil_*.png` and so the ritual floor
  holograms): the user wanted crisp pixelated edges and a finished look. Half of every old sigil's pixels were a
  semi-transparent bloom (a haze, not pixel art), lines stepped unevenly and nothing held the edges. Now: every pixel
  fully solid or clear; rings shaded as round tubes (the crest lit top-left, the bottom-right rim catching light) and
  every bar a tube of even width; a 1 px outline in the sigil's own darkest tone; faceted gem cores with a glint (the
  Session B gem style); glowing rune marks in the band; shapes mirror-symmetric (checked: 1-6 px, the glint). The
  Abyssal eye's lids are two arcs meeting at the corners; the Bound spirit is bound by three spokes.
- **Armor icons** (`tools/art/session_o2_armor.py`; session_e/f's functions draw from it): vanilla's armor
  silhouettes (what players read as armor at a glance), each drawn as its left half and mirrored - exactly symmetric -
  the mirrored half a step darker (light from the top-left). Abyssal: teal plate, scale arcs (the old checker of
  scales broke the no-checker rule), fins, sea-glow brow, gem and soles. Hollow: black-grey steel, purple horns, cuffs
  and hem, sculk creeping on cheeks and thighs, a soul core and soul-blue soles. v1's boots read as bottles -> wide
  shafts with cuffs, toes and glowing soles. Sheet: `session-e/review-armor-o2.png`.

**Session O3 - showpieces (2026-10-03).**
- **Trophy Board -> a real pedestal:** a museum pedestal in dark polished wood with thin gold lines - a stepped base,
  a column whose faces carry a framed panel with a small gold trophy cup, a moulded capital, a crimson velvet cushion
  piped in gold (tufted) where the statue stands. v1 was mostly gold and read cheap; the panel's crossed blades read as
  a checker at 8 px. It's smaller than its cube, so it moved to a chorus-plant state (15 of 16 used).
- **Boss statues at one size:** they were scaled by height only, so wide bosses (spider, guardian, phantom) stood
  oversized. Now by the larger of height and width, times how far a look spreads past its hitbox (phantom wings 1.9,
  guardian spikes 1.3, breeze and blaze 1.15), to 0.75 blocks; they stand on the cushion (15 px up).
- **Arcane Altar reworked:** its custom block no longer has the vanilla enchanting table's floating book. Now: dark
  stone brick on a gold-banded plinth with ember arcane eyes, a top slab with O2's crisp pentagram inlaid and glowing
  (the 64 px texture across the top), and an open spellbook floating above it - violet covers tipped into a V, pages
  of violet runes lighting in turn, a soft glow.
- Preview tool: `render3d` sampled every texture at 16 px (a 64 px inlay came out smeared) - fixed.
- Then (the user): the pentagram goes on the ground while the altar crafts, not on its top. The top is plain stone
  again (the floating book stays); an infusion lays O2's pentagram across the pedestal ring as a glowing floor hologram
  (`ritual_sigil_pentagram`, 5.6 blocks), turning faster as it builds (a quarter turn in 20, 12, then 8 ticks) and
  folding away when it finishes, the altar breaks or the server stops. Without the pack the old particle pentagram stays.

**Session O4 - floor markings for boss fights (2026-10-03).** Options offered: attack warnings, ground zones, impact
marks, boss-themed colours; the user chose **warnings** and **zones**. Both replace the fight's potion-particle clouds
(kept as the fallback without the pack) and go through the two calls every boss already used, so all fourteen attacks
and three zones changed at once (`boss/FloorDecals`; art `tools/art/session_o4.py`; sheets
`session-g/review-o4.png`, `review-o4-floor.png`).
- **Warnings:** a ring at the exact hit radius (it snaps out in 6 ticks), a see-through fill that grows from the centre
  and reaches the edge as the hit lands, and the attack's symbol in the middle (slam, dive, web, flame, storm, spikes,
  wind, roots, sweep, danger). Drawn in shaded light greys and tinted per attack by the item model's dye tint
  (`tint.txt` in a part folder -> `tints: [dye]` in its item definition; faces carry `tintindex`), so each attack keeps
  its colour; very dark colours (the Hollow Warlord's near-black sweep) are lifted to stay visible.
- **Zones:** animated, fully coloured 32 px surfaces sized to the damage radius - acid (bubbles swell and pop, glows),
  web (strands with gaps, a glint runs round), yolk (white rim, glossy yolk) for the existing three, and fire (charred
  cracks, flickering flames, glows), poison (a slow swirl), frost (cracked ice, a glint), shadow (turning tendrils)
  ready for new attacks. They unfold and shrink away at the end.
- Every marking is an item display spawned through the fight (removed with it), never saved, animated by the client.
- **Fix (the user): markings spawned tilted, half under the floor.** A display takes its spawn spot's rotation, and
  spots taken from a player carry their pitch and yaw. Markings now drop the rotation and snap to the top of the floor
  under the spot (`FloorDecals.floor`: out of solid blocks, down to the floor, the block's real top - slabs, carpets).
- **More attacks marked** (the user: every boss fight that needs it). New shapes: a **wedge** (The Unbound's cleave),
  a **lane** (Tidebreaker's ram, the Vanguard's lance charge), a **travelling ring** (the Sovereign's landing shockwave,
  the Drowned Elder's tidal waves, the Tempest's squall closing in and holding), a **splash** (where the Witch Coven's
  harming potions burst), a **curse** mark (the coven's curser), small rings on each Archevoker fang, the Brood
  Mother's pounce landing, and the Doppelganger's echo path in shadow before the echo walks it. Each keeps its old
  particles as the no-pack fallback. Self-test: markings lie flat from a tilted spot in the air; the new shapes appear.

**Session O5 phase 1 - effects in the air: beams, chains, bolts (2026-10-03).** Plan agreed with the user: beams and
bolts, then hit bursts, auras, projectile skins - each phase reviewed in game first. The global-clock problem (an
animated texture can start mid-animation): these textures are seamless loops scrolling along the effect, and every
"start" is the display's own interpolated motion (`boss/AirEffects`, art `tools/art/session_o5.py`, sheet
`session-g/review-o5.png`). Models: two crossed planes along y, the texture repeated 8 times along a beam/chain, tinted.
- **Beams** - one change in the shared `Abyss.Beam` covers the Abyssal Warden, the Drowned Elder and its guardians, the
  Colossus pylons, the Outrider's snipe and Gallus's hollow echoes: the beam shoots out to its target, tracks it
  (re-aimed once a boss step, interpolated), thickens as it charges, turns white for its warning, flashes white and
  wide as it fires, collapses and goes.
- **Soul chains** - the Hollow Warlord's chains to each living guard while two or more shield it; a chain snaps when its
  guard dies or the shield drops.
- **Plasma bolts** - three jagged shapes at random: one drops from the sky in 3 ticks, flashes, thins away; at the
  Outrider's snipe hit and on its arrow rain, alongside the vanilla lightning flash and thunder.
- Without the pack, fights keep their particle lines.
- Fix (the user: "the pylon beams don't seem to have any effects; still the purple dust"): the pylon beams fired from
  the Colossus's eyes (the shared beam had no other firing point) and the pylons' repair links were still drawn in
  dust. `Abyss.Beam` takes a firing point (a pylon's tip; it fizzles if the pylon breaks), and each standing pylon feeds
  the Colossus a thin stream of corrupt energy that snaps when it breaks.

**Session O5 phase 2 - hit bursts (2026-10-03).** A burst plays once from its first frame: its five 32 px frames are
separate models, and the server steps the item's custom-model-data number every 2 ticks (`build_pack`: part folders
`<name>_f0.._f4` become one item `<name>` that range-dispatches on custom_model_data); facing the viewer (billboard),
tinted, glowing, gone after 10 ticks. Art: `session_o5.py bursts`, sheet `session-g/review-o5-bursts.png`.
- **Slash** (a crescent drawn on, flaring, breaking into sparks): The Unbound's cleave, the Warlord's sweep.
- **Impact** (a point, a star of rays, a ring racing out, sparks): the Sovereign's landing, the Colossus's slam, the
  Night Matriarch's dive, the Tempest's wind burst, the Abyssal Warden's spikes, the Blaze Choir's eruptions.
- **Crackle** (plasma forks round a point): on whoever any beam hits (Warden, Elder, pylons, snipe, echoes).
- **Soul** (an orb, a blooming ring, wisps rising): a fight object broken (egg sacs, wards, pylons, hearts,
  phylacteries) and an add killed (guards, shards, thralls, vexes...).
- **Splash** (a blob bursting into droplets): where the Witch Coven's potions burst, with the floor splash.

**Session O5 phase 3 - boss auras (2026-10-03).** Flat glowing rings that stay with a boss and show its state; their
textures loop seamlessly (the pattern repeats k times round the ring and turns 1/k of a turn over 8 frames). They
follow their host each boss step with an interpolated teleport - not as passengers: a boss carrying a passenger can't
be teleported, and the arena's anti-pillar rule, the Horror's lunge and the Matriarch's landing all teleport bosses.
`AirEffects.Aura` (the fight keeps them following); art `session_o5.py auras`, sheet `session-g/review-o5-auras.png`.
- **Blaze Choir** - a ring of fire on the shielded singer; it passes with the shield.
- **Hollow Warlord** - a soul halo over its head while two or more guards shield it.
- **Heartwood Horror** - a coil of roots with amber sap round its feet while its hearts make it invulnerable.
- **Volley** - an amethyst ward ring round it while a ward crystal stands; each ward also feeds it a stream of violet
  light (the old particle line), snapping when the crystal breaks.

**The technique (G1).** Nothing vanilla is retextured. A placed Occultech block keeps its vanilla block (Slimefun's);
`items/BlockSkinService` puts an item display over it showing our model (`occultech:<id>`, 1.004x so it hides the
vanilla block; the display stands on top of the block so it is lit by the air above, its model shifted down into the
block). Displays have no hitbox: clicks and breaking reach the real block. Skins are saved with the chunk, re-tracked on
load, and removed when the block is really gone (type changed) - never just because Slimefun's data isn't loaded yet.
New placements get a skin from `SlimefunBlockPlaceEvent`; altar upgrades and debug placement call `ensure`;
`/occultech skins [radius]` skins blocks placed before skins existed. The inventory item uses the same 3D model.
Rule: a skin must enclose its vanilla block's shape - so a block that should look low needs a low vanilla block.

**Tools:** `tools/art/blockkit.py` (Model: textured boxes -> block-model JSON; `render_iso`: a 3D preview drawn like the
inventory shows a block), `tools/art/session_g.py` (per-block models + textures into `docs/art/session-g/<key>/`),
`build_pack.py` now packs block models, block-atlas textures (animated via mcmeta) and `occultech-pack-skins.txt`
(id + variant count). Self-test: skins appear, never duplicate, vanish with their block (285 checks pass).

**G1 blocks**
- Initiate's Altar - chalk-stone masonry on a dark plinth, an ember rune band, bone trim, an Initiate-sigil top that
  breathes, four burning candles.
- Offering Bowl - first a blackstone pedestal with a bowl on top; **the user: bowls must be lower so they don't hide
  the altar.** A skin can't be smaller than its vanilla block, so the Offering Bowl's vanilla block is now a black
  carpet (recipes.yml) and the skin is a thin blackstone plate with a low hammered-iron bowl of embers, ~5 px tall;
  holograms float just above whatever is there. (Bowls placed before this stay blackstone, unskinned, until replaced.)
- Chalk Glyph - a thin dark-slate tile over the carpet with a chalk rune; 4 variants picked by position.
- Arcane Altar - gold-banded dark stone, ember arcane eyes on the sides, a turning star on top (full cube, so the
  enchanting table's floating book is hidden).

**G2 blocks** (`python tools/art/session_g.py g2`)
- Arcane Pedestal - a deepslate column (enclosing the wall's post) with a gold-banded base and capital, an ember eye
  glowing on top where the offering rests.
- Brood Egg - a rounded sac of wound spider silk built up in layers (enclosing the sniffer egg), dark eggs pressing from
  inside, crimson veins pulsing, a strand from its top. v1 read as a speckled block of sand.
- Trophy Board - a display pedestal: dark wood panels in gilded frames, a gold crest, a crimson velvet top for the
  trophies. v1 (planks + iron frame) read as a wooden crate.
- Chiming Tile - pale stone with an amethyst star inlay, a ring of light spreading from it (animated).
- Bound Glyph - violet chalk runes on slate, a spirit glint; 4 variants.
- Bound Altar - violet masonry gripped by silver corner clamps, a pulsing band of spirit light, the Bound sigil on top
  and the spirit rising from it as a glowing orb.
- Phantom Roost - a lattice of bone ribs with dusk membrane between them, a dark nest and crossed perch bones on top.
- Frenzy Idol - **redone after review** (the user: "more benevolent, but still angry/serious, orange undertones, a
  non-human face"): a ram guardian in dark terracotta - a pale amber ram's muzzle with flared nostrils, a heavy brow bearing
  down over calm amber eyes, a gold sun on its forehead that breathes light, ivory ridged horns spiralling down its sides.
  First pass was one flat gold (no value contrast, horns like logs); darker stone and a pale muzzle fixed it. (The first
  design - a snarling crimson face with fangs - read as hostile.)
  Then recoloured into the Bound tier family (the user: "match the tier, with orange undertones, along with its
  visual effects"): dark violet slate with ember-brown seams, a silver muzzle with a peach highlight, silver horns,
  ember-orange eyes and sun. Its particles changed from angry-villager clouds to violet motes warming to orange plus
  small flames.
- Servitor Shrine - violet stone framed in silver, an arched niche on each side with its spirit glowing in it, a
  stepped silver roof and finial.
- Floor Sigil - stone with a violet five-pointed sigil turning on its top.
- The self-test's "items without art" check now picks any item the pack has no model for (it broke each time a block
  got art).

**G3 blocks** (`python tools/art/session_g.py g3`) - the Abyssal family: deep teal and prismarine, iron and gold
fittings, sea glow; fire blocks in ember.
- New in the skin service: **skins turn with a block's front** (a horizontal `Directional` block: the model's north face
  is its front; item displays draw a model half a turn round, which the base angle undoes - check the Forge's mouth
  faces you in game) and **skins follow a tile's look** (`StepTile.lookVariant`: variant 0 is the item's own block,
  then the other looks by name; right-click updates the skin in place instead of the type change deleting it).
  Pearl Beds no longer dry into dead coral out of water. Self-test checks both (287 pass).
- Occult Forge - abyss stone bound in riveted iron, gold corner fittings; its front an arched furnace mouth with ember
  fire licking (animated); a sea-glow Abyssal rune on each iron flank; a glowing grate and a short chimney on top.
- Soul Condenser - an iron cage with gold-capped posts, smoky glass panes with a sea-glow wisp circling behind each,
  trailing its tail (animated, 8 frames); a gold condenser coil round a pulsing core on top. (v1's wisp was scattered
  dots on near-black glass - it didn't read.)
- Abyssal Glyph - sea-glow runes on abyss slate; 4 variants.
- Abyssal Altar - deep-teal masonry banded in gold, a rolling sea-glow tide in a dark band round its middle, prismarine
  crystal spires at the corners, the Abyssal eye sigil on top with a drifting pupil. (v1's tide was lost in the bricks.)
- Guardian Eye - a guardian made sentry: teal scaled hide, amber spikes at its corners and edges, a great eye on every
  side whose slit pupil glances left and right (16 frames, so the gaze holds).
- Pearl Bed - sea-floor rock with a coral crust along its top edge; on top a blush-pink scallop fan standing open
  behind a big glowing pearl. (v1's ivory shell read as a chair and hid the pearl.)
- Ember Brazier - a squat black-iron stove: riveted plates, a barred grille with coals glowing behind, a gold lip, and
  coal lumps with fire breathing between them on top. (v1's all-over slats read as a crate.)
- Abyssal Lantern - dark iron cap and foot rimmed in gold, iron posts, sea-glow panes brightest at the heart with
  bubbles rising; an iron hanging ring. (v1's gold cap overpowered it.)
- Tidal Tile - living coral in a worn prismarine frame, a water film glinting over the top; 5 variants (tube, brain,
  bubble, fire, horn), shown for whichever coral the tile is set to.
- Prismatic Netherrack - dark nether rock split by two crystal cracks whose light runs through the rainbow (8 frames);
  the top stays flat for the fire. (v1's scattered vein pixels didn't read as cracks.)

**G2/G3 revisions after review** (the user: Pearl Bed, Soul Condenser and Ember Brazier "AMAZING"; the rest below)
- New in the tools: elements can glow (`light_emission`, so they shine in the dark) and turn (45-degree crossed planes);
  a model can be a *part* the plugin shows itself (`part.txt`, not a skin), and a block whose inventory look differs
  from its placed skin gets a `<key>_inventory` model (the item definition selects on `display_context`: "none" is the
  skin's item display).
- Bound Glyph - "not clear enough, glow stronger with purple light": the rune now also burns on an emissive layer over
  the tile, white-violet strokes in a soft violet halo, pulsing.
- Phantom Roost - "looks off": redone as a small tower of dark slate where phantoms sleep - silver corner caps, an
  arched roosting hole on each side with a phantom's pale green eyes glowing in the dark (emissive) and now and then
  blinking, a silver perch on top with rags of membrane hanging from it. (The bone lattice read as a crate of ribs.)
- Brood Egg - "the shape looks off": a real egg profile - wider than its foot, bulging round its middle, rising to a
  rounded crown above the block (the sniffer egg's 14x16x12 box is still enclosed up to y16).
- Guardian Eye - "an eye on a column that shoots the lasers": the block is a fluted column of guardian stone, amber
  spikes round its capital, a gold claw cradle on top; the eye is a separate display (`guardian_eye_orb`: pale hide,
  sea-glow iris with a slit pupil, glowing) that the plugin turns toward its target - or slowly round when idle - and
  the beam now leaves from the eye. The inventory shows the column with its eye.
- Abyssal Lantern - "a little smaller than a full block": vanilla block is now a LANTERN (light 15), the skin a lamp
  12 wide and 14 tall with glowing panes, enclosing the lantern standing or hanging. Lanterns placed before stay sea
  lanterns, unskinned, until replaced.
- Tidal Tile - "no grid pattern when placed together": seamless coral, no frame, polyps wrapping round the edges.
- Prismatic Netherrack - "requires new textures for fires in different colours": it now burns with its own fire.
  Lighting it (flint and steel, fire charge, spreading fire, lava) puts an invisible light block (level 15) on top
  instead of vanilla fire, and the plugin shows coloured flames there (`prismatic_fire`, `_v1`, `_v2`: rainbow, aurora,
  dusk - crossed planes like vanilla fire, glowing, 16 frames) in the palette chosen by right-click. It never spreads
  or burns anything; a left-click on its top or water puts it out. Without the pack it keeps vanilla fire + sparks.
- Self-test: the eye exists and turns along its gaze; the netherrack lights, shows its flames and puts out (292 pass).

**Second review**
- Skins lagged a second behind their blocks (put on a tick later after looking the block up in Slimefun's storage;
  taken off by a 2-second sweep). Now they come and go in the same tick: placing skins the block from the item in
  hand, and breaking, burning or an explosion removes it at once; the sweep (now every second) only catches the rest.
  Nexo looks instant because its blocks are real block states with retextured models - nothing to spawn - but that
  needs vanilla block states set aside for the pack, which clashes with Nexo and other packs; displays stay.
- Chiming Tile - polished stone bricks in a muted lilac grey (`LILAC_STONE`), the same texture on every side and
  running bond across exactly one block, so floors and walls join seamlessly; two amethyst quavers inlaid, catching
  the light in turn on top.
- Tidal Tile - corals pulled ~18% toward grey.
- Brood Egg - blocky like the sniffer egg it covers (a 14x12 block of silk with a low cap and a strand).
- Prismatic fire - now vanilla's own fire (`tools/art/vanilla_fire`: fire_0/fire_1 and their timing, from the 1.21.5
  client; the floor-fire shape from template_fire_floor) recoloured: every pixel keeps vanilla's lightness, its hue
  runs through the palette rolling up the flame and through time, like the first version's rainbow sparks.

