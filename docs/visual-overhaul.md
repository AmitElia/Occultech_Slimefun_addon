# Visual overhaul plan: resource pack via Nexo (not started)

Goal: give Occultech its own look - custom items, armor, blocks, animated bosses, menus, glyphs and effects - using the
server's Nexo to build and send the resource pack, while everything keeps working (with today's vanilla visuals) for
players who decline the pack. Builds on [visual-effects.md](visual-effects.md).

## 1. How the pieces fit

| Piece | Tool | How Occultech uses it |
|---|---|---|
| Pack build and hosting | **Nexo** (paid, already on the production server) | Occultech ships its assets inside the jar (`src/main/resources/pack/`) and copies them on startup to `plugins/Nexo/pack/external_packs/occultech/`; Nexo merges external packs into the one pack it sends ([Nexo resource pack docs](https://docs.nexomc.com/configuration/resourcepack)). No Nexo item configs needed for our items. |
| Item looks | vanilla `item_model` data component (1.21.4+) | Each Slimefun item stack gets `item_model = occultech:<id>`. Without the pack the client falls back to the vanilla material, so nothing breaks. |
| Armor looks | vanilla `equippable` component + equipment assets | Abyssal and Hollow armor point at `occultech:abyssal` / `occultech:hollow` equipment textures (worn layers, optional glow layer). |
| Block looks | display entities with custom models over the real block | Slimefun blocks stay real blocks (Slimefun's storage needs that); a model is shown on top/around them. See section 3. |
| Animated bosses | **BetterModel** (free, open source, Blockbench models, display-entity based, no shaders) ([GitHub](https://github.com/toxicity188/BetterModel)) | Bosses keep an invisible vanilla mob as the hitbox and AI; a BetterModel rig is attached and animations are triggered from our boss states. |
| Menus, glyphs, HUD | pack font: private-use characters + negative-space glyphs | Menu titles (they're plain strings in Slimefun) carry a shifted background glyph -> full custom menu art. The same glyph font powers sigils, runes and halos in text displays. |
| Particles | retextured vanilla particle sprites | Only obscure particles that our effects own (section 6). |
| Sounds | `assets/occultech/sounds.json` | `playSound("occultech:boss.gallus.cluck")` etc. |

Code stays in `setup/` and `items/` for anything pack-aware; `boss/` only gains a small `BossVisual` interface so the
model engine stays optional. A config switch `visuals.resource-pack: true/false` turns the pack-based visuals on.

## 2. Items (~120)
- One 16x16 (or 32x32 for showpieces) texture per item, sharing a palette per tier: tier 0 bone/chalk/candle wax,
  tier 1 violet/silver, tier 2 teal/prismarine, tier 3 deep sculk/cyan + crimson.
- Held weapons get 3D handheld models (Wyrmbreath, Gaze, Censer, Anchor, Dreadlance, Stormstring); talismans and sigils
  get animated glow (`.mcmeta` frames).
- Order: materials and sigils (seen most) -> weapons/armor -> contracts, talismans -> boss drops -> decor.

## 3. Blocks
- **Full-cube blocks** (glyphs, machines): an item-display "skin" scaled to 1.002 sits exactly over the block, so the block
  looks fully custom while staying a normal block for Slimefun, cargo and break handling.
- **Shaped blocks** (altars, offering bowls, pedestals, shrine, Nexus, Guardian Eye, Wind Chime): the base block is a
  low/open vanilla block with the right collision (slab, wall, lectern...), and the model adds the real shape -
  carved altar tops with candles, bowls with a lip, pedestals with a floating plate, the shrine as a stone niche with a
  spirit inside.
- Displays only exist while players are near (as decorations already do), one per block, no per-tick updates unless
  animated.
- Circle glyphs: the chalk/bound/abyssal/hollow glyphs become flat painted runes on the floor (a thin glyph block plus a
  glowing decal), so a finished circle finally looks like a drawn ritual circle.

## 4. Armor
- Abyssal: barnacled dark-teal plate with glowing seams; Hollow: hollowed bone-and-sculk plate with cyan cracks.
- Worn layers via equipment assets; matching item icons; optional emissive seams.

## 5. Bosses (BetterModel)
| Boss | Model idea | Key animations |
|---|---|---|
| Gallus | undead rooster the size of a ghast, armored knight rider | strut, wing-leap, slam, egg-lay, unhorse, hollowing transformation, frantic last chase |
| Heartwood Horror | bark-and-resin giant with glowing heart cavity | frozen pose, lunge, creak-turn, root snare |
| Corrupted Colossus | iron golem rebuilt with conduits and pylons | rear-up slam, overload sparks |
| Hollow Warlord | armored wither skeleton with banner | sweep wind-up |
| Drowned Elder / Abyssal Warden | barnacled elder guardians with tendrils | beam charge, tidal surge |
| others | keep vanilla mobs with custom textures where possible | - |
Priority: the four gate bosses first (Sovereign, Archevoker, Drowned Elder, Gallus), then minis by popularity.
Each boss keeps working without the pack (the vanilla mob is shown instead of the model).

## 6. Glyphs, menus and effects
- **Glyph font** `occultech:glyphs`: pentagram, hexagram, tier sigils, 24 runes, crown pieces, footprint shapes. Used by:
  - ground telegraphs (filled sigil decals instead of potion clouds), the summoning sigil, ritual circles lighting up;
  - Floor Sigil, Hollow Halo styles, Aura footprints;
  - boss bars with a framed title per boss.
- **Menus**: altar, offering bowl, shrine, Nexus, Arcane Altar, Codex - each gets a painted background (stone tablet,
  parchment book for the Codex, a ritual circle for the altar) with slot frames drawn where items go.
- **Particle retextures** (only ones Occultech effects use, chosen to be rare elsewhere): e.g. `nautilus` -> soul motes,
  `glow` -> rune sparks, `dust_plume` -> chalk dust. Note: these also change vanilla uses of those particles server-wide.
- **Sounds**: boss voices and ritual chants; shrine spirit whispers; altar infusion swell.

## 7. Phases and effort
| Phase | Content | Who | Size |
|---|---|---|---|
| 0 | pipeline: assets in jar -> Nexo external pack, `item_model`/`equippable` on stacks, config switch, self-test that every model and texture referenced exists | me | 1 session |
| 1 | glyph font + menus + sigil decals + telegraph upgrade | me (geometric art is my strength) | 1-2 sessions |
| 2 | item textures (placeholders by me, final art by an artist or commissioned pack) | me + artist | large |
| 3 | block skins and shaped models | me for simple geometry, artist for detailed | medium |
| 4 | armor sets | artist | medium |
| 5 | boss models and animations (BetterModel) | 3D modeler/animator; me for integration | large |
| 6 | particle retextures and sounds | me + sound source | small |

## 8. Honest assessment of what I can make
Samples in [art-samples/](art-samples/) (`preview.png`), made procedurally from code:
- **Good:** geometric art - sigils, runes, circles, pentagrams, GUI frames, slot borders, decals, animated glow frames,
  palette swaps and consistent recolors. The 64x64 sigil sample is usable as-is.
- **Usable as placeholders:** 16x16 item icons. They read (the Spirit Essence vial works) but have flat shading,
  weak outlines and crude symbols at 16px (the Hollow Sigil's pentagram fills in to a star).
- **Weak:** hand-drawn organic pixel art at the level of Occultism (its icons have careful shading, outlines and a
  consistent hand-made style), and 3D boss models with good UV textures and natural animation. I can write the
  model/animation files and wire everything, but they wouldn't look professional.
- **Recommendation:** I build the whole pipeline, all geometric assets (glyphs, menus, decals, effects) and placeholder
  icons; item, armor and boss art come from an artist or a licensed asset pack (check licenses - Occultism's art can't be
  reused without its authors' permission), dropped into the same pipeline file by file.
