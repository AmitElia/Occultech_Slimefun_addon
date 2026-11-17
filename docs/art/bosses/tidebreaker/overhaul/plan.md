# The Tidebreaker redesign: the plan (the Last Harpooner)

Agreed direction (2026-11-04): **the Last Harpooner**, from the draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md), reworked with the user.

## Identity

The user's brief (2026-11-04):
- **The rider: a drowned whaler in a sou'wester**, barnacled and mutated. Not a diving helmet: the Abyssal Warden
  is the diving helmet now. (Changed at the step 1 pick: a drowned Viking, see below.)
- **The mount: a colossal nautilus**, with **harpoon lines and nets** round its shell.
- **No nailed-on trophy figureheads.** Instead **the front of the shell** (the end away from the tentacles) **is a
  makeshift ship's bow**: wooden planks and **one decorated figurehead**, as if a piece of an old ship were nailed onto
  the nautilus.
- The textures must be great.

**Step 1 pick (2026-11-04): B, the Serpent Stem, which reads as a Viking ship**, with two changes:
- **The rider stands in the bow** like C's harpooner.
- **He is a drowned Viking** now, not a whaler: a horned helmet, torn leather clothes, and a long spear that he throws.

**Why the bow leads:** a real nautilus swims shell first, pushing water out of its siphon, with its tentacles
trailing. So the Tidebreaker rams prow first, and the wreck's bow is his battering ram.

**Vanilla ties:**
- **The nautilus** (26.2 `NautilusModel`): its cream shell with red tiger stripes, the hood over the body, the
  tentacles round the mouth, and the eyes on the body's sides.
- **The drowned:** its sea-green skin, its glowing eyes, and its trident.

## The fight (Tidebreaker.java; the code stays)

| Moment | Server | Look (to design) |
|---|---|---|
| glide | the nautilus swims through the air over land after the nearest fighter, with the rider on it | the tentacles trail and pulse; the shell pitches as it steers |
| ram | a 1 s lane warning, then a charge of up to 25 ticks: 33.5 damage and a throw | the tentacles pull into the shell, the bow dips, and the rider lowers his harpoon like a lance |
| winded | 2 s after a charge: the melee opening | the nautilus sags and its huge eye opens and rolls. The rider comes down within reach |
| trident volley | three tridents in a fan, every 10 s | the rider stands up in the saddle and throws |
| trident thrust | anyone within 4 blocks, 23 damage | a short jab from the saddle |
| death | - | the rider slumps over the bow; the nautilus pulls into its shell and sinks |

**Gameplay truth:**
- **Only the rider can be hurt,** so he must always be in plain view. The bow, the lines and the nets must never
  cover him, and must not look like weak spots.
- **He must be in melee reach:** the seat sits at about 2.5 blocks, so a player 2 blocks away can reach his body.
  When winded, the nautilus sags and he comes lower still.

## Materials (not repeated from other bosses)

Already used by other bosses:
- wax and candles;
- amethyst and bone;
- iron vessels and brew;
- leather, chains and fire;
- sculk;
- cards;
- lava and basalt;
- gold;
- dark oak and emerald;
- copper, sea glass and prismarine.

The Tidebreaker's:
- **the nautilus shell:** cream, with tiger stripes and a nacre sheen inside the opening;
- **tarred ship planking:** grey, sea-worn spruce, with iron nails and rust streaks;
- **a carved, painted figurehead:** paint flaking off;
- **hemp rope and fishing net;**
- **yellow oilskin, gone mouldy;**
- **the drowned's skin,** with a few barnacles (the Warden's barnacles grow on a hand; his grow on a face).

**His light:** a whaler's oil lantern on the bow, and his eyes. A warm, sickly lantern yellow sets him apart from the
Warden's sea teal.

## Process

Session 1 in gated steps:
1. **Silhouettes:** three takes on the bow, the figurehead and the rider, shown idle and lowering the harpoon for
   the ram, next to a player.
2. **The detail studies** the pick needs: the figurehead, and the rider's face under the sou'wester.
3. **The blockout.**

Sessions 2-8 as in [boss-art-sessions.md](../../../../boss-art-sessions.md).
