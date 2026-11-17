Subawu mount (MythicMobs 5.13 + BetterModel 3.5, no other plugins)

Install: there is no plugin jar; copy these files into the MythicMobs and BetterModel folders already on the server:
  plugins/MythicMobs/Packs/Subawu/packinfo.yml
  plugins/MythicMobs/Packs/Subawu/Mobs/Subawu.yml
  plugins/MythicMobs/Packs/Subawu/Skills/Subawu.yml
  plugins/BetterModel/models/subawu_mount.bbmodel   (the truck: texture, click box and both seats inside)
then run /bm reload (rebuilds the resource pack with the model) and /mm reload, and spawn one.

Spawn:  /mm mobs spawn SUBAWU_MOUNT
Remove: /mm mobs kill SUBAWU_MOUNT          (/kill doesn't work: it is invincible)

What it is: one mob, a pig wearing the truck model, made the same way as the Volcano Toad. The pig's AI is cleared:
a parked truck stays where it was left. Its skills play the animations: parked (the engine idling, a light shiver)
and driving (the wheels rolling, the chassis rumbling).
Driving: right-click anywhere on the truck. You sit in the driver's seat (right-hand drive, as in the real truck);
W/S/A/D to drive, space toots the horn, sneak to get out. You steer by looking: once it moves, the truck turns to
face where you look, so the driver always faces forward. While parked you can look around freely. No jumping (space
is the horn); it drives up full blocks. Riding is BetterModel's (mountmodel on the model's seat bones): no saddle, no
sprint.
Six seats: while someone drives, the next players to right-click sit beside them in the cab (the passenger's seat, on
the left), then on the floor of the bed (two rows of two, upper bodies above the bed walls); nobody more once all six
are taken. Only the driver's keys drive, honk and drift. When the driver gets out the passengers get out too (with only
passengers aboard, BetterModel would keep the truck rolling on its own); anyone can then click to take the wheel.
Sounds, only while someone is in the driver's seat: a starter and the engine catching when you get in, the engine humming
(lower when parked), a rolling rumble while driving, exhaust smoke, and on a hard turn (more than about 140 degrees a
second while driving) tyre squeal and smoke from the rear wheels. Space toots the horn (toot toot, again every 0.8 s
while held). They are all vanilla sounds, so no extra resource pack is needed; change them in Skills/Subawu.yml (the
sound{...} lines).
Players need BetterModel's resource pack with this model in it (rebuilt by /bm reload, then sent to players again):
without it every part shows as a purple-black cube; with an older copy the parts are drawn wrong.
A pig struck by lightning turns into a zombified piglin and the truck is lost; respawn it.
Entity clearers: the truck's click box and seat are BetterModel hitbox entities (armour stands and interactions). The
truck tags them and itself CLE_PROTECTED (ClearLaggEnhanced spares that tag) on spawn, on load and every minute; with a
different clearing plugin, exclude that tag or those entity types near the truck, or it can't be driven after a clear.
It runs no console commands (they print a line each time): everything is done with MythicMobs' own mechanics, so it adds nothing to the console.
Tuning (Mobs/Subawu.yml): Options.MovementSpeed (driving speed, now 0.75: about 9 blocks a second), StepHeight
(drives up full blocks), the attributeModifier line (jump strength times 0: no jumping). The wheels' roll is made for
MovementSpeed 0.75: at another speed they slide or spin. The drift threshold is in Skills/Subawu.yml (the 14 in the
SUBAWU_TURN_ ranges: degrees per 2 ticks).
Ownership, despawning and how players get one are up to you.
