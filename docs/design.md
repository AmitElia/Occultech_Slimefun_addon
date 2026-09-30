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
- Arena: 18 blocks around the altar (+2 per tier). A boss past the edge is pushed back in; one far outside (6+ blocks) is put back just inside the edge where it left, never in the middle.
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

## Tier 1 · Bound (implemented)
- Balanced for basic diamond gear; tuned for **solo first**, groups handled by health scaling.
- 7x7 circle wrapping the tier-0 circle (8 bowls, 8 candles, 16 chalk + 16 bound glyphs). The Initiate's Altar is
  upgraded in place by ritual into the Bound Altar.
- Mini-bosses: The Unbound, Night Matriarch (**any time**, never burns, ~20% stronger at night), Mirrored Magus.
  Gate: Archevoker. Bonus drops (15%): Frenzy Idol, Phantom Roost, Scrying Mirror.
- Both the Servitor Shrine and the Bone Scepter (necromancy) ship in tier 1.

| Boss | Base | Health | Mechanics | Drop |
|------|------|-------:|-----------|------|
| The Unbound | Vindicator ("Johnny") | 320 | Speeds up as it's hurt; red-wedge telegraphed cleave; husk thralls every 20s - it attacks thralls near it and is **sated** (stunned, +50% damage taken) for 3s after devouring one | Frenzied Edge; 15% Frenzy Idol |
| Night Matriarch | giant Phantom | 260 | Dark-circle telegraphed dives, then **stunned 2s on the ground**; small phantoms join; +20% damage and faster dives at night; never burns | Dusk Membrane; 15% Phantom Roost |
| Mirrored Magus | Illusioner | 220 | Every 15s 3 decoys (can't cast) and a blink; the real one sparkles; hitting a decoy makes you glow and it blinks again | Mirror Dust; 15% Scrying Mirror |
| Archevoker | Evoker (gate) | 700 | Fang patterns (ring / line / spiral) drawn 1s ahead, faster below 50%; its vexes are adopted, capped and leashed; 3 phylacteries let it cheat death once at 40% - break them first | Evoker's Sigil |

- **Servitor Shrine** is the tier-1 capstone: a Bound-circle ritual that needs 2 Evoker's Sigils (~6.7k raw). At most 4
  shrines within 12 blocks of each other. One action every 2s; a Frenzy Idol within 8 blocks makes it 1.5x faster (idols
  never stack); **Empower** (1 Spirit Essence) doubles speed for an hour, banking up to 24h (so 3x at most). Its store
  takes output and supplies; cargo/Networks can use it. Contracts (swap any time):
  Harvest, Gather, Shepherd, Beekeeper, Brewer's Aid (9x9) and Ward, Acolyte (17x17). The Acolyte restocks an altar's
  bowls with the offerings of the last ritual done there, one bowl per action, and never starts a ritual.
- **Repair ritual:** a damaged weapon on the altar and only its repair item in the bowls; each item restores 25%, only
  what's needed is used, and breaking the circle loses the repair items but never the weapon. (Slimefun forbids its items
  in anvils, so repairs are rituals.)
- **Head textures:** any item can use `head: <texture>` in recipes.yml instead of `material`.
- **Bone Scepter**: 2 skeleton archers for 30s, 20s cooldown, 64 uses (durability). Minions attack whatever their owner
  attacks (except players, other minions and the owner's pets) and hold that target; on their own they only fight
  hostile mobs and bosses.
- **Gear**: Frenzy Cleaver (+0.2 attack speed per stack, max 5), Duskwing Charm (double jump, no fall damage after it,
  4s cooldown), Mirror Ward (decoy below 30% HP, 60s cooldown). Mending never repairs Occultech gear.

### Servitor Shrine
- **Its own block, placed next to your farm.** It works a 9x9 area around it (±1 block vertically); crops stay normal
  blocks you can see and walk through. A bound spirit (display entity, never a real mob) floats to each plot it works.
- **No fuel.** Spirit Essence is a crafting cost (shrine + contracts), never a running upkeep. Balance comes from speed
  (1 action every ~2s), area, and caps per chunk/player instead.
- **Contracts** go in the shrine's slot and decide the job; swap them any time. Output goes into the shrine's own
  store (cargo/Networks can pull) or an adjacent container.
- Only works in loaded chunks, only where the owner may build, stops when its store is full.
- Contract ideas: Harvest (T1), Gather (T1), Ward - no hostile spawns in the area (T1), Brewer's Aid - feeds wart and
  ingredients into brewing stands (T2), Shepherd/Beekeeper (T2), Acolyte - keeps a circle's bowls stocked with a chosen
  ritual's offerings from a chest, never starts rituals itself (T2). Servitor Nexus (T3) links shrines and widens areas.

## Tier 2 · Abyssal (implemented)
- Balanced for max-enchanted netherite. First **powered machines** (Occult Forge, Soul Condenser); **rituals never use
  power** but cost more (mini-boss summons ~1.1k raw, the Drowned Elder ~4.6k, 3-13% of the 9x9 circle).
- Ocean bosses fight **on land with custom movement** (no ponds). Mini-bosses: Abyssal Warden, Tidebreaker, Blaze Choir,
  Tempest. Gate: Drowned Elder -> Elder Scale.
- Bonus drops (15%): Guardian Eye (sentry beam vs hostile mobs; a Frenzy Idol within 8 makes it 1.5x stronger, never
  stacking), Pearl Bed (prismarine), Ember Brazier (blaze powder), Bottled Gale (decoration).
- Gear: Wyrmbreath, Guardian's Gaze, Grave Lantern, **Abyssal Anchor** (chain-hook pull weapon), **Choir Bell**
  (burning shockwave talisman that staggers summoned creatures), **Wind Chime** (placed: Speed II + Jump Boost II
  within 32 blocks; a soft random chime every 10-25s, never constant). Tempest Treads and Nautilus Harness were dropped.
- Abyssal armor: netherite-level defense; helm Water Breathing, chest Thorns V, legs Conduit Power in water, boots
  Dolphin's Grace; 4/4: -20% damage from summoned creatures.
- **Abyssal Tether** (moved from tier 3's Servitor Nexus): shrine range upgrade in its own slot - 15x15, Ward/Acolyte 25x25.
- **Decorations** (visual effects only, never change blocks, animate only with a player within 24 blocks, right-click
  palettes where they fit): Wisp Jar (firefly-bush style, wisps up to 10 blocks out), Abyssal Lantern, Rune Obelisk,
  Occult Orrery, Soulfire Brazier, Bottled Gale. Orbiting parts use display-entity interpolation (the client animates;
  the server sends one update every few seconds). Cut as not multiplayer friendly: Aurora Beacon (sky-wide particle
  ribbon), Tide Fountain (constant heavy particle arcs).
- The 9x9 Abyssal circle comes from upgrading the Bound Altar in place (like Initiate -> Bound).
- Crafting rituals keep the center item's enchantments (an enchanted netherite helmet stays enchanted as an Abyssal Helm).

### Cosmetics by tier (implemented for tiers 0-2)
Visual only, never change other blocks, animate only near players; tiles have no ticker (nothing runs until stepped on).
| Tier | Block | Effect | Made with |
|------|-------|--------|-----------|
| 0 | Chiming Amethyst Tile | pentatonic chime + sparkle underfoot, quiet while sneaking | amethyst, Warded Silver |
| 1 | Moonlit Lily | star motes and a little moon orbit it, twinkles at night | Dusk Membrane (Night Matriarch) |
| 1 | Witchcap | crimson fungus bubbling red and green like a brew | Coven Brew Base (Witch Coven) |
| 2 | Everliving Coral | never dries out of water, bubble stream; right-click cycles the five corals | Tide Glass |
| 2 | Tidal Coral Tile | never dries, splash underfoot; right-click cycles coral blocks | Tide Glass |
| 2 | Prismatic Netherrack | lit fire shimmers through hue-cycling colors (particles over vanilla fire) | Choir Ember (Blaze Choir) |
| 3 (planned) | Watchful Eyeblossom | opens when someone is near, particles drift toward them | Heartwood Resin (Heartwood Horror, creaking) |
| 3 (planned) | Resin Tile | amber drips underfoot | Heartwood Resin |
Breaking the block under a decorative flower drops the Occultech item, never a plain vanilla flower.

### Tier-2 bosses (implemented)
Health attributes cap at 1024, so tier-2 bosses have modest health and thick hides: minis take a third of the damage
dealt (~900-1000 effective health solo), the Drowned Elder a fifth (~2500). Group scaling still applies.
Sea creatures are "puppets": no vanilla goals and no gravity, moved by the boss script so they glide over the land.
| Boss | Mechanics |
|------|-----------|
| Abyssal Warden | glides after players; charged beam tracks for 2s, turns white and locks 0.5s before firing (step aside); spike burst after a 1s ring; two beams at once below half health |
| Tidebreaker | drowned on a zombie nautilus; ram charge along a warned line, then winded for 2s (melee window); trident fan volley (no pickup); trident melee |
| Blaze Choir | three blazes orbit the altar; the shield passes between them every 6s (90% less damage, glowing); fireballs never light blocks; Chorus flame circles under players; survivors sing faster |
| Tempest | breeze with its own AI; wind-charge fan; squall ring closes in from the arena edge to 5 blocks (outside hurts); wind burst; two small breezes at half health |
| Drowned Elder | Mining Fatigue II pressure; beams at up to three players; two gliding guardians every 20s with small beams; Tidal Surge at half health: three waves roll out - jump over each |

## Later tiers
| Tier | Boss | Base mob | Idea |
|------|------|----------|------|
| 1 | Archevoker | Evoker | circle-shaped fang patterns, phylactery totem |
| 2 | Drowned Elder | Elder Guardian | mining fatigue aura, summons guardians |
| 3 | Hollow Wither | Wither | phase shift at 50% HP, skull barrages |
See [boss-ideas.md](boss-ideas.md) for the full pool.
