# The Night Matriarch redesign, session 5: texture painting

The session 4 layout painted: the same 256x256 atlas and islands, with fine ramps (close shades, cool darks, lighter
highlights) so the detail stays subtle. The shading is ambient occlusion baked from the real geometry; there's no
painted light direction.

![Painted: hero, front, from above, side, her head, a wing, the tail, the open flank, and gliding from a player's eye](sheet.png)

- **Hide:** vanilla's phantom blue-grey, mottled and leathery, with creases and the tops of masses catching the light.
  The underside is paler and banded like the phantom's.
- **The split down her head:** where the hide gives way to bare skull, it is torn, with a ragged dark edge and raw
  flesh along it.
- **Sculk** (the user: mostly texture):
  - **Where:** dark teal blotches spread over her hide and the roots of her wings, flecked with points of cyan light.
    It is heavier on her rotten left side and her back. It creeps onto her skull and ribs only sparingly.
  - **How:** the blotches are drawn from smooth noise in world space, so they run across cube edges instead of
    stopping at them.
- **Bone:** old and yellowed, pitted and cracked, with a suture down her bare forehead.
- **Rotten flesh:** inside the open flank, dark and sinewed, with wet glints between the ribs.
- **Wings:** dark membrane with paler veins fanning from the shoulder.
  - **Tears** (the user: in the texture, not missing blocks): ragged holes and a torn trailing edge, cut out so the
    sky shows through. Where whole stretches are gone, the finger bones are left bare.
  - **Different per side:** each wing is torn its own way.
  - **Lined up:** a tear is placed by world position, so the same hole goes through the top, the bottom and the edges
    of a strip.
- **Owl's tail:** grey feathers with soft, wide bars across them like an owl's, darker at the tips, each feather's
  edge drawn so the fan reads. One feather is broken off partway.
- **Gills:** warden horns (see take 2 below). Each pair shares one horn, mirrored.
- **Glow:** the phantom's green eye with a pale core, and the sculk light deep in the empty socket.

**Take 2** (after the user's review: the tears looked too square, the tail was a different shade, there was barely
any sculk, and the head tendrils were the wrong colour and didn't look like sculk horns):
- **Wings filled in:** the tears are redone.
  - **Rips:** narrow ones running in from the trailing edge and tapering to a point, each leaning its own way.
  - **Punctures:** a few small ones.
  - **The edge:** a finely frayed trailing edge, every tear rimmed dark where it frays.
- **The tail:** in her hide's blue, a shade deeper, with sculk reaching onto it in patches.
- **Sculk all over her back:**
  - **Coverage:** anything facing up is taken: her body, head, wing roots and tail.
  - **Colours:** vanilla sculk's range, from black-blue at the heart of a patch through teal towards its edge.
  - **Veins:** pale veins run through the growth and creep out beyond it over the hide, like sculk veins.
  - **Light:** sparse points of cyan.
- **2D sculk growth:** nine tufts of sculk sensor tendrils across her back. Like vanilla's sculk sensor, each is two
  crossed flat planes with the tendrils cut out of the texture: thin dark teal stalks, swaying, each tipped with a
  glowing cyan point. They replace the blockout's box tendrils.
- **The head tendrils as warden horns:** each plane is now cut into a dark sculk blade.
  - **Shape:** broad at her head, tapering to a point that curls up, darkest at its edge.
  - **Glow:** a cyan core glows inside near the base, and fades out along the blade.

**In game:** the review rig on your server has the painted texture.

```
/bm reload
/bm test occultech_night_matriarch_rig glide
```

Regenerate with `python tools/art/bosses/matriarch_s5.py` (after `matriarch_s4.py`).
