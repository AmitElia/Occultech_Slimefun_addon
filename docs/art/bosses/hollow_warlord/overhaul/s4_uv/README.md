# Hollow Warlord, the Headsman: session 4 (UV and material zones)

Script: `tools/art/bosses/headsman_s4.py <client folder> [--server]`. Sheet: [sheet.png](sheet.png) (colour and grey,
in the idle pose). Atlas: [occultech_hollow_warlord_rig.png](occultech_hollow_warlord_rig.png) and its grey copy;
textured review rig: `occultech_hollow_warlord_rig.bbmodel` (`--server` copies it to run/ models).

- **Atlas:** 512 x 256 at one texel per model unit; 753 islands for 771 visible faces (39 buried faces left out), 61%
  fill, no half-clear texels.
- **Skulls:** his skull and the three taken skulls carry the real wither skeleton head from the 26.2 client at 2x
  (8 texels over 16 units), all four on one set of islands. Over each pair of eyes sits a glow cube in soul cyan.
- **Zones** (one grey family with the wither skin, soul cyan the only accent):

| Zone | Colour | Value (L*) | Where |
|---|---|---|---|
| bone / bone_dark | vanilla-dark wither bone | 19 / 12 | ribs, spine, limbs, neck, the taken skulls' vertebrae; joints |
| plate / plate_lit | worn grey iron | 31 / 44 | breastplate, pauldrons, gauntlets, greaves, the hat, the belt; bevelled edges |
| grip | black leather | 11 | the sword's wrap |
| cloth / cloth_dark | soot black | 6 | the tabard |
| blade / guard | steel / iron | 52 / 31 | the sword |
| socket | near black | 4 | the shadow under the brim |
| soul, brand | soul cyan, glowing | - | eyes; the brand's glyphs |

Changed after session 5's review: every grey now comes from the wither skin's own neutral greys (the first zones had
lavender blackstone, paler bone, a red tabard and brown leather).

- **Value check:** every pair of neighbouring zones is at least 12 L* apart, measured against the skull skin's real
  mean value (10). In grey he still reads: dark skull under a darker hat, pale bone between dark plates.

Session 5 paints over these zones (form shading, wear, edges, the brand rune, the soul fire's shape).
