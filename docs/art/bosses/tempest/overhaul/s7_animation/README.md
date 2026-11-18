# Tempest, session 7: animation

Script: `tools/art/bosses/tempest_s7.py <client assets folder>` (after `tempest_s6.py`). Output: `occultech_tempest_rig.bbmodel`
with ten clips (copied to `run/` and `run-mythic-b`), [keyframes.png](keyframes.png), a GIF per clip in [gifs/](gifs/),
[clips.json](clips.json).

Each clip is a few of session 2's whole poses at key times, plus small additive moves. Keys are deltas from the bind pose
(the whole seal), so whenever a clip returns a shard to its true place it returns to exactly zero. The whirl of arms and
the twister's bands spin with continuous linear keys at thirds, so no step passes 180 degrees (the Unbound lesson).
Scale keys carry the whirl's and the twister's size changes.

| Clip | Length | Type | What happens | Contact |
|---|---|---|---|---|
| idle | 4.0 s | loop | the frozen blast breathing: the arms whirl a full turn, the twister spins the other way, the shards drift out of step, the head bobs, the blown tip wobbles | |
| squall | 2.0 s | loop | while the squall ring closes in: idle at double speed, bigger drift | |
| spawn | 2.6 s | once | the seal comes through the circle **whole**, gathers, then cracks open into the frozen blast at 1.85 s | |
| volley | 1.4 s | once | the seal snaps together by 0.5 s, the charges leave through its cracks, then it flies apart again | **0.7 s** |
| burst | 1.2 s | hold | drawn in tight through the 1 s warning, flung out at the wind burst | **1.0 s** |
| spent | 1.5 s | hold | straight after the burst, everything drops to the floor and stays down: the opening | |
| recover | 0.8 s | once | the opening ends: the shards lift and are flung back out | |
| split | 2.4 s | once | below half: drawn in, then the seal breaks into two halves as the small gales join, then back | **1.0 s** |
| flinch | 0.4 s | once | hit: the head kicks back, the shards jolt | |
| death | 3.0 s | hold | a last flare outwards, then everything falls | |

All clips but idle and squall are `override`.

**Load test (server b, 2026-11-17):** the animated rig loaded with no errors. BetterModel built it into its pack, and the
server then stopped cleanly. The clips haven't been played in a real client yet:
`/bm test occultech_tempest_rig <clip>` on your server.

**Floor check** (every 1/20 s of every clip): nothing goes below the floor, except in death. There, one shard's corner
grazes 1.5 units (under a tenth of a block) under it for a moment mid-fall, because the fall interpolates rotation and
position separately. The end pose rests above the floor. Death uses linear keys, so it can't overshoot.

## For session 8 (the fight code)

- **Gust volley:** start `volley` and the volley tell tint, then launch the three charges 0.7 s later (Tempest.java fires
  them at once today).
- **Wind burst:** play `burst` when the warning circle appears. The burst lands at 1.0 s, which matches the existing
  20-tick telegraph.
- **Spent and recover:** play `spent` when the burst lands, with the spent tint. When `spentUntil` ends, play `recover` and
  the calm tint.
- **Squall:** `squall` replaces idle while the ring closes.
- **Split:** play `split` at the enrage, with the adds spawning at 1.0 s, then the storm tint for the rest of the fight.
