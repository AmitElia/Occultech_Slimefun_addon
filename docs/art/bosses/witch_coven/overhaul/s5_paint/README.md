# Witch Coven redesign, session 5: texture painting

This paints session 4's layout ([../s4_uv](../s4_uv/README.md)): one shared 256 x 256 atlas for the three sisters, at
one texel per unit. Each ramp is a range of shades of one colour, darkest to lightest. Every ramp is hue-shifted:
shadows lean cool or violet, lights lean warm. Session 4's flat colour is one shade of each ramp. Detail comes in
clusters (no single-pixel speckle), and there is no painted light direction: ambient occlusion is baked from the real
geometry. Shared body islands take their occlusion from the body alone, so one sister's ropes or pot never print on
another's robe.

![The cauldron witch](cauldron/sheet.png)
![The bottle witch](bottles/sheet.png)
![The pot witch](pot/sheet.png)

**Vanilla's witch, aged:**
- **Robe:** purple with deep folds, and vanilla's green stripe down its front.
- **Hem:** a cut-out plane: torn teeth along its lower edge and a few moth holes, so it reads as rags as she hovers.
- **Coat:** a brown coat with grime, worn top edges, its front opening, and a stitched patch.
- **Sleeves and cuffs:** sleeves creased down their length, and dark cuffs fraying at the end.
- **Face:**
  - pale skin with forehead wrinkles under the hat, crow's feet and sagging cheeks;
  - age spots;
  - grey hair hanging from under the hat at the back and sides;
  - bushy grey brows;
  - purple eyes with a dark pupil and a catch-light;
  - the brown mole.
- **Hat:** vanilla's near-black felt, with a lit brim edge and the green band.

**The vessels and kit:**
- **Iron:** vanilla's cauldron greys, with a darker border round each panel, rust spots, soot low down and a bright lip.
- **Rope:** twisted.
- **Strap:** leather, stitched along its edges.
- **Bottles:** glass with a highlight down one side, and cork stoppers.

## The brew is painted neutral

Every sister takes every role, so the brew is painted in neutral greys, carrying only its shading:
- the brew's soft blotches;
- the foam;
- the drips;
- the rising steam puffs;
- the bottles' liquid;
- the cauldron witch's cast.

In the fight, BetterModel tints those bones the role colour. Its per-bone tint (`TrackerUpdateAction.tint(rgb)`
applied through a bone filter, which is also the MythicMobs `tint` mechanic's `part` filter) multiplies the texture
by the colour. Checked in BetterModel 3.5.0.

**One rig change made this work:** the bottle witch's liquid shared a bone with its glass, cork and strap, which a
tint would have coloured too. It now has glow bones of its own: `glow_brew` on the belt and `glow_brew_held` in her
sleeve. The coven now draws 51 displays (15, 22, 14).

The renders and the in-game review rigs show each sister with her brew already tinted: green, purple and red. The
shipped model will carry the neutral atlas ([occultech_coven.png](occultech_coven.png)), and session 6 wires the tint.

**Fixed on the way:**
- The grey hair started on the front of the head's sides: each side face's texture runs the other way.
- Dark brows read as a moustache, so they became grey.
- The brew's first pattern looked like a circuit board, and became soft blotches.

## In game

The review rigs on your server (`occultech_coven_cauldron_rig`, `_bottles_rig`, `_pot_rig`) carry this paint. On
the second test server they loaded with the shipped models and no warnings.

```
/bm reload
/bm test occultech_coven_cauldron_rig idle
```

Regenerate with `python tools/art/bosses/coven_s5.py`. It also copies the review rigs to your server.

Next, session 6:
- wire the role tint (and check it doesn't fight BetterModel's red damage flash);
- phase and damage variants;
- readability at night and under the hit tint.
