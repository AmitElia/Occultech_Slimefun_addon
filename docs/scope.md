# Occultech v1.0 - scope

**Status:** positioning, size, power model and balance rules are locked (2026-09-29).
**Tiers, the boss list and progression are still a draft.** Mini-boss ideas are being explored in
[boss-ideas.md](boss-ideas.md) before these are finalized.

This defines what v1.0 is. Individual item and boss designs go in `design.md` and must stay within these limits.
Data behind these decisions: [server-analysis.md](server-analysis.md).

## Positioning
- **Pitch:** the server's first *combat-gated* progression. Every other addon gates progress on automation volume.
  Occultech gates on **boss fights**: you craft ritual materials the Slimefun way, then earn upgrade materials by
  defeating what you summon.
- **Where it sits:** mid to late game, **parallel to InfinityExpansion2**. It is its own progression line and does not require Supreme,
  Infinity or Networks. Top-tier raw cost is capped around **~1M**, comparable to Infinity's upper tiers.
- **Power level:** top-tier rewards are *unique abilities* (mechanical or magical effects), not simply bigger stats than
  Infinity or Supreme gear.
- **Size:** about **100 items**, 4 tiers, 4 bosses.

## Tiers and gates (DRAFT, not locked)

| Tier | Theme | Crafted from | Boss gate (unlocks the next tier) | Raw cost target |
|---|---|---|---|---|
| 0 · Initiate | chalk, candles, salts, first circle and altar | base Slimefun magic items (Magical/Ender Lumps, Essence of Afterlife, Runes) | none (tier 0 enables the first summon) | 100 - 1k |
| 1 · Bound | tier-1 glyphs, first ritual machine, starter weapon | tier 0 + slime-derived materials | **Gelatinous Sovereign** (Slime) | 1k - 10k |
| 2 · Abyssal | ocean materials, powered ritual engine, armor | tier 1 + Sponge / Prismarine / Heart of the Sea | **Abyssal Warden** (Guardian), then **Drowned Elder** (Elder Guardian) | 10k - 100k |
| 3 · Hollow | pinnacle circle, top weapons | tier 2 + Occultech wither materials (not raw Nether Stars) | **Hollow Wither** (Wither) | 100k - ~1M |

**Gate rule:** the capstone items of tier N+1 require a drop from the tier N boss. Summoning the tier N boss requires tier N
materials. There are no shortcuts: boss drops cannot be crafted, bought or duplicated.

## Item budget (~100)

| Category | Count | Notes |
|---|---:|---|
| Materials and intermediates | ~35 | about 10 / 8 / 10 / 7 per tier |
| Ritual infrastructure | ~20 | glyph blocks, altars, offering bowls and pedestals, candles |
| Machines | ~10 | tier 2 and up need Slimefun power |
| Summon catalysts and boss drops | ~16 | 1 catalyst and about 3 drops per boss |
| Weapons and tools | ~12 | each with a unique active or passive ability |
| Armor | ~8 | 2 sets (Abyssal and Hollow) |
| Utility | ~5 | e.g. a circle-inspection tool, ritual guide |

## Design rules
- **Grind:** the repeated cost is the summon (consumable offerings plus a catalyst), not raw-material volume. Keep the
  raw-cost targets above; don't push players toward cobblestone-generator scale.
- **Drops:** always a guaranteed minimum, with a small random bonus. Each player who contributed to the fight gets their own drops.
- **Power:** hybrid. Tiers 0-1 are purely magical (offerings only). Tier 2 and up ritual engines and infusers use Slimefun energy.
- **Balance:** each boss is beatable solo with that tier's gear. HP and extra spawned mobs scale with the number of players in the arena.
- **Every resource has its own purpose:** each Occultech material (especially boss drops) has its own recipes and never substitutes
  for another resource, whether Occultech, Slimefun or another addon's. Bosses never drop their base mob's vanilla loot.
- **Protecting other addons' materials:** avoid adding lots of demand for heavily used inputs (Nether Star in 285 recipes,
  Slime Ball in 177). Prefer the unused ocean drops, Heavy Core and Breeze Rod as crafting inputs.
- **No griefing, and built to resist abuse:** fights never change world blocks, and every fight follows the engine rules against abuse
  in [boss-ideas.md](boss-ideas.md). Only use mechanics that plugins can do reliably in multiplayer.
- **Fun first:** attacks are telegraphed, there are no unavoidable one-shots, and repeat summons are cheap relative to the player's progression.
- **Only depend on base Slimefun.** Optional integrations with other addons can come after v1.0.

## Not in v1.0
- Bosses beyond the four above, or boss variants and hard modes
- Integrations with other addons (Networks storage, Infinity inputs)
- Dimensions, custom structures, or natural world spawns of bosses
- Custom models or resource packs (vanilla items and Slimefun heads only)
