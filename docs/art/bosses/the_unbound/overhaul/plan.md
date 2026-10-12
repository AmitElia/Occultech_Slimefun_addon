# The Unbound redesign: the plan (the Horned Frenzy)

Agreed direction (2026-10-12): the **Horned Frenzy**, without a mask. It replaces the Reliquary Breaker draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md). Rejected pitches: the Reliquary Breaker (a spirit in a
box that hides the torso) and the Muzzled Berserker. The Unbound is where the Frenzied armour set and the Frenzy
Cleaver come from, so the rewards echo the fight.

## Identity

A berserk vindicator who broke out of a ritual binding, half beast. The user's brief:
- **Clearly a vindicator:** the illager head (the long face, the big nose, the heavy brow), grey skin; trousers only. Larger than a player, with a **buff upper body**.
- **Bull horns** grow from the sides of the head.
- **A red cloth wrapped around his eyes**, its ends trailing. **One eye burns through the cloth.**
- **Chains dangle from his limbs**: broken shackles on the wrists and ankles.
- **He burns from the inside** (user, after the face study: no chest piece, no furnace look): the fire shows
  through splits in the skin of his chest.
- **Silver-studded leather straps** across his body.
- **A giant bloody meat cleaver** in his right hand: the Frenzy Cleaver's design (a broad butcher's blade, a thick
  spine, the haft up through it, blood along the edge), at his size. Blood stays dark, dried stains along the edge,
  not gore.
- **Embers and fire grow as he speeds up.** The chest piece burns brighter at each health threshold and embers
  stream off him. No fire on the horns.

**User's changes after the first silhouettes (2026-10-12):** no burning horn tips; clear shackles with chains
hanging; only trousers (bare, buff upper body); C's hunched posture at B's height and width, a little bigger
(about 3.25 blocks to the top of the head); he **drags the cleaver behind him when he walks and lifts it round his
shoulder to attack**; the burning eye is **tier 1's spirit cyan** through the red cloth.

**Vanilla ties:**
- the vindicator's head, nose, brow and grey skin, and his dark trousers;
- the axe swing he's built on (now the cleaver);
- the husks he calls up stay vanilla husks.

## The fight, and the pose for each moment (the code stays; see the fixes below)

| Moment | Server | Pose |
|---|---|---|
| idle | - | breathing heavy, shoulders rolling, the cleaver low; the chains sway |
| walk / chase | speeds up as he loses health | a forward, heavy stride; at low health a charging run, head down, horns first |
| axe swing | melee, at most every 1.2 s | a short chop |
| cleave | a red wedge for 1.25 s, then a sweep | the cleaver hauled back over his shoulder, held, then a full sweep and a heavy recovery |
| thrall call | every 14 s two husks rise | he roars and slams his fist (or the cleaver) into the ground; chains rattle |
| devour | he kills a thrall | he grabs and gorges; the fire flares |
| sated | 3 s stunned, +50% damage taken | he sinks to one knee, panting, the cleaver dropped; the fire dims to coals. Open to hits from the first tick |
| enraged stages | health thresholds | more fire and embers (eye, chest, horn tips) |
| death | - | he falls to his knees, then forward; the fire goes out, embers drift away |

## Materials (not repeated from other bosses)

- **Taken:** Brood Mother's wax and candles; Volley's amethyst and bone; the Coven's iron vessels and coloured brew;
  the Monarch's toxic slime.
- **The Unbound:** grey illager skin (bare above the waist) and dark trousers; dark leather and **silver studs** (tier 1's silver);
  **blackened iron** (chest piece, shackles, chains); **bone horns**; **red cloth**; the steel cleaver with dried
  blood; **fire and embers** as the one living light (the Frenzied set's ember).

## Process

**Session 1, in three gated steps:**
1. **Silhouettes:** three postures of this design, side and front, silhouette and value, next to a player. Pick one.
2. **Face study:** the head with the horns, the red cloth and the burning eye, three takes. Pick or mix.
3. **Blockout:** the full figure from cuboids, clay renders from several angles.

Sessions 2-8 as for the Coven (boss-art-sessions.md). For The Unbound specifically:
- the chains, the cloth's trailing ends and the straps' loose ends get their own bones (they swing);
- the fire stages are shown by glow parts appearing or tinting, never by scaling a bone that holds other parts;
- the death clip can be long: the dying model now hands over to a stand-in that plays it in full.

## Fight fixes (boss-rework-plan.md, done in session 8 with the code)

1. Lock the cleave's origin and facing when its warning appears, and hold him through the wind-up.
2. Being sated cancels an unfinished cleave.
3. Only a thrall The Unbound kills himself makes him sated.
4. The plain axe swing and the cleave stay two separate attacks.

## Open

- **The head (face study, 2026-10-12):** F3's horns (a horn boss and buffalo horns), F3's iron nose ring and eye
  (a cyan slit with a soft halo), F2's scowling brow and slipping ragged band, without F2's jaw and tusks.
- **The chest:** which way he burns (s1_face2: the fissure, ember veins, the burning heart).
