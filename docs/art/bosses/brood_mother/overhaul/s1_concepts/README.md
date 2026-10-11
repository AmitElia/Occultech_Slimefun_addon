# Brood Mother redesign, session 1 (take 2): three directions

The first take (a villager mask and egg cocoons) was rejected; it stays in git history. The new brief (2026-10-10):
- the **vanilla spider**, buffed and mutated;
- **long predator legs** with several joints;
- on her back, a **mountain of melted wax and lit candles**;
- no mask; **large mandibles**.

These are blockouts for picking a direction, in flat colours. Texture, the candle glow and the flicker come in later
sessions.

![Three directions: front, side, three-quarter](compare.png)
![Material zones: front, side, back](compare_material.png)

| | Direction | Posture | Size (w x h x d) |
|---|---|---|---|
| A | **Candle stalker** | slung high between very long four-joint legs, the knees far above her back (a harvestman's build); a tall, narrow wax spire | 5.7 x 5.9 x 4.9 blocks |
| B | **Wax hulk** | heavy and muscled, low to the ground on thick legs; the biggest wax mountain, spilling down her sides | 5.9 x 5.3 x 6.0 |
| C | **Ambush hunter** | head carried low with the mandibles spread wide; the front pair of legs held up and folded like a mantis's scythes | 5.6 x 4.9 x 4.7 |

Sheets per direction: [A](A/sheet.png), [B](B/sheet.png), [C](C/sheet.png). Regenerate:
`python tools/art/bosses/brood_s1.py`.

## What all three share

- **The vanilla spider underneath:** the vanilla parts in their vanilla proportions, scaled up 2 to 2.6 times. A big
  square head, a small thorax, a long boxy abdomen, and the red eye pattern on the face. Mutated: the thorax is swollen
  with muscle humps, an extra cluster of eyes spills down one cheek, and the abdomen bulges and splits its flank plates
  under the wax.
- **Predator legs:** eight legs with four segments each, bristled, climbing to a high knee and reaching down to the floor.
- **Mandibles:** big chelicerae under the face, reaching forward like pincers, with a hooked fang and a row of teeth
  inside.
- **The wax mountain:** lumps of melted wax run together around one slumped peak. A skirt of drips hangs over the edge
  of the abdomen. Candles of every height stand all over it: tall ones crown the peak, some are burnt down to stubs and
  some lean. Each flame is its own `glow_` bone, ready for full-bright and a flicker.
- **Colours:** tier 0. Dark chitin and bone-coloured mandibles; honey wax in two shades; red eyes; orange flames.

## Fit with the fight

- **Egg sacs:** they could become wax-sealed egg clutches dropped from the mountain, so the pile shrinks as the fight goes on.
- **Web zone:** the spinnerets at the back of the abdomen.
- **Pounce:** A rears up on its long legs, B crouches low, and C cocks its scythes: each is a clear one-second warning.
- **A wax hazard:** molten wax spilling from the pile as a slowing puddle, telegraphed by the flames flaring.

## Inspirations

- **The vanilla spider:** body plan, head and eye pattern.
- **Harvestmen (daddy longlegs):** legs many times the body length, which reach down from a high body (A).
- **Candle golems and wax golems:** wax heaped into a body, candles on every ledge, drips everywhere.
- **Mantids and solifuges:** the folded front scythes and the forward pincer jaws (C).
