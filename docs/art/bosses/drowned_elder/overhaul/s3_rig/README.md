# Drowned Elder, session 3: rig and pose test

Script: `tools/art/bosses/drowned_s3.py` (on top of `drowned_s2.py`, unchanged in look). Output:
`occultech_drowned_elder_rig.bbmodel` (a review model only, never shipped), [report.json](report.json),
[summary.json](summary.json), [pivots.md](pivots.md).

## In game

```
/bm test occultech_drowned_elder_rig idle
/bm test occultech_drowned_elder_rig aim
/bm test occultech_drowned_elder_rig stare
/bm test occultech_drowned_elder_rig dive
/bm test occultech_drowned_elder_rig emerge
/bm test occultech_drowned_elder_rig death
```

The rig is in both `run/plugins/BetterModel/models` (your server; restart it or run `bm reload`) and `run-mythic-b`. It
shows a flat colour per material, the eyes full-bright. Each pose is a held animation: joint rotations down the body
chain, a position key on `base` (the whole body moves onto the pose's curve) and scale keys on the hood's webs (they
stretch as the hood flares). Session 7 makes the real clips.

**Load test (server b, 2026-11-17):** BetterModel built all 43 bones that carry geometry into its pack (`build.zip`,
134 files); the four `ob_` hitbox bones built no item model, as hitboxes should. No errors in the log apart from
Windows' usual system-report noise. Server b was stopped cleanly. Not yet seen in a real client: the poses, and whether
the four hitboxes follow the body (that needs a player; session 8 also checks each hit lands once).

## Checks

| Check | Result |
|---|---|
| Cubes / bones with cubes | 120 / 43 |
| Displays (BetterModel item displays) | **90** |
| Flicker (faces sharing a plane) | 0, after 9 small resolver nudges |
| Longest cube | 48 units (the head), at the 48 limit |
| BetterModel tags | only `hi_head`, `glow_eye`, `glow_eye2/4/6`, `ob_head`, `ob_body0..2` |
| Hitboxes | head 3 x 3 x 3.4 blocks; body 1.9, 1.6 and 1.25 blocks (segments 3, 6, 9) |

**Pivots the check flags but that are right:**
- **`web0`..`web7`:** each turns from the head's back, between the roots of its two spikes (where the fin is attached),
  not from the web's own middle; that's what keeps a web between its spikes as the hood opens.
- **`glow_eye2/4/6`:** between the segment's two eyes; glow bones never turn on their own.

**Draw cost:** 90 displays, the lowest of the tier 2 bosses (Tempest 215, the Choir 517). Most segments cost 6 because
their shingles tilt at 7 and 14 degrees and the spikes lie on diagonals. As agreed, any cutting waits for the M6 pass
(snapping the shingle tilts to 0/22.5 would bring each segment to about 3).
