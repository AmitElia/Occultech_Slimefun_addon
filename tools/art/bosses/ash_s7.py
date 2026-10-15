"""The Elder of Ash, session 7: animation (plan: docs/art/bosses/elder_of_ash/overhaul/plan.md).

Each clip is a few whole poses at key times, built with session 2's pose code (ash_s2.pose: hands and feet planted
back on the ground unless a limb is in mid-step); the keyframes are each bone's turn away from the rest pose, plus
position keys for the whole toad sinking or rising, the tongue sliding out along itself and the brows lifting.
Movement over the ground stays with the server (the leap's arc is the entity's), so no clip travels.

Timed to MireMonarch.java:
  idle      4.0 s loop   heavy, slow breathing (the back rises, the brows settle), a pull on the pipe, a glance aside
  walk      2.0 s loop   a heavy crawl: one hand reaching forward at a time, the body rolling over it
  spawn     2.6 s once   the ritual arrival: he rises out of the circle, volcano first, and settles
  coil      1.5 s hold   the leap's 1.5 s warning (SLAM_WARNING 30 ticks): he sinks onto his haunches, elbows up,
                         glaring up at the target, trembling; the volcano flares white (a tint, session 6)
  leap      0.4 s hold   the jump (the server throws him): arms reaching, hind legs thrown back, held in the air
  land      1.0 s once   the landing: contact at 0 s (the shockwave), a heavy splayed squash, back up
  tongue    1.9 s once   the tongue (TONGUE_WARNING 25 ticks): he lowers his head and glares down the lane, the throat
                         swells, the jaw cracks, and at 1.25 s the tongue shoots out 5 blocks and snaps back
  erupt     2.2 s once   at 66%: a crouch, then head thrown back, jaw wide, as the volcano throws the magma cubes
  blow      2.0 s once   at 33%: a shudder, then the blast at 0.9 s (the cap is swapped for the blown top then)
  flinch    0.4 s once   hit: a jolt, the brows up (layered over whatever he's doing)
  death     3.0 s hold   a gasp, a sag, then slumped flat, chin on the ground

Run from the repository root: python tools/art/bosses/ash_s7.py
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
from bosses import ash_s2 as s2, ash_s3 as s3, ash_s4 as s4, ash_s6 as s6, volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s7_animation"
RIG = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s6_variants" / f"{s3.MODEL_ID}.bbmodel"
P = {k: v[1] for k, v in s2.POSES.items()}
REST = {"plant": True}
OVERRIDE = ("coil", "leap", "land", "tongue", "erupt", "blow", "flinch")
CONTACT = {"land": 0.0, "tongue": 1.25, "blow": 0.9}          # seconds into the clip: the shockwave, the lash, the blast


def spec(base, **changes):
    out = dict(base)
    out.update(changes)
    return out


def clips():
    breathe = spec(REST, y=1.2, head=2, brows=0.5)
    puff = spec(breathe, jaw=-3, head=4)
    glance = spec(REST, turn=-14, head=1)
    step = lambda side, f: spec(REST, y=0.6 * f, tilt=1.5 * f, lifted=(f"hand_{side}",),   # noqa: E731
                                **{f"arm_{side}": (-24, 0, -10), f"forearm_{side}": (-18, 0, 0)},
                                **{f"thigh_{'right' if side == 'left' else 'left'}": (6, 0, 0)})
    roll = spec(REST, y=-1.2)
    coil = P["coil"]
    tremble = lambda d: spec(coil, head=coil["head"] + d, y=coil["y"] - abs(d) * 0.4)   # noqa: E731
    coil_deep = spec(coil, y=coil["y"] - 2, head=coil["head"] + 2)
    leap = spec(P["leap"], y=0)                      # the server throws him; the clip only changes his shape
    slam = spec(P["slam"], jaw=-6)
    slam_deep = spec(slam, y=slam["y"] - 3, head=-10)
    glare = spec(REST, head=-5, brows=-1.5, y=-2)
    swell = spec(glare, jaw=-3, y=-2.5)
    crack = spec(glare, jaw=-10)
    lash = spec(P["tongue"], brows=-1.0)
    snap = spec(lash, jaw=-12, tongue=24)
    crouch = spec(REST, y=-6, head=-8, arm=(0, 0, -12))
    erupt = P["erupt"]
    howl = spec(erupt, head=26, jaw=-28)
    shudder = lambda d: spec(REST, y=-8, head=-10 + d, tilt=d * 0.5)   # noqa: E731
    blast = spec(REST, y=2, tilt=-6, head=18, jaw=-18, brows=2, arm=(0, 0, 8))
    risen = lambda y, tilt, head: spec(REST, y=y, tilt=tilt, head=head, plant=False)   # noqa: E731
    flinch = spec(REST, head=6, tilt=-2, brows=1.5, jaw=-4)
    gasp = spec(REST, head=10, jaw=-12, brows=1.5)
    sag = spec(REST, y=-6, head=-4, tilt=-3, arm=(0, 0, -20))
    death = P["death"]
    return {
        "idle": (4.0, "loop", [(0, REST), (1.2, breathe), (1.7, puff), (2.2, breathe), (2.9, glance), (3.5, REST),
                               (4.0, REST)]),
        "walk": (2.0, "loop", [(0, step("left", 1)), (0.5, roll), (1.0, step("right", 1)), (1.5, roll),
                               (2.0, step("left", 1))]),
        "spawn": (2.6, "once", [(0, risen(-70, 10, 12)), (0.9, risen(-30, 8, 10)), (1.6, risen(-6, 3, 6)),
                                (2.1, spec(REST, y=2, head=4)), (2.6, REST)]),
        "coil": (1.5, "hold", [(0, REST), (0.3, spec(coil, y=-5, head=6)), (0.6, coil), (0.85, tremble(2)),
                               (1.05, tremble(-1.5)), (1.25, tremble(2)), (1.5, coil_deep)]),
        "leap": (0.4, "hold", [(0, coil_deep), (0.12, spec(leap, head=-2)), (0.4, leap)]),
        "land": (1.0, "once", [(0, slam), (0.1, slam_deep), (0.4, slam), (0.75, spec(REST, y=-3)), (1.0, REST)]),
        "tongue": (1.9, "once", [(0, REST), (0.3, glare), (0.8, swell), (1.05, glare), (1.2, crack), (1.25, lash),
                                 (1.45, lash), (1.65, snap), (1.9, REST)]),
        "erupt": (2.2, "once", [(0, REST), (0.4, crouch), (0.9, erupt), (1.3, howl), (1.8, erupt), (2.2, REST)]),
        "blow": (2.0, "once", [(0, REST), (0.3, shudder(0)), (0.5, shudder(4)), (0.65, shudder(-3)), (0.8, shudder(4)),
                               (0.9, blast), (1.4, blast), (2.0, REST)]),
        "flinch": (0.4, "once", [(0, REST), (0.1, flinch), (0.4, REST)]),
        "death": (3.0, "hold", [(0, REST), (0.5, gasp), (1.4, sag), (2.2, death), (3.0, death)]),
    }


# ---- tracks --------------------------------------------------------------------------------------------------------

_POSED = {}


def posed(sp):
    key = json.dumps(sp, sort_keys=True)
    if key not in _POSED:
        m = s2.rig("p", decals=False)
        s2.pose(m, sp)
        _POSED[key] = {g.name: list(g.rotation) for g in m.groups}
    return _POSED[key]


def wrap(d):
    return (d + 180) % 360 - 180


def tracks(clip, rest_rot):
    """Keyframes per bone (rotation deltas from rest, position offsets) for one clip's poses."""
    length, loop, keys = clip
    poses = [(t, sp, posed(sp)) for t, sp in keys]
    moving = set()
    for _, _, rot in poses:
        for name, r in rot.items():
            if any(abs(wrap(r[i] - rest_rot[name][i])) > 0.05 for i in range(3)):
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

    def channel(bone, fn):
        keys_ = [(t, tuple(round(v, 3) for v in fn(sp)), "catmullrom") for t, sp, _ in poses]
        if any(any(abs(v) > 1e-6 for v in k[1]) for k in keys_):
            bones.setdefault(bone, {})["position"] = keys_

    channel("base", lambda sp: (0.0, float(sp.get("y", 0)), 0.0))
    channel("brows", lambda sp: (0.0, float(sp.get("brows", 0)), 0.0))

    def tongue(sp):
        a = math.radians(sp.get("jaw", 0) * 0.5)
        t = sp.get("tongue", 0)
        return (0.0, math.sin(a) * t, -math.cos(a) * t)
    channel("tongue", tongue)
    return bones


def blockbench_animations(model_id, clip_set):
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
        anims.append({"uuid": _uuid(f"{model_id}/anim/{clip}"), "name": clip, "loop": loop, "override": clip in OVERRIDE,
                      "length": length, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                      "start_delay": "", "loop_delay": "", "animators": animators})
    return anims


# ---- preview: the rest model in its zone colours, posed per frame ----------------------------------------------------

LAVA = np.array((255, 132, 40), float)


def frame(model, bones, t, yaw=-38, pitch=14, size=(460, 400), scale=2.3):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    polys = []
    for c in model.cubes:
        if s6.hidden_in(c, False) or min(np.array(c.to) - np.array(c.frm)) < 0.01:
            continue
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        world = (m @ pts)[:3]
        v = (view @ world).T
        wt = world.T
        glow = c.mat.startswith(s4.GLOWING)
        for face, idx in v7.QUADS.items():
            q = wt[list(idx)]
            n = np.cross(q[1] - q[0], q[2] - q[0])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n = n / nn
            if np.dot(q.mean(0) - wt.mean(0), n) < 0:
                n = -n
            if c.mat in s4.TOAD:
                base = np.array(s4.ZONES["skin" if n[1] > s4.UP else "flank"], float)
            elif c.mat.startswith("lava"):
                base = LAVA
            else:
                base = np.array(s4.ZONES.get(c.mat, (128, 128, 128)), float)
            light = 1.0 if glow else 0.55 + 0.45 * max(0.0, n[1] * 0.7 + 0.3 * abs(n[0]) + 0.2 * -n[2])
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * 0.86 - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * 0.86 + 1, size[0], size[1]), fill=(30, 28, 34))
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
    s3.setup()
    rest = s2.rig("rest", decals=False)
    rest_rot = {g.name: list(g.rotation) for g in rest.groups}
    clip_set = {name: (c[0], c[1], tracks(c, rest_rot)) for name, c in clips().items()}
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["animations"] = blockbench_animations(s3.MODEL_ID, clip_set)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    model = s2.build("preview", decals=False)
    s2.finish(model)
    stills = []
    for name, (length, loop, bones) in clip_set.items():
        frames = [frame(model, bones, t) for t in np.arange(0, length + 1e-6, 1 / 15)]
        frames[0].save(OUT / "gifs" / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)
        if name in CONTACT:
            r = CONTACT[name]
            picks = sorted({0.0, round(r * 0.5, 3), r, min(length, round(r + 0.25, 3)), length})
            extra = [round(length * f, 3) for f in (0.5, 0.75, 0.9)]
            while len(picks) < 5:                          # a contact at the start: fill in later moments
                picks = sorted(set(picks) | {extra.pop(0)})
        else:
            picks = [length * f for f in (0, 0.25, 0.5, 0.75, 1.0)]
        stills.append((name, [(t, frame(model, bones, t, size=(300, 260), scale=1.5)) for t in picks[:5]]))
        print(name, "done")
    tw, th, pad, top, left = 300, 260, 8, 54, 100
    img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "The Elder of Ash - key frames (session 7); the GIFs show the motion", font=sheet._font(24),
            fill=sheet.INK)
    for r_, (name, row) in enumerate(stills):
        y = top + r_ * (th + 26 + pad)
        dr.text((pad, y + th // 2 - 10), name, font=sheet._font(19), fill=sheet.INK)
        for c, (t, im) in enumerate(row):
            img.paste(im, (left + c * (tw + pad), y))
            mark = " contact" if name in CONTACT and abs(t - CONTACT[name]) < 1e-6 else ""
            dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s{mark}", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT / "keyframes.png")
    summary = {n: {"length": v[0], "loop": v[1], "bones": len(v[2])} for n, v in clip_set.items()}
    (OUT / "clips.json").write_text(json.dumps({"contact_seconds": CONTACT, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
