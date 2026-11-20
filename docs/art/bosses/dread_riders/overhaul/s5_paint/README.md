# Dread Riders, session 5: texture painting

Script: `tools/art/bosses/dread_s5.py <client folder> [--server]`, on session 4's layout (the same islands, one atlas
per model).

Sheets: [sheet_vanguard.png](sheet_vanguard.png), [sheet_outrider.png](sheet_outrider.png). Each has eight views:
- the hero view;
- about 10 blocks away;
- the side;
- a player's eye;
- the back;
- close-ups of the rider's head and the horse's head.

The painted review rigs, with session 3's poses, replace the textured ones in `run/plugins/BetterModel/models`. For
example: `/bm test occultech_dread_vanguard_mount_rig idle`.

## How it's painted

Every texel is fully clear or fully opaque.
- **Ramps:** each runs from a cool violet or blue dark, through the zone's colour, to a warm light.
- **Form only:** the game already shades by face direction, so the texture adds only form, plus ambient occlusion
  baked from the real geometry.
- **Clusters, not speckle:** detail sits in 2x2 to 3x3 clusters.
- **Smooth metal:** metal keeps one highlight band.
- **Vanilla untouched:** the vanilla skins (the riders' heads and bodies, the skeleton's limbs, the horses' heads) are
  left as they are.

**The Vanguard's horse**
- **Hide:** vanilla's rotting zombie-horse green, broadly mottled, with a little darker rot and paler mould. On the
  flanks the ribs show through the hide as pale bars.
- **Mane and tail:** dark, in strands.
- **Barding and armour:** netherite-dark plate. Each plate has a lit bevel and a groove inside it, one soft highlight
  band, grime pooling low, scuffed edges in broken runs, and a few scratches with a shadow under them. Rivets run along
  the big plates' edges.
- **Spikes:** smooth, with a lit ridge and a highlight band.
- **Glows:** the chest boss's sigil and the eyes glow crimson.
- **Saddle cloth and banner:** near-black violet cloth in folds, with the hanging ends tattered. The trim is crimson
  with a stitched line.

**The Vanguard**
- **Head:** vanilla's zombie face under the horned armet.
- **Horns:** dark horn ringed with growth ridges, pale at the tips.
- **Lance:** the grain runs along its length, and the grip is wrapped in leather bands.

**The Outrider's horse**
- **Bones:** old bone, lit along the top and darker towards the joints, with hairline cracks.
- **Rope:** red rope lashings, twisted in diagonal bands.
- **Blanket:** a coarse weave, frayed along its lower edge.
- **Tail:** a dark horsehair tail.
- **Glows:** the cyan eyes, over vanilla's dark socket.

**The Outrider**
- **Head and body:** vanilla's skeleton.
- **Steppe helm:** smooth iron with a highlight band and a few hammer dents. The gold rim and ribs are polished.
- **Aventail:** rows of rings.
- **Plume:** red horsehair in strands.

## Self-review before showing

The first pass was too busy:
- **The zombie horse's hide** read as green camouflage. The mottle is now broader and rarer, and the rot and mould are
  fainter.
- **The plates** were light and grainy, like granite rather than netherite. They are now darker and smooth, with only
  the bevel, the band, the scuffs and the scratches.
- **The bones** were spotty, like cork. They are now calm bone with cracks.

## Review 1 (user, 2026-11-20)

- **The skeleton horse's head was too small for its body, and a different colour.** Both horses now wear vanilla's
  horse head at 3x instead of 2x: the skull is 18 x 15 x 21 before the overall scale, with the vanilla skins at
  3 pixels per texel. The skeleton horse's bones are painted in vanilla's skeleton-horse greys (white to grey, sampled
  from `horse_skeleton.png`), so skull and body are one bone.
- **The zombie horse's eyes were hidden.** That wasn't on purpose: the chanfron's cheek guards covered them. The guards
  now sit below the eyes, and the crimson eyes show.
- **Parts clipped on the zombie horse's head.**
  - The ears poked through the chanfron; they are plate ear cups now.
  - The poll spikes and the brow spikes start behind and outside the head instead of inside it.
- **The skeleton's body was boring.** He now wears a steppe horse archer's kit over the vanilla skeleton:
  - a lamellar cuirass in laced bands, with a gold-rimmed mirror plate on the chest and a cyan rune in it;
  - two lames on each shoulder, and lamellar tassets over the thighs;
  - leather bracers;
  - a belt with a gold buckle and a pouch;
  - a sabre on the left hip and a bow case on the left flank.
- **The riders were too big next to a player.** The whole pair is now 0.75 of its old size:

  | | Withers | Seat | Rider's head top | Rider's hitbox |
  |---|---|---|---|---|
  | Vanguard | 3.3 blocks | 3.3 | 5.3 | 1.88 x 5.58 x 1.88 |
  | Outrider | 3.3 blocks | 3.4 | 5.4 | 1.88 x 6.14 x 1.88 |

  The scale is baked into the geometry after the UVs are laid out, so every face keeps its whole-texel island. The
  boss's texel density is therefore 4/3 per unit (a texel is 0.75 of a vanilla pixel) everywhere, one density for the
  whole boss, as a documented decision. The flicker resolver runs again at the new size, so there are 0 flickering
  faces.
- **New counts:** the Outrider rider has 138 cubes and 79 displays. The value check is still clean: lamellar
  (L* 56) against gold (darker brass now, 43) and leather (31).

## Not checked yet

- **In a real client:** colours under the game's lighting, night, and the hit tint.
