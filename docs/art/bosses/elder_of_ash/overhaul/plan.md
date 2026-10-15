# The Elder of Ash (was the Mire Monarch): the plan

Agreed direction (2026-10-14): a complete restart of the tier-0 gate boss as the **Volcano Toad**. Everything from the
earlier Monarch rounds (the slimes, the toxic toad, the Brute posture and its face study) is dropped. The id stays
`MIRE_MONARCH` (and `GELATINOUS_SOVEREIGN` keeps mapping to it via `core/BossIds`); the display name becomes **the
Elder of Ash** when the model ships.

## Identity

A giant elder toad sage, in the spirit of the toad sages from Naruto (never a copy), with a volcano growing out of
its back. The user's brief:
- **A giant elder toad**, crouched low so the volcano points straight up.
- **The toad sage face:** the heavy brow and the iconic wide frog face, old and calm.
- **A volcano growing out of its back.** The back turns from skin to mountain: olive-brown warty skin on the flanks,
  the warts hardening into ash-grey crust up the back, dark basalt at the cone, a jagged crater rim.
- **Colours:** brown, green and ash grey for the toad; a pale belly and throat.
- **Clear lava streams** flowing from the crater down the cone and over its sides: the boss's one living light.
- **A pipe in its mouth** with smoke coming out of it, echoing the volcano.
- **Smoke and explosions** from the crater, more when it is compressed (the leap's coil).
- No crown. No ritual rope.

**Vanilla ties:** the frog's eye placement, webbed feet and flat tongue; the temperate frog's orange-brown; basalt,
magma block and lava; the shards become vanilla magma cubes.

## The fight (numbers and timings unchanged)

| Moment | Server | Look |
|---|---|---|
| idle | - | still and heavy, slow breathing, the pipe smoking, a lazy plume from the crater |
| leap + shockwave | 1.5 s warning ring, then the leap; the landing wave only hurts grounded players | **the compressed pose**: he sinks onto his haunches, the cone rumbles, the smoke thickens and small explosions burst at the crater; he leaps; the landing throws ash and a ripple of cracked crust |
| tongue | a locked lane for 1.25 s, then the lash and the pull | the flat tongue with a hot tip; the lane in ember |
| split at 66% | 3 shards crawl back from the rim; each that arrives heals 6% | **the eruption**: the volcano throws 3 lava bombs that land at the arena's edge as small **magma cubes** and crawl back |
| 33% | faster, puddles that hurt | the cone **blows its top**: the crater cracks wider and never stops erupting; he leaves cooling **lava pools** instead of acid. No shrinking. |
| death | - | the volcano goes cold: the lava dims to grey crust, the smoke thins to one last wisp from the pipe |

The colours move from lime to tier 0's ember. The damage names change with the look (Acid -> Magma).

## Process

Session 1 in three gated steps:
1. **Silhouettes (2D):** how big the volcano is against the toad. A: the toad dominates (a hump). B: balanced. C: the
   mountain dominates. Side and front, silhouette and value, next to a player.
2. **Face study:** the sage's face with the pipe, three takes.
3. **Blockout:** the full figure from cuboids, clay renders from several angles.

Sessions 2-8 as in [boss-art-sessions.md](../../../../boss-art-sessions.md). For the Elder specifically:
- the lava is painted on glow parts; the crater and streams tint per state (idle, compressed, erupting, cold);
- smoke and explosions are particles from the crater's and the pipe bowl's real positions, scaled by state and capped;
  smoke rises, so floor warnings stay clear;
- the carrier must draw nothing when invisible (to check: an invisible slime, or another carrier).
