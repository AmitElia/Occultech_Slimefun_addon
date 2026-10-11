# Boss visual overhaul: scarier, bigger, more magical

Status: **CONCEPT PLAN for review.** Drafted 2026-10-10. Names, ids, tiers, themes and the mechanics in
[boss-rework-plan.md](boss-rework-plan.md) stay. Everything about how the bosses *look, move, enter, transform and die*
is open. Built with BetterModel models driven by MythicMobs skills ([mythic-integration-plan.md](mythic-integration-plan.md)).
The user's identity anchors still hold: Tidebreaker rides a nautilus, the Choir are upgraded Blazes, Tempest is a Breeze,
the Elder is an Elder Guardian, the Doppelganger is a convincing player copy, Gallus is a rooster with a tiny knight.

## Shared horror language

The addon's story is that every boss is **something pulled through a ritual circle that did not want to come.** That
gives the whole roster one visual grammar:

- **The arrival.** No boss just appears. The circle's glyphs ignite one by one, the offerings in the bowls rot, burn or
  float, and the boss is *dragged* up through the altar: a hand grips the rim, a crown rises first, a shadow pours out.
  Mythic's cinematic camera mechanics give a short (2-3 s, skippable by moving) intro. Nobody can be hit during it.
- **The binding.** Each boss wears visible evidence of the ritual holding it: sigil brands, chains of light, wax seals,
  nails, halo-rings. When a phase changes, a binding **breaks** on the model. Players read progress from the body, not
  only from the bar.
- **Eyes.** Every boss has one unmistakable light source on its face (glow group). It is the first thing players see
  in the dark and it tracks the current target before every attack. Being looked at is the warning.
- **Scale and stillness.** Scary comes from size, silence and sudden motion, not gore. Idles are slow and too calm;
  attacks snap. Long held breaths before big moves.
- **Sound motif per tier.** T0 whispers and wet sounds, T1 choir and bells, T2 deep-water pressure and furnace roar,
  T3 silence broken by single huge impacts.
- **Death is a banishing.** The circle drags the boss back down; the binding marks on the body flare and it is pulled
  apart into the glyphs. The loot rises from the altar, not from the corpse.

**Readability contract** (unchanged): floor telegraphs stay brighter than any decoration, models never cover their own
warnings, decorative parts are not hitboxes, no flashing faster than 3 Hz, darkness effects are short and never during a
dodge window.

---

## Tier 0 — the things in the cellar

### 01. Brood Mother
Visual direction is open for a future restart. Earlier model studies and their dedicated files were discarded. No
silhouette is selected.

### 02. Volley
**Concept: "The Hanged Arbalest."** A tall, armored skeletal archer, held upright by a small execution yoke. It has
two arms, two legs and a recognizable human posture. It carries a giant bone-and-iron crossbow strung with tendon; its
skull is the sight and its jaw counts shots by clacking. Two ward lanterns hang from the yoke. The earlier walking
siege-engine shape was rejected as too grotesque; the [humanoid revision](art/bosses/volley/overhaul/s1_silhouettes/README.md)
replaces it. Its crossbow belongs in the right hand at the side, angled slightly outward, so the chest and waist stay
visible from the front. Apply the broader [boss art lessons](art/BOSS_STYLE.md) to future designs.
**Moments.** Burst: Volley plants both feet, draws the tendon and fires five bolts while its jaw snaps on each;
tracers are faint soul-fire. Wards: each lantern holds a trapped wisp; breaking one makes Volley turn its head toward
the attacker. Low health: a wrist binding snaps and one arm starts aiming more freely. Death: the bowstring snaps and
the archer folds beneath the yoke.

### 03. Witch Coven
**Concept: "The Three Who Hum."** Three wax crones that never touch the ground, hovering a block up with their feet melted
into long drips. Each wears a different mask: *The Maiden* (cracked smile), *The Mother* (sewn eyes), *The Crone* (no
face, just a candle in the hole). A single shared flame passes between their candle-hearts to show who holds which role.
**Moments.** Role rotation: all three freeze, their heads turn 180°, the flame jumps between them. Curse: the cursing
witch's shadow detaches and slides across the floor to the marked area. Healing: wax flows from healer to the weakest
witch along the ground. Deaths: a dead witch melts into a puddle with her mask lying face-up; the survivors stop and
look at it before continuing (brief, never during an attack).

### 04. Mire Monarch (was the Gelatinous Sovereign)
**Concept: a giant crowned cellar toad.** Chosen 2026-10-11 after two slime takes were rejected (the drowned king in
jelly; the radioactive slime). Vanilla's frog, mutated huge and warty, squatting low and wide on folded back legs; a
crown sunk into the fat of its head, a bulging throat sac, a back crusted with warts and toadstools.
**Moments (the fight is unchanged).** Leap: the back legs coil (the telegraph), the belly-flop sends the shockwave
players jump. Split at 66%: it retches up three spawn (tadpoles or egg clumps) that wriggle back to the altar to feed
it. 33%: its skin dries and splits; leaner and faster, it sweats acid puddles. The id is `MIRE_MONARCH`; the old
`GELATINOUS_SOVEREIGN` still resolves in saved data (`core/BossIds`). Its items (Sovereign Gel, Sovereign's Catalyst)
are to be redesigned later.

---

## Tier 1 — the church gone wrong

### 05. The Unbound
**Concept: "The Reliquary Breaker."** A giant illager-shaped spirit, too tall and too thin, bursting out of an iron
reliquary that is still nailed around its torso. Its head is wrapped in prayer cloth with one eye burning through. Chains
from the broken reliquary drag and spark.
**Moments.** Cleave: it raises a door from the reliquary as an axe-blade. Thralls: it pulls them out of the ground
by chains. **Sated:** after the thrall interaction its chains go slack and it kneels, the reliquary doors swing open and
you can see a tiny trapped figure inside: the original prisoner. Enrage: the cloth burns away revealing a face of
nothing but teeth.

### 06. Night Matriarch
**Concept: "Our Lady of Moths."** A huge moth with a veil of tattered black lace for wings, the underside painted with
dozens of **false eyes** that open during the dive. Her body is a pale, elongated porcelain woman's face with an owl's
mouth, held in place by needle-thin legs. Dust falls from her constantly.
**Moments.** Circling: her shadow passes over the arena before she does. Dive tell: the wings spread and every false eye
opens and looks at the target at once. Recovery: the lace collapses over her like a shroud; she is helpless and shaking.
Night: her eyes glow brighter and the swarm leaves luminous trails. Death: she folds her wings around herself and
crumbles into a pile of moth dust that flies away.

### 07. Mirrored Magus
**Concept: "The Stage of Shards."** A tall magician whose entire body is cut from mirror panels on hinges; under the
mirrors is darkness with stars in it. His face is a theatre mask on a stick he holds in front of himself. Decoys are
identical, but **only the real one has a reflection** (a faint ghost-copy on the floor). That replaces nothing in the
mechanic, it just reinforces the existing spark tell for observant players.
**Moments.** Bow: he lowers the mask; there's nothing behind it. Wrong hit: the decoy shatters into a spray of glass,
and every remaining copy turns its head to you and laughs. Prism blast: the panels unfold into a huge fan and focus light.
Death: he holds the mask up one last time, then it drops and the body falls apart into a heap of mirrors that show
the players' reflections.

### 08. Archevoker
**Concept: "The Hierophant of Ribs."** A towering high priest whose robes open on a giant ribcage that is also a
cathedral door. Six skeletal hands float around him like an orchestra conductor's, each holding a sigil. Phylacteries are
three stained-glass lanterns, each with a tiny copy of his heart beating inside.
**Moments.** Fang patterns: the floating hands draw the pattern in the air in glowing ink a beat before the fangs.
Vexes: they climb out of the ribcage. Revival: he dies, falls, and one phylactery bursts; the ribcage closes over his
body like doors and he stands back up taller, now with a crown of fangs. Final death: the ribcage door slams shut and
cracks, the hands drop one by one.

---

## Tier 2 — the deep and the furnace

### 09. Abyssal Warden
**Concept: "The Pressure Jailer."** A bathysphere the size of a house, gliding on a cushion of black water. Its single
porthole is the eye; inside you can see something pressed against the glass, looking out. Rusted chains and keys hang
from its hull; barnacles grow in sigil patterns.
**Moments.** Beam: the porthole's shutters iris down and the thing inside pushes its face into the glass. Spikes: hull
plates burst outward on pistons. Below half: the porthole cracks, water sprays, the creature inside has its hand through
the crack. Death: the hull implodes inward with a deep groan.

### 10. Tidebreaker
**Concept: "The Last Harpooner."** A drowned whaler in a rotting oilskin coat, faceless under a diving helmet full of
water, riding a **colossal armored nautilus** whose shell is wrapped in harpoon lines and old ship figureheads nailed on
as trophies. The nautilus' tentacles drag a trail of kelp and wet sand.
**Moments.** Ram: the nautilus pulls its tentacles into its shell, the rider lowers a harpoon like a lance. Winded:
the nautilus' eye (huge, goat-pupilled) opens and rolls; the rider looks down at it. Trident volley: the rider stands up
in the saddle. Death: the helmet floods and he slumps; the nautilus slowly retreats into its shell.

### 11. Blaze Choir
**Concept: "The Furnace Cantors."** Three Blazes upgraded into a cathedral organ: each is a molten blaze head inside a
cage of brass organ pipes that orbit instead of rods. *Soprano*: thin, tall pipes, a white-hot head. *Alto*: a ring of
mid pipes, orange. *Bass*: a heavy double ring, deep red, slow. Their singing is **visible**: sound rings pulse from the
pipes on each beat.
**Moments.** Shield rotation: the shielded singer's pipes close into a cage. Chorus: all three align and their pipes
point at one spot like a choir looking at the conductor. When one dies, the others' pipes play a single falling note and
glow hotter. Last singer: its cage breaks open, the head is exposed and screams.

### 12. Tempest
**Concept: "The Storm Vane."** A Breeze grown to monstrous size whose wind body is now a **torn ship's sail wrapped
around a pressure gauge** core with the Breeze face. Weathervane rods orbit it like a crown and point toward the next
target. Lightning lives in the sail's tears.
**Moments.** Wind fan: the sail tightens and the vanes snap into line before the shots. Knockback burst: the whole body
unravels into a whirlwind for half a second. Spent: the sail hangs limp and the gauge needle drops to zero. Low health:
it tears itself in two and the two Breeze adds are its torn halves.

### 13. Drowned Elder
**Concept: "The Benthic Oracle."** An ancient Elder Guardian grown into a floating temple: its body carries a
crown of three broken prismarine arches, long translucent veils hang from its fins like jellyfish, and its single eye is
ringed with smaller closed eyes that open one per beam. Old offerings (pots, bones, drowned pilgrims) hang tangled in the
veils.
**Moments.** Beams: one small eye opens per aimed beam. Mining Fatigue pulse: its ghost image appears in front of each
player's screen (the vanilla Elder curse, made deliberate). **Surge:** it rises, the veils lift like a dress in water, and
the three waves roll out from beneath it. Death: the arches fall, the eye clouds over, and it sinks through the floor
glyphs.

---

## Tier 3 — the kings of the end

### 14. Hollow Warlord
**Concept: "The Empty Throne."** A colossal suit of black funeral armor with no one inside: through the gaps you
see a starless void. It carries a banner pole hung with the shields of the guards it commands. The helmet's visor is a
crown of spikes; the eyes are two cold soul flames. The soul-chain tethers run from its chest to each guard.
**Moments.** Tethers glow and pulse when a guard protects it. Circular sweep: it plants the banner and spins the pole
around itself. A guard dies: its shield falls off the banner. Low health: the breastplate falls open; the void inside
pulls particles in like a black hole. Death: the armor collapses into a pile with the helm landing last, on top.

### 15. Heartwood Horror
**Concept: "The Orchard of the Hanged."** A walking forest shrine made of three dead trees grown together and fighting
over the same body, an inverted crown of roots on top. Its four hearts are amber resin lanterns with a pulsing thing
inside, hanging from branches around the arena. Its face is a creaking heart's eye in a split trunk.
**Moments.** Invulnerable: amber light runs from the hearts to the trunk along the roots. Vulnerable (heart phase down):
the trunk splits open and the core is exposed. **Behind-player ambush:** the lights go out for a heartbeat and it is
standing behind you, branches lowered over your head. Regrowth: new hearts bud like fruit and ripen.
Death: it pulls its own roots out and topples.

### 16. Dread Riders
**Concept: "The Ninth Hour."** Two headless funeral heralds. *The Vanguard*: a giant in rusted plate on an antlered
undead warhorse wearing a shroud, carrying a bell instead of a head that tolls on every charge. *The Outrider*: a lean
figure in a ragged cloak on a skeletal horse made of wind, whose head is a lantern that swings and aims.
**Moments.** Charge: the bell tolls three times. Halt (the aiming window): both horses rear and freeze mid-air with
their hooves dripping shadow. One dies: the survivor's horse screams and its eyes ignite (enrage). Death: the
riders fall but the horses keep galloping in a circle until they fade.

### 17. Corrupted Colossus
**Concept: "The Engine of the Last Rite."** A walking ritual machine: an iron golem frame grown into a cathedral organ
and a furnace, with a **caged heart** in its chest that's visibly being pumped by pistons. The corruption is purple
crystal growing through the joints, making it limp. The pylons are three tall ritual obelisks feeding the heart with
beams.
**Moments.** Slam: it pulls both fists into the air, pistons hiss, then a heavy drop. Pylon down: one beam goes out and
the heart stutters. **Overload:** the cage opens, the heart floats out on chains and the whole body glows from inside,
crystal cracking off. Death: the heart stops; the body freezes mid-step and slowly tips forward.

### 18. Doppelganger
**Concept: "The Understudy."** Stays a perfect copy of a player, but the horror is in **small wrongness**: it blinks a
beat too late, its shadow faces the wrong way, it mirrors your emotes and gestures. When it chooses a target it turns
only its head first. The dark echo trailing it is a faceless black silhouette in the copy's pose.
**Moments.** Reflection: its skin glints like glass for the duration. Damage hits flash a crack line across the face
that heals. **Defeat reveal:** the skin peels off like paper and underneath is a smooth porcelain mannequin with no face,
which bows to the player it copied and shatters.
(The disguise stays convincing the whole fight; wrongness lives in timing and shadows, not the model.)

### 19. Gallus, the Hollow Jockey
**Concept: "Cock-crow at the End of the World."** A monstrous cathedral rooster: feathers like layered black-and-gold
roof tiles, a comb of iron spikes, and a gaze that is just a little too human. The tiny knight riding it is a dead knight
in an over-sized helmet with a banner. Absurd and terrifying at once.
- **Phase 1, the Joust:** proud. Crows before each charge, the knight lowers a lance, eggs rain gold.
- **Phase 2, the Fall:** the knight is thrown; Gallus panics, feathers shed; the knight crawls back while a soul tether
  pulls them together.
- **Phase 3, the Hollowing:** the rooster's body becomes hollow like the Warlord, feathers floating around a void
  skeleton, it flies without wings. Hollow Eggs pulse with the faces of earlier bosses (their echoes hatch out).
- **Last Cluck:** shrinks to a tiny, ordinary-looking chicken that runs away. When killed, the camera lingers on a
  single feather falling.

---

## Production order

The visual overhaul comes before the MythicMobs integration. Each boss goes through the eight sessions in
[boss-art-sessions.md](boss-art-sessions.md), Volley first. Every concept above is a starting point for review,
not an approved design.
