"""The Archevoker redesign, session 7: animation (plan: docs/art/bosses/archevoker/overhaul/plan.md).

Each clip of the priest is a few whole poses at key times, built with session 2's pose code (archevoker_s2.pose);
the keyframes are each bone's turn away from the rest pose, plus position keys for the priest rising off the seat and
the whole model sinking, and the ring's turn. Movement over the ground stays with the server (the throne glides with
the carrier), so no clip travels. The casting hands have their own clips on their own models.

Timed to Archevoker.java (the pattern's 20-tick warning, the burst's warning, which session 8 sets to 15 ticks) and to
the hands mechanic agreed in the plan:
  priest
  idle         8.0 s loop   breathing, a slow look round; at 3.5 s he uncrosses his legs, at 7 s crosses them again;
                            the ring turns a full circle
  idle_fold    4.0 s once   now and then while he waits: he folds his arms, holds, and unfolds them
  walk         2.0 s loop   gliding: the throne bobs and dips forward (the carrier moves him)
  spawn        2.6 s once   rising out of the circle, the ring spinning up
  line         1.6 s once   the line pattern: his right arm lifts and thrusts; contact at 1.0 s (the 20-tick warning)
  ring         1.6 s once   the ring pattern: an overhead sweep; contact at 1.0 s
  spiral       1.6 s once   the spiral pattern: his left wrist twirls; contact at 1.0 s
  burst        1.2 s once   the fang burst: both arms flung down; contact at 0.75 s (15 ticks)
  hand_lost    1.0 s once   a casting hand dies: he recoils and turns to it
  caught       2.6 s once   cheating death: he slumps forward into the hands (0.5 s), hangs, and sits back up
  rise         2.0 s hold   both hands dead: he stands up off the throne, arms spreading
  risen_idle   3.0 s loop   standing in the air before the throne, breathing, arms half spread
  risen_cast   1.6 s once   casting for himself, both arms thrust out; contact at 1.0 s
  flinch       0.4 s once   hit: a jolt (layered over anything)
  death        3.0 s hold   a gasp, then he slumps sideways as the throne lists and sinks
  each casting hand
  idle         3.0 s loop   bobbing, the spell circle turning
  tell         1.0 s hold   drawing its pattern: pressing forward, the circle spinning fast (its vulnerable window)
  hit          0.3 s once   a jolt
  spawn        1.0 s once   rising into place
  death        1.5 s hold   it sags and drops; session 8 shows the eyelid as it starts

Run from the repository root: python tools/art/bosses/archevoker_s7.py (after archevoker_s6.py)
"""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import _uuid, pivot_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_s2 as s2, archevoker_s3 as s3, archevoker_s4 as s4, archevoker_s6 as s6  # noqa: E402
from bosses import volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s7_animation"
S6 = ROOT / "docs/art/bosses/archevoker/overhaul/s6_variants"
P = {k: v[1] for k, v in s2.POSES.items()}
OVERRIDE = ("idle_fold", "line", "ring", "spiral", "burst", "hand_lost", "caught", "rise", "risen_cast", "flinch")
CONTACT = {"line": 1.0, "ring": 1.0, "spiral": 1.0, "burst": 0.75, "risen_cast": 1.0}
HAND_OVERRIDE = ("tell", "hit")
CIRCLE_CENTRE = (0.0, 27.0, 4.0)                  # the spell circle turns about its own middle


def spec(start, **changes):
    out = {k: v for k, v in start.items() if k != "hands"}
    out.update(changes)
    return out


def arms(right, left=None):
    return {"right": right} if left is None else {"right": right, "left": left}


REST = P["rest"]
DOWN, FWD, UP = s2.DOWN, s2.FWD, s2.UP


def clips():
    rest = spec(REST, ring=0)
    breathe = lambda r, **k: spec(rest, torso=(-6.5, 0, 0), head=(-2, 0, 0), ring=r, **k)   # noqa: E731
    look = lambda r, yaw: spec(rest, head=(1, yaw, 0), torso=(-5, yaw * 0.25, 0), ring=r)   # noqa: E731
    spread = lambda r, **k: spec(rest, legs="spread", ring=r, **k)   # noqa: E731
    fold = spec(P["fold"], ring=0)
    fold_b = spec(fold, torso=(-6.5, 0, 0), head=(-2, 0, 0))
    glide = lambda d, r: spec(rest, base=(1.5 * d, 0), torso=(-7, 0, 0), ring=r)   # noqa: E731
    rise_from = lambda dy, r: spec(rest, base=(dy, 0), head=(6, 0, 0), ring=r)   # noqa: E731

    def cast(key, lift, r_end=60):
        p = spec(P[key], ring=0)
        return [(0, spec(rest, ring=0)), (0.3, spec(lift, ring=10)), (0.75, spec(p, ring=35)), (1.0, spec(p, ring=50)),
                (1.15, spec(p, ring=56)), (1.6, spec(rest, ring=r_end))]

    line_lift = spec(rest, legs="spread", torso=(-7, -4, 0), arm=arms(((26, 70, 6), (30, 80, -6), FWD)))
    ring_lift = spec(rest, legs="spread", torso=(-8, -8, 0), arm=arms(((28, 82, 8), (30, 98, 4), DOWN),
                                                                    ((-24, 61, 14), (-25, 59.5, -3), DOWN)))
    spiral_lift = spec(rest, torso=(-8, 6, 0), arm=arms(((24, 61, 14), (25, 59.5, -3), DOWN),
                                                       ((-26, 80, 4), (-24, 94, -6), FWD)))
    burst = spec(P["burst"], ring=0)
    burst_up = spec(rest, legs="spread", torso=(-2, 0, 0), head=(8, 0, 0),
                    arm=arms(((28, 84, 6), (34, 98, -2), FWD)), ring=10)
    recoil = spec(rest, torso=(4, 14, 0), head=(4, 34, 4), legs="spread",
                  arm=arms(((24, 61, 14), (25, 59.5, -3), DOWN), ((-26, 70, 2), (-30, 80, -12), FWD)))
    caught = spec(P["caught"], ring=0)
    caught_low = spec(caught, torso=(-28, 0, 0), head=(-34, 0, 10))
    risen = spec(P["risen"], ring=0)
    half = spec(risen, arm=arms(((28, 72, 6), (38, 74, -8), FWD)))
    risen_b = spec(half, torso=(2.5, 0, 0), head=(4, 0, 0))
    push = spec(rest, legs="spread", torso=(-16, 0, 0), head=(-6, 0, 0), body=(0, 4, -8),
                arm=arms(((24, 61, 14), (25, 59.5, -3), DOWN)))
    thrust = spec(risen, arm=arms(((24, 80, -10), (26, 82, -28), FWD)))
    gather = spec(risen, arm=arms(((26, 66, 8), (24, 74, -2), UP)), torso=(6, 0, 0))
    flinch = spec(rest, torso=(-2, 0, 4), head=(10, 6, 6))
    gasp = spec(rest, head=(14, 0, 0), torso=(2, 0, 0), legs="spread")
    sag = spec(rest, legs="spread", torso=(-8, 0, 8), head=(-10, 4, 12), base=(-2, 4),
               arm=arms(((20, 60, 12), (21, 46, 6), (-1, 0, 0))))
    death = spec(P["death"], ring=0)
    return {
        "idle": (8.0, "loop", [(0, rest), (1.5, breathe(45)), (3.0, rest | {"ring": 90}),
                               (3.5, spread(105)), (4.5, spread(135, torso=(-6.5, 0, 0))),
                               (5.5, look(165, -18) | {"legs": "spread"}), (6.5, spread(195)),
                               (7.0, spread(210)), (7.5, rest | {"ring": 225}), (8.0, rest | {"ring": 240})]),
        "idle_fold": (4.0, "once", [(0, rest), (0.6, fold | {"ring": 15}), (2.0, fold_b | {"ring": 50}),
                                    (3.4, fold | {"ring": 85}), (4.0, rest | {"ring": 100})]),
        "walk": (2.0, "loop", [(0, glide(0, 0)), (0.5, glide(1, 15)), (1.0, glide(0, 30)), (1.5, glide(-1, 45)),
                               (2.0, glide(0, 60))]),
        "spawn": (2.6, "once", [(0, rise_from(-110, 0)), (0.9, rise_from(-50, 180)), (1.7, rise_from(-8, 330)),
                                (2.2, spec(rest, base=(3, 0), ring=390)), (2.6, spec(rest, ring=420))]),
        "line": (1.6, "once", cast("line", line_lift)),
        "ring": (1.6, "once", cast("ring", ring_lift)),
        "spiral": (1.6, "once", cast("spiral", spiral_lift)),
        "burst": (1.2, "once", [(0, rest), (0.4, burst_up), (0.75, burst), (0.9, spec(burst, torso=(-8, 0, 0))),
                                (1.2, spec(rest, ring=30))]),
        "hand_lost": (1.0, "once", [(0, rest), (0.15, recoil), (0.6, recoil), (1.0, rest)]),
        "caught": (2.6, "once", [(0, rest), (0.5, caught), (0.8, caught_low), (1.6, caught), (2.1, spec(push, ring=0)),
                                 (2.6, rest)]),
        "rise": (2.0, "hold", [(0, rest), (0.5, push), (1.1, spec(risen, arm=arms(((24, 62, 10), (26, 52, 0), DOWN)))),
                               (1.6, risen), (2.0, half)]),
        "risen_idle": (3.0, "loop", [(0, half), (1.5, risen_b | {"ring": 45}), (3.0, half | {"ring": 90})]),
        "risen_cast": (1.6, "once", [(0, half), (0.4, gather), (0.75, thrust), (1.0, thrust), (1.15, thrust),
                                     (1.6, half)]),
        "flinch": (0.4, "once", [(0, rest), (0.1, flinch), (0.4, rest)]),
        "death": (3.0, "hold", [(0, rest), (0.5, gasp), (1.4, sag), (2.2, death), (3.0, death)]),
    }


# ---- tracks --------------------------------------------------------------------------------------------------------

_POSED = {}


def posed(sp):
    key = json.dumps(sp, sort_keys=True, default=str)
    if key not in _POSED:
        m = s2.rig("p")
        s2.pose(m, {k: v for k, v in sp.items() if k not in ("body", "base", "ring")})
        rot = {g.name: list(g.rotation) for g in m.groups}
        if sp.get("base"):
            rot["base"] = [0.0, 0.0, float(sp["base"][1])]
        _POSED[key] = rot
    return _POSED[key]


def wrap(d):
    return (d + 180) % 360 - 180


def tracks(clip, rest_rot):
    """Keyframes per bone: rotation deltas from rest, the priest's and the model's position offsets, the ring's turn."""
    length, loop, keys = clip
    poses = [(t, sp, posed(sp)) for t, sp in keys]
    moving = set()
    for _, _, rot in poses:
        for name, r in rot.items():
            if name != "ring" and any(abs(wrap(r[i] - rest_rot[name][i])) > 0.05 for i in range(3)):
                moving.add(name)
    bones = {}
    for name in sorted(moving):
        out, prev = [], None
        for t, _, rot in poses:
            d = [wrap(rot[name][i] - rest_rot[name][i]) for i in range(3)]
            if prev is not None:                      # keep the track continuous: never the long way round
                d = [d[i] + 360 * round((prev[i] - d[i]) / 360) for i in range(3)]
            prev = d
            out.append((t, tuple(round(v, 2) for v in d), "catmullrom"))
        bones[name] = {"rotation": out}
    turns = [(t, (0.0, 0.0, -float(sp.get("ring", 0))), "linear") for t, sp, _ in poses]
    if any(abs(k[1][2]) > 1e-6 for k in turns):
        bones["ring"] = {"rotation": turns}

    def channel(bone, fn):
        keys_ = [(t, tuple(round(v, 3) for v in fn(sp)), "catmullrom") for t, sp, _ in poses]
        if any(any(abs(v) > 1e-6 for v in k[1]) for k in keys_):
            bones.setdefault(bone, {})["position"] = keys_

    channel("body", lambda sp: tuple(float(v) for v in sp.get("body", (0, 0, 0))))
    channel("base", lambda sp: (0.0, float(sp.get("base", (0, 0))[0]), 0.0))
    return bones


def hand_clips():
    c = 0.0
    idle = [(t, {"hand": ((-2 + 4 * (t in (1.5,)), 0, 0), (0, 1.5 * math.sin(t / 3 * 2 * math.pi), 0)),
                 "glow_circle": ((0, 0, -120 * t), None)}) for t in (0, 0.75, 1.5, 2.25, 3.0)]
    tell = [(0, {"hand": ((0, 0, 0), (0, 0, 0)), "glow_circle": ((0, 0, 0), None)}),
            (0.3, {"hand": ((-20, 0, 0), (0, -2, -2)), "glow_circle": ((0, 0, -180), None)}),
            (0.6, {"hand": ((-35, 0, 0), (0, -3, -4)), "glow_circle": ((0, 0, -420), None)}),
            (1.0, {"hand": ((-35, 0, 0), (0, -3, -4)), "glow_circle": ((0, 0, -720), None)})]
    hit = [(0, {"hand": ((0, 0, 0), (0, 0, 0))}), (0.08, {"hand": ((12, 0, 10), (0, 1, 2))}),
           (0.3, {"hand": ((0, 0, 0), (0, 0, 0))})]
    spawn = [(0, {"hand": ((30, 0, 0), (0, -24, 0)), "glow_circle": ((0, 0, 0), None)}),
             (0.7, {"hand": ((-6, 0, 0), (0, 2, 0)), "glow_circle": ((0, 0, -300), None)}),
             (1.0, {"hand": ((0, 0, 0), (0, 0, 0)), "glow_circle": ((0, 0, -360), None)})]
    death = [(0, {"hand": ((0, 0, 0), (0, 0, 0))}), (0.2, {"hand": ((14, 0, 12), (0, 2, 0))}),
             (0.9, {"hand": ((70, 0, 30), (0, -10, 0))}), (1.5, {"hand": ((88, 0, 40), (0, -22, 0))})]
    _ = c
    return {"idle": (3.0, "loop", idle), "tell": (1.0, "hold", tell), "hit": (0.3, "once", hit),
            "spawn": (1.0, "once", spawn), "death": (1.5, "hold", death)}


def hand_tracks(keys):
    bones = {}
    for t, d in keys:
        for bone, (rot, pos) in d.items():
            interp = "linear" if bone == "glow_circle" else "catmullrom"
            bones.setdefault(bone, {}).setdefault("rotation", []).append((t, tuple(map(float, rot)), interp))
            if pos is not None:
                bones[bone].setdefault("position", []).append((t, tuple(map(float, pos)), "catmullrom"))
    return bones


def blockbench_animations(model_id, clip_set, override):
    anims = []
    for clip, (length, loop, bones) in clip_set.items():
        animators = {}
        for bone, channels in bones.items():
            frames = []
            for ch, keys in channels.items():
                for t, v, interp in keys:
                    if ch == "rotation":
                        point = {"x": round(-v[0], 2), "y": round(-v[1], 2), "z": round(v[2], 2)}
                    else:
                        point = {"x": round(-v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    frames.append({"channel": ch, "data_points": [point], "time": round(t, 3), "color": -1,
                                   "interpolation": interp, "uuid": _uuid(f"{model_id}/{clip}/{bone}/{ch}/{t}")})
            animators[_uuid(f"{model_id}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{model_id}/anim/{clip}"), "name": clip, "loop": loop, "override": clip in override,
                      "length": length, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                      "start_delay": "", "loop_delay": "", "animators": animators})
    return anims


def set_origin(bb, name, origin):
    """Moves a bone's pivot in a finished .bbmodel (its cubes don't move: they're stored in model space)."""
    def walk(nodes):
        for n in nodes:
            if isinstance(n, dict):
                if n.get("name") == name:
                    n["origin"] = list(origin)
                walk(n.get("children", []))
    for g in bb["groups"]:
        if g["name"] == name:
            g["origin"] = list(origin)
    walk(bb["outliner"])


# ---- preview: the rest model in its zone colours, posed per frame ----------------------------------------------------

def frame(model, bones, t, yaw=-34, pitch=12, size=(420, 440), scale=2.6, floor=0.92, hide=()):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    polys = []
    for c in model.cubes:
        if c.group.name in hide or min(np.array(c.to) - np.array(c.frm)) < 0.01:
            continue
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        world = (m @ pts)[:3]
        v = (view @ world).T
        wt = world.T
        glow = c.mat in s4.GLOWING
        for face, idx in v7.QUADS.items():
            q = wt[list(idx)]
            n = np.cross(q[1] - q[0], q[2] - q[0])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n = n / nn
            if np.dot(q.mean(0) - wt.mean(0), n) < 0:
                n = -n
            base = np.array(s4.ZONES.get(c.mat, (128, 128, 128)), float)
            light = 1.0 if glow else 0.55 + 0.45 * max(0.0, n[1] * 0.7 + 0.3 * abs(n[0]) + 0.2 * -n[2])
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * floor - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * floor + 1, size[0], size[1]), fill=(30, 28, 34))
    for _, pts, col in sorted(polys, key=lambda p: -p[0]):
        dr.polygon(pts, fill=col)
    return img


def previews(model, clip_set, prefix, kw, contact, label):
    stills = []
    for name, (length, loop, bones) in clip_set.items():
        frames = [frame(model, bones, t, **kw) for t in np.arange(0, length + 1e-6, 1 / 15)]
        frames[0].save(OUT / "gifs" / f"{prefix}{name}.gif", save_all=True, append_images=frames[1:], duration=66,
                       loop=0)
        if name in contact:
            r = contact[name]
            picks = sorted({0.0, round(r * 0.4, 3), round(r * 0.75, 3), r, length})
        else:
            picks = [round(length * f, 3) for f in (0, 0.25, 0.5, 0.75, 1.0)]
        small = dict(kw, size=(260, 270), scale=kw.get("scale", 2.6) * 0.62)
        stills.append((name, [(t, frame(model, bones, t, **small)) for t in picks[:5]]))
    tw, th, pad, top, left = 260, 270, 8, 54, 110
    img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), label, font=sheet._font(24), fill=sheet.INK)
    for r_, (name, row) in enumerate(stills):
        y = top + r_ * (th + 26 + pad)
        dr.text((pad, y + th // 2 - 10), name, font=sheet._font(17), fill=sheet.INK)
        for c, (t, im) in enumerate(row):
            img.paste(im, (left + c * (tw + pad), y))
            mark = " contact" if name in contact and abs(t - contact[name]) < 1e-6 else ""
            dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s{mark}", font=sheet._font(15), fill=sheet.DIM)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    (OUT / "gifs").mkdir(exist_ok=True)
    # the priest
    rest = s2.rig("rest")
    s2.pose(rest, REST)
    rest_rot = {g.name: list(g.rotation) for g in rest.groups}
    clip_set = {name: (c[0], c[1], tracks(c, rest_rot)) for name, c in clips().items()}
    rig = json.loads((S6 / f"{s3.MODEL_ID}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = blockbench_animations(s3.MODEL_ID, clip_set, OVERRIDE)
    paths = [OUT / f"{s3.MODEL_ID}.bbmodel"]
    paths[0].write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    model = s3.build("rest")
    sheet_a = previews(model, clip_set, "", {}, CONTACT, "The Archevoker - key frames (session 7); the GIFs show the motion")
    sheet_a.save(OUT / "keyframes.png")
    # the casting hands
    hand_set = {name: (c[0], c[1], hand_tracks(c[2])) for name, c in hand_clips().items()}
    for colour in ("cyan", "purple"):
        name = f"occultech_archevoker_hand_{colour}_rig"
        hb = json.loads((S6 / f"{name}.bbmodel").read_text(encoding="utf-8"))
        set_origin(hb, "glow_circle", CIRCLE_CENTRE)
        hb["animations"] = blockbench_animations(name, hand_set, HAND_OVERRIDE)
        p = OUT / f"{name}.bbmodel"
        p.write_text(json.dumps(hb, indent=1) + "\n", encoding="utf-8")
        paths.append(p)
    hm = s6.hand_with_lid("cyan")
    next(g for g in hm.groups if g.name == "glow_circle").origin = list(CIRCLE_CENTRE)
    sheet_b = previews(hm, hand_set, "hand_", {"yaw": -20, "pitch": 6, "scale": 7.5, "floor": 0.98,
                                                "hide": ("eyelid",)}, {}, "The casting hand - key frames (session 7)")
    sheet_b.save(OUT / "hand_keyframes.png")
    if s3.SERVER_MODELS.is_dir():
        for p in paths:
            shutil.copyfile(p, s3.SERVER_MODELS / p.name)
    summary = {n: {"length": v[0], "loop": v[1], "bones": len(v[2])} for n, v in clip_set.items()}
    summary_h = {n: {"length": v[0], "loop": v[1]} for n, v in hand_set.items()}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "priest": summary, "hand": summary_h},
                                               indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
