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
- Health scales on a flattening curve with the players present at the summon: x1.45 / 1.76 / 2.03 / 2.27 for 2-5,
  no more past 5 (config: `bosses.group-scaling`, `group-exponent`, `group-cap`, plus a global `bosses.health-multiplier`). Only players damage bosses; environment can't. Bosses pulled out of the arena heal 2%.
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

## Arcane Altar (tier 0, implemented)
Occultech's replacement for Slimefun's Ancient Altar. Every ingredient goes into the altar's 9 input slots (cargo can
fill it); 8 Arcane Pedestals around it (sides and corners, 2 blocks out) only show floating copies of what's inside, so
nothing has to be restocked pedestal by pedestal. Infusion takes 3 seconds: the items rise and spiral in, motes stream to
the altar over a turning sigil, then the result appears. Recipes are shapeless with amounts (an extra item type blocks
the recipe). It runs Occultech's altar recipes and imports every Slimefun Ancient Altar recipe at startup (runes,
Essence of Afterlife, talismans...).

## Cosmetic talismans
- Hollow Halo styles: the Halo is always available; each boss has its own style (Silk Crown, Quill Crown, Coven Crown,
  Slime Crown, Frenzy Crown, Moon and Stars, Mirror Halo, Soul Crown, Watcher's Halo, Tide Crown, Solar System, Storm
  Halo, Tidal Crown, Dark Rune Crown, Thorn Crown, Lightning Crown, Corrupted Crown, Little Twin, Hollow Pentagram),
  unlocked by defeating that boss 5 times. Operators have all; `/occultech unlockhalos <player>` grants all. A locked
  style never renders (it falls back to the Halo). Styles are display entities following the head, plus a light particle.
- Aura Talisman: trails (prismatic sparks, petals, soul wisps) or footprints (ember, frost, rune, ink, blossom): flat
  colored prints that fade over 3s, with a particle burst per step.
- Abyssal armor (4/4) has a light aura: rising bubbles and a teal swirl at the feet.

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

## Tier 3 · Hollow (implemented)
Balanced for InfinityExpansion2 gear; the final tier. 11x11 circle, arena radius 24, raw cost 100k - ~1M.
11x11 Hollow circle: the Abyssal circle wrapped in Hollow Glyphs, 12 bowls; the Abyssal Altar upgrades in place.
The Hollow Assembler is a powered machine with 9 input slots (cargo/Networks friendly) rather than a hand-filled 6x6
grid; recipes are count-based like every other Occultech machine. Assembling Hollow armor consumes the Abyssal piece;
the result has its own enchantments.

### Mini-bosses
| Boss | Base | Fight | Drop -> purpose |
|------|------|-------|-----------------|
| Hollow Warlord | Wither Skeleton, netherite gear | wither-aura sweeps, bodyguard squad, speeds up as it weakens | Warlord's Brand -> Hollow armor, Lich's Grimoire |
| Heartwood Horror | Creaking (no real creaking heart) | only moves while nobody looks at it; invulnerable until its heart markers (display entities) are broken, so someone must look away | Heartwood Resin -> Heartwood Aegis, Watchful Eyeblossom, Resin Tile |
| Dread Riders | Outrider: Skeleton on a Skeleton Horse; Vanguard: Zombie on a Zombie Horse with a spear | see below | Lancer's Pennant (Vanguard) -> Dreadlance; Outrider's Fletching -> Stormstring Bow |
| Corrupted Colossus | Iron Golem | warned shockwave slams; the tech-meets-occult boss | Corrupted Circuit -> Hollow Assembler, Servitor Nexus |
| Doppelganger | Mannequin (player model) | see boss-ideas.md: wears its target's skin, mirror stance, echo shadows, reflection window, shattered mirror at 50% | Mirror Visage -> Aura Talisman |

**Dread Riders.** Both very fast; each rider has its own health, the horses can't be hurt; both leashed to the arena.
- *Outrider* (fragile, evasive): circles the arena edge 12-20 blocks from its target. Snipe: an aiming line locks on,
  then a heavy shot ends in a lightning strike; arrow rain on a marked circle; lightning-charged volleys.
  Its lightning is **visual only** (flash and thunder, plugin damage): never fires, never charges creepers or turns
  pigs, villagers or other mobs.
- *Vanguard* (tanky, about half damage taken): hard-hitting spear, warned lance charges (stunned 2s if cut short), and
  Intercept - charges anyone who gets within 8 blocks of the Outrider.
- When one dies the other enrages and takes a piece of its partner's kit (Outrider dead: the Vanguard throws spears;
  Vanguard dead: the Outrider fires faster and closer). Solo: juggle both; group: tank the Vanguard, focus the Outrider.

### Gate: Gallus, the Hollow Jockey
A chicken the size of a ghast ridden by a baby-zombie knight in hollow armor (scripted puppets, like the Tidebreaker).
Summoned with the Hollow Effigy (one drop of each mini-boss). Fight length 6-8 minutes, group-scaled.
1. **The Joust (100-66%)**: charges and spear jabs; wing leap (warned landing ring, it never takes fall damage); egg
   barrage - custom eggs (vanilla eggs would hatch chickens) leave splat zones, some crack into capped chick jockeys.
2. **Unhorsed (66-33%)**: the rider falls - a slow, tanky chicken that keeps laying eggs and a tiny, fast, hard-hitting
   rider. The rider tries to **remount every ~20 seconds** (a warned run back to the chicken); a successful remount heals
   the chicken, so knock the rider away when it tries. Killing the rider here is optional but rewarding (below).
3. **The Hollowing (33-0%)**: the chicken turns undead and flies above the arena, laying Hollow Eggs (display entities)
   around the circle; eggs not broken in time hatch weak **echoes** of earlier gate bosses (Sovereign, Archevoker,
   Drowned Elder) with one signature attack each. At 10% it shrinks to a normal chicken and goes frantic.
   - **The rider in phase 3:** if it survived phase 2 it climbs back on for good and rides the flying chicken, diving
     down every so often to strike players who are breaking eggs, then being carried up again. If it was killed in
     phase 2, the chicken fights phase 3 alone (and can't be healed) - the reward for managing the rider well.

### Rewards
- Hollow Heart (2 per win) -> pinnacle gear; Gallus Wishbone (1 per win) -> the final talismans. ~3-5 wins per capstone.
- **Hollow armor**: like Infinity armor but a little worse - Infinity is netherite with Protection XX (one piece already
  reaches the damage-reduction cap), unbreakable and soulbound; Hollow is netherite with Protection V (the cap needs the
  full set), Unbreaking V, repairable, not soulbound. Unique effects Infinity doesn't have: Crown - immune to Darkness and
  Blindness; Cuirass - immune to Wither, Thorns V; Greaves - immune to Slowness; Sabatons - no fall damage. 4/4: -25%
  damage from summoned creatures and faint soul wisps drifting off the armor (subtle).
- **Dreadlance**: every hit heals 15% of the damage dealt (capped per second). **Stormstring Bow**: arrows call visual
  lightning on the mob hit and arc to 2 more hostile mobs; never players or pets, never fires.
- Soulfire Censer, Lich's Grimoire, Heartwood Aegis (as before).
- **Servitor Nexus**: links up to 8 shrines within 24 blocks - one shared store (cargo/Networks), shared supplies,
  empower all at once, and an overview menu showing every linked shrine's contract, area and status, with contract
  swapping. Shrines show "Servitor Nexus: linked" in their range readout.
- **Final talismans** (work from the inventory, only ever affect the carrier):
  Hollow Halo (a ring of light over your head, toggle and colors), Wishbone Talisman (half size, toggle),
  Aura Talisman (walking trail: prismatic sparks, petals, soul wisps, or off), Gallus Egg (a big rideable chicken for its
  owner only: movement keys steer, jump flaps, slow glide; it vanishes on dismount or logout).
- Cosmetics: Watchful Eyeblossom, Resin Tile (Heartwood Resin). Trophy Board is already in tier 0.
- Cut: Hollow Wither (replaced by Gallus; the wither theme lives on in the Hollow Warlord), Dread Lancer (now the Dread
  Riders), Gallus Wing, Hollow Anvil and Ritual of Dawn (other addons cover anvils/enchanting).

See [boss-ideas.md](boss-ideas.md) for the full pool.
