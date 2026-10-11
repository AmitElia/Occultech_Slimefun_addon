"""Volley redesign, session 7: animation.

The clips, written into the review model `occultech_volley_rig` (and later the shipped model):

  idle     loop 3.0 s   breathing hunch, a counting click of the jaw, the geode pulses
  walk     loop 1.6 s   heavy crone lumber, the left knuckles swinging low
  spawn    once 2.4 s   uncurls out of the ritual, the geode grows out of the hump, the head comes up last
  burst    once 2.6 s   Volley.java: warning 0-1.0 s (cranking the windlass), arrows at 1.0/1.25/1.5/1.75/2.0 s
                        (one recoil and one jaw click each), recover 2.0-2.6 s
  wards    once 1.6 s   rears up, the geode flares (raising the amethyst wards)
  stagger  once 0.9 s   the last ward shatters
  cracked  once 1.4 s   below 40% health: a shudder as the big shards snap
  death    hold 2.6 s   a last rearing cry, then he folds onto his knees and the arbalest drops

Animation is cosmetic: every hit, telegraph and timing still comes from Volley.java. Each clip starts on the
server event that starts the attack (session 8 wires the Mythic `state` calls), so the motion can't drift from the
damage.

Keyframes are written as offsets from the rest pose. Rotations use Blockbench's group convention here; the converter
negates X and Y for Blockbench's animator, as in session 3.

Previews: each clip as a GIF from a small software renderer (cuboids, depth-sorted, shaded per face). It's for
judging motion, not looks.

Run from the repository root: python tools/art/bosses/volley_crone_s7.py
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
from bosskit.bbmodel import _uuid, pivot_matrix, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s3 as s3, volley_crone_s4 as s4, volley_crone_s6 as s6  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s7_animation"
SHOTS = (1.0, 1.25, 1.5, 1.75, 2.0)          # Volley.java: BURST_CONTACT at +20 ticks, then one arrow per 5-tick step


def rest(model):
    return {g.name: list(g.rotation) for g in model.groups}


def pose_delta(model, pose):
    r = rest(model)
    return {k: tuple(v[i] - r[k][i] for i in range(3)) for k, v in pose.items()}


def clips(model):
    """name -> (length, loop, {bone: {channel: [(time, value, interpolation)]}}); rotations are deltas from rest."""
    windup, aim = pose_delta(model, s3.POSES["windup"]), pose_delta(model, s3.POSES["aim"])
    wards, stagger = pose_delta(model, s3.POSES["wards"]), pose_delta(model, s3.POSES["stagger"])
    zero = (0, 0, 0)
    out = {}

    def rot(*keys, interp="linear"):
        return [(t, v, interp) for t, v in keys]

    out["idle"] = (3.0, "loop", {
        "torso": {"rotation": rot((0, zero), (1.5, (-2.5, 0, 0)), (3.0, zero), interp="catmullrom")},
        "waist": {"rotation": rot((0, zero), (1.5, (1, 0, 0)), (3.0, zero), interp="catmullrom")},
        "h_head": {"rotation": rot((0, zero), (1.0, (2, -5, 0)), (2.2, (-1, 4, 0)), (3.0, zero), interp="catmullrom")},
        "arm_left_upper": {"rotation": rot((0, zero), (1.5, (3, 0, -2)), (3.0, zero), interp="catmullrom")},
        "arm_right_upper": {"rotation": rot((0, zero), (1.5, (2, 0, 0)), (3.0, zero), interp="catmullrom")},
        # the counting jaw: three small clicks, then stillness
        "jaw_counter": {"rotation": rot((0, zero), (0.4, (-5, 0, 0)), (0.5, zero), (0.8, (-5, 0, 0)), (0.9, zero),
                                        (1.2, (-5, 0, 0)), (1.3, zero), (3.0, zero), interp="step")},
        "crystals_back": {"scale": rot((0, (1, 1, 1)), (1.5, (1.03, 1.03, 1.03)), (3.0, (1, 1, 1)),
                                       interp="catmullrom")},
    })

    swing = lambda a, length=1.6: rot((0, a), (length / 2, tuple(-v for v in a)), (length, a), interp="catmullrom")
    out["walk"] = (1.6, "loop", {
        "leg_left_thigh": {"rotation": swing((22, 0, 0))},
        "leg_right_thigh": {"rotation": swing((-22, 0, 0))},
        "leg_left_shin": {"rotation": rot((0, zero), (0.4, (-28, 0, 0)), (0.8, zero), (1.6, zero), interp="catmullrom")},
        "leg_right_shin": {"rotation": rot((0, zero), (0.8, zero), (1.2, (-28, 0, 0)), (1.6, zero), interp="catmullrom")},
        "root_body": {"position": rot((0, zero), (0.4, (0, -1, 0)), (0.8, zero), (1.2, (0, -1, 0)), (1.6, zero),
                                      interp="catmullrom")},
        "waist": {"rotation": swing((0, 6, 2))},
        "torso": {"rotation": rot((0, zero), (0.4, (-2, 0, 0)), (0.8, zero), (1.2, (-2, 0, 0)), (1.6, zero),
                                  interp="catmullrom")},
        "arm_left_upper": {"rotation": swing((-16, 0, 0))},
        "arm_left_forearm": {"rotation": swing((-6, 0, 0))},
        "arm_right_upper": {"rotation": swing((4, 0, 0))},
        "h_head": {"rotation": swing((0, -5, 0))},
    })

    out["spawn"] = (2.4, "once", {
        "waist": {"rotation": rot((0, (-20, 0, 0)), (1.4, (4, 0, 0)), (2.0, zero), interp="catmullrom")},
        "torso": {"rotation": rot((0, (-14, 0, 0)), (1.4, (5, 0, 0)), (2.0, zero), interp="catmullrom")},
        "h_head": {"rotation": rot((0, (-28, 0, 0)), (1.2, (-28, 0, 0)), (1.8, (10, 0, 0)), (2.2, zero),
                                   interp="catmullrom")},
        "arm_left_upper": {"rotation": rot((0, (25, 0, 0)), (1.4, zero), interp="catmullrom")},
        "arm_right_upper": {"rotation": rot((0, (-6, 0, 0)), (1.4, zero), interp="catmullrom")},
        "crystals_back": {"scale": rot((0, (0.2, 0.2, 0.2)), (1.6, (1.15, 1.15, 1.15)), (2.0, (1, 1, 1)),
                                       interp="catmullrom")},
        "glow_crystals": {"scale": rot((0, (0.1, 0.1, 0.1)), (1.7, (1.2, 1.2, 1.2)), (2.1, (1, 1, 1)),
                                       interp="catmullrom")},
        "jaw_counter": {"rotation": rot((1.8, zero), (1.9, (-14, 0, 0)), (2.3, zero), interp="catmullrom")},
    })

    burst = {}

    def key(bone, channel, t, v, interp="catmullrom"):
        burst.setdefault(bone, {}).setdefault(channel, []).append((t, v, interp))

    for bone in set(windup) | set(aim):
        w, a = windup.get(bone, zero), aim.get(bone, zero)
        key(bone, "rotation", 0.0, zero)
        key(bone, "rotation", 0.3, w)                 # prepare: settle into the crank
        key(bone, "rotation", 0.85, w)
        key(bone, "rotation", 1.0, a, "linear")       # commit: snap up to aim as the first bolt leaves
        key(bone, "rotation", 2.05, a)
        key(bone, "rotation", 2.6, zero)              # recover
    key("windlass", "rotation", 0.0, zero, "linear")
    key("windlass", "rotation", 0.85, (720, 0, 0), "linear")  # two turns of the crank during the 1 s warning
    key("windlass", "rotation", 2.6, (720, 0, 0), "linear")
    jaw = [(0.0, zero, "step")]
    for t in SHOTS:                                   # contact: a kick and a counting click per arrow
        key("arm_right_forearm", "rotation", t + 0.06, tuple(v + d for v, d in zip(aim["arm_right_forearm"], (-9, 0, 0))))
        key("arm_right_forearm", "rotation", t + 0.2, aim["arm_right_forearm"])
        jaw += [(t, (-7, 0, 0), "step"), (t + 0.12, zero, "step")]
    for bone in burst:
        burst[bone]["rotation"].sort(key=lambda k: k[0])
    burst["jaw_counter"] = {"rotation": jaw}
    out["burst"] = (2.6, "once", burst)

    def to_pose_and_back(pose, length, hold_from, hold_to, extra=None):
        clip = {b: {"rotation": rot((0, zero), (hold_from, v), (hold_to, v), (length, zero), interp="catmullrom")}
                for b, v in pose.items()}
        clip.update(extra or {})
        return clip

    flare = lambda peak: {"scale": rot((0, (1, 1, 1)), (0.6, (peak,) * 3), (1.0, (1, 1, 1)), interp="catmullrom")}
    out["wards"] = (1.6, "once", to_pose_and_back(wards, 1.6, 0.5, 1.1, {"crystals_back": flare(1.18),
                                                                         "glow_crystals": flare(1.25)}))
    out["stagger"] = (0.9, "once", to_pose_and_back(stagger, 0.9, 0.18, 0.45))
    shudder = [(t / 10, (-4 if i % 2 else 4, 0, 0), "linear") for i, t in enumerate(range(0, 9))]
    out["cracked"] = (1.4, "once", {
        "torso": {"rotation": shudder + [(1.4, zero, "catmullrom")]},
        "h_head": {"rotation": rot((0, zero), (0.3, (-18, 0, 6)), (1.0, (-10, 0, 0)), (1.4, zero), interp="catmullrom")},
        "arm_left_upper": {"rotation": rot((0, zero), (0.25, (10, 0, -10)), (1.4, zero), interp="catmullrom")},
        "jaw_counter": {"rotation": rot((0, zero), (0.2, (-16, 0, 0)), (1.0, (-10, 0, 0)), (1.4, zero), interp="catmullrom")},
    })
    out["death"] = (2.6, "hold", {
        "root_body": {"position": rot((0, zero), (0.4, (0, 1, 0)), (1.6, (0, -9, 0)), (2.6, (0, -9, 0)), interp="catmullrom")},
        "waist": {"rotation": rot((0, zero), (0.4, (12, 0, 0)), (1.6, (-30, 0, 4)), (2.6, (-32, 0, 4)), interp="catmullrom")},
        "torso": {"rotation": rot((0, zero), (0.4, (10, 0, 0)), (1.6, (-24, 0, 0)), (2.6, (-26, 0, 0)), interp="catmullrom")},
        "h_head": {"rotation": rot((0, zero), (0.4, (22, 0, 0)), (1.6, (-22, 8, 0)), (2.6, (-26, 10, 0)), interp="catmullrom")},
        "jaw_counter": {"rotation": rot((0, zero), (0.35, (-20, 0, 0)), (1.2, (-8, 0, 0)), (2.6, (-12, 0, 0)), interp="catmullrom")},
        "leg_left_thigh": {"rotation": rot((0.4, zero), (1.6, (62, 0, -6)), (2.6, (62, 0, -6)), interp="catmullrom")},
        "leg_right_thigh": {"rotation": rot((0.4, zero), (1.6, (62, 0, 6)), (2.6, (62, 0, 6)), interp="catmullrom")},
        "leg_left_shin": {"rotation": rot((0.4, zero), (1.6, (-100, 0, 0)), (2.6, (-100, 0, 0)), interp="catmullrom")},
        "leg_right_shin": {"rotation": rot((0.4, zero), (1.6, (-100, 0, 0)), (2.6, (-100, 0, 0)), interp="catmullrom")},
        "arm_left_upper": {"rotation": rot((0, zero), (0.4, (-10, 0, -20)), (1.6, (25, 0, 0)), (2.6, (28, 0, 0)), interp="catmullrom")},
        "arm_right_upper": {"rotation": rot((0, zero), (0.4, (-10, 0, 20)), (1.6, (15, 0, 0)), (2.6, (18, 0, 0)), interp="catmullrom")},
        "arbalest": {"rotation": rot((0, zero), (1.0, zero), (1.4, (70, 0, 10)), (2.6, (75, 0, 10)), interp="catmullrom")},
    })
    return out


# ---- the bbmodel ---------------------------------------------------------------------------------------------------

def blockbench_animations(model, clip_set, name):
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
                                   "interpolation": interp, "uuid": _uuid(f"{name}/{clip}/{bone}/{channel}/{t}")})
            animators[_uuid(f"{name}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{name}/anim/{clip}"), "name": clip, "loop": loop, "override": False,
                      "length": length, "snapping": 20, "selected": False, "anim_time_update": "", "blend_weight": "",
                      "start_delay": "", "loop_delay": "", "animators": animators})
    return anims


# ---- preview renderer ----------------------------------------------------------------------------------------------

def sample(keys, t, loop_length=None):
    """Value of a keyframe track at time t (linear between keys, step holds; Catmull-Rom is previewed as linear)."""
    keys = sorted(keys, key=lambda k: k[0])
    if t <= keys[0][0]:
        return np.array(keys[0][1], float)
    for (t0, v0, i0), (t1, v1, _) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            if i0 == "step":
                return np.array(v0, float)
            f = (t - t0) / max(1e-9, t1 - t0)
            f = f * f * (3 - 2 * f) if i0 == "catmullrom" else f
            return np.array(v0, float) * (1 - f) + np.array(v1, float) * f
    return np.array(keys[-1][1], float)


def matrices(model, bones, t):
    out = {}

    def world(g):
        if g.name in out:
            return out[g.name]
        ch = bones.get(g.name, {})
        r = np.array(g.rotation) + (sample(ch["rotation"], t) if "rotation" in ch else 0)
        p = sample(ch["position"], t) if "position" in ch else np.zeros(3)
        s = sample(ch["scale"], t) if "scale" in ch else np.ones(3)
        o = np.array(g.origin)
        m = np.eye(4)
        m[:3, :3] = rotation_matrix(r) @ np.diag(s)
        m[:3, 3] = o + p - m[:3, :3] @ o
        parent = world(g.parent) if g.parent is not None and g.parent.name != "root" else np.eye(4)
        out[g.name] = parent @ m
        return out[g.name]

    for g in model.groups:
        world(g)
    return out


SHADE = {"north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62, "up": 1.0, "down": 0.45}
QUADS = {"north": (0, 2, 6, 4), "south": (1, 5, 7, 3), "west": (0, 1, 3, 2), "east": (4, 6, 7, 5),
         "down": (0, 4, 5, 1), "up": (2, 3, 7, 6)}


def frame(model, bones, t, yaw=-32, pitch=16, size=(420, 420), scale=4.2):
    mats = matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry     # the camera sits in front (-Z), turned by yaw and raised by pitch, looking at +Z
    polys = []
    for c in model.cubes:
        if s6.hidden(c):
            continue
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        world = (m @ pts)[:3].T
        v = (view @ (world - np.array([0, 0, -12])).T).T
        zone = s4.zone_for(c)
        base = np.array(s4.ZONES[zone], float)
        for face, idx in QUADS.items():
            light = 1.0 if zone == "glow" else SHADE[face]
            col = tuple(int(min(255, x * light)) for x in base)
            # painter's order: farthest first; the screen's right is the model's left (-X) from the front
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * 0.86 - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * 0.86 + 1, size[0], size[1]), fill=(30, 28, 34))
    px = size[0] / 2 - 40 * scale
    dr.rectangle((px, size[1] * 0.86 - 29 * scale, px + 6 * scale, size[1] * 0.86), fill=(70, 110, 160))  # 1.8-block player
    for _, pts, col in sorted(polys, key=lambda p: -p[0]):
        dr.polygon(pts, fill=col)
    return img


def main():
    model = s6.build()
    clip_set = clips(model)
    OUT.mkdir(parents=True, exist_ok=True)
    # the review model: session 6's painted rig, with the clips added after the six held test poses
    rig = json.loads((ROOT / "docs/art/bosses/volley/overhaul/s6_variants" / f"{s3.MODEL_ID}.bbmodel").read_text(encoding="utf-8"))
    rig["animations"] = [a for a in rig["animations"] if a["name"] not in clip_set] + \
        blockbench_animations(model, clip_set, s3.MODEL_ID)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    gifs = OUT / "gifs"
    gifs.mkdir(exist_ok=True)
    stills = []
    for name, (length, loop, bones) in clip_set.items():
        frames = [frame(model, bones, t) for t in np.arange(0, length + 1e-6, 1 / 15)]
        frames[0].save(gifs / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)
        marks = SHOTS if name == "burst" else ()
        picks = [0, length * 0.33, length * 0.66, length] if not marks else [0.5, 0.95, 1.06, 2.0, 2.6]
        stills.append((name, [(t, frame(model, bones, t, size=(300, 300), scale=3.0)) for t in picks]))
    tw, pad, top, left = 300, 8, 54, 110
    width = left + 5 * (tw + pad)
    img = Image.new("RGB", (width, top + len(stills) * (tw + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Volley - animation key frames (session 7); the GIFs show the motion", font=sheet._font(26),
            fill=sheet.INK)
    for r, (name, row) in enumerate(stills):
        y = top + r * (tw + 26 + pad)
        dr.text((pad, y + tw // 2 - 10), name, font=sheet._font(20), fill=sheet.INK)
        for c, (t, im) in enumerate(row):
            img.paste(im, (left + c * (tw + pad), y))
            dr.text((left + c * (tw + pad) + 4, y + tw + 3), f"{t:.2f} s", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT / "keyframes.png")
    print(json.dumps({k: {"length": v[0], "loop": v[1], "bones": len(v[2])} for k, v in clip_set.items()}))


if __name__ == "__main__":
    main()
