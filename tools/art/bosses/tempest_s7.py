"""The Tempest redesign, session 7: animation (plan: docs/art/bosses/tempest/overhaul/plan.md).

Each clip is a few of session 2's whole poses at key times plus small additive moves (the whirl's spin, the twister's
spin, the shards' drift). Keys are deltas from the bind pose (the whole seal), so a clip that returns a shard to its true
place returns it to exactly zero.

Timed to Tempest.java (session 8 moves the attacks onto these contacts):
  idle     4.0 s loop   the frozen blast breathing: the arms whirl a full turn, the twister spins the other way, the
                        shards drift on the wind out of step, the head bobs, the blown tip wobbles
  squall   2.0 s loop   while the squall ring closes in: idle at double speed, the whirl opened a little
  spawn    2.6 s once   the seal comes through the circle WHOLE, then cracks open into the frozen blast
  volley   1.4 s once   gust volley: the seal snaps together (0.5 s), the charges leave through the cracks at 0.7 s
                        (contact), it holds, then flies apart again
  burst    1.2 s hold   wind burst: drawn in tight through the 1 s warning, flung out at 1.0 s (contact) and held
  spent    1.5 s hold   straight after the burst: everything drops to the floor and stays down (the opening)
  recover  0.8 s once   the opening ends: the shards lift and are flung back out into the blast
  split    2.4 s once   below half: drawn in, then the seal breaks into two halves at 1.0 s (the gales join), back
  flinch   0.4 s once   hit: the head kicks back, the shards jolt outwards
  death    3.0 hold     a last flare outwards, then everything falls

Run from the repository root, after tempest_s6.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/tempest_s7.py <folder>
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import _uuid  # noqa: E402
from bosses import archevoker_s7 as a7  # noqa: E402
from bosses import tempest_s3 as s3, tempest_s4 as s4  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/tempest/overhaul/s6_variants"
a7.OUT = OUT
a7.s4.ZONES, a7.s4.GLOWING = s4.ZONES, s4.GLOWING
CONTACT = {"volley": 0.7, "burst": 1.0, "split": 1.0}
OVERRIDE = ("spawn", "volley", "burst", "spent", "recover", "split", "flinch", "death")
TAU = 2 * math.pi
SHARDS = [f"shard{i}" for i in range(7)]


def wrap(d):
    return (d + 180) % 360 - 180


_REST = None
_TABLES = {}


def rest():
    global _REST
    if _REST is None:
        _REST = s3.rest_model()
    return _REST


def table(pose):
    """A named pose as (absolute rotation, offset from its parent, scale) per bone."""
    if pose not in _TABLES:
        r_org = {g.name: np.array(g.origin) for g in rest().groups}
        posed = s3.build(pose)
        moved = {g.name: np.array(g.origin) - r_org[g.name] for g in posed.groups}
        rot, pos, scl = {}, {}, {}
        for g in posed.groups:
            rot[g.name] = np.array(g.rotation, float)
            parent = moved.get(g.parent.name, np.zeros(3)) if g.parent is not None else np.zeros(3)
            pos[g.name] = moved[g.name] - parent
            scl[g.name] = np.array(getattr(g, "scale", None) or (1, 1, 1), float)
        _TABLES[pose] = (rot, pos, scl)
    return _TABLES[pose]


# ---- additive moves: bone -> (rotation, position) ---------------------------------------------------------------------

def drift(ph, amp=1.0):
    out = {}
    for i, n in enumerate(SHARDS):
        s = math.sin(ph + i * 0.9)
        # in the seal's frame local z is world down: this bobs each shard up and down, and rocks it a little
        out[n] = ((s * 3 * amp, 0, math.cos(ph + i * 0.7) * 2 * amp), (0, 0, -s * 1.6 * amp))
    out["hi_head"] = ((math.sin(ph + 0.5) * 2 * amp, 0, 0), (0, math.sin(ph) * 1.2 * amp, 0))
    out["tip"] = ((math.sin(ph) * 6 * amp, math.cos(ph) * 6 * amp, 0), (0, 0, 0))
    out["circlet"] = ((0, math.sin(ph * 2) * 3 * amp, 0), (0, 0, 0))
    return out


def kick():
    out = {n: ((0, 0, 0), (0, 0, 0)) for n in SHARDS}
    out["hi_head"] = ((12, 0, -6), (0, 1.5, 0))
    for i, n in enumerate(SHARDS):
        out[n] = ((4 if i % 2 else -4, 0, 0), (0, 0, 0))
    return out


def gather():
    return {"hi_head": ((-6, 0, 0), (0, -2, 0))}


# ---- the clips ------------------------------------------------------------------------------------------------------------

def clips():
    """name -> (length, loop, [(t, pose, extras)], spin) where spin = turns of the whirl and the twister over the clip."""
    idle = [(t, "idle", drift(TAU * t / 4)) for t in (0, 1, 2, 3, 4)]
    squall = [(t, "idle", drift(TAU * t / 2, 1.4)) for t in (0, 0.5, 1, 1.5, 2)]
    return {
        "idle": (4.0, "loop", idle, 1.0),
        "squall": (2.0, "loop", squall, 1.0),
        "spawn": (2.6, "once", [(0, "spent", {}), (0.9, "locked", {}), (1.5, "locked", gather()), (1.85, "burst", {}),
                                (2.6, "idle", {})], 0),
        "volley": (1.4, "once", [(0, "idle", {}), (0.5, "locked", gather()), (0.7, "locked", {}), (0.9, "locked", {}),
                                 (1.4, "idle", {})], 0),
        "burst": (1.2, "hold", [(0, "idle", {}), (0.6, "locked", {}), (0.92, "locked", gather()), (1.0, "burst", {}),
                                (1.2, "burst", {})], 0),
        "spent": (1.5, "hold", [(0, "burst", {}), (0.45, "spent", {}), (1.5, "spent", {})], 0),
        "recover": (0.8, "once", [(0, "spent", {}), (0.45, "burst", {}), (0.8, "idle", {})], 0),
        "split": (2.4, "once", [(0, "idle", {}), (0.7, "locked", gather()), (1.0, "split", {}), (1.6, "split", {}),
                                (2.4, "idle", {})], 0),
        "flinch": (0.4, "once", [(0, "idle", {}), (0.1, "idle", kick()), (0.4, "idle", {})], 0),
        "death": (3.0, "hold", [(0, "idle", {}), (0.4, "burst", {}), (1.8, "death", {}), (3.0, "death", {})], 0),
    }


def spin_track(length, turns, sign, base=(0.0, 0.0, 0.0), axis=1):
    """A continuous linear turn: keys at thirds so no step passes 180 degrees."""
    out = []
    for t in (0, length / 3, 2 * length / 3, length):
        v = list(base)
        v[axis] += sign * 360.0 * turns * t / length
        out.append((t, tuple(v), "linear"))
    return out


LINEAR = ("death",)        # a falling clip must not overshoot through the floor between keys


def tracks(clip, name=""):
    length, loop, keys, turns = clip
    interp = "linear" if name in LINEAR else "catmullrom"
    rest_rot = {g.name: np.array(g.rotation, float) for g in rest().groups}
    bones = {}
    for bone in rest_rot:
        rot, pos, scl, prev = [], [], [], None
        for t, pose, extra in keys:
            r, p, s = table(pose)
            er, ep = extra.get(bone, ((0, 0, 0), (0, 0, 0)))
            d = [wrap(r[bone][i] - rest_rot[bone][i]) + er[i] for i in range(3)]
            if prev is not None:
                d = [d[i] + 360 * round((prev[i] - d[i]) / 360) for i in range(3)]
            prev = d
            rot.append((t, tuple(round(float(v), 2) for v in d), interp))
            pos.append((t, tuple(round(float(p[bone][i] + ep[i]), 3) for i in range(3)), interp))
            scl.append((t, tuple(round(float(v), 3) for v in s[bone]), interp))
        ch = {}
        if any(any(abs(v) > 0.05 for v in k[1]) for k in rot):
            ch["rotation"] = rot
        if any(any(abs(v) > 1e-3 for v in k[1]) for k in pos):
            ch["position"] = pos
        if any(any(abs(v - 1) > 1e-3 for v in k[1]) for k in scl):
            ch["scale"] = scl
        if ch:
            bones[bone] = ch
    if turns:
        # the whirl turns about the seal's normal (z), the twister's bands about the funnel's axis (y), opposite ways
        bones.setdefault("arms", {})["rotation"] = spin_track(length, turns, 1, axis=2)
        for k in range(4):
            bones.setdefault(f"ribbon{k}", {})["rotation"] = spin_track(length, turns, -1, axis=1)
    return bones


def animations(model_id, clip_set):
    anims = []
    for clip, (length, loop, bones) in clip_set.items():
        animators = {}
        for bone, channels in bones.items():
            frames = []
            for ch, keys in channels.items():
                for t, v, interp in keys:
                    if ch == "rotation":
                        point = {"x": round(-v[0], 2), "y": round(-v[1], 2), "z": round(v[2], 2)}
                    elif ch == "position":
                        point = {"x": round(-v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    else:
                        point = {"x": round(v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    frames.append({"channel": ch, "data_points": [point], "time": round(t, 3), "color": -1,
                                   "interpolation": interp, "uuid": _uuid(f"{model_id}/{clip}/{bone}/{ch}/{t}")})
            animators[_uuid(f"{model_id}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{model_id}/anim/{clip}"), "name": clip, "loop": loop, "override": clip in OVERRIDE,
                      "length": length, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                      "start_delay": "", "loop_delay": "", "animators": animators})
    return anims


def floor_check(clip_set, model):
    """The lowest point of the model at every 1/20 s of every clip (model units; the floor is 0)."""
    from bosses.volley_crone_s7 import matrices
    from bosskit.bbmodel import pivot_matrix
    worst = {}
    for name, (length, _, bones) in clip_set.items():
        low = 1e9
        for t in np.arange(0, length + 1e-6, 0.05):
            mats = matrices(model, bones, t)
            for c in model.cubes:
                m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
                lo, hi = np.array(c.frm), np.array(c.to)
                pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
                low = min(low, float((m @ pts)[1].min()))
        worst[name] = round(low, 1)
    return worst


def main():
    (OUT / "gifs").mkdir(parents=True, exist_ok=True)
    for old in (OUT / "gifs").glob("*.gif"):
        old.unlink()
    defs = clips()
    clip_set = {n: (c[0], c[1], tracks(c, n)) for n, c in defs.items()}
    name = s4.NAME
    rig = json.loads((S6 / f"{name}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = animations(name, clip_set)
    p = OUT / f"{name}.bbmodel"
    p.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    for folder in (s3.SERVER_MODELS, s3.TEST_MODELS):
        if folder.is_dir():
            shutil.copyfile(p, folder / p.name)
    model = rest()
    s4.zone_materials(model)
    img = a7.previews(model, clip_set, "", {"yaw": -30, "pitch": 10, "scale": 2.1}, CONTACT,
                      "Tempest: key frames (session 7); the GIFs show the motion")
    img.save(OUT / "keyframes.png")
    floors = floor_check(clip_set, model)
    summary = {n: {"length": c[0], "loop": c[1], "lowest_y": floors[n]} for n, c in defs.items()}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
