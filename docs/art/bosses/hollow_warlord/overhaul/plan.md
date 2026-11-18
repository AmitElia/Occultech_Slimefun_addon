# Hollow Warlord redesign: the Headsman

Started 2026-11-18. Direction picked from a fresh pitch round (the Fortress Gate / the Headsman / the Unfinished Wither):
**B, the Headsman**. Sessions follow [boss-art-sessions.md](../../../../boss-art-sessions.md).

## The brief

The Nether fortress's executioner. A wither skeleton's rare drop is its skull; he is the one who takes them.

- **Body:** a giant wither skeleton, very tall and lean, slightly stooped. Black bone, a real ribcage (the "hollow").
  The vanilla wither skeleton skull is kept exactly, at a whole scale.
- **Helm:** a tall blackstone headsman's bucket helm covering the cranium and eyes, one eye slit glowing soul cyan;
  the skull's jaw shows below it.
- **Sword:** a blackstone executioner's sword about as long as he is tall: square-ended, a straight crossguard, a
  crimson brand-rune burning down the fuller (the **Warlord's Brand**, his drop).
- **The three skulls:** wither skeleton skulls he took, hung on hooks. Each belongs to one guard of his warband.

## Palette (tier 3, Nether-fortress materials no boss uses yet)

Black bone and blackstone, nether brick and soul sand as secondary darks; **soul-fire cyan** (vanilla soul fire, also the
tier-3 hollow cyan) for the eye slit, the skulls and the chains; ~~crimson for the brand~~ (review: no red or brown; the brand is soul cyan, every grey from the wither skin).

Avoid: the Unbound's hanging chains, shackles and cleaver; the Archevoker's hood; sculk (Night Matriarch); copper,
brass, wax, amethyst, basalt; the old "Empty Throne" concept (empty armour, banner of shields).

## The fight, read on the model

| Mechanic (HollowWarlord.java) | On the model |
|---|---|
| Warband: 3 guards; with 2+ alive he takes half damage, soul chains to each | each guard's skull on him burns with soul fire; the soul chains run from that skull to its guard |
| A guard dies | its skull bursts into soul fire and goes dark |
| Soul sweep: 1 s ring, then a blade sweep with Wither | the sword drags round behind him, then one hip-height executioner's whirl |
| Faster below 35% | he tears off the helm and fights bare-skulled; the brand spreads up his sword arm |
| Death | kneels on the sword; his skull drops and rolls; the hung skulls fall round him |

Later (optional): the guards get a matching look (headless wither skeletons, a soul-fire stump).

## Session 1 steps

1. Silhouettes: three ways to carry the skulls ([s1_silhouettes](s1_silhouettes/README.md)): all rejected as goofy
   (too lean in the shoulders, a goofy bucket helm). User: the skulls float above and behind his head.
   Take 2, a complete overhaul ([s1_take2](s1_take2/README.md)): a heavy, stooped top, a V to a hollow waist, floating
   skulls; A the Plate / B the Ossuary / C the Butcher.
   **A, the Plate, picked.**
2. Helm and sword study ([s1_study](s1_study/README.md)): H1 Sallet / H2 Barbute / H3 Kettle Hat;
   S1 Executioner's / S2 Flamberge / S3 Greatsword; real wither skeleton pixels on every skull.
   **H3 Kettle Hat + S1 Executioner's picked.**
3. Full blockout ([s1_blockout](s1_blockout/README.md)): six poses (idle, walk, windup, sweep, enraged, death).
   **Session 1 approved 2026-11-18.**

## Session 2

Design lock ([s2_design](s2_design/README.md), `headsman_s2.py`): the rig, glow bones, the hat bone, the hitbox, six key
poses from the rig. **Approved 2026-11-18.**

## Session 3

Rig and pose test ([s3_rig](s3_rig/README.md), `headsman_s3.py`): review rig in run/ models, 72 displays, 0 flicker,
poses as animations; built clean on server b. **Approved 2026-11-18.**

## Session 4

UV and material zones ([s4_uv](s4_uv/README.md), `headsman_s4.py`): 512 x 256 atlas, the vanilla wither skin at 2x on all
four skulls, value check clean. **Approved 2026-11-18.**

## Session 5

Painting ([s5_paint](s5_paint/README.md), `headsman_s5.py`): blackstone shaded by height (framed faces read as tiles),
tattered tabard, honed blade, brand glyphs, soul-fire tongues. Review 1: no glow under the floating skulls (severed
vertebrae instead), no red or brown (soot-black tabard, black leather, cyan brand), battered armour, every grey from
the wither skin's own greys. **Approved 2026-11-18.**

## Session 6

Variants ([s6_variants](s6_variants/README.md), `headsman_s6.py`, run last): neutral glows tinted per bone; his eyes +
brand calm/tell/enraged/dead, each taken skull lit or dark by its guard; the hat hidden when enraged; night and hit
checks.
**Approved 2026-11-18.**

## Session 7

Animation ([s7_animation](s7_animation/README.md), `headsman_s7.py` + `headsman_gif.py`): eleven clips authored as pose
parameters solved by IK every frame (idle, walk, windup, sweep, attack, call, enrage, idle_enraged, flinch, spawn,
death), lit GIFs, built clean on server b.

Review of take 1: the pauldrons did not follow the arms, the sword struck flat-on, the clips should be more
intimidating, the hat-tearing enrage was dropped, and the idle should hold the sword behind him. Take 2: pauldrons
turn with the upper arms, every cut travels edge first (checked by `edge_report`), the idle hangs the sword behind
him, a new enrage (the sword driven into the floor, a roar as the skulls whirl round him, shouldered), heavier timing
throughout; the hat now stays on in every state.

Review of take 2: the windup and swing clipped the hands through the body. Take 3: the swing is carried by the hips and
chest turning (hands in front of the chest on a short arc), the chop from a high guard before his face, the enraged
stance a low guard, planted swords further out, pauldrons following less, and a clipping check on every played frame.

## Session 8

Ship ([s8_ship](s8_ship/README.md), `headsman_ship.py`): shipped 2026-11-18, pack 2920b3de, self-test 581/0. The model
on an invisible wither skeleton, steered and turned in code; the chop as his own melee from the blade's reach; the
windup clip as the sweep's warning; each skull's fire bound to its guard; the in-game sign-off is pending.
