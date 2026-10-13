"""The Night Matriarch redesign, session 7: animation.

Each clip is a few whole poses at key times, built from session 2's pose fields (body pitch/yaw/roll, head, tail,
both wings at shoulder and elbow, the warden horns); the keyframes are each bone's turn away from the rest pose, and
the body bobs with a position key on the wingbeats. The wings beat with the elbow lagging the shoulder (the tip
follows through), and the warden horns flick through every clip like an axolotl's gills. Her fight's moments
(NightMatriarch.java) set the timings:

  idle      2.4 s loop   hovering: slow, deep wingbeats, the body bobbing, the horns waving
  walk      3.2 s loop   flying: a long glide, banking side to side, then one great beat
  spawn     2.6 s once   the ritual arrival: up from the ground in two heavy beats into the glide
  tell      1.5 s hold   the dive's warning (30 ticks): she rears, wings raised high, head down at her target, the
                         horns flared, trembling
  dive      2.0 s hold   the dive (up to 40 ticks): wings swept back, nose down, the horns streaming
  impact    1.9 s once   the landing: slammed down (0.15 s), sprawled and stunned for the 1.5 s melee window,
                         twitching
  takeoff   0.9 s once   up again: a great downbeat, nose up
  call      1.6 s once   the swarm: head thrown up, wings spread wide, the horns flared (the phantoms join on it)
  bite      0.6 s once   her rake: the head lunges down, contact at 0.3 s
  flinch    0.4 s once   hit: a jolt (layered over whatever she's doing)
  death     3.0 s hold   crashing onto her side, one wing folding over her

Run from the repository root: python tools/art/bosses/matriarch_s7.py
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
from bosses import matriarch_s2 as s2, matriarch_s3 as s3, matriarch_s4 as s4, matriarch_s5 as s5  # noqa: E402
from bosses import volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s7_animation"
RIG = ROOT / "docs/art/bosses/night_matriarch/overhaul/s5_paint" / f"{s3.MODEL_ID}.bbmodel"
PARTIAL = ("bite", "flinch", "call")
RELEASE = {"bite": 0.3, "impact": 0.15}          # seconds into the clip: the bite's contact, the floor


def wings(up, elbow, sweep=0.0, esweep=0.0):
    """Both wings: raised `up` at the shoulder, the tip a further `elbow`, swept back `sweep` and `esweep`."""
    return lambda sx: ((0, -sx * sweep, sx * up), (0, -sx * esweep, sx * elbow))


def horns(fan=0.0, sweep=0.0):
    """The warden horns: fanned up (+) or down (-), swept back (-) or flared forward (+), on top of their rest."""
    return lambda sx: (0, sx * sweep, sx * fan)


def pose(body=(0, 0, 0), head=0, tail=0, wing=None, gill=None, bob=0.0):
    return {"body": body, "head": head, "tail": tail, "wing": wing or wings(4, 2), "gill": gill or horns(), "bob": bob,
            "alt": 0}


P = {k: dict(v[1], bob=0.0, gill=v[1].get("gill", horns())) for k, v in s2.POSES.items()}
UP, DOWN = wings(34, -10, 6, 4), wings(-26, 18, -4, -8)            # the top and bottom of a wingbeat


def clips():
    hover_up = pose(body=(6, 0, 0), head=-4, tail=-6, wing=UP, gill=horns(-6, -10), bob=-2.0)
    hover_mid = pose(body=(3, 0, 0), head=-2, tail=-2, wing=wings(6, 10), gill=horns(4, 4), bob=1.0)
    hover_down = pose(body=(0, 0, 0), head=2, tail=4, wing=DOWN, gill=horns(8, 8), bob=3.0)
    glide = lambda roll, g=0: pose(body=(2, 0, roll), head=-4, tail=-3, wing=wings(8, 4), gill=horns(g, -g), bob=0.0)  # noqa: E731
    tell = P["tell"]
    tremble = dict(tell, body=(tell["body"][0] + 2, 0, 1.5), gill=horns(10, 26))
    dive = P["dive"]
    impact, grounded = P["impact"], P["grounded"]
    twitch = dict(grounded, wing=lambda sx: ((0, 0, -sx * 3), (0, 0, -sx * 14)), head=grounded["head"] + 4,
                  gill=horns(-18, 6))
    takeoff = P["takeoff"]
    call = P["call"]
    death = P["death"]
    bite_down = pose(body=(-14, 0, 0), head=-34, tail=10, wing=wings(18, 6), gill=horns(-10, 20))
    out = {
        "idle": (2.4, "loop", [(0, hover_up), (0.7, hover_mid), (1.2, hover_down), (1.8, hover_mid), (2.4, hover_up)]),
        "walk": (3.2, "loop", [(0, glide(-8)), (1.0, glide(8, 6)), (1.9, glide(-6, -4)), (2.3, hover_up),
                               (2.75, hover_down), (3.2, glide(-8))]),
        "spawn": (2.6, "once", [(0, dict(grounded, gill=horns(-22, 0))), (0.5, takeoff), (0.9, hover_down),
                                (1.3, hover_up), (1.7, hover_down), (2.1, hover_up), (2.6, glide(0))]),
        "tell": (1.5, "hold", [(0, glide(0)), (0.4, tell), (0.7, tremble), (0.95, tell), (1.2, tremble), (1.5, tell)]),
        "dive": (2.0, "hold", [(0, tell), (0.25, dive), (0.9, dict(dive, body=(dive["body"][0], 0, 4), gill=horns(-6, -30))),
                               (1.5, dict(dive, body=(dive["body"][0], 0, -4))), (2.0, dive)]),
        "impact": (1.9, "once", [(0, dive), (0.15, impact), (0.45, grounded), (0.8, twitch), (1.1, grounded),
                                 (1.4, twitch), (1.9, grounded)]),
        "takeoff": (0.9, "once", [(0, grounded), (0.35, takeoff), (0.65, hover_down), (0.9, hover_up)]),
        "call": (1.6, "once", [(0, hover_mid), (0.35, hover_up), (0.8, call), (1.2, dict(call, head=call["head"] + 6,
                                                                                          gill=horns(14, 26))),
                               (1.6, hover_mid)]),
        "bite": (0.6, "once", [(0, hover_mid), (0.15, dict(hover_up, head=10)), (0.3, bite_down), (0.6, hover_mid)]),
        "flinch": (0.4, "once", [(0, hover_mid), (0.1, dict(hover_mid, body=(10, 0, 6), head=12, gill=horns(-14, -14))),
                                 (0.4, hover_mid)]),
        "death": (3.0, "hold", [(0, hover_mid), (0.5, dict(dive, body=(-28, 0, 30))), (1.0, impact), (1.8, death),
                                (2.4, dict(death, head=death["head"] - 8)), (3.0, dict(death, head=death["head"] - 8))]),
    }
    return out


def posed(sp):
    m = s2.build("p")
    s2.pose(m, dict(sp, alt=0))
    return m


def wrap(d):
    return (d + 180) % 360 - 180


def tracks(clip, rest_rot):
    """Keyframes per bone (rotation deltas from rest, kept continuous) and the body's bob, for one clip's poses."""
    length, loop, keys = clip
    poses = [(t, sp, posed(sp)) for t, sp in keys]
    moving = set()
    for _, _, m in poses:
        for g in m.groups:
            if any(abs(wrap(g.rotation[i] - rest_rot[g.name][i])) > 0.05 for i in range(3)):
                moving.add(g.name)
    bones = {}
    for name in sorted(moving):
        rot, prev = [], None
        for t, _, m in poses:
            g = s2.group(m, name)
            d = [wrap(g.rotation[i] - rest_rot[name][i]) for i in range(3)]
            if prev is not None:                      # keep the track continuous: never the long way round
                d = [d[i] + 360 * round((prev[i] - d[i]) / 360) for i in range(3)]
            prev = d
            rot.append((t, tuple(round(v, 2) for v in d), "catmullrom"))
        bones[name] = {"rotation": rot}
    bob = [(t, (0.0, round(sp.get("bob", 0.0), 3), 0.0), "catmullrom") for t, sp, _ in poses]
    if any(abs(v[1]) > 1e-6 for _, v, _ in bob):
        bones.setdefault("body", {})["position"] = bob
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

def frame(model, bones, t, yaw=-35, pitch=22, size=(480, 330), scale=2.0):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    polys = []
    for c in model.cubes:
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        v = (view @ (m @ pts)[:3]).T
        zone = s4.zone_for(c)
        glow = zone in s4.GLOWING
        ramp, shade = s5.ZONE[zone]
        base = np.array(s5.RAMP[ramp][min(shade + (2 if glow else 0), len(s5.RAMP[ramp]) - 1)], float)
        for face, idx in v7.QUADS.items():
            light = 1.0 if glow else v7.SHADE[face]
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * 0.7 - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * 0.7 + 1 + s2.LIFT * 0 + 18, size[0], size[1]), fill=(30, 28, 34))
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
    rest = s2.build("rest")
    rest_rot = {g.name: list(g.rotation) for g in rest.groups}
    clip_set = {name: (c[0], c[1], tracks(c, rest_rot)) for name, c in clips().items()}
    model = s2.build("preview")
    s2.finish(model)
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
            picks = [0, r * 0.5, r, min(length, r + 0.3), length]
        else:
            picks = [length * f for f in (0, 0.25, 0.5, 0.75, 1.0)]
        stills.append((name, [(t, frame(model, bones, t, size=(300, 210), scale=1.25)) for t in picks]))
    tw, th, pad, top, left = 300, 210, 8, 54, 100
    img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Night Matriarch - key frames (session 7); the GIFs show the motion", font=sheet._font(24),
            fill=sheet.INK)
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
