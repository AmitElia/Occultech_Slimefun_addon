# Tempest, session 4: UV and material zones

Script: `tools/art/bosses/tempest_s4.py <client assets folder>`. Output: [sheet.png](sheet.png) (the idle pose, colour and grey),
the atlas `occultech_tempest_rig.png` (+ `_grey`), the review model `occultech_tempest_rig.bbmodel` (copied to `run/` and
`run-mythic-b`, so `/bm test occultech_tempest_rig idle` now shows these flat zones), [uv_report.json](uv_report.json).

## Atlas

- **512 x 512**, one texel per model unit everywhere except the vanilla skin.
- 1,716 faces drawn as 1,704 islands (the three rods share theirs), 61% fill. No buried faces.
- 0 half-clear texels.
- **Vanilla breeze skin** (`breeze.png`, 26.2 client) on the head, the visor band and the three rods. It's upscaled by whole
  pixels: 4 per texel on the head and band, 3 on the rods. That's the same deliberate exception as the Blaze Choir's
  blaze heads. Vanilla's few clear skin texels are made solid.

## Zones (value = CIE L*)

| Zone | Colour | L* | Where |
|---|---|---|---|
| stone | pale carved stone (196,188,168) | 76 | the seal's tiles |
| stone_dark | (106,100,92) | 43 | the seal's raised rim |
| stone_aged | weathered dark stone (72,68,66) | 29 | the circlet; it must part from the breeze skin it sits on |
| steel | dark steel (78,82,89) | 35 | the heavy core's eight blocks |
| wind / wind_dark | lavender-white (222,232,250) / blue-violet (128,140,196) | 92 / 59 | alternating bands and arms |
| core_glow / glyph | sea teal (86,232,208) / (120,250,226) | 84 / 91 | the heart, the glyphs: full-bright |
| eye | white | 97 | the brows on the band: full-bright |

The value check passes: no two touching zones are within 12 L* of each other. The first palette failed twice: the seal
stone against the wind, and the circlet against the breeze skin. Hence the darker weathered circlet and the brighter wind.

## Found while mapping the vanilla face

Vanilla's breeze face is: **white V strokes on the band are its brows; its eyes are two yellow texels just under the
band**, each wrapping a corner of the head (one texel on the front, one on the side). Both sit on the emissive eyes layer.
The skin already shows the yellow eyes. Session 5 adds small full-bright cubes for them so they glow like vanilla's, next
to the white brows that already glow.
