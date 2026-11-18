# Tempest, session 8: ship

Scripts: `tools/art/bosses/tempest_ship.py <client assets folder>` (after `tempest_s7.py`), `tools/art/bosses/tempest_gif.py`.

## What shipped

- **`src/main/models/occultech_tempest.bbmodel`:** the final rig, built from the session 7 clips and the session 6
  neutral glows. It has 290 elements, 10 clips and its hitbox. The ship script refuses to ship if any faces would flicker
  or any texel is half-clear.
- **`src/main/mythic/Mobs/Tempest.yml`, `Skills/Tempest.yml`:** look and sound only. Each skill is `TEMPEST_<ACTION>`:
  `VOLLEY`, `BURST`, `SPENT`, `RECOVER`, `SQUALL` / `SQUALL_END` (swap the default idle), `SPLIT`, `FLINCH`,
  `STATE_CALM|TELL|STORM|SPENT` (tints), and `DEATH`.
- **`MythicPackInstaller`:** both files and the model are on its fixed lists.

**The carrier is an invisible blaze, not a breeze.** The 26.2 client's `LivingEntityRenderer` draws every render layer
whatever the invisibility flag, and neither `BreezeWindLayer` nor `BreezeEyesLayer` checks it. So an invisible breeze
would still draw its wind and eyes under the model. That's the Illusioner lesson again, found before shipping this time.
The self-test checks for it.

## The fight (`Tempest.java`)

Without MythicMobs and BetterModel nothing changes: a great breeze with its own AI. With the model:

- **Carrier and steering:**
  - Unscaled, puppeted (no AI), floating 0.3 blocks over the floor.
  - Steered every tick to keep 7 blocks from its target, drifting slowly round it inside the arena.
  - Turned to face the target.
  - Holds still while winding up a burst and while spent.
- **Gust volley:**
  - `VOLLEY` plus the tell tint lock a target.
  - The three charges leave **0.7 s later** (the clip's contact), from the model's heart (4.5 blocks up, 1.6 blocks in
    front of the seal), not from the carrier's eye.
  - The state tint comes back when the clip ends.
- **Wind burst:** `BURST` starts with the warning circle. The burst lands on the existing 20-tick telegraph, which is the
  clip's contact.
- **Spent:** `SPENT` (dark heart, dimmed eyes) for the 30-tick opening, then `RECOVER` and the calm or storm tint.
- **Squall:** `SQUALL` swaps the idle for the faster squall loop while the ring closes, and `SQUALL_END` swaps it back.
- **Below half:** `SPLIT` breaks the seal in two, and the two small gales spawn 1.0 s later, on the split's contact.
  From then on the state tint is storm blue.
- **Flinch:** on a hit, only between attack clips and at most once in 15 ticks, so it never cuts a volley or a burst.
- **Hit flash:** the state tint is re-applied 12 ticks after a hit, because BetterModel's hit flash restores the tint it
  found.
- **Death:** the corpse stand-in plays the death clip with the heart, glyphs and eyes tinted out.

## Tests and pack

- **Unit tests:** pass.
- **Self-test** with MythicMobs and BetterModel on test server b: **577 passed, 0 failed**. That includes the two new
  Tempest checks: it wears the Shattered Seal once with its hitbox, and its carrier is an unscaled, invisible blaze.
- **Pack:** sha1 `d97837ba`, published to the local pack clone `occultech_texture_pack_v1.0` (you push it). The jar with
  that pack is in `run/plugins` and on b.
- **Not tried yet:** nothing has been fought with a player. Still to check in a real fight:
  - the volley's 0.7 s lead;
  - the steering and facing;
  - the spent and recover timing;
  - the split;
  - the corpse tint.

## The seal, broken to whole

[seal_gif/tempest_seal_broken_to_whole.gif](seal_gif/tempest_seal_broken_to_whole.gif):
- **What it shows:** the frozen blast snapping into the whole seal and breaking apart again.
- **How it's made:** the real painted model posed from the volley clip, each frame rendered with full texture and
  lighting in Blender.
- **Tint:** the glyphs ease from calm teal to the white tell as the seal locks.
- **Stills:** [broken.png](seal_gif/broken.png) and [whole.png](seal_gif/whole.png).
