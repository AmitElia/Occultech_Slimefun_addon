# Heartwood Horror, session 7: animation

Scripts:
- `tools/art/bosses/heartwood_s7.py [--no-gifs] [clip ...] <client folder>`: the motion system, the checks, the
  export and the GIFs.
- `tools/art/bosses/heartwood_clips.py`: the clips themselves.

Output:
- **[lit/](lit/):** lit, fully textured GIFs of every clip, 10 fps, with the glows tinted the way the fight will tint
  them (session 6).
- **The rig with all twelve clips:** `occultech_heartwood_horror_rig.bbmodel`, also in `run/plugins/BetterModel/models`.
  Try one with `/bm test occultech_heartwood_horror_rig <clip>`.
- **[clips.json](clips.json):** every check, per clip.
- **[heartwood_showcase.gif](heartwood_showcase.gif):** the dramatic moves in one take, in full colour (18 s, 640 px,
  11 MB), from one fixed three-quarter camera. It runs: spawn, swipe, slam, the creak into the lunge, the stagger, death.
  Made by `tools/art/bosses/heartwood_showcase.py`.

## How it moves

Authored as motion, not as poses blended in joint space:

- **World-space keys.** Each key says where every hand, foot and the trunk's bend should be. Every key step it's
  solved onto the rig:
  - arms are fitted along a curve through their control points at their real bone lengths;
  - legs land on the floor by two-bone IK.
- **Points near the shoulder ride with the body; hands stay where they're keyed.** So the crutch stays planted while
  the body lurches over it, and the dragging hands slide along the floor behind.
- **An arm that must shorten raises its elbow** (spidery) instead of crumpling at the hand.
- **Anticipation, a fast strike, an overshoot, a slow settle** on every attack. Strikes use an ease-in, snaps a
  back-out.
- **Follow-through.** Down each arm every point runs a little behind the one before. Strikes use a short lag, so the
  hand still lands on the contact.
- **Simulated secondary motion, not keyed.** The lantern hangs as a damped pendulum from the brow, and bumps off the
  womb, the trunk and the legs instead of passing through them. Every moss strand is its own small pendulum. Loops are
  simulated three times round and the last pass kept, so they close.
- **Rotations that behave:**
  - each bone turns the least it can from the frame before and is pulled gently back to its bind twist, so nothing
    flips or drifts;
  - near gimbal lock, a bone rolls slightly about its own length so its angles stay well-defined;
  - finger directions turn between keys rather than blending through zero.
- **Dense keys.** Every 0.05 s, and every 0.025 s for the fast clips (swipe, lunge, eruption, slam, death), so
  BetterModel's interpolation follows the whips.

## No clipping

A collision check runs on the exported tracks, sampled the way BetterModel interpolates them:
- every arm, leg and trunk segment is a capsule as thick as the part;
- the lantern and the womb are spheres.

Any limb passing into another part is reported with the clip and the time. The clips were tuned until none does: arm
swings route round the outside of the body, and the thin and back arms (whose shoulders sit together on the hump)
never rise together. **Result: 0 collisions in all twelve clips.**

## The clips, timed to the fight

| Clip | Length | Contact | What happens |
|---|---|---|---|
| idle | 4.0 s loop | | breathing, the trunk creaking, the arms shifting, the lantern swaying; a sudden creaking twitch of the thin arm |
| walk | 2.0 s loop | | a lurching three-beat gait: the crutch swings ahead and plants, the body vaults over it, then the right and the left leg; the dragging hands slide behind |
| spawn | 4.2 s | 2.8 s | curled in the circle, it shudders, unfolds limb by limb (crutch, legs, the right arms, the back arm), rears and roars, settles into the stalk; its lights come on as it rises |
| swipe | 1.4 s | 0.55 s | coils right with the great arm high, rakes it down on the target and digs in, swings it back round its right side |
| lunge | 1.2 s | 0.3 s | arrives crouched behind its prey (the creak's teleport) and stabs forward, then pulls back round the outside |
| eruption | 2.4 s | 0.55 s, 1.5 s | rears with every hand off the floor, drives them in (0.55), strains while the lanes charge, wrenches as the roots burst (1.5) |
| sap | 2.6 s | 1.75 s | rears, the womb lifted, the arms flung wide and trembling; a shudder as the sap falls |
| slam | 2.3 s | 1.5 s | a long rise with the crutch and the great arm raised overhead, brought down together |
| creak | 1.0 s | | stop-motion jerks like a watched creaking, folding in while every light goes out; then it vanishes |
| twitch | 0.5 s | | a heart breaks: a sharp flinch |
| stagger | 1.8 s | | the last heart breaks: it reels back, the crutch slips, it sags; the sleeper's eyes open |
| death | 3.6 s hold | | the legs give, it leans on the crutch, the crutch splays, it collapses; a last twitch of the thin arm; the lights fade |

## Checks

| Check | Result |
|---|---|
| Collisions (limbs into other parts) | 0 in every clip |
| Euler interpolation error (the Euler midpoint against the true halfway turn) | idle 0.1, walk 0.4, eruption 4.2, sap 3.9, creak 3.7; the fast strikes 9 to 21 (the great hand at the swipe's contact) |
| Lowest point | -1 to -6 units: fingers dug into the floor and the lantern resting on it in the spawn and death (the floor hides them) |
| Load test, server b (2026-11-19) | BetterModel 3.5.0 built the rig with its twelve clips clean (185 files, no errors); taken off b again |

The rig file is 9 MB because of the dense keys. That's fine for a server-side model, since the resource pack doesn't
carry animations.

## For session 8

- **The walk speed:** the walk's stride is 1.6 blocks a second. Set `HeartwoodHorror.SPEED` to 0.08 (blocks a tick),
  or the feet skate. Today it is 0.2.
- **The contacts:**
  - The swipe hits 0.55 s (11 ticks) after the clip starts; today it hits at once.
  - The lunge hits 0.3 s after the teleport.
  - The slam's ring at 1.5 s and the eruption's lanes at 1.5 s already match the fight's 30-tick warning, if the clip
    starts with the warning.
  - The sap falls at 1.75 s (35 ticks).
- **The creak:** play `creak` over the 20-tick warning before the teleport, with the lights tinted out, then `lunge`
  on arrival.
- **The tints** (session 6):
  - calm while the hearts stand;
  - vulnerable from the stagger on (20 s);
  - out for the creak;
  - dead with the death clip.
- **`twitch`** on each heart broken, **`stagger`** on the last.
- **Not watched in a real client yet:** the lantern's pendulum under `hi_lantern` turning to its target, and how
  BetterModel blends one clip into the next.
