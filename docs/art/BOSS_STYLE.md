# Boss art and encounter design: lessons from Volley

This is the working brief for future Occultech bosses. Read it with [STYLE.md](STYLE.md),
[boss-art-sessions.md](../boss-art-sessions.md), [boss-visual-overhaul.md](../boss-visual-overhaul.md), and
[boss-rework-plan.md](../boss-rework-plan.md) before starting a model. These notes record the user's feedback from the
Volley pass on 2026-10-10. Volley is a promising first pass, **not a signed-off production asset**; its rig, attack
poses, BetterModel import, and in-game appearance still need review.

## Direction the user established

- **Original occult boss, recognizably Minecraft.** Use Blockbench cuboids, broad angular shapes, consistent texel
  density, and restrained pixel textures. The silhouette can depart from its vanilla carrier. Use mod models such as
  [Threateningly Mobs](https://www.curseforge.com/minecraft/mc-mods/threateningly-mobs/gallery) to study shape
  hierarchy and material contrast, never to copy a model, texture, or animation.
- **Readable character before spectacle.** For a humanoid, retain an understandable head, torso, two arms, two legs,
  stance, and held equipment. The first Volley siege-engine blockout read as grotesque; the user preferred the
  armored skeletal arbalest bearer. Do not turn an anatomy-specific brief into a walking weapon or a pile of parts.
  This is a lesson for humanoid bosses, not a rule that moths, slimes, guardians, or ritual machines must look human.
- **Keep the torso legible.** A large prop should be carried or mounted where its function is clear. The centered
  arbalest obscured Volley's chest and waist and produced an unwanted visual reading. The revised weapon sits at his
  **right** side (model +X), held by the right hand, slightly pointed outward; the left arm rests at his side. Check
  front, three-quarter, side, and player-eye views for accidental silhouettes and blocked face/chest details.
- **Scary through identity and timing, not gore.** The ritual binding, yoke, lanterns, skull sight, counting jaw, and
  huge crossbow explain this boss's story and attacks. Slow stillness followed by a committed motion can be more
  unsettling than extra spikes, limbs, or constant effects. Keep one face light and a few purposeful magic accents.
- **Texture is part of the design.** The user asked for the humanoid revision to be textured, not left as flat material
  colors. Put major mass in geometry and seams, wear, grain, and shading in the atlas. Use one coherent texel density,
  muted material ramps, small selective glow, and enough contrast to read at combat distance. Review actual textured
  geometry from multiple angles, not just the PNG atlas.
- **Gameplay truth stays visible.** Never cover floor warnings with effects or a low, wide model. Decorative parts
  should not look like hittable weak spots. An attack pose must lead into the server's real telegraph and contact
  timing; animation and Mythic FX do not create a second damage path.

## Workflow that worked, and the next gate

1. Write the boss's identity anchors and encounter tells before modeling. Preserve established mechanics and source
   material in `boss-visual-overhaul.md` and `boss-rework-plan.md`. Treat concepts there as proposals until reviewed.
2. Build an editable `.bbmodel` with a sensible bone hierarchy. Render real cuboids as silhouette and clay in front,
   side, top, three-quarter, and player-eye views beside a 1.8-block player. Correct anatomy and prop placement before
   relying on texture to make a weak shape readable.
3. Paint and UV-map the chosen geometry; verify atlas coverage, embedded texture identity, and a rendered front,
   three-quarter, and player-eye view. Volley's first texture pass uses 256×256, 95 cuboids, and 24 named bones; those
   counts describe this asset, **not** a quota for the roster.
4. Keep authoring scripts with the model so later changes regenerate the `.bbmodel`, atlas, UVs, and previews together.
   Volley's source is `tools/art/bosses/volley_s1.py` and `volley_texture.py`; review assets are in
   `docs/art/bosses/volley/overhaul/s1_silhouettes/`.
5. Then test in BetterModel and the real client. Blender renders are design reviews, not evidence of the in-game
   hitbox, material behavior, animation, pack delivery, or combat readability. Pose test before declaring a final rig.

## Status and boundaries

- The discarded Brood Mother visual studies are not a template. Its direction remains open; start it afresh when its
  session begins. Do not recreate or refer to deleted Brood Mother model files.
- Volley has a textured, right-side arbalest blockout and offline renders. Its user feedback establishes the direction
  above; it does not approve every detail or complete art sessions 2–8.
- Keep the production asset separate from optional MythicMobs / BetterModel integration. Occultech owns fight
  identity, telegraphs, damage, loot, and cleanup; the visual bridge may trigger cosmetic states and effects.
