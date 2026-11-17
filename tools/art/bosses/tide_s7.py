"""The Tidebreaker redesign, session 7: animation (plan: docs/art/bosses/tidebreaker/overhaul/plan.md).

Each clip is a few whole poses at key times, built with session 2's pose code. Both models carry the same clip names, so
the server plays one name on both. The Viking is a separate model on a passenger, so his clips follow the deck: his
`rider` bone gets the pitch and the movement of the deck under his feet. idle and walk keep the deck still, since the two
models play those on their own; the server bobs the whole boss instead. Movement over the ground stays with the server.

Timed to Tidebreaker.java:
  idle       4.0 s loop   floating: a wave runs down the tentacles, the lantern sways, he breathes
  walk       2.0 s loop   gliding: nose up, the tentacles streaming and pumping
  spawn      2.6 s once   rising out of the circle, the tentacles unfurling
  ram_tell   1.0 s once   the 20-tick warning: the shell rears back, the tentacles coil, he couches the spear
  ram        1.25 s once  the charge (25 ticks): bow down, the tentacles pumping
  winded     2.0 s once   the 40-tick opening: he sags over the rail, the eye snaps open and rolls, then recovers
  throw      1.2 s once   the volley: drawn back, release at 0.7 s, follow through
  thrust     0.6 s once   the jab: contact at 0.25 s
  flinch     0.4 s once   hit (the Viking only)
  death      3.0 s hold   he slumps over the bow; the animal pulls in and sinks

Run from the repository root, with a folder holding the 26.2 zombie textures as the last argument (after tide_s6.py):
python tools/art/bosses/tide_s7.py <folder>
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, rotation_matrix  # noqa: E402
from bosses import archevoker_s7 as a7, tide_s2 as s2, tide_s3 as s3, tide_s4 as s4  # noqa: E402
from bosses.tide_silhouettes import CY, CZ  # noqa: E402

OUT = ROOT / "docs/art/bosses/tidebreaker/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/tidebreaker/overhaul/s6_variants"
a7.OUT = OUT
a7.s4.ZONES, a7.s4.GLOWING = s4.ZONES, ("glow",)
P = {k: v[1] for k, v in s2.POSES.items()}
OVERRIDE = ("ram_tell", "ram", "winded", "throw", "thrust", "flinch")
CONTACT = {"ram_tell": 1.0, "throw": 0.7, "thrust": 0.25}
TAU = 2 * math.pi


def spec(start, **changes):
    return {**start, **changes}


def clips():
    rest = spec(P["idle"], wave=(0.14, 0.0), lantern=0)
    drift = lambda ph, dy, pitch, lamp, tb: spec(rest, base=(0, 0), wave=(0.14, ph), lantern=lamp, torso=(tb, 0, 0))  # noqa: E731
    glide = spec(P["glide"], wave=(0.22, 0.0), lantern=0)
    swim = lambda ph, dy, lamp, tent="glide": spec(glide, base=(0, 0), wave=(0.22, ph), lantern=lamp, tent=tent)  # noqa: E731
    rear = spec(P["ram"], base=(11, 1), tent=((.35, -.3, .8), (-.3, -.3, .3), (-.6, .3, -.6)), torso=(-12, 0, 0), lantern=-16)
    ram = spec(P["ram"], lantern=14, wave=(0.2, 0.0))
    wind = spec(P["winded"], lantern=0)
    slump = spec(wind, base=(-4, -3.8), torso=(-30, 8, 0), head=(4, 8, 0), lantern=20, lid=4)
    roll = lambda pu, head: spec(wind, pupil=pu, head=head, lantern=-6)  # noqa: E731
    th = P["throw"]
    draw = spec(th, torso=(14, -22, 0), head=(-8, 22, 0))
    arm_rel = (((1.2, -2, -4), (.4, -3.2, -11)), th["arms"][1])
    release = spec(th, torso=(-16, 12, 0), head=(0, -6, 0), arms=arm_rel, spear=(0, -.1, -1))
    thr = P["thrust"]
    pull = spec(thr, torso=(-6, -10, 0), arms=(((1.2, -4.5, 3), (.6, -7, 3)), thr["arms"][1]), spear=(0, -.2, -1))
    gasp = spec(rest, head=(16, 0, 0), torso=(4, 0, 0), lantern=10)
    dead = spec(P["death"], lantern=-24)
    half = spec(dead, base=(-6, -3), torso=(-30, 0, 6), head=(-12, 0, 8), tent="trail", lantern=12)
    hit = spec(rest, torso=(4, 0, 5), head=(12, 8, 6))
    return {
        "idle": (4.0, "loop", [(0, drift(0, 0, 0, 0, -4)), (1, drift(TAU / 4, 1.2, 1.5, 8, -5.5)), (2, drift(TAU / 2, 0, 0, 0, -4)),
                               (3, drift(3 * TAU / 4, -1.2, -1.5, -8, -3)), (4, drift(TAU, 0, 0, 0, -4))]),
        "walk": (2.0, "loop", [(0, swim(0, 0, -10)), (.5, swim(TAU / 4, 1.5, 0)), (1, swim(TAU / 2, 0, 10)),
                               (1.5, swim(3 * TAU / 4, -1.5, 0)), (2, swim(TAU, 0, -10))]),
        "spawn": (2.6, "once", [(0, spec(rest, base=(-20, -56), tent="pulled", wave=(0, 0))),
                                (.9, spec(rest, base=(-14, -30), tent="pulled", wave=(0, 0))),
                                (1.7, spec(rest, base=(-4, -4), tent="splay", wave=(0, 0), lantern=14)),
                                (2.2, spec(rest, base=(4, 2.5), wave=(.2, 1), lantern=-10)), (2.6, rest)]),
        "ram_tell": (1.0, "once", [(0, rest), (.45, rear), (.85, spec(rear, base=(13, 1.5))), (1.0, spec(rear, base=(13, 1.5)))]),
        "ram": (1.25, "once", [(t, spec(ram, tent="splay", wave=(.1, 1), base=(-9, 1.2), lantern=8) if i % 2 else ram)
                               for i, t in enumerate((0, .25, .5, .75, 1.0, 1.25))]),
        "winded": (2.0, "once", [(0, ram), (.2, slump), (.5, wind), (.9, roll((0, 1, 2), (10, -10, 0))), (1.3, roll((0, -1, -2), (14, 16, 0))),
                                 (1.65, wind), (2.0, rest)]),
        "throw": (1.2, "once", [(0, rest), (.45, th), (.62, draw), (.7, release), (.85, release), (1.2, rest)]),
        "thrust": (.6, "once", [(0, rest), (.12, pull), (.25, thr), (.35, thr), (.6, rest)]),
        "flinch": (.4, "once", [(0, rest), (.1, hit), (.4, rest)]),
        "death": (3.0, "hold", [(0, rest), (.5, gasp), (1.4, half), (2.4, dead), (3.0, dead)]),
    }


_POSED = {}


def fresh(kind):
    if kind == "mount":
        return s2.mount_rig("p")
    m = Model("p")
    s2.viking_rig(m.group("carrier", (0, 0, 0)), (0, 0, 0), False)
    return m


def posed(kind, sp):
    k = kind + json.dumps(sp, sort_keys=True, default=str)
    if k not in _POSED:
        m = fresh(kind)
        if kind == "mount":
            s2.pose_mount(m, {**sp, "base": (sp["base"][0], 0), "lid": 0, "pupil": None})
        else:
            s2.pose_rider(m, sp)
        _POSED[k] = {g.name: list(g.rotation) for g in m.groups}
    return _POSED[k]


def wrap(d):
    return (d + 180) % 360 - 180


def deck(sp):
    """Where the deck under his feet moves to: (pitch, offset)."""
    pitch, dy = sp["base"]
    c = np.array((0.0, CY, CZ))
    f = np.array(s2.FEET)
    return pitch, tuple(float(v) for v in c + rotation_matrix((pitch, 0, 0)) @ (f - c) - f + (0, dy, 0))


def tracks(kind, clip, rest):
    length, loop, keys = clip
    poses = [(t, sp, posed(kind, sp)) for t, sp in keys]
    moving = {n for _, _, rot in poses for n, r in rot.items() if any(abs(wrap(r[i] - rest[n][i])) > 0.05 for i in range(3))}
    bones = {}
    for name in sorted(moving):
        out, prev = [], None
        for t, _, rot in poses:
            d = [wrap(rot[name][i] - rest[name][i]) for i in range(3)]
            if prev is not None:
                d = [d[i] + 360 * round((prev[i] - d[i]) / 360) for i in range(3)]
            prev = d
            out.append((t, tuple(round(v, 2) for v in d), "catmullrom"))
        bones[name] = {"rotation": out}

    def channel(bone, ch, fn):
        ks = [(t, tuple(round(float(v), 3) for v in fn(sp)), "catmullrom") for t, sp, _ in poses]
        if any(any(abs(v) > 1e-6 for v in k[1]) for k in ks):
            bones.setdefault(bone, {})[ch] = ks

    if kind == "mount":
        channel("base", "position", lambda sp: (0, sp["base"][1], 0))
        channel("lantern", "rotation", lambda sp: (0, 0, sp.get("lantern", 0)))
        for side in s2.SIDES.values():
            channel(f"lid_{side}", "position", lambda sp: (0, sp.get("lid") or 0, 0))
            channel(f"pupil_{side}", "position", lambda sp: sp.get("pupil") or (0, 0, 0))
    else:
        channel("rider", "rotation", lambda sp: (deck(sp)[0], 0, 0))
        channel("rider", "position", lambda sp: deck(sp)[1])
    return bones


def lowest(sp):
    m = s2.mount_rig("low")
    s2.viking_rig(s2.group(m, "base"), s2.FEET, False)
    s2.pose_mount(m, sp)
    s2.pose_rider(m, sp)
    return float(m.bounds()[0][1])


def main():
    (OUT / "gifs").mkdir(parents=True, exist_ok=True)
    defs = clips()
    sets = {}
    for kind, name in (("mount", s3.MOUNT_ID), ("rider", s3.RIDER_ID)):
        rest = posed(kind, P["idle"])
        chosen = {n: c for n, c in defs.items() if kind == "rider" or n != "flinch"}
        sets[kind] = {n: (c[0], c[1], tracks(kind, c, rest)) for n, c in chosen.items()}
        rig = json.loads((S6 / f"{name}.bbmodel").read_text(encoding="utf-8"))
        rig["animations"] = a7.blockbench_animations(name, sets[kind], OVERRIDE)
        p = OUT / f"{name}.bbmodel"
        p.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    floor = {n: round(min(lowest(sp) for _, sp in c[2]), 1) for n, c in defs.items()}
    print("lowest y per clip", floor)
    model = s2.model("idle", preview=False)
    both = {}
    for n in defs:
        b = dict(sets["rider"][n][2])
        b.pop("rider", None)                                  # in the preview he stands on the moving deck already
        b.update(sets["mount"].get(n, (0, 0, {}))[2])
        both[n] = (defs[n][0], defs[n][1], b)
    a7.previews(model, both, "", {"yaw": -58, "pitch": 10, "scale": 2.5}, CONTACT,
                "The Tidebreaker - key frames (session 7); the GIFs show the motion").save(OUT / "keyframes.png")
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "lowest_y": floor,
                                                "clips": {n: {"length": c[0], "loop": c[1]} for n, c in defs.items()}},
                                               indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
