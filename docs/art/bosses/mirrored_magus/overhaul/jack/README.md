# Mirrored Magus - the Jack-in-the-Box (design approved; built in sessions 7-8)

A second mechanic beside his mirrored copies. The user's brief (2026-10-13): little pop-up box clowns with the colours
and shape of his face and upper body but much less detail, on a spring, animated to shoot cards with a bopping
animation.

Study renders: `jack.png`, made by `python tools/art/bosses/magus_jack.py`.

## The model
- **The box:** crimson, gold-trimmed, a harlequin diamond on each side (black on the front and back, white on the sides),
  the lid standing open behind it, a crank on its right side.
- **The spring:** a gold coil (rings of four bars, every other ring turned 45 degrees).
- **The clown:** his face with much less detail. It has the same white head, brows, red nose and illager eyes, and the
  same face paint.
  - The grin has two upper and three lower lip segments a side and five big teeth.
  - There are two tufts of hair a side and a shrunken hat with two floppy points and bells.
  - The upper body is black and white chest halves, a ruff of eight wedges and stubby arms. The right hand holds a fan
    of three cards.
- **Size:** built at the Magus's head size, so his face paint fits unchanged, and scaled by half (BetterModel scale).
  About 2 blocks tall with the hat, so it comes up to a player's head.
- **Cost:** about 100 cubes on 12 bones. Every turn is 0, 22.5 or 45 degrees on one axis, so a cube adds no extra
  display.
- **Bones:** `jack_box`, `lid`, `crank`, `spring`, `body`, `hi_head`, `glow_eyes`, `arm_left`, `arm_right`, `cards`,
  `hat_left`, `hat_right`.

## The animations (session 7)
- **pop (spawn, 0.5 s):** the box sits shut and the crank turns, playing a music-box tune (the telegraph). Then the lid
  flies open and the spring shoots up past full length and settles with a wobble.
- **bop (idle, loop):** the spring squashes and stretches (y scale), the body and head nod forward and back, and the hat
  points flop. A spring "boing" plays on each bop.
- **throw:** three quick bops wind up, then a big stretch back and a flick of the right arm. The card leaves the hand on
  the flick.
- **wind-down (despawn):** the spring sags, the clown droops into the box and the lid slams shut. The box then fades
  out in a puff of confetti.
- **death (broken):** the head pops off the spring with a squeaky honk, the spring goes limp and the box bursts into
  confetti.

## The mechanic: "Jack-in-the-Box"
- **When:** every 20 s, staggered with the decoys (which come every 15 s), the Magus snaps his fingers.
  - Two boxes appear, plus one per extra fighter, up to four.
  - Each box appears at a random spot on the arena floor, at least 6 blocks from every player and 3 from each other.
- **Telegraph (1.5 s):** each box appears shut, its crank turning to a music-box tune, with particles above it. Then it
  pops open.
- **Attack:** each jack bops in place and turns to face the nearest fighter it can see.
  - Every 2.5 s it throws one card: three bops wind up, then the flick.
  - The card is a visible flying item display that moves slowly enough to sidestep and flies straight.
  - On a hit it deals `Mechanic` "Jack card": 8 raw, PROJECTILE, telegraphed. That is half the Magus's own thrown card (16, replacing his arrow in session 8).
    It goes through `BossFight.hit`, so the balance tool grades it.
- **Breaking one:**
  - **Health:** each jack is a breakable fight object (an interaction hitbox) with 3 hits' health, so any weapon breaks
    it quickly.
  - **Bursting:** on its last hit it bursts.
  - **Lifetime:** it winds down after 15 s if left alone.
  - **Cap:** at most four jacks are alive.
- **No hint:** a jack is a plain damage-and-distraction add. Breaking one tells you nothing about which Magus
  is real (the user, 2026-10-13); the counterplay is to clear them or dodge their cards while you hunt.
- **Rules check (docs/boss-ideas.md):**
  - **Rule 1:** the jack is a plugin entity (display rig, interaction hitbox) removed when the fight ends. It places no
    blocks and the card breaks nothing.
  - **Rule 3:** each jack is tagged in its PDC and counts toward the fight's extra-mob cap. Only hits from players in
    the arena count. It can't be pushed, leashed or moved.
  - **Rule 4:** no drops or XP.
  - **Rule 6:** each throw is telegraphed by the three-bop wind-up and the cards are dodgeable. The 1.5 s crank warns
    before each box opens, and a box never spawns next to a player.
  - **Crash safety:** a crash or unload removes jacks like any other add (fresh adds on resume).
- **Without Mythic/BetterModel:** the vanilla body is an item display of a
  player head painted like his face, on a jumping slime-block display, with the same hitbox and cards.

## Decided (the user, 2026-10-13)
- No sparkle hint when a jack breaks: they are a plain damage-and-distraction add.
- The count scales with fighters: two, plus one per extra fighter, up to four.
