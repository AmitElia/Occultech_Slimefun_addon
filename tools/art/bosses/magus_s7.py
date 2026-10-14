"""The Mirrored Magus redesign, session 7: animation - his clips and the Jack-in-the-Box's.

His clips are built from session 2's key poses (each bone's turn away from rest; the hips sink with a position key
where a pose sits him lower). Timings follow MirroredMagus.java and the jack's design (overhaul/jack/README.md).
Animation is cosmetic: every hit and telegraph comes from the server, and session 8 starts each action clip so its
release lands on the server's real moment.

The Magus (`occultech_mirrored_magus_rig`), take 2 - a marionette that isn't quite alive (magus_clips() describes
each clip): idle 4.0 s loop, walk 2.0 s loop, spawn 3.4 s, throw 1.4 s (release 0.6), prism 2.4 s (1.5), curtsey 2.0 s
(1.0), blink 0.9 s (0.45), laugh 1.8 s, snap 1.2 s (0.6), flinch 0.6 s, death 3.0 s hold.

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
RELEASE = {"throw": 0.6, "prism": 1.5, "curtsey": 1.0, "blink": 0.45, "snap": 0.6}
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


C, L, S = "catmullrom", "linear", "step"


def track(*keys):
    """Keys as (time, value, interpolation): holds (step), snaps (linear) and eases (catmullrom), mixed."""
    return [(t, v, i) for t, v, i in keys]


def jitter(base, t0, t1, amp, every=0.06, axis=0):
    """A trembling hold: the value shaken back and forth from t0 to t1."""
    out, t, k = [], t0, 0
    while t < t1 - 1e-6:
        v = list(base)
        v[axis] += amp if k % 2 else -amp
        out.append((round(t, 3), tuple(v), L))
        t += every
        k += 1
    return out


def flop(clip, length, amp, lag=0.12, beats=1):
    """The hat's three points flopping, each segment lagging the one before (a whip)."""
    for name, sign, axis in (("hat_left", 1, 2), ("hat_right", -1, 2), ("hat_back", 1, 0)):
        for j in range(3):
            keys = []
            for i in range(4 * beats + 1):
                t = length * i / (4 * beats)
                v = [0, 0, 0]
                v[axis] = sign * amp * (1 + 0.5 * j) * (1, 0.2, -0.8, 0.2)[i % 4]
                keys.append((min(length, t + lag * j) if 0 < i < 4 * beats else t, tuple(v)))
            clip.setdefault(f"{name}_{j}", {})["rotation"] = rot(*keys)


def magus_clips():
    """His clips, take 2 (the user: the first take was too stiff and robotic, not horror; the knees bent the wrong
    way): a marionette that isn't quite alive. Long unnatural stillness broken by sudden jerks and snapped head tilts,
    holds that last a beat too long, trembling, a limping lurch with a dragged foot, a bow too deep with his face still
    staring up at you, a head that turns all the way round."""
    out = {}
    # ---- idle: hanging from his strings, swaying; the head snaps to a cocked tilt, holds, snaps the other way
    idle = {
        "hips": {"position": rot((0, (0, -0.8, 0)), (1.0, (0, -1.3, 0)), (2.0, (0, -0.8, 0)), (3.0, (0, -1.3, 0)),
                                 (4.0, (0, -0.8, 0)))},
        "torso": {"rotation": rot((0, (-10, 0, 4)), (2.0, (-8, 0, -4)), (4.0, (-10, 0, 4)))},
        "neck": {"rotation": track((0, (8, 0, 14), C), (1.15, (8, 2, 16), L), (1.2, (4, 28, 42), S),
                                   (1.9, (4, 28, 42), L), (1.97, (14, -12, -16), C), (2.9, (12, -8, -10), S),
                                   (3.05, (12, -8, -4), C), (4.0, (8, 0, 14), C))},
        "leg_left": {"rotation": rot((0, (6, 0, -2)), (4.0, (6, 0, -2)))},
        "leg_right": {"rotation": rot((0, (6, 0, 2)), (4.0, (6, 0, 2)))},
        "shin_left": {"rotation": rot((0, (-12, 0, 0)), (4.0, (-12, 0, 0)))},
        "shin_right": {"rotation": rot((0, (-12, 0, 0)), (4.0, (-12, 0, 0)))},
        "arm_left": {"rotation": rot((0, (4, 0, -4)), (1.0, (-6, 0, -2)), (2.0, (8, 0, -6)), (3.0, (-4, 0, -2)),
                                     (4.0, (4, 0, -4)))},
        "forearm_left": {"rotation": rot((0, (10, 0, 0)), (1.3, (2, 0, 0)), (2.3, (16, 0, 0)), (3.3, (4, 0, 0)),
                                         (4.0, (10, 0, 0)))},
        "arm_right": {"rotation": rot((0, (12, 0, 8)), (2.0, (6, 0, 10)), (4.0, (12, 0, 8)))},
        "forearm_right": {"rotation": rot((0, (10, 0, 0)), (2.2, (18, 0, 0)), (4.0, (10, 0, 0)))},
    }
    flop(idle, 4.0, 6)
    out["idle"] = (4.0, "loop", idle)
    # ---- walk: a marionette's limping lurch - the left leg yanked up high, the right foot dragged behind; the head
    # held on its target while the body rolls under it, with a twitch every cycle
    walk = {
        "hips": {"position": rot((0, (0, -0.6, 0)), (0.35, (0, 2.2, 0)), (1.0, (0, -1.4, 0)), (1.5, (0, -0.8, 0)),
                                 (2.0, (0, -0.6, 0))),
                 "rotation": rot((0, (0, 8, -5)), (0.5, (0, 2, 7)), (1.0, (0, -8, 4)), (1.5, (0, -4, -6)),
                                 (2.0, (0, 8, -5)))},
        "torso": {"rotation": rot((0, (-18, -4, 6)), (0.5, (-22, 0, -8)), (1.0, (-16, 6, -4)), (1.5, (-20, 2, 7)),
                                  (2.0, (-18, -4, 6)))},
        "neck": {"rotation": track((0, (14, -4, 0), C), (0.5, (18, -2, 2), C), (1.0, (12, 4, -2), C),
                                   (1.45, (12, 4, -2), L), (1.5, (8, 26, 30), S), (1.75, (8, 26, 30), L),
                                   (1.82, (14, -4, 0), C), (2.0, (14, -4, 0), C))},
        "leg_left": {"rotation": rot((0, (-22, 0, 0)), (0.35, (50, 0, -4)), (0.7, (30, 0, 0)), (1.0, (24, 0, 0)),
                                     (2.0, (-22, 0, 0)))},
        "shin_left": {"rotation": rot((0, (-10, 0, 0)), (0.22, (-80, 0, 0)), (0.55, (-34, 0, 0)), (0.8, (-4, 0, 0)),
                                      (1.4, (-6, 0, 0)), (2.0, (-10, 0, 0)))},
        "leg_right": {"rotation": rot((0, (26, 0, 0)), (1.0, (-24, 0, 4)), (1.6, (4, 0, 2)), (2.0, (26, 0, 0)))},
        "shin_right": {"rotation": rot((0, (-4, 0, 0)), (1.0, (-12, 0, 0)), (1.3, (-28, 0, 0)), (1.7, (-14, 0, 0)),
                                       (2.0, (-4, 0, 0)))},
        "arm_left": {"rotation": rot((0, (-26, 0, -4)), (0.6, (-8, 0, -10)), (1.0, (14, 0, -4)), (1.6, (-4, 0, -8)),
                                     (2.0, (-26, 0, -4)))},
        "forearm_left": {"rotation": rot((0, (4, 0, 0)), (0.4, (30, 0, 0)), (1.2, (6, 0, 0)), (1.6, (26, 0, 0)),
                                         (2.0, (4, 0, 0)))},
        "arm_right": {"rotation": rot((0, (18, 0, 8)), (1.0, (-16, 0, 10)), (2.0, (18, 0, 8)))},
        "forearm_right": {"rotation": rot((0, (20, 0, 0)), (0.5, (6, 0, 0)), (1.4, (28, 0, 0)), (2.0, (20, 0, 0)))},
    }
    flop(walk, 2.0, 10, lag=0.1, beats=2)
    out["walk"] = (2.0, "loop", walk)
    # ---- spawn: crumpled on the floor, pulled up by his strings in jerks - the body, the legs, the arms yanked
    # overhead with the wrists dangling, the head last; it snaps sideways, holds, snaps upright; a too-deep bow
    death, death_drop = pose_deltas("death")
    curtsey, curtsey_drop = pose_deltas("curtsey")
    spawn = {}
    lift = ((0, 1.0), (0.45, 1.0), (0.5, 0.55), (0.85, 0.55), (0.9, 0.2), (1.25, 0.2), (1.3, 0.0))
    for b, v in death.items():
        if b.startswith(("leg_", "shin_", "coat")):
            spawn[b] = {"rotation": track(*[(t, scale3(v, w), L) for t, w in lift], (3.4, ZERO, C))}
    tv = death.get("torso", ZERO)
    spawn["torso"] = {"rotation": track(*[(t, scale3(tv, w), L) for t, w in lift], (2.3, ZERO, C),
                                        (2.7, (-60, 0, 0), C), (3.0, (-60, 0, 0), C), (3.4, ZERO, C))}
    spawn["hips"] = {"position": track((0, (0, death_drop, 0), L), (0.45, (0, death_drop, 0), L),
                                       (0.5, (0, death_drop * 0.5 + 3, 0), C), (0.9, (0, 2.5, 0), L),
                                       (1.3, (0, 1.5, 0), C), (2.3, (0, 1.5, 0), C), (2.6, ZERO, C),
                                       (3.4, ZERO, C))}
    for side, sx in (("left", -1), ("right", 1)):
        a0, f0 = death.get(f"arm_{side}", ZERO), death.get(f"forearm_{side}", ZERO)
        spawn[f"arm_{side}"] = {"rotation": track((0, a0, L), (1.3, a0, L), (1.38, (165, 0, sx * 18), C),
                                                  (2.3, (160, 0, sx * 22), L), (2.45, (10, 0, sx * 6), C),
                                                  (3.4, ZERO, C))}
        spawn[f"forearm_{side}"] = {"rotation": track((0, f0, L), (1.3, f0, L), (1.38, (40, 0, 0), C),
                                                      (2.3, (50, 0, 0), L), (2.45, (20, 0, 0), C), (3.4, ZERO, C))}
    spawn["neck"] = {"rotation": track((0, death["neck"], L), (1.7, death["neck"], L), (1.75, (-10, 0, 72), S),
                                       (2.3, (-10, 0, 72), L), (2.35, (6, 0, 0), C), (2.7, (40, 0, 0), C),
                                       (3.0, (40, 0, 0), C), (3.4, ZERO, C))}
    flop(spawn, 3.4, 12, lag=0.15, beats=2)
    out["spawn"] = (3.4, "once", spawn)
    # ---- throw: a slow, coiled wind-up, his head cocked after the arm; the whip; a twisted hold, trembling; a jerky
    # return
    tp, _ = pose_deltas("throw")
    r = RELEASE["throw"]
    throw = {}
    for b, v in tp.items():
        coiled = b.startswith(("arm_right", "torso", "hips"))
        wind = (-0.45 * v[0], -0.6 * v[1], -0.3 * v[2]) if coiled else scale3(v, 0.3)
        throw[b] = {"rotation": track((0, ZERO, C), (0.45, wind, L), (r, scale3(v, 1.15), L),
                                      *jitter(scale3(v, 1.1), r + 0.04, 0.95, 1.5), (0.95, scale3(v, 1.0), S),
                                      (1.05, scale3(v, 0.45), C), (1.4, ZERO, C))}
    throw["neck"] = {"rotation": track((0, ZERO, C), (0.45, (0, -24, 26), L), (r, (-6, 40, -10), S),
                                       (0.95, (-6, 40, -10), L), (1.0, (6, 30, 24), C), (1.4, ZERO, C))}
    throw["cards"] = {"scale": rot((0, ONE), (r, ONE), (r + 0.05, (0.2, 0.2, 0.2)), (1.15, (0.2, 0.2, 0.2)),
                                   (1.4, ONE))}
    out["throw"] = (1.4, "once", throw)
    # ---- prism: he rises off the floor, toes dangling, arms lifting slowly with the cards, his head lolled back and
    # twitching; trembling all over through the warning; the burst snaps his face down at you; he drops
    pp, _ = pose_deltas("prism")
    r = RELEASE["prism"]
    prism = {b: {"rotation": track((0, ZERO, C), (0.7, v, C), *jitter(v, 0.75, r, 2.0, 0.05),
                                   (r, scale3(v, 1.15), L), (r + 0.12, scale3(v, 1.05), C), (2.0, scale3(v, 0.3), C),
                                   (2.4, ZERO, C))}
             for b, v in pp.items() if b != "neck"}
    prism["neck"] = {"rotation": track((0, ZERO, C), (0.6, (40, 0, 8), C), (0.8, (40, 0, 8), L),
                                       (0.84, (44, 10, -16), S), (1.1, (44, 10, -16), L), (1.14, (38, -12, 18), S),
                                       (r, (38, -12, 18), L), (r + 0.06, (-18, 0, 0), C), (2.4, ZERO, C))}
    prism["hips"] = {"position": rot((0, ZERO), (1.2, (0, 4.5, 0)), (r, (0, 5, 0)), (r + 0.25, ZERO),
                                     (1.95, (0, -1.5, 0)), (2.4, ZERO))}
    for side in ("left", "right"):
        prism[f"leg_{side}"] = {"rotation": rot((0, ZERO), (1.0, (-8, 0, 0)), (r, (-10, 0, 0)),
                                                (r + 0.25, (10, 0, 0)), (2.4, ZERO))}
        prism[f"shin_{side}"] = {"rotation": rot((0, ZERO), (1.0, (-24, 0, 0)), (r, (-26, 0, 0)),
                                                 (r + 0.4, (-36, 0, 0)), (2.4, ZERO))}
    out["prism"] = (2.4, "once", prism)
    # ---- curtsey: a bow far too deep, his face still turned up staring at you; a long hold, a twitch, a snap upright
    r = RELEASE["curtsey"]
    deep = dict(curtsey, torso=(-72, 0, 0), neck=(64, 0, 0))
    curt = {b: {"rotation": track((0, ZERO, C), (0.7, scale3(v, 0.9), C), (r, v, C), (1.5, v, L),
                                  (1.58, scale3(v, 0.15), C), (2.0, ZERO, C))} for b, v in deep.items()}
    curt["neck"]["rotation"] = track((0, ZERO, C), (0.7, (56, 0, 0), C), (r, (64, 0, 0), L), (1.2, (64, 0, 0), L),
                                     (1.24, (62, 18, 24), S), (1.5, (62, 18, 24), L), (1.58, (8, 0, 0), C),
                                     (2.0, ZERO, C))
    curt["hips"] = {"position": rot((0, ZERO), (r, (0, curtsey_drop - 1.5, 0)), (1.5, (0, curtsey_drop - 1.5, 0)),
                                    (1.62, ZERO), (2.0, ZERO))}
    out["curtsey"] = (2.0, "once", curt)
    # ---- blink: he folds into a crouch as his head turns all the way round, shrinking to nothing; where he lands he
    # unfolds with the head turning back the other way
    blink, blink_drop = pose_deltas("blink")
    r = RELEASE["blink"]
    bl = into(blink, ((0, 0), (r, 1.0), (0.9, 0)))
    bl["hi_head"] = {"rotation": track((0, ZERO, L), (r, (0, 180, 0), L), (r + 0.001, (0, -180, 0), L),
                                       (0.9, ZERO, C))}
    bl["hips"] = {"position": rot((0, ZERO), (r, (0, blink_drop, 0)), (0.9, ZERO)),
                  "scale": rot((0, ONE), (r - 0.1, (0.6, 0.6, 0.6)), (r, (0.05, 0.05, 0.05)),
                               (r + 0.1, (0.6, 0.6, 0.6)), (0.75, (1.06, 1.06, 1.06)), (0.9, ONE))}
    out["blink"] = (0.9, "once", bl)
    # ---- laugh: his head thrown back, convulsing - shoulders jerking, the head bobbing, a hand clutching his belly;
    # it stops dead and his face snaps down to stare at you
    lp, _ = pose_deltas("laugh")
    laugh = {b: {"rotation": track((0, ZERO, C), (0.2, v, L), (1.3, v, L), (1.36, ZERO, C), (1.8, ZERO, C))}
             for b, v in lp.items() if not b.startswith(("neck", "torso", "arm_", "forearm_"))}
    laugh["neck"] = {"rotation": track((0, ZERO, C), (0.2, (36, 0, -10), L), *jitter((36, 0, -10), 0.24, 1.3, 7, 0.09),
                                       (1.3, (-16, 0, 6), S), (1.55, (-16, 0, 6), C), (1.8, ZERO, C))}
    laugh["torso"] = {"rotation": track((0, ZERO, C), (0.2, (14, 0, 0), L), *jitter((14, 0, 0), 0.24, 1.3, 5, 0.09),
                                        (1.3, (-8, 0, 0), S), (1.55, (-8, 0, 0), C), (1.8, ZERO, C))}
    laugh["arm_left"] = {"rotation": track((0, ZERO, C), (0.25, (44, 0, 34), C),
                                           *jitter((44, 0, 34), 0.3, 1.3, 4, 0.09, axis=2), (1.8, ZERO, C))}
    laugh["forearm_left"] = {"rotation": rot((0, ZERO), (0.25, (90, 0, 0)), (1.3, (90, 0, 0)), (1.8, ZERO))}
    laugh["arm_right"] = {"rotation": track((0, ZERO, C), (0.25, (40, 0, -30), C),       # both hands clutch inwards
                                            *jitter((40, 0, -30), 0.3, 1.3, 4, 0.09, axis=2), (1.8, ZERO, C))}
    laugh["forearm_right"] = {"rotation": rot((0, ZERO), (0.25, (80, 0, 0)), (1.3, (80, 0, 0)), (1.8, ZERO))}
    out["laugh"] = (1.8, "once", laugh)
    # ---- snap: the left hand rising slowly, his head tilting after it; the snap jolts his whole body; his head jerks
    # round to stare at you
    r = RELEASE["snap"]
    snap = into(SNAP, ((0, 0), (0.45, 0.9), (r, 1.08), (0.85, 1.0), (1.2, 0)))
    snap["forearm_left"] = {"rotation": track((0, ZERO, C), (0.45, (36, 0, 0), C), (r, (64, 0, 0), L),
                                              (r + 0.08, (40, 0, 0), C), (1.2, ZERO, C))}
    snap["neck"] = {"rotation": track((0, ZERO, C), (0.45, (-4, -26, -30), C), (r, (-6, -30, -34), L),
                                      (0.7, (-6, -30, -34), L), (0.74, (6, 6, 22), S), (1.0, (6, 6, 22), C),
                                      (1.2, ZERO, C))}
    snap["torso"] = {"rotation": track((0, ZERO, C), (0.45, (4, 8, 0), C), (r, (4, 8, 0), L),
                                       (r + 0.05, (12, 0, 6), L), (r + 0.15, (2, 6, 0), C), (1.2, ZERO, C))}
    out["snap"] = (1.2, "once", snap)
    # ---- flinch: a violent jerk, the head snapped sideways; it turns back slowly, with one twitch
    out["flinch"] = (0.6, "once", {
        "torso": {"rotation": track((0, ZERO, L), (0.05, (-14, 6, 8), C), (0.6, ZERO, C))},
        "neck": {"rotation": track((0, ZERO, L), (0.06, (-10, 34, -40), L), (0.3, (-8, 26, -30), S),
                                   (0.36, (-6, 14, -18), C), (0.6, ZERO, C))},
        "arm_left": {"rotation": track((0, ZERO, L), (0.06, (-20, 0, -24), C), (0.6, ZERO, C))},
        "arm_right": {"rotation": track((0, ZERO, L), (0.06, (-14, 0, 26), C), (0.6, ZERO, C))},
        "hat_left_0": {"rotation": rot((0, ZERO), (0.12, (0, 0, 22)), (0.6, ZERO))},
        "hat_right_0": {"rotation": rot((0, ZERO), (0.12, (0, 0, -22)), (0.6, ZERO))}})
    # ---- death: the strings jerk taut - arms flung out, head thrown back - then cut: he drops like dead weight into
    # the slump; a pause; a last twitch of the arm, then of the head
    tense = {"torso": (12, 0, 0), "neck": (34, 0, 0), "arm_left": (20, 0, -70), "arm_right": (20, 0, 70),
             "forearm_left": ZERO, "forearm_right": ZERO}
    death_c = {}
    for b in set(death) | set(tense):
        v = death.get(b, ZERO)
        keys = [(0, ZERO, L), (0.12, tense.get(b, ZERO), L), (0.2, tense.get(b, ZERO), L),
                (0.55, scale3(v, 1.08), C), (0.75, v, C)]
        if b == "forearm_right":
            keys += [(1.8, v, L), (1.85, add(v, (-30, 0, 0)), S), (1.95, add(v, (-30, 0, 0)), L), (2.0, v, C)]
        if b == "neck":
            v2 = add(v, (-12, 10, 14))
            keys += [(2.2, v, L), (2.25, v2, S), (3.0, v2, C)]
        else:
            keys.append((3.0, v, C))
        death_c[b] = {"rotation": track(*keys)}
    death_c["hips"] = {"position": track((0, ZERO, L), (0.12, (0, 2.0, 0), L), (0.2, (0, 2.0, 0), L),
                                         (0.55, (0, death_drop, 0), L), (0.65, (0, death_drop + 1.0, 0), C),
                                         (0.75, (0, death_drop, 0), C), (3.0, (0, death_drop, 0), C))}
    out["death"] = (3.0, "hold", death_c)
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
