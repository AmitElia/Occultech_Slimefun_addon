# Hollow Warlord, the Headsman: session 3 (rig and pose test)

Script: `tools/art/bosses/headsman_s3.py <client folder> [--no-server]`. On top of the session 2 design lock
([s2_design](../s2_design/README.md)), unchanged in look.

- **Review rig:** `occultech_hollow_warlord_rig.bbmodel` (here and in `run/plugins/BetterModel/models`), flat colours
  per material, the glows full-bright. Never shipped.
- **Poses as animations:** idle, walk, windup, sweep, enraged, death. Try one in game with
  `/bm test occultech_hollow_warlord_rig <pose>`. Position keys move the hips down (wide stances, kneeling), float the
  taken skulls to the head and settle the sword in the fist.
- **Not an animation channel:** the hat (hidden in the enraged pose) and the skulls' glow (dark at death) are hidden
  from the fight code in session 8, so in `/bm test` the hat stays on and the skulls stay lit.
- **Counts:** 135 cubes, 27 bones with cubes, **72 displays** (the torso's angled ribs are 31 of them; cutting that
  waits for the M6 pass over every boss), 0 flicker pairs after 31 nudges, longest cube 36 (the brand); the blade is two
  halves because an item model holds at most 48 units.
- **Checks:** no unintended BetterModel tags. Pivots flagged for a look: the pauldrons (their pivot is the shoulder
  joint, outside the plates, on purpose) and the glow bones (they never turn on their own).
- **Hitbox:** 4.9 x 5.5 x 2.5 blocks.
- **Load test:** built clean on server b (BetterModel 3.5.0 wrote 100 files for it); the rig was removed from b
  afterwards (b's build.zip keeps it until its next boot).

Report: [summary.json](summary.json), [report.json](report.json), [pivots.md](pivots.md).
