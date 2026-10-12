"""The Unbound redesign, session 1 step 1 (take 2): the hunched brute in his two poses, side and front.

The brief (user, 2026-10-12; plan: docs/art/bosses/the_unbound/overhaul/plan.md): clearly a vindicator, larger than a
player, a buff upper body; bull horns (no burning tips); a red cloth wrapped round his eyes with one eye burning
through it in tier 1's spirit cyan; clear iron shackles on his wrists and ankles with chains hanging from them; a
burning chest piece; silver-studded leather straps; no clothes but his trousers; a giant bloody meat cleaver (the
Frenzy Cleaver's design) in his right hand.

Take 1 offered three postures. The user took C's hunched side posture (the Brute) at B's height and width (the
Executioner), a little bigger than both. He drags the cleaver behind him when he walks and lifts it round his
shoulder to attack, so the two columns are those two poses.

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
S = 3.3
BG, INK = (24, 22, 28), (236, 228, 214)
PLAYER = (150, 178, 222)
SIL = (34, 33, 40)
TONE = {"skin": (120, 126, 124), "skin_dark": (94, 100, 100), "skin_far": (84, 90, 90), "nose": (108, 114, 112),
        "brow": (70, 72, 74), "pants": (50, 50, 58), "pants_far": (38, 38, 44), "boot": (34, 30, 30),
        "cloth": (150, 34, 34), "cloth_dark": (110, 24, 26), "strap": (88, 60, 40), "stud": (206, 210, 218),
        "iron": (70, 66, 72), "iron_lit": (124, 120, 128), "chain": (150, 150, 160), "skin_body": (108, 114, 112),
        "horn": (206, 194, 162), "horn_dark": (160, 146, 112),
        "steel": (156, 162, 168), "spine": (102, 106, 112), "blood": (104, 22, 20), "haft": (88, 62, 40),
        "glow": (255, 132, 36), "hot": (255, 214, 120), "ember": (255, 170, 60),
        "eye": (80, 226, 255), "eye_hot": (214, 252, 255)}


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


def chain(top, length, sway=0.0):
    """A broken chain hanging from a shackle: big alternating links, swinging a little; whatever reaches the ground
    lies along it, trailing behind."""
    out, x, y, i = [], top[0], top[1] - 1.6, 0
    left = length
    while left > 0:
        if y > 1.6:
            out.append(("chain", rect(x + sway * min(1.0, i / 4), y, 3.2 if i % 2 else 1.8, 3.6)))
            y -= 3.2
        else:
            x += 3.2 * (1 if sway >= 0 else -1)
            out.append(("chain", rect(x + sway, 1.0, 3.6, 2.6 if i % 2 else 1.5)))
        left -= 3.2
        i += 1
    return out


def shackle(c, w, ang=0.0):
    """A heavy blackened iron shackle round a wrist or ankle, its ring on the front."""
    return [("iron", rect(c[0], c[1], w + 2.8, 5.0, ang)), ("iron_lit", rect(c[0], c[1] + 1.6, w + 2.8, 1.0, ang)),
            ("iron_lit", rect(c[0], c[1] - 3.0, 3.0, 2.4, ang))]


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


def grounded_cleaver(grip, squash=1.0, flip=True, scale=1.0, behind=1):
    """The cleaver dragged behind: the angle where its lowest corner just touches the ground, the blade trailing."""
    best = None
    for tenth in range(0, 1800):
        a = (-1 if behind > 0 else 1) * tenth / 10.0
        parts = cleaver(grip, a, squash, flip, scale)
        low = min(y for _, p in parts for _, y in p)
        far = max(x * behind for _, p in parts for x, _ in p)
        if abs(low) < 0.25 and far > grip[0] * behind + 8:
            if best is None or far > best[0]:
                best = (far, parts)
    return best[1] if best else cleaver(grip, -100 * behind, squash, flip, scale)


# ---- the head: the vindicator's long face, the nose, the brow; bull horns; the red cloth --------------------------

def head_side(c, tilt=0.0):
    """Side view, facing left. c = the head's centre. The vindicator head at 1.35x: 11 deep, 13.5 tall."""
    hx, hy = c
    out = [("skin", rect(hx, hy, 11, 13.5)),
           ("nose", rect(hx - 6.8, hy - 3.4, 2.7, 5.4)),                           # the big nose, low on the face
           ("brow", rect(hx - 4.8, hy + 2.0, 2.2, 1.8)),
           ("cloth", rect(hx, hy + 0.8, 11.8, 3.8)),                               # the band round the eyes
           ("eye", rect(hx - 6.0, hy + 0.7, 0.9, 1.8)),                            # the eye burning through it
           ("cloth_dark", limb((hx + 5.6, hy + 1.4), (hx + 11, hy - 4.5), 2.4, 1.5)),  # its knotted ends trailing
           ("cloth_dark", limb((hx + 5.6, hy + 0.4), (hx + 9.4, hy - 7.2), 2.0, 1.1))]
    # a bull's horn from the side of the skull, above the cloth: out, then forward and up
    out.append(("horn", [(hx + 2, hy + 3.6), (hx - 2, hy + 7.6), (hx - 7, hy + 12.4), (hx - 8.2, hy + 15.6),
                         (hx - 5.8, hy + 12), (hx - 1.6, hy + 9.8), (hx + 4, hy + 6)]))
    out.append(("horn_dark", rect(hx + 1.6, hy + 4.8, 3, 2.6, 30)))                 # the horn's root on the skull
    return tturn(out, c, tilt)


def head_front(c):
    hx, hy = c
    out = []
    for sgn in (-1, 1):
        out += [("horn", [(hx + sgn * 5, hy + 2.6), (hx + sgn * 10.5, hy + 4.4), (hx + sgn * 15.4, hy + 7.6),
                          (hx + sgn * 17, hy + 13.2), (hx + sgn * 14.4, hy + 10.2), (hx + sgn * 9.8, hy + 8),
                          (hx + sgn * 5, hy + 5.8)]),
                ("horn_dark", rect(hx + sgn * 6.2, hy + 4.2, 2.6, 3))]
    out += [("skin", rect(hx, hy, 11, 13.5)), ("brow", rect(hx, hy + 2.6, 9.2, 1.8)),
            ("nose", rect(hx, hy - 3.4, 2.7, 5.4)),
            ("cloth", rect(hx, hy + 0.8, 11.8, 3.8)),
            ("eye", rect(hx + 2.6, hy + 0.7, 1.8, 1.2)), ("eye_hot", rect(hx + 2.6, hy + 0.7, 0.9, 0.6))]
    return out


# ---- the body pieces ------------------------------------------------------------------------------------------------

def studs_along(a, b, n, size=0.9):
    return [("stud", rect(a[0] + (b[0] - a[0]) * (i + 0.5) / n, a[1] + (b[1] - a[1]) * (i + 0.5) / n, size, size))
            for i in range(n)]


def chest_piece_front(c, w=10, h=9):
    """The burning chest piece: a blackened iron plate strapped over the bare chest, a fire grate burning in it."""
    x, y = c
    out = [("iron", [(x - w / 2, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2 - 1.2, y - h / 2), (x - w / 2 + 1.2, y - h / 2)]),
           ("glow", rect(x, y, w * 0.55, h * 0.55))]
    out += [("iron", rect(x + dx, y, 0.8, h * 0.6)) for dx in (-1.5, 0, 1.5)]          # the grate's bars
    out += [("hot", rect(x, y - 0.7, 1.2, 1.4))]
    out += [("ember", rect(x - 2.4 + 4.8 * (i % 2), y + h / 2 + 1.6 + i * 2.0, 0.8, 0.8)) for i in range(3)]
    return out


def bare_chest_front():
    """The buff, bare torso: wide shoulders and lats tapering to the waist, traps up round the low head."""
    out = [("skin", [(-9, 21), (-14, 30), (-18.5, 40), (-17.5, 45), (-10.5, 48.5), (-6, 50), (6, 50), (10.5, 48.5),
                     (17.5, 45), (18.5, 40), (14, 30), (9, 21)])]
    out += [("skin_dark", rect(-5.4, 37.2, 9, 1.2, -6)), ("skin_dark", rect(5.4, 37.2, 9, 1.2, 6)),   # under the pecs
            ("skin_dark", rect(0, 32, 1, 10))]
    out += [("skin_dark", rect(dx, y, 3.6, 0.8)) for dx in (-2.4, 2.4) for y in (29, 26, 23)]       # the abs
    out += [("strap", limb((-14, 44), (8.5, 22), 2.6)), ("strap", limb((14, 44), (-8.5, 22), 2.6))]
    out += studs_along((-14, 44), (8.5, 22), 7) + studs_along((14, 44), (-8.5, 22), 7)
    out += chest_piece_front((0, 35))
    return out


def legs_front():
    out = [("pants", [(-10, 14), (10, 14), (10.5, 23), (-10.5, 23)]), ("strap", rect(0, 22, 21, 2.6))]
    out += studs_along((-10, 22), (10, 22), 7)
    for sgn in (-1, 1):
        hip, knee, foot = (sgn * 5.5, 18), (sgn * 7, 10), (sgn * 7.4, 0)
        out += [("pants", limb(hip, knee, 9, 8.6)), ("pants", limb(knee, (foot[0], 2.6), 8.6, 8.2)),
                ("boot", rect(foot[0], 1.4, 10, 2.8))]
        out += shackle((foot[0], 5.6), 8.2) + chain((foot[0] + sgn * 1.2, 3.2), 12, sgn * 1.5)
    return out


def arm_front(shoulder, elbow, fist, tone="skin"):
    return [(tone, limb(shoulder, elbow, 10, 10.5)), (tone, limb(elbow, fist, 11.5, 10.5)),
            (tone, rect(fist[0], fist[1] - 1.5, 10, 7))]


# ---- the two poses -------------------------------------------------------------------------------------------------
#   walk    hunched forward, his long arms hanging past his knees; the cleaver dragged behind him, its blade on the
#           ground
#   attack  the same stance, the cleaver lifted round his right shoulder for the cleave, the blade hanging behind
#           his back

HUNCH = 20                                    # degrees the upper body leans forward over the hips
HIP = (1, 22)


def side(pose):
    out = []
    # legs: the far one, then the near one; shackles and chains on both ankles
    for knee, foot, tone, sway in (((6, 10.5), (8, 0), "pants_far", 2.0), ((-4, 11), (-7, 0), "pants", 1.5)):
        out += [(tone, limb(HIP, knee, 9, 8.6)), (tone, limb(knee, (foot[0], 2.6), 8.6, 8.2)),
                ("boot", rect(foot[0] - 1.2, 1.4, 11, 2.8))]
        out += shackle((foot[0], 5.6), 8.2) + chain((foot[0] + 3, 3.4), 14, sway)
    out += [("pants", [(-8, 15), (9.5, 15), (10, 24), (-8.5, 24)]), ("strap", rect(0.8, 23.4, 19, 2.6))]
    # the bare torso, deep chest and huge back, hunched over the hips
    torso = [("skin_body", [(-8, 22), (-12, 31), (-14, 41), (-12, 49), (-5, 52), (6, 52.5), (12, 47), (12.5, 34), (9, 22)]),
             ("skin_dark", limb((-12.6, 38), (-9, 33), 1.0)),                               # under the pec
             ("strap", limb((-6, 51), (8, 24), 2.6))] + studs_along((-6, 51), (8, 24), 6)
    torso += [("iron", [(-14.8, 32), (-15.2, 41), (-12.2, 42), (-12, 31)]), ("glow", rect(-14.5, 36.5, 1.4, 5.4)),
              ("ember", rect(-17, 43, 0.8, 0.8)), ("ember", rect(-15.6, 46, 0.8, 0.8))]
    shoulder_far, shoulder_near = turn([(2, 47)], HIP, HUNCH)[0], turn([(-3, 46)], HIP, HUNCH)[0]
    head_at = turn([(-13, 51)], HIP, HUNCH)[0]
    # the far arm hangs past the knee, its shackle and chain swinging
    far = [("skin_far", limb(shoulder_far, (-10, 29), 10, 10.5)), ("skin_far", limb((-10, 29), (-11, 13), 11.5, 10.5)),
           ("skin_far", rect(-11, 10.6, 10, 7))]
    far += shackle((-11, 17), 10.5) + chain((-11, 14.2), 20, -1.0)
    out += far + tturn(torso, HIP, HUNCH)
    out += head_side(head_at, 0)
    if pose == "walk":
        fist = (-1, 13)
        out += grounded_cleaver(fist, 1.0, True, 1.2, behind=1)
        out += [("skin", limb(shoulder_near, (-5, 29), 10, 10.5)), ("skin", limb((-5, 29), fist, 11.5, 10.5)),
                ("skin", rect(fist[0], fist[1] - 1.4, 10, 7))]
        out += shackle((-2.4, 19), 10.5, -10) + chain((-2.4, 16.2), 22, 1.2)
    else:
        fist = (-4, 55)
        out += cleaver(fist, -58, 1.0, True, 1.2)
        out += [("skin", limb(shoulder_near, (-17, 40), 10, 10.5)), ("skin", limb((-17, 40), fist, 11.5, 10.5)),
                ("skin", rect(fist[0], fist[1], 10, 7, 40))]
        out += shackle((-11, 47), 10.5, 52) + chain((-12.5, 45), 12, -1.2)
    return out


def front(pose):
    out = legs_front() + bare_chest_front()
    out += head_front((0, 45.5))
    # his left arm (viewer's right) hangs long, its chain swinging
    out += arm_front((17, 42), (21.5, 28), (22, 12)) + shackle((22, 18.5), 10.5) + chain((22, 15.6), 20, 1.2)
    if pose == "walk":
        fist = (-22, 12)
        out += grounded_cleaver(fist, 0.4, True, 1.0, behind=-1)
        out += arm_front((-17, 42), (-21.5, 28), fist) + shackle((-22, 18.5), 10.5) + chain((-22, 15.6), 20, -1.2)
    else:
        fist = (-17, 49)
        out += cleaver(fist, 16, 0.6, False, 1.2)
        out += arm_front((-17, 42), (-25, 43), fist) + shackle((-21.5, 46), 10.5, -35) + chain((-23, 44), 7, -1)
    return out


# ---- the sheet --------------------------------------------------------------------------------------------------------

POSES = [("walk", "walking: dragging the cleaver"), ("attack", "attacking: the cleaver round his shoulder")]


def draw_row(view, mode):
    W, H = 1200, 330
    img = Image.new("RGB", (W, H), (58, 56, 64) if mode == "value" else (244, 241, 234))
    d = ImageDraw.Draw(img)
    oy = H - 24
    if mode == "value":
        d.rectangle((0, oy, W, H), fill=(46, 44, 52))
    d.line((0, oy, W, oy), fill=(120, 116, 110), width=2)
    for i, (pose, _) in enumerate(POSES):
        ox = 260 + i * 470
        for tone, p in (side(pose) if view == "side" else front(pose)):
            col = SIL if mode == "sil" else TONE[tone]
            d.polygon([(ox + x * S, oy - y * S) for x, y in p], fill=col)
    px, ph, pw = 1110, 28.8 * S, 7.2 * S
    d.rectangle((px - pw / 2, oy - ph * 0.75, px + pw / 2, oy), fill=PLAYER)
    d.rectangle((px - pw * 0.55, oy - ph, px + pw * 0.55, oy - ph * 0.75), fill=PLAYER)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    pad, top, lab, rh = 12, 56, 34, 330
    rows = [("side", "sil"), ("side", "value"), ("front", "sil"), ("front", "value")]
    sheet = Image.new("RGB", (1200 + 2 * pad, top + len(rows) * (rh + pad) + 2 * lab), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 14), "The Unbound (take 2) - walking, dragging the cleaver | attacking, the cleaver round his shoulder",
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
