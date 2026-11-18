# Hollow Warlord, the Headsman: session 7 (animation)

Scripts: `tools/art/bosses/headsman_s7.py <client folder>` (the clips, written into the rig) and
`tools/art/bosses/headsman_gif.py [clip ...] <client folder>` (lit, textured GIFs from the same keys BetterModel
plays). GIFs: [lit/](lit/). Rig: `occultech_hollow_warlord_rig.bbmodel` (also in `run/plugins/BetterModel/models`;
try `/bm test occultech_hollow_warlord_rig <clip>`). Report: [clips.json](clips.json).

## Take 2 (after the first review)

Review of take 1: the shoulder pads did not move with the arms; the sword struck with its flat, not its edge; the
clips needed to be more intimidating; the hat-tearing enrage was disliked; the idle should hold the sword behind him.

- **Pauldrons ride the arms:** each shoulder plate turns with its upper arm (60% of the arm's swing away from hanging,
  at most 60 degrees, no twist), so a raised arm lifts its plate.
- **Edge first:** the sweep now travels with the flat level and the chop with the flat upright, so the edge leads;
  the raise before the chop and the windup's lift roll the blade so the edge leads them too. `edge_report` measures
  it (in clips.json): at the sweep's and the chop's full speed under 5% of the blade's motion is along its flat's
  normal.
- **The sword hangs behind him** in the idle, its end resting on the floor, the same carry as the walk's drag and the
  windup's start, so idle, walk and windup blend into each other without the blade crossing his body.
- **A new enrage:** he buckles, rises with the sword point-down high in both hands, drives it into the floor (contact
  1.05 s), roars with the skulls whirling once round him, wrenches it out and swings it over the top onto his
  shoulder. The hat stays on; idle_enraged has the skulls circling his head.
- **Weight:** slow starts and a held beat before each blow (the chop hangs at the top for 0.1 s), the body sinks into
  every impact and every footfall, the head stays on the target while the body turns under it, and a hit barely moves
  him (a short recoil, then the head drops back onto you).
- **Paths round him, not through him:** the hands swing wide round the shoulder to raise the sword, the sword is
  carried round his right side to plant it or let it hang, the kneeling foot rolls over its toes.
- Limbs that carried twist in from a big swing ease it back out whenever they point anywhere but up, so every clip
  ends in the same arm twist the idle has.

## Take 3 (after the second review)

Review of take 2: the windup and the swing looked wrong, the hands clipped through the body. The sweep circled the
hands round his spine, so in the windup both hands reached behind his back and the arms cut through the torso.

- **The swing is a body turn:** hips and chest turn up to 80 degrees into the blade (hips 40%, chest 60%), the head
  stays on the front, and the hands only cover the rest on a short arc well in front of the chest, elbows out and
  forward. No hand ever passes behind him or across his chest.
- **The chop starts from a high guard** in front of his face (the blade up and back over the hat), not with the hands
  on top of his head.
- **The enraged stance is a low two-handed guard** with the point levelled at you (the shoulder carry put a hand
  through his skull); the enrage ends by swinging the point up off the floor into it.
- **Every planted sword sits further out** (call, enrage, kneel), so the bowed head and the chest clear the hilt.
- **Pauldrons follow less** (45% of the arm's swing, at most 40 degrees): they rode up like wings.
- **`clip_check`** (in clips.json) tests points through both forearms, the hands and the sword against every cube of
  the torso, belt, head and legs on every frame BetterModel plays. Take 2 had arms up to 7 units inside the body; take
  3 is at most about 2.5 units anywhere (armour edges brushing), mostly 0.

## How it is animated

- **Pose parameters, not joint angles:** a frame is where the ankles, the hands, the sword's grip and point, and the
  floating skulls are, plus the torso's lean and twist. Every frame is solved with two-bone IK at fixed bone lengths, so
  the feet stay planted, both hands stay on the grip and nothing folds through itself between keys.
- **Anticipation, overshoot and settle** on every committed motion; **secondary motion:** breathing, the tabard
  swaying a beat behind, the taken skulls bobbing and drifting on their own phases (each loop closes on itself).
- **Dense keys:** 0.025 s for the windup, the sweep, the chop, the call and the enrage; 0.05 s for the walk, flinch,
  spawn and death; 0.1 s for the idles.

## Clips (contacts for session 8)

| Clip | Length | Loop | What happens |
|---|---|---|---|
| idle | 4.0 s | loop | tall over his prey, the sword hanging behind him, its end on the floor; deep slow breaths, a slow look round |
| walk | 1.6 s | loop | in place (the server moves him); a stalking stride that sinks into every footfall, the sword dragged behind |
| windup | 1.0 s | hold | the soul sweep's warning: the blade lifted off the floor and drawn far back, coiled and trembling (contact 1.0 s) |
| sweep | 1.8 s | once | the whirl round the front to his left, contact 0.3 s; a held follow-through, swung back one-handed, let fall behind |
| attack | 1.5 s | once | melee: raised into a high guard before his face, a held beat, the chop down in front (contact 0.72 s), let swing back behind |
| call | 2.2 s | once | the warband answers: the sword driven into the floor, his fist raised, the skulls flaring up (contact 0.9 s) |
| enrage | 2.4 s | once | buckles, raises the sword point-down, drives it into the floor (contact 1.05 s), roars as the skulls whirl, levels the point at you |
| idle_enraged | 4.8 s | loop | lower and wider, a low two-handed guard with the point at you, breathing hard; the skulls circle his head |
| flinch | 0.5 s | once | a short recoil, then the head drops back onto you |
| spawn | 3.4 s | once | from a kneel over the planted sword: the skulls rise off the floor and light, he stands, wrenches the sword out |
| death | 3.2 s | hold | staggers, swings the sword round to plant it, drops to one knee and bows; the skulls go dark and fall |

Session 8 needs: the glow tints driven as in the GIFs (tell through the windup, the sweep and the raised chop,
white-hot from the enrage's slam on, skulls dark per dead guard, all out at death); the fallen skulls and the kneel
come from the death clip, so the corpse must be handed to a stand-in that holds it. The skulls circle by moving, not
turning, so no bone's angle winds up between clips. Floor check: nothing sinks more than about 2 units, apart from
the sword (driven into the floor in the chop, call, enrage, death and spawn) and the fallen skulls and tabard lying
on it.
