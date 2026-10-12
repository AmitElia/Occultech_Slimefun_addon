"""The Unbound redesign, session 7: animation (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

Each clip is a few whole poses at key times, built with session 2's pose code (unbound_s2.pose), so at every key the
cleaver's edge faces where the swing carries it and the chains hang straight; the keyframes are each bone's turn
away from the rest pose. Kneeling sinks the hips (a position key); a dropped cleaver is set on the floor (another).

  idle     3.0 s loop   heavy breathing: the chest rises and falls, the shoulders roll, the chains and the band's
                        tails sway
  walk     1.6 s loop   a heavy stride, the hips bobbing, the free arm swinging, the cleaver dragging behind
  run      1.0 s loop   enraged (below 1/3 health): head down, horns first, a long stride, arms back
  spawn    2.0 s once   rising from a kneel to a roar (the ritual arrival)
  swing    0.8 s once   the axe swing (melee): a short chop, contact at 0.35 s
  cleave   2.2 s once   the cleave: wound up over his shoulder through the 1.25 s warning (trembling), then the
                        sweep, contact at 1.3 s, a heavy recovery
  call     1.8 s once   calling the thralls: he crouches, then roars, arms spread
  devour   1.6 s once   seizing a thrall and gorging, fist to his mouth (the bite at 0.8 s)
  sated    3.0 s once   the 3 s opening: down on one knee at 0.4 s, panting, back up at the end
  enrage   1.2 s once   a stage change: a short roar as the fire flares
  flinch   0.4 s once   hit: a jolt (layered over whatever he's doing)
  death    2.6 s hold   to his knees, then folding forward, the cleaver dropped

Run from the repository root: python tools/art/bosses/unbound_s7.py
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
from bosses import unbound_s2 as s2, unbound_s3 as s3, unbound_s4 as s4, unbound_s5 as s5, volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s7_animation"
RIG = ROOT / "docs/art/bosses/the_unbound/overhaul/s5_paint" / f"{s3.MODEL_ID}.bbmodel"
H = s2.H
P = {k: v[1] for k, v in s2.POSES.items()}
REST = P["idle"]
PARTIAL = ("swing", "cleave", "call", "devour", "enrage", "flinch")
RELEASE = {"swing": 0.35, "cleave": 1.3, "devour": 0.8}       # seconds into the clip: contact, the bite


def spec(base, **changes):
    """A pose spec: a copy of base with some fields replaced (arms/legs merged per side, extras added)."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in changes.items():
        if k in ("arms", "legs"):
            out[k] = dict(out.get(k, {} if k == "arms" else s2.REST_LEGS), **v)
        elif k == "extra":
            merged = dict(out.get("extra", {}))
            for bone, d in v.items():
                old = merged.get(bone, (0, 0, 0))
                merged[bone] = tuple(old[i] + d[i] for i in range(3))
            out[k] = merged
        else:
            out[k] = v
    return out


ARMS = REST["arms"]
SWAY = lambda a: {"chain_wrist_left": (a, 0, a * 0.6), "chain_wrist_right": (-a, 0, -a * 0.6),   # noqa: E731
                  "chain_ankle_left": (0, a * 0.5, 0), "chain_ankle_right": (0, -a * 0.5, 0),
                  "band_tails": (a * 1.5, 0, a)}


def clips():
    breathe_in = spec(REST, torso=2, head=-1, arms={"left": ((-H, 0, -8), (4, 0, -3)), "right": ((-H - 14, 0, 8), (-6, 0, 3))},
                      extra=SWAY(4))
    stride = lambda f, lean=0, reach=22, arm=14: spec(REST, torso=lean, head=-lean * 0.8, legs={   # noqa: E731
        "left": ((reach * f, 0, 3), (-10 if f > 0 else 26, 0, 0)), "right": ((-reach * f, 0, -3), (26 if f > 0 else -10, 0, 0))},
        arms={"left": ((-H - arm * f, 0, -6), (4 + 6 * max(0, f), 0, -3)), "right": ((-H - 14 + 4 * f, 0, 6), (-6, 0, 3))},
        extra=dict(SWAY(5 * f), torso=(0, 5 * f, 0)))
    run = lambda f: spec(stride(f, lean=-16, reach=32, arm=0), head=16, arms={   # noqa: E731
        "left": ((-24 - 10 * f, 0, -10), (-8, 0, 0)), "right": ((-20 + 6 * f, 0, 8), (-4, 0, 0))})
    kneel = spec(P["sated"], torso=-30, head=-20, cleaver="flat")
    windup, sweep, call = P["windup"], P["sweep"], P["call"]
    chop_up = spec(REST, torso=4, head=-2, arms={"right": ((70, 0, 30), (70, 0, -12))}, cleaver=(0.25, 0.55, 0.8))
    chop_down = spec(REST, torso=-8, head=6, arms={"right": ((44, 0, 10), (12, 0, 0))}, cleaver=(0.1, -0.5, -0.86))
    crouch = spec(REST, torso=-18, head=-8, arms={"left": ((-H + 10, 0, -4), (14, 0, -3)), "right": ((-H - 4, 0, 4), (6, 0, 3))},
                  legs={"left": ((14, 0, 3), (-20, 0, 0)), "right": ((10, 0, -3), (-16, 0, 0))})
    grab = spec(REST, torso=-24, head=-2, arms={"left": ((44, 0, -10), (22, 0, 0))})
    pant = lambda d: spec(P["sated"], torso=P["sated"]["torso"] + d, head=P["sated"]["head"] - d * 0.5)   # noqa: E731
    roar = spec(call, head=30)
    out = {
        "idle": (3.0, "loop", [(0, REST), (1.5, breathe_in), (3.0, REST)]),
        "walk": (1.6, "loop", [(0, stride(1)), (0.4, spec(stride(0), hips=-0.8)), (0.8, stride(-1)),
                               (1.2, spec(stride(0), hips=-0.8)), (1.6, stride(1))]),
        "run": (1.0, "loop", [(0, run(1)), (0.25, spec(run(0), hips=-1.2)), (0.5, run(-1)),
                              (0.75, spec(run(0), hips=-1.2)), (1.0, run(1))]),
        "spawn": (2.0, "once", [(0, kneel), (0.9, spec(crouch, drop=3, cleaver="flat")), (1.4, roar), (2.0, REST)]),
        "swing": (0.8, "once", [(0, REST), (0.2, chop_up), (0.35, chop_down), (0.8, REST)]),
        "cleave": (2.2, "once", [(0, REST), (0.6, windup), (0.9, spec(windup, torso=windup["torso"] + 2)),
                                 (1.1, spec(windup, arms={"right": ((106, 0, 40), (130, 0, -30))})),
                                 (1.3, sweep), (1.6, spec(sweep, torso=sweep["torso"] - 4)), (2.2, REST)]),
        "call": (1.8, "once", [(0, REST), (0.4, crouch), (0.9, call), (1.4, roar), (1.8, REST)]),
        "devour": (1.6, "once", [(0, REST), (0.4, grab), (0.8, P["devour"]),
                                 (1.0, spec(P["devour"], head=P["devour"]["head"] - 12)), (1.2, P["devour"]), (1.6, REST)]),
        "sated": (3.0, "once", [(0, REST), (0.4, P["sated"]), (0.9, pant(4)), (1.4, pant(-3)), (1.9, pant(4)),
                                (2.4, pant(-3)), (3.0, REST)]),
        "enrage": (1.2, "once", [(0, REST), (0.3, crouch), (0.7, spec(roar, arms={
            "left": ((-H + 6, 0, -30), (0, 0, -10)), "right": ((-H + 6, 0, 30), (0, 0, 10))})), (1.2, REST)]),
        "flinch": (0.4, "once", [(0, REST), (0.1, spec(REST, torso=8, head=10, arms={"left": ((-H + 30, 0, -14), (30, 0, -3))})),
                                 (0.4, REST)]),
        "death": (2.6, "hold", [(0, REST), (0.6, spec(P["death"], torso=-10, head=0)), (1.4, P["death"]),
                                (2.0, spec(P["death"], torso=-62, head=-26)), (2.6, spec(P["death"], torso=-62, head=-26))]),
    }
    return out


def posed(sp):
    m = s2.rig("p")
    s2.pose(m, sp)
    return m


def wrap(d):
    return (d + 180) % 360 - 180


def tracks(clip, k, rest_rot):
    """Keyframes per bone (rotation deltas from rest, position offsets) for one clip's poses."""
    length, loop, keys = clip
    poses = [(t, sp, posed(sp)) for t, sp in keys]
    moving = set()
    for _, _, m in poses:
        for g in m.groups:
            if any(abs(wrap(g.rotation[i] - rest_rot[g.name][i])) > 0.05 for i in range(3)):
                moving.add(g.name)
    bones = {}
    for name in sorted(moving):
        rot = []
        for t, _, m in poses:
            g = s2.group(m, name)
            rot.append((t, tuple(round(wrap(g.rotation[i] - rest_rot[name][i]), 2) for i in range(3)), "catmullrom"))
        bones[name] = {"rotation": rot}
    hips = [(t, (0.0, round((-sp.get("drop", 0) + sp.get("hips", 0)) * k, 3), 0.0), "catmullrom") for t, sp, _ in poses]
    if any(abs(v[1]) > 1e-6 for _, v, _ in hips):
        bones.setdefault("hips", {})["position"] = hips
    cl = [(t, (0.0, round(-m.flat_low * k, 3), 0.0), "catmullrom") for t, _, m in poses]
    if any(abs(v[1]) > 1e-6 for _, v, _ in cl):
        bones.setdefault("cleaver", {})["position"] = cl
    return bones


def blockbench_animations(model_id, clip_set):
    anims = []
    for clip, (length, loop, bones) in clip_set.items():
        animators = {}
        for bone, channels in bones.items():
            frames = []
            for channel, keys in channels.items():
                for t, v, interp in keys:
                    if channel == "rotation":
                        point = {"x": round(-v[0], 2), "y": round(-v[1], 2), "z": round(v[2], 2)}
                    else:
                        point = {"x": round(-v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    frames.append({"channel": channel, "data_points": [point], "time": round(t, 3), "color": -1,
                                   "interpolation": interp, "uuid": _uuid(f"{model_id}/{clip}/{bone}/{channel}/{t}")})
            animators[_uuid(f"{model_id}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{model_id}/anim/{clip}"), "name": clip, "loop": loop, "override": clip in PARTIAL,
                      "length": length, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                      "start_delay": "", "loop_delay": "", "animators": animators})
    return anims


# ---- preview: the rest model in its painted zone colours, posed per frame --------------------------------------------

def frame(model, bones, t, yaw=-40, pitch=12, size=(380, 420), scale=3.6):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    polys = []
    for c in model.cubes:
        if s5.hidden(c) or min(np.array(c.to) - np.array(c.frm)) < 0.01:
            continue
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        v = (view @ (m @ pts)[:3]).T
        zone = s4.zone_for(c)
        glow = zone.startswith(s5.GLOWING)
        ramp, shade = s5.ZONE[zone]
        base = np.array(s5.RAMP[ramp][min(shade, len(s5.RAMP[ramp]) - 1)], float)
        if zone.startswith("fire"):
            base = base * np.array((255, 150, 60)) / 255
        for face, idx in v7.QUADS.items():
            light = 1.0 if glow else v7.SHADE[face]
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * 0.88 - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * 0.88 + 1, size[0], size[1]), fill=(30, 28, 34))
    for _, pts, col in sorted(polys, key=lambda p: -p[0]):
        dr.polygon(pts, fill=col)
    return img


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    (OUT / "gifs").mkdir(parents=True)
    k = s3.scale_factor()
    rest = s2.build("rest")
    rest_rot = {g.name: list(g.rotation) for g in rest.groups}
    clip_set = {name: (c[0], c[1], tracks(c, k, rest_rot)) for name, c in clips().items()}
    # the preview model: the rest pose at the shipped size (positions in the tracks are already scaled)
    model = s2.build("preview")
    s2.finish(model, k)
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["animations"] = blockbench_animations(s3.MODEL_ID, clip_set)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    stills = []
    for name, (length, loop, bones) in clip_set.items():
        frames = [frame(model, bones, t) for t in np.arange(0, length + 1e-6, 1 / 15)]
        frames[0].save(OUT / "gifs" / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)
        if name in RELEASE:
            r = RELEASE[name]
            picks = [0, r * 0.5, r, min(length, r + 0.25), length]
        else:
            picks = [length * f for f in (0, 0.25, 0.5, 0.75, 1.0)]
        stills.append((name, [(t, frame(model, bones, t, size=(250, 270), scale=2.4)) for t in picks]))
    tw, th, pad, top, left = 250, 270, 8, 54, 100
    img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Unbound - key frames (session 7); the GIFs show the motion", font=sheet._font(24), fill=sheet.INK)
    for r_, (name, row) in enumerate(stills):
        y = top + r_ * (th + 26 + pad)
        dr.text((pad, y + th // 2 - 10), name, font=sheet._font(19), fill=sheet.INK)
        for c, (t, im) in enumerate(row):
            img.paste(im, (left + c * (tw + pad), y))
            mark = " contact" if name in RELEASE and abs(t - RELEASE[name]) < 1e-6 else ""
            dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s{mark}", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT / "keyframes.png")
    summary = {n: {"length": v[0], "loop": v[1], "bones": len(v[2])} for n, v in clip_set.items()}
    (OUT / "clips.json").write_text(json.dumps({"release_seconds": RELEASE, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
