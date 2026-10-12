"""The Unbound redesign, session 1 step 1: three postures of the Horned Frenzy, side and front, silhouette and value.

The brief (user, 2026-10-12; plan: docs/art/bosses/the_unbound/overhaul/plan.md): clearly a vindicator, larger than a
player, a buff upper body; bull horns; a red cloth wrapped round his eyes with one eye burning through; chains
dangling from his limbs; a burning chest piece; silver-studded leather straps; a giant bloody meat cleaver (the Frenzy
Cleaver's design) in his right hand; embers and fire grow as he speeds up.

Shapes are angular polygons and turned rectangles, buildable from cuboids. Units are model pixels (16 = one block),
y up, the ground at 0. Side views face left (the front is -x). In the front views he faces us, so his right hand
(the cleaver) is on the viewer's left. The blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/unbound_silhouettes.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s1_silhouettes"
S = 3.6
FIG = 0.88                  # the drawn figures are scaled to about 2.9 blocks to the top of the head
BG, INK = (24, 22, 28), (236, 228, 214)
PLAYER = (150, 178, 222)
SIL = (34, 33, 40)
TONE = {"skin": (118, 124, 122), "skin_dark": (92, 98, 98), "nose": (106, 112, 110), "brow": (70, 72, 74),
        "coat": (52, 54, 62), "coat_far": (40, 42, 48), "pants": (44, 42, 48), "boot": (34, 30, 30),
        "cloth": (150, 34, 34), "cloth_dark": (110, 24, 26), "strap": (88, 60, 40), "stud": (206, 210, 218),
        "iron": (50, 46, 48), "iron_far": (36, 34, 36), "chain": (112, 112, 120),
        "horn": (206, 194, 162), "horn_dark": (160, 146, 112),
        "steel": (156, 162, 168), "spine": (102, 106, 112), "blood": (104, 22, 20), "haft": (88, 62, 40),
        "glow": (255, 132, 36), "hot": (255, 214, 120), "ember": (255, 170, 60)}


# ---- shape helpers -----------------------------------------------------------------------------------------------

def rect(cx, cy, w, h, ang=0.0):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return [(cx + dx * c - dy * s, cy + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2),
                                                                         (w / 2, h / 2), (-w / 2, h / 2))]


def turn(points, pivot, ang):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    px, py = pivot
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in points]


def tturn(parts, pivot, ang):
    return [(t, turn(p, pivot, ang)) for t, p in parts]


def shift(parts, dx, dy):
    return [(t, [(x + dx, y + dy) for x, y in p]) for t, p in parts]


def mirror(parts):
    return [(t, [(-x, y) for x, y in p]) for t, p in parts]


def limb(a, b, w0, w1=None):
    """A tapered segment from a (w0 wide) to b (w1 wide)."""
    w1 = w0 if w1 is None else w1
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    return [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
            (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]


def chain(top, length, sway=0.0, links=None):
    """A broken chain hanging from a shackle: alternating links, swinging a little."""
    links = links or max(2, int(length / 2.2))
    out = []
    for i in range(links):
        y = top[1] - 1.2 - i * 2.2
        x = top[0] + sway * (i / links) ** 1.5
        out.append(("chain", rect(x, y, 1.9 if i % 2 else 1.2, 2.4)))
    return out


def cuff(c, w, h=3.0, ang=0.0):
    """A blackened iron shackle round a wrist or ankle."""
    return [("iron", rect(c[0], c[1], w + 1.2, h, ang))]


# ---- the cleaver (the Frenzy Cleaver at his size) -----------------------------------------------------------------

def cleaver(grip, ang, squash=1.0, flip=False, scale=1.0):
    """In its own frame the haft runs up +y from the grip and the blade hangs off the -x side (+x with flip).
    squash narrows the blade across (1 = seen face-on, small = turned edge-on). ang turns it about the grip (degrees,
    counter-clockwise; 0 = haft straight up)."""
    k = scale
    f = (-1 if flip else 1) * squash
    parts = [("haft", rect(0, 9 * k, 2.2 * k, 30 * k)),                           # grip, then the haft up through it
             ("steel", [(-17 * k, 9 * k), (-0.5 * k, 9 * k), (-0.5 * k, 26 * k), (-18 * k, 26 * k)]),   # the flat
             ("spine", [(-18 * k, 24.4 * k), (-0.5 * k, 24.4 * k), (-0.5 * k, 26.6 * k), (-18 * k, 26.6 * k)]),
             ("blood", [(-17 * k, 9 * k), (-15.4 * k, 9 * k), (-15.6 * k, 20 * k), (-12 * k, 22 * k), (-12.6 * k, 17 * k),
                        (-10 * k, 15 * k), (-11 * k, 12 * k), (-8 * k, 9 * k), (-6 * k, 9 * k), (-9 * k, 13 * k),
                        (-16 * k, 24 * k), (-18 * k, 24.4 * k)]),                 # dried blood along the edge
             ("iron", rect(0, 25.6 * k, 3 * k, 2.4 * k)), ("iron", rect(0, -5 * k, 3 * k, 2 * k))]
    parts = [(t, [(x * f if x < -0.6 * k else x, y) for x, y in p]) for t, p in parts]
    parts = tturn(parts, (0, 0), ang)
    return shift(parts, grip[0], grip[1])


# ---- the head: the vindicator's long face, the nose, the brow; bull horns; the red cloth --------------------------

def head_side(c, tilt=0.0, horn="up"):
    """Side view, facing left. c = the head's centre. The vindicator head at 1.25x: 10 deep, 12.5 tall."""
    hx, hy = c
    out = [("skin", rect(hx, hy, 10, 12.5)),
           ("nose", rect(hx - 6.2, hy - 3.2, 2.5, 5)),                             # the big nose, low on the face
           ("brow", rect(hx - 4.3, hy + 1.6, 2, 1.6)),
           ("cloth", rect(hx, hy + 0.6, 10.8, 3.4)),                               # the band round the eyes
           ("glow", rect(hx - 5.5, hy + 0.5, 0.8, 1.6)),                           # the eye burning through
           ("cloth_dark", limb((hx + 5.2, hy + 1.2), (hx + 10, hy - 4), 2.2, 1.4)),  # its knotted ends trailing
           ("cloth_dark", limb((hx + 5.2, hy + 0.2), (hx + 8.6, hy - 6.5), 1.8, 1.0))]
    # a bull's horn from the side of the skull, just above the cloth: out, then forward and up
    if horn == "up":
        pts = [(hx + 1.5, hy + 3.5), (hx - 2, hy + 7), (hx - 6.5, hy + 11.5), (hx - 7.5, hy + 14.5), (hx - 5.4, hy + 11),
               (hx - 1.6, hy + 9.2), (hx + 3.5, hy + 5.6)]
    else:   # "forward": lowered, pointing ahead like a charging bull's
        pts = [(hx + 1.5, hy + 3.5), (hx - 3.5, hy + 6.5), (hx - 10, hy + 7.4), (hx - 13.5, hy + 9.2), (hx - 10.4, hy + 5.4),
               (hx - 4, hy + 3.4), (hx + 2.8, hy + 1.8)]
    out.append(("horn", pts))
    tip = pts[3]
    out.append(("glow", rect(tip[0], tip[1] - 0.6, 1.4, 1.6)))                      # the burning tip
    return tturn(out, c, tilt)


def head_front(c, horn="up", flare=1.0):
    hx, hy = c
    out = []
    for sgn in (-1, 1):
        if horn == "up":
            pts = [(hx + sgn * 4.5, hy + 2.6), (hx + sgn * 9.5, hy + 4.6), (hx + sgn * 14 * flare, hy + 7.5),
                   (hx + sgn * 15.5 * flare, hy + 12.5), (hx + sgn * 13.2 * flare, hy + 9.6), (hx + sgn * 9, hy + 7.4),
                   (hx + sgn * 4.5, hy + 5.4)]
        else:
            pts = [(hx + sgn * 4.5, hy + 2.6), (hx + sgn * 10, hy + 3.4), (hx + sgn * 13.6 * flare, hy + 6.4),
                   (hx + sgn * 13.2 * flare, hy + 9.6), (hx + sgn * 11.4 * flare, hy + 6.8), (hx + sgn * 8, hy + 5.6),
                   (hx + sgn * 4.5, hy + 5.0)]
        out += [("horn", pts), ("glow", rect(pts[3][0], pts[3][1] - 0.4, 1.6, 1.6))]
    out += [("skin", rect(hx, hy, 10, 12.5)), ("brow", rect(hx, hy + 2.4, 8.4, 1.6)),
            ("nose", rect(hx, hy - 3.2, 2.5, 5)),
            ("cloth", rect(hx, hy + 0.6, 10.8, 3.4)),
            ("glow", rect(hx + 2.4, hy + 0.5, 1.6, 1.0)), ("hot", rect(hx + 2.4, hy + 0.5, 0.8, 0.6))]
    return out


# ---- the body pieces ------------------------------------------------------------------------------------------------

def studs_along(a, b, n, size=0.9):
    return [("stud", rect(a[0] + (b[0] - a[0]) * (i + 0.5) / n, a[1] + (b[1] - a[1]) * (i + 0.5) / n, size, size))
            for i in range(n)]


def chest_piece_front(c, w=9, h=8, fire=1.0):
    """The burning chest piece: a blackened iron plate, a fire grate burning in its middle."""
    x, y = c
    out = [("iron", [(x - w / 2, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2 - 1, y - h / 2), (x - w / 2 + 1, y - h / 2)]),
           ("glow", rect(x, y, w * 0.55, h * 0.55))]
    out += [("iron", rect(x + dx, y, 0.8, h * 0.6)) for dx in (-1.4, 0, 1.4)]          # the grate's bars
    out += [("hot", rect(x, y - 0.6, 1.2, 1.4))]
    out += [("ember", rect(x - 2 + 4 * (i % 2), y + h / 2 + 1.5 + i * 1.8 * fire, 0.8, 0.8)) for i in range(int(3 * fire))]
    return out


def front_straps(lsh, rsh, lhip, rhip):
    """Two studded straps crossing his chest, from each shoulder to the other hip."""
    out = [("strap", limb(lsh, rhip, 2.4)), ("strap", limb(rsh, lhip, 2.4))]
    out += studs_along(lsh, rhip, 6) + studs_along(rsh, lhip, 6)
    return out


# ---- postures ---------------------------------------------------------------------------------------------------------
#   A  the Charging Bull: leaning far forward, head low between the shoulders, horns lowered ahead, the cleaver held
#      back low to swing; knees bent, a wide stance
#   B  the Executioner: upright, chest out, the cleaver resting on his right shoulder, the left fist hanging with
#      its chain; the horns sweep up and out
#   C  the Brute: a gorilla's build, huge shoulders hunched, long heavy arms hanging past the knees, the cleaver's
#      point dragging on the ground; short legs

def posture(name, view):
    return {"A": charging, "B": executioner, "C": brute}[name](view)


def legs_side(front_knee, back_knee, hip, front_foot, back_foot, w=6.5):
    out = []
    for knee, foot, tone in ((back_knee, back_foot, "coat_far"), (front_knee, front_foot, "pants")):
        out += [(tone, limb(hip, knee, w, w - 0.5)), (tone, limb(knee, (foot[0], foot[1] + 2), w - 0.5, w - 1)),
                ("boot", rect(foot[0] - 1, foot[1] + 1.4, w + 2, 2.8))]
        out += cuff((foot[0], foot[1] + 4.6), w - 1)
    out += chain((front_foot[0] + 1.5, front_foot[1] + 4), 3, -1.5, 2)
    return out


def executioner(view):
    out = []
    if view == "side":
        out += legs_side((-4, 9), (4, 8.5), (0, 17), (-6, 0), (5, 0))
        # the coat skirt to mid-thigh, then the buff torso: deep chest, wide back, a thick neck
        out += [("coat", [(-7, 10), (7, 10), (8, 19), (-8, 19)])]
        torso = [(-7, 18), (-10.5, 27), (-11, 34), (-8, 39.5), (5, 40.5), (9, 36), (8.5, 26), (6.5, 18)]
        out += [("coat", torso)]
        out += [("strap", limb((-6, 39), (5, 20), 2.4)), ("strap", rect(-0.5, 19, 15.5, 2.4))]   # a strap over the shoulder, a belt
        out += studs_along((-6, 39), (5, 20), 5)
        out += [("iron", [(-11.6, 27), (-11.8, 35), (-9, 36), (-9, 26.5)]), ("glow", rect(-11.4, 31, 1.2, 4.6))]  # the chest piece edge-on
        out += head_side((-3.5, 45), 4, "up")
        # the left arm (far side) hanging; the right (near) bent up, the cleaver resting on the shoulder
        out += [("coat_far", limb((1, 37), (2, 27), 7, 7.5)), ("skin_dark", limb((2, 27), (0, 17), 8, 7.5)),
                ("skin_dark", rect(0, 14.6, 7.5, 5))]
        out += cuff((0.6, 19.5), 8.2) + chain((0.6, 18), 9, 1.5)
        out += cleaver((-3, 33), -64, 1.0, True, 1.05)
        out += [("coat", limb((0, 37.5), (-6, 27.5), 7.5, 8)), ("skin", limb((-6, 27.5), (-4.5, 33), 8.5, 8.5)),
                ("skin", rect(-4.6, 33.4, 7.6, 6))]
        out += cuff((-5.6, 29.5), 9, 3, 75) + chain((-7, 27.5), 8, -1)
    else:
        out += front_legs(5, 17)
        out += [("coat", [(-8, 10), (8, 10), (8.5, 19), (-8.5, 19)])]
        torso = [(-7.5, 18), (-12, 30), (-14.5, 37), (-11, 40.5), (11, 40.5), (14.5, 37), (12, 30), (7.5, 18)]
        out += [("coat", torso), ("skin", [(-5, 38.5), (5, 38.5), (6.5, 41), (-6.5, 41)])]       # the thick neck
        out += front_straps((-10.5, 39), (10.5, 39), (-7, 20), (7, 20)) + [("strap", rect(0, 19.5, 16, 2.4))]
        out += chest_piece_front((0, 30.5))
        out += head_front((0, 46.5), "up")
        # his right arm (viewer's left) up, the cleaver over his shoulder; his left hangs with its chain
        out += [("coat", limb((-13.5, 37), (-16.5, 27), 7.5, 8)), ("skin", limb((-16.5, 27), (-12, 35), 8.5, 8.5)),
                ("skin", rect(-11.5, 36.5, 7.5, 6))]
        out += cleaver((-11.5, 36.5), 8, 0.55, False, 1.05)
        out += cuff((-14.8, 30), 9, 3, -55) + chain((-15.5, 28.5), 8, -1)
        out += [("coat", limb((13.5, 37), (16, 27), 7.5, 8)), ("skin", limb((16, 27), (16.4, 17), 8.5, 8)),
                ("skin", rect(16.4, 14.6, 7.8, 5.5))]
        out += cuff((16.3, 19.5), 9) + chain((16.3, 18), 9, 1.2)
    return out


def front_legs(spread, hip_y, w=6.5, bend=0.0):
    out = []
    for sgn in (-1, 1):
        hip, knee, foot = (sgn * spread * 0.7, hip_y), (sgn * (spread + bend), hip_y * 0.52), (sgn * (spread + bend * 0.5), 0)
        out += [("pants", limb(hip, knee, w, w - 0.4)), ("pants", limb(knee, (foot[0], 2), w - 0.4, w - 0.8)),
                ("boot", rect(foot[0], 1.4, w + 1.2, 2.8))]
        out += cuff((foot[0], 4.4), w - 0.6)
    out += chain((-spread, 3.2), 3, -1, 2)
    return out


def charging(view):
    out = []
    lean = 32
    if view == "side":
        out += legs_side((-7, 8), (6, 6.5), (2, 14), (-9, 0), (10, 0), 7)
        out += [("coat", [(-5, 8.5), (9, 8.5), (9, 16), (-5, 16)])]
        upper = [("coat", [(-6, 14), (-9.5, 23), (-10, 31), (-7, 36.5), (6, 37.5), (10, 33), (9.5, 23), (7.5, 14)])]
        upper += [("strap", limb((-6, 36), (6, 17), 2.4))] + studs_along((-6, 36), (6, 17), 5)
        upper += [("iron", [(-10.6, 23), (-10.8, 31), (-8.2, 32), (-8.2, 22.5)]), ("glow", rect(-10.4, 27, 1.2, 4.6))]
        upper += [("coat_far", limb((1, 34), (-5, 26), 7, 7.5)), ("skin_dark", limb((-5, 26), (-12, 21), 8, 7.5)),
                  ("skin_dark", rect(-14, 19.6, 6, 6.5, 30))]                          # the left arm reaching ahead
        upper += cuff((-11, 21.6), 8.2, 3, 30)
        upper += head_side((-6.5, 42), -lean + 8, "forward")
        out += tturn(upper, (2, 15), lean)
        # the cleaver hauled back low on his right, ready to swing
        out += cleaver((-6, 15), 112, 1.0, True, 1.05)
        out += [("coat", limb((-5, 29), (-3, 21), 7.5, 8)), ("skin", limb((-3, 21), (-6, 15), 8.5, 8)),
                ("skin", rect(-6, 15, 7.5, 6))]
        out += cuff((-4.4, 18.5), 9, 3, -30) + chain((-4.6, 17), 7, 2)
        out += chain((-17, 19), 8, -2)
    else:
        out += front_legs(7, 14, 7, 2.5)
        out += [("coat", [(-8, 8.5), (8, 8.5), (8.5, 15), (-8.5, 15)])]
        torso = [(-8, 14), (-13, 23), (-16, 29), (-12, 33), (12, 33), (16, 29), (13, 23), (8, 14)]   # leaning at us
        out += [("coat", torso)]
        out += front_straps((-11.5, 31.5), (11.5, 31.5), (-7, 16), (7, 16))
        out += chest_piece_front((0, 23.5), 9, 7, 1.6)
        out += head_front((0, 31), "forward", 1.05)
        out += [("coat", limb((-14, 29), (-18, 21), 7.5, 8)), ("skin", limb((-18, 21), (-20, 13), 8.5, 8)),
                ("skin", rect(-20.3, 11.6, 7.6, 5.5))]
        out += cleaver((-20.3, 11.6), 62, 0.6, False, 1.05)
        out += cuff((-19.5, 15.5), 9) + chain((-19.5, 14), 7, -1)
        out += [("coat", limb((14, 29), (17, 23), 7.5, 8)), ("skin", limb((17, 23), (13, 17), 8.5, 8)),
                ("skin", rect(12, 16, 7.6, 6))]
        out += cuff((14, 19), 9, 3, 40) + chain((14, 17.5), 8, 1)
    return out


def brute(view):
    out = []
    if view == "side":
        out += legs_side((-3, 7), (4, 6.5), (0, 13), (-5, 0), (5, 0), 7)
        out += [("coat", [(-6, 7.5), (8, 7.5), (8.5, 15), (-6, 15)])]
        upper = [("coat", [(-6, 14), (-11, 24), (-12.5, 32), (-8, 37), (7, 39.5), (12.5, 34), (11, 22), (8, 14)])]
        upper += [("strap", limb((-7, 36), (7, 16), 2.6))] + studs_along((-7, 36), (7, 16), 5)
        upper += [("iron", [(-12.6, 24), (-13, 32), (-10, 33), (-10, 23.5)]), ("glow", rect(-12.5, 28, 1.2, 4.6))]
        out += tturn(upper, (1, 14), -12)
        out += head_side((-9.5, 35.5), 6, "up")
        # the long arms hang past the knees: the far one, then the near one with the cleaver dragging its point
        out += [("coat_far", limb((2, 35), (0, 23), 8, 8.5)), ("skin_dark", limb((0, 23), (-2, 9), 9.5, 9)),
                ("skin_dark", rect(-2.4, 6.4, 9, 6))]
        out += cuff((-1.6, 12), 9.6) + chain((-1.6, 10.5), 6, 1)
        out += cleaver((-6, 7), -104, 1.0, False, 1.15)
        out += [("coat", limb((-1, 34), (-5, 22), 8.5, 9)), ("skin", limb((-5, 22), (-6, 9), 10, 9.5)),
                ("skin", rect(-6, 6.4, 9, 6))]
        out += cuff((-5.8, 12), 10.4) + chain((-5.8, 10.5), 6, -1)
    else:
        out += front_legs(5.5, 13, 7.5, 1)
        out += [("coat", [(-8.5, 7.5), (8.5, 7.5), (9, 15), (-9, 15)])]
        torso = [(-8.5, 14), (-14, 25), (-18, 34), (-14, 38.5), (14, 38.5), (18, 34), (14, 25), (8.5, 14)]
        out += [("coat", torso)]
        out += front_straps((-13, 37), (13, 37), (-7.5, 16), (7.5, 16))
        out += chest_piece_front((0, 27.5), 10, 9)
        out += head_front((0, 38.5), "up", 1.1)
        for sgn, tone in ((-1, "skin"), (1, "skin")):
            sh, el, fist = (sgn * 16.5, 35), (sgn * 20.5, 22), (sgn * 21, 8)
            out += [("coat", limb(sh, el, 8.5, 9)), (tone, limb(el, fist, 10, 9.5)), (tone, rect(fist[0], fist[1] - 1.5, 9, 6))]
            out += cuff((sgn * 20.8, 13.5), 10.4) + chain((sgn * 20.8, 12), 6, sgn * 1.2)
        out += cleaver((-21, 7), 125, 0.35, True, 0.5)
    return out


# ---- the sheet --------------------------------------------------------------------------------------------------------

NAMES = [("A", "the Charging Bull"), ("B", "the Executioner"), ("C", "the Brute")]


def draw_row(view, mode):
    W, H = 1500, 330
    img = Image.new("RGB", (W, H), (58, 56, 64) if mode == "value" else (244, 241, 234))
    d = ImageDraw.Draw(img)
    oy = H - 24
    if mode == "value":
        d.rectangle((0, oy, W, H), fill=(46, 44, 52))
    d.line((0, oy, W, oy), fill=(120, 116, 110), width=2)
    for i, (key, _) in enumerate(NAMES):
        ox = 210 + i * 420
        for tone, p in posture(key, view):
            col = SIL if mode == "sil" else TONE[tone]
            d.polygon([(ox + x * S * FIG, oy - y * S * FIG) for x, y in p], fill=col)
    px, ph, pw = 1420, 28.8 * S, 7.2 * S
    d.rectangle((px - pw / 2, oy - ph * 0.75, px + pw / 2, oy), fill=PLAYER)
    d.rectangle((px - pw * 0.55, oy - ph, px + pw * 0.55, oy - ph * 0.75), fill=PLAYER)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    pad, top, lab, rh = 12, 56, 34, 330
    rows = [("side", "sil"), ("side", "value"), ("front", "sil"), ("front", "value")]
    sheet = Image.new("RGB", (1500 + 2 * pad, top + len(rows) * (rh + pad) + 2 * lab), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 14), "The Unbound - A the Charging Bull, B the Executioner, C the Brute; side and front; a player",
            font=font, fill=INK)
    y = top
    for view, mode in rows:
        if mode == "sil":
            dr.text((pad, y + 2), view, font=font, fill=INK)
            y += lab
        img = draw_row(view, mode)
        img.save(OUT / f"{view}_{mode}.png")
        sheet.paste(img, (pad, y))
        y += rh + pad
    sheet.save(OUT / "silhouettes.png")
    print("wrote", OUT / "silhouettes.png")


if __name__ == "__main__":
    main()
