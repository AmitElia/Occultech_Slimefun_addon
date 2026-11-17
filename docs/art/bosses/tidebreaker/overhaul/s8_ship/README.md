# The Tidebreaker, session 8: shipped

Made by `python tools/art/bosses/tide_ship.py 2.7 <folder with the 26.2 zombie textures>`, after `tide_s7.py`. The 2.7 is
the rider's measured seat above the carrier, in model units.

## In the fight

- **Two models, one boss.** `occultech_tidebreaker` is on the drowned, the only thing that can be hurt.
  `occultech_tidebreaker_mount` is on an invisible pig, and has no hitbox, so it can't catch swings aimed at him.
- **He stays on the deck.** He rides at the seat and the model is moved from there to the deck. His body keeps the ship's
  yaw, and only his head follows the target (within 55 degrees).
- **The bow leads.** The ship faces along the charge during the warning and the ram.
- **Clips play on both models** together. The lantern tints run from the fight: calm, blue during the ram, guttering when
  winded.
- **The bob** is done by moving the entity, so he and the ship rise and fall together.
- **Timing:** the volley leaves his hand 0.7 s into the throw and the jab lands 0.25 s in. Damage used to land at once.
- **Death:** both models play it as stand-ins, the lantern out.

## The bow wave

While he moves, water peels off both sides of the prow in a V that widens back along the hull:

- **Foam** low on the ground (fishing wake particles).
- **Spray** over it (splash).
- **Mist** drifting outward (cloud).
- **Steam** off the stem (white smoke).

It grows with speed. The ram throws a wall of spray over the prow, with rushing water sounds, and when the charge stops
the wave breaks over the bow.

## Checked

Self-test on the test server with MythicMobs and BetterModel. Unit tests pass. Nothing has been fought in game with a
player, so the bow wave's look, the alignment on the deck and the clips in play still need a real fight.

## Test notes

Test server b's world had been left on Peaceful, where no hostile carrier can spawn. `difficulty normal` fixed it.
