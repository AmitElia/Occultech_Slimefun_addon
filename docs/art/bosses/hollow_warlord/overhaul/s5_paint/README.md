# Hollow Warlord, the Headsman: session 5 (texture painting)

Script: `tools/art/bosses/headsman_s5.py <client folder> [--server]`. Sheet: [sheet.png](sheet.png) (hero, about 10
blocks away, a player's eye, the face, the sword, the back); the taken skulls close up: [skulls.png](skulls.png).
The painted review rig is in `run/plugins/BetterModel/models` (`/bm test occultech_hollow_warlord_rig idle`).

## Review 1 (user, 2026-11-18)

- No cyan glow on the floating heads' "spine pieces" (the soul-fire blocks): they are now a **severed vertebra** in
  plain bone under each skull, no glow.
- **No red or brown:** the tabard is soot black, the grip black leather, the belt an iron girdle, the brand soul cyan.
- **Battered armour:** grime pooling low on each piece, scuffed edges, scratches with a shadow under them, dents,
  chipped corners, the odd crack. A first pass was so busy it read as granite camo; it was calmed (a narrower ramp,
  fewer and fainter marks).
- **One grey family:** every grey now comes from the wither skin's own neutral greys (with its faint teal in the
  lights). The armour was lavender blackstone and the bones a paler grey; neither matched the black skull. The bones
  are now vanilla-dark wither bone, the plate a worn mid-grey iron, so the skull, bones and armour read as one creature.

## How it's painted

Over session 4's islands (512 x 256), ambient occlusion from the real geometry, detail in 2x2-3x3 clusters, every
texel fully clear or fully opaque:
- **Plate:** worn grey iron, battered as above.
- **Bone:** dark wither bone, lit along the top, darker towards the joints, hairline cracks.
- **Tabard:** soot-black cloth in folds, ragged tatters and moth holes cut out.
- **Blade:** smooth steel, a bright honed edge with nicks, a darker fuller, one highlight band; the brand's glyphs in
  soul cyan.
- **Skulls:** vanilla's wither skull, untouched; the eyes are the only glow besides the brand.
