# The Night Matriarch redesign, session 1: the full blockout

The user skipped the face study (2026-10-12) and asked for these changes to take 2 of the Phantom Queen:
Take 1 of the blockout was reviewed too: the wings looked better; the crown looked worse; the tendrils swept
forward (a sign error) and should sweep back like an axolotl's gills; the face should be more menacing, with no mouth
and more rot. This page shows take 2.

1. the sculk is mostly texture;
2. the tendrils round her head look like the warden's horns, smaller and many, like feathers round a bird's face;
3. the bones on her head stand in several rows and arch backwards;
4. a less scary face, close to vanilla's phantom;
5. the torn wings are texture, not missing blocks.

![The full blockout](blockout.png)

- **Size:** vanilla's phantom model at 4.5x, about 12 blocks across the wings and 7.5 long, 133 cubes. Her right side
  keeps its hide; her left flank is rotted open to the ribs. In the texture, half her head becomes bare skull.
- **Sculk:** painted in session 5. Only three small sensor tendrils with glowing tips stay modelled, on her back.
- **Face** (take 2 of the blockout, after the user's notes: more menacing, no mouth, more rotted):
  - the phantom's head, with hide on her right and a sunken bare skull on her left, torn hide hanging over the split;
  - a heavy brow pressed down in a V over the phantom's green eye, slanting in;
  - on the skull side, a deep empty socket under a bare brow ridge, a sculk light far inside, and a bare cheekbone.
  More rot comes in the texture.
- **The gills** (the user: sweep back, like dragon feathers or an axolotl's gills, smaller): three sculk fronds a side
  from the back of her head, fanned up, out and down, and swept back.
  - **Vanilla reference:** the axolotl's gills (`AdultAxolotlModel`) and the warden's horns (`WardenModel`). Both are
    flat zero-thickness planes, with the frond's shape cut out of the texture.
  - **Here:** each frond will be one such plane. The blockout draws its cut-out as a glowing stalk with filaments
    along both edges.
- **The crown** (the user: the first rows looked a lot worse): fewer, bigger bones, each tapering in segments that
  bend further back one by one:
  - a band of five short jagged shards along her brow;
  - four horns behind them;
  - two long horns arching back over her head;
  - the outer ones lean out.
- **The wings:** take 2's torn wings, kept at the user's request.
  - **Shape:** a ragged trailing edge, made of strips of uneven length and torn differently on each side.
  - **Bones:** a bone spar along each leading edge, and finger bones fanning across.
  - **What changed:** take 2's holes and missing strips are now whole membrane, painted as cut-outs in the texture
    (like the chains on The Unbound).
- **The owl's tail:** five broad rounded feathers fanned behind a short tail with bare vertebrae.

The crown, ruff and tail are turned in Blockbench's free steps (22.5 or 45 degrees). The finger bones are at odd
angles for now; session 2 snaps them.

Model: `occultech_night_matriarch_blockout.bbmodel` (the gliding pose). Regenerate with
`python tools/art/bosses/matriarch_s1.py`.
