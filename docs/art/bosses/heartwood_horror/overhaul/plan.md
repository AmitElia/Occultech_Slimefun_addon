# Heartwood Horror overhaul plan

The 8-session plan from [docs/boss-art-sessions.md](../../../../boss-art-sessions.md). Mechanics and name are set
(`boss/tier3/HeartwoodHorror.java`); the look is new.

## Direction (picked 2026-11-18)

Combined by the user from five fresh pitches:

- **The Stilt Walker's silhouette:** a hunched torso on long thin legs; 4 or 5 long arms that drag behind it; not
  symmetric, a twisted grown tree. Its face is a creaking heart hanging below the torso like a lantern.
- **The Amber Reliquary's chest:** an older creaking curled like a foetus, sealed in a shell of resin that is part of
  the giant's chest.
- **The Eyeblossom Watcher's limbs:** many limbs, covered in eyeblossoms.
- **The Mourning Willow's moss:** pale hanging moss as texture, but no veil.

How the fight can read on it (to settle in session 2): the hearts making it invulnerable glow along its roots; when
they fall the resin cracks and the sleeper opens its eyes; the creak (vanish and strike from behind) closes every
eyeblossom at once; the sap rain drips from the womb; the root lanes and the slam come out of its dragging hands and
stilt feet.

## Progress

1. **Concept and silhouette:** three takes on the combined design: [s1_blockout](s1_blockout/README.md). The user
   picked C, the Crutch, with the sleeper whole inside the resin, asleep (2026-11-18).
2. **Design lock and blockout:** C rebuilt as a rig (89 bones, about 97 displays), the sleeper curled inside the
   shell, hitbox, eight key poses: [s2_design](s2_design/README.md). First review: the upright resin
   block hid the silhouette, so the body became the Stoop's (straight, level, heavy hump) with a compact womb bulge
   and the lantern hung clear of it. Approved 2026-11-18.
3. **Rig and pose test:** review rig with the eight poses as clips, 93 displays, 0 flicker, loaded clean on
   server b: [s3_rig](s3_rig/README.md). Approved 2026-11-18.
4. **UV and material blocking:** 512 atlas at 1x, vanilla creaking skin on the sleeper, the awake creaking heart
   on the lantern (with a glow overlay of its cracks), dithered resin with a window onto the sleeper:
   [s4_uv](s4_uv/README.md). Approved 2026-11-18.
5. **Texture painting:** furrowed pale oak bark with moss in the creases, amber resin with bubbles and drips,
   the sleeper lit through it, ringed heartwood, shaded eyeblossoms: [s5_paint](s5_paint/README.md). Review 1: the dithered resin read as copper,
   so it became truly translucent over an amber chamber. Approved 2026-11-19.
6. **Texture polish and variants:** neutral glows tinted per state (calm, vulnerable, creak, dead), the lantern
   can go out (dormant heart base), the womb glows from inside at night: [s6_variants](s6_variants/README.md).
   Approved 2026-11-19.
7. **Animation:** twelve clips authored as motion (world-space keys, follow-through, a pendulum lantern and
   moss), 0 collisions in every clip, loaded clean on server b: [s7_animation](s7_animation/README.md), with a
   showcase GIF. Approved 2026-11-20.
8. **Ship:** the model, the Mythic mob and skills, a generated rig table of where the hands land, and the fight wired
   to the clips (one move at a time, every hit where the hand comes down): [s8_ship](s8_ship/README.md). Pack
   `729cb80d`. Waiting for an in-game fight.
