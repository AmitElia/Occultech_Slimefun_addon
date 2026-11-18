# Tempest, session 3: rig and pose test

Script: `tools/art/bosses/tempest_s3.py` (on top of `tempest_s2.py`, unchanged in look). Output: `occultech_tempest_rig.bbmodel`
(a review model only, never shipped), [report.json](report.json), [summary.json](summary.json), [pivots.md](pivots.md).

## In game

```
/bm test occultech_tempest_rig idle
/bm test occultech_tempest_rig locked
/bm test occultech_tempest_rig burst
/bm test occultech_tempest_rig spent
/bm test occultech_tempest_rig split
/bm test occultech_tempest_rig death
```

The rig is in both `run/plugins/BetterModel/models` (your server) and `run-mythic-b`. It shows flat colour per material:
- **Full-bright:** the heart, the glyphs and the eyes.
- **Clips:** six held poses as animations, with **scale keys** where a pose scales a bone (the arms' whirl and the twister).
  Session 7 makes the real clips.

**Load test (server b, 2026-11-17):** BetterModel built every one of the 39 bones that carry geometry into its pack
(`build.zip`, 255 Tempest files). The log has no errors apart from Windows' usual perf-counter noise. Server b was then
stopped cleanly. The poses haven't been looked at in a real client yet.

## Checks

| Check | Result |
|---|---|
| Cubes / bones with cubes | 286 / 39 |
| Displays (BetterModel item displays) | **215** |
| Flicker (faces sharing a plane) | 0, after 99 small resolver nudges |
| Longest cube | 40 units (the visor band), under the 48 limit |
| BetterModel tags | only `hi_head`, `glow_*`, `ob_hitbox` |
| Hitbox | 2.5 x 6.5 x 2.5 blocks |

**Pivots the check flags but that are right:**
- **`ribbon0`..`ribbon3`:** on the twister's axis at the floor, so each band spins round the funnel.
- **`rods`:** on the axis too.
- **`circlet`:** at its ring's centre.
- **Glow bones:** never turn on their own.

**Draw cost:** 215 displays is high. Most come from the twister's bands (16 each) and the seal's tiles (11-12 per shard),
because every board turns at its own angle. As agreed, cutting it waits for the M6 pass over all bosses, not this one.
The obvious levers are fewer, longer twister boards and the seal's tiles snapped to 22.5-degree steps.
