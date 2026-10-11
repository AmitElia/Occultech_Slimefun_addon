"""Brood Mother redesign, session 7: animation.

The clips, written into the review model `occultech_brood_mother_rig` (and later the shipped model). Timings follow
BroodMother.java; animation is cosmetic, every hit and telegraph still comes from the server, and each action clip
starts on the server event that starts the attack (session 8 wires the Mythic `state` calls):

  idle     loop 3.0 s   breathing abdomen, a front leg taps, the jaws chew, the palps twitch, small flames flicker
  walk     loop 0.7 s   the spider gait: two alternating sets of four legs (R0 L1 R2 L3 / L0 R1 L2 R3), each leg
                        lifted on an eased arc and pushed back along the ground, a front-to-back ripple, body sway
  spawn    once 2.4 s   unfolds out of a crouch into the threat display, then settles (the ritual arrival)
  pounce   once 2.6 s   POUNCE_WARNING is 20 ticks: she crouches into the tell 0-0.9 s (held still and turned to her
                        mark by the server), launches at 1.0 s, flies about a second front legs first, lands 1.95-2.2 s
  bite     once 0.7 s   a rear-back, then her whole front lunges as the jaws snap and the front legs stab
  egg_sac  once 1.6 s   the abdomen pumps down twice as the two sacs appear
  web      once 1.8 s   WEB_WARNING is 30 ticks: the abdomen tips up and quivers, then jerks at 1.5 s as the web lands
  snuff    once 0.8 s   a shudder as a group of candles goes out (session 6's health thresholds)
  death    hold 2.8 s   the dead-spider curl: the legs fold in under her and she sinks

Keyframes are offsets from the rest pose, in Blockbench's group convention; Volley's converter negates X and Y for
the animator. Leg directions: a positive Z delta raises a segment on either side; a positive hip yaw swings a right
leg forward and a left leg back.

Flame flicker: only the single-flame and small flame bones flicker (knees, head, thorax, flank). The pile's flames share
one bone across the whole pile, so scaling it would move the far flames; it stays still.

Previews: each clip as a GIF from Volley's small software renderer (cuboids, depth-sorted), for judging motion only.

Run from the repository root: python tools/art/bosses/brood_s7.py
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
from bosses import brood_s2 as s2, brood_s3 as s3, brood_s4 as s4  # noqa: E402
from bosses import volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s7_animation"
RIG = ROOT / "docs/art/bosses/brood_mother/overhaul/s6_variants" / f"{s3.MODEL_ID}.bbmodel"
SET_A = ("leg_r0", "leg_l1", "leg_r2", "leg_l3")      # the alternating tetrapod gait
SET_B = ("leg_l0", "leg_r1", "leg_l2", "leg_r3")
LEGS = SET_A + SET_B
FRONT = ("leg_r0", "leg_l0")
SMALL_FLAMES = ("glow_leg_r1_knee", "glow_leg_l0_knee", "glow_leg_l2_knee", "glow_head_flames", "glow_thorax_flames",
                "glow_flank_flames")
# clips that move only part of her: with BetterModel's override on, bones they don't key keep playing the walk/idle
PARTIAL = ("bite", "egg_sac", "web", "snuff")
ZERO = (0, 0, 0)


def rot(*keys, interp="catmullrom"):
    return [(t, v, interp) for t, v in keys]


def fwd(leg, a):
    """A hip yaw that swings this leg forward by a degrees (negative: back)."""
    return (0, a if leg.startswith("leg_r") else -a, 0)


def clips():
    out = {}

    # ---- idle: breathing, a tap, chewing, twitching, flicker
    idle = {
        "abdomen": {"scale": rot((0, (1, 1, 1)), (1.5, (1.03, 1.04, 1.02)), (3.0, (1, 1, 1)))},
        "h_head": {"rotation": rot((0, ZERO), (1.2, (2, -4, 0)), (2.4, (-1, 3, 0)), (3.0, ZERO))},
        "leg_r0_1": {"rotation": rot((0, ZERO), (0.9, ZERO), (1.1, (0, 0, 10)), (1.3, ZERO), (3.0, ZERO))},
        "leg_r0_3": {"rotation": rot((0, ZERO), (0.9, ZERO), (1.1, (0, 0, 8)), (1.3, ZERO), (3.0, ZERO))},
        "leg_l0_1": {"rotation": rot((0, ZERO), (2.1, ZERO), (2.3, (0, 0, 10)), (2.5, ZERO), (3.0, ZERO))},
        "leg_l0_3": {"rotation": rot((0, ZERO), (2.1, ZERO), (2.3, (0, 0, 8)), (2.5, ZERO), (3.0, ZERO))},
        "mandible_r": {"rotation": rot((0, ZERO), (0.4, (0, -6, 0)), (0.7, ZERO), (1.9, ZERO), (2.2, (0, -5, 0)),
                                       (2.5, ZERO), (3.0, ZERO))},
        "mandible_l": {"rotation": rot((0, ZERO), (0.4, (0, 6, 0)), (0.7, ZERO), (1.9, ZERO), (2.2, (0, 5, 0)),
                                       (2.5, ZERO), (3.0, ZERO))},
        "palp_r": {"rotation": rot((0, ZERO), (1.4, ZERO), (1.55, (0, 0, 8)), (1.7, ZERO), (3.0, ZERO), interp="linear")},
        "palp_l": {"rotation": rot((0, ZERO), (0.5, ZERO), (0.65, (0, 0, 8)), (0.8, ZERO), (3.0, ZERO), interp="linear")},
    }
    idle.update(flicker(3.0))
    out["idle"] = (3.0, "loop", idle)

    # ---- walk: a smooth tetrapod gait with a front-to-back ripple, the body swaying over it
    out["walk"] = (WALK, "loop", walk_clip())

    # ---- spawn: a crouch (legs drawn in, body low) unfolding into the threat display
    spawn = {"root_body": {"position": rot((0, (0, -7, 0)), (1.1, ZERO), (2.4, ZERO))}}
    for leg in LEGS:
        spawn[f"{leg}_1"] = {"rotation": rot((0, (0, 0, 28)), (1.1, ZERO), (2.4, ZERO))}
        spawn[f"{leg}_3"] = {"rotation": rot((0, (0, 0, -40)), (1.1, ZERO), (2.4, ZERO))}
    threat = deltas("threat")
    for bone, v in threat.items():
        ch = spawn.setdefault(bone, {})
        base = {t: val for t, val, _ in ch.get("rotation", [])}
        ch["rotation"] = rot((0, base.get(0, ZERO)), (1.1, ZERO), (1.6, v), (2.0, v), (2.4, ZERO))
    out["spawn"] = (2.4, "once", spawn)

    # ---- pounce: crouch into the tell, launch, fly with the front legs reaching, land and absorb
    out["pounce"] = (POUNCE, "once", pounce_clip())

    # ---- bite: a short rear-back, then the whole front of her lunges as the jaws snap
    out["bite"] = (0.7, "once", {
        "root_body": {"position": rot((0, ZERO), (0.12, (0, 0.5, 1.5)), (0.25, (0, -0.5, -3)), (0.7, ZERO))},
        "h_head": {"rotation": rot((0, ZERO), (0.12, (8, 0, 0)), (0.25, (-2, 0, 0)), (0.7, ZERO))},
        "mandible_r": {"rotation": rot((0, ZERO), (0.12, (0, -26, 0)), (0.25, (0, 8, 0)), (0.7, ZERO), interp="linear")},
        "mandible_l": {"rotation": rot((0, ZERO), (0.12, (0, 26, 0)), (0.25, (0, -8, 0)), (0.7, ZERO), interp="linear")},
        **{f"{leg}_1": {"rotation": rot((0, ZERO), (0.12, (0, 0, 14)), (0.25, (0, 0, 2)), (0.7, ZERO))} for leg in FRONT},
        **{f"{leg}_3": {"rotation": rot((0, ZERO), (0.12, (0, 0, 18)), (0.25, (0, 0, -2)), (0.7, ZERO))} for leg in FRONT},
    })

    # ---- egg sac: two pumps
    out["egg_sac"] = (1.6, "once", {
        "abdomen": {"rotation": rot((0, ZERO), (0.4, (14, 0, 0)), (0.6, (4, 0, 0)), (0.9, (14, 0, 0)), (1.6, ZERO)),
                    "scale": rot((0, (1, 1, 1)), (0.4, (1.04, 0.96, 1.04)), (0.6, (1, 1, 1)), (0.9, (1.04, 0.96, 1.04)),
                                 (1.6, (1, 1, 1)))},
    })

    # ---- web: tip up, quiver through the warning, jerk as it lands
    quiver = [(0.4 + 0.15 * i, (-22 + (3 if i % 2 else -3), 0, 0)) for i in range(7)]
    out["web"] = (1.8, "once", {
        "abdomen": {"rotation": rot((0, ZERO), (0.35, (-22, 0, 0)), *quiver, (1.45, (-30, 0, 0)), (1.55, (-20, 0, 0)),
                                    (1.8, ZERO))},
        "h_head": {"rotation": rot((0, ZERO), (0.35, (-6, 0, 0)), (1.45, (-6, 0, 0)), (1.8, ZERO))},
    })

    # ---- snuff: a shudder as candles go out
    shudder = [(i / 10, (3 if i % 2 else -3, 0, 2 if i % 2 else -2)) for i in range(7)]
    out["snuff"] = (0.8, "once", {
        "thorax": {"rotation": rot((0, ZERO), *shudder, (0.8, ZERO), interp="linear")},
        "h_head": {"rotation": rot((0, ZERO), (0.2, (-8, 0, 0)), (0.8, ZERO))},
    })

    # ---- death: the curl
    # she settles a little, only as far as her jaws can go without sinking into the floor
    death = {"root_body": {"position": rot((0, ZERO), (0.3, (0, 1.5, 0)), (1.6, (0, -1.5, 0)), (2.8, (0, -1.5, 0)))},
             "h_head": {"rotation": rot((0, ZERO), (0.3, (12, 0, 0)), (1.6, (3, 0, 0)), (2.8, (3, 0, 0)))},
             "abdomen": {"rotation": rot((0, ZERO), (1.6, (8, 0, 0)), (2.8, (8, 0, 0)))},
             "mandible_r": {"rotation": rot((0, ZERO), (0.3, (0, -24, 0)), (1.6, (0, -14, 0)), (2.8, (0, -14, 0)))},
             "mandible_l": {"rotation": rot((0, ZERO), (0.3, (0, 24, 0)), (1.6, (0, 14, 0)), (2.8, (0, 14, 0)))}}
    for n, leg in enumerate(LEGS):
        start = 0.3 + 0.06 * n                               # the legs curl in one after another
        death[f"{leg}_hip"] = {"rotation": rot((0, ZERO), (start, ZERO), (1.8, fwd(leg, 6 if leg.endswith(("0", "1")) else -6)),
                                               (2.8, fwd(leg, 6 if leg.endswith(("0", "1")) else -6)))}
        death[f"{leg}_1"] = {"rotation": rot((0, ZERO), (start, (0, 0, -6)), (1.8, (0, 0, 22)), (2.8, (0, 0, 22)))}
        death[f"{leg}_3"] = {"rotation": rot((0, ZERO), (start, ZERO), (1.8, (0, 0, -70)), (2.8, (0, 0, -70)))}
        death[f"{leg}_4"] = {"rotation": rot((0, ZERO), (start, ZERO), (1.8, (0, 0, -40)), (2.8, (0, 0, -40)))}
    out["death"] = (2.8, "hold", death)
    return out


WALK = 0.7           # one stride
SWING = 0.42         # the share of a stride a leg spends lifted and swinging forward


def walk_clip():
    """Each leg: lifted and swung forward (an eased arc, the knee rising and the shin tucking) for SWING of the stride,
    then pushed back along the ground for the rest. The two sets of four legs are half a stride apart, and within a
    set the rear legs lead the front ones a little (a ripple, not a march). The body bobs twice a stride, sways side to
    side, and the abdomen sways against it."""
    import math
    n = 10
    times = [round(WALK * k / n, 3) for k in range(n + 1)]
    clip = {}
    for leg in LEGS:
        pair = int(leg[-1])
        phase = (0.0 if leg in SET_A else 0.5) + 0.04 * (3 - pair)
        reach = 12 if pair == 0 else 15
        yaw, femur, tibia, meta = [], [], [], []
        for t in times:
            u = (t / WALK - phase) % 1.0
            if u < SWING:
                f = u / SWING
                ease = f * f * (3 - 2 * f)
                swing, lift = -reach + 2 * reach * ease, math.sin(math.pi * f)
            else:
                f = (u - SWING) / (1 - SWING)
                swing, lift = reach - 2 * reach * f, 0.0
            yaw.append((t, fwd(leg, swing)))
            femur.append((t, (0, 0, 16 * lift)))
            tibia.append((t, (0, 0, -11 * lift)))
            meta.append((t, (0, 0, -6 * lift)))
        clip[f"{leg}_hip"] = {"rotation": rot(*yaw)}
        clip[f"{leg}_1"] = {"rotation": rot(*femur)}
        clip[f"{leg}_3"] = {"rotation": rot(*tibia)}
        clip[f"{leg}_4"] = {"rotation": rot(*meta)}
    clip["root_body"] = {"position": rot(*[(t, (0, -0.35 + 0.35 * math.cos(4 * math.pi * t / WALK), 0)) for t in times])}
    clip["thorax"] = {"rotation": rot(*[(t, (0, 1.5 * math.sin(2 * math.pi * t / WALK), 0.8 * math.sin(2 * math.pi * t / WALK)))
                                        for t in times])}
    clip["abdomen"] = {"rotation": rot(*[(t, (1.0 * math.cos(4 * math.pi * t / WALK), -2.5 * math.sin(2 * math.pi * t / WALK), 0))
                                         for t in times])}
    clip["h_head"] = {"rotation": rot(*[(t, (0, -1.2 * math.sin(2 * math.pi * t / WALK), 0)) for t in times])}
    clip.update(flicker(WALK))
    return clip


POUNCE = 2.6


def pounce_clip():
    """POUNCE_WARNING is 20 ticks; the server holds her still and turned to her mark for it, then throws her (0.75 up:
    about a second in the air).
      0.00-0.35  she sinks into a crouch: knees up, body low, the front legs raised high, the jaws wide (the tell)
      0.35-0.90  held, the head trembling
      0.90-1.05  launch: the rear legs kick straight, the abdomen swings down
      1.05-1.95  in the air: the front legs reach for the mark, the rest trail behind
      1.95-2.20  landing: the legs fold to absorb it, the jaws snap shut
      2.20-2.60  she rises back to her stance"""
    tell = deltas("pounce")
    clip = {}
    for leg in LEGS:
        front = leg in FRONT
        tf = tell.get(f"{leg}_1", ZERO)
        tt = tell.get(f"{leg}_3", ZERO)
        if front:
            femur = [(0, ZERO), (0.35, tf), (0.9, tf), (1.1, (0, 0, -4)), (1.9, (0, 0, -4)), (2.05, (0, 0, 8)),
                     (2.6, ZERO)]
            tibia = [(0, ZERO), (0.35, tt), (0.9, tt), (1.1, (0, 0, -8)), (1.9, (0, 0, -6)), (2.05, (0, 0, -8)),
                     (2.6, ZERO)]
            yaw = [(0, ZERO), (0.9, ZERO), (1.1, fwd(leg, 16)), (1.9, fwd(leg, 12)), (2.15, ZERO), (2.6, ZERO)]
        else:
            femur = [(0, ZERO), (0.35, (0, 0, 10)), (0.9, (0, 0, 10)), (0.98, (0, 0, -6)), (1.15, (0, 0, -2)),
                     (1.9, (0, 0, 2)), (2.05, (0, 0, 10)), (2.6, ZERO)]
            tibia = [(0, ZERO), (0.35, (0, 0, -12)), (0.9, (0, 0, -12)), (0.98, (0, 0, 10)), (1.15, (0, 0, 6)),
                     (1.9, ZERO), (2.05, (0, 0, -10)), (2.6, ZERO)]
            yaw = [(0, ZERO), (0.9, ZERO), (1.1, fwd(leg, -14)), (1.9, fwd(leg, -8)), (2.15, ZERO), (2.6, ZERO)]
        clip[f"{leg}_1"] = {"rotation": rot(*femur)}
        clip[f"{leg}_3"] = {"rotation": rot(*tibia)}
        clip[f"{leg}_hip"] = {"rotation": rot(*yaw)}
    head = tell.get("h_head", (14, 0, 0))
    tremble = [(0.5 + 0.1 * i, tuple(v + (2 if i % 2 else -1) * (k == 0) for k, v in enumerate(head))) for i in range(4)]
    clip["h_head"] = {"rotation": rot((0, ZERO), (0.35, head), *tremble, (0.9, head), (1.1, (8, 0, 0)), (1.9, (4, 0, 0)),
                                      (2.1, ZERO), (2.6, ZERO))}
    jaw_r = tell.get("mandible_r", (0, -28, 0))
    jaw_l = tell.get("mandible_l", (0, 28, 0))
    clip["mandible_r"] = {"rotation": rot((0, ZERO), (0.3, jaw_r), (1.95, jaw_r), (2.05, (0, 8, 0)), (2.6, ZERO))}
    clip["mandible_l"] = {"rotation": rot((0, ZERO), (0.3, jaw_l), (1.95, jaw_l), (2.05, (0, -8, 0)), (2.6, ZERO))}
    clip["root_body"] = {"position": rot((0, ZERO), (0.35, (0, -2, 0)), (0.9, (0, -2, 0)), (1.0, (0, 1, 0)),
                                         (1.9, (0, 0.5, 0)), (2.05, (0, -1.5, 0)), (2.6, ZERO))}
    clip["abdomen"] = {"rotation": rot((0, ZERO), (0.35, (6, 0, 0)), (0.9, (6, 0, 0)), (1.1, (-8, 0, 0)), (1.9, ZERO),
                                       (2.05, (6, 0, 0)), (2.6, ZERO))}
    return clip


def flicker(length):
    """Small flames flicker: quick, uneven scale changes about each flame bone's pivot (on one of its flames)."""
    out = {}
    for n, bone in enumerate(SMALL_FLAMES):
        keys, t, k = [], 0.0, 0
        while t < length - 1e-6:
            up = (n + k) % 3
            keys.append((round(t, 3), ((0.94, 1.12, 0.94), (1.04, 0.92, 1.04), (1.0, 1.05, 1.0))[up], "linear"))
            t += (0.12, 0.17, 0.1, 0.15)[(n + k) % 4]
            k += 1
        keys.append((length, keys[0][1], "linear"))
        out[bone] = {"scale": keys}
    return out


def deltas(pose_name):
    """A session 3 pose as rotation deltas from rest."""
    table = s3.pose_table()[pose_name]
    rest = {g.name: g.rotation for g in s3.rigged().groups}
    return {b: tuple(v[i] - rest[b][i] for i in range(3)) for b, v in table.items()}


def blockbench_animations(clip_set):
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
                                   "uuid": _uuid(f"{s3.MODEL_ID}/{clip}/{bone}/{channel}/{t}")})
            animators[_uuid(f"{s3.MODEL_ID}/group/{bone}")] = {"name": bone, "type": "bone", "keyframes": frames}
        anims.append({"uuid": _uuid(f"{s3.MODEL_ID}/anim/{clip}"), "name": clip, "loop": loop,
                      "override": clip in PARTIAL, "length": length, "snapping": 20, "selected": False,
                      "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
                      "animators": animators})
    return anims


# ---- preview renderer (Volley's, with her colours; hair cards are left out, they are planes) -----------------------

def frame(model, bones, t, yaw=-32, pitch=16, size=(460, 400), scale=2.5):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    polys = []
    for c in model.cubes:
        if c.mat == "hair":
            continue
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        v = (view @ ((m @ pts)[:3].T - np.array([0, 0, 0])).T).T
        base = np.array(s4.ZONES[c.mat], float)
        for face, idx in v7.QUADS.items():
            light = 1.0 if c.mat in s4.GLOW_ZONES else v7.SHADE[face]
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * 0.82 - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * 0.82 + 1, size[0], size[1]), fill=(30, 28, 34))
    px = size[0] / 2 + 70 * scale
    dr.rectangle((px, size[1] * 0.82 - 29 * scale, px + 6 * scale, size[1] * 0.82), fill=(70, 110, 160))  # a player
    for _, pts, col in sorted(polys, key=lambda p: -p[0]):
        dr.polygon(pts, fill=col)
    return img


def main():
    model = s4.rig()
    clip_set = clips()
    names = {g.name for g in model.groups}
    missing = sorted({b for _, _, bones in clip_set.values() for b in bones} - names)
    if missing:
        raise SystemExit(f"clips key bones the model doesn't have: {missing}")
    OUT.mkdir(parents=True, exist_ok=True)
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["animations"] = [a for a in rig["animations"] if a["name"] not in clip_set] + blockbench_animations(clip_set)
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
        picks = {"pounce": [0, 0.5, 1.0, 1.5, 2.05], "web": [0, 0.5, 1.45, 1.55, 1.8],
                 "bite": [0, 0.12, 0.25, 0.45, 0.7]}.get(name, [length * f for f in (0, 0.25, 0.5, 0.75, 1.0)])
        stills.append((name, [(t, frame(model, bones, t, size=(330, 290), scale=1.8)) for t in picks]))
    tw, th, pad, top, left = 330, 290, 8, 54, 110
    img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Brood Mother - animation key frames (session 7); the GIFs show the motion",
            font=sheet._font(26), fill=sheet.INK)
    for r, (name, row) in enumerate(stills):
        y = top + r * (th + 26 + pad)
        dr.text((pad, y + th // 2 - 10), name, font=sheet._font(20), fill=sheet.INK)
        for c, (t, im) in enumerate(row):
            img.paste(im, (left + c * (tw + pad), y))
            dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s", font=sheet._font(15), fill=sheet.DIM)
    img.save(OUT / "keyframes.png")
    print(json.dumps({k: {"length": v[0], "loop": v[1], "bones": len(v[2])} for k, v in clip_set.items()}))


if __name__ == "__main__":
    main()
