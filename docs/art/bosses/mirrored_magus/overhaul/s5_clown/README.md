# The Mirrored Magus redesign, session 5: the horror clown's face

The user rejected all three masks of the study ([../s5_masks](../s5_masks/README.md)): "much more pronounced,
detailed, and full of depth... focus on the face. It should be a horror clown face." So he has no mask: this is his
own face, a horror clown's, sculpted in depth out from the illager's head (`magus_s2.mask_clown`) and painted.

![The horror clown's face: front, three-quarter, side, from a player's eye, and on the whole figure](clown.png)

![His face](face.png)

**Sculpted:**
- **The brow:** heavy, pinched down in the middle into a glare.
- **The eyes:** deep sockets behind the brow.
- **The cheeks:** high cheekbones, with cheeks pushing up into the grin.
- **The nose:** a bulbous red clown's nose.
- **The muzzle:** a low muzzle under the nose that carries the painted grin.
- **The chin:** long and pointed.
- **The hair:** wild tufts sticking out from under his hat.

**Painted at a higher resolution:** his head, face and eyes are textured at 4 texels per model unit (64 per block, four
times the rest of him; `magus_s4.density`). This is a deliberate exception to the vanilla density, at the user's
request.
- **The greasepaint:** white and finely cracked, wrapping round his cheeks onto the sides of his head.
- **Black:** round his eyes, with a black diamond running down from each.
- **The grin:** smooth, thick red lips round an open, dark mouth stretched up into his cheeks.
  - **Teeth:** rows of pointed teeth along both lips, with gaps between them and longer fangs at the corners.
  - **Drips:** a thin red drip from each corner.
- **The eyes:** an illager's eyes, on the glow bone so they stare out full-bright from the black round them:
  - a pale white, faintly bloodshot;
  - a cyan iris;
  - a dark pupil looking a little inward.
- **The nose:** glossy red, with a highlight and a crack.

**Take 2** (after the user's notes: the smile was too blocky and busy, the eyes should be more human or illager-like,
the teeth looked weird, and the head's resolution should go up): the lips built cube by cube and the cube teeth were
replaced by the painted grin; the eyes became illager eyes; and the head got its higher resolution. 157 cubes.

Regenerate with `python tools/art/bosses/magus_clown.py`.
