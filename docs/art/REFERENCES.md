# Art references: arcane Minecraft mods

What we learn from the best-looking magic mods, and what we take into **the Occultech look** (bottom; the rules
themselves are in [STYLE.md](STYLE.md)). **We study styles, never copy art:** no textures, palettes picked from
their files, or traced shapes. Read this before every art session.

The notes describe each mod's look as it appears in play and in its screenshots; check the mod pages for current
visuals.

| Mod | Look | What we take |
|---|---|---|
| [Malum](https://www.curseforge.com/minecraft/mc-mods/malum) | Dark, heavy materials (soulstone, runewood, hallowed gold) set against vivid spirit colours that glow and shift hue; particles with soft, colour-gradient trails; additive bloom on spirits. | **Dark vessel, living light**: the magic is the only saturated, glowing thing. **Chromatic ramps**: glow colours shift hue from dark to light (ember red -> orange -> pale yellow). |
| [Eidolon: Repraised](https://www.curseforge.com/minecraft/mc-mods/eidolon-repraised) | Gothic: pewter, silver, bone, black stone and gold, with soul-blue light; ornate but compact item silhouettes. | Restrained metals and bone as the base; ornament on the silhouette (spikes, crowns), never noisy texture. |
| [Occultism](https://www.curseforge.com/minecraft/mc-mods/occultism) | Chalk pentacles drawn on the floor, glyph blocks, otherworldly purple/green spirits; ritual circles as the centrepiece. | Ritual circles are hero art: a band of marks between two rings, a figure, a core (our sigils). |
| [Ars Nouveau](https://www.curseforge.com/minecraft/mc-mods/ars-nouveau) | Bright, friendly and rounded; purple and gold; glyph icons on plaques; lots of colour. | Charm: little **twinkles** around magical things, clear readable glyph icons. |
| [Botania](https://www.curseforge.com/minecraft/mc-mods/botania) | Soft, natural, pastel; mana blue, petal pinks; flowers everywhere; clean shading. | Natural materials (petals, leaves) get soft, domed shading; pastel accents for the blossom style. |
| [Thaumcraft](https://www.curseforge.com/minecraft/mc-mods/thaumcraft) | Brass, wood and parchment; muted, hand-painted; aspects as round coloured icons. | Muted materials make the accent pop; an icon language of round, colour-coded symbols (our runes). |
| [Blood Magic](https://www.curseforge.com/minecraft/mc-mods/blood-magic) | Deep crimson liquids in glass, dark stone altars, ornate runes. | Liquids in glass read through a bright highlight and a dark rim (Spirit Essence). |
| [Iron's Spells 'n Spellbooks](https://www.curseforge.com/minecraft/mc-mods/irons-spells-n-spellbooks) | Each spell school has its own colour; high-contrast, glowing spell icons; flashy particle effects. | **Tier = colour family**, applied everywhere (gems, sigils, flames all come per tier). |
| [Forbidden & Arcanus](https://www.curseforge.com/minecraft/mc-mods/forbidden-arcanus) | Dark-fantasy relics with saturated gem accents; strong, ornate silhouettes. | Gems as accents set into dark metal; facets with hard edges. |

## The Occultech look (our own synthesis)
1. **Dark vessel, living light.** Bodies are desaturated and dark (sculk, iron, bone, smoked glass, ash). Magic is the
   only saturated thing on an item, and it glows.
2. **Chromatic ramps.** Every ramp shifts hue (shadows toward blue/violet, light toward warm/white). Glows are
   *gradients*, never one flat colour.
3. **Glowing inlay.** Magic is carved in: sigil lines, runes and seams are shaded like raised, glowing tubes (the sigil
   look) - our signature motif.
4. **The twinkle.** Magical items carry 1-3 small four-point twinkles (`Icon.twinkle`), which animate where possible.
   They always stand apart from the object's outline.
5. **Hard facets.** Gems and metals have defined edges: a bright seam on the lit side, a dark one on the shadow side,
   light and dark faces alternating.
6. **Everything magical moves.** Items get animation frames (a glint sweep, twinkles), particles have a life cycle,
   step marks appear, peak and fade.
7. **Bold, readable shapes** (Session A): a unique silhouette at 1x beats detail.
8. **Tier = colour family**: T0 ember on chalk/bone, T1 violet + spirit cyan, T2 abyss teal + sea glow, T3 sculk +
   hollow cyan + crimson.

## Our own reference assets (approved by the user)
- Pentagrams and tier sigils: `session-b/review-sigils-r2v2.png` (liked a lot)
- Animated soul flame and sparkle: `session-b/preview-*.gif` (the user's favourite - animation is the bar to meet)
- Cut gems with twinkles: `session-b/review-pieces-r3v3.png`, animated in `review-particles-r3v3.png`
- Paw print and runes: `session-b/review-prints-r2v3.png`, `review-runes-final.png`
- Session A icons: `session-a/review-final.png` (v4 chalk, v2 essence and sigil)
