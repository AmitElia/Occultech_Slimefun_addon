# Special mechanics: feasibility and design

Covers summoned labor, necromancy weapons and custom "held" weapons such as Wyrmbreath.
Everything here must follow the design and anti-abuse rules in [boss-ideas.md](boss-ideas.md).

## 1. Summoned labor (Servitors)
Inspired by Occultism's bound spirits doing jobs. Items: Servitor Shrine (tier 1), Harvest and Gather Contracts, Servitor Nexus (tier 3).

**Approach: a machine with a visible spirit, not a real mob AI.**
- The Shrine is a Slimefun block with a block ticker. Each cycle it does *one* unit of work in its area, e.g. harvest and replant one mature crop.
- The "spirit" is purely visual: a display entity (or an Allay with AI turned off, invulnerable, no collision) that floats to the block being worked on.
- Why not real pathfinding mobs: they get stuck, leave the area, despawn, can be killed, leashed or pushed into water, and cost a lot of
  server time for pathfinding. A block ticker is predictable and cheap.

**Why it doesn't overlap with other addons:** it's cheap, magical (no power in tier 1, upkeep paid in Spirit Essence) and available early. It's slower than
the electric harvesters in Slimefun and FluffyMachines. The Nexus (tier 3) makes it a real mid-scale option without competing with
Networks or Infinity.

**First contracts:** Harvest (crops, nether wart, cocoa, sugar cane) and Gather (collect dropped items into an adjacent chest).
**Later ideas:** Composter, Brewer's assistant (feeds nether wart to brewing stands), Fisher. Avoid anything that duplicates Slimefun cargo or androids.

**Rules:**
- **Blocks:** this is the one place Occultech changes blocks, and only by design, in the owner's own farm (harvest and replant). It checks Slimefun's protection
  permission when placed and on every action, so it never works in areas the owner can't build in.
- **Loaded chunks only:** it works only in loaded chunks and never loads chunks itself. There are caps per chunk and per player, and a budget of one action per cycle.
- **Output:** it outputs into a chest and pauses when the chest is full, so no item entities pile up. Yields are vanilla drops (no multiplication, no Fortune).
- **Upkeep:** it stops working when out of Spirit Essence.

## 2. Necromancy weapons
Items: Bone Scepter (tier 1: 2 skeleton archers for 30s), Grave Lantern (tier 2: 3 wither-skeleton knights for 30s),
Lich's Phylactery (tier 3: up to 4 Hollow Knights that stay until killed).

**Feasibility: high.** Spawning tagged vanilla mobs and controlling their targets is standard Paper API
(target events plus the Paper Mob Goals API).

**Rules:**
- **Minion properties:** minions are tagged. They give no drops or XP, can't be leashed, ridden, name-tagged or converted, and can't use portals. They don't burn in daylight.
- **Targeting:** minions attack what the owner hits and what hits the owner. They never target the owner, other players' minions, villagers
  or passive animals (unless the owner attacked them), or other players unless PvP is allowed at that spot.
- **Following:** minions follow the owner and teleport back if they fall behind (same world only, like tamed wolves).
- **Despawning:** minions despawn on owner logout, death or world change, and on chunk unload or server stop. The Phylactery's knights are re-summoned after the owner
  logs back in; they are never saved into the world.
- **Limits:** a per-player cap, and all minions count toward the server's entity budget. A cooldown and a cost (energy or Spirit Essence) apply.
- **Anti-farming:** mobs killed only by minions give no XP, and the short lifetime plus cooldown make AFK mob farming impractical.
- **Boss fights:** minions do reduced damage to bosses (e.g. 30%), don't count toward loot eligibility, and boss attacks can hit them. The
  fight's extra-mob cap includes player minions, so necromancy can't trivialize fights.

## 3. Custom weapons, e.g. Wyrmbreath (a dragon-fire stream)
**Feasibility: yes, fully server-side:** particles, sounds and plugin-applied damage. The only tricky part is
detecting that the player is *holding* right-click.

**Detecting "hold to use":**
- **MC 26.2 (the real target):** the `consumable` data component (in the game since 1.21.2) lets *any* item be held like food, with a
  very long use time and no eating animation. Paper exposes this through its data-component API. While the player is using the item → fire.
- **Current test server (1.21.1):** that component doesn't exist yet. The fallback is a press-to-toggle *3-second burst*. (Using a
  trident or shield as the base item works too, but has side effects like blocking, and throws that have to be cancelled.)
- Put this behind one small "use detector" class with two implementations, so the weapon logic stays the same.

**Each tick while firing:**
- **Visuals:** particles along a cone (flame / dragon breath / soul fire for the tier-3 Soulfire Censer), about 20-40 per tick, drifting forward.
  Plus a looping vanilla sound.
- **Hits, every 2-4 ticks:** living entities within about 6 blocks and within 25° of where the player is looking, *with line of sight*
  (a ray check, so it never hits through walls). Damage is applied as coming from the player, so PvP and claim plugins can cancel it. Targets are set on fire.
- **Never ignites blocks.**

**Cost and limits:** Slimefun rechargeable energy drains per tick. A heat bar on the action bar locks the weapon for 3s when it overheats.
Main hand only, a per-player particle budget, and a damage cap per tick.

**Other weapon mechanics that are realistic:**
- Locked beam that ramps up damage (Guardian's Gaze): a particle line, and the lock breaks when line of sight is lost.
- Lunge or charge (Dreadlance): push the player forward with velocity, sweep for hits along the path. 26.2 spears already have lunge animations.
- Dash (Tempest Treads): velocity only, never teleporting, with a ray check so it can't clip through blocks.
- Arrow burst (Quillshot), chain lightning (visual-only lightning plus damage), gravity pull, shockwave ring with knockback,
  homing projectiles (steering item-display entities), decoys (Mirror Ward).

**Not realistic without a resource pack** (and v1.0 ships without one):
- Custom 3D models and animations. Use item-display entities with vanilla items or heads instead.
- Custom sounds (vanilla sounds only).
- Screen effects beyond vanilla ones (darkness, nausea, glowing).
