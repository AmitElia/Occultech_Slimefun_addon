# Boss and mini-boss ideas (brainstorm, not committed to scope)

The **MC** column shows the Minecraft version that added the mob. The local test server runs 26.2, so all of them can be tested.

## Design rules (every idea must pass all of them)
1. **No griefing.** Fights never place, break, burn or change world blocks. Every visual "object" in a fight
   (hearts, phylacteries, wards, webs, barriers) is a plugin entity (display entity plus interaction hitbox) that is removed when the fight ends.
2. **Only what a plugin can do.** Use only standard Paper API: vanilla mobs, attributes, equipment, potion effects, projectiles,
   particles and sounds, display and interaction entities, boss bars. No client mods, resource packs, or packet tricks that multiplayer servers can't rely on.
3. **Built to resist abuse** (see the engine rules below). If an idea can't be protected against cheese or duplication, it gets cut.
4. **Every resource has its own purpose.** Each boss drop is a new material with its own recipes. It never replaces or substitutes
   an existing Occultech, Slimefun or other-addon resource. Vanilla drops are a curated list per boss (`mob_drops` in
   recipes.yml): common items only, never ones other progression gates (totems, skulls, nether stars), and only from the
   boss itself - extra mobs spawned in the fight drop nothing.
5. **No mechanics that are fragile across players or server events.** Nothing that takes or holds player items, swaps inventories, or
   depends on precise client-side timing.
6. **Fun, and cheap to repeat.** Every attack is telegraphed (particles and sound before it lands). No unavoidable one-shots.
   Phases are easy to read. Repeat summons are cheap relative to the player's progression (see costs below).

## Engine rules against abuse (apply to every boss and mini-boss)
- **Tagging:** every summoned entity (boss, extra mobs, mounts, clones) is tagged in its persistent data. Tagged entities give no vanilla drops or XP
  on death; the boss's curated drops and XP are handed to contributors with the rest of the loot.
  They can't be leashed, name-tagged, ridden by players, traded with or converted (e.g. zombie → drowned). They can't use portals.
- **No block changes:** a global listener cancels block changes, block damage from explosions and fire started by tagged entities
  or their projectiles. Lightning is visual only, with damage applied by the plugin.
- **Arena:** each fight has a radius around the altar.
  - If the boss is pulled outside, it goes back to the center and heals slightly.
  - Only damage from players inside the arena counts.
  - The boss is immune to suffocation, cramming, drowning (unless aquatic), fall damage, and lava or void damage from being pushed.
    Only player damage matters.
  - Vehicles (boats, minecarts) can't trap bosses.
- **Anti-pillaring:** if no player in the arena can be reached for a few seconds, the boss becomes immune and uses a ranged or
  gap-closing ability. It never teleports players.
- **Loot:**
  - Drops go directly to each contributor, given only to them and never dropped on the ground for others to grab.
  - To count as a contributor, a player must deal a minimum share of damage *and* be in the arena for part of the fight, so AFK players get nothing.
  - Creative mode or `/sf cheat` involvement voids the loot.
- **Limits:** one active fight per circle, a configurable cap per player and per server, and a cap on how many extra mobs a fight can have.
- **Crashes and chunk unloads:** if a fight's chunk unloads or the server restarts, the fight fails cleanly. Tagged entities are removed on
  load, the catalyst is refunded (logged), offerings are not refunded, and no loot is given. This way a crash can't duplicate items.
- **Permissions:** summoning checks Slimefun's protection integration, so a player can only summon where they're allowed to build.
- **Performance:** a budget for particles and entities per fight, and one scheduler task per fight.

## Repeat costs (rule 6)
- **The circle and altar are built once and reused.** Each summon only consumes offerings and a catalyst.
- **Lesser (mini-boss) summon cost** should be about 1-5% of what it costs to build that tier's circle. Major summons cost about 3-5× a lesser summon. Checked by `tools/cost_model.py`.
- **Drops per win:** about 3-5 wins should be enough for one capstone item of the next tier, so progress feels steady.
- **Fight length:** 1-3 minutes for a mini-boss, 4-8 minutes for a major boss.

## Mounted and cavalry
| Name | Base | Gimmick | Unique drop and its purpose | MC |
|---|---|---|---|---|
| Dread Lancer | armored Zombie on a Zombie Horse, with a spear | Lance charges across the arena, warned by a particle line. At 50% HP the rider is unhorsed: the horse fights as a second enemy and the rider becomes faster on foot | *Lancer's Pennant*: used in charge and mobility weapons | 1.21.11+ |
| Dune Caravan | Camel Husk carrying a Husk and a Parched archer | Two riders with two roles: the husk charges, the Parched shoots slowness arrows. Kill the camel to split them up | *Sunbaked Hide*: used for armor upgrades | 1.21.11+ |
| Tidebreaker | Drowned on a Zombie Nautilus, with a trident | Water-arena fight (the circle must be near water, checked when summoning). Diving ram charges and trident volleys | *Nautilus Core*: used in ocean-tier machines | 1.21.11+ |
| Stormcaller | Skeleton Horseman | Calls lightning, marked on the ground before it strikes (visual only, damage from the plugin, no fire). Spawns horsemen in waves | *Stormglass Shard*: charges weapon abilities | any |

## Illagers
| Name | Base | Gimmick | Unique drop and its purpose | MC |
|---|---|---|---|---|
| Archevoker | Evoker, scaled up | Fangs in circle-shaped patterns (lines, rings, spirals). Tethered vexes that can't leave the arena. Survives death once while its phylacteries (display entities) stand, so players must break those first | *Evoker's Sigil*: used in ritual upgrades. It does NOT drop a vanilla Totem | any |
| Mirrored Magus | **Illusioner** (never spawns in survival) | Spawns decoy clones (tagged entities, no drops). Hitting a clone makes the player glow briefly and lets the real Magus reposition | *Mirror Dust*: used in illusion or utility items | any |
| Warband Captain | Pillager captain riding a Ravager | *Reworked for rule 1:* no block breaking. Telegraphed ravager charges that knock back and stun, plus crossbow volleys from pillager extras | *Warband Standard*: used in group-support items | any |
| The Unbound | Vindicator named "Johnny" | Attacks everything, including its own extras, so players can bait it. Speeds up as its HP drops | *Frenzied Edge*: used in berserker weapons | any |
| Witch Coven | 3 Witches | One heals, one curses, one throws splash potions; their roles rotate. Potions only affect players | *Coven Brew Base*: used in potion or charm items | any |

## Undead
| Name | Base | Gimmick | Unique drop and its purpose | MC |
|---|---|---|---|---|
| Hollow Warlord | Wither Skeleton, scaled up, netherite gear | Wither-aura sword sweeps, a bodyguard squad, speeds up as its HP drops | *Warlord's Brand*: its own recipes in Hollow-tier weapons. It does not substitute Nether Stars or any other resource, and does not drop Wither Skeleton skulls | any |
| Volley | Skeleton / Stray / Bogged | A rapid-fire archer that cycles arrow types (slowness, poison, spectral). Hides behind ward entities that must be broken, not blocks. Each volley is warned by a draw sound | *Fletcher's Quill*: used in ranged weapons | any (Bogged 1.21) |
| Night Matriarch | giant Phantom | Only summonable at night. Warned dive-bombs, plus a capped swarm of phantoms. Immune to burning in sunlight | *Dusk Membrane*: used in movement items | any |

## Other mobs
| Name | Base | Gimmick | Unique drop and its purpose | MC |
|---|---|---|---|---|
| Tempest | Breeze | Knockback from wind charges (capped). A shrinking ring of damage particles marks the arena edge; nothing pushes players into the void or lava | *Tempest Core*: used in wind or mobility items | 1.21 |
| Heartwood Horror | Creaking | Can't be damaged while its linked hearts stand. The hearts are display entities placed around the circle (not real blocks) | *Heartwood Resin*: used in regeneration items | 1.21.4+ |
| Brood Mother | giant Spider | Egg sacs (display entities) hatch cave spiders unless broken. Web zones are shown with particles and give slowness; no real cobwebs are placed | *Brood Silk*: used in trap or utility items | any |
| Blaze Choir | 3 Blazes | Circle the altar with rotating shields. Their fireballs are custom projectiles that start no fires | *Choir Ember*: used as fuel for powered ritual machines | any |
| Corrupted Colossus | Iron Golem | The tech-meets-occult boss for the "Occultech" name. Warned shockwave slams | *Corrupted Circuit*: used in Occultech machines (a separate item, not a Basic Circuit Board substitute) | any |

## Cut or on hold
- **Voidwalker (Enderman):** cut. Taking held items breaks rule 5 (risk of duplication or lost items), and teleporting endermen are hard to keep in an arena.
- **Siege Captain:** replaced by *Warband Captain* (no block breaking).
- **Shulker Bastion:** cut. Levitation into hazards is easy to cheese (blocks placed overhead, water buckets, elytra) and not much fun.
- **Echo of the Deep (Warden):** on hold. Vanilla warden AI (digging away, sonic boom through walls, extreme damage) is hard to control.
  Only revisit with a heavily customized ruleset.

## Structure ideas (keep open)
- **Two layers of summons:**
  - *Major rituals*: big circles, a tier boss, and the drops that gate tier progression.
  - *Lesser rituals*: small circles, cheap and repeatable mini-bosses whose drops feed side items like weapons, charms and armor upgrades.
- **Rituals going wrong** (Occultism-style): an incomplete or unstable ritual may summon a random mini-boss from that tier's pool
  instead of the intended result, but never something from a higher tier. Offerings are still consumed; no world damage.
- **A pool of mini-bosses per tier**, which lets content grow without new tiers.
