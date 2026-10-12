"""Witch Coven redesign, step 1 (take 2): the three sisters on the user's body (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

The body (user, 2026-10-11): a villager with a hunched, big back, larger than a player. The robe falls straight, like
a villager's, with no flare. When she hovers, a flat ragged hem (a 2D plane, ragged in its texture) hangs below it.
A real witch's hat. No fingers: the sleeves end in dark cuffs. The sisters are the same size and differ only by their
vessels:
  1  the cauldron   an extra-large cauldron hung on her hunched back, tied on with ropes round her middle; her
                    sleeves are free to cast and throw
  2  the bottles    a diagonal shoulder belt of large potion bottles, and one bottle held up in her sleeve
  3  the pot        a pot held out in front of her in both sleeves
The brew's colour is the role (green healer, purple curser, red bomber); each sister is shown in one.

Shapes are angular polygons and turned rectangles, buildable from cuboids. Units are model pixels (16 = one block).
Run from the repository root: python tools/art/bosses/coven_lineup.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s1_lineup"
S = 3.9
BG, INK = (24, 22, 28), (236, 228, 214)
PLAYER = (150, 178, 222)
SIL = (34, 33, 40)
TONE = {"robe": (66, 56, 46), "robe_dark": (48, 40, 33), "hem": (56, 47, 38), "sleeve": (58, 49, 40),
        "cuff": (30, 25, 21), "skin": (150, 128, 98), "nose": (136, 114, 86), "wart": (96, 120, 60), "brow": (70, 56, 44),
        "eye": (40, 70, 40), "hat": (42, 34, 50), "band": (84, 98, 54), "iron": (56, 54, 60), "iron_dark": (34, 33, 38),
        "rope": (150, 128, 84), "glass": (150, 170, 170), "cork": (120, 92, 60), "strap": (82, 60, 40),
        "herb": (86, 96, 58), "bone": (196, 186, 160)}
ROLE = {"green": ((110, 230, 90), (170, 240, 150)), "purple": ((170, 70, 220), (200, 150, 235)),
        "red": ((230, 70, 60), (240, 150, 130))}


def rect(cx, cy, w, h, ang=0.0):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return [(cx + dx * c - dy * s, cy + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2),
                                                                         (w / 2, h / 2), (-w / 2, h / 2))]


def octagon(cx, cy, rx, ry=None):
    ry = ry or rx
    k = 0.42
    return [(cx + px * rx, cy + py * ry) for px, py in ((-k, -1), (k, -1), (1, -k), (1, k), (k, 1), (-k, 1), (-1, k), (-1, -k))]


def turn(points, pivot, ang):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    px, py = pivot
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in points]


def segment(a, b, w):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return rect((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, L, w, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def ragged_hem(x0, x1, top, depth, teeth):
    """The hovering hem: a flat plane hanging straight down from the robe, its lower edge torn into teeth."""
    pts = [(x0, top), (x1, top)]
    for i in range(teeth * 2 + 1):
        x = x1 + (x0 - x1) * i / (teeth * 2)
        pts.append((x, top - depth * (1.0 if i % 2 else 0.45) - (i % 3) * 0.6))
    return pts


# ---- the body (villager 1.45x: head 12 x 14.5, robe 12 wide; the back built up into a hump) ------------------------
HEM_TOP, SHOULDER = 9, 34          # the robe runs straight from y 9 up to the shoulders at y 34
HEAD = (-10, 41)                   # an old woman's stoop: the upper body leans forward, the head comes forward
TILT = 6
STOOP = 9                          # degrees the robe leans forward above the waist


def hat(hx, top):
    """Vanilla's witch hat at the head's scale: a brim about 1.3x the head, a cone in steps, the tip bent back."""
    return [("hat", rect(hx, top + 1, 16, 2)), ("band", rect(hx, top + 2.9, 10.5, 1.8)),
            ("hat", [(hx - 5.2, top + 2), (hx + 5.2, top + 2), (hx + 4.4, top + 7), (hx + 3.4, top + 11.5), (hx + 5, top + 15),
                     (hx + 8.5, top + 17.5), (hx + 6.2, top + 18.6), (hx + 2, top + 16), (hx - 0.6, top + 11.5), (hx - 3, top + 7)])]


def side_body():
    """Side view, facing left (-z is the front)."""
    upper = turn([(-6, 20), (-6, SHOULDER - 1), (-4.5, SHOULDER + 2), (3, SHOULDER + 3), (7, SHOULDER + 1), (7, 20)],
                 (0, 18), STOOP)                            # straight sides, rounded old shoulders, leaning forward
    out = [("robe", [(-6, HEM_TOP)] + upper + [(7, HEM_TOP)])]
    out.append(("hem", ragged_hem(-6, 7, HEM_TOP, 5, 4)))
    out.append(("herb", rect(-3, 18, 3.5, 7, 6)))
    out.append(("bone", rect(0.5, 15.5, 2.2, 3.4)))
    hx, hy = HEAD
    head = [("robe_dark", [(-8, SHOULDER + 1), (hx + 1, hy - 6), (hx + 7, hy - 3), (-1, SHOULDER + 3)]),  # the collar
            ("skin", rect(hx, hy, 12, 14.5)), ("brow", rect(hx - 4.5, hy + 3.6, 4, 1.8)),
            ("eye", rect(hx - 5.4, hy + 1.6, 1.4, 2)),
            ("nose", [(hx - 6, hy + 1.5), (hx - 12, hy - 5), (hx - 11, hy - 7), (hx - 6, hy - 3.5)]),
            ("wart", rect(hx - 9.6, hy - 3, 1.8, 1.8))] + hat(hx, hy + 7.25)
    out += [(t, turn(p, (hx, hy - 4), -TILT)) for t, p in head]
    return out


def side_sleeve(shoulder, cuff, w=6.5):
    return [("sleeve", segment(shoulder, cuff, w)), ("cuff", rect(cuff[0], cuff[1], w + 0.6, w * 0.7))]


def side_sister(kind, role):
    glow, steam = ROLE[role]
    G, M = ("glow", glow), ("steam", steam)
    out = []
    if kind == "cauldron":
        # the extra-large cauldron rides the hump, roped round her middle; one sleeve raised to cast
        out += [("iron", octagon(15, 29, 12, 11)), ("iron_dark", rect(13.5, 40, 22, 3, 12)), (G, rect(13, 41.8, 17, 1.6, 12))]
        out += [(M, rect(11, 46, 1.8, 5, 8)), (M, rect(16, 47, 1.5, 4, -10))]
        out += side_body()
        out += [("rope", segment((-7.6, 24), (8, 27), 1.6)), ("rope", segment((-8.4, 29), (6, 35), 1.6)),
                ("rope", rect(-7.9, 26.5, 1.6, 6, STOOP))]
        out += side_sleeve((-3, 31), (-17, 27))
        out += [(G, octagon(-21, 27.5, 2.8))]                                  # magic gathering at her cuff
    elif kind == "bottles":
        out += side_body()
        # the shoulder belt crosses her front; large bottles stand out from it, one more held up in her sleeve
        out += [("strap", segment((-6.6, 33), (-6.6, 14), 2.2))]
        for i, y in enumerate((30, 24, 18)):
            out += [("glass", rect(-9.5, y, 4.5, 6)), (G, rect(-9.5, y - 0.8, 3.4, 3.6)), ("cork", rect(-9.5, y + 3.8, 2, 1.8))]
        out += side_sleeve((-3, 31), (-18, 34))
        out += [("glass", rect(-21.5, 38.5, 5, 7, 10)), (G, rect(-21.5, 37.5, 3.8, 4, 10)), ("cork", rect(-22.3, 42.8, 2.2, 2, 10))]
    else:
        # a pot held out in front in both sleeves
        out += side_body()
        out += [("iron", octagon(-17, 21, 8.5, 7.5)), ("iron_dark", rect(-17, 28, 18, 2.6)), (G, rect(-17, 29.6, 14, 1.4))]
        out += [(M, rect(-19, 33, 1.6, 4.5, 10)), (M, rect(-15, 34, 1.4, 3.5, -12))]
        out += side_sleeve((-3, 33), (-11, 23))
    return out


def front_body():
    out = [("robe", [(-6.5, HEM_TOP), (6.5, HEM_TOP), (7, SHOULDER), (5.5, SHOULDER + 3), (-5.5, SHOULDER + 3), (-7, SHOULDER)])]
    out.append(("hem", ragged_hem(-6.5, 6.5, HEM_TOP, 5, 4)))
    hx, hy = 0, HEAD[1] - 3
    out += [("skin", rect(hx, hy, 12, 14.5)), ("brow", rect(hx, hy + 3.6, 9, 1.8)),
            ("eye", rect(-2.6, hy + 1.4, 2, 1.4)), ("eye", rect(2.6, hy + 1.4, 2, 1.4)),
            ("nose", rect(0, hy - 3, 3, 8)), ("wart", rect(1, hy - 4.5, 1.8, 1.8))]
    out += hat(hx, hy + 7.25)
    return out


def front_sleeves(left, right, w=6):
    out = []
    for sh, cuff in (((-8, 34), left), ((8, 34), right)):
        out += [("sleeve", segment(sh, cuff, w)), ("cuff", rect(cuff[0], cuff[1], w + 0.6, w * 0.7))]
    return out


def front_sister(kind, role):
    glow, steam = ROLE[role]
    G, M = ("glow", glow), ("steam", steam)
    out = []
    if kind == "cauldron":
        out += [("iron", octagon(0, 33, 14, 11)), ("iron_dark", rect(0, 43.5, 30, 3)), (G, rect(0, 45.2, 24, 1.6))]
        out += front_body()
        out += [("rope", rect(0, 26, 14.5, 1.6)), ("rope", rect(0, 31, 15, 1.6))]
        out += front_sleeves((-14, 22), (13, 40))
        out += [(G, octagon(15, 43, 2.6))]
    elif kind == "bottles":
        out += front_body()
        out += [("strap", segment((-7.5, 34), (7, 13), 2.4))]
        for i, t in enumerate((0.2, 0.45, 0.7)):
            x, y = -7.5 + 14.5 * t, 34 - 21 * t
            out += [("glass", rect(x, y, 4.5, 6)), (G, rect(x, y - 0.8, 3.4, 3.6)), ("cork", rect(x, y + 3.8, 2, 1.8))]
        out += front_sleeves((-12, 20), (13, 40))
        out += [("glass", rect(14, 45.5, 5, 7)), (G, rect(14, 44.5, 3.8, 4)), ("cork", rect(14, 49.8, 2.2, 2))]
    else:
        out += front_body()
        out += front_sleeves((-9, 22), (9, 22))
        out += [("iron", octagon(0, 19, 10, 7.5)), ("iron_dark", rect(0, 26, 22, 2.6)), (G, rect(0, 27.6, 17, 1.4))]
        out += [(M, rect(-2, 31, 1.6, 4.5, 10)), (M, rect(2, 32, 1.4, 3.5, -12))]
    return out


SISTERS = [("cauldron", "green", "the cauldron"), ("bottles", "purple", "the bottles"), ("pot", "red", "the pot")]


def draw_row(view, mode):
    W, H = 1500, 330
    img = Image.new("RGB", (W, H), (52, 50, 60) if mode == "value" else (244, 241, 234))
    d = ImageDraw.Draw(img)
    oy = H - 26
    if mode == "value":
        d.rectangle((0, oy, W, H), fill=(44, 42, 50))
    d.line((0, oy, W, oy), fill=(120, 116, 110), width=2)
    for i, (kind, role, _) in enumerate(SISTERS):
        ox = 190 + i * 400
        parts = side_sister(kind, role) if view == "side" else front_sister(kind, role)
        for tone, p in parts:
            col = SIL if mode == "sil" else (tone[1] if isinstance(tone, tuple) else TONE[tone])
            d.polygon([(ox + x * S, oy - y * S) for x, y in p], fill=col)
    px, ph, pw = 1400, 28.8 * S, 7.2 * S
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
    dr.text((pad, 14), "Witch Coven - the three sisters (the cauldron, the bottles, the pot), side and front; a player",
            font=font, fill=INK)
    y = top
    for view, mode in rows:
        if mode == "sil":
            dr.text((pad, y + 2), "side" if view == "side" else "front", font=font, fill=INK)
            y += lab
        img = draw_row(view, mode)
        img.save(OUT / f"{view}_{mode}.png")
        sheet.paste(img, (pad, y))
        y += rh + pad
    sheet.save(OUT / "lineup.png")
    print("wrote", OUT / "lineup.png")


if __name__ == "__main__":
    main()
