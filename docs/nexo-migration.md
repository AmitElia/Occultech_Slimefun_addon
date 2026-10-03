# Moving Occultech's blocks to Nexo (Session N, second half)

Session N made Occultech's blocks **custom blocks the way Nexo makes them**, without Nexo: each block look owns a vanilla
block state set aside for it, and Occultech's resource pack shows the block's model for that state. Solid blocks use
powered note-block states (Nexo's `NOTEBLOCK` type); the flat, walk-through ritual glyphs use disarmed tripwire states
(Nexo's `STRINGBLOCK` type); models smaller than their cube use chorus-plant states with neither up nor down (Nexo's
`CHORUSBLOCK` type - a note block would hide its neighbours' faces). This file is the plan for the day the plugin runs
on the Nexo server.

## What exists now

| Piece | Where |
|---|---|
| The states, given out once and never changed (placed blocks are stored as their state) | `tools/art/block_states.json` (append-only) |
| The states per block look, read by the plugin | `src/main/pack/occultech-pack-blocks.txt` (generated) |
| Blockstate files: our states show our models, every other state keeps vanilla's look | `assets/minecraft/blockstates/note_block.json`, `tripwire.json` in the pack (generated) |
| The one place that places and reads a block's look | `items/CustomBlockService` (`place`, `lookOf`, `ensure`) |
| Old display skins: converted to custom blocks when their chunk loads | `items/BlockSkinService.adopt` |
| A draft Nexo item config for the same blocks | `docs/nexo/occultech-blocks.yml` (generated, untested) |
| Mode switch | `custom-blocks.mode` in config.yml: `auto` (custom blocks unless Nexo is installed), `blocks`, `skins` |

Paper must have `block-updates.disable-noteblock-updates`, `disable-chorus-plant-updates` and `disable-tripwire-updates` set to `true` in
`config/paper-global.yml` (Nexo needs the same); the plugin warns at startup if they're off.

## Why not just keep our states on the Nexo server

Nexo owns the note-block and tripwire states there: it writes its own `note_block.json` / `tripwire.json`, hands out
states for the server's other custom blocks by `custom_variation`, and resets vanilla note blocks. Two systems
claiming the same states would show each other's models. So with Nexo installed:

- `custom-blocks.mode: auto` keeps Occultech on **display skins** (the older interim) until the hookup below is done.
- The pack Occultech hands to Nexo (`resource-pack.mode: nexo`) leaves out `assets/minecraft/blockstates/` so it
  can't clash with Nexo's.

## The hookup (with Nexo installed, so it can be tested)

1. **Nexo items.** Copy `docs/nexo/occultech-blocks.yml` into `plugins/Nexo/items/`, check it against the installed
   Nexo's docs (key names, `directional` for the Occult Forge, `STRINGBLOCK` for glyphs), `/nexo reload all`, and check
   each block in game. The models are already in Occultech's pack (Nexo merges it as an external pack).
2. **A Nexo backend in `CustomBlockService`.** Add `compileOnly` Nexo API and, when Nexo is present:
   - `place(block, id, look, facing)` -> `NexoBlocks.place("occultech_<model>", location)` (directional: the facing
     variant);
   - `lookOf(block)` -> `NexoBlocks.customBlockMechanic(block)` -> its Nexo id -> back to (item, look, facing);
   - `ensure` and placement are unchanged around them.
   Slimefun keeps its block data by location as now; only the vanilla state under it changes.
3. **Convert placed blocks.** A command (`/occultech skins <radius>` already re-runs `ensure` on every Occultech
   block nearby) re-places each block through Nexo - its look comes from the old state or the old skin, as now.
4. **Mode.** Set `custom-blocks.mode: nexo` (new value) and retire the skins fallback once everything is converted.

## Things to check on the Nexo server

- Placing, breaking (drops come from Slimefun, not Nexo), right-click menus, Slimefun's block data surviving.
- Glyph circles are still walkable and still detected (detection reads Slimefun ids, not block types).
- The Tidal Tile's right-click looks, the Occult Forge's facing.
- Nexo's mining speed and sounds for the blocks (`hardness`, `block_sounds`).
