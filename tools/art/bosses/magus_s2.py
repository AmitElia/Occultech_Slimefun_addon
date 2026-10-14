"""The Mirrored Magus redesign, session 2: design lock.

The approved take 4 (magus_take4.py: horror proportions, the ruff and petal collar, the porcelain mask; the user will
judge the mask again once it's textured) rebuilt as a rig:
- every part on a named bone (BetterModel names): the hips, both legs (thigh and shin), the torso, the coat (it
  sways), the collar (two bones: the petals pointing straight out and those pointing diagonally), both arms
  (upper and forearm), the neck, `hi_head` (head, mask, hat), the hat's three points in three bones each (they flop),
  the crystal bow in his left hand and its string in two halves (the draw pulls them);
- the glow on its own bone, `glow_eyes` (his eyes; the crystal bow of the first takes became a fan of playing cards,
  `cards`) - `glow_eyes` (a cold glint deep
  in each of the mask's sockets);
- four of him are on the field at once (the real one and three decoys, all identical), so he stays lean: every cube is
  axis-aligned or turned once by 22.5 or 45 degrees (no cube costs an extra display), and the curves come from bones;
- every cube snapped to whole texels; the hitbox (`ob_hitbox`): a column over his body and head, not the hat, the
  arms or the bow;
- the fight's key poses.

Run from the repository root: python tools/art/bosses/magus_s2.py
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
from bosskit.bbmodel import Model, add_hitbox, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import magus_take4 as t4, volley_crone_s2 as v2, volley_crone_s3 as v3  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s2_design"
PALETTE = dict(t4.PALETTE, hitbox=(220, 60, 60), eye_glint=(150, 240, 255), card=(238, 232, 220),
               face=(230, 226, 216), lips=(150, 14, 28), teeth=(214, 200, 160), rednose=(196, 24, 36),
               hair=(96, 16, 28), throat=(30, 4, 10))
HIP = 46.0
SH = HIP + 18                      # the shoulders
NECK = HIP + 22
YH = HIP + 36.5                    # the head's centre
ZF = -5.5                          # the face


def group(model, name):
    return next(g for g in model.groups if g.name == name)


def yaw_box(g, name, centre, size, mat, yaw, extra=(0, 0, 0)):
    """A box turned `yaw` degrees about y, expressed with a free angle (-45..45): a quarter turn swaps its x and z
    sizes, a half turn changes nothing for a box. `extra`: a turn about x applied in the turned frame (only when yaw is
    0 after that, so the cube still turns on one axis)."""
    w, h, d = size
    a = ((yaw + 45) % 90) - 45
    turns = round((yaw - a) / 90) % 2
    if turns:
        w, d = d, w
    return g.box(name, centre, (w, h, d), mat, rotation=(extra[0], a, extra[2]))


# ---- legs and body ---------------------------------------------------------------------------------------------------

def legs(hips):
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        thigh = hips.group(f"leg_{side}", (sx * 2.8, HIP, 0))
        thigh.box(f"thigh_{side}", (sx * 2.8, 35, 0), (4, 22, 4), "leg")
        shin = thigh.group(f"shin_{side}", (sx * 2.8, 25, 0))
        shin.box(f"knee_{side}", (sx * 2.8, 24, -0.5), (5, 3, 5), "black")
        shin.box(f"shin_{side}_box", (sx * 2.8, 13, 0), (4, 20, 4), "leg")
        shin.box(f"shoe_{side}", (sx * 2.8, 1.5, -3), (5, 3, 12), "black")
        shin.box(f"shoe_point_{side}", (sx * 2.8, 3.2, -10.5), (3, 2, 6), "crimson", rotation=(-22.5, 0, 0))
        shin.box(f"shoe_curl_{side}", (sx * 2.8, 6.2, -13.4), (2, 4, 2), "crimson", rotation=(22.5, 0, 0))


def torso_parts(torso):
    h = HIP
    torso.box("corset", (0, h + 3, 0), (8, 6, 6), "crimson")
    for sx in (-1, 1):
        torso.box(f"ribs_{sx}", (sx * 2.75, h + 10, 0), (5.5, 8, 7), "black" if sx < 0 else "white")
        torso.box(f"chest_{sx}", (sx * 3.5, h + 17, 0), (7, 6, 8), "black" if sx < 0 else "white")
    coat = torso.group("coat", (0, h, 0.5))
    for i in range(11):                                    # hanging points round his sides and back
        yaw = -112.5 + i * 22.5
        a = math.radians(yaw)
        x, z = math.sin(a) * 4.8, math.cos(a) * 3.8 + 0.5
        length = 22 - abs(i - 5) * 1.2
        mat = "black" if x < -0.1 else "white"
        yaw_box(coat, f"coat_{i}", (x, h - length / 2, z), (4, length, 1), mat, yaw)
        yaw_box(coat, f"coat_point_{i}", (x, h - length - 1.5, z), (2, 3, 1), mat, yaw)


def collar(torso):
    """A pleated ruff, and two layers of pointed petals tipped down over his shoulders, chest and back: the petals
    pointing straight out sit on `collar`, the diagonal ones on `collar_diagonal` (turned 45 degrees), so each petal
    tips down with one turn of its own."""
    h = HIP
    for i in range(16):
        a = math.radians(i * 22.5)
        yaw_box(torso, f"ruff_{i}", (math.sin(a) * 6.0, h + 21.8, math.cos(a) * 5.2), (2.4, 4, 6.4),
                "white" if i % 2 else "black", i * 22.5)
    cardinal = torso.group("collar", (0, h + 21, 0.4))
    diagonal = torso.group("collar_diagonal", (0, h + 21, 0.4), (0, 45, 0))
    for layer, (r0, length, width, tip, mats) in enumerate(((6.5, 11, 5, 45, ("crimson", "black")),
                                                            (5.5, 7, 4, 45, ("white", "white")))):
        for k, (g, base) in enumerate(((cardinal, 0), (diagonal, 0))):
            for i in range(4):
                # in the bone's own frame: straight out along +z, -x, -z, +x; tipped down about the tangent
                ang = i * 90
                y = h + 21 + layer * 0.8 - length * 0.35
                r = r0 + length * 0.35
                pos = (math.sin(math.radians(ang)) * r, y, math.cos(math.radians(ang)) * r * 0.85 + 0.4)
                if i % 2 == 0:            # pointing along z: tip about x
                    rot = (tip if i == 0 else -tip, 0, 0)
                    size = (width, 1, length)
                else:                     # pointing along x: tip about z
                    rot = (0, 0, -tip if i == 1 else tip)
                    size = (length, 1, width)
                mat = mats[(i + k) % 2]
                g.box(f"petal_{layer}_{k}_{i}", pos, size, mat, rotation=rot)


def arms(torso):
    for sx in (-1, 1):
        side = "left" if sx < 0 else "right"
        arm = torso.group(f"arm_{side}", (sx * 7.6, SH, 0))
        arm.box(f"cap_{side}", (sx * 8.2, SH + 0.5, 0), (6, 3, 6), "crimson")
        arm.box(f"cap_point_{side}", (sx * 11, SH - 1.5, 0), (4, 2, 3), "crimson", rotation=(0, 0, sx * 45))
        arm.box(f"upper_{side}", (sx * 7.6, SH - 9, 0), (4, 18, 4), "white" if sx < 0 else "black")
        fore = arm.group(f"forearm_{side}", (sx * 7.6, SH - 18, 0))
        fore.box(f"fore_{side}", (sx * 7.6, SH - 27, 0), (3, 18, 3), "black" if sx < 0 else "white")
        fore.box(f"cuff_{side}", (sx * 7.6, SH - 35.5, 0), (5, 2, 5), "crimson")
        fore.box(f"hand_{side}", (sx * 7.6, SH - 38.5, 0), (4, 4, 3), "skin")
        for j, dx in enumerate((-1.3, -0.45, 0.45, 1.3)):     # long clawed fingers, splayed a little
            spread = 0 if abs(dx) < 1 else (22.5 if dx * sx > 0 else -22.5) * sx
            fore.box(f"finger_{side}_{j}", (sx * 7.6 + dx * 1.3, SH - 45, -0.4), (1, 9, 1), "claw",
                     rotation=(0, 0, spread))
            fore.box(f"claw_{side}_{j}", (sx * 7.6 + dx * 1.3 + (spread / 22.5) * 1.6, SH - 50, -1.4), (1, 3, 1),
                     "claw", rotation=(-22.5, 0, 0))
    cards(group(torso.model, "forearm_right"))


CARD = (6, 9)              # a card's width and height (it's a flat plane)


def cards(fore):
    """His weapon (the user, 2026-10-13: in place of the crystal bow): a spread hand of playing cards fanned in his right
    palm, thrown in fans instead of arrows. Five cards, each a flat plane, fanned by 22.5 degrees about the palm; their
    faces and backs are painted (session 5), at the head's resolution."""
    px, py, pz = 7.6, SH - 39.5, -0.6
    g = fore.group("cards", (px, py, pz))
    w, h = CARD
    for k, angle in enumerate((-45, -22.5, 0, 22.5, 45)):
        z = pz - 0.3 - k * 0.25                            # each card just in front of the last
        g.box(f"card_{k}", (px, py - h / 2 + 0.6, z), (w, h, 0), "card", rotation=(0, 0, angle), origin=(px, py, z))


# ---- the head ----------------------------------------------------------------------------------------------------------

# The mask (session 5: the user loves the body, arms, legs and hat, and disliked the panelled porcelain mask entirely;
# three new masks are studied on the same body - s5_masks). Each sits in front of the face (its front 1.1 texels out,
# just behind the eye glints), its features painted in session 5.
MASK = "clown"


def mask_panels(head):
    """Take 1 (rejected): a centre panel and two turned side panels, a brow, cheekbones, a short nose and chin."""
    head.box("mask_centre", (0, YH - 0.5, ZF - 0.8), (8, 18, 1), "porcelain")
    for sx in (-1, 1):
        head.box(f"mask_side_{sx}", (sx * 5.6, YH - 0.5, ZF + 0.4), (3, 16, 1), "porcelain", rotation=(0, -sx * 22.5, 0))
        head.box(f"mask_socket_{sx}", (sx * 3.1, YH + 2.2, ZF - 1.15), (4, 2, 1), "socket", rotation=(0, 0, -sx * 22.5))
        head.box(f"mask_cheek_{sx}", (sx * 3.4, YH - 2.2, ZF - 1.7), (3, 2, 1), "porcelain", rotation=(0, 0, sx * 22.5))
    head.box("mask_brow", (0, YH + 4.4, ZF - 1.9), (10, 2, 2), "porcelain")
    head.box("mask_peak", (0, YH + 7.4, ZF - 1.1), (2, 3, 1), "porcelain", rotation=(0, 0, 45))
    head.box("mask_nose", (0, YH - 2.8, -7.2), (3, 6, 3), "porcelain")
    head.box("mask_chin", (0, YH - 10, ZF - 0.6), (3, 3, 1), "porcelain", rotation=(0, 0, 45))


def mask_volto(head):
    """A clean one-piece porcelain face: a smooth plate over the whole face, a low brow, a small nose, a pointed chin.
    Everything else is painted: a black harlequin diamond through one eye, a black tear under the other, small
    blood-red lips in a thin grin, a hairline crack."""
    head.box("mask_face", (0, YH - 0.5, ZF - 0.6), (12, 17, 1), "porcelain")
    head.box("mask_brow", (0, YH + 4.6, ZF - 1.4), (10, 1, 1), "porcelain")
    head.box("mask_nose", (0, YH - 1.6, ZF - 1.6), (2, 5, 2), "porcelain")
    head.box("mask_chin", (0, YH - 9.2, ZF - 0.6), (3, 3, 1), "porcelain", rotation=(0, 0, 45))


def mask_colombina(head):
    """A black domino mask over his eyes only, its wings swept up and out, trimmed in gold (painted); below it the
    illager's own long nose and grey face, a grin stitched across it (painted)."""
    head.box("nose", (0, YH - 5, -7), (3, 6, 3), "nose")
    head.box("mask_band", (0, YH + 2.2, ZF - 0.6), (13, 6, 1), "porcelain")
    for sx in (-1, 1):
        head.box(f"mask_wing_{sx}", (sx * 7.4, YH + 4.4, ZF - 0.4), (4, 2, 1), "porcelain", rotation=(0, 0, sx * 22.5))


def mask_comedy(head):
    """The theatre's comedy mask: a porcelain face with brows arched high, raised cheeks; painted, crescent eyes that
    smile and a huge grinning mouth, a black void."""
    head.box("mask_face", (0, YH - 0.5, ZF - 0.6), (12, 17, 1), "porcelain")
    for sx in (-1, 1):
        head.box(f"mask_brow_{sx}", (sx * 3, YH + 5.2, ZF - 1.4), (5, 1, 1), "porcelain", rotation=(0, 0, -sx * 22.5))
        head.box(f"mask_cheek_{sx}", (sx * 3.6, YH - 2.6, ZF - 1.4), (3, 2, 1), "porcelain")
    head.box("mask_nose", (0, YH - 0.8, ZF - 1.6), (2, 4, 2), "porcelain")


MOUTH_W = 5.0              # half the grin's width (take 4d: a little smaller overall)


def mouth_edges(x):
    """The grin's edges at x: the upper lip's gentle curve and the lower lip's deep U, meeting at the corners up in his
    cheeks."""
    return YH - 3.9 + 0.08 * x * x, YH - 7.0 + 0.2 * x * x


def mouth_curve(x):
    """The grin's centre line and half-height at x (from its edges)."""
    x = max(-MOUTH_W, min(MOUTH_W, x))
    up, low = mouth_edges(x)
    return (up + low) / 2, max(0.0, (up - low) / 2)


def _snap_angle(a):
    """The nearest turn that costs no display: 0, 22.5 or 45 degrees either way."""
    return min((-45, -22.5, 0, 22.5, 45), key=lambda s: abs(s - a))


def _lip(head, name, x0, x1, upper):
    """One segment of a lip, from x0 to x1 along the grin, turned to follow it (snapped to a free angle), sitting just
    outside the opening."""
    def edge(x):
        up, low = mouth_edges(x)
        return up if upper else low
    ya, yb = edge(x0), edge(x1)
    angle = _snap_angle(math.degrees(math.atan2(yb - ya, x1 - x0)))
    length = math.hypot(x1 - x0, yb - ya) + 1.1
    xm, ym = (x0 + x1) / 2, (ya + yb) / 2
    off = 0.8 if upper else -0.8
    nx, ny = -math.sin(math.radians(angle)), math.cos(math.radians(angle))
    head.box(name, (xm + nx * off, ym + ny * off, ZF - 1.4), (length, 1.6, 2.4), "lips", rotation=(0, 0, angle))


def mouth(head):
    """His mouth, built (take 4: the painted grin wrapped round blocky shapes and read as a texture on a mask): a
    gaping grin - a gently curved upper lip, a deep U of a lower lip, thick and red, in segments turned along it;
    inside, real teeth, each a block with a pointed tip, crooked and uneven, fangs among them, hanging from the upper
    lip and rising from the lower, set back behind the lips' front; behind them a dark throat. Round it (take 4d: the
    long, wide jaw looked out of proportion): white flesh under the lower lip, cheeks rounding over the corners, and a
    jaw of angled blocks narrowing in a V to a small chin."""
    for upper, tag, cuts in ((True, "upper", (0.0, 1.8, 3.2, 4.3, 4.9)),
                             (False, "lower", (0.0, 1.1, 2.1, 3.0, 3.8, 4.4, 4.9))):
        _lip(head, f"lip_{tag}_0", -cuts[1], cuts[1], upper)
        for i in range(1, len(cuts) - 1):
            for sx in (-1, 1):
                a, b = sorted((sx * cuts[i], sx * cuts[i + 1]))
                _lip(head, f"lip_{tag}_{i}_{sx}", a, b, upper)
    for row, (upper, xs) in enumerate(((True, [-3.8, -2.95, -2.1, -1.15, -0.25, 0.65, 1.5, 2.4, 3.3]),
                                       (False, [-3.1, -2.3, -1.5, -0.65, 0.25, 1.1, 1.9, 2.7]))):
        for k, x in enumerate(xs):
            up, low = mouth_edges(x)
            gap = up - low
            if gap < 1.2:
                continue
            fang = (abs(x - 2.4) < 0.2 or abs(x + 2.1) < 0.2) if upper else abs(abs(x) - 2.3) < 0.3
            length = (0.5 if fang else 0.24 + 0.12 * ((k * 7 + row * 3) % 5) / 4) * gap
            wide = 0.85 if fang else 0.6 + 0.25 * ((k * 5 + row) % 3) / 2
            root = up if upper else low
            sign = -1 if upper else 1
            body = max(0.3, length - wide * 0.45)
            name = f"tooth_{'upper' if upper else 'lower'}_{k}"
            head.box(name, (x, root + sign * body / 2, ZF - 0.9), (wide, body, 0.9), "teeth")
            head.box(f"{name}_tip", (x, root + sign * (body + wide * 0.12), ZF - 0.9), (wide * 0.7, wide * 0.7, 0.9),
                     "teeth", rotation=(0, 0, 45))
    for sx in (-1, 1):
        # the cheek (take 4g): a smooth plane under each eye, and over the grin's corner an apple pushed up by it
        head.box(f"cheekbone_{sx}", (sx * 3.4, YH + 0.0, ZF - 0.5), (3.6, 2.4, 1.0), "face")
        head.box(f"mouth_cheek_{sx}", (sx * 5.0, YH - 0.4, ZF - 0.8), (3.4, 2.6, 1.6), "face", rotation=(0, 0, sx * 22.5))
    jaw(head)


JAW = (0.0, 1.8, 3.4, 4.6, 5.5)    # where the jaw's segments break, out from the chin


def jaw_line(x):
    """The jaw's lower edge at x (take 4g): a narrow, round U from the chin up past the grin's corners."""
    return YH - 10.2 + 0.27 * x * x


def jaw(head):
    """The jaw (take 4g, after Pennywise sculpts and block-built clown faces: a round, narrow jaw curving under the
    grin to a pronounced chin): one continuous U of blocks whose lower edges follow jaw_line, each turned to a free
    angle and running back under the head as a volume; at its bottom a chin jutting forward and down, its front edge
    rounded by a turned prism."""
    thick, z0, z1 = 2.4, ZF - 1.0, ZF + 3.0
    for i in range(len(JAW) - 1):
        a, b = JAW[i], JAW[i + 1]
        ya, yb = jaw_line(a), jaw_line(b)
        angle = _snap_angle(math.degrees(math.atan2(yb - ya, b - a)))
        length = math.hypot(b - a, yb - ya) + 0.8
        nx, ny = -math.sin(math.radians(angle)), math.cos(math.radians(angle))
        for sx in ((1,) if a == 0 else (-1, 1)):
            xm, ym = sx * (a + b) / 2 if a else 0.0, (ya + yb) / 2
            ex = (-nx if sx < 0 else nx) * thick / 2
            if a == 0:
                xm, ex, length, angle = 0.0, 0.0, 2 * b + 0.4, 0
            head.box(f"jaw_{i}_{sx}", (xm + ex, ym + ny * thick / 2, (z0 + z1) / 2), (length, thick, z1 - z0), "face",
                     rotation=(0, 0, sx * angle))
    head.box("chin", (0, YH - 10.3, ZF - 1.7), (3.6, 2.6, 2.4), "face")
    head.box("chin_round", (0, YH - 11.6, ZF - 1.9), (3.6, 1.4, 1.4), "face", rotation=(45, 0, 0))


def mask_clown(head):
    """No mask: his own face, a horror clown's, sculpted in depth out from the illager's head. A heavy brow pinched
    down into a glare; deep sockets behind it with his cold eyes glinting far back; high cheekbones pushing up into the
    grin; a bulbous red nose; a huge grin stretched up into his cheeks, thick lips round an open dark mouth, rows of
    uneven teeth, longer fangs at the corners; a long pointed chin; wild tufts of hair under his hat. The greasepaint,
    the diamonds through his eyes, the smeared lipstick and the drips are painted (session 5)."""
    for sx in (-1, 1):
        head.box(f"brow_{sx}", (sx * 2.7, YH + 4.5, ZF - 0.9), (5, 1.6, 1.8), "face", rotation=(0, 0, sx * 22.5))
        head.box(f"brow_tail_{sx}", (sx * 5.4, YH + 5.2, ZF - 0.6), (1.8, 1.2, 1.2), "face", rotation=(0, 0, sx * 45))
    head.box("brow_furrow", (0, YH + 3.5, ZF - 0.7), (1.6, 1.6, 1.4), "face")
    head.box("nose_bridge", (0, YH + 1.8, ZF - 0.6), (2, 3, 1.2), "face")
    head.box("nose", (0, YH - 0.4, ZF - 2.4), (3.4, 3.4, 3.4), "rednose")
    head.box("nose_round_x", (0, YH - 0.4, ZF - 2.2), (4.4, 2.4, 2.6), "rednose")
    head.box("nose_round_y", (0, YH - 0.4, ZF - 2.2), (2.4, 4.4, 2.6), "rednose")
    mouth(head)
    # wild tufts of hair under his hat, angled out and down (the user preferred the first clown's angled tufts to the
    # ring - and more of them): five a side at different heights and depths, three angled down at the back
    for sx in (-1, 1):
        for k, (dy, dz, ang) in enumerate(((6.6, -2.6, 22.5), (5.0, -0.6, 45), (6.4, 1.4, 22.5), (4.4, 3.0, 45),
                                           (5.9, 4.6, 22.5))):
            head.box(f"hair_{sx}_{k}", (sx * 7.4, YH + dy, dz), (5, 2.2, 2.4), "hair", rotation=(0, 0, -sx * ang))
    for k, x in enumerate((-3.2, 0.0, 3.2)):
        head.box(f"hair_back_{k}", (x, YH + 5.4 - (k % 2) * 1.2, 7.2), (2.6, 2.2, 5), "hair", rotation=(22.5, 0, 0))

MASKS = {"panels": mask_panels, "volto": mask_volto, "colombina": mask_colombina, "comedy": mask_comedy,
         "clown": mask_clown}


def head_parts(head):
    head.box("head", (0, YH, 0), (11, 16, 11), "skin")
    MASKS[MASK](head)
    eyes = head.group("glow_eyes", (0, YH + 2.2, ZF - 1))
    deep = MASK == "clown"                                 # the clown's sockets are deep: the glint sits far back
    for sx in (-1, 1):                                     # a cold glint deep in each socket
        if deep:                                           # an illager's eye: white, a cyan iris, a dark pupil (painted)
            eyes.box(f"eye_{sx}", (sx * 3.1, YH + 2.2, ZF - 0.3), (2.6, 1.4, 0.4), "eye_glint")
        else:
            eyes.box(f"glint_{sx}", (sx * 3.1, YH + 2.2, ZF - 1.3), (1, 1, 0.4), "eye_glint")
    # the hat: band and cap on the head, three floppy points of three bones each (they flop)
    top = YH + 8
    head.box("hat_band", (0, top + 1.2, 0), (12, 3, 12), "crimson")
    head.box("hat_cap", (0, top + 4, 0.5), (11, 4, 11), "black")
    for name, base, turn, mats in (("hat_left", (-4, top + 5, 0), (0, 0, 1), ("black", "crimson")),
                                   ("hat_right", (4, top + 5, 0), (0, 0, -1), ("white", "black")),
                                   ("hat_back", (0, top + 5, 3.5), (1, 0, 0), ("crimson", "white"))):
        g, p = head, list(base)
        for k, (angle, length, w0) in enumerate(((40, 13, 6), (55, 12, 4.6), (55, 10, 3.4))):
            rot = tuple(angle * t for t in turn)
            g = g.group(f"{name}_{k}", tuple(p), rot)
            for j, (frac, wf) in enumerate(((0.3, 1.0), (0.75, 0.82))):          # each bone: two stepped boxes
                g.box(f"{name}_{k}_{j}", (p[0], p[1] + length * frac, p[2]), (w0 * wf, length * 0.55, w0 * wf),
                      mats[(k + j) % 2])
            p = [p[0], p[1] + length, p[2]]
        g.box(f"{name}_bell", (p[0], p[1] + 1.2, p[2]), (2, 2, 2), "gold")


# ---- the rig -----------------------------------------------------------------------------------------------------------

def build(name):
    model = Model(name)
    hips = model.group("hips", (0, HIP, 0))
    legs(hips)
    torso = hips.group("torso", (0, HIP, 0), (-8, 0, 0))
    torso.model = model
    torso_parts(torso)
    collar(torso)
    arms(torso)
    neck = torso.group("neck", (0, NECK, 0), (6, 0, 0))
    neck.box("neck_box", (0, NECK + 3, 0), (4, 7, 4), "face")   # his white greasepaint goes on down
    head = neck.group("hi_head", (0, NECK + 6, 0))
    head_parts(head)
    return model


_BUILD = build                     # his own builder (session 8's jack study swaps `build` out while it paints)
_NUDGES = {}


def finish(model):
    """Whole-texel sizes, the cards flat, and the flicker fix (session 8): no two faces share a plane (they z-fight in
    game; the teeth's tips shared their bodies' front and back). The smaller part of each clash moves a fraction of a
    texel off the plane (the Witch Coven's resolver); the nudges are found once in the rest pose and kept per cube, so
    every pose gets the same model, and sizes don't change, so the texture layout doesn't either. The jack (a model
    with a `spring` bone) gets its own nudges."""
    _finish_base(model)
    kind = "jack" if any(g.name == "spring" for g in model.groups) else "magus"
    if kind not in _NUDGES:
        _NUDGES[kind] = {}
        if kind == "jack":
            from bosses import magus_jack
            rest = magus_jack.build()
        else:
            rest = _BUILD("nudge_rest")
        _finish_base(rest)
        if kind == "jack":                         # the jack ships at half size: resolve it at that size
            magus_jack.settle(rest)
        from bosses.coven_s2 import _resolve
        nudges = {}
        _resolve(rest, nudges)
        if kind == "jack":                         # back to the frame it's built in (settle scales them again)
            nudges = {k: v / magus_jack.SCALE for k, v in nudges.items()}
        _NUDGES[kind] = nudges
    by_name = {c.name: c for c in model.cubes}
    for name, d in _NUDGES[kind].items():
        if name in by_name:
            c = by_name[name]
            c.frm, c.to, c.origin = [(np.array(v) + d).tolist() for v in (c.frm, c.to, c.origin)]


def _finish_base(model):
    v2.snap(model)
    for c in model.cubes:                                  # the cards stay flat planes (snapping makes them 1 thick)
        if c.name.startswith("card_"):
            mid = (c.frm[2] + c.to[2]) / 2
            c.frm[2] = c.to[2] = mid


def hitbox_bounds(model):
    """A column over his legs, body and head; not the hat, the arms, the coat's points or the bow."""
    keep = [c for c in model.cubes if c.group.name in ("hips", "torso", "neck", "hi_head", "leg_left", "leg_right",
                                                      "shin_left", "shin_right")]
    pts = np.vstack([c.corners() for c in keep])
    lo, hi = pts.min(0), pts.max(0)
    half = float(np.ceil(max(-lo[0], hi[0], 8)))
    return (-half, 0.0, float(np.floor(lo[2]))), (half, float(np.ceil(hi[1])), float(np.ceil(hi[2])))


# ---- poses -----------------------------------------------------------------------------------------------------------
# turns added to the rest per bone: (x, y, z)

POSES = {
    "idle": ("idle: hunched, his head tilted, the fan of cards hanging from his right hand", {
        "neck": (4, 0, 14), "arm_left": (8, 0, -6), "arm_right": (10, 0, 8), "forearm_right": (8, 0, 0)}),
    "throw": ("the card fans: a twist and a flick, his right arm flung out at his target, the fan of cards in his palm, "
              "his left arm swung back", {
        "hips": (0, -20, 0), "torso": (2, -24, 0), "neck": (-4, 40, 8),
        "leg_left": (16, 0, -8), "leg_right": (-14, 0, 8), "shin_right": (-12, 0, 0),
        "arm_right": (88, 0, 18), "forearm_right": (6, 0, 0), "arm_left": (-34, 0, -26), "forearm_left": (20, 0, 0)}),
    "prism": ("the prism burst: his arms raised overhead, the fan of cards held up to gather the light", {
        "torso": (12, 0, 0), "neck": (22, 0, 0), "arm_left": (172, 0, -14), "forearm_left": (10, 0, 0),
        "arm_right": (150, 0, 26), "forearm_right": (30, 0, 0), "hat_left_0": (0, 0, 14), "hat_right_0": (0, 0, -14)}),
    "curtsey": ("conjuring the decoys: a deep courtly bow, one arm sweeping out", {
        "torso": (-40, 0, 0), "neck": (-10, 0, 0), "arm_right": (-30, 0, 70), "forearm_right": (0, 0, 20),
        "arm_left": (30, 0, -10), "leg_right": (-20, 0, 0), "shin_right": (-30, 0, 0), "leg_left": (12, 0, 0)}),
    "blink": ("the blink: folding in on himself, arms wrapped, as he vanishes", {
        "torso": (-24, 0, 0), "neck": (-14, 0, 0), "arm_left": (60, 0, 50), "forearm_left": (0, 0, 70),
        "arm_right": (60, 0, -50), "forearm_right": (0, 0, -70), "leg_left": (40, 0, 0), "shin_left": (-70, 0, 0),
        "leg_right": (40, 0, 0), "shin_right": (-70, 0, 0)}),
    "laugh": ("a wrong hit: the decoy shatters and he laughs, head thrown back", {
        "torso": (16, 0, 0), "neck": (28, 0, -10), "arm_left": (20, 0, -30), "arm_right": (40, 0, 40),
        "forearm_right": (60, 0, 0), "hat_left_0": (0, 0, 20), "hat_right_0": (0, 0, -20), "hat_back_0": (20, 0, 0)}),
    "death": ("death: the strings cut - he crumples where he stands and sits slumped, legs out before him, folded "
              "forward over them, his head lolling, his arms limp beside him, the hat's points flopped down", {
        "leg_left": (90, 8, -10), "shin_left": (-4, 0, 0), "leg_right": (90, -10, 12), "shin_right": (-6, 0, 0),
        "torso": (-38, 0, 14), "neck": (-34, 14, 32), "coat": (132, 0, 0),
        "arm_left": (78, 0, -20), "forearm_left": (110, 0, 0), "arm_right": (82, 0, 22), "forearm_right": (106, 0, 0),
        "hat_left_0": (0, 0, 20), "hat_left_1": (0, 0, 30), "hat_right_0": (0, 0, -10), "hat_right_1": (0, 0, -24),
        "hat_back_1": (24, 0, 0)}),
}
# knees bend with a negative shin turn (a positive one swings the foot forward)
# the fan of cards is turned to a world orientation in the prism, whatever his arm does: held up, facing forward
CARD_AIM = {"prism": lambda: rotation_matrix((0, 0, 180))}


def pose(model, key):
    for bone, r in POSES[key][1].items():
        g = group(model, bone)
        g.rotation = [g.rotation[i] + r[i] for i in range(3)]
    if key in CARD_AIM:
        from bosses.unbound_s2 import aim
        aim(group(model, "cards"), CARD_AIM[key]())
    # whatever the pose, he stands (or kneels, or lies) on the floor: the lowest point is set down at 0
    d = float(model.bounds()[0][1])
    for g in model.groups:
        g.origin[1] -= d
    for c in model.cubes:
        c.frm[1] -= d
        c.to[1] -= d
        c.origin[1] -= d
    return d


def parts_list(model):
    rows = []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            parent = g.parent.name if g.parent is not None and g.parent.name != "root" else "-"
            rows.append(f"| `{g.name}` | {parent} | {len(cubes)} | {', '.join(sorted({c.mat for c in cubes}))} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


DESIGN_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.2, "dist": 9.5, "target_z": 2.8},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.8, "dist": 9, "target_z": 2.9,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_back", "mode": "clay", "camera": "persp", "yaw": 150, "height": 3.6, "dist": 9, "target_z": 2.9,
     "player": False},
]
POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 3.2, "dist": 10, "target_z": 2.6,
     "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    rest = build("occultech_mirrored_magus_blockout")
    finish(rest)
    frm, to = hitbox_bounds(rest)
    bb = rest.to_bbmodel()
    add_hitbox(bb, frm, to)
    (OUT / "occultech_mirrored_magus_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    total, per_bone = v3.display_count(rest)
    stats = dict(rest.stats(), displays=total, hitbox_blocks=[round((t - f) / 16, 2) for f, t in zip(frm, to)])
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    (OUT / "parts.md").write_text("# The Mirrored Magus's parts (session 2)\n\nGenerated by `tools/art/bosses/"
                                  "magus_s2.py`. Cube sizes are whole texels.\n\n" + parts_list(rest) + "\n",
                                  encoding="utf-8")
    v2.run_blender(rest.render_json(v2.PALETTE), OUT / "design", DESIGN_VIEWS)
    boxes = rest.render_json(v2.PALETTE)
    for b in boxes:
        b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
    boxes.append(v2.box_json("hitbox", frm, to, "hitbox"))
    v2.run_blender(boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                           {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
    for key in POSES:
        posed = build(key)
        finish(posed)
        pose(posed, key)
        v2.run_blender(posed.render_json(v2.PALETTE), OUT / "poses" / key, POSE_VIEWS)
    sheets(stats)
    print(json.dumps({k: stats[k] for k in ("cubes", "bones_with_geometry", "displays", "size_blocks", "hitbox_blocks")}))
    print({k: v for k, v in per_bone.items() if v > 1})


def sheets(stats):
    tw, th, pad, top = 400, 320, 12, 60
    font, small = sheet._font(26), sheet._font(17)
    cells = [(OUT / "design" / f"{v['name']}.png", v["name"].replace("_", " ")) for v in DESIGN_VIEWS] + \
            [(OUT / "hitbox" / "hitbox_front.png", "the hitbox (red), front"),
             (OUT / "hitbox" / "hitbox_side.png", "the hitbox (red), side")]
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"Mirrored Magus - design lock (session 2): {stats['cubes']} cubes, {stats['displays']} displays",
            font=font, fill=sheet.INK)
    for k, (path, label) in enumerate(cells):
        x, y = pad + (k % 3) * (tw + pad), top + (k // 3) * (th + 34 + pad)
        img.paste(sheet._tile(path, tw, th), (x, y))
        dr.text((x, y + th + 6), label, font=small, fill=sheet.DIM)
    img.save(OUT / "design.png")
    keys = list(POSES)
    for n, chunk in enumerate((keys[:4], keys[4:])):
        img = Image.new("RGB", (pad + 4 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), "Mirrored Magus - key poses (" + ", ".join(chunk) + ")", font=font, fill=sheet.INK)
        for k, key in enumerate(chunk):
            for v, view in enumerate(("flat_34", "sil_side")):
                x, y = pad + ((k % 2) * 2 + v) * (tw + pad), top + (k // 2) * (th + 34 + pad)
                img.paste(sheet._tile(OUT / "poses" / key / f"{view}.png", tw, th), (x, y))
                dr.text((x, y + th + 6), f"{key}: {'three-quarter' if v == 0 else 'side'}", font=small, fill=sheet.DIM)
        img.save(OUT / f"poses_{n + 1}.png")


if __name__ == "__main__":
    main()
