# Server addon analysis

Source: `docs/Public Slimefun Guide - Sheet1.csv`, an export of every craftable item on the target server,
with each recipe tree fully expanded down to raw materials. Rerun with `python tools/analyze_guide.py`.

**Metrics**
- **Steps:** how many crafting operations are needed to make the item from raw materials. Measures how deep the recipe tree is.
- **Raw cost:** the total number of raw items consumed. Measures grind.

It does not capture time, energy, or anything a machine produces on its own over time.

## Addons on the server (1,460 items)

| Addon | Items | Steps (median / p90 / max) | Raw cost (median / p90 / max) | Crafting machines used |
|---|---:|---|---|---:|
| Slimefun (base) | 547 | 8 / 38 / 72 | 84 / 992 / 12.8k | 15 |
| Supreme | 510 | 66 / 100 / 186 | 336k / 2.7M / 48M | 11 |
| InfinityExpansion2 | 175 | 44 / 68 / 95 | 5k / 137k / 1.8M | 12 |
| DyedBackpacks | 96 | 12 / 19 / 19 | 56 / 151 / 151 | 2 |
| Networks | 63 | 50 / 86 / 99 | 1.7k / 25k / 196k | 7 |
| FluffyMachines | 51 | 27 / 49 / 71 | 446 / 5k / 57k | 9 |
| EcoPower | 18 | 26 / 49 / 57 | 946 / 13k / 38k | 5 |

### How the costs are spread (number of items in each raw-cost band)

| Addon | <100 | 100-1k | 1k-10k | 10k-100k | 100k-1M | 1M+ |
|---|---:|---:|---:|---:|---:|---:|
| Slimefun | 317 | 176 | 50 | 4 | 0 | 0 |
| Supreme | 19 | 111 | 68 | 33 | 191 | 88 |
| InfinityExpansion2 | 43 | 31 | 31 | 44 | 25 | 1 |
| Networks | 8 | 17 | 19 | 17 | 2 | 0 |
| FluffyMachines | 15 | 20 | 13 | 3 | 0 | 0 |

## What each big addon is like

- **Slimefun base:**
  - Most items are cheap (median 84 raw items).
  - The costliest items are Androids, the Nuclear Reactor and the Wither Assembler (6-13k raw, around 60-70 steps), almost all of it coal.
  - This is the starting point every other addon builds on.
- **Supreme:**
  - Huge and very grindy.
  - Resource tiers go Titanium → Aurum → Adamantium → Thornium. Gear goes Magic → Rare → Epic → Legendary → Supreme.
  - About 190 items are "Cards" and "Cores" (tiers I-IX of Berserk, Cloning, Efficiency and so on) made in its own fabricators.
  - The top gear costs about 48M raw items, mostly honey, cobblestone and sand produced by automated generators.
  - The grind is limited by how much automation you build, not by player skill.
- **InfinityExpansion2:**
  - A clear curve from mid game to end game.
  - Costs are driven by singularities (thousands of ingots each), Void Bits from the Void Harvester, and the Infinity Workbench.
  - The capstone items cost 0.4-1.8M raw, mostly cobblestone and coal.
  - Also grind through automation.
- **Networks:** logistics and storage. Mid-cost (median 1.7k), deep recipe trees (median 50 steps) that lean on uranium and reactor products.
- **FluffyMachines / EcoPower / DyedBackpacks:** small quality-of-life, power and cosmetic addons, all early to mid game.

## Gaps Occultech can fill

1. **Nothing requires combat.** Across all 1,460 items, the only mob drop is the Basic Circuit Board (from Iron Golems). No addon locks anything behind a fight, so boss-gated progression is completely unclaimed.
2. **Ocean materials are unused.** Sponge, Wet Sponge and Heart of the Sea appear in 0 recipes, and Prismarine in 1. That leaves them free for the Guardian and Elder Guardian bosses.
3. **Other unused drops:** Echo Shard, Totem of Undying, Heavy Core and Breeze Rod appear in 0 recipes.
4. **Crowded materials:**
   - Nether Star appears in 285 recipes, Slime Ball in 177, Wither Skeleton Skull in 84.
   - A wither-themed tier should craft its own materials (e.g. from Wither Roses) rather than raise demand for Nether Stars.
   - The same goes for slime: turn Slime Balls into Occultech materials rather than add more raw Slime Ball demand.
5. **Base Slimefun magic items are used lightly outside Slimefun itself:** Essence of Afterlife (only Slimefun uses it), Runes, Magical Lumps, Soulbound. They're natural inputs for the ritual tier.
