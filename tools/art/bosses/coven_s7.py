"""Witch Coven redesign, session 7: animation (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

The clips, per sister (each built round her own vessel), written into her review rig `occultech_coven_<vessel>_rig`
(and later the shipped models). Timings follow WitchCoven.java. Animation is cosmetic: every hit and telegraph still
comes from the server, and session 8 starts each action clip so its release lands on the server's real moment:

  idle      loop 3.0 s   the hover bob, the robe swaying, a slow look round, the hat's tip flopping, the brew pulsing
  walk      loop 1.2 s   the hovering glide: leaning in, the robe trailing, the sleeves dragging back, a quicker bob
  spawn     once 2.0 s   she rises out of the ritual circle folded over, then unfolds into her stoop
  rotation  once 1.4 s   she strikes her vessel at 0.6 s (the moment her brew changes colour: the tint switches here)
  heal      once 1.4 s   the wind-up, then the pour at 0.8 s (the heal lands on her sister)
  curse     once 1.6 s   CURSE_WARNING is 20 ticks: she leans in and casts, trembling, through the warning; a flick
                         at 1.0 s as the curse lands on the marked floor
  throw     once 1.2 s   the wind-up, the release at 0.65 s (the potion leaves her sleeve), the follow-through
  death     hold 2.4 s   she slumps, her hover gives out and she sinks to the floor, her hat sliding

The action clips (rotation, heal, curse, throw) key only the bones they move, so with BetterModel's override the
hover keeps playing under them. The hover is keyed on the two top bones (robe_lower and torso) together.

Previews: each clip as a GIF from Volley's small software renderer, in session 4's flat zone colours.

Run from the repository root: python tools/art/bosses/coven_s7.py
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
from bosses import coven_s2 as s2, coven_s3 as s3, coven_s4 as s4, coven_s5 as s5  # noqa: E402
from bosses import volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s7_animation"
RIGS = ROOT / "docs/art/bosses/witch_coven/overhaul/s5_paint"
PARTIAL = ("rotation", "heal", "curse", "throw")
ZERO = (0, 0, 0)
ONE = (1, 1, 1)
RELEASE = {"rotation": 0.6, "heal": 0.8, "curse": 1.0, "throw": 0.65}   # seconds into the clip


def rot(*keys, interp="catmullrom"):
    return [(t, v, interp) for t, v in keys]


def pose_deltas(vessel, role, pose):
    """A session 2 key pose as rotation deltas from rest, per bone."""
    rest = {g.name: g.rotation for g in s2.build(vessel, role).groups}
    posed = s2.build(vessel, role, s2.POSES[pose][1].get(vessel, {}))
    return {g.name: tuple(g.rotation[i] - rest[g.name][i] for i in range(3)) for g in posed.groups
            if any(abs(g.rotation[i] - rest[g.name][i]) > 1e-6 for i in range(3))}


def scale3(v, f):
    return tuple(x * f for x in v)


def hover(length, height, bob=1):
    """The same bob on the two top bones (the whole witch rises and falls)."""
    keys = [(length * i / 4, (0, height * (0.5 + 0.5 * math.sin(2 * math.pi * bob * i / 4)), 0)) for i in range(5)]
    return {"position": [(t, v, "catmullrom") for t, v in keys]}


def action(vessel, role, pose, windup, release, length, overshoot=1.15, extra=None):
    """Into the pose by `windup`, a snap past it at `release`, then back to rest by `length`."""
    d = pose_deltas(vessel, role, pose)
    bones = {}
    for bone, v in d.items():
        bones[bone] = {"rotation": rot((0, ZERO), (windup, v), (release, scale3(v, overshoot)),
                                       (release + 0.15, v), (length, ZERO))}
    for bone, ch in (extra or {}).items():
        bones.setdefault(bone, {}).update(ch)
    return bones


def clips(vessel, role):
    out = {}
    right_rest = s2.REST[vessel][0]
    # ---- idle: the hover, the robe, a look round, the hat flopping, the brew pulsing
    idle = {
        "robe_lower": dict(hover(3.0, 1.2), rotation=rot((0, ZERO), (1.5, (2, 0, 1)), (3.0, ZERO))),
        "torso": hover(3.0, 1.2),
        "h_head": {"rotation": rot((0, ZERO), (0.9, (2, 10, 0)), (1.9, (-1, -8, 0)), (3.0, ZERO))},
        "hat_tip": {"rotation": rot((0, ZERO), (0.8, (-6, 0, 4)), (1.8, (4, 0, -3)), (3.0, ZERO))},
        "hat_t3": {"rotation": rot((0, ZERO), (1.0, (-2, 0, 2)), (2.0, (2, 0, -1)), (3.0, ZERO))},
        "arm_left": {"rotation": rot((0, ZERO), (1.5, (4, 0, -2)), (3.0, ZERO))},
        "glow_brew": {"scale": rot((0, ONE), (0.4, (1, 1.06, 1)), (0.8, ONE), (1.7, (1, 1.04, 1)), (2.1, ONE),
                                   (3.0, ONE))},
    }
    if vessel != "pot":
        idle["arm_right"] = {"rotation": rot((0, ZERO), (1.2, (-4, 0, 2)), (3.0, ZERO))}
    out["idle"] = (3.0, "loop", idle)
    # ---- walk: the hovering glide
    walk = {
        "robe_lower": dict(hover(1.2, 0.8, 2), rotation=rot((0, (10, 0, 0)), (0.6, (14, 0, 0)), (1.2, (10, 0, 0)))),
        "torso": dict(hover(1.2, 0.8, 2), rotation=rot((0, (-6, 0, 0)), (0.6, (-8, 0, 0)), (1.2, (-6, 0, 0)))),
        "h_head": {"rotation": rot((0, (6, 0, 0)), (1.2, (6, 0, 0)))},
        "hat_tip": {"rotation": rot((0, (10, 0, 0)), (0.6, (16, 0, 0)), (1.2, (10, 0, 0)))},
        "arm_left": {"rotation": rot((0, (-14, 0, 0)), (0.6, (-18, 0, 0)), (1.2, (-14, 0, 0)))},
    }
    if vessel == "bottles":
        walk["arm_right"] = {"rotation": rot((0, (-10, 0, 0)), (0.6, (-14, 0, 0)), (1.2, (-10, 0, 0)))}
    out["walk"] = (1.2, "loop", walk)
    # ---- spawn: rising out of the circle folded over, unfolding
    out["spawn"] = (2.0, "once", {
        "robe_lower": {"position": rot((0, (0, -22, 0)), (1.0, (0, 0, 0)), (2.0, ZERO))},
        "torso": {"position": rot((0, (0, -22, 0)), (1.0, (0, 0, 0)), (2.0, ZERO)),
                  "rotation": rot((0, (-40, 0, 0)), (0.9, (-30, 0, 0)), (1.5, (6, 0, 0)), (2.0, ZERO))},
        "h_head": {"rotation": rot((0, (-30, 0, 0)), (1.2, (-20, 0, 0)), (1.6, (10, 0, 0)), (2.0, ZERO))},
        "arm_right": {"rotation": rot((0, (-20, 0, 0)), (1.2, (-10, 0, 0)), (1.6, (30, 0, -30)), (2.0, ZERO))},
        "arm_left": {"rotation": rot((0, (-20, 0, 0)), (1.2, (-10, 0, 0)), (1.6, (30, 0, 30)), (2.0, ZERO))},
        "hat_tip": {"rotation": rot((0, (30, 0, 0)), (1.5, (-14, 0, 0)), (2.0, ZERO))},
    })
    # ---- the fight's actions, each released on the server's moment
    out["rotation"] = (1.4, "once", action(vessel, role, "rotation", 0.45, RELEASE["rotation"], 1.4, extra={
        "glow_brew": {"scale": rot((0, ONE), (0.6, ONE), (0.7, (1.1, 1.25, 1.1)), (0.95, ONE), (1.4, ONE))}}))
    out["heal"] = (1.4, "once", action(vessel, role, "heal", 0.6, RELEASE["heal"], 1.4))
    curse = action(vessel, role, "curse", 0.35, RELEASE["curse"], 1.6, overshoot=1.25)
    for bone, ch in curse.items():               # a tremble while she casts through the warning
        keys = ch["rotation"]
        hold = dict((t, v) for t, v, _ in keys)[0.35]
        tremble = [(0.35 + 0.1 * i, tuple(x + (1.5 if i % 2 else -1.5) for x in hold)) for i in range(1, 6)]
        ch["rotation"] = rot((0, ZERO), (0.35, hold), *tremble, (RELEASE["curse"], scale3(hold, 1.25)),
                             (RELEASE["curse"] + 0.15, hold), (1.6, ZERO))
    out["curse"] = (1.6, "once", curse)
    throw = action(vessel, role, "throw", 0.5, 0.55, 1.2, overshoot=1.08)
    if "arm_right" in throw and vessel != "pot":
        wound = pose_deltas(vessel, role, "throw")["arm_right"]
        follow = (40 - right_rest[0], -right_rest[1], -right_rest[2])          # whipped forward and down past rest
        throw["arm_right"]["rotation"] = rot((0, ZERO), (0.5, wound), (RELEASE["throw"], follow),
                                             (0.85, follow), (1.2, ZERO))
    if vessel == "pot":                          # the pot is heaved out on the release
        for bone in ("pot_carry", "arm_right", "arm_left"):
            if bone in throw:
                k = throw[bone]["rotation"]
                v = dict((t, v) for t, v, _ in k)[0.5]
                throw[bone]["rotation"] = rot((0, ZERO), (0.5, v), (RELEASE["throw"], scale3(v, 0.55)),
                                              (0.85, scale3(v, 0.55)), (1.2, ZERO))
    out["throw"] = (1.2, "once", throw)
    # ---- death: the slump, the hover giving out, the hat sliding
    death = {bone: {"rotation": rot((0, ZERO), (0.35, scale3(v, 0.3)), (1.0, v), (2.4, v))}
             for bone, v in pose_deltas(vessel, role, "death").items()}
    for top in ("robe_lower", "torso"):
        death.setdefault(top, {})["position"] = rot((0, ZERO), (0.6, (0, 1.5, 0)), (1.6, (0, -6, 0)), (2.4, (0, -6, 0)))
    death["hat"] = {"rotation": rot((0, ZERO), (1.0, ZERO), (1.8, (-10, 0, 24)), (2.4, (-10, 0, 24)))}
    death["glow_brew"] = {"scale": rot((0, ONE), (1.0, ONE), (2.0, (1, 0.6, 1)), (2.4, (1, 0.6, 1)))}
    out["death"] = (2.4, "hold", death)
    return out


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
                        point = {"x": round(v[0], 3), "y": round(v[1], 3), "z": round(v[2], 3)}
                    frames.append({"channel": channel, "data_points": [point], "time": round(t, 3), "color": -1,
                                   "interpolation": interp,
                                   "uuid": _uuid(f"{model_id}/{clip}/{bone}/{channel}/{t}")})
            animators[_uuid(f"{model_id}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{model_id}/anim/{clip}"), "name": clip, "loop": loop,
                      "override": clip in PARTIAL, "length": length, "snapping": 20, "selected": False,
                      "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
                      "animators": animators})
    return anims


# ---- preview renderer (Volley's), in session 4's zone colours with the role's brew -----------------------------------

def frame(model, bones, t, role, yaw=-40, pitch=14, size=(380, 400), scale=4.0):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    tint = np.array(s5.ROLE_TINT[role], float) / 255
    polys = []
    for c in model.cubes:
        if min(np.array(c.to) - np.array(c.frm)) < 0.01:
            continue                                   # the hem planes: thin cards, left out of the preview
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        v = (view @ (m @ pts)[:3]).T
        zone = s5.zone_for(c)
        glow = zone in s5.TINTED
        base = np.array(s5.RAMP[s5.ZONE[zone][0]][s5.ZONE[zone][1]], float) * (tint if glow else 1)
        for face, idx in v7.QUADS.items():
            light = 1.0 if glow else v7.SHADE[face]
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * 0.9 - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * 0.9 + 1, size[0], size[1]), fill=(30, 28, 34))
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
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    sheets = []
    for vessel, role, title in s2.SISTERS:
        model = s2.build(vessel, role)
        clip_set = clips(vessel, role)
        names = {g.name for g in model.groups}
        missing = sorted({b for _, _, bones in clip_set.values() for b in bones} - names)
        if missing:
            raise SystemExit(f"{vessel}: clips key bones the model doesn't have: {missing}")
        model_id = s3.model_id(vessel)
        rig = json.loads((RIGS / vessel / f"{model_id}.bbmodel").read_text(encoding="utf-8"))
        rig["animations"] = [a for a in rig["animations"] if a["name"] not in clip_set] + \
            blockbench_animations(model_id, clip_set)
        out = OUT / vessel
        (out / "gifs").mkdir(parents=True)
        path = out / f"{model_id}.bbmodel"
        path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
        stills = []
        for name, (length, loop, bones) in clip_set.items():
            frames = [frame(model, bones, t, role) for t in np.arange(0, length + 1e-6, 1 / 15)]
            frames[0].save(out / "gifs" / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)
            if name in RELEASE:
                r = RELEASE[name]
                picks = [0, r * 0.5, r, min(length, r + 0.2), length]
            else:
                picks = [length * f for f in (0, 0.25, 0.5, 0.75, 1.0)]
            stills.append((name, [(t, frame(model, bones, t, role, size=(260, 280), scale=2.8)) for t in picks]))
        tw, th, pad, top, left = 260, 280, 8, 54, 110
        img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Witch Coven - {title}: key frames (session 7); the GIFs show the motion",
                font=sheet._font(24), fill=sheet.INK)
        for r_, (name, row) in enumerate(stills):
            y = top + r_ * (th + 26 + pad)
            dr.text((pad, y + th // 2 - 10), name, font=sheet._font(19), fill=sheet.INK)
            for c, (t, im) in enumerate(row):
                img.paste(im, (left + c * (tw + pad), y))
                mark = " release" if name in RELEASE and abs(t - RELEASE[name]) < 1e-6 else ""
                dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s{mark}", font=sheet._font(15),
                        fill=sheet.DIM)
        img.save(out / "keyframes.png")
        summary[vessel] = {k: {"length": v[0], "loop": v[1], "bones": len(v[2])} for k, v in clip_set.items()}
        print(vessel, "animated")
    (OUT / "clips.json").write_text(json.dumps({"release_seconds": RELEASE, "clips": summary}, indent=2) + "\n",
                                    encoding="utf-8")


if __name__ == "__main__":
    main()
