Volcano Toad mount (MythicMobs 5.13 + BetterModel 3.5, no other plugins)

Install: there is no plugin jar; copy these files into the MythicMobs and BetterModel folders already on the server:
  plugins/MythicMobs/Packs/VolcanoToadMount/packinfo.yml
  plugins/MythicMobs/Packs/VolcanoToadMount/Mobs/VolcanoToadMount.yml
  plugins/MythicMobs/Packs/VolcanoToadMount/Skills/VolcanoToadMount.yml
  plugins/BetterModel/models/volcano_toad_mount.bbmodel   (the toad: texture, click box and seat inside)
(earlier versions also had volcano_toad_mount_hitbox.bbmodel: delete it)
then run /bm reload (rebuilds the resource pack with the model) and /mm reload. Kill any old toads and spawn new ones.

Spawn:  /mm mobs spawn VOLCANO_TOAD_MOUNT
Remove: /mm mobs kill VOLCANO_TOAD_MOUNT          (/kill doesn't work: it is invincible)

What it is: one mob, a pig wearing the toad model. BetterModel hides the pig and the toad does everything the pig
does: it wanders and looks around on the pig's AI and turns with its body. Its skills play every animation: the
idle (the Elder of Ash boss's), the waddle (a frog's walk, palms and feet planted on the ground) whenever it moves,
ridden or not, and the leap and landing. (Not a camel: on a camel BetterModel draws this model collapsed and never
animates it; tested side by side with a pig.)
Riding: right-click anywhere on the toad. You sit on the saddle; WASD to move, space to jump (a frog's leap,
about 4.5 blocks up; no fall damage), sneak to get off. Riding is BetterModel's (mountmodel on the model's seat bone), not the pig's: no saddle
item, no carrot on a stick, no jump-charge bar and no sprint. Right-clicks never feed or saddle the pig.
Players need BetterModel's resource pack with this model in it (rebuilt by /bm reload, then sent to players again):
without it every part shows as a purple-black cube; with an older copy the parts are drawn wrong.
A pig struck by lightning turns into a zombified piglin and the toad is lost; respawn it.
The volcano and the pipe smoke and steam.
Entity clearers: the toad's click box and seat are BetterModel hitbox entities (armour stands and interactions). The
toad tags them and itself CLE_PROTECTED (ClearLaggEnhanced spares that tag) on spawn, on load and every minute; with a
different clearing plugin, exclude that tag or those entity types near the toad, or it can't be mounted after a clear.
It runs no console commands (they print a line each time): everything is done with MythicMobs' own mechanics, so it adds nothing to the console.
Tuning (Mobs/VolcanoToadMount.yml): Options.MovementSpeed (walk speed, ridden and wandering), StepHeight (climbs full
blocks), the attributeModifier line (jump strength: the pig's 0.42 plus 0.43, now 0.85). The waddle's stride is made for MovementSpeed 0.30 (3.6 blocks a second ridden): at another speed the planted feet slide.
Ownership, despawning and how players get one are up to you.
