"""The Abyssal Warden redesign, session 7: animation (plan: docs/art/bosses/abyssal_warden/overhaul/plan.md).

Each clip is a few whole poses at key times, built with session 2's pose code (warden_s2.pose). The keyframes are:
- each bone's turn away from the rest pose;
- position keys for the model sinking and rising (`base`), the eye looking round (`glow_iris`), the valves jumping out
  (`valve0-3`) and the arm sliding out of the burst window (`arm`);
- the pupil's width as a scale key.
He glides with his carrier, so no clip travels. Glows and part swaps (the spray, the burst window, the hand, the
bloodshot white) are the fight's, in session 8: the clips only move bones.

Timed to AbyssalWarden.java:
  idle          4.0 s loop   hanging in the air: a slow bob and sway, the hose and the growth swaying after him, the
                             eye looking round
  idle_furious  2.0 s loop   below half: the same, tighter, the eye darting from spot to spot
  idle_33       3.0 s loop   from 33%: furious, the hand hovering beside him, its fingers flexing
  walk          2.0 s loop   gliding after a player: leaning in, the hose trailing
  spawn         3.0 s once   rising out of the circle, turning to face the arena, a small overshoot
  beam          2.6 s once   the eye locks on and the pupil narrows to a thread; contact at 2.0 s (the beam's 40
                             ticks), a recoil as it fires
  lash          0.9 s once   the hose whips round: the server hits as it starts, so contact at 0.25 s
  spikes        1.6 s once   he swells and the valves strain for the 20-tick warning; contact at 1.0 s, the valves
                             blow out
  rest          2.0 s once   the 40-tick rest after the spikes: he sinks, heaves and vents, the eye drooping, and rises
                             again at the end
  burst         2.4 s once   33%: he shudders as something pushes from inside; contact at 0.8 s (the window bursts),
                             the arm slides out and the hand claws open
  smash         2.8 s once   the hand rears over a player (the 1.25 s tell), slams at 1.25 s and stays down for 1 s
                             (the opening), then lifts
  flinch        0.4 s once   hit: a jolt
  death         3.6 s hold   a groaning shudder, then the hull tips over and sinks, the eye rolled up
  beam_33, lash_33, spikes_33, rest_33, flinch_33: the same with the hand out. Once the hand is shown, a clip that
  didn't key the arm would snap it back to its bind pose, straight out sideways.

Run from the repository root: python tools/art/bosses/warden_s7.py (after warden_s6.py)
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s7 as a7  # noqa: E402
from bosses import warden_s2 as s2, warden_s3 as s3, warden_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/abyssal_warden/overhaul/s6_variants"
P = {k: v[1] for k, v in s2.POSES.items()}
CONTACT = {"beam": 2.0, "lash": 0.25, "spikes": 1.0, "burst": 0.8, "smash": 1.25}
CONTACT.update({f"{k}_33": v for k, v in CONTACT.items() if k in ("beam", "lash", "spikes")})
OVERRIDE = ("spawn", "beam", "lash", "spikes", "rest", "burst", "smash", "flinch", "death",
            "beam_33", "lash_33", "spikes_33", "rest_33", "flinch_33")
LOOK = (0.2, -0.1)                                           # where the iris rests

# the hand from 33% (elbow, wrist, palm normal, finger direction; in the body's space)
HOVER = ((62, 70, 4), (66, 92, -16), (-0.4, -0.5, -0.7), (0, 0.8, -0.5))
HOVER_FLEX = ((62, 68, 6), (67, 89, -13), (-0.35, -0.55, -0.7), (0.1, 0.75, -0.6))
HANG = ((62, 60, 6), (74, 46, -8), (-0.9, -0.1, 0.4), (0.4, -0.6, -0.7))          # dangling as he dies
PROP = ((70, 49, -6), (76, 22, -26), (0, -0.98, 0.2), (-0.15, -0.2, -1))             # propped on the floor: the rest
BIND = (tuple(s2.BIND_ELBOW), tuple(s2.BIND_WRIST), s2.BIND_PALM, tuple(s2.SIDE))   # straight out of the window
WINDUP = ((64, 72, 0), (72, 96, -22), (-0.1, -0.6, -0.8), (-0.1, 0.7, -0.7))
CLAWED = ((58, 76, 10), (60, 100, -8), (-0.7, -0.3, -0.6), (0, 0.95, -0.3))


def spec(start=None, **changes):
    out = dict(start or {})
    out.update(changes)
    return out


def hose(*yaws, pitch=0):
    return tuple((pitch, y, 0) for y in yaws)


def with_arm(keys, arm):
    """A clip's keys with the hand out: every key without an arm of its own holds `arm`."""
    return [(t, sp if "arm" in sp else spec(sp, arm=arm)) for t, sp in keys]


def clips():
    still = {}
    sway = lambda d, **k: spec(base=(0, 1.5 * d, 0), body=(2 * d, 4 * d, 0), growth=(d, 0),   # noqa: E731
                               hose=hose(4 * d, 6 * d, 8 * d, 6 * d), **k)
    idle = [(0, still), (1.0, sway(1, look=(0.35, -0.05))), (2.0, spec(growth=(0, 1))),
            (3.0, sway(-1, look=(0.0, -0.15))), (4.0, still)]

    darts = [(0.35, -0.05), (0.0, -0.25), (0.42, 0.12), (0.12, -0.3)]
    furious = []
    for i, look in enumerate(darts):                 # a quick move, then a hold: darting, not drifting
        t = i * 0.5
        d = 1 if i % 2 == 0 else -1
        k = sway(0.6 * d, look=look, pupil=0.8)
        furious += [(t, k), (t + 0.4, spec(k, look=look))]
    furious.append((2.0, spec(sway(0.6), look=darts[0], pupil=0.8)))

    hover = []
    for i, look in enumerate(darts[:3]):
        t = i * 1.0
        hover += [(t, sway(0.5 if i % 2 == 0 else -0.5, look=look, pupil=0.8, arm=HOVER if i % 2 == 0 else HOVER_FLEX)),
                  (t + 0.85, sway(0.4 if i % 2 == 0 else -0.4, look=look, pupil=0.8,
                                  arm=HOVER if i % 2 == 0 else HOVER_FLEX))]
    hover.append((3.0, hover[0][1]))

    lean = lambda d: spec(body=(-6, 0, 1.5 * d), base=(0, 1.0 * d, 0), hose=hose(-6 * d, -8 * d, -10 * d, -8 * d),   # noqa: E731
                          growth=(0, -2), look=(0.2, -0.2))
    walk = [(0, lean(0)), (0.5, lean(1)), (1.0, lean(0)), (1.5, lean(-1)), (2.0, lean(0))]

    spawn = [(0, spec(base=(0, -96, 0), body=(14, -90, 0), look=(0.2, 0.4), pupil=1.4, growth=(0, 4))),
             (1.4, spec(base=(0, -40, 0), body=(8, -30, 0), look=(0.2, 0.3), pupil=1.3, growth=(0, 3))),
             (2.2, spec(base=(0, 4, 0), body=(-4, 4, 0), look=(0.3, -0.1), growth=(0, -2))),
             (2.6, spec(base=(0, -1, 0), body=(1, 0, 0))), (3.0, still)]

    lock = spec(body=(-6, 0, 0), look=(0.35, -0.2), pupil=0.35)
    beam = [(0, still), (0.3, lock), (1.0, spec(lock, body=(-7, 1, 1))), (1.6, spec(lock, body=(-8, 0, 0), pupil=0.25)),
            (2.0, spec(lock, body=(-2, 0, 0), pupil=1.3)), (2.15, spec(lock, body=(-3, 0, 0), pupil=1.2)),
            (2.6, still)]

    lash = [(0, still), (0.1, spec(body=(0, 8, -4), hose=hose(-14, -10, -8, -4), growth=(-2, 0))),
            (0.25, spec(P["lash"])),
            (0.45, spec(P["lash"], hose=hose(44, 40, 34, 24), body=(3, -16, 7))), (0.9, still)]

    spikes = [(0, still), (0.4, spec(valves=0.8, body=(3, 0, 0), pupil=1.2, base=(0, 1, 0))),
              (0.8, spec(valves=1.2, body=(4, 0, 2), pupil=1.4, base=(0, 1.5, 0))),
              (0.95, spec(valves=1.0, body=(4, 0, -2), pupil=1.4, base=(0, 1.5, 0))),
              (1.0, spec(P["spikes"], base=(0, 2, 0))), (1.2, spec(P["spikes"], valves=3.4, body=(7, 0, 0))),
              (1.6, spec(valves=2.5, body=(2, 0, 0), pupil=1.3))]

    sunk = spec(P["rest"])
    rest = [(0, spec(valves=2.5, body=(2, 0, 0), pupil=1.3)), (0.5, sunk),
            (1.1, spec(sunk, body=(-12, 0, 8), base=(0, -2.5, 0), valves=0.5)), (1.6, sunk), (2.0, still)]

    # the arm is hidden until the window bursts (the fight shows it at contact). It slides straight out along the
    # window's axis - any other way the rigid arm would poke through the hull - and only then rears up
    inside = dict(look=(0.45, 0), pupil=1.5, arm=BIND, arm_out=50)
    burst = [(0, spec(**inside)), (0.3, spec(inside, body=(0, -8, -6))), (0.5, spec(inside, body=(0, -4, -2))),
             (0.7, spec(inside, body=(0, -12, -10))), (0.8, spec(inside, body=(0, -14, -12))),
             (1.05, spec(P["burst"], arm=BIND, arm_out=0, body=(0, -6, -4))),
             (1.45, spec(P["burst"])), (1.8, spec(P["burst"], arm=CLAWED)),
             (2.4, spec(look=(0.35, -0.05), pupil=0.8, arm=HOVER))]

    raised = spec(P["raised"])
    slam = spec(P["slam"])
    smash = [(0, spec(look=(0.35, -0.05), pupil=0.8, arm=HOVER)), (0.6, raised),
             (1.1, spec(raised, arm=WINDUP, body=(3, 0, -3))), (1.25, slam),
             (1.35, spec(slam, body=(-5, 0, 0))), (2.25, slam),
             (2.8, spec(look=(0.35, -0.05), pupil=0.8, arm=HOVER))]

    jolt = spec(body=(4, 6, 4), look=(0.25, 0.05), pupil=0.7)
    flinch = [(0, still), (0.08, jolt), (0.4, still)]

    dead = spec(P["death"])
    death = [(0, spec(arm=HOVER)), (0.3, spec(body=(4, 0, -6), look=(0, 0.4), arm=HOVER)),
             (0.6, spec(body=(-4, 0, 6), look=(0, 0.45), arm=HOVER)),
             (1.0, spec(body=(-10, 6, 10), base=(0, -1, 0), pupil=0.8, look=(0, 0.5), arm=HANG)),
             (2.2, dead), (2.6, spec(dead, base=(0, -5, 0))), (3.6, dead)]

    out = {
        "idle": (4.0, "loop", idle), "idle_furious": (2.0, "loop", furious), "idle_33": (3.0, "loop", hover),
        "walk": (2.0, "loop", walk), "spawn": (3.0, "once", spawn), "beam": (2.6, "once", beam),
        "lash": (0.9, "once", lash), "spikes": (1.6, "once", spikes), "rest": (2.0, "once", rest),
        "burst": (2.4, "once", burst), "smash": (2.8, "once", smash), "flinch": (0.4, "once", flinch),
        "death": (3.6, "hold", death),
    }
    for name in ("beam", "lash", "spikes", "flinch"):
        length, loop, keys = out[name]
        out[f"{name}_33"] = (length, loop, with_arm(keys, HOVER))
    length, loop, keys = out["rest"]
    out["rest_33"] = (length, loop, [(t, spec(sp, arm=PROP if 0 < t < 2.0 else HOVER)) for t, sp in keys])
    return out


# ---- tracks --------------------------------------------------------------------------------------------------------

_POSED = {}


def posed(sp):
    """The bones' rotations for one key's pose, from session 2's pose code."""
    key = json.dumps(sp, sort_keys=True, default=str)
    if key not in _POSED:
        tmp = f"_s7_{len(_POSED)}"
        s2.POSES[tmp] = ("", {k: v for k, v in sp.items() if k != "arm_out"})
        try:
            m = s3.build(tmp)
        finally:
            del s2.POSES[tmp]
        _POSED[key] = {g.name: list(g.rotation) for g in m.groups}
    return _POSED[key]


def positions(sp):
    """Position and scale keys for one pose (model units; Blockbench's x is flipped on export)."""
    pos = {"base": tuple(map(float, sp.get("base", (0, 0, 0))))}
    lx, ly = sp.get("look", LOOK)
    pos["glow_iris"] = (16 * (lx - LOOK[0]), 16 * (ly - LOOK[1]), 0.0)
    for i, d in enumerate(s2.VALVES):
        d = np.array(d, float) / np.linalg.norm(d) * sp.get("valves", 0)
        pos[f"valve{i}"] = tuple(map(float, d))
    pos["arm"] = tuple(map(float, -s2.SIDE * sp.get("arm_out", 0)))
    return pos


def tracks(clip, rest_rot):
    length, loop, keys = clip
    poses = [(t, sp, posed(sp)) for t, sp in keys]
    bones = {}
    for name in sorted(rest_rot):
        if name.endswith(tuple(f"_col{i}" for i in range(12))):
            continue
        out, prev = [], None
        for t, _, rot in poses:
            d = [a7.wrap(rot[name][i] - rest_rot[name][i]) for i in range(3)]
            if prev is not None:                      # keep the track continuous: never the long way round
                d = [d[i] + 360 * round((prev[i] - d[i]) / 360) for i in range(3)]
            prev = d
            out.append((t, tuple(round(v, 2) for v in d), "catmullrom"))
        if any(abs(v) > 0.05 for _, k, _ in out for v in k):
            bones[name] = {"rotation": out}
    for bone in ("base", "glow_iris", "arm") + tuple(f"valve{i}" for i in range(4)):
        ks = [(t, tuple(round(v, 3) for v in positions(sp)[bone]), "catmullrom") for t, sp, _ in poses]
        if any(abs(v) > 1e-6 for _, k, _ in ks for v in k):
            bones.setdefault(bone, {})["position"] = ks
    sc = [(t, (float(sp.get("pupil", 1.0)), 1.0, 1.0), "catmullrom") for t, sp, _ in poses]
    if any(abs(k[0] - 1) > 1e-6 for _, k, _ in sc):
        bones.setdefault("pupil", {})["scale"] = sc
    return bones


def floor_check(clip_defs):
    """The lowest point of every key pose with the hand out: nothing may sink under the floor (y 0)."""
    low = {}
    for name, (_, _, keys) in clip_defs.items():
        for t, sp in keys:
            if "arm" not in sp or (name == "burst" and t < CONTACT["burst"]):
                continue
            tmp = "_floor"
            s2.POSES[tmp] = ("", {k: v for k, v in sp.items() if k != "arm_out"})
            try:
                m = s3.build(tmp)
            finally:
                del s2.POSES[tmp]
            ys = [c.corners()[:, 1].min() for c in m.cubes if c.group.name in ("arm", "forearm", "hand")]
            low[f"{name}@{t}"] = round(float(min(ys)), 1)            # the pose already moves the base
    return low


def animations(model_id, clip_set):
    anims = a7.blockbench_animations(model_id, {n: (c[0], c[1], {b: {k: v for k, v in ch.items() if k != "scale"}
                                                                  for b, ch in c[2].items()})
                                                for n, c in clip_set.items()}, OVERRIDE)
    for anim, (name, (_, _, bones)) in zip(anims, clip_set.items()):  # a7 writes rotation and position only
        sc = bones.get("pupil", {}).get("scale")
        if not sc:
            continue
        uid = a7._uuid(f"{model_id}/group/pupil")
        an = anim["animators"].setdefault(uid, {"name": "pupil", "type": "bone", "keyframes": []})
        for t, v, interp in sc:
            an["keyframes"].append({"channel": "scale", "data_points": [{"x": v[0], "y": v[1], "z": v[2]}],
                                    "time": round(t, 3), "color": -1, "interpolation": interp,
                                    "uuid": a7._uuid(f"{model_id}/{name}/pupil/scale/{t}")})
    return anims


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    (OUT / "gifs").mkdir(exist_ok=True)
    rest_rot = {g.name: list(g.rotation) for g in s3.build("idle").groups}
    defs = clips()
    clip_set = {name: (c[0], c[1], tracks(c, rest_rot)) for name, c in defs.items()}
    low = floor_check(defs)
    under = {k: v for k, v in low.items() if v < 0}
    print("lowest hand point per key (model units):", min(low.values()), "under the floor:", under)
    rig = json.loads((S6 / f"{s3.MODEL_ID}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = animations(s3.MODEL_ID, clip_set)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
        for variant in ("_spikes", "_33"):                   # one model with every clip replaces the review variants
            (s3.SERVER_MODELS / f"{s3.MODEL_ID}{variant}.bbmodel").unlink(missing_ok=True)

    a7.s4, a7.OUT = s4, OUT                                  # the Archevoker's preview, in the Warden's zone colours
    model = s4.zoned("idle")
    before = ("spray", "window_r_burst", "arm", "forearm", "hand")
    after = ("spray", "window_r_glass")
    kw = {"yaw": -50, "pitch": 12, "scale": 2.2, "floor": 0.95}
    pre = {n: c for n, c in clip_set.items() if not n.endswith("_33") and n not in ("idle_33", "burst", "smash", "death")}
    post = {n: c for n, c in clip_set.items() if n not in pre}
    a7.previews(model, pre, "", dict(kw, hide=before), CONTACT,
                "The Abyssal Warden - key frames before 33% (session 7); the GIFs show the motion").save(
        OUT / "keyframes.png")
    a7.previews(model, post, "", dict(kw, hide=after, scale=1.9, yaw=50), CONTACT,
                "The Abyssal Warden - key frames from 33%, with the hand").save(OUT / "keyframes_33.png")
    summary = {n: {"length": v[0], "loop": v[1], "bones": len(v[2])} for n, v in clip_set.items()}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "clips": summary, "hand_lowest": low}, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
