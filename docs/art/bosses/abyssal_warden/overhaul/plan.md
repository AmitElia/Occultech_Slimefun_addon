# The Abyssal Warden redesign: the plan (the Pressure Jailer)

Agreed direction (2026-10-29): **the Pressure Jailer**, from the draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md), reworked. Not taken: the Drowned Lighthouse and the
Abyssal Angler.

## Identity

The user's brief (2026-10-29, revised):
- **A round bathysphere that really looks like the sphere of an old diving helmet**: copper, a big bolted front
  window, the look of a standard diving dress helmet. Round, built from cuboids.
- **From the central window you see a crammed eye**, filling the glass, **looking around and shooting the lasers**.
- **Rivets and pressure valves** that **burst outward in jets of spray** (the spike burst).
- **At 33% health a side window bursts** (where an ear would be) **and a hand comes out** to smash players like
  flies: much larger, buff and mutated. The front window stays clear, so the pupil keeps shooting lasers (take 2).
- **The Lost Helmet** (C, picked): no breastplate; the open neck underneath, with **tendrils and kelp hanging from it
  as a growth**.
- The textures must be great.

**Vanilla ties:**
- **The guardian:** the single eye and its laser; the valves standing out round the sphere where its spikes stand;
  its tail as the helmet's trailing air hose.
- **Copper's weathering** (exposed, weathered, oxidised) as the hull's colours. Prismarine and sea lanterns as fittings.

## The fight (AbyssalWarden.java; the code stays, plus the hand)

| Moment | Server | Look (to design) |
|---|---|---|
| glide | it glides over land after the nearest fighter | it hangs over a cushion of black water, the hose trailing |
| beam | tracks a player 2 s, white near the end; two at once below half | the crammed eye swivels to its target, the pupil narrows and flares, the beam from the window |
| tail lash | anyone within 3.5 blocks, once a second | the hose whips round |
| spike burst | a ring warns 1 s, then spikes hurt and push | the valves and rivets blow: jets of spray from every valve, rivets popping off |
| rest | 2 s after the spikes, its opening | it sinks and vents, the valves hissing |
| below half | two beams, more often | the eye darts faster, bloodshot |
| **33%: the hand** (new) | the window cracks; then a hand smash every 10 s (14 s solo): a 2.5-block ring under a player up to 7 blocks ahead for 1.25 s, about 26 damage and a knockback, the hand left down for 1 s (an opening) | a side window bursts and the mutated hand rears out of it; the eye still looks out and fires |
| death | - | the hull implodes with a deep groan |

## Materials (not repeated from other bosses)

Taken: wax and candles, amethyst and bone, iron vessels and brew, leather, chains and fire, sculk, cards, lava and
basalt, gold, dark oak and emerald. The Warden's: **copper** in its weathering stages (the hull, the rivets, the
valves), **thick sea glass** (the porthole), **prismarine and sea lanterns** (the fittings), **barnacles** growing in
sigil patterns, **kelp**, and the creature's skin. Its one living light: the sea glow of the eye and the cracks.

## Process

Session 1 in gated steps:
1. **Silhouettes:** three takes on the helmet (its breastplate, windows, valves and hose), idle and with the hand
   out, next to a player.
2. **The window study:** the window, the crammed eye and the cracked glass with the hand.
3. **The blockout.**

Sessions 2-8 as in [boss-art-sessions.md](../../../../boss-art-sessions.md).
