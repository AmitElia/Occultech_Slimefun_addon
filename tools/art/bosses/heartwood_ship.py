"""The Heartwood Horror, session 8: ship the model, write its Mythic mob and cosmetic skills, and the rig table the
fight reads.

- src/main/models/occultech_heartwood_horror.bbmodel: the final rig (session 7: the painted model with its hitbox, glow
  bones and the twelve clips), carrying the **neutral** glows (session 6): the fight tints them per state. Three glow
  bones are renamed here, because BetterModel drops the glow_ tag from a bone's name and a tint would then also match
  the solid part of the same name: glow_lantern -> glow_heartlight (hi_lantern), glow_womb -> glow_chamber (womb),
  glow_sleeper -> glow_eyelids (sleeper).
- src/main/mythic/Mobs/HeartwoodHorror.yml and Skills/HeartwoodHorror.yml: look and sound only. HeartwoodHorror.java
  decides when each runs and deals every hit.
- src/main/java/.../boss/tier3/HeartwoodHorrorRig.java (generated): where the model's hands, womb and lantern are, in
  blocks from the carrier's feet (ahead, up, right), at the moments the fight needs.
- Refuses to ship with faces that would flicker, or with half-clear texels anywhere but the resin shell (the one
  deliberate exception: the user asked for transparent resin; the client sorts translucent item faces back to front).

Run from the repository root after heartwood_s7.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/heartwood_ship.py <folder>
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
from bosskit.bbmodel import pivot_matrix  # noqa: E402
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import heartwood_s3 as s3, heartwood_s4 as s4, heartwood_s6 as s6, heartwood_s7 as s7  # noqa: E402

MODELS = ROOT / "src/main/models"
SKILLS = ROOT / "src/main/mythic/Skills/HeartwoodHorror.yml"
MOBS = ROOT / "src/main/mythic/Mobs/HeartwoodHorror.yml"
RIG_JAVA = ROOT / "src/main/java/io/github/amitelia/occultech/boss/tier3/HeartwoodHorrorRig.java"
NAME = "occultech_heartwood_horror"
P = "HEARTWOOD_HORROR"
RENAME = {"glow_lantern": "glow_heartlight", "glow_womb": "glow_chamber", "glow_sleeper": "glow_eyelids"}
BLOOMS = ["glow_blooms_crutch1", "glow_blooms_crutch2", "glow_blooms_crutch4", "glow_blooms_great1",
          "glow_blooms_great2", "glow_blooms_great3", "glow_blooms_lesser1", "glow_blooms_lesser2", "glow_blooms_thin1",
          "glow_blooms_thin2", "glow_blooms_back0", "glow_blooms_back1", "glow_blooms_back2", "glow_blooms_back3",
          "glow_hump_blooms"]


def hexc(rgb):
    return "".join(f"{v:02X}" for v in rgb)


# the session 6 states: (blooms, the lantern's light, the sleeper's eyelids, the chamber behind the resin)
STATES = {
    "CALM": (s6.BLOOM["calm"], s6.LANTERN["calm"], s6.SLEEPER["shut"], s6.WOMB["calm"]),
    "VULNERABLE": (s6.BLOOM["vulnerable"], s6.LANTERN["vulnerable"], s6.SLEEPER["open"], s6.WOMB["vulnerable"]),
    "OUT": (s6.BLOOM["creak"], s6.LANTERN["creak"], s6.SLEEPER["shut"], s6.WOMB["creak"]),
    "DEAD": (s6.BLOOM["dead"], s6.LANTERN["dead"], s6.SLEEPER["dead"], s6.WOMB["dead"]),
}


def check():
    model = s3.model()
    for c in model.cubes:           # an inflated cube (the lantern's glow) is drawn that much bigger (as session 3)
        if c.inflate:
            c.frm = (np.array(c.frm) - c.inflate).tolist()
            c.to = (np.array(c.to) + c.inflate).tolist()
    clash = flicker_pairs([c for c in model.cubes if c.mat != "hitbox"])
    if clash:
        raise SystemExit(f"faces that would flicker in game: {clash[:5]}")


def ship():
    rig = json.loads((s7.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    for tex in rig["textures"]:
        rgba = np.array(Image.open(io.BytesIO(base64.b64decode(tex["source"].split(",", 1)[1]))).convert("RGBA"))
        half = (rgba[..., 3] > 0) & (rgba[..., 3] < 255)
        # no face but the resin shell's may show a half-clear texel (padding no face samples doesn't matter)
        shown = np.zeros(half.shape, bool)
        w = rgba.shape[1] / tex.get("uv_width", rgba.shape[1])
        h = rgba.shape[0] / tex.get("uv_height", rgba.shape[0])
        resin = {c.name for c in s3.model().cubes if c.mat in ("resin", "resin_dark")}
        for e in rig["elements"]:
            if e["name"] in resin:
                continue
            for f in e["faces"].values():
                if f.get("uv"):
                    u0, v0, u1, v1 = f["uv"]
                    shown[int(min(v0, v1) * h):int(np.ceil(max(v0, v1) * h)),
                          int(min(u0, u1) * w):int(np.ceil(max(u0, u1) * w))] = True
        stray = half & shown
        if stray.any():
            raise SystemExit(f"{int(stray.sum())} half-clear texels on faces other than the resin shell")
        print("half-clear texels, all on the resin shell:", int(half.sum()))
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
    names = []

    def walk(nodes):
        for n in nodes:
            if isinstance(n, dict):
                names.append(n["name"])
                walk(n.get("children", []))
    walk(rig["outliner"])
    for b in BLOOMS + list(RENAME.values()):
        assert b in names, b
    stripped = [n.split("_", 1)[1] if n.startswith(("glow_", "hi_", "ob_")) else n for n in names]
    dup = {n for n in stripped if stripped.count(n) > 1}
    if dup:
        raise SystemExit(f"bone names that clash once the tag is dropped: {sorted(dup)}")
    (MODELS / f"{NAME}.bbmodel").write_text(json.dumps(rig, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"animations": sorted(a["name"] for a in rig["animations"]), "elements": len(rig["elements"]),
            "bones": len(names)}


# ---- where the parts are --------------------------------------------------------------------------------------------------

def blocks(p):
    """Model units -> (ahead, up, right) in blocks from the carrier's feet: the model faces -z, its right is +x."""
    return (round(-float(p[2]) / 16, 3), round(float(p[1]) / 16, 3), round(float(p[0]) / 16, 3))


_TRACKS = {}


def centre(clip, t, group):
    from bosses.heartwood_clips import CLIPS
    if clip not in _TRACKS:
        _TRACKS[clip] = s7.tracks(CLIPS[clip])
    model = s3.model()
    mats = s7.matrices(model, _TRACKS[clip], t)
    pts = []
    for c in model.cubes:
        if c.group.name != group:
            continue
        m = mats[group] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        for x in (lo[0], hi[0]):
            for y in (lo[1], hi[1]):
                for z in (lo[2], hi[2]):
                    pts.append((m @ np.array([x, y, z, 1.0]))[:3])
    return np.mean(pts, axis=0)


def landing(clip, hands, after, floor=0.45, step=0.025):
    """The first moment after `after` at which any of `hands` is on the floor (the follow-through lands them a little
    after the keyed contact), and where every one of them is then."""
    from bosses.heartwood_clips import CLIPS
    t = after
    while t <= CLIPS[clip].length:
        pts = [centre(clip, t, h) for h in hands]
        if min(p[1] for p in pts) / 16 < floor:
            return round(t, 3), [blocks(p) for p in pts]
        t += step
    raise SystemExit(f"{clip}: {hands} never reach the floor")


def table():
    from bosses.heartwood_clips import CLIPS
    swipe_t, swipe = landing("swipe", ["hand_great"], CLIPS["swipe"].contact - 0.1)
    dig_t, _ = landing("eruption", ["hand_crutch", "hand_great", "hand_lesser", "hand_back"], 0.3)
    dig = [blocks(centre("eruption", dig_t + 0.1, h)) for h in ("hand_crutch", "hand_great", "hand_lesser", "hand_back")]
    slam_t, slam = landing("slam", ["hand_crutch", "hand_great"], CLIPS["slam"].contact - 0.1)
    slam = [blocks(centre("slam", slam_t, h)) for h in ("hand_crutch", "hand_great")]
    return {
        "swipe_t": swipe_t, "swipe": swipe[0],
        "lunge_t": CLIPS["lunge"].contact, "lunge": blocks(centre("lunge", CLIPS["lunge"].contact, "hand_great")),
        "dig_t": dig_t, "dig": dig,
        "slam_t": slam_t, "slam": slam,
        "sap_t": CLIPS["sap"].contact, "womb": blocks(centre("sap", CLIPS["sap"].contact, "glow_womb")),
        "lantern": blocks(centre("idle", 0.0, "hi_lantern")),
    }


def java(t):
    def vec(v):
        return "{" + ", ".join(f"{x}" for x in v) + "}"

    def vecs(vs):
        return "{" + ", ".join(vec(v) for v in vs) + "}"

    def ticks(sec):
        return int(round(sec * 20))

    return f"""package io.github.amitelia.occultech.boss.tier3;

/**
 * Where the Heartwood Horror model's parts are, in blocks from the carrier's feet, as {{ahead, up, right}} for the
 * carrier facing its body yaw, and when its hands land (ticks from the clip's start; follow-through lands a hand a little
 * after its key). Generated by tools/art/bosses/heartwood_ship.py from the session 7 clips; do not edit by hand.
 */
final class HeartwoodHorrorRig {{
    private HeartwoodHorrorRig() {{}}

    /** The great hand lands at the end of the swipe's rake ({t["swipe_t"]} s). */
    static final int SWIPE_CONTACT = {ticks(t["swipe_t"])};
    static final double[] SWIPE = {vec(t["swipe"])};
    /** The great hand at the lunge's stab ({t["lunge_t"]} s): a level thrust, not a blow to the floor. */
    static final int LUNGE_CONTACT = {ticks(t["lunge_t"])};
    static final double[] LUNGE = {vec(t["lunge"])};
    /** The hands driven into the floor as the eruption starts ({t["dig_t"]} s): crutch, great, lesser, back. */
    static final int DIG_CONTACT = {ticks(t["dig_t"])};
    static final double[][] DIG = {vecs(t["dig"])};
    /** The crutch and the great arm brought down together ({t["slam_t"]} s). */
    static final int SLAM_CONTACT = {ticks(t["slam_t"])};
    static final double[][] SLAM = {vecs(t["slam"])};
    /** The resin womb, lifted as the sap falls ({t["sap_t"]} s). */
    static final int SAP_CONTACT = {ticks(t["sap_t"])};
    static final double[] WOMB = {vec(t["womb"])};
    /** The creaking-heart lantern hanging under the brow (idle). */
    static final double[] LANTERN = {vec(t["lantern"])};
}}
"""


# ---- Mythic -----------------------------------------------------------------------------------------------------------------

def tints(state):
    bloom, light, eyelids, chamber = STATES[state]
    out = [f"  - tint{{m={NAME};p={b};c={hexc(bloom)}}} @self" for b in BLOOMS]
    out.append(f"  - tint{{m={NAME};p=glow_heartlight;c={hexc(light)}}} @self")
    out.append(f"  - tint{{m={NAME};p=glow_eyelids;c={hexc(eyelids)}}} @self")
    out.append(f"  - tint{{m={NAME};p=glow_chamber;c={hexc(chamber)}}} @self")
    return out


def twice(lines):
    """Applied, then again after BetterModel's hit flash would have restored the old tint."""
    return lines + ["  - delay 12"] + lines


def skill(name, lines):
    return [f"{P}_{name}:", "  Skills:"] + lines + [""]


def state(clip):
    return f"  - state{{m={NAME};s={clip}}} @self"


def skills():
    out = ["# Look and sound only. HeartwoodHorror.java decides when each of these runs and deals every hit.",
           "# Generated by tools/art/bosses/heartwood_ship.py. Its blooms, the lantern's light, the sleeper's eyelids and the",
           "# chamber behind the resin are painted neutral and tinted per state (session 6): CALM while the hearts stand,",
           "# VULNERABLE once the last one breaks (the sleeper's eyes open, the blooms go red), OUT for the creak, DEAD.", ""]
    for name in STATES:
        out += skill(name, twice(tints(name)))
    out += skill("SPAWN", [state("spawn")] + tints("OUT") + [
        "  - sound{s=block.creaking_heart.spawn;v=2;p=0.5} @self", "  - delay 24",
        "  - sound{s=entity.creaking.activate;v=2;p=0.5} @self"] + tints("CALM") + [
        "  - delay 32", "  - sound{s=entity.creaking.ambient;v=2.5;p=0.4} @self",
        "  - sound{s=entity.ravager.roar;v=1.2;p=0.6} @self"])
    out += skill("SWIPE", [state("swipe"), "  - sound{s=entity.creaking.ambient;v=1.6;p=0.6} @self", "  - delay 12",
                           "  - sound{s=entity.creaking.attack;v=2;p=0.6} @self",
                           "  - sound{s=block.roots.break;v=1.5;p=0.6} @self"])
    out += skill("LUNGE", [state("lunge"), "  - sound{s=entity.creaking.attack;v=2;p=0.5} @self"])
    out += skill("ERUPTION", [state("eruption"), "  - sound{s=entity.creaking.activate;v=2;p=0.5} @self",
                              "  - delay 12", "  - sound{s=block.rooted_dirt.break;v=2;p=0.5} @self",
                              "  - sound{s=block.roots.place;v=2;p=0.5} @self"])
    out += skill("SAP", [state("sap"), "  - sound{s=entity.creaking.ambient;v=2;p=0.5} @self", "  - delay 20",
                         "  - sound{s=block.resin.break;v=1.5;p=0.5} @self", "  - delay 15",
                         "  - sound{s=block.honey_block.slide;v=2;p=0.5} @self"])
    out += skill("SLAM", [state("slam"), "  - sound{s=entity.creaking.activate;v=2;p=0.5} @self", "  - delay 16",
                          "  - sound{s=entity.creaking.ambient;v=2;p=0.4} @self"])
    out += skill("CREAK", [state("creak"), "  - sound{s=entity.creaking.freeze;v=2;p=0.5} @self", "  - delay 3"]
                 + tints("OUT") + ["  - delay 7", "  - sound{s=entity.creaking.unfreeze;v=2;p=0.5} @self"])
    out += skill("TWITCH", [state("twitch"), "  - sound{s=entity.creaking.twitch;v=2;p=0.6} @self",
                            "  - sound{s=block.creaking_heart.break;v=2;p=0.6} @self"])
    out += skill("STAGGER", [state("stagger"), "  - sound{s=entity.creaking.twitch;v=2.5;p=0.4} @self",
                             "  - sound{s=block.creaking_heart.break;v=2;p=0.4} @self", "  - delay 4"]
                 + twice(tints("VULNERABLE")))
    out += skill("DEATH", ["  - sound{s=entity.creaking.death;v=2.5;p=0.5} @self"] + tints("DEAD"))
    return "\n".join(out)


def mobs():
    return "\n".join([
        "# The Heartwood Horror's body: the Crutch model (a hunched, tree-grown giant creaking on four stilt-thin limbs and a",
        "# crutch, an older creaking asleep in the resin womb of its chest, a creaking-heart lantern hanging from its brow)",
        "# on an invisible creaking carrier (an invisible creaking draws nothing, its eyes included). Occultech moves it,",
        "# decides every attack, deals all damage (HeartwoodHorror.java) and hands out loot. Health is the solo value;",
        "# Occultech multiplies it for the group after the spawn.", "",
        "OCCULTECH_HEARTWOOD_HORROR:", "  Type: CREAKING", "  Display: '&6Heartwood Horror'", "  Health: 320",
        "  Damage: 0", "  Armor: 0", "  Options:",
        "    # Occultech rebuilds the fight from its saved state; Mythic never restores it",
        "    Despawn: true", "    PreventOtherDrops: true", "    PreventMobKillDrops: true", "    PreventItemPickup: true",
        "    MovementSpeed: 0.2", "    KnockbackResistance: 1", "    FollowRange: 48", "    AlwaysShowName: true",
        "  Drops: []",
        "  # The carrier stays at normal size; the model is drawn as authored (about 7 blocks to the top of the hump). Its",
        "  # ob_hitbox bone covers the body and passes hits to the carrier. idle and walk play by themselves; the fight",
        "  # starts every other clip (Skills/HeartwoodHorror.yml).",
        "  Skills:", f"  - model{{m={NAME}}} @self ~onSpawn", f"  - skill{{s={P}_SPAWN}} @self ~onSpawn",
        "  - bodyrotation{mh=35;mnh=-35;rde=0;rdu=3} @self ~onSpawn",
        f"  - skill{{s={P}_DEATH}} @self ~onDeath", ""])


def main(argv):
    check()
    print(json.dumps(ship(), indent=1))
    t = table()
    RIG_JAVA.write_text(java(t), encoding="utf-8")
    print(json.dumps(t, indent=1))
    SKILLS.write_text(skills(), encoding="utf-8")
    MOBS.write_text(mobs(), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
