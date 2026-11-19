"""Heartwood Horror, session 7: the clips themselves (the motion system is heartwood_s7.py).

Every arm is keyed as points in world space, from the shoulder out to the hand (model units; it faces -z, its right
is +x, the floor is y 0). Points near the shoulder ride along with the body; the hand stays where it is keyed, so
planted and dragging hands stay put. Ease names: smooth, in (strike), out (settle), back (overshoot), snap (a
creaking jerk), linear.
"""
import math

import numpy as np

from bosses import heartwood_s6 as s6
from bosses.heartwood_s7 import ARM0, BIND, SHOULDER0, Clip, N, SPEED, clamp01, pose, smooth

CR, GR, LE, TH, BK = (ARM0[k] for k in ("crutch", "great", "lesser", "thin", "back"))


def bump(t, at, width):
    """0 -> 1 -> 0 round `at`, a smooth hump `width` wide."""
    x = (t - at) / width
    return math.cos(x * math.pi / 2) ** 2 if abs(x) < 1 else 0.0


def arm_pts(P, key):
    return P["arm:" + key].reshape(N, 3)


def nudge_arm(P, key, d, weights=None):
    pts = arm_pts(P, key)
    w = weights if weights is not None else [i / (N - 1) for i in range(N)]
    for i in range(N):
        pts[i] += np.array(d, float) * w[i]
    P["arm:" + key] = pts.reshape(-1)


def tremor(t, amp, seed=0):
    return amp * np.array([math.sin(t * 37 + seed), math.sin(t * 43 + seed * 2.1), math.sin(t * 31 + seed * 3.3)])


# ---- idle ------------------------------------------------------------------------------------------------------------------

def idle_layer(t, P):
    b = math.sin(2 * math.pi * t / 4.0)                    # one slow breath every 4 s
    P["trunk"][1] += -1.6 * b
    P["trunk"][2] += -0.8 * b
    P["trunk"][5] += 1.5 * math.sin(2 * math.pi * t / 4.0 + 1.2)
    P["hips"][0] += -0.8 * b
    for k, ph in (("great", 0.0), ("lesser", 1.7), ("back", 3.1), ("crutch", 4.4)):
        nudge_arm(P, k, (0, 2.5 * math.sin(2 * math.pi * t / 4.0 + ph), 0), [0.3, 0.8, 0.6, 0.3, 0.0])
    nudge_arm(P, "thin", (3 * math.sin(2 * math.pi * t / 4.0 + 0.6), 0, 2 * math.cos(2 * math.pi * t / 4.0)))
    k = bump(t, 2.72, 0.12) if t < 2.72 else clamp01(1 - (t - 2.72) / 0.6) * (t < 3.32)
    nudge_arm(P, "thin", (6 * k, 5 * k, -4 * k))           # a sudden creaking twitch, eased back
    P["trunk"][3] += 1.2 * k
    P["lantern"] = np.array([10 * math.sin(2 * math.pi * t / 4.0), 0, 6 * math.cos(2 * math.pi * t / 4.0)])
    return P


IDLE = Clip("idle", 4.0, "loop", [(0.0, BIND, "smooth")], idle_layer)

# ---- walk ------------------------------------------------------------------------------------------------------------------

STRIDE = SPEED * 1.5                       # each foot and the crutch stand on the floor 1.5 s of the 2 s cycle


def foot_track(t, x, z_mid, swing0, swing1, lift=13.0):
    """An in-place gait foot: planted and sliding back at the walk speed, then swung ahead."""
    T = 2.0
    t = t % T
    plant = swing1
    if swing0 <= t < swing1:
        s = smooth((t - swing0) / (swing1 - swing0))
        z = (z_mid + STRIDE / 2) + (-STRIDE) * s
        return np.array([x, 2 + lift * math.sin(math.pi * s), z]), s
    since = (t - plant) % T
    return np.array([x, 2.0, z_mid - STRIDE / 2 + SPEED * since]), None


def walk_layer(t, P):
    T = 2.0
    ph = t % T
    # the crutch: swung ahead 0.0-0.5, planted and sliding back the rest
    hand, s = foot_track(ph, -43, -68, 0.0, 0.5, lift=22.0)
    hand[1] += 7
    pts = arm_pts(P, "crutch") + SHOULDER0["crutch"]
    d = hand - pts[-1]
    for i, w in enumerate((0.0, 0.25, 0.55, 0.85, 1.0)):
        pts[i] += d * w
    if s is not None:
        pts[2] += np.array([-4, 8, -4]) * math.sin(math.pi * s)
    P["arm:crutch"] = (pts - SHOULDER0["crutch"]).reshape(-1)
    # the legs
    for side, x, z_mid, s0, s1 in (("right", 15, 8, 0.8, 1.3), ("left", -16, 10, 1.3, 1.8)):
        foot, _ = foot_track(ph, x, z_mid, s0, s1)
        P["leg:" + side][:3] = foot
    # the body vaults over the crutch, then dips onto each foot
    P["hips"][0] += 1.6 * bump(ph, 0.75, 0.3) - 2.6 * bump(ph, 1.38, 0.18) - 2.6 * bump(ph, 1.88, 0.18)
    P["hips"][1] += -3.0 * bump(ph, 0.8, 0.4)
    P["trunk"][1] += -3.5 * bump(ph, 0.8, 0.35) + 1.2 * bump(ph, 1.4, 0.2) + 1.2 * bump(ph, 1.9, 0.2)
    P["trunk"][5] += 3.0 * math.sin(2 * math.pi * (ph - 0.6) / T)
    P["hips"][4] += 2.0 * math.sin(2 * math.pi * (ph - 0.6) / T)
    # the dragging hands slide along with the body (still in model space); their elbows rock
    for k, phase in (("great", 0.0), ("lesser", 0.9), ("back", 0.4)):
        nudge_arm(P, k, (2.5 * math.sin(2 * math.pi * (ph / T + phase)), 3 * math.sin(2 * math.pi * (ph / T + phase + 0.25)),
                         0), [0.2, 0.7, 0.8, 0.4, 0.0])
    nudge_arm(P, "thin", (4 * math.sin(2 * math.pi * (ph - 0.9) / T), 0, 3 * math.cos(2 * math.pi * (ph - 0.9) / T)))
    return P


WALK = Clip("walk", 2.0, "loop", [(0.0, BIND, "smooth")], walk_layer)

# ---- spawn ---------------------------------------------------------------------------------------------------------------

FOLD = pose(hips=(-34, 6, 0, 0, 0), trunk=(-14, -6, 4, 6, 0, 0, 0),
            arms={"crutch": ([(-32, 76, -34), (-44, 64, -38), (-46, 34, -42), (-40, 6, -44)], (0, 0, -1), -25),
                  "great": ([(32, 76, -34), (44, 64, -36), (46, 34, -40), (40, 6, -44)], (0.3, 0, -1)),
                  "lesser": ([(34, 86, -6), (50, 74, 0), (56, 40, 8), (54, 6, 14)], (0.5, 0, 1)),
                  "thin": ([(18, 110, 14), (28, 104, 24), (32, 84, 30)], (0, -1, 0.3)),
                  "back": ([(-10, 112, 12), (-24, 108, 24), (-34, 84, 30), (-34, 48, 30), (-30, 8, 30)],
                           (-0.4, 0, 1))},
            legs={"right": ((17, 2, 4), (0, 0.45, 1), (0.3, 0, -1)), "left": ((-18, 2, 8), (0, 0.45, 1), (-0.3, 0, -1))})
RISE1 = pose(FOLD, hips=(-22, 4, 0, 0, 0), trunk=(-12, -8, 0, 0, 0, 0, 0),
             arms={"crutch": (CR, (0, 0, -1), -25)},
             legs={"right": ((16, 2, 6), (0, 0.8, 1), (0, 0, -20)), "left": ((-17, 2, 9), (0, 0.8, 1), (0, 0, -20))})
RISE2 = pose(RISE1, hips=(-8, 2, 0, 0, 0), trunk=(-6, -4, 0, 0, 0, 0, 0),
             arms={"great": (GR, (0, 0, 1)), "lesser": (LE, (0, 0, 1))}, legs={})
RISE2["leg:right"], RISE2["leg:left"] = BIND["leg:right"].copy(), BIND["leg:left"].copy()
RISE3 = pose(RISE2, hips=(0, 0, 0, 0, 0), trunk=(0, 0, 0, 0, 0, 0, 0),
             arms={"back": (BK, (0, 0, 1)), "thin": (TH, (0, -1, 0.3))})
ROAR = pose(RISE3, hips=(3, 4, 0, 0, 0), trunk=(12, 7, 3, -10, -12, 0, 0),
            arms={"great": ([(32, 116, -18), (48, 136, -6), (62, 146, 8), (70, 140, 24)], (1, 0.3, 0.3)),
                  "back": ([(-16, 126, 10), (-34, 140, 18), (-52, 142, 28), (-62, 132, 42)], (-1, 0.3, 0.3)),
                  "thin": ([(20, 116, 10), (34, 118, 26), (44, 100, 40), (46, 72, 50), (42, 46, 56)], (0, -1, 0.3))},
            lantern=(0, 0, 160))
SETTLE = pose(BIND, trunk=(-3, -2, 0, 0, 0, 0, 0), hips=(-1.5, 0, 0, 0, 0))


def spawn_layer(t, P):
    k = bump(t, 0.8, 0.6) + bump(t, 0.25, 0.25)            # shudders while still folded
    P["trunk"][1] += tremor(t, 1.6 * k)[0]
    P["hips"][0] += tremor(t, 0.8 * k, 2)[1]
    return P


SPAWN = Clip("spawn", 4.2, "once", [(0.0, FOLD, "smooth"), (1.2, FOLD, "linear"), (1.75, RISE1, "out"),
                                    (2.2, RISE2, "smooth"), (2.55, RISE3, "smooth"), (2.8, ROAR, "back"),
                                    (3.4, SETTLE, "smooth"), (4.2, BIND, "smooth")], spawn_layer, contact=2.8)

# ---- swipe -----------------------------------------------------------------------------------------------------------------

WIND = pose(hips=(0, 3, 0, 0, 0), trunk=(8, 4, 0, -6, -6, -14, 0),
            arms={"great": ([(34, 116, -22), (52, 136, -14), (64, 150, -2), (68, 148, 14), (64, 136, 22)],
                            (0.3, 0.8, 0.5), 0)},
            lantern=(0, 0, 90))
CHOP = pose(hips=(-4, -6, 0, 0, 0), trunk=(-12, -6, 0, 0, 0, 10, 0),
            arms={"great": ([(32, 104, -40), (40, 90, -66), (38, 58, -88), (32, 26, -100), (28, 8, -104)],
                            (0, -0.3, -1), -40)},
            lantern=(0, 0, -180))
DIG = pose(CHOP, trunk=(-14, -7, 0, 0, 0, 12, 0), hips=(-5, -7, 0, 0, 0),
           arms={"great": ([(32, 102, -42), (40, 88, -68), (38, 56, -90), (32, 24, -104), (28, 7, -108)],
                           (0, -0.3, -1), -45)})
ROUND = pose(trunk=(-3, -2, 0, 0, 0, 4, 0),
             arms={"great": ([(34, 104, -24), (54, 102, -20), (68, 74, -6), (66, 38, 14), (58, 10, 32)], (0.3, 0, 1))})
SWIPE = Clip("swipe", 1.4, "once", [(0.0, BIND, "smooth"), (0.35, WIND, "out"), (0.55, CHOP, "in"),
                                    (0.72, DIG, "back"), (1.02, ROUND, "smooth"), (1.4, BIND, "smooth")], contact=0.55,
             lag=0.012, dt=0.025)

# ---- lunge (the creak's arrival) ----------------------------------------------------------------------------------------

COIL = pose(hips=(-14, 8, 0, 0, 0), trunk=(-4, 6, 2, 0, 0, -6, 0),
            arms={"great": ([(34, 96, -14), (54, 92, 0), (60, 66, 14), (58, 40, 20), (54, 22, 18)], (0, -0.4, -1), 0),
                  "crutch": ([(-32, 92, -28), (-44, 84, -40), (-46, 50, -50), (-42, 22, -54), (-40, 9, -54)],
                             (0, 0, -1), -25)},
            legs={"right": ((17, 2, 2), (0, 0.6, 1), (0, 0, -20)), "left": ((-18, 2, 12), (0, 0.6, 1), (0, 0, -20))})
STAB = pose(hips=(-2, -14, 0, 0, 0), trunk=(-16, -8, 0, 0, 0, 4, 0),
            arms={"great": ([(30, 96, -46), (30, 86, -76), (26, 72, -106), (22, 60, -128), (18, 52, -142)],
                            (0, -0.2, -1), -10),
                  "crutch": ([(-34, 96, -40), (-44, 84, -60), (-44, 48, -76), (-40, 22, -82), (-38, 9, -84)],
                             (0, 0, -1), -25)},
            legs={"right": ((16, 2, -10), (0, 0.9, 1), (0, 0, -20)), "left": ((-16, 2, 24), (0, 0.6, 1), (0, 0, -20))},
            lantern=(0, 0, -220))
LUNGE_BACK = pose(arms={"great": ([(34, 104, -30), (56, 102, -30), (70, 74, -16), (68, 38, 6), (60, 10, 26)],
                                  (0.3, 0, 1))})
LUNGE = Clip("lunge", 1.2, "once", [(0.0, COIL, "smooth"), (0.3, STAB, "in"), (0.45, STAB, "back"),
                                    (0.8, LUNGE_BACK, "smooth"), (1.2, BIND, "smooth")], contact=0.3, lag=0.012,
             dt=0.025)

# ---- creak --------------------------------------------------------------------------------------------------------------

J1 = pose(trunk=(0, 4, -3, 0, 0, 3, 0), arms={"thin": ([(18, 122, 6), (30, 126, 18), (38, 110, 30), (40, 84, 40)],
                                                       (0, -1, 0.3))})
J2 = pose(J1, hips=(-6, 0, 0, 0, 0), trunk=(-6, -4, 0, 0, 0, -4, 0), lantern=(40, 0, 0))
J3 = pose(J2, hips=(-12, 4, 0, 0, 0), trunk=(-10, -6, -2, 0, 0, 2, 0),
          arms={"great": ([(30, 96, -20), (40, 96, -10), (48, 70, 4), (48, 34, 22), (44, 10, 40), (42, 4, 54)],
                          (0, 0, 1)),
                "back": ([(-8, 112, 8), (-14, 116, 24), (-22, 104, 40), (-24, 74, 54), (-20, 38, 66), (-16, 4, 84)],
                         (0, 0, 1))})
CREAK = Clip("creak", 1.0, "once", [(0.0, BIND, "smooth"), (0.15, J1, "snap"), (0.4, J2, "snap"), (0.65, J3, "snap"),
                                    (1.0, J3, "linear")], lag=0.0)

# ---- eruption -----------------------------------------------------------------------------------------------------------

REAR = pose(hips=(2, 4, 0, 0, 0), trunk=(10, 6, 0, -8, -8, 0, 0),
            arms={"great": ([(34, 112, -16), (54, 108, -8), (66, 76, -4), (64, 40, -10)], (1, 0.3, -0.3), 20),
                  "lesser": ([(30, 76, -4), (44, 64, 2), (52, 40, 8)], (1, 0.2, 0.3), 20),
                  "back": ([(-10, 122, 10), (-26, 124, 22), (-44, 100, 30), (-52, 66, 32), (-52, 44, 30)],
                           (-1, 0.3, 0.3), 20),
                  "crutch": ([(-34, 100, -26), (-50, 96, -38), (-58, 66, -48), (-56, 36, -52)], (-0.3, 0.3, -1), 20)},
            lantern=(0, 0, 70))
DRIVE = pose(hips=(-6, 0, 0, 0, 0), trunk=(-10, -4, 0, 0, 0, 0, 0),
             arms={"great": ([(34, 104, -20), (56, 104, -18), (66, 64, -30), (62, 6, -36)], (0.6, 0, -1), -45),
                   "lesser": ([(30, 72, -4), (46, 58, -2), (54, 6, 6)], (1, 0, 0.3), -45),
                   "back": ([(-10, 120, 10), (-28, 118, 22), (-48, 90, 30), (-54, 40, 32), (-52, 6, 32)],
                            (-1, 0, 0.3), -45),
                   "crutch": ([(-34, 98, -28), (-50, 92, -42), (-58, 50, -54), (-52, 6, -58)], (-0.4, 0, -1), -45)},
             lantern=(0, 0, -120))
STRAIN = pose(DRIVE, trunk=(-12, -5, 0, 0, 0, 0, 0), hips=(-7, 0, 0, 0, 0))
WRENCH = pose(DRIVE, hips=(2, 0, 0, 0, 0), trunk=(6, 4, 0, 0, 0, 0, 0))
for k in ("great", "lesser", "back", "crutch"):
    nudge_arm(WRENCH, k, (0, 12, 0))


def eruption_layer(t, P):
    k = clamp01((t - 0.6) / 0.8) * (t < 1.5)                # the strain builds while the lanes charge
    P["trunk"][1] += tremor(t, 1.4 * k)[0]
    P["hips"][0] += tremor(t, 0.7 * k, 1)[1]
    return P


ERUPTION = Clip("eruption", 2.4, "once", [(0.0, BIND, "smooth"), (0.4, REAR, "out"), (0.55, DRIVE, "in"),
                                          (1.4, STRAIN, "smooth"), (1.5, WRENCH, "back"), (2.4, BIND, "smooth")],
                eruption_layer, contact=0.55, lag=0.015, dt=0.025)

# ---- sap rain ----------------------------------------------------------------------------------------------------------

RISE = pose(hips=(2, 4, 0, 0, 0), trunk=(9, 6, 2, -10, -12, 0, 0),
            arms={"great": ([(36, 114, -14), (58, 128, -6), (76, 132, 6), (88, 124, 20)], (1, 0.1, 0.3)),
                  "back": ([(-18, 118, 8), (-42, 128, 14), (-64, 128, 24), (-82, 118, 36)], (-1, 0.1, 0.3)),
                  "thin": ([(20, 116, 10), (34, 118, 26), (44, 100, 40), (46, 72, 50), (42, 46, 56)], (0, -1, 0.3)),
                  "lesser": ([(30, 76, -4), (44, 60, 4), (50, 38, 10)], (1, 0, 0.3))},
            lantern=(0, 0, 120))
SHUDDER = pose(RISE, hips=(-2, 2, 0, 0, 0), trunk=(5, 3, 1, -8, -10, 0, 0))


def sap_layer(t, P):
    k = clamp01((t - 0.8) / 0.3) * (t < 1.8)
    for i, a in enumerate(("great", "back", "thin")):
        nudge_arm(P, a, tremor(t, 1.6 * k, i + 3))
    P["trunk"][1] += tremor(t, 0.8 * k, 7)[0]
    return P


SAP = Clip("sap", 2.6, "once", [(0.0, BIND, "smooth"), (0.8, RISE, "out"), (1.6, RISE, "linear"),
                                (1.75, SHUDDER, "snap"), (2.6, BIND, "smooth")], sap_layer, contact=1.75)

# ---- ground slam -------------------------------------------------------------------------------------------------------

RAISE = pose(hips=(4, 6, 0, 0, 0), trunk=(14, 8, 0, -10, -12, 0, 0),
             arms={"crutch": ([(-32, 116, -30), (-42, 144, -38), (-36, 164, -56), (-26, 158, -72)], (0.2, 0.5, -1), 0),
                   "great": ([(32, 116, -32), (42, 144, -40), (36, 164, -58), (26, 158, -74)], (-0.2, 0.5, -1), 0)},
             lantern=(0, 0, 20))
HANG = pose(RAISE, trunk=(15, 9, 0, -10, -12, 0, 0), hips=(5, 7, 0, 0, 0))
SLAMMED = pose(hips=(-8, -6, 0, 0, 0), trunk=(-18, -8, 0, 0, 0, 0, 0),
               arms={"crutch": ([(-38, 102, -46), (-44, 84, -70), (-34, 42, -90), (-24, 7, -96)], (0.3, 0, -1), -40),
                     "great": ([(38, 102, -48), (44, 84, -72), (34, 42, -92), (24, 7, -98)], (-0.3, 0, -1), -40)},
               lantern=(0, 0, -260))
OVER = pose(SLAMMED, trunk=(-20, -9, 0, 0, 0, 0, 0), hips=(-9, -7, 0, 0, 0))
SLAM = Clip("slam", 2.3, "once", [(0.0, BIND, "smooth"), (1.1, RAISE, "out"), (1.25, HANG, "smooth"),
                                  (1.5, SLAMMED, "in"), (1.65, OVER, "back"), (2.3, BIND, "smooth")], contact=1.5,
            lag=0.015, dt=0.025)

# ---- twitch, stagger ----------------------------------------------------------------------------------------------------

FLINCH = pose(hips=(2, 2, 0, 0, 0), trunk=(6, 4, 0, -4, -4, 0, 0), lantern=(0, 0, 150))
nudge_arm(FLINCH, "great", (4, 3, 0), [0.3, 1, 0.8, 0.3, 0])
nudge_arm(FLINCH, "back", (-4, 3, 0), [0.3, 1, 0.8, 0.3, 0])
TWITCH = Clip("twitch", 0.5, "once", [(0.0, BIND, "smooth"), (0.08, FLINCH, "snap"), (0.5, BIND, "out")])

REEL = pose(hips=(2, 6, 0, 0, 0), trunk=(16, 10, 4, -12, -14, 0, 0),
            arms={"great": ([(34, 114, -14), (54, 120, -2), (64, 98, 10), (62, 64, 22)], (1, 0, 0.5)),
                  "back": ([(-10, 126, 8), (-28, 136, 18), (-46, 120, 30), (-52, 84, 40)], (-1, 0, 0.5))},
            lantern=(0, 0, 140))
SLIP = pose(hips=(-14, -4, 0, 0, 0), trunk=(-14, -8, 0, 0, 0, 0, 0),
            arms={"crutch": ([(-34, 96, -34), (-50, 88, -54), (-60, 50, -74), (-60, 20, -88), (-58, 9, -94)],
                             (-0.2, 0, -1), -25)},
            lantern=(0, 0, -100))
STAGGER = Clip("stagger", 1.8, "once", [(0.0, BIND, "smooth"), (0.25, REEL, "back"), (0.6, SLIP, "in"),
                                        (1.2, SLIP, "linear"), (1.8, BIND, "smooth")])

# ---- death -------------------------------------------------------------------------------------------------------------

D_SHUDDER = pose(hips=(2, 0, 0, 0, 0), trunk=(4, 2, 0, 0, 0, 0, 0))
D_BUCKLE = pose(hips=(-18, -4, 0, 0, 0), trunk=(-14, -8, 0, 0, 0, 0, 0),
                legs={"right": ((17, 2, 4), (0, 0.5, 1), (0, 0, -20)), "left": ((-18, 2, 12), (0, 0.5, 1), (0, 0, -20))})
D_LEAN = pose(D_BUCKLE, hips=(-24, -6, 0, 0, 0), trunk=(-18, -10, 0, 0, 0, 4, 0),
              arms={"crutch": ([(-36, 88, -34), (-54, 80, -52), (-64, 46, -66), (-62, 18, -76), (-60, 9, -80)],
                               (-0.3, 0, -1), -25)})
D_DOWN = pose(hips=(-28, -6, 0, 0, 0), trunk=(-24, -16, 0, 0, 0, 8, 0),
              arms={"crutch": ([(-50, 60, -44), (-74, 40, -66), (-96, 10, -84), (-106, 4, -92)], (-0.6, 0, -1)),
                    "great": ([(46, 50, -30), (60, 20, -20), (70, 6, 4)], (1, 0, 0.6)),
                    "lesser": ([(32, 30, -4), (40, 10, 20), (36, 6, 40)], (0, 0, 1)),
                    "back": ([(-10, 118, 16), (-24, 110, 38), (-36, 70, 56), (-40, 30, 66), (-40, 6, 74)], (0, 0, 1)),
                    "thin": ([(14, 96, 18), (22, 80, 36), (26, 40, 50), (26, 8, 58)], (0, 0, 1))},
              legs={"right": ((24, 2, -16), (0, 0.25, 1), (0, 0, -20)), "left": ((-22, 2, 14), (0, 0.25, 1), (0, 0, -20))})
D_BOUNCE = pose(D_DOWN, hips=(-26, -6, 0, 0, 0), trunk=(-22, -15, 0, 0, 0, 8, 0))
D_LAST = pose(D_DOWN)
nudge_arm(D_LAST, "thin", (4, 6, 0))
DEATH = Clip("death", 3.6, "hold", [(0.0, BIND, "smooth"), (0.5, D_SHUDDER, "smooth"), (1.2, D_BUCKLE, "in"),
                                    (1.8, D_LEAN, "smooth"), (2.5, D_DOWN, "in"), (2.75, D_BOUNCE, "out"),
                                    (3.0, D_DOWN, "smooth"), (3.15, D_LAST, "snap"), (3.6, D_DOWN, "out")],
             interp="linear", dt=0.025)

CLIPS = {c.name: c for c in (IDLE, WALK, SPAWN, SWIPE, LUNGE, ERUPTION, SAP, SLAM, CREAK, TWITCH, STAGGER, DEATH)}

# ---- the glows through each clip (session 6's tints), and the GIF cameras ------------------------------------------

CALM = {"bloom": s6.BLOOM["calm"], "glow": s6.LANTERN["calm"], "eyelid": s6.SLEEPER["shut"], "resin_core": s6.WOMB["calm"]}
VULN = {"bloom": s6.BLOOM["vulnerable"], "glow": s6.LANTERN["vulnerable"], "eyelid": s6.SLEEPER["open"],
        "resin_core": s6.WOMB["vulnerable"]}
OUT_ = {"bloom": s6.BLOOM["creak"], "glow": s6.LANTERN["creak"], "eyelid": s6.SLEEPER["shut"],
        "resin_core": s6.WOMB["creak"]}
DEAD = {"bloom": s6.BLOOM["dead"], "glow": s6.LANTERN["dead"], "eyelid": s6.SLEEPER["dead"],
        "resin_core": s6.WOMB["dead"]}


def mix(a, b, k):
    return {z: tuple(a[z][i] + (b[z][i] - a[z][i]) * k for i in range(3)) for z in a}


def STATE(name, t):
    if name == "creak":
        return mix(CALM, OUT_, smooth((t - 0.15) / 0.5))
    if name == "spawn":
        s = mix(OUT_, CALM, smooth((t - 1.2) / 1.0))
        return mix(s, VULN, bump(t, 2.85, 0.45) * 0.7)
    if name == "stagger":
        return mix(CALM, VULN, smooth((t - 0.2) / 0.4))
    if name == "death":
        return mix(CALM, DEAD, smooth((t - 1.0) / 2.0))
    if name == "lunge":
        return mix(OUT_, CALM, smooth(t / 0.3))
    return CALM


VIEWS = {
    "spawn": {"scale": 16.0}, "sap": {"scale": 17.0, "target": (0, 0.5, 4.6)}, "slam": {"scale": 17.0},
    "swipe": {"scale": 16.0, "location": (12, 13, 7.0)}, "lunge": {"scale": 17.0, "target": (0, 2.0, 3.6)},
    "death": {"scale": 16.0, "target": (0, 0.5, 2.6)},
    "walk": {"location": (15, 9, 6.0), "target": (0, -0.5, 3.4), "scale": 18.0},
}
