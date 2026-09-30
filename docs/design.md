# Occultech - content design (living document)

Must stay within [scope.md](scope.md) (tiers, gates, item budget, raw-cost targets).
Items and recipes: [recipes.yml](recipes.yml) → [items.md](items.md). Mechanics: [mechanics.md](mechanics.md).

## Core loop
Slimefun resources -> occult materials -> ritual components -> circle glyph blocks + altar
-> summon a boss -> boss drops -> higher-tier circles, machines and weapons.

## Rituals (implemented for tier 0)
- The Initiate's circle is 5x5 on one layer: altar in the middle, Offering Bowls on its four sides, Tallow Candles on the
  diagonals, Chalk Glyphs around the outside. Any rotation works.
- **Crafting ritual:** center item on the altar, one offering per bowl, press Begin Ritual (5 seconds).
- **Summoning ritual:** offerings in the bowls; the altar stays *empty* for a mini-boss and holds the *catalyst* for a gate boss.
- Offerings are taken at the start. Breaking the circle mid-ritual loses them. A server stop mid-ritual finishes a
  crafting ritual and gives a summoning ritual's offerings back.
- The Occult Codex GUI shows circle layouts, crafting rituals and summoning rituals; right-clicking an altar with it
  checks that circle and marks missing pieces.

## Boss fights (engine rules implemented)
- Arena: 12 blocks around the altar (+2 per tier). Bosses pulled out go back to the middle and heal 5%.
- Health scales +25% per extra player present at the summon (config: `bosses.health-per-extra-player`, plus a global
  `bosses.health-multiplier`). Only players damage bosses; environment can't. Bosses pulled out of the arena heal 2%.
- Anti-pillar: if the boss can't land a hit for 10s while being damaged, it teleports next to the nearest player
  (melee bosses only).
- Loot goes straight to each contributor (at least 5% of the damage and present for 25% of the fight):
  the guaranteed amount plus a 25% chance of one bonus, the boss's curated vanilla drops and XP, and any chance-based
  bonus items (e.g. the Brood Egg). Creative-mode players get nothing.
- Holograms float above Offering Bowls (contents), altars (center item or what the circle is doing) and Brood Eggs.
- Fight ends: victory; abandoned (nobody in the arena for 30s); timeout (10 min, gate bosses 15 min); interrupted
  (chunk unload, shutdown, error) refunds the catalyst. Crash: the catalyst comes back the next time the altar loads.

## Tier-0 bosses (implemented)
| Boss | Base | Health | Mechanics | Drop |
|------|------|-------:|-----------|------|
| Brood Mother | giant Spider | 220 | Egg sacs hatch cave spiders unless smashed (3 hits); web zones slow; telegraphed pounce | Brood Silk; 15% Brood Egg |
| Volley | Skeleton archer | 160 | Glowing 1s warning, then a 5-arrow volley (slowness/poison/spectral); ward crystals cut its damage taken by 70% until broken | Fletcher's Quill |
| Witch Coven | 3 Witches | 3x80 | Roles rotate every 15s (healer green, curser purple, bomber red); kill the healer first | Coven Brew Base |
| Gelatinous Sovereign | Slime (size 7) | 600 | Ringed leap-slam with a jumpable shockwave; at 66% three shards crawl to the altar and heal it 6% each; at 33% it shrinks, speeds up and leaves acid puddles | Sovereign Gel |

**Brood Egg** (15% per contributor per Brood Mother win): placed, it's a sniffer egg that never hatches and spins 1 String
every 20s (config) into a 9-slot store while its chunk is loaded - no offline catch-up. Right-click to collect; Slimefun
cargo and Networks can pull from it but not insert.

Health values are before group scaling. Balance is untested with real players; tune after playtests.

## Later tiers
| Tier | Boss | Base mob | Idea |
|------|------|----------|------|
| 1 | Archevoker | Evoker | circle-shaped fang patterns, phylactery totem |
| 2 | Drowned Elder | Elder Guardian | mining fatigue aura, summons guardians |
| 3 | Hollow Wither | Wither | phase shift at 50% HP, skull barrages |
See [boss-ideas.md](boss-ideas.md) for the full pool.
