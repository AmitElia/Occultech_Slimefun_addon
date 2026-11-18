# Drowned Elder (the Wyrm), session 1 step 3: the full blockout

Script: `tools/art/bosses/drowned_blockout.py` (builds on `drowned_serpent.py` and `drowned_study.py`). Plan:
[../plan.md](../plan.md). Picked so far: body plan B, the Wyrm ([s1_serpent](../s1_serpent/README.md)); head H3, the Spike
Hood, and segment S2, the Shingle ([s1_study](../s1_study/README.md)).

Sheet: [blockout.png](blockout.png): four poses, each from a three-quarter view, side and top silhouettes, a player's
eye, and close from the right. Colours are blockout zones only (teal = a glowing eye).

## The model

- **Head:** vanilla's Elder Guardian at 3x (2.25 blocks across): the box body, its four plates, the side and front
  spikes, the eye on its face; behind it a fan of nine long spikes webbed with fin (the hood).
- **Body:** ten Shingle segments tapering from 28 to 12 units across. Each has four plates tilted back over the next
  segment (top 14 degrees, sides 7, bottom flush) and one back spike, tallest behind the head (44 units) and shortening
  towards the tail. Segments 3, 5 and 7 carry the beam eyes under their side shingles.
- **Pectoral fins** on the first segment, swept back and down; the forked **fluke** at the tail.
- About 17.5 blocks long; it hovers 1.2 blocks over the floor. 120 cubes.

## The poses

| Pose | Fight moment | What it shows |
|---|---|---|
| idle | between attacks | swimming in humps, the hood folded back along the neck |
| aim | the multi-beam tell (0.5 s lock) | it curls to face the players; three segments swing their side shingles open like gill covers and the eyes under them light up |
| stare | the Mining Fatigue pulse | it coils into a ring overhead, the head hanging down out of the ring at the players, the hood flared into a spiked halo, the eye lit |
| surge | the Tidal Surge | it dives head first into the floor, the hood tucked flat along the neck like a sheath, the body arched over the arena (the waves start where it went in) |

## Self-review fixes before showing

- The stare's coil first sat behind the head; the ring now runs over the head, which hangs down from it.
- The opened eyes were too small to see from far views; the close view from the right shows them.
- In the dive the folded hood stood up like a bundle of sticks; it now tucks flat for the dive.

## Still open (session 2, design lock)

- The head is still vanilla's plain box: the face (brow, jaw line, eye size) can carry more menace without losing the
  vanilla tie.
- Final spike lengths, the fins' shape, the hitboxes along a long body and how BetterModel drives ten segment bones.
