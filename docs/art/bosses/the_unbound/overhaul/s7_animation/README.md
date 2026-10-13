# The Unbound redesign, session 7: animation

Twelve clips on the session 6 rig. Each clip is a few whole poses at key times, built with session 2's pose code, so at
every key the cleaver's edge faces where the swing carries it and the chains hang straight. The keyframes are each
bone's turn away from the rest pose. Kneeling sinks the hips with a position key; a dropped cleaver is set on the
floor with another.

| Clip | Length | Plays | What happens |
|---|---|---|---|
| idle | 3.0 s | loop | heavy breathing: the chest rises and falls, the shoulders roll, the chains and the band's tails sway |
| walk | 1.6 s | loop | a heavy stride, the hips bobbing, the free arm swinging, the cleaver dragging behind |
| run | 1.0 s | loop | enraged (below 1/3 health): head down, horns first, a long stride, arms back |
| spawn | 2.0 s | once | rising from a kneel to a roar (the ritual arrival) |
| swing | 0.8 s | once | the axe swing (melee): the same overhead arc as the cleave, quicker and shallower, **contact at 0.35 s** |
| cleave | 2.2 s | once | an anticipation crouch; the cleaver raised **above his shoulder**, the blade hanging behind his back, through the 1.25 s warning (breathing, trembling); then up over the top and down in a lunge with a twist, the free arm swinging back, **contact at 1.3 s**; an overshoot and a heavy settle |
| call | 1.8 s | once | calling the thralls: he crouches, then roars, arms spread |
| devour | 1.6 s | once | seizing a thrall and gorging, fist to his mouth (**the bite at 0.8 s**) |
| sated | 3.0 s | once | the 3 s opening: down on one knee by 0.4 s, panting, back up at the end |
| enrage | 1.2 s | once | a stage change: a short roar as the fire flares |
| flinch | 0.4 s | once | hit: a jolt, layered over whatever he's doing |
| death | 2.6 s | hold | to his knees, then folding forward, the cleaver dropped |

The action clips (swing, cleave, call, devour, enrage, flinch) override only the bones they move, so the breathing
goes on underneath.

![Key frames of every clip](keyframes.png)

**Take 2 of the attacks** (after the user's review in game: the arm went under the shoulder, and the motion was stiff):
- **Above the shoulder:** the wind-up now raises his arm above his shoulder with the blade hanging behind his back.
- **Over the top:** a key at the very top of the swing makes the chop come over his head and down in front.
- **A bug fixed:** a rotation passing 180 degrees wrapped to -180, so the arm spun the long way round, under and
  backwards. Every track is now kept continuous from key to key.
- **Less stiff:** anticipation, a crouch into the strike, a torso twist, the free arm counterbalancing, an overshoot
  and a heavy settle, with the chains and the band's tails lagging behind.

**The cleave, from the side** (0.18 to 2.0 s): the crouch, the wind-up above the shoulder, over the top, the strike, the
overshoot, the settle.

![The cleave from the side](cleave_side.png)

**The swing, from the side** (0.06 to 0.62 s): the same arc, quicker.

![The swing from the side](swing_side.png)

The GIFs in `gifs/` show each clip moving (flat zone colours, the fire at its burning stage).

## For the fight code (session 8)

- **Lead times:** start each clip early enough that its contact lands on the server's moment:
  - **cleave** with the warning, about 1 tick early (contact at 1.3 s, the warning is 1.25 s);
  - **swing** 7 ticks before the hit;
  - **devour** 16 ticks before the thrall dies.
- **Sated** plays for the whole 60-tick opening. Nothing blocks the player's hits during it.
- **Walk** for normal movement and **run** once he's enraged (below 1/3 health). **Enrage** plays at each stage
  change, with the stage tint (session 6).

**Load test:** the animated rig loaded on the second test server with the shipped models and no warnings, and is on
your server:

```
/bm reload
/bm test occultech_unbound_rig cleave
/bm test occultech_unbound_rig walk
/bm test occultech_unbound_rig sated
```

Regenerate with `python tools/art/bosses/unbound_s7.py` (after `unbound_s5.py`).
