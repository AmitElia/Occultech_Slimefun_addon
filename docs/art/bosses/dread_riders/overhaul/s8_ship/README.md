# Dread Riders, session 8: shipped

Made by `python tools/art/bosses/dread_ship.py`, after `dread_s7.py`. The fight is `boss/tier3/DreadRiders.java`.

## In the fight

**Four models, one boss.** The riders are the fight's two main bosses, and the horses are lookalikes:

| Mythic mob | Wears | Carrier |
|---|---|---|
| `OCCULTECH_DREAD_RIDERS_VANGUARD` | `occultech_dread_riders_vanguard` | an invisible zombie, empty-handed |
| `OCCULTECH_DREAD_RIDERS_OUTRIDER` | `occultech_dread_riders_outrider` | an invisible skeleton, empty-handed |
| `OCCULTECH_DREAD_RIDERS_VANGUARD_MOUNT` | `occultech_dread_riders_vanguard_mount` | an invisible pig (draws nothing) |
| `OCCULTECH_DREAD_RIDERS_OUTRIDER_MOUNT` | `occultech_dread_riders_outrider_mount` | an invisible pig |

Without Mythic, the fight keeps its vanilla look: skeleton and zombie horses, and the riders' bows, spears and helmets.

**Riders in the saddle:**
- **Seat:** each rider rides its pig at the vanilla seat (2.7 units up, the Tidebreaker's measured value), and its model
  is moved from there to the saddle (3.3 blocks up).
- **Facing:** a rider's body keeps its horse's yaw, so it never spins in the saddle. Only its head follows the target,
  within 55°.
- **Hitbox:** it runs from the ground to the helm, so a swing at the horse's body reaches the rider. The horses have
  no hitbox and can't be hurt.

**Clips, with the same name on rider and horse:**

| What happens in the fight | Clip played |
|---|---|
| The ritual arrival | `spawn` on all four |
| Moving | `gallop` (each body's walk state is swapped to the gallop on spawn) |
| The charge's warning | `rear` |
| The 25-tick charge | `charge` |
| A charge cut short | `stunned` |
| The aimed shot | the Outrider's `draw`; its horse plays `halt`, then paws |
| The moving snipes | the Outrider's `snipe` |
| The volleys | `volley` |
| The arrow rain | `rain` |
| Melee | `sweep` |
| The enraged spear | `throw` |
| A hit | `flinch` |

The nocked arrow shows from the draw until the loose.

**Contacts:** the hits land on the clips:
- the volley's arrows 8 ticks in;
- the melee 7 ticks in, still within 4 blocks;
- the thrown spear 11 ticks in;
- the snipes as before (40 and 30 ticks, matching the draw and the snipe).

**From the hands:** the snipe's line and the volley's arrows leave the bow tip, and the spear leaves the raised hand,
not the carrier's eyes.

**Tints** (session 6):

| Pair | States |
|---|---|
| Vanguard | calm, tell (rear and charge), stunned (2 s, then back), enraged |
| Outrider | calm, lock (the aimed shot), enraged |

- **The enrage:** the survivor takes the fallen rider's colour, and keeps it as its new base.
- **After a hit flash:** the state tint is put back 12 ticks after a hit.

**Death:** the rider and its horse play the death clip on stand-ins, with their glows dark, and the horse goes with
its rider.

## Files

- **Models:** the four `src/main/models/occultech_dread_riders_*.bbmodel`.
- **Mythic:** `src/main/mythic/Mobs/DreadRiders.yml` and `Skills/DreadRiders.yml`, generated. They are look and sound
  only; every hit is the fight's.
- **Installer:** `MythicPackInstaller` lists both Mythic files and the four models.

## Tests and pack

- **Unit tests:** pass.
- **Self-test** with MythicMobs and BetterModel on test server b: **583 passed, 0 failed**. The first run had the known
  crash-ritual flake, which passed on the rerun.
  - The four Mythic bodies were used: no "definition missing" warning.
  - Both riders ride their horses.
- **BetterModel** built the four models on b (426 files).
- **Pack:** sha1 `f9717c70`, published to the local pack clone `occultech_texture_pack_v1.0` (you push it). The jar
  with that pack is in `run/plugins` and on b. The review rigs are gone from `run/plugins/BetterModel/models`.

## Not tried yet: check in a real fight

Nothing has been fought with a player. Things only a played fight shows:

- **The seat.** 2.7 units is the drowned-on-pig value. If a rider floats above its saddle or sinks into it, measure it
  and change `PIG_SEAT` in `dread_ship.py`.
- **Which side is the model's right.** The bow-tip and spear-hand points assume Blockbench +x is the model's right. If
  the arrows leave the wrong side, flip the sign of `right` in `DreadRiders.modelPoint`.
- **Layering.** The rider-only attacks animate only the torso, arms and weapons. Check whether BetterModel plays them
  over the gallop, or whether the rider's bob pauses during an attack.
- **The pig's speed** carrying a 3.3-block horse: the gallop's stride is timed to 0.3 to 0.34 blocks a tick.
- **The tints and the hit flash, the corpses, and the arrow showing and hiding.**
