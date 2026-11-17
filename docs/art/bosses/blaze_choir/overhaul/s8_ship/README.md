# The Blaze Choir, session 8: ship

Made by `python tools/art/bosses/choir_ship.py` (after `choir_s7.py`).

## In the fight

- **Three bodies.** Each singer is a Mythic carrier, an invisible blaze, wearing its own model:
  `OCCULTECH_BLAZE_CHOIR_SOPRANO`, `_ALTO` and `_BASS`. The models are drawn at their own size, so the carriers are
  unscaled; a plain blaze without the model is still grown 1.5 times.
- **They fly lower:** 1 block over the altar instead of 2.5, so the tall instruments stay in reach. The bell's lip
  clears the floor when it swings.
- **The strike lands on the beat.** The `strike` clip starts on the singer's beat and the fireball leaves its mouth
  10 ticks later, on the strike. Each singer has its own strike sound: chime, cymbal, bell.
- **The shield** closes the instrument (`shield`, held) and banks its fire. When it moves on, the old holder plays
  `unshield`. The vanilla glow outline is used only without a model, since it would draw the hidden carrier's shape.
- **The chorus** clip starts with the 1.5 s flame-circle warning and peaks at the eruption.
- **A voice falls:** the survivors burn hotter. The last singer swaps its idle for `last` and burns hottest.
- **Hit:** `flinch`. **Death:** the model stays as a stand-in for its whole death clip, its fire out.

## Files

- `src/main/models/occultech_blaze_choir_{soprano,alto,bass}.bbmodel`
- `src/main/mythic/Mobs/BlazeChoir.yml`, `src/main/mythic/Skills/BlazeChoir.yml`, both in `MythicPackInstaller`'s lists
- `BlazeChoir.java`; the self-test now checks that each singer wears its own model, unscaled, and flies at least 0.3
  blocks up (it was 1, the old height).

## Checked

Unit tests pass. Self-test with MythicMobs and BetterModel on test server b: 575 passed, 0 failed. A first run had the
known crash-test ritual flake (2 failures) and passed on a rerun. Pack sha1 8be702a4, published to the local pack clone;
the jar is in `run/plugins` and on b. Nothing has been fought with a player yet: the strike timing, the shield, the
heights and the sounds need a real fight.
