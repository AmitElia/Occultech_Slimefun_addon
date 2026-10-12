# Witch Coven redesign: the plan (Hedge Witches x Cauldron Coven)

Agreed direction (2026-10-11): the **Hedge Witches'** look (witches grown out of the swamp thicket) combined with the
**Cauldron Coven's** weapons (iron vessels they brew and fight with). This replaces the wax-crone draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md), because wax and candles are now Brood Mother's look.
Rejected pitches: the Bottle Sisters (hard to read, easy to make goofy) and the Three Spinners (dull tools).

## Identity

**Three hedge witches who brew in the swamp.**
- **Bodies and robes:** grown from bramble and root, hats woven of thorns, bundles of dried herbs and bone charms
  hanging on twine.
- **Vessels:** each sister's soot-black iron vessel is her weapon, and the only saturated thing about her is the brew
  glowing in it.
- **Menace:** folk horror, not gore. They are too tall and too thin, with twig fingers and faces in the shadow of
  their hat brims, and they stand very still until they act.

**Vanilla ties:**
- the witch's bent, pointed hat and big nose;
- the swamp hut;
- vanilla's splash potions, which stay real;
- the three vanilla potion colours of the roles.

## The three sisters: one build and one vessel each, kept for the whole fight

| Sister | Build | Vessel (her weapon) | How she does each role |
|---|---|---|---|
| **The Root-Mother** | round, heavy, low; robe of thick roots spreading on the ground like a skirt | a big iron **cauldron** hanging in front of her from a yoke, stirred with a long ladle-staff | heal: pours steam; curse: tips the cauldron so smoke rolls out over the floor; bomb: ladles a potion and flicks it |
| **The Briar** | tall and tapered, the tallest; a long bramble robe that drags; the tallest hat | a **censer** on a long chain, swung | heal: a smoke stream to her sister; curse: the censer swung low, leaving a smoke trail on the marked ground; bomb: the censer flung out and a potion thrown from it |
| **The Crook** | hunched, crooked, very long arms; twig fingers to the ground | a small **pot on her back** with a long **ladle** she flings from | heal: a ladle of brew splashed onto her sister; curse: drips from the ladle drawing the mark; bomb: a fast overhand ladle-fling |

**The role shows in the brew.** Each vessel's glow and steam turn the role colour (green healer, purple curser, red
bomber). That colour is the one thing a player needs to read: "kill the green one first".

**The rotation moment:** all three strike their vessels at once (a ladle on the rim, a censer on the ground, the pot
tapped), and the brews change colour in a ripple from one sister to the next.

**Death:** a witch slumps into a heap of brambles and her vessel tips over, spilling brew that fades. The survivors
glance at it briefly, never during an attack.

## Rules for the design

- **The bodies are hedge, the weapons are iron**, so the two materials never blur. The palette:
  - dark bramble and root (brown to black);
  - dried, desaturated herb greens;
  - bone and twine for the tier-0 family;
  - soot iron for the vessels;
  - a small ember accent (coals under the cauldron, sparks in the censer);
  - the role colour on the brew only.
- **A vessel never covers the face or the torso.** That's the Volley arbalest lesson: it hangs in front below the
  chest, swings at the side, or rides the back. Each vessel stays within about 40% of its witch's silhouette.
- **The three silhouettes must differ at a glance:** round and low, tall and thin, hunched and long-armed. The hat
  is the shared mark.
- **Few parts:** the boss-modeling lessons say about 40-60 cubes per witch, so three witches stay near Brood
  Mother's 72 displays in total. The leaves, thorns, herb texture and twine are paint, not geometry.
- **Faces:** the vanilla witch's face layout (big nose, wart, deep-set eyes) is the recognisable part. Whether it's
  the exact vanilla face at a whole scale, or our own face in that style, is an open question below.
- **Not used:** wax or candles, masks, gore, flowers as the role signal (too small to read in a fight).

## Gameplay fixes to make alongside (from boss-rework-plan.md)

1. **Make the curse dodgeable.** Today it marks the floor, but the effect lands on the player 1 s later wherever they
   have moved. The fix keeps the 1 s warning on a fixed spot of ground and affects only players still on it. The
   curser's smoke (or drips) draws that spot. This is a balance change.
2. **Cancel a witch's unfinished cast** when she dies or loses the role.
3. **Make wind-ups take real time.** Heal and potion throws start their wind-up before the existing release times, so
   each animation leads into the server's real moment.

## How we get there (the process that worked for the Monarch)

1. **Silhouette line-up:** 2-3 flat 2D line-ups of all three sisters side by side with a player for scale. They
   differ in proportion, heights and vessel placement. You pick one.
2. **Character study:** one sister, the Root-Mother, close up in 3D, to settle the face, the hat, how hedge meets iron,
   and the brew glow. You pick one, and that sets the language for all three.
3. **One careful blockout** of all three, checked from a player's eye height before you see it.
4. Then the usual sessions 2-8: design lock, rig, UV, paint, variants, animation, pack.

**Animation budget note:** each sister does three roles with her own vessel, so 9 role clips plus the shared idle,
walk, rotation, death and spawn clips. The clips share one structure (windup, release, recover) to keep that
manageable.

## Open questions

- **Faces:** the exact vanilla witch face at a whole scale (as Brood Mother kept the spider's), or our own face in the
  same style?
- **Height:** should the sisters stay player-sized (vanilla witches are about 1.95 blocks), or grow to 2.5-3 blocks
  so they loom?
- **Movement:** do they walk (vanilla witch AI), or hover low with their robes trailing like roots?
