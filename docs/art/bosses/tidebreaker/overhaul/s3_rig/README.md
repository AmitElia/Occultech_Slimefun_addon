# The Tidebreaker, session 3: rig and pose test

Made by `python tools/art/bosses/tide_s3.py <folder with the 26.2 zombie textures>`.

Two review models with flat material colours (the lantern full-bright) and the seven key poses as animations. They are
in `run/plugins/BetterModel/models` and are never shipped.

| Model | Cubes | Bones with cubes | Displays | Flicker pairs | Unintended tags |
|---|---|---|---|---|---|
| `occultech_tidebreaker_mount_rig` | 405 | 52 | 197 | 0 | none |
| `occultech_tidebreaker_rig` | 209 | 14 | 53 | 0 | none |

**In game** (poses: `idle`, `glide`, `ram`, `winded`, `throw`, `thrust`, `death`):

```
/bm test occultech_tidebreaker_mount_rig ram
/bm test occultech_tidebreaker_rig ram
```

The two are separate models here, so `/bm test` won't stand him on the deck. The poses with him on the deck are in
[session 2](../s2_design/poses.png). Lining them up is session 8.

## Checked

- Both models built on test server b with no BetterModel errors: 52 item models for the mount, 14 for the rider. The
  server had no player online, so **the animations have not been seen in game**.
- The spear's shaft is two cubes, so no cube is longer than the 48-unit limit (the longest is 45).
- Pivots: `shell`, `hull`, `flesh` and `figurehead` have their pivot in the coil on purpose, since they never move on
  their own and only follow `base`. `figure_jaw` and `glow_lantern` were flagged as well, and neither is posed.

## Cost

250 displays together. The most expensive are `shell` (68), `hull` (64) and `figure_upper` (15): round shapes and the
longship's curved planks have many different angles. As agreed, the cost isn't cut per boss; that is the M6 pass.
