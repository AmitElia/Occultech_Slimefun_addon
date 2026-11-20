# Dread Riders, session 7: animation

Script: `tools/art/bosses/dread_s7.py <client folder> [clip ...] [--server] [--gifs]`, after session 6.

- **Lit, textured GIFs:** `lit/<pair>_<clip>.gif`, 12 frames a second. Each is the real painted model, tinted the way
  the fight will tint it.
- **Animated review rigs:** the four `occultech_dread_*_rig.bbmodel` files. They are here and in
  `run/plugins/BetterModel/models`. For example:

  ```
  /bm test occultech_dread_vanguard_mount_rig gallop
  /bm test occultech_dread_vanguard_rig gallop
  ```

- **Report:** [report.json](report.json).

## How it's authored

**Gaits come from leg phases.** Each leg runs its own cycle:
- **Stance:** the hoof sweeps back along the floor.
- **Swing:** the knee or hock folds, and the leg carries forward and reaches.

The cycles are offset per gait:
- **The walk** is four-beat: LH, LF, RH, RF a quarter of a cycle apart.
- **The gallop** is the transverse gallop on the right lead: LH, RH, LF, RF, then a moment of suspension.
- **The charge** is the same gallop stretched: a longer reach and a lower neck.

On top of the legs:
- **Grounding:** the body is set on its lowest hoof at every key.
- **Rocking:** the body rocks nose-up on the push and nose-down on the landing, and the neck swings against it.
- **Tail and banner:** they stream and flutter.

**The rider rides the horse.** Rider and horse are two entities, so each gait clip also moves the rider's root along the
saddle's real path: its rise, fall and pitch through the mount's pose.

**Attack clips are rider-only.** The sweep, the throw, the volley and the rain animate only the torso, arms and weapon,
never the root. If BetterModel layers clips, an attack plays over the gallop. If it doesn't, the bob pauses for the
attack. Session 8 has to check this in game.

**Weight and timing:**
- a crouch before the rear, and an overshoot on landing;
- the lance swung back before the sweep;
- the bow held a beat at full draw;
- a snap on the loose.

**Keys:** 24 per gait cycle and every 0.025 s in the other clips.

**Arm continuity:** each arm's turn is carried forward from the previous key, so an arm swinging far from its bind
direction never flips. The first pass flipped the archer's forearm by 180° when its elbow passed the shoulder, and the
nock and loose paths were reshaped to stop that.

## Clips

Each clip has the same name on a pair's mount and rider.

**The Vanguard**

| Clip | Length | Timed to |
|---|---|---|
| idle | 3.0 s loop | breathing, a slow toss of the head, the tail swishing; the lance carried |
| walk | 1.4 s loop | four-beat walk |
| gallop | 0.72 s loop | the ride at 0.3 blocks a tick, the banner streaming |
| charge | 0.5 s loop | the charge (0.8 blocks a tick, 25 ticks); lance couched across the neck |
| rear | 1.0 s hold | the charge's 20-tick warning: a crouch, the rear with the hooves pawing, the drop into the charge at 1.0 s; the rider leans into the neck with the lance high |
| stunned | 2.0 s | the 40-tick stun: the nose down, the forelegs buckle, the head shakes, it gathers itself; the rider slumps, the lance trails |
| sweep | 0.8 s | melee (rider only), contact 0.35 s |
| throw | 1.0 s | the enraged spear (rider only), contact 0.55 s |
| flinch | 0.4 s | the horse tosses its head, the rider recoils |
| spawn | 2.6 s | out of a crouch, the rear, pawing, a stamp down; the lance raised |
| death | 2.6 s hold | a weak rear, then a collapse onto the knees; the rider slumps, the lance falls |

**The Outrider**

| Clip | Length | Timed to |
|---|---|---|
| idle, walk, gallop | as above | the circling at 0.34 blocks a tick; he leans in, the bow held low |
| halt | 0.7 s hold | the rein-in every 10 s: a sliding stop, haunches down, forelegs braced |
| draw | 2.4 s | the aimed snipe (the 40-tick beam): the forehoof paws, nock (0.6 s), full draw (1.0 s), a held trembling aim, the loose at 2.0 s |
| volley | 0.6 s | the volley (rider only), loose 0.35-0.4 s |
| rain | 1.2 s | the arrow rain (rider only): lean back, aim high, loose at 0.45-0.52 s |
| flinch, spawn, death | as above | |

## Checks

| Check | Result |
|---|---|
| Lowest point of any mount in any clip | -0.04 blocks (the hooves sit on the floor) |
| Largest real turn between keys, gaits | 38° (a hoof folding in a 0.03 s step of the charge) |
| Largest real turn between keys, attacks | 45° on a forearm, the lance's swing |
| The loose | 70 to 92° on the right forearm: a deliberate snap |
| Load test on server b | all four animated rigs built clean, no warnings; then taken off b again |

## For session 8

- **Scripted contacts:** the attacks fire on the clip contacts: the snipe at the draw's 2.0 s, the volley at 0.35 s,
  the rain's arrows at 0.45 s, the sweep at 0.35 s, the throw at 0.55 s. The charge starts at the rear's 1.0 s.
- **Arrow and string:** the nocked arrow is a hidden bone. Show it for the draw, volley and rain (part visibility), and
  hide it at the loose.
- **Layering:** check that rider-only attacks layer over the gallop.
- **Mount and rider in step:** start each pair's mount and rider clips on the same tick so the saddle and the rider stay
  together.
- **Re-tint after hits:** re-apply the glow tint 12 ticks after a hit flash.
- **Death:** the horse is removed when its rider dies, so the death clip needs the corpse stand-in (`BossBody.corpse`).
