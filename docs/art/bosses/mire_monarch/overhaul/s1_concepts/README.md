# Mire Monarch, session 1 (take 5): three directions for the radioactive toad king

**Rejected 2026-10-11:** the eyes looked horrible, the proportions were goofy rather than intimidating, and it had too many parts. The redesign restarts from posture silhouettes: [../s1_silhouettes](../s1_silhouettes/README.md).

**The brief (2026-10-11):**
- a mutated version of vanilla's frog;
- radioactive and toxic;
- a large crown;
- large warts on its back;
- a new attack: a tongue that pulls a player in.

![Three directions: three-quarter, side silhouette, front, tongue out](compare.png)

## What changed from the rejected toads

Take 4 built every part from stepped "rounded boxes", so the toads read as crates with a crown on top. This take
changes how they are built:

- **Vanilla's real frog head, exactly.** The head is the client's `FrogModel`, read from the 26.2 jar: a 7x3x9 head slab
  over a 7x3x9 jaw split by the dark mouth line, 3x2x3 eyes on the front corners, and flat 8x8 webbed hands and feet.
  It is scaled by a whole factor (4x), the way Brood Mother kept the vanilla spider's face at 3x.
- **The head is small and the body is huge.** Take 4 had a head as wide as the body, so from the front it was all
  head. Here a real toad's proportions apply: a wide, low dome with the head out in front.
- **Chamfered masses instead of terraces.** Every big form is an octagonal prism: a box with its long edges cut at
  45 degrees, which any rotation allows in game. Nothing is a stepped stack.
- **A clean crown.** It is a square band with one triangle per point: a turned square, half sunk into the band, with
  a gold ball on top. A first try with tapering points read as "wedding cake" steps and was cut.

## References

These are studied for principles, never copied:

| Source | What we take |
|---|---|
| Alex's Caves, Toxic Caves ([wiki](https://alexscaves.wiki.gg/wiki/Toxic_Caves), [Nucleeper](https://alexscaves.wiki.gg/wiki/Nucleeper)) | Radioactive reads as a dark, calm body with lime light coming *from inside*: cracks, cores, a glowing tell (the Nucleeper's core and siren). We use glowing cores in split warts and glands, not a green-tinted body. |
| L_Ender's Cataclysm ([CurseForge](https://www.curseforge.com/minecraft/mc-mods/lendercataclysm)) | Heavy faceted masses with emissive seams; rotated cuboids for bevels and slopes rather than stacked steps. |
| Mowzie's Mobs ([guide](https://www.minecraft-guides.com/mod/mowzies-mobs/wiki/)) | One dominant, exaggerated mass per creature (Frostmaw's arms, the Wroughtnaut's helm), long readable wind-ups. |
| Twilight Forest | Bosses that stay close to vanilla's texture language and are made big by simple shapes. |
| Vanilla frog (`FrogModel`, `frog_cold.png`) | The head, eyes, mouth line, flat webbed feet and the tongue plane, all kept as they are. |
| Real toads | The cane toad's **parotoid glands** (real poison glands swelling behind the eyes) are the source of the glowing glands. The bullfrog's folded haunches and the toad's sacral hump (the back peaking over the hips) give the side silhouette. |
| [MobZ giant toad](https://www.curseforge.com/minecraft/mc-mods/mobz) | The only giant-toad mob found. Its model is borrowed from another mod, so there's nothing to learn from it beyond the fact that nobody owns this look yet. |

## The three directions

| | Direction | The mutation | Crown | Size (w x h x d) |
|---|---|---|---|---|
| A | **The Glowback** | The body ballooned into a low, huge dome peaking over the hips, crowded with **large radioactive warts**, each a bulb split open on a glowing core. Two glowing poison glands sit behind the eyes. | A wide crown on the back of the skull, tipped forward. | 8.0 x 4.1 x 7.2 blocks |
| B | **The Stilt Tyrant** | The legs mutated: over-long hind legs folded so the **knees rise above its back**, long straight arms lifting the chest, the head held high. A ridge of glowing pustules runs down the spine. | A tall, narrow crown with high points. | 6.1 x 5.3 x 6.8 |
| C | **The Lantern Throat** | The croaking sac swollen into a **huge glowing bladder of toxin** hanging under the chin to the floor, the skin stretched over it in bands. The back is packed with warts. | The heaviest crown, slipping to one side. | 7.5 x 5.3 x 7.0 |

Each direction's sheet (front, side, top, player's eye, clay, flat, tongue): [A](A/sheet.png), [B](B/sheet.png), [C](C/sheet.png).

**How each one plays the fight:**
- **A:** the hump and warts are its identity; the leap is a heavy belly-flop (it's the lowest and widest). The 33%
  dried phase has the most to show: the warts burst and empty, and the glands leak.
- **B:** the coiled knees *are* the leap's tell (they rise further before it jumps), the most readable of the three.
  It is the narrowest at 6 blocks, and the least "fat toad".
- **C:** the bladder pulses as the tongue and acid tells and empties at 33%. Risk: a big glowing sac looks like a
  weak spot, which the boss rules warn against, because hits anywhere count the same. It would need to be dimmer, or
  really be a weak spot (a design change).

**My read:** A is the most "toad king". Its silhouette, a lumpy dome with a crown, reads at any distance, and it shows
all four brief points at once. B has the strongest animation potential. C has the most unusual idea, but the
weak-spot problem comes with it.

Not in this take: the dried 33% form. It comes after you pick a direction. Textures come in session 5, and the
vanilla frog's texture will go on the head at 4x.

## The tongue pull (new attack, in `MireMonarch.java`)

- **When:** every 10 s, or 8 s once it's below 33%. It never overlaps a leap.
- **Target:** a random player 5-14 blocks away whom the boss can see.
- **Tell:** a lime lane on the floor, 2 blocks wide, 14 long, pointed at that player and locked for 1.25 s. The
  frog croaks.
- **Lash:** the tongue shoots down the same lane. The first player in it takes 5 (Tongue, `MELEE`) and is yanked to
  about 2 blocks in front of the mouth. This is a capped pull (knockback, never a teleport) into its crush range.
- **Dodge:** step out of the lane. Jumping does not help, which keeps it different from the shockwave.
- On the models, the tongue shows as the long lime tongue with a sticky club in the `tongue_34` renders. Vanilla's
  tongue is a flat plane; this one is thick.

Regenerate with `python tools/art/bosses/monarch_s1.py` (`quick` renders four views; `A`/`B`/`C` picks directions).
Take 4 (Bullfrog Tyrant / Horned Maw / Bog King) and earlier rounds are in git history.
