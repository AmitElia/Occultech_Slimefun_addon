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
Lich's Grimoire (tier 3: up to 4 Hollow Knights that stay until killed).

**Feasibility: high.** Spawning tagged vanilla mobs and controlling their targets is standard Paper API
(target events plus the Paper Mob Goals API).

**Rules:**
- **Minion properties:** minions are tagged. They give no drops or XP, can't be leashed, ridden, name-tagged or converted, and can't use portals. They don't burn in daylight.
- **Targeting:** minions attack what the owner hits and what hits the owner. They never target the owner, other players' minions, villagers
  or passive animals (unless the owner attacked them), or other players unless PvP is allowed at that spot.
- **Following:** minions follow the owner and teleport back if they fall behind (same world only, like tamed wolves).
- **Despawning:** minions despawn on owner logout, death or world change, and on chunk unload or server stop. The Grimoire's knights are re-summoned after the owner
  logs back in; they are never saved into the world.
- **Limits:** a per-player cap, and all minions count toward the server's entity budget. A cooldown applies, and each summon uses durability
  (see "Durability" below).
- **Anti-farming:** mobs killed only by minions give no XP, and the short lifetime plus cooldown make AFK mob farming impractical.
- **Boss fights:** minions fight bosses at full strength. Their damage counts toward the owner's contribution, and boss attacks can hit them.

## 3. Custom weapons, e.g. Wyrmbreath (a dragon-fire stream)
**Feasibility: yes, fully server-side:** particles, sounds and plugin-applied damage. The only tricky part is
detecting that the player is *holding* right-click.

**Detecting "hold to use":**
- The `consumable` data component (in the game since 1.21.2) lets *any* item be held like food, with a very long use time and no
  eating animation. Paper exposes this through its data-component API. While the player is using the item → fire.
  The local test server runs 26.2, so this can be tested directly.
- Keep it behind one small "use detector" class, so a future API change only touches one place.

**Each tick while firing:**
- **Visuals:** built-in vanilla particles, the same ones cosmetic and particle-effect plugins use. No resource pack.
  Wyrmbreath mixes `FLAME`, `SMALL_FLAME`, `LAVA` sparks and `LARGE_SMOKE` with a `DRAGON_BREATH` haze. The Soulfire Censer uses
  `SOUL_FIRE_FLAME` and `SOUL`. Spawned along the cone with forward velocity (count 0 + direction as offset, so each particle
  flies outward), about 20-40 per tick. Plus looping vanilla sounds (`ENTITY_BLAZE_SHOOT`, `BLOCK_FIRE_AMBIENT`).
- **Hits, every 2-4 ticks:** living entities within about 6 blocks and within 25° of where the player is looking, *with line of sight*
  (a ray check, so it never hits through walls). Damage is applied as coming from the player, so PvP and claim plugins can cancel it. Targets are set on fire.
- **Never ignites blocks.**

**Cost and limits:** uses durability (below). A heat bar on the action bar locks the weapon for 3s when it overheats.
Main hand only, a per-player particle budget, and a damage cap per tick.

**Other weapon mechanics that are realistic:**
- Locked beam that ramps up damage (Guardian's Gaze): a particle line, and the lock breaks when line of sight is lost.
- Lunge or charge (Dreadlance): push the player forward with velocity, sweep for hits along the path. 26.2 spears already have lunge animations.
- Dash (Tempest Treads): velocity only, never teleporting, with a ray check so it can't clip through blocks.
- Arrow burst (Quillshot), chain lightning (visual-only lightning plus damage), gravity pull, shockwave ring with knockback,
  homing projectiles (steering item-display entities), decoys (Mirror Ward).

## Particles and colors
**Particles that take a color:**
- `DUST`: any RGB color, size 0.01-4.
- `DUST_COLOR_TRANSITION`: fades from one color to another over its lifetime. This is what cosmetic plugins use for "colored flames".
- `ENTITY_EFFECT`: the potion swirl, any color.
- `TINTED_LEAVES`: any color.
- `ITEM`, `BLOCK` and `FALLING_DUST`: take their color from whatever item or block you pick, e.g. slime-ball crumbs or lime-concrete dust.

**Fixed-color particles:** `FLAME`, `SOUL_FIRE_FLAME`, `LAVA`, `SMOKE` and campfire smoke use fixed textures. There's no orange soul fire and no green lava.
A resource pack could only recolor them for *every* fire in the game, so that's out.

**How to get custom-colored fire anyway:**
- **Build the color from dust:** stack `DUST_COLOR_TRANSITION` particles (e.g. orange→dark red for fire, lime→dark green for "green fire",
  with sizes shrinking along the cone), often mixed with a few real flames for texture.
  - *Orange soul-fire:* a `SOUL_FIRE_FLAME` core with an orange/amber dust halo.
  - *Green lava sparks:* small lime→green dust with a few `ITEM` crumbs from a lime dye or slime ball.
  - *Green smoke:* large (size 2-4) grey-green dust, plus `ENTITY_EFFECT` in a dark green.
- **Catch:** dust and potion-swirl particles **ignore velocity**; they drift in place. So a colored stream has to be *drawn* by spawning dust at points
  along the cone each tick. Only the real flames can be launched with speed. A mix of both reads best.

**Ground effects (e.g. Sovereign acid puddles, web zones, fire patches):**
- **Recommended: the zone is a vanilla lingering-potion cloud** (`AreaEffectCloud`), colored per boss (lime for the Sovereign).
  - Players already read a colored circle on the ground as a harmful area, and it has a clean, visible edge.
  - Damage or effects come from the plugin, and the cloud is an entity, so no blocks change.
  - Never use the `DRAGON_BREATH` particle on these clouds: players can bottle those clouds with glass bottles.
- **Flavor on top:** `ITEM_SLIME` / slime-ball `ITEM` bubbles inside the puddle, and `BLOCK` (slime block) splashes on impact.
- **Warnings that must always be visible** (e.g. where the Sovereign will land): add a flat **block display** on the ground (lime stained glass, very
  thin) plus a sound. Players can turn particles down to "minimal" in their settings, but display entities still render.
- **Accessibility:** never rely on color alone (red vs green). Pair each color with a distinct shape, particle or sound.

All presets live in one place (an `ability/fx` helper), so colors and densities can be tuned in one spot.

## Durability (all Occultech weapons and charms with active abilities)
No Slimefun energy on weapons. Every active weapon uses **item durability** instead.
- **Per-item max durability:** any item can have its own max durability (Paper `Damageable#setMaxDamage`, available since 1.20.5).
  Example: Wyrmbreath has 1200 durability and loses 1 per half-second of fire, so about 10 minutes of total fire per full repair.
  Necromancy items lose durability per summon.
- **Unbreaking:** handled through Slimefun's `DamageableItem` attribute, so Unbreaking works as players expect.
- **Never breaks:** at 1 durability the item stops working ("depleted") instead of being destroyed. A 160k-cost item should never vanish.
- **Repair:** in an anvil using that item's themed boss drop (e.g. Choir Ember for Wyrmbreath, Abyssal Lens for Guardian's Gaze). 26.2 has a
  native `repairable` item component. Slimefun blocks its items from anvils by default, so Occultech explicitly allows its own items.
- **Mending: disabled (recommended).** Repairing with boss drops gives mini-bosses lasting value after the gear is crafted, which fits
  "cheap repeat summons". Mending would make that loop pointless.

## Visuals: what needs a resource pack and what doesn't
**Why some things need a pack:** the player's game can only draw models and textures and play sounds that exist in the vanilla game files.
There is no way for a server to send new art to players except through a resource pack. So "not possible without a pack" means
*brand-new* models, textures and sounds only.

**What we can do without a pack:**
- **Custom player-head textures:** Slimefun already uses these for many items and blocks. Any texture uploaded as a skin works, e.g. altars, bowls, charms.
- **Display entities:** vanilla blocks and items that can be scaled, rotated and smoothly animated. They can build "models" such as floating
  runes orbiting a boss, a spirit at a servitor shrine, glowing sigils over the altar, or a phylactery.
- **Swapping to another vanilla model:** from 1.21.4 an item can use *any vanilla item's model*, e.g. a staff that looks like a blaze rod or trident.
- **Coloured dust particles, text displays with symbol art, and vanilla sounds** with pitch and volume changes.

**Adding a pack to a Slimefun addon:**
1. Slimefun items are normal items. Give each one a model id when it's defined (`SlimefunItemStack` accepts an `ItemMeta` consumer;
   on 26.x use the `item_model` / `custom_model_data` components).
2. The pack (models made in Blockbench, textures, `sounds.json`) maps those ids to art. Bosses play custom sounds by key, e.g. `occultech:sovereign.roar`.
3. Delivery: Paper can send **multiple packs** to a player (since 1.20.3), so Occultech's pack sits on top of the server's existing pack
   without merging them. Host the zip anywhere (GitHub release or the server's web host).
4. Keep it **optional**: everything falls back to vanilla or head visuals for players without the pack.
- **Cost:** art time, hosting, and updating the pack when Minecraft changes the pack format.
