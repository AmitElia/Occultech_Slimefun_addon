# Heartwood Horror, session 4: UV and material zones

Script: `tools/art/bosses/heartwood_s4.py <client folder> [--server]`, run after session 3's rig.

What's here:
- **Sheet:** [sheet.png](sheet.png), in colour and in grey, in the stalk pose.
- **Atlas:** [occultech_heartwood_horror_rig.png](occultech_heartwood_horror_rig.png) and its grey copy.
- **Textured review rig:** `occultech_heartwood_horror_rig.bbmodel`. It's also in `run/plugins/BetterModel/models`
  for the in-game check below.

## The atlas

- **Size and density:** 512 x 512, one texel per model unit. 1763 islands for 1763 visible faces, 55 buried faces left
  out, 67% fill.
- **Clean alpha:** no half-clear texels. Every texel is fully solid or fully clear.

## Vanilla pixels, at 1x like everything else

- **The sleeper** wears the real creaking skin (`creaking.png`):
  - head, crown and body on their own vanilla UVs;
  - its folded limbs take the arm and leg strips, turned to lie along them;
  - its leaves take the leaf panel.
- **The lantern** is now exactly one block, so the awake creaking heart maps 1:1 (`creaking_heart_awake` on the sides,
  `_top_awake` on the top and bottom).
  - Over it, a glow copy of the block a quarter texel bigger carries only the heart's orange cracks, full-bright.
  - The bark between the cracks stays lit by the world, so at night the lantern burns from inside its own wood.
  - This replaced the blockout's flat eye bar.
- **The moss strands** carry `pale_hanging_moss` strips with the tip texture at the bottom. Their clear texels stay
  clear.

## The resin

**Superseded in session 5:** the dither read as copper, so the shell is now really translucent over an opaque
amber chamber ([s5_paint](../s5_paint/README.md)). What session 4 did:

Half-clear texels flicker in game, so the shell is dithered, mixing fully solid and fully clear texels:

- **Each face is graded:** about 90% solid at its edges, opening to about 30% in the middle, a window onto the sleeper.
  The window's solid texels are a lighter amber.
- **The shell's inner chamfer layer** keeps only a 2-texel solid rim. With both layers dithered evenly, the shell read
  as solid. The first pass, an even 50% checker, read as a grate.
- **In these renders the inside of the shell looks dark** because Blender casts shadows. Minecraft doesn't, so in game
  the sleeper is lit like every other face. Session 5 can still warm its skin toward amber so it seems lit from within.

## Zones

Tier 3, in the pale garden's own colours: the bark is pale oak, and the glow is the creaking heart's orange.

| Zone | Colour | Value (L*) | Where |
|---|---|---|---|
| bark / bark_dark | pale oak bark / its dark | 34 / 22 | trunk, arms, legs / knots, brow, hump cap, the lantern's root |
| root | pale root | 51 | fingers, toes, the lantern's tail |
| wood | pale oak heartwood | 77 | the broken branches' ends |
| moss | pale moss | 64 | the hanging strands (vanilla moss strips on them) |
| resin / resin_dark | resin amber / dark amber | 56 / 31 | the shell / its rims |
| heart_frame | near-black wood | 17 | the lantern's cage |
| petal / bud / bloom | white / grey / orange | 89 / 61 / 71 | eyeblossoms: open petals, closed buds, glowing eyes |
| sleeper, heart | vanilla pixels | 37, 43 (means) | the sleeper, the lantern |

**Value check:** every pair of neighbouring zones is at least 12 L* apart. In grey it still reads: dark bark, white
blooms, the grey lantern in its black cage, and the resin's window.

## In game (first pixel-size check)

The textured rig is in your server's models folder:

```
/bm reload
/bm test occultech_heartwood_horror_rig idle
```

Check:
- the pixel size against vanilla blocks next to it (it should match: 16 texels a block);
- the resin window at fighting distance (does the sleeper show?);
- the lantern's glow at night.

Session 5 paints over these zones: bark ridges and form shading, the resin's bubbles and streaks, the sleeper lit
through amber, moss on the bark itself, and the cage's wear.
