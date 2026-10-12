# Witch Coven redesign: the plan (Hedge Witches x Cauldron Coven)

Agreed direction (2026-10-11): the **Hedge Witches'** look (witches grown out of the swamp thicket) combined with the
**Cauldron Coven's** weapons (iron vessels they brew and fight with). This replaces the wax-crone draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md), because wax and candles are now Brood Mother's look.
Rejected pitches: the Bottle Sisters (hard to read, easy to make goofy) and the Three Spinners (dull tools).

## Identity

**Three hedge witches who brew in the swamp.**
- **Bodies and robes:** robes grown through with bramble and root (a ragged root hem), bundles of dried herbs and bone
  charms hanging on twine; a real witch's hat.
- **Vessels:** each sister's soot-black iron vessel is her weapon, and the only saturated thing about her is the brew
  glowing in it.
- **Menace:** folk horror, not gore. They loom over you, hunched, with faces in the shadow of their hat brims, and
  they hover very still until they act.

**Vanilla ties:**
- the witch's bent, pointed hat and big nose;
- the swamp hut;
- vanilla's splash potions, which stay real;
- the three vanilla potion colours of the roles.

## The three sisters: the same body, told apart only by their vessels

**Decided by the user (2026-10-11):**
- **Body:** built like a vanilla witch or villager (the long robe, the head, the big nose), **larger than a player**
  so they loom over you, and crouched forward in an old woman's stoop. No hump.
- **No fingers, no visible hands.** The sleeves end in dark cuffs; whatever a sister holds or throws comes out of
  her sleeves.
- **All three are the same size and build.** Only their vessels tell them apart.
- **The hat is clearly a witch's hat** (vanilla's tall, bent, pointed hat), not woven thorns.
- **They hover low**, the hem of the robe trailing a little above the ground.
- **Every sister does every role.** The role is the colour of the smoke and liquid in her vessel (green healer,
  purple curser, red bomber), and it changes on rotation.
- **Faces:** the vanilla witch face (the big nose, the wart, the deep-set eyes), but made more interesting.

**The vessels (revised by the user after the first line-up):**

| Sister | Vessel | How she works |
|---|---|---|
| **The cauldron** | an extra-large cauldron hung on her back, tied on with ropes round her middle | her sleeves are free: she casts and throws with them, drawing from the cauldron |
| **The bottles** | a diagonal shoulder belt of large potion bottles, and one held in her sleeve | she throws the bottles; the brew in all of them shows the role |
| **The pot** | a pot held in front of her in both sleeves | she pours, tips and flings from it |

The robe is straight like a villager's (no flare, not a dress). As she hovers, a flat ragged hem (a 2D plane with
the rags in its texture) hangs below it.

**The rotation moment:** all three strike their vessels at once (a sleeve on the cauldron's rim, the bottles
clinked together, a sleeve rapped on the pot), and the brews change colour in a ripple from one sister to the next.

**Death:** a witch slumps into a heap of robe and brambles, her hat falling, and her vessel tips over, spilling brew
that fades. The survivors glance at it briefly, never during an attack.

## Rules for the design

- **The bodies are hedge, the weapons are iron**, so the two materials never blur. The palette:
  - dark bramble and root (brown to black);
  - dried, desaturated herb greens;
  - bone and twine for the tier-0 family;
  - soot iron for the vessels;
  - a small ember accent (coals glowing under the cauldron and the pot);
  - the role colour on the brew only.
- **A vessel never covers the face or the torso.** That's the Volley arbalest lesson: it hangs in front below the
  chest, swings at the side, or rides the back. Each vessel stays within about 40% of its witch's silhouette.
- **The three sisters share one body**, so the vessels must be large and placed differently (on the back, across
  the chest, held in front) for the sisters to differ at a glance. The hat and the stoop are the shared marks.
- **Few parts:** the boss-modeling lessons say about 40-60 cubes per witch, so three witches stay near Brood
  Mother's 72 displays in total. The leaves, thorns, herb texture and twine are paint, not geometry.
- **Faces:** the vanilla witch's face (big nose, wart, deep-set eyes) is the recognisable part, made more interesting.
  For example, a longer, crooked nose, eyes lit in the role colour under the hat brim, or strands of moss hanging from
  under the hat. The character study settles this.
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
   differ in the shared body's proportion and hunch. You pick one.
2. **Character study:** one sister, the cauldron witch, close up in 3D, to settle the face, the hat, how hedge meets iron,
   and the brew glow. You pick one, and that sets the language for all three.
3. **One careful blockout** of all three, checked from a player's eye height before you see it.
4. Then the usual sessions 2-8: design lock, rig, UV, paint, variants, animation, pack.

**Animation budget note:** each sister does three roles with her own vessel, so 9 role clips plus the shared idle,
walk, rotation, death and spawn clips. The clips share one structure (windup, release, recover) to keep that
manageable.

## Decided questions

- **Faces:** the vanilla witch face, made more interesting.
- **Height:** larger than a player, so they loom over you.
- **Movement:** they hover low.
