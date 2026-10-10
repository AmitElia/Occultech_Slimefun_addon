# Occultech: comprehensive boss rework plan

**Visual production now starts with Volley; previous Brood Mother model work was discarded.** This is the implementation brief for all 19 bosses in [recipes.yml](recipes.yml). The encounter requirements below remain the baseline. [boss-visual-overhaul.md](boss-visual-overhaul.md) holds the current visual concepts. [bettermodel.md](bettermodel.md) records the installed engine, modeling workflow and resource-pack constraints.

The brief follows the user's corrections: original imaginative silhouettes, Tidebreaker on a nautilus, existing signature mechanics retained, a convincing player-copy Doppelganger, Gallus eggs that drop and hatch, and preservation of held-item models and armor sets. New timing, targeting and geometry below are **proposed combat changes**, not claims about current behavior. Numerical timings explicitly called “current” were checked against the Java implementation; some older design notes and class comments differ.

## 1. Art and gameplay contract

### Original concepts in Minecraft's visual language

“Vanilla-esque” describes construction and rendering: angular geometry, deliberate pixel textures, readable materials, coherent detail and clear gameplay signals. It does not require every boss to retain its carrier mob's anatomy, face or proportions. A silk-cathedral spider, bone arbalest, widow moth or ritual engine can belong visually in Minecraft. Judge the silhouette by the boss's name, character and encounter. Restore the original occult bestiary: imprisoned spirits, ritual architecture, ceremonial mechanisms and bodies that explain their powers.

Specific earlier requests still apply: Tidebreaker rides a nautilus; Choir members resemble highly upgraded blazes; Tempest and Elder are ambitious boss interpretations of Breeze and Elder Guardian; Doppelganger convincingly copies a player; Gallus remains a chicken/rooster and tiny knight. These identity anchors do not impose vanilla anatomy on the rest of the roster. Keep signature mechanics, including guard/remount tethers and hatching eggs, and preserve held-item geometry and armor sets.

### Concept and visualization gate

Discuss the concept before replacing models. Establish silhouette explorations, material hierarchy, front/side design and a polished three-quarter concept before production geometry. Review the model's silhouette, connected joints, negative space and an expressive pose before texture polish. A technically importable blockout is not an accepted design. Label concept images separately from renders of actual model geometry. Preserve defining features through simplification; redistribute or expand measured asset budgets where those features require it.

Every boss gets a characteristic idle, locomotion, attack preparation, release/contact, recovery, phase transition where applicable, and death. Expressiveness comes from stance, head direction, anticipation and follow-through. Large models still leave the floor warnings visible. Accessories must not imply attackable limbs or weak spots that do not exist.

### Preserve the encounter's identity

- Keep the 19 IDs, tier gates, offerings, catalysts, drops, contribution rules and equipment progression. This plan requires no recipe changes.
- Keep each boss's distinguishing interactions listed below. The Hollow Warlord's guard tethers are mandatory; Gallus's remount tether is also retained.
- Preserve solo viability, party scaling, add caps, arena containment, no griefing, no vanilla loot from adds, and crash-safe rewards. Validate against [scope.md](scope.md) and the anti-abuse rules in [boss-ideas.md](boss-ideas.md). Their old visual restrictions predate the explicitly requested optional BetterModel track; their economy and fairness constraints still apply. Current save/resume behavior takes precedence over obsolete crash-refund prose.
- Start with current damage values. A longer opening, removed overlapping hit, added wind-up or changed target lock can change difficulty even if damage is unchanged; those changes need combat-log review and benchmark playtests.
- Use the existing optional-pack path and prove packless presentation. Installing BetterModel did not install custom bosses or deliver its generated pack to clients.

### Held items and armor are protected assets

Preserve existing held-item geometry, first/third-person transforms, UV layouts, use/block variants, item selectors, custom helmets, armor silhouettes and set identities. Boss hands should attach the existing item asset where appropriate instead of generating a lookalike replacement. Boss-only ornament belongs to the boss rig and must not silently replace a player's equipment model.

[build_pack.py](../tools/art/build_pack.py) already distinguishes `_held/model.json`, `_held_using` and `_head/model.json`, item display contexts and equipment assets. Keep Heartwood Aegis's normal/blocking forms. Keep the Frenzied, Abyssal and Hollow armor assets, including existing back pieces. The current equipment textures under `docs/art/session-g/equipment/` use 64×32 humanoid/leggings layouts; custom helmet rendering requires the current opaque-or-transparent alpha treatment.

Retexturing may substantially improve material separation, shading, wear, color relationships and readability **inside those existing UVs**. Before changes, capture a model/selector manifest and screenshots in inventory, first person, third person, held-use, blocking, full worn sets and back view. Review texture changes independently of boss geometry. Preserve model/equipment IDs, Slimefun IDs, stats, durability and abilities. Pack merging must retain these assets and allocated custom-block states. Doppelganger must copy their visual components correctly.

## 2. Shared engineering work before polished models

### Reuse and extension map

| Existing code | Reuse | Required addition or correction |
|---|---|---|
| [BossFight](../src/main/java/io/github/amitelia/occultech/boss/BossFight.java), [BossService](../src/main/java/io/github/amitelia/occultech/boss/BossService.java), [Mechanic](../src/main/java/io/github/amitelia/occultech/boss/Mechanic.java) | Entity ownership, health, contribution, labels, damage, arena, hazards, objects, rewards and cleanup. | Emit visual/action events without creating a second damage authority. New damage still goes through `fight.hit` or existing labelled entities/projectiles. |
| [BossBehavior](../src/main/java/io/github/amitelia/occultech/boss/BossBehavior.java) | `tick()` decisions, per-tick `move()`, damage/add hooks. | Add explicit action ownership, cancellation and lifecycle/restore hooks. A full attack-state framework does **not** already exist. |
| `spawnBoss`, `spawnAdd`, `spawnExtra`, `spawnObject` and destructible fight objects | Main bodies, limited adds, mounts, wards, hearts, eggs and phylacteries. | Attach model trackers to those identities; handle spawn-cap refusal and partial multi-entity spawn cleanup. No untracked cosmetic entities. |
| [FloorDecals](../src/main/java/io/github/amitelia/occultech/boss/FloorDecals.java) | Ground sectors, lanes, rings, patches, warning/impact assets. | Feed rendering and damage from one geometry snapshot. Keep existing indicators when they are already clear. |
| [AirEffects](../src/main/java/io/github/amitelia/occultech/boss/AirEffects.java) | `Streak` links/beams, `Aura`, bursts, bolts and snaps. | Re-anchor existing effects to validated rig attachment points. Preserve Warlord chains, Volley ward links and Colossus pylon links. |
| [Abyss](../src/main/java/io/github/amitelia/occultech/boss/tier2/Abyss.java) | Ground movement and beam geometry reused across several fights. | Explicit tracking/lock/fire/cancel events; snapshot the final ray; test all consumers when it changes. |
| [FightState](../src/main/java/io/github/amitelia/occultech/boss/FightState.java) | Existing boss ID, clock, ordered health and fighter ledger. | Versioned optional behavior state for one-shot phase flags, revival use and detached riders; backward-compatible restore. |

Keep `boss/` dependent only on Bukkit/Occultech. Introduce an engine-facing visual interface there and implement BetterModel integration outside it, for example in `model/`. Optional API dependency and plugin ordering must allow startup without BetterModel. Validate the pinned 3.5.0 API before committing an abstraction around newer wiki examples.

### The server owns attack timing

Use `prepare → lock → execute/contact → recover → idle`, with explicit interruption reasons and a fight-generation token. A server action owns target, geometry, deadline, hit ledger and recovery. Animation consumes those events; a Blockbench keyframe or cosmetic script never decides damage. A late viewer receives the current pose/state without replaying damage or earlier effects.

Behavior decisions currently run every **5 ticks**. Movement runs each tick, but the fight's decision clock advances in steps. Use deadlines with `>=` and one-shot consumption, not fragile equality checks. Quantize decision timings to that cadence, or deliberately introduce a per-tick action clock and test it. A 12-tick warning is not automatically executed at tick 12 by the current loop. Animation sampling may be smoother than damage decisions without becoming authoritative.

Separate locomotion, aim, attack and reaction layers; define priority and interruption for each boss. Only one action may own root movement. Keep in-place animation plus server translation; do not apply a lunge twice. If an authored attack replaces vanilla AI melee/projectiles, disable that native attack path. If native contact remains, react to the actual contact event instead of inventing a second hit at the animation peak.

Audit each warning's origin, direction, radius, height and active interval. Several current behaviors mark one position and strike from a later position. Lock the actor or move a clearly tracking marker before commitment, then use the same final geometry for damage. For physical leaps and charges, show the actual trajectory/landing corridor and use collision/landing events. Decorative expanding ripples must not imply an avoidable traveling wave when the damage is an instant disk.

Shared beams currently whiten 15 ticks before firing but continue tracking until the final **5 ticks**; white is not presently the lock signal. Expose the true lock event, freeze the final ray's origin and direction, and hold the source pose through release. Test whether the existing five-tick commitment gives a practical dodge window at normal latency before tuning it. Changing shared beam timing affects Warden, Elder, Colossus pylons, Dread Riders and relevant Gallus echoes.

### Save, pause and teardown are part of every boss

Current `FightState` v1 cannot fully reconstruct private behavior flags from health alone. Examples include Archevoker's used revival, Gallus's killed rider and a phase entered before later healing. Add typed, versioned behavior data with safe defaults for old saves; preserve entity-health ordering and reward ledgers. Save stable phase/one-shot facts, not BetterModel tracker instances. On restore, rebuild the current neutral phase, fresh allowed objects/adds under a documented policy, and no in-flight damaging attack. Never replay transitions or award loot because a visual was restored.

Pause stops attack deadlines and visuals coherently. Banishment, defeat, unload, shutdown, projectile removal and invalid targets cancel pending actions and free trackers/effects. Decide whether each object persists logically or is regenerated on resume; already-destroyed objects must not accidentally regain one-use benefits. Packet-only displays need their own cleanup even though real auxiliary entities use Occultech PDC/ClearLag protection.

## 3. Per-boss implementation briefs

Effort ratings are relative engineering risk, not calendar estimates. **Moderate** means the encounter largely survives with attack scheduling and visual integration; **High** requires substantial state, movement or multiplayer work. Each brief includes a vertical slice that must work before final art.

### 01. Brood Mother — `BROOD_MOTHER` · tier 0

**Model and personality.** Visual direction is open. Prior silhouette and model studies were discarded; the spider body, sacks and attack tells will be designed anew when this boss returns to production.

**Keep / reuse.** [BroodMother.java](../src/main/java/io/github/amitelia/occultech/boss/tier0/BroodMother.java): breakable sacs, cave-spider hatching, slowing webs and warned pounces. Current sacs hatch after 120 ticks; web preparation is 30 ticks and pounce preparation is 20. Reuse sac object callbacks, add limits, web hazards and labelled bites.

**Rework steps.** Mechanics are restored to the original behavior at the user's request (2026-10-10). Keep the original player-following pounce, native movement, web timing, sac hatching and bites. Restrict integration to presentation: attach web charge/spit to the mouth and the sac creation gesture to the abdomen; drive cosmetic sac growth/cracking from the existing hatch deadline. Animation must follow the encounter without imposing new movement locks, target snapshots, flight bounds or recovery windows.

**Animation and effects.** Idle abdomen pulse, eight-leg walk, `lay_sac`, 30-tick web charge, 20-tick pounce crouch, airborne legs, contact/landing recovery and folding death. Web floor coverage remains the actual slowing region. Sac wriggles accelerate near hatching without shortening the counterplay window.

**Feasibility / proof.** Moderate; existing encounter logic remains authoritative. Verify visual timing matches the original leap and hatch deadlines, sac destruction prevents its hatchlings, add-cap refusal is clean, and long legs do not obscure the clickable body or web boundary. Cosmetic animation must not change combat timing or targeting.

### 02. Volley — `VOLLEY` · tier 0

**Model and personality.** The Hanged Arbalest is a tall, armored skeletal archer with a human posture, carrying a giant bone crossbow. An execution yoke holds two caged wisps that mark the breakable wards. The skull serves as the sight and the jaw counts shots. The earlier four-legged machine designs were rejected as too grotesque; the session 1 [humanoid model](art/bosses/volley/overhaul/s1_silhouettes/README.md) replaces them.

**Keep / reuse.** [Volley.java](../src/main/java/io/github/amitelia/occultech/boss/tier0/Volley.java): two breakable wards and damage reduction, visible ward links, five-arrow bursts, cycling slowness/poison/spectral arrows. Reuse `shoot`, projectile labels/no pickup, ward objects and `AirEffects` links. The current tell is 20 ticks; arrows actually emit one per 5-tick behavior step, and arrow type cycles per shot.

**Rework steps.** (1) Introduce an owned burst action with draw, five release events and recovery. (2) Keep target tracking before each shot visibly expressed through aim; decide and test a brief per-shot commitment instead of showing a stationary aim while projectiles retarget invisibly. (3) Audit native skeleton shooting so it cannot bypass the authored burst. (4) Bind ward shield appearance to actual ward existence and snap the correct links when broken; retain existing respawn rules.

**Animation and effects.** Draw for 20 ticks; five compact recoil beats synchronized to real projectiles; relaxed bow reset. Ward crystals use different notch/symbol cues for the arrow family along with color. Short tracers follow arrows rather than simulate independent hits.

**Feasibility / proof.** Moderate, high reuse. Validate exactly five projectiles at five-tick spacing, no extra AI arrows, cancellation on death/pause, and immediate shield/link updates when wards break during a burst.

### 03. Witch Coven — `WITCH_COVEN` · tier 0

**Model and personality.** Restore three wax-and-rag crones: tall/tapered, rounded/cauldron-bodied and crooked/long-armed, each with a distinct carved mask, rag mantle and candle recess. Witch hats, bottles and ritual habits can anchor recognition without restricting anatomy to vanilla robes. Their stable personal silhouettes contrast with changing role emblems and postures. A living flame passes between recesses when roles rotate. Shared clip structure adapts to each body rather than producing identical synchronized witches.

**Keep / reuse.** [WitchCoven.java](../src/main/java/io/github/amitelia/occultech/boss/tier0/WitchCoven.java): three health pools, 300-tick role rotation, healing the weakest other witch, curses, real thrown harming potions and role reassignment after a death. Keep existing healing/bomb cadence and potion labels as the baseline.

**Rework steps.** (1) Replace the pending curse's bare player reference with caster, role generation, deadline and geometry. It currently warns on the floor but applies effects to the player later regardless of where they moved. Proposed correction: retain the 20-tick warning and curse effects but make the marked ground area genuinely dodgeable. This is a balance change. (2) Cancel unfinished casts when that witch dies or loses the role. (3) Make heal and potion preparation occupy actual scheduled time; start preparation before the existing release deadlines. (4) Audit independent vanilla witch potion behavior and attach splash visuals to real impacts.

**Animation and effects.** Gentle two-handed healing, stiff pointing curse, vigorous bottle shake and throw; hat/sleeve follow-through. A short symbol exchange announces role rotation without creating a fourth body. Potion splash, curse boundary and healing recipient must remain distinct in a crowded fight.

**Feasibility / proof.** Moderate. Prototype a rotation with a curse pending and one witch dying. Check that no orphaned caster applies a delayed curse, two remaining witches get valid roles, a lone witch cannot heal a nonexistent partner, and ground warnings truthfully describe the curse.

### 04. Gelatinous Sovereign — `GELATINOUS_SOVEREIGN` · tier 0 gate

**Model and personality.** Restore an immense royal jelly wearing fragments of a drowned throne, with a heavy crooked crown and painted or selectively modeled treasures suspended inside its mass. Large gel lobes imply deformation; a scepter-like appendage droops while it tries to remain dignified. Chartreuse/apple jelly and tarnished gold provide a focused palette. The throne frame surrounds a visible attackable body and leaves floor warnings readable. The smaller phase becomes an indignant, springy tyrant.

**Keep / reuse.** [GelatinousSovereign.java](../src/main/java/io/github/amitelia/occultech/boss/tier0/GelatinousSovereign.java): leap/slam, the one-time split near 66%, healing shards, shrink/acid phase near 33%, and the grounded-player counter to slam. Current shards arrive from the arena rim and return to heal; retain that actual spatial interaction.

**Rework steps.** (1) Keep the 30-tick launch preparation, but carry the landing warning through the actual flight rather than letting it expire early. (2) Couple slam contact to a valid landing; timeout must resolve safely instead of producing an unexplained impact. (3) Preserve the existing instantaneous grounded damage disk: the expanding aftermath ripple is decorative, not a traveling hit. (4) Send visible gel energy toward the rim before shards emerge, making their existing spawn positions coherent. (5) Apply phase scale from authoritative state and rebuild it on resume without retriggering the split.

**Animation and effects.** Idle wobble, hop compression, flight stretch, landing squash, crown lag, splitting shudder and compact enraged bounce. Acid remains a thin floor film with a clear boundary; crown and splashes must not cover it. Shard arrival/heal uses an actual server arrival event.

**Feasibility / proof.** Moderate. Prototype landing geometry and phase scaling before deformation polish. Test interrupted flights, airborne players at contact, rapid threshold crossings, shard kills versus arrivals, full add caps and restart after the one-time split.

### 05. The Unbound — `THE_UNBOUND` · tier 1

**Model and personality.** Restore an escaped spirit forcing apart a broken reliquary: fragments of illager-like face, axe stance and torn ceremonial containment can connect it to its origin, but the silhouette is an overextended prisoner rupturing its cage. Broken shackles drag and lag behind violent movement. Frenzied-set material echoes connect rewards to the encounter while player models stay intact. Sated posture reveals the exhausted creature inside the frame; avoid permanent decorative effects obscuring that vulnerability.

**Keep / reuse.** [TheUnbound.java](../src/main/java/io/github/amitelia/occultech/boss/tier1/TheUnbound.java): escalating aggression, thralls that can be used against him, cone cleave and the sated vulnerability after the intended thrall-kill interaction. Current cleave warning is 25 ticks, thrall interval 280 ticks and sated duration 60 ticks.

**Rework steps.** (1) Lock the cleave origin and facing and hold the actor through preparation; the current warning and eventual cone can have different origins. (2) Entering sated explicitly cancels an unfinished cleave. The current early return can skip an equality-based strike deadline. (3) Check thrall-kill attribution: a missing player killer must not automatically make every unrelated environmental death count as the intended devour/bait event. (4) Keep native axe contact separate from scripted cleave or deliberately replace it with one authored attack path.

**Animation and effects.** 25-tick axe haul-back, full cone sweep, heavy recovery, thrall-call gesture and 60-tick sated collapse/breathing. Use the existing held weapon shape. The entire sated interval is a useful player opening; a long transition cannot consume it invisibly.

**Feasibility / proof.** Moderate, high reuse. Test thrall death during cleave preparation, non-player/environmental kills, correct incoming-damage multiplier while sated, and exact cone alignment after knockback or target movement.

### 06. Night Matriarch — `NIGHT_MATRIARCH` · tier 1

**Model and personality.** Restore the widow-moth concept with an owl-like porcelain face, veil wings and false-eye markings. Broad angular wing panels fold and bank with a phantom's predatory flight, but the model may substantially diverge from phantom anatomy. The false eyes open during dive preparation and the veil collapses during vulnerable recovery. Needle limbs and exposed abdomen remain readable below the wings. Swarm silhouettes repeat a simplified motif within the existing add budget.

**Keep / reuse.** [NightMatriarch.java](../src/main/java/io/github/amitelia/occultech/boss/tier1/NightMatriarch.java): circling flight, warned dive, exposed grounded recovery, capped swarm and stronger nighttime behavior. Current implementation permits daytime encounters. The dive warning is 30 ticks and the post-impact stun is **30 ticks / 1.5 seconds**.

**Rework steps.** (1) Keep the locked dive target and reuse per-tick dive movement. (2) Replace timeout's forced teleport-to-impact with a collision-aware finish or safe aborted pass; never announce a flight path then hit from an unexplained teleport. (3) Keep the landing mark visible until resolution and align impact radius with the actual contact. (4) Give the close rake a readable preparation if it remains an independent attack, and arbitrate it against diving. (5) Restore free flight only after the full exposed recovery.

**Animation and effects.** Bank left/right, 30-tick wing fold, committed dive, landing skid, 30-tick vulnerable wing-spread, takeoff and swarm call. Wing gusts trail the real path; feather particles stay sparse. False-eye wings open at commitment; veil effects remain clear of the landing mark.

**Feasibility / proof.** High movement risk, otherwise reusable. Test obstructed dives, late/failed landings, recovery damage access, target disconnect, day/night transition and viewers joining during flight. Do not polish wings before safe dive termination works.

### 07. Mirrored Magus — `MIRRORED_MAGUS` · tier 1

**Model and personality.** Restore a masked stage magician built from folding mirror panels, with an articulated ceremonial mantle and deft spell hands. Its bow, spell gestures and subtle spark retain the encounter's identity without requiring a vanilla illager face. A courteous bow hides a second gesture preparing deception. Every decoy receives the same silhouette, mask, equipment and performance; exclusive ornament or animation must not accidentally reveal the real one.

**Keep / reuse.** [MirroredMagus.java](../src/main/java/io/github/amitelia/occultech/boss/tier1/MirroredMagus.java): three decoys, subtle real-body spark, punishment/reposition after a wrong hit, three-arrow fans and the warned prism blast. Current prism warning is 30 ticks; the real spark remains the deliberate observation-based clue.

**Rework steps.** (1) Make clone spawn, pose changes and blink an atomic visual update so model loading or delayed clips do not reveal the real one. (2) Reuse decoy health/removal and wrong-hit logic, but ensure a destroyed decoy cannot leave its rig behind. (3) Add a short scheduled bow preparation, initially prototyped at 10 ticks, ahead of the existing fan release cadence; this timing requires balance validation. (4) Preserve prism target snapshots and give casting priority over cosmetic bow flourishes. Decoys can mimic preparation cosmetically but never emit unlabelled damaging arrows.

**Animation and effects.** Conjure, synchronized draw, prism gesture, blink-in/out and shared idle/walk. Keep the real spark small and intentional; avoid an exclusive crown animation or outline accidentally becoming a stronger giveaway.

**Feasibility / proof.** Moderate. Prototype one real body plus three clones with synchronized state. Test wrong-hit reposition during casting, simultaneous clone hits, blink cleanup and subtle-clue visibility on ordinary graphics settings. This remains an illusioner puzzle; player impersonation belongs to Doppelganger.

### 08. Archevoker — `ARCHEVOKER` · tier 1 gate

**Model and personality.** Restore a many-handed hierophant framed by a floating rib arch. A central caster body remains an accessible target while spectral/ceremonial hands conduct line, ring and spiral fangs with distinct calligraphic strokes. Ivory ribs, dark cloth and small sigil accents connect the phylacteries, fangs and vexes. Extra hands are visual articulation, not new health pools or unannounced attacks. Resurrection assembles the frame around the same authoritative body.

**Keep / reuse.** [Archevoker.java](../src/main/java/io/github/amitelia/occultech/boss/tier1/Archevoker.java): line/ring/spiral fangs, vex pressure, three breakable phylacteries, close-range fang burst and one survival/revival while a phylactery remains. Reuse pattern point generation, arena clipping, native labelled EvokerFangs and revival damage interception.

**Rework steps.** (1) Give pattern and proximity casts explicit priority so competing arm poses do not hide an attack. (2) Keep the 20-tick main warning; normalize the proximity warning's current 12-tick deadline to an explicit 15-tick behavior-grid duration, matching its effective stepped execution, then test it. (3) Account for native fang emergence/contact timing; an animated jaw overlay must not add another damage source. (4) Audit native evoker casts and vex limits. (5) Save the one-use revival flag independently of HP, and make the visual resurrection consume that exact event once.

**Animation and effects.** Distinct line thrust, circular sweep and spiral wrist motion, close defensive gesture, phylactery call, resurrection and final collapse. Vex spawning and phylactery cracks follow the existing server objects. Revival does not add an unplanned invulnerable cinematic.

**Feasibility / proof.** Moderate to high, chiefly cast arbitration and persistence. Validate lethal hits with zero/one surviving phylactery, simultaneous damage, restart after revival, fang hit timing and the absence of extra vanilla summons outside caps.

### 09. Abyssal Warden — `ABYSSAL_WARDEN` · tier 2

**Model and personality.** Restore the bathysphere jailer: a pressurized prismarine/metal shell with a shuttered iris lens, steering fins and an articulated tail or supporting limbs suited to land gliding. Its recognizable guardian eye/beam vocabulary is useful, but its body need not remain a vanilla box. Lens shutters tighten like a held breath; shell panels flare for spikes and relax during rest. Keep one broad reachable target and low floor clearance for attack warnings.

**Keep / reuse.** [AbyssalWarden.java](../src/main/java/io/github/amitelia/occultech/boss/tier2/AbyssalWarden.java): ground gliding, dodgeable magic beams, close lash, spike eruption, recovery and increased beam pressure below half health. Keep current solo/party beam-target limits. Reuse `Abyss.Beam`, movement and `Mechanic` labels.

**Rework steps.** (1) Add eye attachment and beam-stage events using the shared final-ray snapshot. (2) Keep the current 40-tick beam preparation while making its tracking and final commitment legible. (3) Hold position for the 20-tick spike preparation or fix the footprint to the warned position; choose the former so the physical body and eruption stay together. Current movement can displace the damage origin. (4) Give the radial lash a short owned preparation and animate a full surrounding sweep, not a rear-only tail strike. Prevent lash/spike full-body actions from obscuring the beam tell. (5) Keep the existing recovery window visible through relaxed spines and a dim eye.

**Animation and effects.** Hover/glide, tail steering, eye track/lock/fire, spine flare, radial lash, rest and death. The beam originates at the same validated eye point used by the server ray. Decorative eye rotation cannot bend damage away from the shown line.

**Feasibility / proof.** Moderate. Prototype one moving eye beam and the stationary spike tell. Test a solo player's dodge window, multi-target enrage, no damage outside the spike marker, obstruction policy, and clean cancellation when a target leaves the arena or disconnects.

### 10. Tidebreaker — `TIDEBREAKER` · tier 2

**Model and personality.** A drowned harpooner riding an elaborate armored nautilus ram. The coiled shell is the central silhouette, wrapped in ceremonial braces and angular spiral bands, with a thick tentacle fringe beneath. A crest and harpooner's mantle provide rank; rider and mount lean into the charge together. Preserve the explicitly requested nautilus rather than restoring the earlier cuttlefish. Keep the rider exposed as the real damage target and preserve existing held trident geometry.

**Keep / reuse.** [Tidebreaker.java](../src/main/java/io/github/amitelia/occultech/boss/tier2/Tidebreaker.java) already uses a Zombie Nautilus. Preserve land gliding, the invulnerable mount/damageable rider relationship, warned ram, winded opening, close trident combat and three-trident volley. Reuse mount steering/remount, real projectiles, hit-once tracking and damage labels. Current ram preparation is 20 ticks, travel lasts up to 25 ticks and winded recovery is 40 ticks.

**Rework steps.** (1) Keep separate authoritative rider and mount entities; map the rig seat and rider target to the real passenger. (2) Replace the approximate charge lane with a shared swept corridor whose length, width and endpoint match actual travel and collision. (3) Stop at solid obstacles/arena limits, preserving a visible recovery rather than sliding through geometry. (4) Add scheduled trident thrust/throw preparations and arbitrate them against charging; the current fan release has no separate authored wind-up. (5) Keep the exposed rider hittable during all intended windows; shell ornament must not visually cover the only valid target.

**Animation and effects.** Tentacle propulsion idle, shell pitch on steering, 20-tick compression/brace, ram, 40-tick exhausted tentacle droop, rider thrust and fan throw. A narrow wake follows the mount. Shell sparks on collision never imply terrain damage. Preserve existing held-item geometry when assigning equipment.

**Feasibility / proof.** High for coupled movement, moderate art complexity. First prove a blockout mounted charge on flat and uneven terrain. Test rider hit access, failed passenger remount, walls, edge-of-lane dodges, target movement after lock and the full winded opening. No water requirement is introduced.

### 11. Blaze Choir — `BLAZE_CHOIR` · tier 2

**Model and personality.** Restore the furnace-cantor ambition while keeping all three unmistakably upgraded Blazes. Square blazing heads sit within elaborate orbiting rod cages that suggest organ pipes, chimneys and ceremonial crowns. Soprano, Alto and Bass have distinct pipe lengths, contraction rhythms and head postures. Their cages inhale and open on actual beats; furnace apertures and restrained ember glow support their musical roles. The Blaze core stays visible, and smoke cannot blanket ground warnings.

**Keep / reuse.** [BlazeChoir.java](../src/main/java/io/github/amitelia/occultech/boss/tier2/BlazeChoir.java): three independent bodies, orbiting formation, rotating shield, labelled non-incendiary fireballs, group chorus and acceleration as singers die. Current shield rotation is 120 ticks. Fire cadence changes from 60 to 45 to 30 ticks as the group shrinks; the last singer loses the rotating shield.

**Rework steps.** (1) Give each singer a stable identity and beat schedule so list reindexing after death cannot cause skipped/doubled release events. (2) Prepare rod contraction and head aim before each real fireball release. (3) Bind shield visuals to the exact protected member and remove protection immediately under the existing survivor rule. (4) Retain the 30-tick chorus ground warning. Proposed fairness correction: overlapping chorus circles deal at most one chorus hit per player per synchronized release; balance that deliberate reduction in stacking. (5) Keep orbit movement under the existing puppet controller and prevent cosmetic rod motion from becoming extra collision geometry.

**Animation and effects.** Rod orbit idle, inhaling contraction, upward/downward head accents per voice, fireball release, shared chorus pose, shield handoff and loss-of-singer reaction. Fire density rises modestly with tempo, but the face and floor warnings remain visible. Use recognizably Blaze sounds as the base for a musical rhythm.

**Feasibility / proof.** Moderate; no new encounter required. Prototype all three together, including a death during shield handoff and chorus preparation. Check actual 60/45/30 cadence, one shield owner, overlapping circle damage, no fires and readable surviving targets under smoke.

### 12. Tempest — `TEMPEST` · tier 2

**Model and personality.** Restore the storm-bird/torn-sail/pressure-vane motifs as an ambitious interpretation around a recognizable Breeze face and wind core. Swept sail-like cloud panels form an expressive mantle; vane-like rods orbit around a still eye before the body uncoils and collapses into force. This keeps the user's Breeze-boss requirement while recovering the original striking motion and silhouette language. Avoid an opaque vortex: wind structure opens to expose the face during the spent window.

**Keep / reuse.** [Tempest.java](../src/main/java/io/github/amitelia/occultech/boss/tier2/Tempest.java): hopping mobility, three wind-charge fan, knockback burst, spent opening, shrinking pressure ring and the pair of low-health Breeze adds. Reuse labelled BreezeWindCharge projectiles, ring radius/damage calculations, capped knockback and add spawn logic.

**Rework steps.** (1) Establish one controller for native Breeze attacks and authored volleys; audit autonomous projectiles before layering clips onto AI. Keep the hop character while controlling attack ownership. (2) Freeze the burst origin during its 20-tick preparation, aligning the 4.5-block warning and damage. (3) Preserve the 30-tick spent state and visibly drop the wind cage to expose the face. (4) Keep the ring's eight-second contraction and final hold as explicit states; it may continue during spent recovery, so avoid presenting that opening as globally safe. (5) Use the actual pressure boundary for floor effects; decorative cloud rings are thinner and less saturated.

**Animation and effects.** Hop coil/release, midair spin, aimed volley, 20-tick inward compression, burst, 30-tick exhausted droop, ring channel and add call. Wind trails show direction; ground indicators show damage. Keep the Breeze core visible within the swept sail/bird-like composition; avoid an opaque tornado.

**Feasibility / proof.** High around native-AI coordination; the ring and projectile systems are reusable. Prototype one hop-to-volley transition and one burst first. Test hidden AI shots, ring radius/hold agreement, ring-plus-recovery overlap, low-health adds and safe knockback near uneven ground.

### 13. Drowned Elder — `DROWNED_ELDER` · tier 2 gate

**Model and personality.** Restore the benthic-oracle mood, bell-shaped shell mantle and deliberate unfurling motion around a clearly identifiable Elder Guardian core. Layer ancient prismarine arches, dangling fin/veil forms and a three-part ceremonial crown around its pale body and central eye. Preserve guardian ancestry without limiting the whole model to an enlarged vanilla cuboid. Multiple beams emerge coherently from the eye; architectural crown elements are decorative rather than additional faces or health pools.

**Keep / reuse.** [DrownedElder.java](../src/main/java/io/github/amitelia/occultech/boss/tier2/DrownedElder.java): Mining Fatigue pressure, up to three aimed beams, guardian adds with their own beams, and the one-time low-health sequence of three expanding jumpable waves. Reuse shared beam logic, add limits, the fixed surge center and per-wave hit tracking. Main beam preparation is currently 40 ticks.

**Rework steps.** (1) Drive eye tracking and beam release from shared server events, exposing separate ray locks where targets differ. (2) Make surge a clear owned phase action: complete or explicitly cancel already-active beams before starting its wave pattern; suppress incompatible new casts during it. (3) Preserve actual moving wave damage rather than replacing it with an instantaneous slam. Check the swept radial interval between behavior updates so a fast boundary does not miss or unfairly double-hit players. (4) Keep the existing grounded/height test that allows jumping, and expose the exact crest with low floor geometry. (5) Persist the used-surge fact if phase state is added; do not turn a one-time event into a repeated ability unintentionally.

**Animation and effects.** Heavy tail strokes, single-eye focus, three-ray release, fatigue pulse, guardian call, rising surge posture and one body contraction per wave. Cracked prismarine fragments dissolve cosmetically; no blocks change. Waves stay thin enough to see feet and the next crest.

**Feasibility / proof.** Moderate to high. Prototype the three waves with placeholder art before the full eye rig. Test jumping at different distances, beam cancellation versus surge, add-beam overlap, solo targeting, one hit per wave and restart after the one-time phase.

### 14. Hollow Warlord — `HOLLOW_WARLORD` · tier 3

**Model and personality.** Restore the hollow armored monarch carrying funeral standards: ceremonial armor contains a visible void, with a dark skull/mask and long disciplined weapon arms. The frame can depart substantially from a wither skeleton while maintaining the martial identity. A composed salute gives way to forceful rotations as support fails. Soul-chain tethers to guards and the supported halo remain defining visual/gameplay features. Player Hollow armor and held weapon geometry remain protected.

**Keep / reuse — tethers are mandatory.** [HollowWarlord.java](../src/main/java/io/github/amitelia/occultech/boss/tier3/HollowWarlord.java) is the roster's counterpart to the user's “hollow knight.” Keep its soul-chain tethers to guards, guard-supported protection, warband replenishment, full circular sweep and low-health aggression. Existing `air_chain` streaks link Warlord and guards; `aura_soul_halo` shows support while at least two guards live. Current guard protection multiplies incoming damage by 0.6 on top of base armor. Reuse those systems rather than substituting a new shield puzzle.

**Rework steps.** (1) Re-anchor the existing chains to chest/guard attachment points; match the actual two-guard threshold. When support falls below two, the whole supported-chain/halo state ends; show the snap immediately. (2) Retain the three-guard replenishment cap and existing cadence. (3) Hold position during the 20-tick sweep tell so the warning and strike share an origin. (4) Animate the existing **360-degree** damage area as a complete rotation; a forward sword slash would misrepresent it. (5) Preserve enrage below roughly 35% and route pose/speed changes through stable phase state.

**Animation and effects.** Commanding idle, measured march, guard rally, chain-supported posture, 20-tick sword draw-back, full sweep, recovery, support-break stagger and faster enrage variants. Tethers communicate support; they do not become damaging tripwires or distance-break mechanics without a separate design change.

**Feasibility / proof.** Moderate, very high reuse. Prototype three guards and the existing effects first. Test guard counts 3→2→1→0, replenishment, simultaneous guard death, restored fights and whether every chain/halo matches the actual damage multiplier. Gallus's separate knight remount tether is preserved too.

### 15. Heartwood Horror — `HEARTWOOD_HORROR` · tier 3

**Model and personality.** Restore an uprooted orchard shrine with an inverted branch crown, resin hearts and several interlocking tree masses. Creaking eyes and bark vocabulary may survive within a much more ambitious body. Its limbs move as though several trees disagree over one creature; roots open into readable lanes and chambers hold its protected hearts. Use pale bark, dead moss and amber resin. Keep the active boss behavior rather than adding an observation-freeze mechanic.

**Keep / reuse.** [HeartwoodHorror.java](../src/main/java/io/github/amitelia/occultech/boss/tier3/HeartwoodHorror.java): four linked hearts, invulnerability while hearts remain, the 400-tick vulnerable interval, regrowth, root lanes, sap zones, slam, heart thorns and the unsettling behind-player ambush. Current hearts take 12 hits each. Reuse destructible objects, `Pending` warning/geometry structures and existing damage labels.

**Rework steps.** (1) Retain the heart objective and clearly change bark/eye state when protection drops. (2) Preserve lane, sap and slam patterns but give them action priority and a bounded overlap policy; simultaneous body clips cannot hide separate damage tells. (3) **Rebuild the ambush's hit logic.** It currently teleports behind the player's later position and directly hits them. Keep the audio cue and behind-player threat, but choose a safe arena-valid destination, visibly reappear, then commit to a dodgeable local sweep or root lunge. Use a ground/clearance check and fizzle if no valid destination exists. Never move the player. (4) Associate pending heart-thorn attacks with their heart; destroying it before commitment cancels that attack. (5) Regrowth resets only the intended object cycle, not already-consumed phase facts.

**Animation and effects.** Uneven walk, root-arm lane sweep, sap spit, raised-root slam, listening ambush pose, reappearance unfold, brief attack preparation, vulnerable sag and regrowth. Hearts pulse and crack according to actual hit count. Floor roots remain visual entities, not placed blocks.

**Feasibility / proof.** High; this is a real combat rewrite around an intact signature objective. Build the dodgeable ambush and heart ownership first. Validate multiplayer target changes, moving/airborne targets, blocked destinations, destroyed-heart cancellation, protection transitions and fair root/sap/ambush combinations.

### 16. Dread Riders — `DREAD_RIDERS` · tier 3

**Model and personality.** Restore the imposing antlered war-mount and lean spectral courier contrast while retaining the pair's existing mounted identities and independent pools. The Vanguard's undead horse can carry antler-like ritual armor and heavier barding; the Outrider's skeletal mount gets a stretched, airy courier silhouette. Rider motion, horse articulation and existing held weapons must remain coherent. Each survivor changes its rhythm and posture, not merely its color.

**Keep / reuse.** [DreadRiders.java](../src/main/java/io/github/amitelia/occultech/boss/tier3/DreadRiders.java): two independent health pools, invulnerable mounts, orbiting pressure, Vanguard interception/charge, Outrider ranged attacks, survivor-specific enrage and the periodic 60-tick halt that creates an aiming window. Reuse `checkDeaths`, horse dismissal/remount, charge hit tracking, ranged labels and `Abyss.Beam` attacks.

**Rework steps.** (1) Treat each rider/mount as a coupled visual pair while retaining separate combat identities. (2) Share the tested swept-charge geometry with Tidebreaker: actual speed/travel must match the warning lane and stop at obstacles. Current charge preparation is 20 ticks and travel up to 25. (3) Preserve the distinction between ordinary charge completion and the 40-tick stun caused by an obstructed/failed charge. (4) Schedule spear/bow preparation around orbit and halt states, auditing native contact attacks during commitment. (5) On one rider's death, remove the right horse/rig and switch the survivor's existing attack pattern exactly once; do not replace it with a generic damage buff.

**Animation and effects.** Walk/trot/gallop matched to actual speed, halt/brace, lance couch, impact/recovery, bow draw and bereavement/enrage. Use low hoof dust and narrow charge trails; mounts must not blanket the floor with smoke. The stationary aiming opportunity should be obvious in posture.

**Feasibility / proof.** High coordination cost, strong reuse of combat logic. Prototype both mounted blockouts together. Test simultaneous deaths, target chasing, blocked charges, 60-tick halt accessibility, saddle alignment while turning, and each survivor's distinct enrage.

### 17. Corrupted Colossus — `CORRUPTED_COLOSSUS` · tier 3

**Model and personality.** Restore a walking ritual engine with an imprisoned heart: massive iron-golem-derived arms, an industrial chest chamber, piston-like joints and corruption pulling the body off its measured rhythm. Broader machinery and ceremonial frames can substantially reshape the vanilla body. Pylons visibly feed the heart through existing links. Preserve a broad target, clear raised-arm preparation and floor visibility; layered mechanism motion should explain weight rather than add surface noise.

**Keep / reuse.** [CorruptedColossus.java](../src/main/java/io/github/amitelia/occultech/boss/tier3/CorruptedColossus.java): three breakable pylons, their healing/beam pressure, visible chest links, ground slam and low-health overload. Reuse pylon objects/callbacks, beam-origin suppliers, `air_beam` links and the existing 25-tick slam preparation. Pylons currently replenish on the 400-tick check when none remain.

**Rework steps.** (1) Lock the body to the slam's already-snapshotted center during preparation; current damage uses that center even if the golem walks elsewhere. (2) Keep slam as an instantaneous grounded disk with a cosmetic trailing ripple, unless a later deliberate balance change makes it a moving wave. (3) Map pylon-to-chest link endpoints to the model while preserving actual healing count. (4) Breaking a pylon cancels its pending beam, link and visual charge together. (5) Overload below roughly 30% changes tempo and exposed seams through one phase event. Mirror native melee contact or replace it explicitly; do not add a second fist hit from the clip.

**Animation and effects.** Heavy gait, chest pulse on actual healing, 25-tick raised-arm slam, impact/recovery, pylon call, overload and collapse. Preserve a broad attackable torso and readable arm/contact geometry within the ritual-engine silhouette. Dust falls after contact and does not obscure the next warning.

**Feasibility / proof.** Moderate and the recommended first complete prototype: readable anatomy, existing geometry and clear supporting objects. Verify marker/contact alignment, jump counterplay, pylon destruction during beam lock, healing count, overload timing and no duplicate melee/slam damage.

### 18. Doppelganger — `DOPPELGANGER` · tier 3

**Model and personality.** Keep the required convincing player copy as the primary body: skin, supported proportions/layers, armor appearance, both hands, stance and visible name. The original porcelain-understudy concept may appear only as a brief transition or defeat reveal outside the baseline disguise. It must not create permanent seams, alien gait, a boss-only silhouette or a lasting outline that makes identification trivial. Native Mannequin fidelity takes priority over a custom rig; preserve the appearance-copy engineering and multiplayer confusion tests below.

**Keep / reuse.** [Doppelganger.java](../src/main/java/io/github/amitelia/occultech/boss/tier3/Doppelganger.java): real player profile copying, selection of a player to imitate, melee/bow/held-flame stance selection, recorded-path dark echo, temporary damage reflection and the owner-specific shatter reflections. Preserve fight health, contribution and protections. Existing profile application, target logic, trail recording and reflection ownership are useful foundations.

**Required appearance rework.** Current `dress()` recreates equipment from its **material only**, copying neither custom item models nor full armor appearance, and omits the off hand. Build a safe cosmetic appearance snapshot: copy the necessary item-model/equipment asset data, visible trim/dye, cosmetic glint, hand choice and use state onto temporary display equipment. Do not copy functional Slimefun PDC, inventories, stats or usable item behavior. The copied gear is never dropped or collectible. Keep snapshots synchronized when the player changes equipment; prototype a modest bounded update cadence before adding event-specific optimization. Apply profile, gear and pose atomically to avoid a conspicuous partial transformation.

**Combat and deception rework.** (1) Match visible name formatting and practical skin/pose options supported by Mannequin; investigate team/prefix behavior on this server. No “reflection” suffix or permanent special outline on a clone intended to deceive. (2) Add player-like draw/use/thrust preparations to actual server attacks, including off-hand posture. Do not require copying live client input, which the server cannot reproduce perfectly. (3) Retain short, action-specific tells for reflection and dark echo so their counters remain learnable; the baseline body returns to a clean player appearance afterward. (4) Make shatter copies use the intended disguise, while keeping owner restrictions clear through a brief phase cue. Handle an owner's death/disconnect so an untouchable leftover copy cannot leave the boss permanently protected. (5) Preserve PvP/protection rules: confusion must not require forcing teammates to damage real players.

**Animation and effects.** Native-like walk, sprint, head aim, sneak/use poses where supported, real bow draw and attack recovery. Copy player equipment shapes exactly. Dark echo remains an intentionally dark hazard tracing the recorded route; it is distinct from the convincing primary impersonator. Transformation may use one brief shimmer, never a lingering boss-only aura.

**Feasibility / proof.** High, with client-visible fidelity as a go/no-go prototype. First test two similarly positioned bodies with custom armor, custom held item, off hand, skin layers and slim/wide profiles before producing any new rig. Run blind two- and four-player identification tests: participants should sometimes need behavior or a transient ability tell to distinguish the copy. Also test pack refusal, gear changes, reconnect and ownership loss. Native entity type, debug tools, tab entries and unsupported player animations can reveal it; ordinary combat-view confusion is the goal, not a claim of perfect protocol-level impersonation.

### 19. Gallus, the Hollow Jockey — `GALLUS` · tier 3 final gate

**Model and personality.** Restore the cathedral rooster and tiny funeral knight: proud chicken/rooster proportions become monumental through layered feather buttresses, wing architecture and a ceremonial saddle canopy. Keep beak, comb, wattle and bird identity clearly legible. Pompous joust becomes panic and then uncanny weightlessness in Hollowing; hanging ornament and feathers follow those transitions. Egg drops/hatches and independent rider behavior remain essential.

**Keep / reuse.** [Gallus.java](../src/main/java/io/github/amitelia/occultech/boss/tier3/Gallus.java): mounted joust, leap impacts, ordinary egg barrage, dismounted knight, remount chase/tether and heal on successful remount, flying Hollowing, breakable Hollow Eggs, lesser boss echoes, rider dive and the small fleeing Last Cluck. The code has three main phases plus a below-10% ending state. Reuse labelled egg projectiles, egg hazards, chick-jockey spawning, Hollow Egg objects, echo variants and existing per-tick movement. Preserve the knight's yellow remount tether as well as Warlord's separate guard tethers.

**Both egg systems remain.** Ordinary thrown eggs currently splat into short-lived hazards and have a 25% chance to hatch a chick jockey. Hollow Eggs currently appear directly on the ground, take four hits to break and hatch after 200 ticks into lesser slime/evoker/guardian echoes. The new presentation adds a genuine visible drop to Hollow Eggs while preserving their destroy-before-hatch interaction. These are two distinct readable threats, not interchangeable decorative projectiles.

| Stage | Retained gameplay | Rework and required animations |
|---|---|---|
| Joust, above about 66% | Mounted knight jab, warned chicken leap, ordinary egg salvos. | Rider brace/jab, chicken 20-tick leap crouch, flight and actual landing response, wing-assisted egg release. Keep floor warning through landing; resolve obstructed/timeout leaps safely. Egg trails track real projectiles. |
| Unhorsed, about 66–33% | Knight separates; Gallus continues leaps/eggs; remount attempts and successful-remount heal remain. | Separate knight locomotion and chicken action ownership. Show the existing tether/chase, a clear boarding attempt and a seated recovery. Rider death permanently prevents further remounts in this fight, including after restart. |
| Hollowing, about 33–10% | Flight, ordinary eggs, three Hollow Eggs per wave, lesser boss echoes and rider dives if alive. | Chicken lay/drop pose, visible falling eggs, landing/cracking/incubation, exactly-once hatch; independent rider launch/return. Keep flight readable without hiding floor eggs beneath wings. |
| Last Cluck, below about 10% | Small grounded fleeing chicken, final pursuit. | Collapse flight into grounded scramble; stop new Hollow Egg waves. Existing landed eggs continue their owned incubation/hatch or destruction lifecycle instead of becoming frozen leftovers. Test this overlap so the ending remains fair. |

**Egg implementation steps.** (1) Introduce an egg lifecycle with stable identity: `dropping → landed/incubating → hatched` or `broken/cancelled`. Allocate a valid, warned landing point and a short cosmetic descent; start the full 200-tick incubation on landing, preserving ten seconds of break counterplay. (2) Animate four-hit damage states and increasing hatch movement from actual state; a break callback and hatch deadline cannot both win. (3) Separate egg ticking from the current phase-specific method. Today, switching to Last Cluck stops the Hollowing update and can leave unprocessed eggs. (4) Enforce pending-egg/add budgets; if the add cap refuses a hatch, resolve the egg cleanly rather than retrying forever. (5) Use real projectile collision events for ordinary egg splats/hatches, distinguishing impact from cleanup/removal. If a chick mount spawns but its rider cannot, remove the orphan immediately. (6) Define resume policy for eggs explicitly: safely recreate allowed incubation objects with saved remaining time, or cancel them on restore; never reroll an already-resolved hatch for extra adds.

**Other engineering work.** Add explicit phase and rider-life save data before detailed animation. Health alone cannot reliably reconstruct all one-time transitions after remount healing. Give chicken and knight separate action layers and a shared seat contract; egg release, leap and rider dive cannot all seize root movement. Reuse the shared beam fixes for guardian echoes. Keep weaker echoes recognizable as the earlier boss families with reduced visual complexity and their existing limited abilities.

**Feasibility / proof.** Highest combined scope. Prototype egg drop/landing/destruction/hatch and detached rider persistence with simple models before the full Gallus rig. Then test every threshold crossed during leap, drop, remount and incubation; rider death; phase healing; simultaneous break/hatch; full add caps; Last Cluck with live eggs; pause/banish/restart; cleanup and reward delivery exactly once. A finished chicken model alone is not completion of this rework.

## 4. Production order and concrete deliverables

1. **Baseline and protected assets.** Capture current fight footage/combat logs and the held-item/armor manifest. Record signature mechanics and packless behavior. Resolve model/equipment rendering in a small test scene before touching player textures.
2. **Shared action and visual bridge.** Implement optional integration, attack/lifecycle events, geometry snapshots, cancellation, current-state synchronization and versioned behavior saves. Verify the pinned API and merged resource-pack delivery on a real client. A successfully loaded plugin is not enough.
3. **Early risk probes, with placeholder art.** Prove Doppelganger appearance fidelity, Gallus egg lifecycle, Heartwood's dodgeable ambush and one rider/mount charge. These high-risk features run early so expensive art is not built around unsupported behavior.
4. **First finished encounter: Colossus.** Deliver one rig, texture, complete animation set, pylon effects and aligned slam. This establishes the production standard and measurable render budget.
5. **Different animation problems.** Sovereign tests deformation/scale; Matriarch tests flight/contact; Coven or Choir tests multiple bodies and simultaneous warnings. Correct their engine issues before expanding the art pipeline.
6. **Roster production.** Complete Volley first, then return to Brood Mother after a new visual concept review; continue with Unbound, Magus and Archevoker, then Warden, Tidebreaker, Choir, Tempest and Elder, then Warlord, Heartwood and Riders. Reuse proven controllers and effects, not copied timing bugs. Complete Doppelganger's multiplayer polish and Gallus's full staging after their early probes pass.
7. **Textures and final integration.** Retexture protected equipment in separate reviewable batches. Capture the same baseline views, verify all original geometry/selectors remain, merge packs deterministically and run the full regression/performance pass.

Each boss delivers: editable `.bbmodel` and texture sources; a rig/attachment map; named clips with server event timings; body/add/object/effect assets; an explicit reuse/change checklist; model and pack registration; behavior integration; packless fallback; restore/cleanup policy; and test evidence. Keep notes on practical export limitations discovered with BetterModel 3.5.0. Do not purchase/import reference packs or assume their ModelEngine/MythicMobs configurations can run unchanged.

## 5. Acceptance gates

### Combat and lifecycle

Run unit tests for any extracted action timeline, geometry, phase serialization and egg lifecycle logic. Test state behavior rather than clip filenames. Run Maven with the project JDK, then the existing in-game self-test for all 19 bosses and the new targeted cases. Preserve registration, summoning, refunds, contributions and rewards.

Validate every proposed timing/geometry change with `/occultech balance`, benchmark kits and combat logs: solo first, then parties. The scope's fight-length and hit-severity targets remain the baseline. Capture warning → commitment → contact → recovery, checking the damage ledger against the visible event. Include targets moving out of range, dead/disconnected casters, latency, low TPS, multi-target overlap, walls and uneven terrain. Invulnerability, hidden AI attacks and model hitboxes must never add duplicate damage or make a required target inaccessible.

For each boss: pause/resume, chunk unload, shutdown/restore, late join, reconnect, pack refusal, model reload, banishment, defeat during preparation, and maximum adds. Old saves must still load. Destroyed/consumed one-shot objects and phase flags follow the documented policy, and no delayed event survives into a later fight.

### Visual and resource budget

Use the provisional budgets in [bettermodel.md](bettermodel.md) as starting targets, not guarantees. Measure total simultaneously rendered bodies, bones, effects and adds. Record MSPT, client frame time, network traffic, pack size and first-visible delay with 1/4/8 players and multiple arenas. Reduce decorative bone/effect complexity before sacrificing warning clarity. Inspect on an ordinary unshaded client; selective glow is not dynamic lighting.

Require the approved original silhouettes, the explicit identity anchors, clear floor geometry, consistent face/weapon aiming, correct seat alignment, no feet sliding at normal speed, no lingering effects and no invisible damage. Review each protected held item and armor set after pack changes. For Doppelganger, require observed multiplayer confusion without a permanent visual defect giving the copy away; for Gallus, require filmed drop → landing → incubation → hatch and a separate destroy-before-hatch example.

**Completion means the visual, mechanic and lifecycle tests pass together.** The current deliverable is this plan; BetterModel's earlier installation and sample-load verification do not establish any of these future acceptance results.
