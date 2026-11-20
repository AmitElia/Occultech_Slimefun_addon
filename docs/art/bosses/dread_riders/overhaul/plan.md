# Dread Riders overhaul plan

The 8-session plan from [docs/boss-art-sessions.md](../../../../boss-art-sessions.md). Mechanics and name are set
(`boss/tier3/DreadRiders.java`); the look is new.

## Direction (restarted 2026-11-20)

The earlier rounds (Pestilence and War, [s1_blockout](s1_blockout/README.md) and [s1_round2](s1_round2/README.md)) are
set aside; nothing from them carries over. The user's brief for the restart:

- **The warhorses are the main focus, and they are large.** References: a fully barded, spiked black charger with a
  banner behind the saddle, and an articulated bone horse with chunky bones and rope tack.
- **The riders' heads are vanilla's** (the zombie's and the skeleton's), under helmets that fit a **dark vanguard
  lancer** (the Vanguard) and a **cavalry archer-mage** (the Outrider).

## Progress

1. **Concept and silhouette:** three takes, the horses first: [s1_concepts](s1_concepts/README.md). Picks: A's charger, C's
   horned armet, A's steppe helm (reworked), a buffer bone horse: take 2, [s1_take2](s1_take2/README.md). **Approved 2026-11-20.**
2. **Design lock and blockout:** four rigs (mount and rider per pair), whole texels, the riders' hitboxes, key poses:
   [s2_design](s2_design/README.md). **Approved 2026-11-20.**
3. **Rig and pose test:** four review rigs, poses as animations, built clean on server b: [s3_rig](s3_rig/README.md).
   **Approved 2026-11-20.**
4. **UV and material blocking:** one atlas per model, vanilla skins on the heads, zones, value check clean:
   [s4_uv](s4_uv/README.md). **Approved 2026-11-20.**
5. **Texture painting:** painted, calmed after self-review: [s5_paint](s5_paint/README.md). Review 1: 3x horse heads, vanilla bone
   greys, the zombie horse's eyes opened, the archer's armour, the whole pair at 0.75. **Approved 2026-11-20.**
6. **Texture polish and variants:** neutral glows tinted per state (the survivor takes the fallen rider's colour),
   lance bands and banner sigil added for night readability: [s6_variants](s6_variants/README.md). **Approved 2026-11-20.**
7. **Animation:** gaits from leg phases, the rider riding the saddle's path, 11 clips per pair timed to the fight, lit
   GIFs, built clean on server b: [s7_animation](s7_animation/README.md). **Approved 2026-11-20.**
8. **Pack and in-game review:** shipped: four Mythic bodies (invisible pigs under the horses), clips and tints wired
   to the fight, attacks on the clips' contacts from the model's hands, pack f9717c70, self-test 583/0:
   [s8_ship](s8_ship/README.md). In-game fight pending.
