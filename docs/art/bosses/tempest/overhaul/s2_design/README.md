# Tempest, session 2: design lock

Script: `tools/art/bosses/tempest_s2.py`. Outputs: [design.png](design.png) (idle, four views), [poses.png](poses.png) (six key
moments, three-quarter and front), `design/occultech_tempest_blockout.bbmodel`, [parts.md](parts.md), [stats.json](stats.json).

## The rig, `occultech_tempest`

286 cubes on whole texels, 43 bones (39 carry geometry), about 5.7 x 8.0 x 4.7 blocks in the bind pose.

```
base (the core's centre)
  funnel > ribbon0..ribbon3 (the twister's bands, each can spin), rods (three breeze rods)
  core (on its corner) > glow_heart (the light inside), tip (the blown-off top block)
  hi_head (the breeze head) > glow_eyes, circlet > glow_circlet, circlet_chunk
  seal (stood up behind the core) > shard0..shard6 > glow_shard0..glow_shard6
  arms (spins in the seal's plane) > arm0..arm3 > armN_mid > armN_end (a chain each, so it can curl)
```

- **The bind pose is the whole seal.** Every shard sits in its true place, so the volley's "snap together" sends every
  shard bone back to zero and nothing can drift. Every other moment moves the shards out from there.
- **Glow bones** (`glow_heart`, `glow_eyes`, `glow_circlet`, `glow_shardN`) are kept apart so session 6 can tint and dim
  them: the heart goes dark when spent, and the glyphs die with it.
- **Hitbox** (`ob_hitbox`): 2.5 x 6.5 x 2.5 blocks round the head, the heart and the twister's throat. It doesn't cover the
  shards or the arms, so nothing decorative becomes a target.
- No bone name carries a stray BetterModel tag: only `hi_head`, `glow_*` and `ob_hitbox` do.

## Key moments ([poses.png](poses.png))

| Pose | Fight moment (Tempest.java) | How the rig gets there |
|---|---|---|
| idle | between attacks | shards thrown out (the frozen blast), the arms ending at them |
| locked | gust volley | shards back to zero, arms wound tight (+18 per joint, 0.78 scale), the tip pulled close |
| burst | wind burst | shards to their widest, arms opened and riding up, head thrown back |
| spent | the 1.5 s opening | every shard on the floor, arms limp, the twister half size, the heart and glyphs dark, head bowed |
| split | below half: the two small gales join | the seal breaks into two halves that swing off left and right |
| death | death | everything down: shards flat, the core and head on the pile, the twister a stub |

Every pose stays above the floor: shards, tip, core, head and the twister rest on it.

## Session 1 notes, fixed

- **The twister's lip** used to sit like a shelf under the core. Now each band thickens up the funnel, then whips thin and
  flicks up at the lip. A first try that curled the whole top quarter stacked into a drum and was dropped.
- **The idle front:** the arms now end at the shards (the shards ride their tips) instead of reaching past them.

## Tooling

`bosskit/bbmodel.py`: a group can carry a `scale` for pose previews only (an animation's scale key). It is never
exported, and nothing changes for other bosses.
