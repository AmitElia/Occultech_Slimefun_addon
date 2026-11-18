# Tempest, session 1 step 3: the full blockout

Picked 2026-11-17: **C, the Frozen Blast** + **W3, the Full Storm** + **H2, the Seal Circlet** + **K3, the Cracked Heart**.
Script: `tools/art/bosses/tempest_blockout.py` (built from tempest_silhouettes, tempest_take2 and tempest_study).
Sheet: [blockout.png](blockout.png); each pose's renders are in its own folder.

| Pose | Fight moment | What it shows | Size (blocks) |
|---|---|---|---|
| idle | between attacks | seven shards frozen mid-blast, four wind arms carrying them, the twister under the core, the blown tip floating by the head | 8.4 x 8.8 x 4.9 |
| locked | gust volley | the seal snapped whole behind the core, arms wound tight, the tip pulled close | 5.6 x 8.0 x 3.7 |
| burst | wind burst | shards and arms flung to their widest (the arm tips spread along the floor), seams wider, head thrown back | 11.2 x 10.0 x 4.9 |
| spent | the 1.5 s opening | every shard down on the floor, arms limp, the twister a spout, the heart dark, the head bowed | 7.4 x 7.6 x 3.8 |

About 280 cubes. Every pose stays above the floor: shards, the funnel and the blown tip are rested on it.

Fixed in self-review: the burst and spent shards sank up to 2.5 blocks through the floor, so they now rest on it. The idle
and spent arms filled the front silhouette and hid the core, so they are shorter and slimmer, and only the burst throws
them wide. Spent shards that hung in the air made a blob; now they all lie on the floor.

Known, for session 2 (design lock): the twister's top lip sits like a shelf under the core in the three-quarter view, so it
should whip thinner and curl up. The idle front silhouette is dense: it's a storm, but session 2 can open gaps between
arm and shard so the starburst reads again.
