"""The Hollow Warlord (the Headsman), session 8: ship the model, write its Mythic mob and cosmetic skills, and the rig
table the fight reads.

- src/main/models/occultech_hollow_warlord.bbmodel: the final rig (session 7: the painted model with its hitbox, glow
  bones and the eleven clips), carrying the **neutral** glows (session 6): the fight tints them per state. The skulls'
  glow bones are renamed glow_soul_c / _l / _r here, so a tint on a skull's fire can never match the skull itself
  (BetterModel drops the glow_ tag from a bone's name).
- src/main/mythic/Mobs/HollowWarlord.yml and Skills/HollowWarlord.yml: look and sound only. HollowWarlord.java decides
  when each runs and deals every hit.
- src/main/java/.../boss/tier3/HollowWarlordRig.java (generated): where the model's parts are, in blocks from the
  carrier's feet (ahead, up, right), at the moments the fight needs: the blade's end at the chop, the call's plant and
  the enrage's slam; each taken skull in the idle (the soul chains leave them).
- Refuses to ship with faces that would flicker, or with half-clear texels.

Run from the repository root after headsman_s7.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/headsman_ship.py <folder>
"""
import base64
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import headsman_s3 as s3, headsman_s4 as s4, headsman_s7 as s7, headsman_study as st  # noqa: E402

S7 = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s7_animation"
MODELS = ROOT / "src/main/models"
SKILLS = ROOT / "src/main/mythic/Skills/HollowWarlord.yml"
MOBS = ROOT / "src/main/mythic/Mobs/HollowWarlord.yml"
RIG_JAVA = ROOT / "src/main/java/io/github/amitelia/occultech/boss/tier3/HollowWarlordRig.java"
NAME = "occultech_hollow_warlord"
P = "HOLLOW_WARLORD"
RENAME = {f"glow_skull_{k}": f"glow_soul_{k}" for k in "clr"}
HIS = {"CALM": "5CE8F0", "TELL": "D6FFFC", "ENRAGED": "C8FFFF"}            # session 6
SOUL, DARK = "5CE8F0", "282C2C"


def check():
    model = s3.rest_model()
    clash = flicker_pairs([c for c in model.cubes if c.mat != "hitbox"])
    if clash:
        raise SystemExit(f"faces that would flicker in game: {clash[:5]}")


def ship():
    rig = json.loads((S7 / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    for tex in rig["textures"]:
        a = np.array(Image.open(io.BytesIO(base64.b64decode(tex["source"].split(",", 1)[1]))).convert("RGBA"))[..., 3]
        if ((a > 0) & (a < 255)).any():
            raise SystemExit("half-clear texels")
        tex["name"] = f"{NAME}.png"
    rig["name"] = NAME

    def rename(nodes):
        for n in nodes:
            if isinstance(n, dict):
                n["name"] = RENAME.get(n["name"], n["name"])
                rename(n.get("children", []))
    rename(rig["outliner"])
    for g in rig.get("groups", []):
        g["name"] = RENAME.get(g["name"], g["name"])
    for anim in rig["animations"]:
        for animator in anim["animators"].values():
            animator["name"] = RENAME.get(animator["name"], animator["name"])
    (MODELS / f"{NAME}.bbmodel").write_text(json.dumps(rig, separators=(",", ":")) + "\n", encoding="utf-8")
    names = []

    def walk(nodes):
        for n in nodes:
            if isinstance(n, dict):
                names.append(n["name"])
                walk(n.get("children", []))
    walk(rig["outliner"])
    return {"animations": sorted(a["name"] for a in rig["animations"]), "elements": len(rig["elements"]),
            "bones": names}


# ---- where the parts are --------------------------------------------------------------------------------------------------

def blocks(p):
    """Model units -> (ahead, up, right) in blocks from the carrier's feet: the model faces -z, its right is +x."""
    return (round(-float(p[2]) / 16, 3), round(float(p[1]) / 16, 3), round(float(p[0]) / 16, 3))


def posed(clip, t):
    s7.PREV.clear()
    s7.STEP[0] = 0.025
    fn = s7.CLIPS[clip][2]
    m = None
    for ti in [*np.arange(0, t - 1e-6, 0.025), t]:     # solved up to t, so the limbs carry their continuity
        m = s7.apply(fn(float(ti)), float(ti))
    return m


def centre(m, name):
    return next(c for c in m.cubes if c.name == name).corners().mean(0)


def table():
    idle = posed("idle", 0.0)
    return {
        "chop": blocks(centre(posed("attack", s7.CONTACT["attack"]), "blade_end")),
        "plant": blocks(centre(posed("call", 0.5), "blade_end")),
        "slam": blocks(centre(posed("enrage", s7.CONTACT["enrage"]), "blade_end")),
        "skulls": [blocks(centre(idle, f"skull_{k}_cube")) for k in "clr"],
    }


def java(t):
    def vec(v):
        return "{" + ", ".join(f"{x}" for x in v) + "}"

    return f"""package io.github.amitelia.occultech.boss.tier3;

/**
 * Where the Hollow Warlord model's parts are, in blocks from the carrier's feet, as {{ahead, up, right}} for the carrier
 * facing its body yaw. Generated by tools/art/bosses/headsman_ship.py from the session 7 clips; do not edit by hand.
 */
final class HollowWarlordRig {{
    private HollowWarlordRig() {{}}

    /** The blade's end as the chop bites the floor (attack clip, {s7.CONTACT["attack"]} s). */
    static final double[] CHOP = {vec(t["chop"])};
    /** The blade's end driven into the floor as the warband is called (call clip, 0.5 s). */
    static final double[] PLANT = {vec(t["plant"])};
    /** The blade's end driven into the floor at the enrage's slam ({s7.CONTACT["enrage"]} s). */
    static final double[] SLAM = {vec(t["slam"])};
    /** The taken skulls over his head in the idle: centre, left, right (the soul chains leave them). */
    static final double[][] SKULLS = {{{", ".join(vec(v) for v in t["skulls"])}}};
}}
"""


# ---- Mythic -----------------------------------------------------------------------------------------------------------------

def tint(bone, colour):
    return f"  - tint{{m={NAME};p={bone};c={colour}}} @self"


def his(colour):
    return [tint("glow_eyes", colour), tint("glow_brand", colour)]


def twice(lines):
    """Applied, then again after BetterModel's hit flash would have restored the old tint."""
    return lines + ["  - delay 12"] + lines


def skill(name, lines):
    return [f"{P}_{name}:", "  Skills:"] + lines + [""]


def skills():
    out = ["# Look and sound only. HollowWarlord.java decides when each of these runs and deals every hit.",
           "# Generated by tools/art/bosses/headsman_ship.py. His eyes and the sword's brand are painted neutral and",
           f"# tinted: calm {HIS['CALM']} (soul cyan), the sweep's tell {HIS['TELL']}, enraged {HIS['ENRAGED']} (white-hot);",
           f"# each taken skull's fire is lit ({SOUL}) while its guard stands and dark ({DARK}) once it falls.", ""]
    for state, colour in HIS.items():
        out += skill(state, twice(his(colour)))
    for k in "clr":
        out += skill(f"SOUL_{k.upper()}_LIT", twice([tint(f"glow_soul_{k}", SOUL)]))
        out += skill(f"SOUL_{k.upper()}_DARK", twice([tint(f"glow_soul_{k}", DARK)]))
    out += skill("WINDUP", [f"  - state{{m={NAME};s=windup}} @self"] + his(HIS["TELL"]) +
                 ["  - sound{s=entity.wither_skeleton.ambient;v=2;p=0.5} @self", "  - delay 8",
                  "  - sound{s=block.grindstone.use;v=1.2;p=0.5} @self"])
    out += skill("SWEEP", [f"  - state{{m={NAME};s=sweep}} @self", "  - delay 5",
                           "  - sound{s=entity.player.attack.sweep;v=2;p=0.5} @self",
                           "  - sound{s=item.trident.riptide_1;v=1.4;p=0.6} @self"])
    out += skill("ATTACK", [f"  - state{{m={NAME};s=attack}} @self",
                            "  - sound{s=entity.wither_skeleton.ambient;v=1.6;p=0.6} @self", "  - delay 13",
                            "  - sound{s=entity.player.attack.strong;v=1.8;p=0.5} @self",
                            "  - sound{s=block.anvil.land;v=0.8;p=0.5} @self"])
    out += skill("CALL", [f"  - state{{m={NAME};s=call}} @self", "  - delay 10",
                          "  - sound{s=block.anvil.land;v=1.4;p=0.5} @self", "  - delay 8",
                          "  - sound{s=entity.wither_skeleton.ambient;v=2;p=0.4} @self",
                          "  - sound{s=particle.soul_escape;v=2;p=0.6} @self"])
    out += skill("ENRAGE", [f"  - state{{m={NAME};s=enrage}} @self",
                            f"  - defaultstate{{m={NAME};t=idle;s=idle_enraged}} @self", "  - delay 21",
                            "  - sound{s=entity.generic.explode;v=1.4;p=0.5} @self",
                            "  - sound{s=block.anvil.land;v=1.4;p=0.4} @self"]
                 + twice(his(HIS["ENRAGED"])) +
                 ["  - delay 2", "  - sound{s=entity.wither.ambient;v=2;p=0.6} @self"])
    out += skill("FLINCH", [f"  - state{{m={NAME};s=flinch}} @self"])
    out += skill("DEATH", ["  - sound{s=entity.wither_skeleton.death;v=2;p=0.5} @self"]
                 + his(DARK) + [tint(f"glow_soul_{k}", DARK) for k in "clr"])
    return "\n".join(out)


def mobs():
    return "\n".join([
        "# The Hollow Warlord's body: the Headsman model (a giant wither skeleton in battered blackstone plate, the",
        "# executioner's sword, three taken skulls over his head) on an invisible wither skeleton carrier that holds nothing.",
        "# Occultech steers it, decides every swing, sweep and call, deals all damage (HollowWarlord.java) and hands out",
        "# loot. Health is the solo value; Occultech multiplies it for the group after the spawn.", "",
        "OCCULTECH_HOLLOW_WARLORD:", "  Type: WITHER_SKELETON", "  Display: '&8Hollow Warlord'", "  Health: 330",
        "  Damage: 0", "  Armor: 0", "  Options:", "    # Occultech rebuilds the fight from its saved state; Mythic never restores it",
        "    Despawn: true", "    PreventOtherDrops: true", "    PreventMobKillDrops: true", "    PreventItemPickup: true",
        "    MovementSpeed: 0.26", "    KnockbackResistance: 1", "    FollowRange: 48", "    AlwaysShowName: true",
        "  Drops: []",
        "  # The carrier stays at normal size; the model is drawn as authored (about 5.5 blocks to the top of his hat). Its",
        "  # ob_hitbox bone covers him and passes hits to the carrier. idle and walk play by themselves (idle_enraged once",
        "  # he enrages); the fight starts every other clip (Skills/HollowWarlord.yml).",
        "  Skills:", f"  - model{{m={NAME}}} @self ~onSpawn", f"  - state{{m={NAME};s=spawn}} @self ~onSpawn",
        "  - bodyrotation{mh=35;mnh=-35;rde=0;rdu=3} @self ~onSpawn",
        f"  - skill{{s={P}_CALM}} @self ~onSpawn", f"  - skill{{s={P}_DEATH}} @self ~onDeath", ""])


def main(argv):
    st.SKIN = Image.open(Path(argv[-1]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    check()
    print(json.dumps(ship(), indent=1))
    t = table()
    RIG_JAVA.write_text(java(t), encoding="utf-8")
    print(json.dumps(t, indent=1))
    SKILLS.write_text(skills(), encoding="utf-8")
    MOBS.write_text(mobs(), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
