# Occultech art style

The look we aim for: chunky, readable, lightly hand-made pixel art in the spirit of magic mods like Occultism - our own
designs, never copied art.

**Read [REFERENCES.md](REFERENCES.md) first** - the arcane mods we learn from and *the Occultech look* (dark vessel,
living light; chromatic ramps; glowing inlay; the twinkle; hard facets; everything magical moves).

## Rules
0. **Bold beats literal.** A striking, simple shape wins over an accurate symbol (the Hollow Sigil's bold star was
   preferred to a "proper" pentacle).
1. **Silhouette first.** Every icon has a shape you can recognise filled solid black. A flask is not enough - the Spirit
   Essence's flask has a ghost escaping it.
2. **Readable at 1x** (16 px in an inventory slot). Details that blur into a blob at 1x are cut or simplified - a
   pentagram drawn in lines fills in at 16 px, so the star goes in the silhouette instead.
3. **Volume from one light.** Light comes from the top-left, slightly in front. Shapes are shaded from their real form
   (sphere, cylinder, bevelled plate) with 3-5 steps of a ramp, never a flat fill or a "pillow" (shading toward the
   centre).
4. **Hue-shifted ramps.** Shadows lean blue/violet, highlights lean warm. Ramps live in `tools/art/palettes.py`.
5. **Coloured outlines.** Outlines use the object's own darkest tones - lighter on the lit top-left side, darkest on the
   shadow side. Never pure black. Outlines only go on empty pixels; a part on top of another separates itself by its own
   tone, not by drawing a line across it.
6. **One accent per item.** A saturated accent (spirit cyan, crimson core, ember orange) marks what's magical about it.
7. **Tier families** so tier reads at a glance:
   | Tier | Family | Accent |
   |---|---|---|
   | 0 Initiate | chalk, bone, candle wax, twine, iron | ember |
   | 1 Bound | violet, smoky glass, silver | spirit cyan |
   | 2 Abyssal | deep teal, prismarine | sea glow |
   | 3 Hollow | sculk black-teal, old bone | hollow cyan, crimson |
8. **Symmetry where it belongs.** Sigils, glyphs and runes are exactly symmetric (checked by the toolkit); objects are
   not. Shading follows the light, so only the silhouette is mirrored.
9. **No flat shortcuts.** Every asset - sigils and decals included - gets ramps, light and volume. Don't make art
   grayscale "so the game can tint it"; draw a coloured version per tier instead (Session B round 1 was rejected for this).
10. **Light sprites are emissive.** Particles (flames, sparkles, motes) are coloured by heat, not by the top-left light,
    have no dark outline, little glow, and are animated (flicker, life cycle) rather than a single static frame.
11. **Magic moves and twinkles.** Magical items get an animated version (glint sweep, twinkles taking turns) and carry
    the twinkle motif clear of their outline. Materials stay dark and calm so the magic is what you notice.
12. **Books look like Minecraft books.** Every book icon uses the vanilla book's pose and silhouette (`BookFrame` in
    `session_c.py`); only the cover, fittings and emblem change. Held books also get a 3D model (Session G).

## Toolkit (`tools/art/`)
- `palettes.py` - ramps and tier families, the light direction.
- `pixelkit.py` - shapes with surface normals (sphere, capsule, box, bevelled polygon, ring, tubes for line art, flat
  gem facets, tilted ellipse ring), ramp shading, selective outlines, glow, the twinkle, symmetry check.
- `glyphkit.py` - flat glyphs (runes, paw print): supersampled strokes, outline and glow.
- `review.py` - review sheets: `sheet` (16 px icons in inventory slots, dark/light, silhouette, values), `big_sheet`
  (large assets, also on a stone floor), `gif` (animated previews).
- `session_*.py` - each session's assets (`session_c.py` = tier-0 icons, `session_d.py` = tier-1 icons); outputs and review sheets go to `docs/art/session-*/`.

## Self-critique checklist (every asset, every iteration)
- [ ] Silhouette unique and recognisable?
- [ ] Readable at 1x in a slot?
- [ ] Tier palette, one accent?
- [ ] Light from the top-left, real volume, no pillow shading?
- [ ] Outlines in the object's own tones, not across other parts?
- [ ] Values: does it still read in grayscale?
- [ ] Symmetric if it's a sigil/glyph?
- [ ] Does it look like a *finished* texture next to Session A's icons (not a placeholder)?
- [ ] Particles: animated, emissive colours, readable at 1x in every frame?
