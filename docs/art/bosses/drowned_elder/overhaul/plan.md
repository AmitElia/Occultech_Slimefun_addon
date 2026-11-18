# The Drowned Elder redesign: the plan (the Abyssal Serpent)

Direction picked 2026-11-17, in a fresh round of pitches (the Marionette, the Thawing Leviathan, the Tide Moon, the
Abyssal Serpent). It replaces every earlier direction for this boss, including the "Benthic Oracle" draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md) and the earlier lure/coral take.

## Identity

- **The Elder Guardian grown into a sea serpent.** The head is vanilla's Elder Guardian at a whole scale (the barrel body
  with its four plates, the twelve spikes, the eye on its face; `GuardianModel`, 26.2 client). Behind it, around ten
  armoured segments trail away, each built on the guardian's own plan (a core, plates, spikes), ending in the guardian's
  tail fin.
- **It swims through the air** around the arena; the motion is the selling point (undulation, coils, a dive).
- It is the tier 2 **gate** boss: the biggest thing in the tier, about 18 blocks long in a 22-block arena.

## The fight stays (DrownedElder.java)

| Mechanic | What the model shows |
|---|---|
| Multi-beam (up to three players, each locked 0.5 s before firing) | three segments roll over to open eyes along its side, each locking on its own player; that eye fires the beam |
| Pressure (Mining Fatigue II) | it coils into a tight spiral overhead and stares down with the head's great eye |
| Guardians join every 20 s | a segment's spikes split away and the piece becomes a guardian (the body regrows it) |
| Tidal Surge at half health (three waves to jump) | it dives into the floor and bursts back out; the waves ripple from where it surfaced |

## Materials

The elder's pale, ancient hide and plates, its spikes, fin membranes, and the segment eyes' sea-glow (tier 2 teal).
Not used: copper, kelp, barnacles (the Warden), planks/nautilus (Tidebreaker), brass (the Choir), carved stone (Tempest).

## Progress

- Step 1, three body plans ([s1_serpent](s1_serpent/README.md)): **B, the Wyrm** picked (overlapping armoured
  segments, a row of tall spikes down the back, pectoral fins, swimming in humps).
- Step 2, the head and segment study ([s1_study](s1_study/README.md)): **H3, the Spike Hood**
  (a webbed fan of spikes that flares in the stare) + **S2, the Shingle** (plates overlapping back like shingles; the side
  shingle swings out like a gill cover to show the eye) picked.
- Step 3, the full blockout ([s1_blockout](s1_blockout/README.md)): idle, aim, stare, surge; **session 1 approved 2026-11-17**.
- Session 2, design lock ([s2_design](s2_design/README.md), drowned_s2.py): the rig (a body chain, hood bones,
  gill bones, four hitboxes) and six key poses; **approved 2026-11-17**.
- Session 3, rig and pose test ([s3_rig](s3_rig/README.md), drowned_s3.py): review rig built clean on server b,
  90 displays; **approved 2026-11-17**.
- Session 4, UV and material zones ([s4_uv](s4_uv/README.md), drowned_s4.py): 512x512 atlas, vanilla elder skin
  on the head at 3x, zones and value check; **approved 2026-11-17**.
- Session 5, painting ([s5_paint](s5_paint/README.md), drowned_s5.py): body painted in 3x3 clusters to match the
  head's vanilla skin; **approved 2026-11-18**.
- Session 6, variants ([s6_variants](s6_variants/README.md), drowned_s6.py, run last): neutral eyes tinted per state
  (beam eyes calm/lock/surged/dead, head eye calm/stare/dead), night and hit checks; **approved 2026-11-18**.
- Session 7, animation ([s7_animation](s7_animation/README.md), drowned_s7.py): nine clips timed to the fight
  (contacts aim 2.0, stare 1.0, shed 0.5, dive 1.0, emerge 0.8). Take 2 (user: the animations matter most, impressive
  and smooth): authored as motion (shape blending down the body, path following through the floor, anticipation and
  follow-through, dense continuous keys), lit textured GIFs in s7_animation/lit/; loads clean on server b; **approved 2026-11-18**.
- Session 8, ship ([s8_ship](s8_ship/README.md), drowned_ship.py): shipped 2026-11-18, pack 5f56e185, self-test 579/0;
  the in-game sign-off is pending.

## Process

Session 1 in gated steps: silhouettes (three body plans for the serpent) -> a head and segment study -> the blockout.
Sessions 2-8 as in [boss-art-sessions.md](../../../../boss-art-sessions.md). Scripts `tools/art/bosses/drowned_*.py`.
Session 8 needs a carrier that can move a long body (the segments are bones of one model, driven by the clips and a
follow-the-head trail in code), and a hitbox plan for a long body (head + a few segment hitboxes).
