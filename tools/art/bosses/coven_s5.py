"""Witch Coven redesign, session 5: texture painting (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

Paints the session 4 layout (one shared 256 x 256 atlas for the three sisters, same islands), take 2 (more refined
after the user's review: finer ramps of 9-11 close shades, so detail can be subtle):
- fabric: the wool robe in soft rounded folds, darker to the hem, a stitched trim above it, vanilla's green stripe
  down its front; a ragged cut-out hem (torn strips, moth holes); the coat in a fine twill with grime, worn edges,
  stitched seams, horn buttons down its opening, a stitched patch; creases winding down the sleeves; frayed cuffs;
- skin: forehead creases each with a lit edge, dark eye sockets and bags, crow's feet, lit cheekbones over hollow
  cheeks, deep smile lines, a jaw in shadow, a wart, age spots, a reddened nose tip and nostrils; grey hair in strands;
- iron: hammered, a lit top edge and a shadowed foot on each panel, rivet rows with rust running from them, soot
  rising from the base, a worn rim and a dark wet inner wall; brass on the hat's band;
- bottles: the brew deeper at the bottom with a meniscus and a reflection down the glass, clear glass necks with
  bright edges, ringed corks;
- bubbles: a bright rim round a darker film with a highlight, on the bubble cubes and painted into the brew's surface;
- **the brew in neutral greys** (brew, foam, drips, steam, the bottles' liquid, the cast): in game the fight tints
  those bones the role colour (BetterModel's per-bone tint multiplies the texture). The role colours are potion tones
  that sit with the muted clothes (take 1's near-neon fought them);
- form only, no painted light direction: ambient occlusion baked from the real geometry. Shared body islands take
  their occlusion from the body alone, so one sister's ropes or pot never print on another's robe.

Run from the repository root: python tools/art/bosses/coven_s5.py
"""
import base64
import json
import shutil
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, brood_s5 as b5, coven_s2 as s2, coven_s3 as s3, coven_s4 as s4  # noqa: E402
from bosses import volley_crone_s3 as v3, volley_crone_s4 as v4, volley_crone_s5 as v5  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s5_paint"
noise = v5.noise
# The role colours BetterModel multiplies into the neutral brew: potion tones that sit with the muted clothes
# (session 5 take 1 used near-neon colours that fought them).
ROLE_TINT = {"green": (150, 214, 108), "purple": (176, 124, 212), "red": (220, 112, 88)}
TINTED = ("brew", "foam", "steam")          # zones on the tinted glow bones, painted in neutral greys


def make_ramp(dark, mid, light, n):
    """n shades from a cool dark through the zone's colour to a warm light: close steps, so detail can be subtle."""
    m = (n - 1) // 2
    out = []
    for i in range(n):
        a, b, t = (dark, mid, i / m) if i <= m else (mid, light, (i - m) / (n - 1 - m))
        out.append(tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3)))
    return out


RAMP = {
    "robe": make_ramp((12, 5, 24), (58, 28, 88), (124, 86, 142), 9),
    "coat": make_ramp((22, 17, 13), (84, 68, 46), (158, 136, 100), 9),
    "cuff": make_ramp((10, 8, 8), (32, 27, 22), (74, 64, 52), 5),
    "skin": make_ramp((90, 76, 84), (171, 159, 141), (232, 222, 202), 9),
    "nose": make_ramp((100, 82, 84), (166, 150, 134), (220, 204, 184), 7),
    "mole": make_ramp((54, 30, 22), (117, 71, 47), (172, 124, 92), 5),
    "hair": make_ramp((56, 54, 58), (150, 146, 140), (226, 222, 214), 7),
    "eye": [(36, 16, 52), (92, 50, 118), (138, 84, 164), (186, 140, 206), (236, 220, 244)],
    "hat": make_ramp((8, 8, 12), (46, 44, 52), (106, 102, 118), 9),
    "band": make_ramp((20, 38, 20), (56, 92, 46), (134, 178, 100), 7),
    "iron": make_ramp((20, 20, 28), (92, 92, 98), (182, 178, 172), 11),
    "rust": make_ramp((66, 36, 24), (126, 76, 46), (178, 120, 76), 5),
    "rope": make_ramp((66, 50, 32), (146, 124, 82), (206, 186, 140), 7),
    "strap": make_ramp((52, 34, 20), (122, 88, 54), (180, 142, 98), 7),
    "brass": make_ramp((80, 60, 30), (170, 138, 70), (238, 216, 152), 5),
    "glass": make_ramp((44, 58, 66), (118, 146, 152), (226, 240, 240), 7),
    "cork": make_ramp((70, 50, 30), (126, 96, 62), (186, 152, 110), 7),
    "herb": make_ramp((32, 42, 24), (86, 98, 58), (142, 154, 100), 7),
    "bone": make_ramp((124, 114, 96), (200, 190, 164), (242, 236, 218), 7),
    "neutral": make_ramp((58, 58, 58), (150, 150, 150), (242, 242, 242), 9),
}
# zone -> (ramp, base shade)
ZONE = {"robe": ("robe", 4), "robe_hem": ("robe", 3), "coat": ("coat", 4), "coat_dark": ("coat", 2),
        "cuff": ("cuff", 2), "skin": ("skin", 4), "nose": ("nose", 3), "mole": ("mole", 2), "brow": ("hair", 3),
        "eye": ("eye", 2), "hat": ("hat", 4), "hat_tip": ("hat", 2), "band": ("band", 3), "iron": ("iron", 5),
        "iron_dark": ("iron", 3), "rope": ("rope", 3), "strap": ("strap", 3), "buckle": ("brass", 2),
        "glass": ("glass", 3), "cork": ("cork", 3), "herb": ("herb", 3), "bone": ("bone", 3),
        "brew": ("neutral", 5), "foam": ("neutral", 7), "steam": ("neutral", 6)}


def zone_for(cube):
    """Session 4's zones, with every role colour folded into one neutral brew, foam or steam."""
    z = s4.zone_for(cube)
    for t in TINTED:
        if z.startswith(t + "_"):
            return t
    return z


def island_key(cube, face, w, h):
    name = cube.name
    if name.startswith("left_"):
        name = "right_" + name[5:]
    return (name, face, w, h, zone_for(cube))


def in_subtree(cube, names):
    g = cube.group
    while g is not None:
        if g.name in names:
            return True
        g = g.parent
    return False


def is_body(cube):
    """A part every sister shares (its islands are shared too)."""
    return not in_subtree(cube, {"vessel", "pot_carry", "bottle_held", "glow_cast"}) and not cube.name.startswith("rope_")


# ---- painters ------------------------------------------------------------------------------------------------------
# Each painter returns (lv, over): a shade map on the zone's ramp, and overlay pixels [(y, x, ramp, shade)] painted from
# another ramp (a stripe, rust, a button, a wart) after the ambient occlusion.

def blank(cube, w, h):
    return np.full((h, w), ZONE[zone_for(cube)][1], int), []


def clusters(seed, x, y, lo=170, hi=830, cell=2):
    r = noise(seed, x, y, cell)
    return -1 if r < lo else (1 if r > hi else 0)


def paint_robe(cube, face, w, h, seed):
    """Wool robe: soft rounded folds (light ridge, shaded valley), darker towards the hem, a stitched trim above it,
    vanilla's green stripe down the front."""
    lv, over = blank(cube, w, h)
    upright = face not in ("up", "down")
    phase = seed % 6
    for y in range(h):
        for x in range(w):
            if upright:
                lv[y, x] += int(round(1.3 * np.cos(2 * np.pi * (x + phase) / 6)))
                if y >= h - 3:
                    lv[y, x] -= 1
            lv[y, x] += clusters(seed + 3, x, y, 120, 900, 3)
    if cube.name == "robe_lower_box" and upright and h > 6:
        trim = h - 4
        for x in range(w):
            lv[trim, x] = 6 if x % 2 == 0 else 3                     # a stitched trim above the hem
            lv[trim + 1, x] = 2
        if face == "north":
            cx = w // 2
            for y in range(h):
                over.append((y, cx, "band", 3 if y % 3 else 4))      # vanilla's green stripe, a stitch every third row
                lv[y, cx - 1] -= 1
                lv[y, cx + 1] -= 1
    return lv, over


def paint_hem(cube, face, w, h, seed):
    """The hovering hem: torn strips of different lengths, moth holes, the seam where it hangs."""
    lv, over = paint_robe(cube, face, w, h, seed)
    lv -= 1
    alpha = np.full((h, w), 255, np.uint8)
    for x in range(w):
        tear = noise(seed + 11, x, 0, 1) % 4
        if tear:
            alpha[h - tear:, x] = 0
        if h - tear - 1 >= 0:
            lv[h - tear - 1, x] -= 1                                 # the torn edge darkens
    for y in range(1, h - 1):
        for x in range(w):
            if noise(seed + 13, x, y, 1) < 40:
                alpha[y, x] = 0                                      # moth holes
    lv[0, :] += 2                                                    # the seam where it hangs from the robe
    return lv, over, alpha


def paint_coat(cube, face, w, h, seed):
    """A wool coat: a fine diagonal twill, grime in clusters, worn top edges; seams with stitches, buttons down the
    opening, a stitched patch; creased sleeves."""
    lv, over = blank(cube, w, h)
    upright = face not in ("up", "down")
    n = cube.name
    for y in range(h):
        for x in range(w):
            if (x + y) % 4 == 0:
                lv[y, x] -= 1                                        # twill
            lv[y, x] += clusters(seed + 5, x, y, 70, 945, 3)
    if upright:
        lv[0, :] += 1                                                # worn top edge
    if n.startswith("robe_upper") and upright and w > 6:
        cx = w // 2
        if face == "north":
            lv[:, cx] -= 3                                           # the coat's front opening
            for y in range(1, h - 1, 4):
                over.append((y, cx + 1, "bone", 4))                  # horn buttons, each with its shadow
                over.append((y + 1, cx + 1, "coat", 2))
        elif face == "south":
            lv[:, cx] -= 1                                           # the back seam
            for y in range(0, h, 2):
                lv[y, cx + 1] += 2
        else:
            lv[:, cx] -= 1                                           # the side seams, stitched
            for y in range(1, h, 2):
                lv[y, cx - 1] += 2
        if n == "robe_upper_h" and face == "east" and h >= 8 and w >= 7:
            for y in range(2, 7):
                for x in range(1, 6):
                    edge = y in (2, 6) or x in (1, 5)
                    lv[y, x] = (6 if (x + y) % 2 else 2) if edge else 5   # a lighter patch, stitched on
    if n.endswith("_sleeve") and upright:
        for y in range(h):
            for x in range(w):
                if (y + x // 2) % 5 == 0:
                    lv[y, x] -= 2                                    # creases winding down the sleeve
                    if y > 0:
                        lv[y - 1, x] += 1                            # each crease's lit fold above it
    if n == "collar":
        lv[0, :] += 1
    return lv, over


def paint_cuff(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 150, 880)
    if face not in ("up", "down"):
        lv[0, :] += 1                                                # the cuff's seam
        for x in range(w):
            if noise(seed + 5, x, 0, 1) < 450:
                lv[h - 1, x] += 2                                    # frayed threads
    return lv, over


def paint_head(cube, face, w, h, seed):
    """An old face: forehead creases with a lit edge, dark eye sockets and bags, crow's feet, lit cheekbones over
    hollow cheeks, deep smile lines, a jaw in shadow, a wart, age spots; grey hair in strands at the back and sides."""
    lv, over = blank(cube, w, h)
    hair = np.full((h, w), -1, int)
    for y in range(h):
        for x in range(w):
            if noise(seed, x, y, 2) < 45:
                lv[y, x] -= 1                                        # age spots
    if face == "north":
        L, R = 3, w - 4                                              # the eyes' columns
        for y in range(h):
            for x in range(w):
                if y <= 3:
                    lv[y, x] += 1                                    # the forehead catches more light
                if x in (0, w - 1) and y <= 7:
                    lv[y, x] -= 1                                    # temples
        for y in (1, 3):
            for x in range(2, w - 2):
                if noise(seed + 1, x, y, 2) < 750:
                    lv[y, x] -= 2                                    # forehead creases...
                    lv[y - 1, x] += 1                                # ...each with its lit edge
        for c in (L, R):
            for y in (6, 7, 8):
                for x in (c - 1, c, c + 1):
                    lv[y, x] -= 1                                    # the eye sockets
            for x in (c - 1, c, c + 1):
                lv[9, x] -= 2                                        # bags under the eyes
                lv[10, x] += 1
        for (x, y) in ((0, 6), (1, 7), (0, 8)):
            lv[y, x] -= 2                                            # crow's feet
            lv[y, w - 1 - x] -= 2
        for x in (0, 1, w - 2, w - 1):
            lv[9, x] += 1                                            # lit cheekbones
            lv[10, x] += 1
            lv[11, x] -= 1                                           # hollow cheeks under them
            lv[12, x] -= 1
        for (x, y) in ((4, 10), (3, 11), (3, 12)):
            lv[y, x] -= 2                                            # smile lines from the nose
            lv[y, w - 1 - x] -= 2
        lv[h - 2:, :] -= 1                                           # the jaw in shadow
        lv[h - 1, :] -= 1
        over += [(11, w - 3, "mole", 3), (10, w - 3, "mole", 4), (11, w - 2, "mole", 2)]   # a wart on her cheek
    elif face in ("south", "east", "west"):
        lv[h - 3:, :] -= 1
        lv[h - 1, :] -= 1
        for x in range(w):
            back = face == "south" or (x < w // 2 if face == "east" else x >= w // 2)
            if not back:
                continue
            length = 6 + noise(seed + 2, x, 0, 1) % 6
            for y in range(min(h, length)):
                shade = 3 + (x % 3 == 0) - (x % 4 == 2)              # strands of three greys
                if y == length - 1:
                    shade += 1                                       # lighter tips
                hair[y, x] = max(0, shade - (1 if y == 0 else 0))
    return lv, over, hair


def paint_nose(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    if face == "north":
        lv[:, w // 2] += 1                                           # the bridge catches the light
        lv[h - 2:, :] += 1                                           # a reddened tip
    elif face == "down":
        lv[:, :] -= 1
        lv[h // 2, 0] = 0                                            # nostrils
        lv[h // 2, w - 1] = 0
    else:
        lv[h - 2:, :] -= 1
    return lv, over


def paint_brow(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += 1 if (x + y // 2) % 3 == 0 else (-1 if (x + y // 2) % 3 == 2 else 0)   # bristles
    lv[0, :] += 1                                                    # lighter tips
    lv[h - 1, :] -= 2                                                # dark roots under the shelf
    return lv, over


def paint_eye(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    if face == "north":
        lv[:, :] = 2
        lv[:, max(0, w // 2 - 1):w // 2 + 1] = 0                     # the pupil
        lv[0, 0] = 4                                                 # a catch-light
    return lv, over


def paint_mole(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    lv[0, 0] += 2
    lv[h - 1, :] -= 1
    return lv, over


def paint_hat(cube, face, w, h, seed):
    """Felt: soft mottling, a dent down the cone, a lit brim edge."""
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 160, 880, 3)
    n = cube.name
    if n == "hat_brim":
        if face == "up":
            for y in range(h):
                for x in range(w):
                    e = min(x, y, w - 1 - x, h - 1 - y)
                    lv[y, x] += 2 if e == 0 else (1 if e == 1 else 0)
        elif face == "down":
            lv[:, :] = 2
        else:
            lv[0, :] += 1
    elif face not in ("up", "down"):
        lv[:, w // 3] -= 1                                           # a dent down the cone
        lv[h - 1, :] -= 1                                            # where the tier sits in the one below
    return lv, over


def paint_band(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    for x in range(w):
        lv[0, x] += 1 if x % 2 == 0 else 0                           # woven
    lv[h - 1, :] -= 1
    if face == "north" and w >= 5:
        cx = w // 2                                                  # a brass buckle
        over += [(0, cx - 1, "brass", 3), (0, cx + 1, "brass", 3), (0, cx, "brass", 4),
                 (h - 1, cx - 1, "brass", 2), (h - 1, cx + 1, "brass", 2), (h - 1, cx, "band", 0)]
    return lv, over


def paint_iron(cube, face, w, h, seed):
    """Hammered iron in vanilla's cauldron greys: a lit top edge and a shadowed foot on each panel, seams at the
    corners, rivet rows with rust running from them, soot rising from the base, a worn rim, a dark wet inner wall."""
    lv, over = blank(cube, w, h)
    n = cube.name
    upright = face not in ("up", "down")
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 180, 830)               # hammer marks
    if n in ("cauldron", "pot") and upright:
        lv[0, :] += 2
        lv[1, :] += 1
        lv[:, 0] -= 1
        lv[:, w - 1] -= 1                                            # the seams where the plates meet
        for y in range(h):
            soot = (y - h * 0.55) / (h * 0.45)
            if soot > 0:
                for x in range(w):
                    if noise(seed + 7, x, y, 2) < 1000 * min(1, soot):
                        lv[y, x] -= 1 + (soot > 0.6)                 # soot rising from the fire
        for ry in (2, h - 4):
            for rx in range(2, w - 2, 4):
                lv[ry, rx] = 8                                       # a rivet...
                lv[ry + 1, rx] = 2                                   # ...and its shadow
                if ry == 2 and noise(seed + 21, rx, 0, 1) < 500:
                    run = 2 + noise(seed + 23, rx, 0, 1) % 5
                    for t in range(run):
                        if ry + 2 + t < h:
                            over.append((ry + 2 + t, rx, "rust", 3 if t == 0 else (2 if t < run - 1 else 1)))
        for y in range(h):
            for x in range(w):
                if noise(seed + 29, x, y, 2) < 25:
                    over.append((y, x, "rust", 2))                   # a few rust blooms
    elif n in ("cauldron", "pot") and face == "down":
        lv[:, :] = 1
    elif "lip" in n:
        inner = {"_n": "south", "_s": "north", "_w": "east", "_e": "west"}.get(n[-2:])
        if face == "up":
            lv[:, :] += 2
            for x in range(w):
                if noise(seed + 3, x, 0, 1) < 350:
                    lv[:, x] += 1                                    # worn bright where hands and ladles rub
        elif face == inner:
            lv[:, :] -= 3                                            # the dark, wet inner wall
        else:
            lv[0, :] += 1
    elif "band" in n and upright:
        for x in range(w):
            if x % 3 == 1:
                lv[0, x] = 7                                         # rivets along the band
        lv[h - 1, :] -= 1
    elif ("ear" in n or "handle" in n) and upright:
        lv[0, :] += 1
        if w >= 3 and h >= 3:
            lv[h // 2, w // 2] = 8
    elif "leg" in n or n == "pot_base":
        lv[h - 1, :] -= 1
    return lv, over


def paint_rope(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += (-1, 0, 1, 2)[(x + 2 * y) % 4]               # three twisted strands
    return lv, over


def paint_strap(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 150, 900, 3)
            if x in (0, w - 1) and w > 1:
                lv[y, x] -= 1
                if y % 2 == 0 and w >= 3:
                    lv[y, 1 if x == 0 else w - 2] += 2               # stitches along each edge
    return lv, over


def paint_buckle(cube, face, w, h, seed):
    lv = np.full((h, w), 3, int)
    if w >= 3 and h >= 3:
        lv[1:h - 1, 1:w - 1] = 0                                     # the buckle's opening
        lv[0, 0] = 4
    return lv, []


def paint_glass(cube, face, w, h, seed):
    """Bottle glass: clear (dark) in the middle, bright at the edges, a streak and a glint."""
    lv, over = blank(cube, w, h)
    lv[:, :] = 2
    for y in range(h):
        for x in range(w):
            if min(x, y, w - 1 - x, h - 1 - y) == 0:
                lv[y, x] = 3
    lv[:, 0] = 4
    if w >= 2 and h >= 2:
        lv[0, 0] = 6
    return lv, over


def paint_cork(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    if face == "up":
        for y in range(h):
            for x in range(w):
                lv[y, x] = 2 if min(x, y, w - 1 - x, h - 1 - y) == 0 else 4
    else:
        lv[0, :] += 1
        for y in range(h):
            for x in range(w):
                lv[y, x] += clusters(seed, x, y, 200, 950, 1)
    return lv, over


def paint_bottle_liquid(cube, face, w, h, seed):
    """The brew in a bottle (neutral, tinted in game): deeper towards the bottom, a bright surface over a meniscus
    line, a reflection streak down the glass and a glint."""
    lv, over = blank(cube, w, h)
    if face in ("up", "down"):
        lv[:, :] = 6 if face == "up" else 3
        return lv, over
    for y in range(h):
        lv[y, :] = 6 - (3 * y) // max(1, h)                          # deeper towards the bottom
    lv[0, :] = 7                                                     # the bright surface
    if w >= 3:
        lv[1:h - 1, 1] += 1                                          # a reflection down the glass
        lv[1, w - 2] = 8                                             # and a glint
    return lv, over


def paint_bubble(cube, face, w, h, seed):
    """A bubble: a bright rim round a thin, darker film, a highlight at its top corner."""
    if w >= 3 and h >= 3:
        lv = np.full((h, w), 4, int)
        for y in range(h):
            for x in range(w):
                if min(x, y, w - 1 - x, h - 1 - y) == 0:
                    lv[y, x] = 7
        lv[0, 0] = 8
    elif w >= 2 and h >= 2:
        lv = np.array([[8, 7], [7, 5]])[:h, :w]
    else:
        lv = np.full((h, w), 7 if (w == 1 and h == 1) else 5, int)  # a single bubble bright; a popping ring soft
        if w > 1:
            lv[:, ::3] = 6
    return lv, []


def paint_brew(cube, face, w, h, seed):
    """The brew's surface: soft blotches, darker where it meets the iron, bubbles of a few sizes rising through it
    (a bright rim, a darker film, a highlight); drips with a bright bead."""
    lv, over = blank(cube, w, h)
    n = cube.name
    if n.startswith("drip_"):
        lv[:, :] = 5
        if h >= 2:
            lv[h - 1, :] = 7
            lv[0, :] = 6
        return lv, over
    if n == "cast":
        for y in range(h):
            for x in range(w):
                lv[y, x] = 8 if min(x, y, w - 1 - x, h - 1 - y) > 0 else 6
        return lv, over
    if n.startswith(("bottle_",)):
        return paint_bottle_liquid(cube, face, w, h, seed)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed + 17, x, y, 160, 760, 3)
            if min(x, y, w - 1 - x, h - 1 - y) == 0 and face == "up" and n in ("brew", "pot_brew"):
                lv[y, x] -= 1                                        # darker where it meets the iron (not the dome)
    if face == "up" and w >= 6 and h >= 6:
        count = max(2, w * h // 70)
        for k in range(count):
            bx = 1 + noise(seed + 31, k, 0, 1) % (w - 3)
            by = 1 + noise(seed + 37, k, 0, 1) % (h - 3)
            if k % 3 == 0:                                           # a 3 x 3 bubble
                for dy in range(3):
                    for dx in range(3):
                        if by + dy < h and bx + dx < w:
                            lv[by + dy, bx + dx] = 6 if (dx in (0, 2) or dy in (0, 2)) else 4
                lv[by, bx] = 7
            else:                                                    # a 2 x 2 bubble
                lv[by, bx], lv[by, bx + 1], lv[by + 1, bx], lv[by + 1, bx + 1] = 7, 6, 6, 5
        for k in range(2 if w >= 10 else 1):                         # popping rings: a pale ring, the brew inside
            rx = 1 + noise(seed + 41, k, 0, 1) % max(1, w - 6)
            ry = 1 + noise(seed + 43, k, 0, 1) % max(1, h - 6)
            for dy in range(5):
                for dx in range(5):
                    ring = dx in (0, 4) or dy in (0, 4)
                    corner = dx in (0, 4) and dy in (0, 4)
                    if ring and not corner and ry + dy < h and rx + dx < w:
                        lv[ry + dy, rx + dx] = 6
    return lv, over


def paint_steam(cube, face, w, h, seed):
    lv = np.full((h, w), 7, int)
    if w >= 2 and h >= 2:
        for y in range(h):
            for x in range(w):
                if x in (0, w - 1) and y in (0, h - 1):
                    lv[y, x] = 5                                     # soft, rounded corners
                elif min(x, y, w - 1 - x, h - 1 - y) == 0:
                    lv[y, x] = 6
    return lv, []


def paint_herb(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    for y in range(h):
        for x in range(w):
            lv[y, x] += clusters(seed, x, y, 220, 760, 1)
    if face not in ("up", "down") and h >= 4:
        for x in range(w):
            over.append((h // 2, x, "rope", 4))                     # the twine binding the bundle
    return lv, over


def paint_bone(cube, face, w, h, seed):
    lv, over = blank(cube, w, h)
    lv[0, :] += 1
    lv[h - 1, :] -= 1
    return lv, over


def painter_for(cube):
    z, n = zone_for(cube), cube.name
    if n == "head":
        return paint_head
    if n.startswith("hem_"):
        return paint_hem
    if n in ("bubble_0", "bubble_1", "bubble_2", "bubble_3", "bubble_4") or n.startswith("ring_"):
        return paint_bubble
    return {"robe": paint_robe, "robe_hem": paint_robe, "coat": paint_coat, "coat_dark": paint_coat, "cuff": paint_cuff,
            "skin": paint_head, "nose": paint_nose, "mole": paint_mole, "brow": paint_brow, "eye": paint_eye,
            "hat": paint_hat, "hat_tip": paint_hat, "band": paint_band, "iron": paint_iron, "iron_dark": paint_iron,
            "rope": paint_rope, "strap": paint_strap, "buckle": paint_buckle, "glass": paint_glass, "cork": paint_cork,
            "herb": paint_herb, "bone": paint_bone, "brew": paint_brew, "foam": paint_bubble,
            "steam": paint_steam}[z]


def from_levels(lv, ramp, alpha=None):
    lv = np.clip(lv, 0, len(ramp) - 1)
    rgb = np.array(ramp, np.uint8)[lv]
    a = np.full(lv.shape + (1,), 255, np.uint8) if alpha is None else alpha[..., None].astype(np.uint8)
    return np.concatenate([rgb, a], -1)


def paint_face(model, i, face, w, h, solids_all, solids_body):
    cube = model.cubes[i]
    seed = zlib.crc32(f"{cube.name}/{face}".encode())
    zone = zone_for(cube)
    result = painter_for(cube)(cube, face, w, h, seed)
    alpha = hair = None
    if cube.name.startswith("hem_"):
        lv, over, alpha = result
    elif cube.name == "head":
        lv, over, hair = result
    else:
        lv, over = result
    if zone not in TINTED:
        ao = b5.occlusion(model, i, face, w, h, solids_body if is_body(cube) else solids_all)
        lv = lv - (ao >= 0.3) - (ao >= 0.55)
    ramp = RAMP[ZONE[zone][0]]
    out = from_levels(lv, ramp, alpha)
    if hair is not None and (hair >= 0).any():
        hl = from_levels(np.maximum(hair, 0), RAMP["hair"])
        out[hair >= 0] = hl[hair >= 0]
    for y, x, rname, shade in over:
        if 0 <= y < h and 0 <= x < w:
            r = RAMP[rname]
            out[y, x, :3] = r[max(0, min(len(r) - 1, shade))]
    return out


def build_atlas(models, keys, positions):
    owner = {}
    for mi, k in enumerate(keys):
        for (i, f), key in sorted(k.items(), key=lambda kv: (kv[0][0], FACES.index(kv[0][1]))):
            owner.setdefault(key, (mi, i, f))
    solids = []
    for m in models:
        everything = b5.solids_of(m)
        body = [s for s in everything if is_body(m.cubes[s[0]])]
        solids.append((everything, body))
    height = max(y + h for (_, y, _, h) in positions.values()) + 1
    height = 256 if height <= 256 else 512
    atlas = Image.new("RGBA", (s4.SIZE, height), (0, 0, 0, 0))
    for key, (x, y, w, h) in positions.items():
        mi, i, f = owner[key]
        cube = models[mi].cubes[i]
        patch = Image.fromarray(paint_face(models[mi], i, f, w, h, *solids[mi]), "RGBA")
        if not cube.name.startswith("hem_"):           # cut-out planes keep a clear border
            atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    return atlas


def tinted(atlas, positions, role):
    """The atlas as one sister looks in the fight: every brew, foam and steam island multiplied by her role colour."""
    img = np.array(atlas).astype(int)
    tint = np.array(ROLE_TINT[role])
    for key, (x, y, w, h) in positions.items():
        if key[4] in TINTED:
            img[y - 1:y + h + 1, x - 1:x + w + 1, :3] = img[y - 1:y + h + 1, x - 1:x + w + 1, :3] * tint // 255
    return Image.fromarray(img.astype(np.uint8), "RGBA")


VIEWS = s4.VIEWS + [
    {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 0, 1.9), "scale": 8, "player": False,
     "res": (640, 480)},
    {"name": "vessel", "location": (3.6, -3.2, 4.2), "target": (0, -0.6, 2.1), "scale": 2.6, "player": False},
]
VESSEL_VIEW = {   # each sister's close-up of her vessel
    "cauldron": {"name": "vessel", "location": (3.6, -3.2, 4.2), "target": (0, -0.6, 2.1), "scale": 2.6, "player": False},
    "bottles": {"name": "vessel", "location": (-1.8, 4.2, 2.6), "target": (0.1, 0.4, 1.9), "scale": 2.0, "player": False},
    "pot": {"name": "vessel", "location": (1.6, 4.0, 3.3), "target": (0, 0.9, 1.3), "scale": 2.0, "player": False},
}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    models, keys, sizes = [], [], {}
    for vessel, role, _ in s2.SISTERS:
        m = s2.build(vessel, role)
        m.name = s3.model_id(vessel)
        k = {}
        for i, c in enumerate(m.cubes):
            for f in FACES:
                w, h = v4.face_size(c, f)
                if not w or not h or b4.hidden(c, f):
                    continue
                k[(i, f)] = island_key(c, f, w, h)
                sizes[k[(i, f)]] = (w, h)
        models.append(m)
        keys.append(k)
    positions, used, height = b4.pack(sizes)
    atlas = build_atlas(models, keys, positions)
    atlas_path = OUT / "occultech_coven.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 2, atlas.height * 2), Image.NEAREST).save(OUT / "atlas_preview.png")

    for (vessel, role, title), model, k in zip(s2.SISTERS, models, keys):
        out = OUT / vessel
        out.mkdir()
        preview = tinted(atlas, positions, role)
        preview_path = out / f"occultech_coven_{role}.png"
        preview.save(preview_path)
        # the review rig carries the tinted atlas so it looks right in game before session 6 wires the tint
        bb, _ = s4.rig_bbmodel(model, k, positions, preview_path, atlas.height, s3.pose_table(vessel, role))
        for element, cube in zip(bb["elements"], model.cubes):      # the hitbox element comes last
            element["light_emission"] = 15 if zone_for(cube) in TINTED else 0
        path = out / f"{model.name}.bbmodel"
        path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        if s3.SERVER_MODELS.is_dir():
            shutil.copyfile(path, s3.SERVER_MODELS / path.name)
        boxes = [{"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": zone_for(c) in TINTED,
                  "uv": bb["elements"][i]["faces"]} for i, c in enumerate(model.cubes)]
        job_file = out / "render_job.json"
        job_file.write_text(json.dumps({"texture": str(preview_path), "out": (out / "renders").as_posix(),
                                        "boxes": boxes, "views": VIEWS[:-1] + [VESSEL_VIEW[vessel]],
                                        "player_at": (2.0, 1.6)}), encoding="utf-8")
        (out / "renders").mkdir()
        import subprocess
        result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                                 str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job_file)],
                                capture_output=True, text=True)
        if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
            raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
        job_file.unlink()
        names = [v["name"] for v in VIEWS]
        tw, th, pad, top, cols = 470, 352, 12, 56, 4
        rows = (len(names) + cols - 1) // cols
        img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 12), f"Witch Coven - {title}, painted (session 5; brew shown in her role colour)",
                font=sheet._font(28), fill=sheet.INK)
        for n, name in enumerate(names):
            x, y = pad + (n % cols) * (tw + pad), top + (n // cols) * (th + 34 + pad)
            img.paste(sheet._tile(out / "renders" / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), name.replace("_", " "), font=sheet._font(17), fill=sheet.DIM)
        img.save(out / "sheet.png")
        print(vessel, "painted")
    print(json.dumps({"atlas": [s4.SIZE, atlas.height], "rows_used": used, "islands": len(positions)}))


if __name__ == "__main__":
    main()
