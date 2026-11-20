# Dread Riders, session 2: design lock

Made by `python tools/art/bosses/dread_s2.py` (run from the repository root; `vanguard` or `outrider` for one pair).
It builds on the approved session 1 take 2 (`dread_concepts.py take2`, [s1_take2](../s1_take2/README.md)).

Key poses: [poses_vanguard.png](poses_vanguard.png), [poses_outrider.png](poses_outrider.png). Bind pose, front, back
and hitbox: [design_vanguard.png](design_vanguard.png), [design_outrider.png](design_outrider.png). Bone by bone:
[vanguard/parts.md](vanguard/parts.md), [outrider/parts.md](outrider/parts.md). Sizes: [stats.json](stats.json).
Rigs (Blockbench, flat colours): `design/`.

## Four models

The fight seats each rider on its own horse (two entities each), so each pair is a mount and a rider, like the
Tidebreaker.

| Model | Worn by | Cubes | Bones | Size (blocks) | Hitbox |
|---|---|---|---|---|---|
| `occultech_dread_vanguard_mount` | the zombie horse (can't be hurt) | 288 | 20 | 3.12 x 8.23 x 7.16 (with the banner) | none |
| `occultech_dread_vanguard` | the zombie lancer | 66 | 14 | 3.43 x 6.63 x 5.31 (with the lance) | 2.5 x 7.44 x 2.5 |
| `occultech_dread_outrider_mount` | the skeleton horse (can't be hurt) | 165 | 18 | 2.81 x 5.85 x 7.33 | none |
| `occultech_dread_outrider` | the skeleton archer | 108 | 18 | 2.75 x 5.68 x 3.05 | 2.5 x 8.19 x 2.5 |

**Mount bones:** `base` (pivot in the barrel; it tilts for the rear) holds the body. Off it hang `neck` > `head` >
`glow_eyes` (plus `jaw` on the skeleton), four legs of three bones each (`leg_<fl|fr|hl|hr>` > `_lower` > `_hoof`, with
pivots at the elbow or stifle, the knee or hock, and the fetlock), and `tail`. The charger also has `banner` >
`banner_cloth` and `glow_sigil` (the boss on its chest).
**Rider bones:** `rider` (pivot at the hip) > `thigh_*` > `shin_*`, and `torso` > `hi_head` (the head with its helmet),
`arm_*` > `forearm_*` > `hand_*`. The lance is on `hand_right`; the bow is on `hand_left`, with `string_upper` and
`string_lower` pivoting at its tips. The nocked arrow is on `hand_right` with a cyan `glow_arrow` tip (the storm
snipe's tell), hidden until a draw.

## Decisions

- **The bind pose is the rest pose:** the lance carried at an angle, the reins held, the bow lowered. That is what the
  models show between clips. Key poses are bone rotations from it, plus a lift of the whole model for the gallop.
- **A rider's model has its origin at the seat** (the top of the saddle), where the passenger sits in game. The seat is
  4.4 blocks up on the charger and 4.5 on the skeleton horse.
- **The rider's hitbox runs from the ground to the top of the helm, 2.5 blocks square, round the saddle.** The horses
  can't be hurt and the riders sit about 4.5 blocks up, out of melee reach. With this hitbox, a swing at the horse's
  body hits its rider.
- **Cube sizes are whole texels.** The face patterns (the vanilla eyes, nose and mouth; the skull's sockets and
  nostril) are texture: they appear in the previews but not in the .bbmodel files.
- **The charger's banner cloth swings back as one bone** in the gallop, and the tail lifts.
- **The bowstring is two bones** that turn and stretch from the tips to the drawing hand.

## Key poses

| Vanguard | Outrider |
|---|---|
| idle | idle |
| the charge: a gallop, lance couched across the neck, banner streaming | circling: a gallop, leaning in, bow held low |
| the charge's tell: the horse rears, lance raised | the snipe: a forehoof raised, the bow drawn to the cheek, the cyan arrow nocked |
| stunned (a charge cut short): head to the ground, the rider slumped, the lance trailing | arrow rain: leaning back, aiming high |
| the lance sweep (melee): the torso turned, the lance swung out to the right | the loose: the string slack, the hand flung back |
| the spear throw (enraged): the lance raised over the shoulder | |

Every pose stays above the floor (checked per pose: the lowest point is at 0 or above).

## For later sessions

- **Session 3:** the lance (about 6 blocks) and the banner pole must be split into pieces, because an item model stops
  at 48 units. Odd cube angles cost display entities: the chamfered horse bodies and the cones are many angled cubes
  (the M6 pass for all bosses covers draw cost).
- **Session 4:** the rider heads are 16 units, so the vanilla 8-texel skins sit at exactly 2 pixels per texel.
- **Session 8:**
  - The riders must line up with the saddle at the game's real passenger seat, and follow the mount's tilt in the rear.
  - The fight's horse scales (0.85 and 1.2 today) give way to these models.
  - The hitbox has to pass hits on the horse's body to its rider.
