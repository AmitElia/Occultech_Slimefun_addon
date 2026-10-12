"""Mire Monarch redesign, step 1 of the agreed plan: flat silhouette thumbnails (side and front) of three postures.

The brief (revised 2026-10-11 after take 5 was rejected): a toad mutant monster, intimidating not goofy; not vanilla
geometry, but at home in Minecraft (a Dungeons-style mob or a good mod) and in the other bosses' style. The mouth is
the weapon (a body-wide jaw, an overbite, slightly open); small glowing slit eyes deep under a heavy brow; a tiny crown
between the eyes; a few large burst warts on the back; front-heavy and loaded to leap; few parts.

Shapes are drawn as angular polygons and turned rectangles, so whatever is picked can be built from cuboids.
Units are model pixels (16 = one block); the blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/monarch_silhouettes.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/bosses/mire_monarch/overhaul/s1_silhouettes"
S = 3.7                     # screen pixels per model pixel
BG, INK, DIM = (24, 22, 28), (236, 228, 214), (150, 142, 132)
PAPER = (244, 241, 234)
SIL = (34, 33, 40)
PLAYER = (150, 178, 222)
# value sketch: a dark body, a slightly lighter jaw and belly, a darker far side, the glow
TONE = {"far": (30, 34, 26), "body": (58, 66, 40), "jaw": (66, 72, 46), "shade": (22, 24, 18), "maw": (20, 12, 10), "glow": (176, 255, 40),
        "hot": (236, 255, 160), "crown": (214, 168, 52), "wart": (70, 76, 44)}


# ---- shape helpers (model units, y up) ---------------------------------------------------------------------------

def rect(cx, cy, w, h, ang=0.0):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return [(cx + dx * c - dy * s, cy + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2),
                                                                         (w / 2, h / 2), (-w / 2, h / 2))]


def limb(a, b, w0, w1):
    """A tapered segment from a (w0 wide) to b (w1 wide)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    return [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
            (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]


def octagon(cx, cy, rx, ry=None):
    ry = ry or rx
    k = 0.42
    return [(cx + px * rx, cy + py * ry) for px, py in ((-k, -1), (k, -1), (1, -k), (1, k), (k, 1), (-k, 1), (-1, k), (-1, -k))]


def wart(cx, cy, r, tilt=0.0):
    """A big burst wart: an angular lump with a glowing split on top."""
    body = [(cx - r, cy - r * 0.4), (cx - r * 0.8, cy + r * 0.5), (cx - r * 0.3, cy + r * 0.9), (cx + r * 0.35, cy + r * 0.85),
            (cx + r * 0.85, cy + r * 0.45), (cx + r, cy - r * 0.4)]
    split = rect(cx, cy + r * 0.62, r * 0.9, r * 0.32, tilt)
    return [("wart", body), ("glow", split)]


def crown(cx, base, w):
    """The tiny crown: a band and three points."""
    h = w * 0.35
    pts = [(cx - w / 2, base), (cx + w / 2, base), (cx + w / 2, base + h), (cx + w / 2, base + h + w * 0.42),
           (cx + w / 4, base + h + w * 0.1), (cx, base + h + w * 0.5), (cx - w / 4, base + h + w * 0.1),
           (cx - w / 2, base + h + w * 0.42), (cx - w / 2, base + h)]
    return [("crown", pts)]


def frown(half, y, drop, thick=4.0):
    """The front mouth: a dark band whose corners turn down."""
    return [("maw", [(-half, y - drop), (-half * 0.62, y), (half * 0.62, y), (half, y - drop), (half - 2, y - drop - thick),
                     (half * 0.62 - 1, y - thick), (-half * 0.62 + 1, y - thick), (-half + 2, y - drop - thick)])]


def socket(cx, cy, w, ang):
    """A glowing slit deep in the shadow under the brow: the inner end dips (a scowl)."""
    return [("shade", rect(cx, cy + 0.5, w * 1.35, w * 0.62, ang))] + slit(cx, cy, w, ang)


def slit(cx, cy, w, ang):
    return [("glow", rect(cx, cy, w, w * 0.3, ang)), ("hot", rect(cx, cy, w * 0.45, w * 0.14, ang))]


# ---- the three postures ------------------------------------------------------------------------------------------
# Each returns (side, front): lists of (tone, polygon), drawn in order. Side views face left (-z is the front).

def predator():
    """A: the crouched predator. Head low and level with the shoulders, a body-wide jaw, thick forearms planted wide,
    the back rising to a hump over the hips, hind legs coiled under it."""
    side = []
    side += [("far", limb((-16, 26), (-8, 12), 13, 11)), ("far", limb((-8, 12), (-24, 2), 11, 9)),
             ("far", [(-36, 0), (-16, 0), (-18, 4), (-32, 4)])]
    side += [("far", rect(26, 22, 32, 18, -22))]
    body = [(-50, 26), (-46, 32), (-36, 40), (-26, 41), (-12, 46), (6, 51), (22, 57), (34, 52), (46, 34), (44, 18),
            (32, 12), (6, 9), (-18, 11), (-40, 11), (-49, 15)]
    side += [("body", body)]
    side += [("jaw", [(-46, 17), (-18, 15), (-18, 11), (-40, 11), (-45, 14)])]                  # the lower jaw
    side += [("maw", [(-50, 22), (-16, 18.5), (-16, 16), (-46, 17.5)])]                       # the open mouth
    side += [("body", [(-38, 40), (-24, 43), (-22, 38), (-36, 36)])]                          # the brow ridge
    side += socket(-31, 34.5, 7, -12)
    side += crown(-33, 41, 8)
    side += [("wart", octagon(-14, 46, 7, 4))] + [("glow", rect(-14, 49.5, 6, 1.4))]          # the poison gland
    for x, y, r in ((2, 52, 6), (16, 57, 7), (30, 55, 6), (40, 44, 5)):
        side += wart(x, y, r, -10)
    side += [("body", rect(24, 22, 32, 18, -22)), ("body", limb((8, 26), (38, 5), 10, 8)),
             ("body", [(42, 0), (14, 0), (16, 4), (38, 4)])]
    side += [("body", limb((-18, 28), (-10, 12), 15, 12)), ("body", limb((-10, 12), (-26, 2), 12, 10)),
             ("body", [(-40, 0), (-16, 0), (-18, 5), (-34, 5)])]

    front = []
    front += [("far", octagon(0, 30, 38, 26))]                                                # the hump behind
    for sd in (-1, 1):
        front += [("far", rect(sd * 38, 22, 16, 26, sd * 10))]                                 # thighs at the sides
        front += [("body", limb((sd * 26, 26), (sd * 44, 16), 15, 13)), ("body", limb((sd * 44, 16), (sd * 40, 2), 13, 11)),
                  ("body", [(sd * 30, 0), (sd * 52, 0), (sd * 50, 5), (sd * 32, 5)])]
    front += [("body", [(-34, 14), (-34, 30), (-26, 40), (26, 40), (34, 30), (34, 14), (28, 10), (-28, 10)])]
    front += [("jaw", [(-30, 17), (30, 17), (27, 11), (-27, 11)])]
    front += frown(34, 22, 5)
    front += [("body", [(-28, 40), (-6, 38), (-4, 34), (-24, 35)]), ("body", [(28, 40), (6, 38), (4, 34), (24, 35)])]
    for sd in (-1, 1):
        front += socket(sd * 15, 32.5, 9, -sd * 16)
        front += wart(sd * 22, 44, 5)
    front += crown(0, 38, 8)
    return side, front


def brute():
    """B: the brute. Gorilla-built: a hump of muscle and warts over huge shoulders, enormous forearms planted ahead,
    the head hanging low and forward between them, a small coiled rear."""
    side = []
    side += [("far", limb((-12, 44), (-4, 22), 19, 15)), ("far", limb((-4, 22), (-28, 3), 15, 13)),
             ("far", [(-44, 0), (-18, 0), (-20, 5), (-38, 5)])]
    side += [("far", rect(28, 16, 24, 14, -18))]
    body = [(-48, 20), (-44, 28), (-34, 34), (-24, 40), (-16, 52), (-6, 61), (8, 58), (22, 46), (36, 34), (42, 24),
            (38, 12), (20, 14), (0, 18), (-20, 16), (-38, 8), (-47, 12)]
    side += [("body", body)]
    side += [("jaw", [(-45, 14), (-22, 12), (-22, 8), (-38, 8), (-44, 11)])]
    side += [("maw", [(-48, 19), (-20, 15.5), (-20, 12.5), (-45, 14.5)])]
    side += [("body", [(-38, 34), (-24, 38), (-22, 33), (-36, 31)])]
    side += socket(-31, 29, 7, -14)
    side += crown(-32, 35, 7)
    for x, y, r in ((-10, 59, 7), (4, 59, 7), (18, 49, 6), (32, 37, 5)):
        side += wart(x, y, r, -12)
    side += [("body", rect(28, 16, 24, 14, -18)), ("body", limb((14, 18), (40, 4), 9, 7)),
             ("body", [(44, 0), (20, 0), (22, 4), (40, 4)])]
    side += [("body", limb((-12, 46), (-2, 22), 21, 16)), ("body", limb((-2, 22), (-28, 3), 16, 14)),
             ("body", [(-46, 0), (-18, 0), (-20, 6), (-40, 6)])]

    front = []
    front += [("far", octagon(0, 44, 30, 18))]
    for sd in (-1, 1):
        front += [("far", rect(sd * 30, 14, 12, 18, 0))]
        front += [("body", limb((sd * 32, 48), (sd * 46, 24), 20, 16)), ("body", limb((sd * 46, 24), (sd * 42, 3), 17, 15)),
                  ("body", [(sd * 30, 0), (sd * 56, 0), (sd * 54, 6), (sd * 32, 6)])]
        front += wart(sd * 14, 58, 7)
    front += [("body", octagon(0, 50, 34, 12))]                                               # the shoulder yoke
    front += [("body", [(-26, 10), (-27, 26), (-20, 36), (20, 36), (27, 26), (26, 10), (20, 7), (-20, 7)])]
    front += [("jaw", [(-23, 14), (23, 14), (20, 8), (-20, 8)])]
    front += frown(27, 19, 4)
    front += [("body", [(-22, 36), (-5, 34), (-3, 30), (-19, 31)]), ("body", [(22, 36), (5, 34), (3, 30), (19, 31)])]
    for sd in (-1, 1):
        front += socket(sd * 12, 28.5, 8, -sd * 16)
    front += crown(0, 33, 7)
    return side, front


def lurker():
    """C: the lurker. Low, long and very wide, the head nearly half its length and almost all mouth, elbows cocked
    high like a crocodile's, a ridge of big warts along a flat back."""
    side = []
    side += [("far", limb((-24, 18), (-18, 28), 11, 10)), ("far", limb((-18, 28), (-34, 2), 10, 9)),
             ("far", [(-46, 0), (-26, 0), (-28, 4), (-42, 4)])]
    side += [("far", rect(30, 14, 30, 12, -8))]
    body = [(-60, 18), (-56, 24), (-44, 30), (-30, 31), (-12, 35), (10, 40), (28, 40), (42, 30), (48, 18), (40, 8),
            (10, 6), (-20, 6), (-48, 5), (-59, 10)]
    side += [("body", body)]
    side += [("jaw", [(-56, 11), (-20, 9), (-20, 6), (-48, 5), (-55, 8)])]
    side += [("maw", [(-60, 17), (-18, 13), (-18, 9.5), (-56, 11.5)])]
    side += [("body", [(-46, 31), (-30, 34), (-28, 29), (-44, 27)])]
    side += socket(-38, 26, 7, -10)
    side += crown(-39, 31.5, 7)
    for x, y, r in ((-8, 36, 6), (8, 41, 7), (24, 42, 7), (38, 34, 5)):
        side += wart(x, y, r, -8)
    side += [("body", rect(30, 14, 30, 12, -8)), ("body", limb((18, 12), (50, 3), 8, 6)),
             ("body", [(66, 0), (40, 0), (42, 3), (62, 3)])]
    side += [("body", limb((-24, 18), (-16, 30), 13, 12)), ("body", limb((-16, 30), (-34, 2), 12, 10)),
             ("body", [(-48, 0), (-24, 0), (-26, 5), (-42, 5)])]

    front = []
    front += [("far", octagon(0, 22, 44, 18))]
    for sd in (-1, 1):
        front += [("far", rect(sd * 46, 12, 18, 12, sd * 6))]
        front += [("body", limb((sd * 34, 16), (sd * 54, 28), 13, 11)), ("body", limb((sd * 54, 28), (sd * 52, 2), 11, 10)),
                  ("body", [(sd * 42, 0), (sd * 64, 0), (sd * 62, 5), (sd * 44, 5)])]
        front += wart(sd * 18, 38, 6)
    front += [("body", [(-40, 6), (-41, 20), (-32, 30), (32, 30), (41, 20), (40, 6), (34, 4), (-34, 4)])]
    front += [("jaw", [(-37, 10), (37, 10), (33, 5), (-33, 5)])]
    front += frown(41, 16, 5)
    front += [("body", [(-30, 31), (-7, 29), (-5, 25), (-26, 26)]), ("body", [(30, 31), (7, 29), (5, 25), (26, 26)])]
    for sd in (-1, 1):
        front += socket(sd * 16, 24, 9, -sd * 14)
    front += crown(0, 29, 7)
    return side, front


POSTURES = [("A", "The Crouched Predator", predator), ("B", "The Brute", brute), ("C", "The Lurker", lurker)]


# ---- drawing ----------------------------------------------------------------------------------------------------

def draw(shapes, view, mode, w=560, h=330):
    img = Image.new("RGB", (w, h), PAPER if mode == "sil" else (52, 50, 60))
    d = ImageDraw.Draw(img)
    ox, oy = w / 2 + (40 if view == "side" else -20), h - 34

    def tr(p):
        return (ox + p[0] * S, oy - p[1] * S)

    if mode == "value":
        d.rectangle((0, oy, w, h), fill=(44, 42, 50))
    d.line((0, oy, w, oy), fill=(120, 116, 110) if mode == "sil" else (80, 78, 88), width=2)
    for tone, poly in shapes:
        col = SIL if mode == "sil" else TONE[tone]
        d.polygon([tr(p) for p in poly], fill=col)
    # the player, 1.8 blocks: beside the model
    px = (-82 if view == "side" else 76) * S + ox
    ph = 28.8 * S
    pw = 7.2 * S
    d.rectangle((px - pw / 2, oy - ph * 0.75, px + pw / 2, oy), fill=PLAYER)
    d.rectangle((px - pw * 0.55, oy - ph, px + pw * 0.55, oy - ph * 0.75), fill=PLAYER)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        font, small = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 30), ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 19)
    except OSError:
        font = small = ImageFont.load_default()
    cw, ch, pad, top, lab = 560, 330, 12, 64, 40
    cols = [("side", "sil"), ("front", "sil"), ("side", "value"), ("front", "value")]
    W = pad + len(cols) * (cw + pad)
    H = top + len(POSTURES) * (ch + lab + pad)
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 14), "Mire Monarch - three postures (silhouette and value), the blue figure is a player",
            font=font, fill=INK)
    for r, (key, title, fn) in enumerate(POSTURES):
        side, front = fn()
        y = top + r * (ch + lab + pad)
        dr.text((pad, y + 6), f"{key}  {title}", font=font, fill=INK)
        for c, (view, mode) in enumerate(cols):
            img = draw(side if view == "side" else front, view, mode, cw, ch)
            img.save(OUT / f"{key}_{view}_{mode}.png")
            sheet.paste(img, (pad + c * (cw + pad), y + lab))
    sheet.save(OUT / "silhouettes.png")
    print("wrote", OUT / "silhouettes.png")


if __name__ == "__main__":
    main()
