# Drowned Elder, session 7: animation (take 2)

Scripts: `tools/art/bosses/drowned_s7.py <client assets folder>` (after `drowned_s6.py`) builds the clips;
`tools/art/bosses/drowned_gif.py [clip ...] <client assets folder>` renders the lit GIFs. Output:

- **[lit/](lit/)**: lit, fully textured GIFs of the real painted model, 10 fps, with the eyes tinted the way the fight
  will tint them: `drowned_idle`, `drowned_spawn`, `drowned_aim`, `drowned_stare`, `drowned_surge` (dive + emerge back
  to back), `drowned_death`.
- [keyframes.png](keyframes.png) and `gifs/`: flat-colour previews of every clip; [clips.json](clips.json).
- The rig with its clips, `occultech_drowned_elder_rig.bbmodel`, in `run/` and `run-mythic-b`:
  `/bm test occultech_drowned_elder_rig <clip>`.

## Why take 2

Take 1 blended a few whole poses in joint space. The body moved all at once like a puppet; in-betweens folded through
themselves (the death went through the floor); the dive and emerge didn't go through the floor, they just swapped
poses. Take 2 is authored as motion:

- **Shapes, not joint angles.** The body at any moment is a shape: where the face is, and which way the body runs
  every 8 units down its length. Shapes blend by turning those directions as heading and climb, unwrapped down the body,
  so every in-between is a real, unbroken body of the right length, and a coil winds and unwinds in one sense.
- **Motion travels down the body.** Every change starts at the head and reaches the tail later: the body flows into a
  coil, the head leads and the tail follows through.
- **Path following** through the floor: the head travels a path and every point of the body follows it. In the surge
  the body pours into the floor through one hole and out of a second; in the spawn it spirals up out of the circle.
- **Anticipation, overshoot and settle** on every attack; **secondary motion** while swimming (the hood breathes, the
  fins paddle, the fluke flicks a beat behind the wave).
- **Falls build from the tail**: a falling body hangs from where it lies, so the death's head drops without driving
  the body through the floor.
- **Dense keys** (every 0.05 s, the swim every 0.1 s), each joint kept continuous with the key before it: the roll is
  carried from frame to frame (a head pointing straight up or down no longer flips), and of a joint's two equal angle
  forms the one nearest the last key is used.

## The clips, timed to the fight

| Clip | Length | Contact | What happens | DrownedElder.java |
|---|---|---|---|---|
| idle | 3.2 s loop | | a heading wave runs down the body (the tail swings about 2 blocks each side), a slow rise and dip, hood breathing, fins paddling, fluke flicking, head steady | swimming |
| spawn | 4.0 s once | 2.8 s | the head breaks the floor at once, the body spirals up out of the circle after it, arcs over, rears with the hood flaring and the eye glaring (the roar), settles into the swim | the ritual arrival |
| aim | 2.6 s once | 2.0 s | draws back (0.3 s), throws itself into a wide coiled S facing three ways, the gills snap open past their mark and settle, the hood half open; holds with a slow sway while the beams charge; tenses (hood full) 0.2 s before; fires at 2.0 s with a recoil rippling down the body; swims on | Abyss.Beam: 40-tick charge (white 15 ticks before, locked 5 before) |
| stare | 2.6 s once | 1.0 s | coils overhead head first, the hood flaring into a spiked halo past its mark, the head hanging out of the ring lunges its glare down at 1.0 s; holds, the ring rippling; uncoils | the Mining Fatigue pulse |
| shed | 1.2 s once | 0.5 s | two shudders run down the body, the gills flutter, the hood twitches | the guardians join |
| dive | 1.4 s hold | 1.0 s | rears up and over (hood flaring), hangs at the top, strikes head first into the floor about 9 blocks ahead, the body arching over the hole; holds | the Tidal Surge: the first wave |
| emerge | 2.6 s once | 1.4 s | carries on along the same path: the arch pours into the floor while the head bursts out of a second hole next to the carrier and rises 12 blocks, roars with the hood flared, then lowers into the swim | after the last wave |
| flinch | 0.5 s once | | the head snaps back, a ripple runs down the body, the hood twitches | hit |
| death | 3.4 s hold | | rears, thrashes twice (the head shaking), falls head first, slumps flat, curls into its coil, the tail's last flick; eyes dim | death |

## Checks

| Check | Result |
|---|---|
| Interpolation error (an Euler midpoint against the true halfway turn) | at most 3.4 degrees in any clip (take 1: 20) |
| Largest turn of a joint between two keys | 66 degrees: the tail whipping through the dive's strike (follow-through, on purpose); everything else 50 or less |
| Lowest point | idle 26, aim 32, stare 38, shed 36, flinch 35, death -3 (resting on the floor); spawn, dive and emerge go under the floor on purpose (the floor hides it) |
| Load test, server b (2026-11-18) | the rig with its nine clips loaded clean; BetterModel built all 43 bones; no errors |

Not yet watched in a real client.

## For session 8

- **Beams** fire from the eye of the segment that carries them (that bone's posed position), not from the carrier. The
  aim clip starts with the charge. Tint each eye `lock` 15 ticks before its beam fires.
- **Stare:** start the clip with the head-eye `stare` tint; pulse at 1.0 s.
- **Surge:** play `dive` (it holds), roll the waves from where the head went in (about 9 blocks ahead of the carrier,
  not the carrier itself), play `emerge` after the last wave. During the hold the head is under the floor; the body
  hitboxes in the arch stay hittable.
- **The swim's phase:** an attack clip starts from the swim's first frame. If BetterModel snaps from wherever the swim
  was, the tail jumps up to about 2 blocks; check that in game and, if it shows, start attacks only on the swim's beat.
- **The head bone (`hi_head`)** follows the carrier's look. Check it doesn't fight the clips' head moves (the recoil,
  the lunge, the roar).
- The rig file is 3 MB (dense keys). Fine for a server model; the resource pack doesn't carry animations.
