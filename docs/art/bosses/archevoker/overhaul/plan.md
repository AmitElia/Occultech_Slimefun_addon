# The Archevoker redesign: the plan (the dark priest and his hands)

Agreed direction (2026-10-15): mostly **the Conductor**, enthroned. An illager dark priest floats on a decorated
woodland-mansion throne, his arms crossed, and casts through two large gilded hands held up palm-out like a stop
sign. A ring of smaller gilded hands turns behind the throne. It replaces the "Hierophant of Ribs" draft in
[boss-visual-overhaul.md](../../../../boss-visual-overhaul.md). Not taken: the cathedral-arch collar, the Undying
(totem regalia) and the Enthroned's fang-jaw armrests.

## Identity

The user's brief (2026-10-15):
- **An illager dark priest:** vanilla's illager head kept exactly at a whole scale (the long face, the hanging nose,
  the black unibrow), grey skin; the evoker's black robe and gold trim made into a priest's vestments.
- **A decorated woodland-mansion throne, magically floating**: carved dark oak, no legs, held up by magic. Its
  **armrests end in gilded hands**.
- **His arms stay crossed** (vanilla's illager idle). **His legs** move between crossed at the knee and spread apart
  in his animations.
- **Two large casting hands**, gilded, held up **palm out like a stop sign**: one with a **spirit cyan** glow round
  it, one with a **purple** glow.
- **A ring of smaller gilded hands turns behind the throne.**
- **The glow is tier 1's spirit cyan** (the ring, the sigils), with the purple hand as its counterpart.
- **No vexes.**

**Vanilla ties:** the evoker's head, robe and trim; the crossed arms; the woodland mansion's dark oak; the evoker
fangs; the totem of undying's role (the hands are his totems).

## The hands are his totems (built in session 8)

The two casting hands replace the three phylacteries and the vexes. They are killable, hard to kill and evasive.

- **While at least one hand lives, he cheats death once:** at 0 health the hands catch him and he returns at 40%.
- **Each hand killed makes him stronger;** with both dead he can't come back, but he is far more dangerous.

The hands are the fight's choice: leave them, and the fight is longer (the revival); kill them, and it is shorter
but much harder.

Built as described in [s8_ship](s8_ship/README.md); numbers are tuned with the combat logs.

## Materials (not repeated from other bosses)

Taken: wax and candles (Brood Mother), amethyst and bone (Volley), iron vessels and brew (the Coven), leather,
chains and fire (the Unbound), sculk (the Matriarch), cards and the clown (the Masquerade), lava and basalt (the
Elder of Ash). The Archevoker's: **gold** (the hands), **dark oak** (the throne), the black vestments and gold trim,
and **emerald** as a small accent (the Evoker's Sigil he drops).

## Process

Session 1 in gated steps: silhouettes (the throne, the ring and the casting hands against him, side and front) ->
a face, vestment and hand study -> the blockout. Sessions 2-8 as in
[boss-art-sessions.md](../../../../boss-art-sessions.md). For the Archevoker specifically:
- the ring is **one bone** that spins (one display, cheap however many hands it holds);
- the casting hands are their own models on their own carriers (they fly and have their own health);
- the floating throne keeps the fang burst's floor ring visible round him.

## Fight fixes (boss-rework-plan.md, done in session 8 with the code)

1. Pattern casts and the close-range burst get an explicit priority, so two gestures never fight over a hand.
2. The burst's warning becomes an explicit 15 ticks (it acts on the 5-tick behaviour grid).
3. The animation never adds a damage source: the fangs stay vanilla, labelled.
4. The carrier's vanilla spells (its own fangs and vexes) are removed; the hands cast everything.
5. Which hands live and whether he has revived are saved apart from health, and the revival plays exactly once.
