# Hollow Warlord, the Headsman: session 8 (ship)

Script: `tools/art/bosses/headsman_ship.py <client assets folder>` (after `headsman_s7.py`). Lit previews of every
clip: [../s7_animation/lit/](../s7_animation/lit/).

## What shipped

- **`src/main/models/occultech_hollow_warlord.bbmodel`:** the final rig from the session 7 clips with the session 6
  neutral glows: 135 elements, 11 clips, one hitbox. The skulls' glow bones are renamed `glow_soul_c` / `_l` / `_r`
  (BetterModel drops the `glow_` tag from a bone's name, so `glow_skull_c` would have matched the skull bone `skull_c`
  and a tint would have darkened the whole skull). The ship script refuses to ship if any faces would flicker or any
  texel is half-clear.
- **`src/main/mythic/Mobs/HollowWarlord.yml`, `Skills/HollowWarlord.yml`:** look and sound only. Each skill is
  `HOLLOW_WARLORD_<ACTION>`: `CALM` / `TELL` / `ENRAGED` (his eyes and the brand), `SOUL_C_LIT` / `SOUL_C_DARK` and the
  same for L and R (each skull's fire), `WINDUP`, `SWEEP`, `ATTACK`, `CALL`, `ENRAGE` (also swaps the idle for
  `idle_enraged`), `FLINCH`, `DEATH`. Every tint is applied twice, 12 ticks apart, so a hit flash can't undo it.
- **`boss/tier3/HollowWarlordRig.java` (generated):** where the model's parts are, in blocks from the carrier's feet:
  the blade's end at the chop's contact (5.6 blocks ahead), at the call's plant and at the enrage's slam, and each
  skull in the idle.
- **`MythicPackInstaller`:** both files and the model are on its fixed lists.

## The fight (`HollowWarlord.java`)

Without MythicMobs and BetterModel nothing changes: a 1.8x wither skeleton in netherite. With the model:

- **Carrier:** an unscaled, invisible wither skeleton that holds and wears nothing (any item would show through the
  model). Its vanilla melee is off: he hits from his own reach.
- **Gaze and movement, driven every tick:** body and head turned to his target; he walks up to 3.6 blocks from it at
  the walk clip's pace (0.26, up to 30% faster as he weakens) and stands still while any clip plays.
- **The chop (new melee):** within 5 blocks he raises the sword into the high guard (`ATTACK`); the facing locks as it
  starts and the blade comes down 14 ticks (0.72 s) later on a strip of floor 6.2 blocks long and 2.6 wide in front of
  him (46 damage, a short shove). Blackstone chips and soul fire burst where the blade's end bites, cracks of soul
  light along the strip. One every 2.2 s (1.7 s enraged).
- **Soul sweep:** the ring's warning is the windup clip (20 ticks, his eyes and brand flare to the tell); the sweep clip
  then cuts on its contact 6 ticks in, so the damage lands 26 ticks after the warning appears. It waits for a call or
  the enrage to finish rather than cutting into them.
- **Warband:** each guard is bound to one skull: the skull's fire burns while its guard stands and goes dark when it
  falls. Every 25 s `CALL` drives the sword into the floor; the guards rise 0.9 s in, with soul fire round the planted
  blade. The soul chains now run from each skull to its own guard, and the halo sits over the skulls.
- **Enrage (below 35%):** `ENRAGE` once he's free; on the slam (1.05 s) blackstone and soul fire burst where the blade
  goes in (look only, no damage); from then his eyes and brand burn white-hot and he idles in the low guard with the
  skulls circling.
- **Flinch:** on a hit, only between clips and at most once a second. **Hit flash:** every tint is put back 12 ticks
  after a hit.
- **Death:** the corpse stand-in plays the death clip with every fire out.

## Tests and pack

- **Unit tests:** pass.
- **Self-test** with MythicMobs and BetterModel on test server b: **581 passed, 0 failed**, with two new checks: the
  Warlord wears the Headsman once with its hitbox; its carrier is an unscaled, invisible wither skeleton holding and
  wearing nothing. (One run in between failed the known crash-mid-ritual flake twice; the rerun passed.)
- **Pack:** sha1 `2920b3de`, published to the local pack clone `occultech_texture_pack_v1.0` (you push it). The jar with
  that pack is in `run/plugins` and on b. The review rig is gone from both servers.

## Not tried yet: check in a real fight

Nothing has been fought with a player. Things only a played fight shows:

- **Which side is the model's right.** The rig table assumes Blockbench +x is his right (as the earlier bosses). If the
  chop's sparks or the chains leave from the wrong side, flip the sign of `right` in `HollowWarlord.point`.
- **The chop's strip.** It follows the blade (5.6 blocks); check it feels fair at the 3.6-block standing distance.
- **The walk's pace** against the 1.6 s stride (feet sliding means the speed needs a nudge).
- **Clip blends** between the walk and the clips, and between `idle_enraged` and the walk.
