# The Mirrored Magus redesign, session 7: animation

Eleven clips for the Magus on the session 5 rig, and five for the Jack-in-the-Box on its own rig.
- **Built from poses:** his clips are made from session 2's key poses, as each bone's turn away from rest. The hips
  sink with a position key wherever a pose sits him lower (the curtsey, the blink's fold, the death).
- **The hat:** its three floppy points flop and swing through his idle, walk and flinch, each segment lagging the one
  before it.
- **Releases:** each action clip has a release time (bold below). Session 8 starts the clip so the release lands on the
  server's real moment. Animation is cosmetic, and every hit and telegraph comes from the server.

## The Magus (`occultech_mirrored_magus_rig`)

**Take 2** (the user: the first take was too stiff and robotic, not horror, and the knees bent the wrong way). He moves
like a marionette that isn't quite alive:
- **Stillness and snaps:** long, unnatural stillness broken by sudden jerks. His head snaps to a cocked tilt and holds a
  beat too long (held keys), then snaps back.
- **Trembling:** he shakes through every warning and every hold.
- **The walk:** a limping lurch. One leg is yanked up high, the other foot drags behind, and his head stays fixed on
  its target while his body rolls under it.
- **The knees:** a knee bends with a negative shin turn. Session 2's poses had them reversed (throw, curtsey, blink,
  death) and are fixed. The blink is now a real crouch.

| Clip | Length | Plays | What happens |
|---|---|---|---|
| idle | 4.0 s | loop | hanging from his strings, knees soft, swaying, arms dangling like dead weight; his head snaps to a cocked tilt, holds, snaps the other way |
| walk | 2.0 s | loop | the limping lurch above; a head twitch every cycle; the hat's points whipping |
| spawn | 3.4 s | once | crumpled on the floor, pulled up by his strings in jerks: the body, the legs, the arms yanked overhead with the wrists dangling, the head last. It snaps sideways, holds, snaps upright, then a too-deep bow |
| throw | 1.4 s | once | a slow, coiled wind-up with his head cocked after the arm; the whip **at 0.6 s** (the cards leave his palm); a twisted, trembling hold; a jerky return |
| prism | 2.4 s | once | he rises off the floor, toes dangling, arms lifting slowly with the cards, his head lolled back and twitching, trembling through the 30-tick warning; the burst **at 1.5 s** snaps his face down at you, and he drops |
| curtsey | 2.0 s | once | a bow far too deep with his face still turned up, staring at you; the decoys **at 1.0 s**; a long hold, a twitch, a snap upright |
| blink | 0.9 s | once | folding into a crouch as his head turns all the way round, shrinking to nothing; the teleport **at 0.45 s**; he unfolds where he lands, the head turning back the other way |
| laugh | 1.8 s | once | a decoy struck: head thrown back, convulsing, both hands clutching in, the head bobbing; it stops dead and his face snaps down to stare at you |
| snap | 1.2 s | once | the jacks' summons: the left hand rising slowly, his head tilting after it; the snap **at 0.6 s** jolts his whole body; his head jerks round to stare at you |
| flinch | 0.6 s | once | hit: a violent jerk, the head snapped sideways; it turns back slowly, with one twitch |
| death | 3.0 s | hold | the strings jerk taut (arms flung out, head back), then cut: he drops like dead weight into the slump; a pause, a last twitch of the arm, then of the head |

The throw, snap and flinch override only the bones they move, so the idle or walk goes on underneath.

![Key frames of the Magus's clips](magus/keyframes.png)

## The Jack-in-the-Box (`occultech_mirrored_magus_jack`)

Its clips carry the names the fight engine plays on a fight object's model (session 8): `rise` when it appears,
`hit` per hit, `shatter` when broken; `idle` is BetterModel's default loop.

Its own model, built at half size and set on the ground: about 100 cubes on 12 bones, painted with the Magus's
painters, with a hitbox round the whole jack.
- **The spring:** the clown's body is a sibling of the spring, not its child. Each clip scales the spring in y and
  moves the body with its top, so the clown bounces without being squashed with it.

| Clip | Length | Plays | What happens |
|---|---|---|---|
| rise (the pop) | 2.0 s | once | the box shut, rattling, its crank turning through the 1.5 s warning; the lid flies open **at 1.5 s** and the clown shoots up past full stretch, wobbling to a stop |
| idle (the bop) | 0.6 s | loop | the spring squashing and stretching, the clown nodding, the hat flopping, the arms bouncing |
| throw | 1.5 s | once | three bops winding up, a big stretch back, the flick **at 1.15 s** (the card leaves his hand) |
| wind | 1.4 s | hold | the wind-down: the spring sags, the clown droops into the box, the lid slams shut |
| hit | 0.3 s | once | a jolt: the spring squashed, the clown knocked back |
| shatter | 0.7 s | hold | broken: the head pops off the spring and spins away, the spring goes limp, the box bursts |

![Key frames of the jack's clips](jack/keyframes.png)

The GIFs in `magus/gifs/` and `jack/gifs/` show each clip moving (flat zone colours, the eyes at full glow).
`clips.json` lists every clip's length, mode, bone count and release time.

## For the fight code (session 8)
- **Starting clips on time:** start each action clip early by its release time.
  - **The card fan:** start `throw` 12 ticks before the cards are thrown.
  - **The prism:** start `prism` as the 30-tick warning begins.
  - **The decoys:** start `curtsey` 20 ticks before they spawn.
  - **The blink:** start `blink` 9 ticks before the teleport.
  - **The jacks:** start `snap` 12 ticks before they appear.
- **A struck decoy:** it plays the shatter tint (session 6), then breaks apart. The real Magus plays `laugh`.
- **Each jack's life:**
  - **Spawn:** it plays `pop` when it appears, and its 1.5 s crank is the telegraph.
  - **Idle:** after the pop it loops `bop`.
  - **Attacks:** it plays `throw` for each card, starting 23 ticks before the card leaves.
  - **The end:** it plays `wind` at the end of its 15 s, or `death` when broken, and its entity is removed when the
    clip ends.

Regenerate with `python tools/art/bosses/magus_s7.py` (after `magus_s5.py`). It writes both rigs here and copies them
to the test server's BetterModel models.
