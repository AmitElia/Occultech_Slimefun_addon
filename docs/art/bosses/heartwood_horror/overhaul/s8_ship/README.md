# Heartwood Horror, the Crutch: session 8 (ship)

Script: `tools/art/bosses/heartwood_ship.py <client assets folder>` (after `heartwood_s7.py`). Lit previews of every
clip: [../s7_animation/lit/](../s7_animation/lit/). Showcase: [../s7_animation/heartwood_showcase.gif](../s7_animation/heartwood_showcase.gif).

## What shipped

- **`src/main/models/occultech_heartwood_horror.bbmodel`:** the final rig with the twelve session 7 clips and the
  session 6 neutral glows: 307 elements, 91 bones, one hitbox.
  - Three glow bones are renamed so that a tint can't hit the solid part of the same name (BetterModel drops the
    `glow_` and `hi_` tags from a bone's name): `glow_lantern` is now `glow_heartlight`, `glow_womb` is
    `glow_chamber`, `glow_sleeper` is `glow_eyelids`.
  - The script refuses to ship if any faces would flicker, if two bone names clash once their tags are dropped, or if
    a half-clear texel sits on any face but the resin shell's. The resin is the one deliberate exception (4185 texels,
    all on the shell): the user asked for transparent resin, and the client sorts translucent item faces back to front.
- **`src/main/mythic/Mobs/HeartwoodHorror.yml`, `Skills/HeartwoodHorror.yml`:** look and sound only. Each skill is
  `HEARTWOOD_HORROR_<ACTION>`:
  - the states `CALM`, `VULNERABLE`, `OUT`, `DEAD` tint the fifteen bloom bones, the lantern's light, the sleeper's
    eyelids and the chamber behind the resin (each applied twice, 12 ticks apart, so a hit flash can't undo it);
  - the moves `SPAWN` (its lights come on as it rises), `SWIPE`, `LUNGE`, `ERUPTION`, `SAP`, `SLAM`, `CREAK` (goes
    dark), `TWITCH`, `STAGGER` (vulnerable: the sleeper's eyes open, the blooms go red), `DEATH`.
- **`boss/tier3/HeartwoodHorrorRig.java` (generated):** where the hands, the womb and the lantern are, in blocks from
  the carrier's feet, and when the hands really land. Follow-through lands a hand a little after its key, so the
  script finds the moment each hand reaches the floor: the swipe 0.6 s, the eruption's dig 0.6 s, the slam 1.575 s.
- **`MythicPackInstaller`:** both files and the model are on its fixed lists.

## The fight (`HeartwoodHorror.java`)

Without MythicMobs and BetterModel nothing changes: a 1.6x creaking that stalks and strikes as before. With the model:

- **Carrier:** an unscaled, invisible creaking. The 26.2 client skips the creaking's glowing eyes when it is invisible
  (checked in `LivingEntityEmissiveLayer`), so only the model shows.
- **Gaze and movement, driven every tick:** body and head turned to its target, yaw only, so the lantern (a head bone)
  hangs level. It walks to 5 blocks from its target at the walk clip's stride (0.08 blocks a tick) and stands still
  while any clip plays. It re-picks its target every 8 to 11 s: the top damager half the time, else the nearest.
- **One move at a time:** each move's timer makes it due, and it starts once nothing is playing. The order is stagger,
  creak, slam, eruption, sap, swipe. The thorns from the hearts stay on their own timer.
- **Swipe:** at 2.5 to 8 blocks it turns so the great hand (which lands 6.7 blocks ahead and 1.7 to its right) comes
  down on the target, and locks that facing. 0.6 s later everyone within 2.6 blocks of where the hand lands is hit
  (47 damage, a small shove), with bark and root chips flying.
- **Root eruption:** it faces its target, plays `ERUPTION`, and the hands bite into the floor at 0.6 s. The three lanes
  are the same 30-tick warning as before and burst on the clip's wrench (1.5 s).
- **Sap rain:** `SAP` rears it with the womb lifted. The sap falls on the marked spots at 1.75 s, as before, with amber
  bursting from the womb.
- **Ground slam:** the ring is now centred where the crutch and the great hand land (about 6.4 blocks ahead) instead of
  on the boss. Its warning lasts until they land (32 ticks); the roots erupt there.
- **Creak:** `CREAK` plays over the old 20-tick warning, with every light going out. Then it arrives behind its prey,
  lunges, and the stab lands 0.3 s later on anyone within 2.4 blocks of the hand. The stab reaches 5.6 blocks, so
  the arrival spot is set by the hand, not the old 1.8 blocks behind. Two fallbacks:
  - when there's no room behind (outside the circle or inside a block), it comes from the circle's middle;
  - failing that, it strikes from where it stood.
- **Hearts:** each broken heart plays `TWITCH` (if no clip is playing; otherwise just its sound), with amber sparks
  at the lantern. The last one tints it `VULNERABLE` and plays `STAGGER`, waiting for the current clip if one is
  playing. When the window closes the hearts regrow and it's tinted `CALM` again.
- **Hit flash:** the state tint is put back 12 ticks after a hit.
- **Death:** the corpse stand-in plays the death clip with every light dark.

## Tests and pack

- **Unit tests:** pass.
- **Self-test** with MythicMobs and BetterModel on test server b: **583 passed, 0 failed**. It has two new checks:
  - the Horror wears the Crutch once, with its hitbox;
  - its carrier is an unscaled, invisible creaking.
- **Load:** BetterModel 3.5.0 built the model on b clean (185 files).
- **Pack:** sha1 `729cb80d`, published to the local pack clone `occultech_texture_pack_v1.0` (you push it). The jar
  with that pack is in `run/plugins` and on b. The session 7 review rig is gone from `run/plugins/BetterModel/models`.

## Not tried yet: check in a real fight

Nothing has been fought with a player. Things only a played fight shows:

- **The translucent resin.** Whether the client sorts it cleanly against the sleeper and the chamber from every angle
  as the model moves. If parts behind it vanish, the fallback is fully clear windows with opaque resin ribs.
- **Which side is the model's right.** The rig table assumes Blockbench +x is its right, as for the earlier bosses. If
  the swipe lands on the wrong side of the target, flip the sign of `right` in `HeartwoodHorror.point` and `behind`.
- **The swipe's aim** at the standing distance, and whether 2.6 blocks round the hand feels fair.
- **The creak's arrival:** it now stands about 5 blocks behind its prey; check it reads as "from behind you".
- **The walk's pace** against the stride: if the feet slide, nudge `MODEL_SPEED`.
- **Clip blends** between the walk and the moves, and the lantern's pendulum on the head bone.
