# Visual effects: research and plan (not implemented)

How to get more refined effects out of vanilla visuals on Paper 26.2 (no resource pack), and where they would improve
Occultech the most. Nothing here is built yet; it is a menu to pick from.

## 1. The toolbox

| Tool | What it is good for | Notes |
|---|---|---|
| **Shaped particles** (math on points) | circles, helices, spirals, pentagrams, cones, waves, rising rings | Points on a parametric curve, a few per tick. Pentagram: 5 points on a circle, joined in order 0-2-4-1-3. A rotating version just adds an angle offset each tick. Libraries like [EffectLib](https://www.curseforge.com/minecraft/bukkit-plugins/effectlib) (Helix, Vortex, Star, Warp, Wave...) show the patterns, but they're simple enough to write in-house. |
| **Directed particles** | sparks shooting outward, flames along a cone, blood spray | `count = 0` turns the offset into a velocity: each particle flies in a chosen direction ([Paper particles](https://docs.papermc.io/paper/dev/particles/)). Already used by Wyrmbreath. |
| **Colored particles** | any color: `DUST` (+ size), `DUST_COLOR_TRANSITION` (fades from one color to another), `ENTITY_EFFECT` (colored potion swirls, optional alpha), `NOTE` (offsetX picks the color) | Color is free; shape and motion are what make an effect read as "magic". |
| **`TRAIL` particle** (1.21.4+) | a mote that flies from A to B over N ticks with a color | One packet, smooth client-side motion: homing souls, energy drawn into an altar, life drained into a weapon ([Paper API](https://jd.papermc.io/paper/1.21.4/org/bukkit/Particle.html)). |
| **`VIBRATION`** | a pulse travelling to a block or entity | Warden-style "signal" lines. |
| **Block/item particles** | blood (`BLOCK` with redstone/nether wart block), splinters, gore, sculk splatter | No block changes; e.g. [Custom Blood Particles](https://modrinth.com/plugin/custom-blood-particles) makes puddles from particles alone. |
| **Display entities** (Text / Block / Item) | ground sigils, rotating runes, beams, shields, halos | Scaled, rotated, glowing, full-bright; the **client interpolates** transformation and movement, so one update every few seconds animates smoothly ([Paper display entities](https://docs.papermc.io/paper/dev/display-entities/)). Can be shown to chosen players only. |
| **Block display "lasers"** | solid beams | A thin glowing block (e.g. light-blue concrete or end rod) scaled to the beam's length and rotated to point at the target; interpolate its length to "grow" the beam. Crisper than particle lines, unaffected by the player's particle setting. |
| **Vanilla beams** | the real guardian laser and end-crystal beam | `Guardian#setLaser(true)` needs a target; `EnderCrystal#setBeamTarget(loc)` draws the end beam between two points ([Spigot API](https://hub.spigotmc.org/javadocs/spigot/org/bukkit/entity/EnderCrystal.html)). An invisible crystal (unhittable) can beam "power" between objects. [GuardianBeam](https://github.com/SkytAsul/GuardianBeam) does this with packets. |
| **Text displays with glyphs** | runes, sigils, ☽ ✦ ⛧ symbols floating or laid flat | Billboard FIXED + rotated 90° lays text on the ground like a painted sigil. |
| **Sounds layered with visuals** | readability of telegraphs | Pitch rises as a charge fills; a distinct sound per attack. |

**Limits that shape the design**
- Particles are only sent within **32 blocks** unless spawned with `force` (then 512) ([discussion](https://www.spigotmc.org/threads/increase-distance-of-particle.82309/)). Arena telegraphs at radius 24 need `force`.
- Players who set **Particles: Minimal** don't see most particles. **Important telegraphs** (where an attack will land) should therefore use display entities or a ground sigil, with particles as decoration.
- Budget: aim for **< 100 particles per tick per effect** near players; prefer interpolated displays for anything that should look smooth.
- Per-player visibility (`Player#spawnParticle`, hidden displays) lets cosmetics be shown only to the people who want them.

## 2. Reusable effect kit (proposed `ability/fx/` package)
One small library used by bosses, rituals, blocks and items, so effects look consistent:
- `Sigil` - a flat rotating ground sigil (circle + pentagram/hexagram + runes) from display entities. Color and size are
  parameters; it can pulse, fill (progress) and shatter.
- `Telegraph` - replaces today's potion-cloud circles: a sigil ring that fills over the warning time, using a display
  entity so particle-minimal players still see it.
- `Beam` - block-display beam (charging thin, firing thick, fading), with optional end-crystal core; replaces particle lines.
- `Helix` / `Spiral` / `Ring` / `Burst` / `Trail` - parametric particle shapes.
- `Gore` - blood/ichor puffs and ground splats by creature type (red, green poison, soul-blue for spirits, sap for the
  Horror), with an intensity setting and a per-player off switch.
- `Palette` - the colors already used per tier (gold T0, violet T1, teal T2, sculk/cyan T3).

## 3. Where it would help most

### Boss fights (biggest win: readability)
| Fight | Today | Proposed |
|---|---|---|
| Every telegraph | potion-cloud circle + one dust ring | `Telegraph` sigil that fills up; red rim when about to hit; visible on minimal particles |
| Abyssal Warden / Drowned Elder beams | dust particle lines | `Beam`: thin charging beam that thickens and flashes white at lock; real guardian-laser look via `setLaser` on the caster |
| Outrider snipe | dust line + visual lightning | `Beam` with a scope-glint ring on the target, then lightning |
| Blaze Choir shield | flame ring | rotating translucent shield (item display of orange stained glass) around the shielded singer |
| Corrupted Colossus pylons | dust line to the golem | end-crystal beams pylon → golem (the vanilla look of "power feeding in") |
| Heartwood Horror hearts | dust pulse | `TRAIL` motes drifting heart → Horror (shows the link), sap `Gore` when hit |
| Gallus eggs / Hollow eggs | particles | hatching timer sigil under each Hollow Egg (fills toward the hatch) |
| Doppelganger echo | ink + dust | the echo shown as a translucent **Mannequin** walking the path (much clearer than particles) |
| Phase changes | broadcast text | a short arena-wide sigil flash + sound sting for each phase |
| Hits on bosses | vanilla | small `Gore` puffs in the creature's color (optional, toggleable) |

### Rituals
- The circle **lights up glyph by glyph** while the ritual runs (`TRAIL` motes from each bowl to the altar, then a rising
  `Helix` over the altar), ending in a `Burst`.
- Summoning: a large ground sigil grows across the arena before the boss appears (also shows the arena size).
- Repair ritual: sparks spiral into the weapon. Failure: the sigil cracks and smokes.

### Blocks
- Machines: a slow `Ring` of runes while working (Forge: embers; Condenser: souls drawn in with `TRAIL`; Assembler: a
  small rotating sigil above it).
- Servitor shrines: the spirit leaves a faint `TRAIL` to whatever it works on; Ward draws its border as a dim sigil ring
  occasionally instead of only when the menu is open.
- Guardian Eye: a `Beam` instead of dust.

### Cosmetics (blocks)
- Rune Obelisk / Orrery: already display-based; add `TRAIL` sparks between orbiting parts.
- New possible decor: a **Floor Sigil** block that lays a slowly rotating colored pentagram/hexagram (text/item displays)
  on the floor - the "magic circle" decoration players ask for.

### Weapons
- Wyrmbreath / Censer: directed flame cone already; add heat shimmer (`DUST_COLOR_TRANSITION` orange → grey smoke) and
  ember sparks on hit.
- Guardian's Gaze: `Beam` (block display) - steady and readable, grows with the damage ramp.
- Stormstring Bow: a `TRAIL` of electric sparks on the arrow's path, then the lightning.
- Dreadlance: a crimson `TRAIL` from the hit target to the player on each lifesteal heal.
- Necromancy: summon sigil under raised minions; soul `TRAIL` when they're dismissed.

### Player cosmetics (talismans)
- Hollow Halo: a display-entity halo (a flat ring of tiny items) that bobs smoothly instead of particles.
- Aura Talisman: more styles from the kit: rune footprints (flat text displays that fade), a slow `Helix` around the player,
  floating motes.
- A wing cosmetic is possible with item displays riding the player, but it costs more entities per player; keep it out of
  scope unless asked.

## 4. Suggested order
1. `ability/fx` kit: `Sigil`, `Telegraph`, `Beam`, shapes, palette (one sprint, then reused everywhere).
2. Replace boss telegraphs and beams (readability in fights is the top gameplay benefit).
3. Ritual light-up and summoning sigil.
4. Weapon and block polish.
5. Cosmetic additions (Floor Sigil block, more Aura styles).
