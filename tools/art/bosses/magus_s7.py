"""The Mirrored Magus redesign, session 7: animation - his clips and the Jack-in-the-Box's.

His clips are built from session 2's key poses (each bone's turn away from rest; the hips sink with a position key
where a pose sits him lower). Timings follow MirroredMagus.java and the jack's design (overhaul/jack/README.md).
Animation is cosmetic: every hit and telegraph comes from the server, and session 8 starts each action clip so its
release lands on the server's real moment.

The Magus (`occultech_mirrored_magus_rig`):
  idle     loop 3.0 s   hunched, swaying from the hips, his head tilting side to side, the hat's points flopping
  walk     loop 1.6 s   a long-legged stalk: high knees, the arms swinging loose, a bob on each step
  spawn    once 2.4 s   unfolding out of himself (the blink's fold), rising into a deep curtsey, then up
  throw    once 1.2 s   the card fan: the arm drawn back, flung out at 0.55 s (the cards leave his palm), follow-through
  prism    once 2.2 s   PRISM_WARNING is 30 ticks: his arms rise with the cards overhead, trembling through the warning;
                        the burst at 1.5 s
  curtsey  once 1.8 s   conjuring the decoys: the bow, the decoys appear at 0.9 s
  blink    once 0.8 s   folding into himself and shrinking; the teleport at 0.4 s, unfolding where he lands
  laugh    once 1.4 s   a decoy struck: his head thrown back, shaking with the laugh
  snap     once 1.0 s   the jacks' summons: his left hand raised, the snap at 0.5 s
  flinch   once 0.4 s   hit: a jolt (layered over whatever he's doing)
  death    hold 2.6 s   the strings cut: he crumples and sits slumped, his head lolling, the hat's points flopping

The Jack-in-the-Box (`occultech_mirrored_magus_jack`, its own model, built at half size):
  pop      once 2.0 s   the box shut, rattling, its crank turning through the 1.5 s warning; the lid flies open at
                        1.5 s and the clown shoots up past full stretch, wobbling to a stop
  bop      loop 0.6 s   the spring squashing and stretching, the clown nodding, the hat flopping
  throw    once 1.5 s   three bops winding up, a big stretch back, the flick at 1.15 s (the card leaves his hand)
  wind     hold 1.4 s   the wind-down: the spring sags, the clown droops into the box, the lid slams shut
  death    hold 0.9 s   broken: the head pops off the spring, the spring goes limp, the box bursts

The action clips key only the bones they move, so with BetterModel's override the idle or bop keeps playing under
them. The jack's clown rides the spring's top: the spring is scaled in y and the body moved with its top, so the clown
isn't squashed with it.

Previews: each clip as a GIF from Volley's small software renderer, in flat zone colours.

Run from the repository root: python tools/art/bosses/magus_s7.py (after magus_s5.py)
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
from bosskit.bbmodel import _uuid, add_hitbox, pivot_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import magus_s2 as s2, magus_s3 as s3, magus_s4 as s4, magus_s5 as s5, magus_jack as jack  # noqa: E402
from bosses import volley_crone_s7 as v7  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s7_animation"
RIG = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s5_paint" / f"{s3.MODEL_ID}.bbmodel"
JACK_ID = "occultech_mirrored_magus_jack"
PARTIAL = ("throw", "snap", "flinch")
ZERO = (0, 0, 0)
ONE = (1, 1, 1)
RELEASE = {"throw": 0.55, "prism": 1.5, "curtsey": 0.9, "blink": 0.4, "snap": 0.5}
JACK_RELEASE = {"pop": 1.5, "throw": 1.15}
SPRING = 16.0 * jack.SCALE                     # the jack's spring at rest, in the shipped (half-size) rig


def rot(*keys, interp="catmullrom"):
    return [(t, v, interp) for t, v in keys]


def lin(*keys):
    return rot(*keys, interp="linear")


def scale3(v, f):
    return tuple(x * f for x in v)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


# ---- the Magus ---------------------------------------------------------------------------------------------------------

def pose_deltas(key):
    """A session 2 key pose as rotation deltas from rest, per bone, and how far the hips sink."""
    rest = s2.build("rest")
    s2.finish(rest)
    rest_drop = float(rest.bounds()[0][1])
    rest_rot = {g.name: g.rotation for g in rest.groups}
    posed = s2.build("p")
    s2.finish(posed)
    d = s2.pose(posed, key)
    rot_ = {g.name: tuple(g.rotation[i] - rest_rot[g.name][i] for i in range(3)) for g in posed.groups
            if any(abs(g.rotation[i] - rest_rot[g.name][i]) > 1e-6 for i in range(3))}
    return rot_, -(d - rest_drop)


SNAP = {"arm_left": (128, 0, -22), "forearm_left": (40, 0, 0), "neck": (-6, 0, -12), "torso": (4, 8, 0)}


def into(deltas, keys):
    """Each bone keyed through the pose scaled by each key's weight: keys are (time, weight)."""
    return {bone: {"rotation": rot(*[(t, scale3(v, w)) for t, w in keys])} for bone, v in deltas.items()}


def magus_clips():
    out = {}
    idle_pose, _ = pose_deltas("idle")
    # ---- idle: hunched (the idle pose), swaying, the head tilting, the points flopping
    idle = {b: {"rotation": rot((0, v), (3.0, v))} for b, v in idle_pose.items()}
    idle["torso"] = {"rotation": rot((0, (2, 0, 3)), (1.5, (4, 0, -3)), (3.0, (2, 0, 3)))}
    idle["neck"] = {"rotation": rot((0, idle_pose["neck"]), (1.5, (6, 0, -10)), (3.0, idle_pose["neck"]))}
    idle["hips"] = {"position": rot((0, ZERO), (0.75, (0, -0.6, 0)), (1.5, ZERO), (2.25, (0, -0.6, 0)), (3.0, ZERO))}
    for k, (name, sign) in enumerate((("hat_left", 1), ("hat_right", -1), ("hat_back", 1))):
        axis = 0 if name == "hat_back" else 2
        for j in range(3):
            a = (6 + 3 * j) * sign
            v1, v2 = [0, 0, 0], [0, 0, 0]
            v1[axis], v2[axis] = a, -a * 0.6
            off = 0.25 * j + 0.3 * k
            idle[f"{name}_{j}"] = {"rotation": rot((0, ZERO), (0.75 + off, tuple(v1)), (2.25 + off, tuple(v2)),
                                                   (3.0, ZERO))}
    out["idle"] = (3.0, "loop", idle)
    # ---- walk: a long-legged stalk
    walk = {
        "hips": {"position": rot((0, ZERO), (0.4, (0, 1.2, 0)), (0.8, ZERO), (1.2, (0, 1.2, 0)), (1.6, ZERO))},
        "torso": {"rotation": rot((0, (-8, 4, 0)), (0.8, (-8, -4, 0)), (1.6, (-8, 4, 0)))},
        "neck": {"rotation": rot((0, (6, 0, 6)), (0.8, (6, 0, -6)), (1.6, (6, 0, 6)))},
        "leg_left": {"rotation": rot((0, (28, 0, 0)), (0.8, (-22, 0, 0)), (1.6, (28, 0, 0)))},
        "shin_left": {"rotation": rot((0, (4, 0, 0)), (0.4, (-4, 0, 0)), (0.8, (2, 0, 0)), (1.2, (40, 0, 0)),
                                      (1.6, (4, 0, 0)))},
        "leg_right": {"rotation": rot((0, (-22, 0, 0)), (0.8, (28, 0, 0)), (1.6, (-22, 0, 0)))},
        "shin_right": {"rotation": rot((0, (2, 0, 0)), (0.4, (40, 0, 0)), (0.8, (4, 0, 0)), (1.2, (-4, 0, 0)),
                                       (1.6, (2, 0, 0)))},
        "arm_left": {"rotation": rot((0, (-18, 0, -6)), (0.8, (20, 0, -6)), (1.6, (-18, 0, -6)))},
        "arm_right": {"rotation": rot((0, (20, 0, 6)), (0.8, (-18, 0, 6)), (1.6, (20, 0, 6)))},
        "hat_left_0": {"rotation": rot((0, (0, 0, 8)), (0.8, (0, 0, -4)), (1.6, (0, 0, 8)))},
        "hat_right_0": {"rotation": rot((0, (0, 0, 4)), (0.8, (0, 0, -8)), (1.6, (0, 0, 4)))},
        "hat_back_0": {"rotation": rot((0, (10, 0, 0)), (0.8, (4, 0, 0)), (1.6, (10, 0, 0)))},
    }
    out["walk"] = (1.6, "loop", walk)
    # ---- spawn: unfolding from the blink's fold, the curtsey, up
    blink, blink_drop = pose_deltas("blink")
    curtsey, curtsey_drop = pose_deltas("curtsey")
    spawn = {}
    for b in set(blink) | set(curtsey):
        spawn[b] = {"rotation": rot((0, blink.get(b, ZERO)), (0.6, blink.get(b, ZERO)), (1.3, curtsey.get(b, ZERO)),
                                    (1.8, curtsey.get(b, ZERO)), (2.4, ZERO))}
    spawn["hips"] = {"position": rot((0, (0, blink_drop - 30, 0)), (0.6, (0, blink_drop, 0)),
                                     (1.3, (0, curtsey_drop, 0)), (1.8, (0, curtsey_drop, 0)), (2.4, ZERO)),
                     "scale": rot((0, (0.4, 0.4, 0.4)), (0.6, ONE), (2.4, ONE))}
    out["spawn"] = (2.4, "once", spawn)
    # ---- throw: drawn back, flung out at the release, the follow-through
    throw_pose, _ = pose_deltas("throw")
    throw = into(throw_pose, ((0, 0), (0.3, -0.35), (0.45, 0.6), (RELEASE["throw"], 1.12), (0.75, 1.0), (1.2, 0)))
    throw["cards"] = {"scale": rot((0, ONE), (RELEASE["throw"], ONE), (RELEASE["throw"] + 0.05, (0.2, 0.2, 0.2)),
                                   (0.95, (0.2, 0.2, 0.2)), (1.2, ONE))}
    out["throw"] = (1.2, "once", throw)
    # ---- prism: the arms rising, trembling through the warning, the burst
    prism_pose, _ = pose_deltas("prism")
    prism = {}
    r = RELEASE["prism"]
    for b, v in prism_pose.items():
        tremble = [(0.5 + 0.2 * i, add(v, (1.5 if i % 2 else -1.5, 0, 0))) for i in range(1, 5)]
        prism[b] = {"rotation": rot((0, ZERO), (0.5, v), *tremble, (r, scale3(v, 1.15)), (r + 0.15, v), (2.2, ZERO))}
    out["prism"] = (2.2, "once", prism)
    # ---- curtsey: the bow, the decoys at the release
    curt = into(curtsey, ((0, 0), (0.6, 0.8), (RELEASE["curtsey"], 1.0), (1.3, 1.0), (1.8, 0)))
    curt["hips"] = {"position": rot((0, ZERO), (RELEASE["curtsey"], (0, curtsey_drop, 0)), (1.3, (0, curtsey_drop, 0)),
                                    (1.8, ZERO))}
    out["curtsey"] = (1.8, "once", curt)
    # ---- blink: folding in and shrinking to the teleport, unfolding where he lands
    r = RELEASE["blink"]
    bl = into(blink, ((0, 0), (r, 1.0), (0.8, 0)))
    bl["hips"] = {"position": rot((0, ZERO), (r, (0, blink_drop, 0)), (0.8, ZERO)),
                  "scale": rot((0, ONE), (r - 0.05, (0.5, 0.5, 0.5)), (r, (0.05, 0.05, 0.05)),
                               (r + 0.05, (0.5, 0.5, 0.5)), (0.8, ONE))}
    out["blink"] = (0.8, "once", bl)
    # ---- laugh: the head thrown back, shaking
    laugh_pose, _ = pose_deltas("laugh")
    laugh = into(laugh_pose, ((0, 0), (0.25, 1.0), (1.1, 1.0), (1.4, 0)))
    nv = laugh_pose["neck"]
    laugh["neck"] = {"rotation": rot((0, ZERO), (0.25, nv), *[(0.25 + 0.12 * i, add(nv, (5 if i % 2 else -3, 0, 0)))
                                                              for i in range(1, 7)], (1.1, nv), (1.4, ZERO))}
    laugh["torso"] = {"rotation": rot((0, ZERO), (0.25, laugh_pose["torso"]),
                                      *[(0.25 + 0.12 * i, add(laugh_pose["torso"], (3 if i % 2 else -2, 0, 0)))
                                        for i in range(1, 7)], (1.1, laugh_pose["torso"]), (1.4, ZERO))}
    out["laugh"] = (1.4, "once", laugh)
    # ---- snap: the left hand raised, the snap
    r = RELEASE["snap"]
    snap = into(SNAP, ((0, 0), (0.35, 1.0), (r, 1.08), (0.7, 1.0), (1.0, 0)))
    snap["forearm_left"] = {"rotation": rot((0, ZERO), (0.35, (40, 0, 0)), (r, (58, 0, 0)), (0.7, (40, 0, 0)),
                                            (1.0, ZERO))}
    out["snap"] = (1.0, "once", snap)
    # ---- flinch
    out["flinch"] = (0.4, "once", {
        "torso": {"rotation": rot((0, ZERO), (0.08, (-10, 0, 4)), (0.4, ZERO))},
        "neck": {"rotation": rot((0, ZERO), (0.1, (14, 0, -6)), (0.4, ZERO))},
        "hat_left_0": {"rotation": rot((0, ZERO), (0.12, (0, 0, 14)), (0.4, ZERO))},
        "hat_right_0": {"rotation": rot((0, ZERO), (0.12, (0, 0, -14)), (0.4, ZERO))}})
    # ---- death: the strings cut
    death_pose, death_drop = pose_deltas("death")
    death = {b: {"rotation": rot((0, ZERO), (0.3, scale3(v, 0.25)), (0.9, scale3(v, 1.06)), (1.3, v), (2.6, v))}
             for b, v in death_pose.items()}
    death["hips"] = {"position": rot((0, ZERO), (0.3, (0, 1.0, 0)), (0.9, (0, death_drop, 0)),
                                     (1.1, (0, death_drop + 1.2, 0)), (1.3, (0, death_drop, 0)),
                                     (2.6, (0, death_drop, 0)))}
    out["death"] = (2.6, "hold", death)
    return out


# ---- the Jack-in-the-Box -----------------------------------------------------------------------------------------------

def spring_keys(*keys, interp="catmullrom"):
    """The spring's stretch k over time: the spring scaled in y, the clown's body moved with its top."""
    return ({"scale": [(t, (1, k, 1), interp) for t, k in keys]},
            [(t, (0, SPRING * (k - 1), 0), interp) for t, k in keys])


def jack_clips():
    out = {}
    closed = (-135, 0, 0)                      # the lid shut: from standing open (tilted back) down over the box
    hidden = (0.01, 0.01, 0.01)
    # ---- pop: shut, rattling, cranked; the lid flies open, the clown shoots up and wobbles
    r = JACK_RELEASE["pop"]
    sp, body_pos = spring_keys((0, 0.05), (r, 0.05), (r + 0.1, 1.35), (r + 0.22, 0.82), (r + 0.34, 1.1),
                               (r + 0.5, 1.0))
    out["pop"] = (2.0, "once", {
        "jack_box": {"rotation": lin(*[(0.1 * i, (0, 0, (3 if i % 2 else -3) if i < 15 else 0)) for i in range(16)],
                                     (2.0, ZERO)),
                     "scale": rot((0, ONE), (r - 0.05, (1.06, 0.92, 1.06)), (r + 0.08, (0.95, 1.08, 0.95)),
                                  (r + 0.25, ONE), (2.0, ONE))},
        "crank": {"rotation": lin(*[(r * i / 6, (-180 * i, 0, 0)) for i in range(7)], (2.0, (-1080, 0, 0)))},
        "lid": {"rotation": rot((0, closed), (r, closed), (r + 0.08, (18, 0, 0)), (r + 0.25, (-8, 0, 0)),
                                (r + 0.4, ZERO), (2.0, ZERO))},
        "spring": sp,
        "body": {"position": body_pos,
                 "scale": rot((0, hidden), (r, hidden), (r + 0.06, ONE), (2.0, ONE), interp="linear"),
                 "rotation": rot((0, ZERO), (r + 0.1, (-14, 0, 0)), (r + 0.22, (12, 0, 0)), (r + 0.34, (-5, 0, 0)),
                                 (r + 0.5, ZERO))},
        "hat_left": {"rotation": rot((0, ZERO), (r + 0.15, (0, 0, -24)), (r + 0.3, (0, 0, 14)), (2.0, ZERO))},
        "hat_right": {"rotation": rot((0, ZERO), (r + 0.15, (0, 0, 24)), (r + 0.3, (0, 0, -14)), (2.0, ZERO))},
    })

    # ---- bop: the idle bounce
    def bop(t0, low=0.7, high=1.12, length=0.6):
        q = length / 4
        return [(t0, 1.0), (t0 + q, low), (t0 + 2.2 * q, high), (t0 + length, 1.0)]
    sp, body_pos = spring_keys(*bop(0))
    out["bop"] = (0.6, "loop", {
        "spring": sp,
        "body": {"position": body_pos, "rotation": rot((0, ZERO), (0.15, (14, 0, 0)), (0.33, (-6, 0, 0)), (0.6, ZERO))},
        "hi_head": {"rotation": rot((0, ZERO), (0.18, (8, 0, 4)), (0.36, (-4, 0, -2)), (0.6, ZERO))},
        "hat_left": {"rotation": rot((0, ZERO), (0.2, (0, 0, 16)), (0.4, (0, 0, -8)), (0.6, ZERO))},
        "hat_right": {"rotation": rot((0, ZERO), (0.2, (0, 0, -16)), (0.4, (0, 0, 8)), (0.6, ZERO))},
        "arm_left": {"rotation": rot((0, ZERO), (0.15, (0, 0, -12)), (0.4, (0, 0, 6)), (0.6, ZERO))},
        "arm_right": {"rotation": rot((0, ZERO), (0.15, (0, 0, 12)), (0.4, (0, 0, -6)), (0.6, ZERO))},
    })
    # ---- throw: three bops, the stretch back, the flick
    r = JACK_RELEASE["throw"]
    keys = bop(0, 0.75, 1.08, 0.3)[:-1] + bop(0.3, 0.72, 1.1, 0.3)[:-1] + bop(0.6, 0.7, 1.12, 0.3)[:-1]
    sp, body_pos = spring_keys(*keys, (0.9, 1.0), (1.05, 1.28), (r, 1.18), (1.3, 0.92), (1.5, 1.0))
    out["throw"] = (1.5, "once", {
        "spring": sp,
        "body": {"position": body_pos,
                 "rotation": rot((0, ZERO), *[(0.3 * i + 0.08, (10, 0, 0)) for i in range(3)],
                                 (0.9, ZERO), (1.05, (-18, 0, 0)), (r, (16, 0, 0)), (1.3, (6, 0, 0)), (1.5, ZERO))},
        "arm_right": {"rotation": rot((0, ZERO), (0.9, (10, 0, 0)), (1.05, (60, 0, 0)), (r, (-80, 0, 0)),
                                      (1.3, (-60, 0, 0)), (1.5, ZERO))},
        "cards": {"scale": rot((0, ONE), (r, ONE), (r + 0.04, hidden), (1.4, hidden), (1.5, ONE), interp="linear")},
        "hat_left": {"rotation": rot((0, ZERO), (1.05, (0, 0, 20)), (r + 0.1, (0, 0, -18)), (1.5, ZERO))},
        "hat_right": {"rotation": rot((0, ZERO), (1.05, (0, 0, -20)), (r + 0.1, (0, 0, 18)), (1.5, ZERO))},
    })
    # ---- wind: sagging, drooping into the box, the lid slamming
    sp, body_pos = spring_keys((0, 1.0), (0.4, 0.8), (1.0, 0.3), (1.1, 0.05), (1.4, 0.05))
    out["wind"] = (1.4, "hold", {
        "spring": sp,
        "body": {"position": body_pos,
                 "rotation": rot((0, ZERO), (0.5, (20, 0, 6)), (1.0, (45, 0, 10)), (1.4, (45, 0, 10))),
                 "scale": rot((0, ONE), (1.05, ONE), (1.1, hidden), (1.4, hidden), interp="linear")},
        "hi_head": {"rotation": rot((0, ZERO), (0.8, (24, 0, 16)), (1.4, (24, 0, 16)))},
        "hat_left": {"rotation": rot((0, ZERO), (0.8, (0, 0, -30)), (1.4, (0, 0, -30)))},
        "hat_right": {"rotation": rot((0, ZERO), (0.8, (0, 0, 30)), (1.4, (0, 0, 30)))},
        "lid": {"rotation": rot((0, ZERO), (1.1, ZERO), (1.28, closed), (1.32, add(closed, (6, 0, 0))), (1.4, closed))},
    })
    # ---- death: the head pops off, the spring goes limp, the box bursts
    sp, body_pos = spring_keys((0, 1.0), (0.1, 1.3), (0.4, 0.6), (0.9, 0.6))
    sp["rotation"] = rot((0, ZERO), (0.15, (0, 0, -10)), (0.5, (0, 0, 34)), (0.9, (0, 0, 34)))
    out["death"] = (0.9, "hold", {
        "spring": sp,
        "body": {"position": body_pos, "rotation": rot((0, ZERO), (0.5, (40, 0, 30)), (0.9, (40, 0, 30)))},
        "hi_head": {"position": rot((0, ZERO), (0.25, (0, 14, 0)), (0.5, (0, 22, 0))),
                    "rotation": lin((0, ZERO), (0.5, (0, 0, 220))),
                    "scale": rot((0, ONE), (0.4, ONE), (0.5, hidden), (0.9, hidden), interp="linear")},
        "jack_box": {"scale": rot((0, ONE), (0.55, ONE), (0.68, (1.25, 1.25, 1.25)), (0.8, hidden), (0.9, hidden))},
        "lid": {"rotation": rot((0, ZERO), (0.6, (30, 0, 0)), (0.9, (30, 0, 0)))},
    })
    return out


# ---- export and previews ----------------------------------------------------------------------------------------------

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


def frame(model, bones, t, yaw=-35, pitch=12, size=(300, 400), scale=3.3, floor=0.92):
    mats = v7.matrices(model, bones, t)
    a, b = math.radians(yaw), math.radians(-pitch)
    ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    view = rx @ ry
    polys = []
    for c in model.cubes:
        if min(np.array(c.to) - np.array(c.frm)) < 0.01:
            continue                                   # the cards: flat planes, left out of the preview
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        v = (view @ (m @ pts)[:3]).T
        zone = s4.zone_for(c)
        ramp, shade = s5.ZONE[zone]
        ramp = s5.RAMP[ramp]
        base = np.array(ramp[min(shade, len(ramp) - 1)], float)
        glow = zone.startswith(s4.GLOWING)
        for face, idx in v7.QUADS.items():
            light = 1.0 if glow else v7.SHADE[face]
            col = tuple(int(min(255, x * light)) for x in base)
            polys.append((v[list(idx), 2].mean(), [(size[0] / 2 - p[0] * scale, size[1] * floor - p[1] * scale)
                                                    for p in v[list(idx)]], col))
    img = Image.new("RGB", size, (40, 38, 46))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, size[1] * floor + 1, size[0], size[1]), fill=(30, 28, 34))
    for _, pts, col in sorted(polys, key=lambda p: -p[0]):
        dr.polygon(pts, fill=col)
    return img


def previews(model, clip_set, out, title, release, size, scale, small_scale):
    (out / "gifs").mkdir(parents=True, exist_ok=True)
    stills = []
    for name, (length, loop, bones) in clip_set.items():
        frames = [frame(model, bones, t, size=size, scale=scale) for t in np.arange(0, length + 1e-6, 1 / 15)]
        frames[0].save(out / "gifs" / f"{name}.gif", save_all=True, append_images=frames[1:], duration=66, loop=0)
        if name in release:
            r = release[name]
            picks = [0, r * 0.5, r, min(length, r + 0.2), length]
        else:
            picks = [length * f for f in (0, 0.25, 0.5, 0.75, 1.0)]
        stills.append((name, [(t, frame(model, bones, t, size=(220, 290), scale=small_scale)) for t in picks]))
    tw, th, pad, top, left = 220, 290, 8, 54, 100
    img = Image.new("RGB", (left + 5 * (tw + pad), top + len(stills) * (th + 26 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"{title}: key frames (session 7); the GIFs show the motion", font=sheet._font(24),
            fill=sheet.INK)
    for r_, (name, row) in enumerate(stills):
        y = top + r_ * (th + 26 + pad)
        dr.text((pad, y + th // 2 - 10), name, font=sheet._font(19), fill=sheet.INK)
        for c, (t, im) in enumerate(row):
            img.paste(im, (left + c * (tw + pad), y))
            mark = " release" if name in release and abs(t - release[name]) < 1e-6 else ""
            dr.text((left + c * (tw + pad) + 4, y + th + 3), f"{t:.2f} s{mark}", font=sheet._font(15),
                    fill=sheet.DIM)
    img.save(out / "keyframes.png")


def check(model, clip_set, label):
    names = {g.name for g in model.groups}
    missing = sorted({b for _, _, bones in clip_set.values() for b in bones} - names)
    if missing:
        raise SystemExit(f"{label}: clips key bones the model doesn't have: {missing}")


def jack_rig(out):
    """The jack's shipped rig: painted with the Magus's painters, set on the ground at half size, its hitbox round the
    whole jack (box to hat)."""
    s2.MASK = "clown"
    build, hitbox = s2.build, s2.hitbox_bounds
    s2.build = lambda name: jack.build()
    try:
        model, keys, positions, used, height, atlas = s5.painted()
    finally:
        s2.build = build
    model.name = JACK_ID
    jack.settle(model)
    atlas_path = out / f"{JACK_ID}.png"
    atlas.save(atlas_path)
    s2.hitbox_bounds = lambda m: tuple(m.bounds())
    try:
        bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, {})
    finally:
        s2.hitbox_bounds = hitbox
    return model, bb


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    # the Magus
    s2.MASK = "clown"
    model = s2.build(s3.MODEL_ID)
    s2.finish(model)
    clip_set = magus_clips()
    check(model, clip_set, "magus")
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["animations"] = [a for a in rig["animations"] if a["name"] not in clip_set] + \
        blockbench_animations(s3.MODEL_ID, clip_set)
    path = OUT / f"{s3.MODEL_ID}.bbmodel"
    path.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    previews(model, clip_set, OUT / "magus", "Mirrored Magus", RELEASE, (300, 420), 3.3, 2.3)
    summary["magus"] = {k: {"length": v[0], "loop": v[1], "bones": len(v[2])} for k, v in clip_set.items()}
    # the jack
    jack_out = OUT / "jack"
    jack_out.mkdir(parents=True, exist_ok=True)
    jmodel, bb = jack_rig(jack_out)
    jclips = jack_clips()
    check(jmodel, jclips, "jack")
    bb["animations"] = blockbench_animations(JACK_ID, jclips)
    path = jack_out / f"{JACK_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)
    previews(jmodel, jclips, jack_out, "Jack-in-the-Box", JACK_RELEASE, (300, 360), 8.0, 6.0)
    summary["jack"] = {k: {"length": v[0], "loop": v[1], "bones": len(v[2])} for k, v in jclips.items()}
    (OUT / "clips.json").write_text(json.dumps({"release_seconds": {"magus": RELEASE, "jack": JACK_RELEASE},
                                                "clips": summary}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: len(v) for k, v in summary.items()}))


if __name__ == "__main__":
    main()
