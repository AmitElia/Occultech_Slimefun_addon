# Drowned Elder, session 2: design lock

Script: `tools/art/bosses/drowned_s2.py`. Outputs: [design.png](design.png) (idle: three-quarter, side and top silhouettes,
the head close, the hitboxes), [poses.png](poses.png) (six key moments, four views each),
`design/occultech_drowned_elder_blockout.bbmodel`, [parts.md](parts.md), [stats.json](stats.json).

Session 1 (approved 2026-11-17): the Abyssal Serpent, body plan B (the Wyrm), head H3 (the Spike Hood), segment S2 (the
Shingle): [s1_blockout](../s1_blockout/README.md).

## The rig, `occultech_drowned_elder`

120 cubes on whole texels, 48 bones (43 carry geometry). Laid out straight in the bind pose it is 20.7 blocks long; swimming
in curves it spans about 17.5.

```
base (the head's centre: the carrier sits here; the whole body turns and moves with it)
  hi_head (the elder head, its plates and side/front spikes) > glow_eye, hood0..hood8 (the fan's spikes), web0..web7
  seg0 > seg1 > ... > seg9 > tail0 > tail1 > fluke     (the body: a chain, each joint at a segment's front)
    seg0 > fin_right, fin_left
    seg2, seg4, seg6 > gill<i>_right, gill<i>_left (the side shingles that swing open), glow_eye<i> (the beam eyes)
  ob_head (base), ob_body0 (seg2), ob_body1 (seg5), ob_body2 (seg8)   BetterModel hitboxes
```

- **A chain, not a pile of parts.** Each segment is the child of the one in front, so turning one joint carries the
  whole body behind it. Every pose is just joint rotations plus one move of `base`: session 7's clips need nothing else.
- **Poses come from curves.** Each pose is a smooth curve (the same curves as the blockout); every joint takes the turn
  of the curve at its segment, so the body follows it without kinks. The same tool will key session 7's swimming waves.
- **The hood** is nine spike bones and eight fin webs. Each web bone is turned into its own plane in the bind pose, so
  widening it as the hood flares is one scale axis (the webs stretch between the spikes instead of tearing).
- **The beam eyes** sit under the side shingles of segments 3, 5 and 7 and are always lit: shut, the shingle covers
  them; open (`gill<i>_*` turned out 48 degrees on its hinge), they show. `glow_eye<i>` is kept apart so session 6 can
  tint each eye on its own (each beam has its own target).
- **Hitboxes:** the head (3 x 3 x 3.4 blocks) and three on the body (segments 3, 6 and 9, from 1.9 down to 1.25
  blocks), each a child of its segment so it follows the swimming body. The hood, fins, spikes and fluke are not
  covered, so nothing decorative becomes a target. Several hitboxes on one model is new for us (every boss so far had
  one); session 3 checks that BetterModel builds them and session 8 that each hit lands once.
- **Tags:** only `hi_head`, the `glow_` bones and the `ob_` hitboxes carry a BetterModel tag; sides are spelled out
  (`_right`, `_left`).
- 9 faces were nudged apart so no two share a plane (no flicker).

## Key moments ([poses.png](poses.png))

| Pose | Fight moment (DrownedElder.java) | What it shows |
|---|---|---|
| idle | swimming between attacks | humps, hood folded back along the neck |
| aim | the multi-beam tell (0.5 s lock) | curled to face the players, the three gill shingles open, the eyes showing |
| stare | the Mining Fatigue pulse | coiled in a ring overhead, the head hanging down out of it, hood flared, eye lit |
| dive | the Tidal Surge goes in | head first into the floor, hood tucked flat, body arched over the arena |
| emerge | it bursts back out; the waves start | the head and neck rear about 9 blocks out of the floor, the hood half open, the rest still under it |
| death | death | coiled on the floor, the hood limp, every eye dark |

Every pose keeps the head clear of the floor except the dive (half a block in) and the emerge (the body goes into the
floor; parts below the floor are not drawn).

## Open for later sessions

- **The head is still vanilla's plain box.** It was approved this way; if you want more menace in the face (a heavier
  brow, a deeper-set eye, a jaw line), it's cheapest to add now, before the rig is locked in session 3.
- **Display cost (M6):** the shingles tilt 7 and 14 degrees and the spikes point along diagonals; session 3 counts the
  displays. Per your rule, detail isn't cut for draw cost now; that's the M6 pass for all bosses.
- **Carrier and movement (session 8):** the carrier sits at the head; the body is posed by clips plus a
  follow-the-head trail worked out in code each tick.
