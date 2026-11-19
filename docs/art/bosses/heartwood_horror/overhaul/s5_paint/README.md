# Heartwood Horror, session 5: texture painting

Script: `tools/art/bosses/heartwood_s5.py <client folder> [--server]`, painted over session 4's islands (512 x 512).

- **Sheet:** [sheet.png](sheet.png): hero, about 10 blocks away, a player's eye, the chest, an arm close up, the back.
- **The womb alone:** [womb.png](womb.png), from below and from the front.
- **In game:** the painted review rig is in `run/plugins/BetterModel/models`; view it with
  `/bm test occultech_heartwood_horror_rig idle`.

## How it's painted

**Shading rules:**
- Ramps run from a cool violet dark, through each zone's colour, to a warm light.
- Form comes from the real geometry: faces looking up are lighter, undersides darker, and ambient occlusion is baked
  into the creases.
- Every texel is fully clear or fully opaque.

**Per material:**
- **Bark (pale oak):** furrows run along each limb, broken into lengths, with ridges between them. The knots are ringed.
- **Moss:** pale moss sits in patches on the faces that look up, with a thin fringe of short drips down some sides.
- **Roots** (fingers, toes, the lantern's tail): smoother, with fine streaks, a little lighter than the bark.
- **Broken branch ends:** pale heartwood rings inside a ring of bark.
- **The lantern:**
  - The cage is near-black wood, lit along its top edges.
  - The heart is vanilla's awake creaking heart, untouched. Its orange cracks glow.
  - It now hangs on a dark bark root.
- **The resin (review 1: "why does it look like copper?"):** session 4's dither, a checker of solid and clear
  texels, read as perforated copper. It is now **really translucent**, with half-clear texels:
  - **The shell:** clear honey amber, about 70/255 opaque in the middle of each face and 180 at the edges, with a few
    solid bubbles.
  - **The chamber:** opaque plates (`chamber_back/left/right/top`, added to the rig) just inside the shell's back,
    sides and top, in bright honey amber. The dark sleeper shows against them like a fossil in amber. The front and
    the bottom (what you look into from below) are the windows.
  - **Why this is safe, unlike the Warden's glass:** the 26.2 client draws translucent item models with
    `item_translucent`, which sorts faces back to front before drawing (checked in the client jar). The sleeper sits
    in the womb's own bone, and the chamber stops anything from another bone showing through the shell. **This still
    has to be checked in a real client** (see below).
- **The sleeper:** vanilla's creaking skin, barely warmed, so it stays dark against the bright amber.
- **Eyeblossoms:** white petals shaded towards the flower's centre, grey buds darker at their foot, and orange eyes
  brightest at the centre.
- **Hanging moss strands:** vanilla's pale hanging moss, untouched.

## Self-review

- **The first pass was too busy.** Moss in bright patches everywhere plus heavy mottling turned the bark into
  camouflage up close, the same problem the Headsman's first paint had. The fingers in a pale root colour read as
  planks. Fixed:
  - moss covers about a quarter as much and sits a step darker;
  - mottling is lighter and in bigger clusters;
  - the roots are darker.
- **At about 10 blocks:** a dark, gnarled tree with the lantern and the eyeblossoms as the only bright spots. The
  resin reads as one amber shape.
- **In the full renders the sleeper hides in shadow:** Blender lets the hunched body cast a shadow into the womb.
  Minecraft doesn't cast shadows, so [womb.png](womb.png) (the womb alone) is closer to what the game shows.

## To check in game

The painted rig is in your server's models folder:

```
/bm reload
/bm test occultech_heartwood_horror_rig idle
```

Look at the womb from the front and from below while walking round it:
- the sleeper should show through the amber;
- nothing should flicker or vanish behind the resin, in the poses too (`swipe`, `lunge`).

If anything flickers, the fallback is the dither (`RESIN_MID_A`/`RESIN_EDGE_A` in `heartwood_s4.py` back to solid and
clear texels).
