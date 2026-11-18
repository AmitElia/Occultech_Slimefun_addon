# The Tempest redesign: the plan (the Shattered Seal)

Direction (2026-11-17). Replaces the "Storm Vane" draft in [boss-visual-overhaul.md](../../../../boss-visual-overhaul.md):
its torn sail, gauge and weathervanes repeat the Tidebreaker's ship, the Warden's brass and the Choir's chimes.

## Identity

The user picked option 1 of the second pitch round (after liking the "Heavy Core" take best in round one):
- **Something the circle should never have opened.** The wind was sealed inside a great carved ritual seal, a stone disc
  of glyphs like a summoning circle stood up. The summoning cracked it open.
- **The heavy core is the seal's keystone**, glowing at the centre: vanilla's heavy core block at a whole scale (the mace's
  heart; Tempest drops the Tempest Core).
- **Seal shards orbit the core on the wind**, glyphs still lit.
- **Vanilla's Breeze head** (the 8x8x8 head and its visor band, eyes on the band) above, eyes narrowed and furious.
- **The wind body:** breeze rods and a twisting vortex below and through the gaps between the shards.

**Vanilla ties:** the breeze head and rods at a whole scale, the heavy core, the wind's three-layer funnel.

## The fight stays (Tempest.java)

| Mechanic | What the model shows |
|---|---|
| Gust volley (3 wind charges) | the shards lock back into a near-whole seal, the glyphs flare, the charges leave through the cracks |
| Wind burst (warned circle, throw-up) | the shards blast outward, then reel back in |
| Spent (1.5 s, the opening) | the shards drop and drag, glyphs dark, the core exposed and dim: "hit me now" |
| Squall ring | the vortex widens and spins faster |
| Below half: two small breezes | the seal splits clean in two; a half spins off with each small breeze |

## Materials

New to the roster: **carved ritual stone** (pale chiselled tuff-like stone, deep-cut glyphs), the **dark steel** of the heavy
core, and the breeze's own lavender-blue wind. Glow: tier 2's deep teal / prismarine sea glow in the glyphs and the core's
seams. Not used: copper (Warden), brass (Choir), sail and planks (Tidebreaker), gold (Archevoker).

## Process

Session 1 in gated steps: silhouettes (how the seal is broken and carried) -> a head and core study -> the blockout.
Sessions 2-8 as in [boss-art-sessions.md](../../../../boss-art-sessions.md). Scripts `tools/art/bosses/tempest_*.py`.
