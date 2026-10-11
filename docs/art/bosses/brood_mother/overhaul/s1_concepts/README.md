# Brood Mother redesign, session 1 (take 3): three proportion studies

The brief (2026-10-10):
- the **vanilla spider**, buffed and mutated;
- **long predator legs** with several joints;
- on her back, a **mountain of melted wax and lit candles**;
- no mask; **large mandibles**.

Take 1 (a villager mask and cocoons) was dropped. Take 2 had a small body on stilts and a wax tower. Both stay in git
history.

Take 3 copies a real spider's threat:
- **The body:** low and heavy, with the big head carried low and a fat abdomen raised behind.
- **The legs:** they arch high over her back, then reach far out and down, so she crouches inside a cage of her own
  legs. The front legs are the longest and turn forward; the back legs turn back.
- **The wax:** heaped on the abdomen as a cluster of rounded lumps. Thick flows run down her flanks with thin drips
  between them, and candles stand in clusters, the tallest on the highest lump.

These are flat-colour blockouts. Textures and the candle glow come in later sessions.

![Three studies: front, side, three-quarter](compare.png)
![Material zones: front, three-quarter, side](compare_material.png)

| | Study | Build | Size (w x h x d) |
|---|---|---|---|
| A | **Huntress** | a wolf spider: balanced and low, with thick legs of middle length | 6.8 x 4.1 x 6.0 blocks |
| B | **Brute** | a tarantula: the heaviest body and abdomen, shorter, thicker legs and the biggest wax load | 6.6 x 4.7 x 6.3 |
| C | **Stalker** | a huntsman: a flatter body on very long legs, with the knees far above her back | 7.5 x 3.7 x 6.7 |

Sheets per study: [A](A/sheet.png), [B](B/sheet.png), [C](C/sheet.png). Regenerate:
`python tools/art/bosses/brood_s1.py`.

## What all three share

- **The vanilla spider underneath:**
  - the square head with the vanilla red eye pattern, a thorax and a boxy abdomen;
  - mutated: a muscle-swollen thorax, extra eyes down one cheek, a bulging abdomen with split flank plates.
- **Legs:** six segments each (coxa, femur, patella, tibia, metatarsus, tarsus), tapering from a thick femur to a thin
  foot.
- **Jaws:** big mandibles reaching forward and curling in like pincers, with teeth and a hooked fang. Short pedipalps
  sit beside them.
- **Candles:** every candle is its own bone, and every flame a `glow_` bone, ready for full-bright and a flicker.

## Inspirations

- **Body plan:** the vanilla spider.
- **Proportions:** a wolf spider (A), a tarantula (B) and a huntsman (C).
- **The wax:** harvestman-like knees framing the pile, and candle and wax golems: wax heaped into a body, with drips
  everywhere.
