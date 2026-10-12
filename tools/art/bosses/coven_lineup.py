"""Witch Coven redesign, step 1: silhouette line-ups of the three sisters (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

The sisters share one body: built like a vanilla witch or villager (long robe, big head, big nose, sleeves folded
across the chest, no hands showing), hunched, larger than a player, hovering low, under a real witch's hat. Only their
vessels differ: the Root-Mother's cauldron hanging in front, the Briar's censer on a chain, the Crook's pot on her back
with a ladle over her shoulder. The brew's colour is the role (green healer, purple curser, red bomber).

Three takes on the shared body, one per row:
  A  Villager hunch   vanilla's proportions grown 1.45x, the back rounded into a hump, the head pushed forward.
  B  Deep crone       bent much further: the hump is the highest point under the hat, the head hangs low in front.
  C  Root bell        A's hunch over a robe that flares into a ragged bell of roots trailing behind as it hovers.

Shapes are angular polygons and turned rectangles, buildable from cuboids. Units are model pixels (16 = one block).
Run from the repository root: python tools/art/bosses/coven_lineup.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s1_lineup"
S = 3.6
BG, INK, DIM = (24, 22, 28), (236, 228, 214), (150, 142, 132)
PLAYER = (150, 178, 222)
TONE = {"robe": (64, 54, 44), "root": (40, 33, 27), "sleeve": (54, 46, 38), "skin": (150, 128, 98),
        "nose": (138, 116, 88), "wart": (96, 120, 60), "hat": (42, 34, 50), "band": (84, 98, 54),
        "iron": (56, 54, 60), "iron_dark": (34, 33, 38), "herb": (86, 96, 58), "bone": (196, 186, 160),
        "eye": (30, 24, 20), "chain": (70, 68, 74)}
ROLE = {"green": ((110, 230, 90), (170, 240, 150)), "purple": ((170, 70, 220), (200, 150, 235)),
        "red": ((230, 70, 60), (240, 150, 130))}
SIL = (34, 33, 40)


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


def ragged(z0, z1, y, depth, n):
    """A ragged hem from z1 back to z0: teeth hanging down."""
    pts = []
    for i in range(n + 1):
        z = z1 + (z0 - z1) * i / n
        pts.append((z, y - (depth if i % 2 else 0)))
    return pts


# ---- the shared body ---------------------------------------------------------------------------------------------
# Side views face left: -z is the front. y is up; the ground is y = 0.

VARIANTS = {
    "A": {"title": "Villager hunch", "hem": 5, "hem_front": -9, "hem_back": 10, "chest": (-9, 28), "shoulder": (-6, 38),
          "neck": (2, 44), "hump": (13, 36), "head": (-9, 47), "tilt": 14, "flare": 0},
    "B": {"title": "Deep crone", "hem": 5, "hem_front": -12, "hem_back": 10, "chest": (-13, 24), "shoulder": (-11, 34),
          "neck": (0, 47), "hump": (13, 40), "head": (-16, 40), "tilt": 26, "flare": 0},
    "C": {"title": "Root bell", "hem": 4, "hem_front": -14, "hem_back": 16, "chest": (-9, 28), "shoulder": (-6, 38),
          "neck": (2, 44), "hump": (13, 36), "head": (-9, 47), "tilt": 14, "flare": 1},
}


def head_and_hat(v):
    """The head (a tall vanilla villager head, 1.45x), the long crooked nose with its wart, the deep brow, and a real
    witch's hat: a wide brim and a tall cone in steps, its tip bent back. All tilted forward with the head."""
    hx, hy = v["head"]
    t = -v["tilt"]          # negative: the face (at -z) tips down
    out = []
    head = rect(hx, hy, 13, 15)
    out.append(("skin", head))
    out.append(("eye", rect(hx - 6, hy + 2.5, 1.6, 2.2)))                       # the eye under the brow
    out.append(("skin", rect(hx - 5.5, hy + 4.4, 3, 1.6)))                       # the brow ridge
    out.append(("nose", [(hx - 6.5, hy + 2), (hx - 13, hy - 4.5), (hx - 12, hy - 6.5), (hx - 6.5, hy - 3)]))
    out.append(("wart", rect(hx - 10.5, hy - 2.6, 1.8, 1.8)))
    top = hy + 7.5
    out.append(("hat", rect(hx, top + 1.2, 25, 2.4)))                           # the brim
    out.append(("band", rect(hx, top + 3.4, 14, 2.2)))
    cone = [(hx - 7, top + 2.4), (hx + 7, top + 2.4), (hx + 6, top + 9), (hx + 4.5, top + 15), (hx + 6.5, top + 20),
            (hx + 11, top + 23), (hx + 8, top + 24.5), (hx + 2.5, top + 21), (hx - 1, top + 15), (hx - 4, top + 9)]
    out.append(("hat", cone))
    return [(tone, turn(p, (hx, hy - 4), t)) for tone, p in out]


def body(v, side=True):
    """The robe from the hovering hem up over the hump, the folded sleeves on the chest, a herb bundle and a bone charm
    hanging at the waist on twine."""
    hem, zf, zb = v["hem"], v["hem_front"], v["hem_back"]
    cz, cy = v["chest"]
    sz, sy = v["shoulder"]
    nz, ny = v["neck"]
    hz, hy = v["hump"]
    out = []
    if v["flare"]:
        # roots trailing out behind the bell as it hovers
        for i, (dz, dy, ln, ang) in enumerate(((4, 2, 16, -8), (-2, 1, 12, -14), (8, 3, 10, -4))):
            out.append(("root", rect(zb + dz, hem + dy - 1, ln, 2.2, ang)))
    robe = [(zf, hem), (cz, cy), (sz, sy), (nz, ny), (hz, hy), (zb, hem + 10)] + ragged(zf, zb, hem, 3, 7)
    out.append(("robe", robe))
    out.append(("root", [(zf, hem), (zb, hem + 4), (zb, hem + 9), (zf + 2, hem + 4)]))      # the root-woven hem band
    hx, hyy = v["head"]
    out.append(("robe", [(sz - 1, sy - 3), (hx - 1, hyy - 8), (hx + 7, hyy - 3), (nz + 1, ny - 1), (hz, hy - 4)]))  # the hood/collar
    out.append(("sleeve", rect(cz - 1.5, cy - 2, 10, 7, -10)))                              # the folded sleeves
    out.append(("herb", rect(cz + 5, cy - 9, 3.5, 7, 8)))
    out.append(("bone", rect(cz + 8.5, cy - 11, 2.2, 3.4)))
    return out


def vessel(kind, v, role):
    glow, steam = ROLE[role]
    cz, cy = v["chest"]
    hz, hy = v["hump"]
    out = []
    if kind == "cauldron":
        # a big iron cauldron hanging from the folded sleeves on two chains, in front of the robe
        x, y = cz - 8, cy - 13
        out += [("chain", rect(x + 4, y + 9, 1.2, 8, -14)), ("chain", rect(x - 3, y + 9, 1.2, 8, 14))]
        out += [("iron", octagon(x, y, 9.5, 6.5)), ("iron_dark", rect(x, y + 6, 21, 2.6))]
        out += [("glow", rect(x, y + 7.7, 16, 1.4))]
        out += [("steam", rect(x - 3, y + 11, 1.6, 4, 12)), ("steam", rect(x + 2, y + 12.5, 1.4, 5, -10))]
    elif kind == "censer":
        # a censer swung out on a long chain from the sleeves, trailing smoke
        sx, sy = cz - 5, cy - 3
        ex, ey = cz - 19, cy - 10
        L = math.hypot(ex - sx, ey - sy)
        out += [("chain", rect((sx + ex) / 2, (sy + ey) / 2, L, 1.2, math.degrees(math.atan2(ey - sy, ex - sx))))]
        out += [("iron", octagon(ex, ey - 3, 7.5, 8.5)), ("iron_dark", rect(ex, ey + 5.5, 9, 3)), ("iron_dark", rect(ex, ey + 8.5, 3, 3))]
        out += [("glow", rect(ex, ey - 1.5, 11, 2)), ("glow", rect(ex, ey - 5.5, 8, 1.6))]          # the lit vents
        out += [("steam", rect(ex + 1, ey + 11, 1.8, 5, 10)), ("steam", rect(ex - 3, ey + 12, 1.5, 4, -14))]
    else:
        # a pot riding the hump, a long ladle from the sleeves over the shoulder into it
        px, py = hz + 2, hy + 4
        out += [("iron", octagon(px, py, 7.5, 6.5)), ("iron_dark", rect(px, py + 6, 16, 2.4)), ("glow", rect(px, py + 7.6, 12, 1.3))]
        out += [("steam", rect(px + 2, py + 11, 1.6, 4.5, 10)), ("steam", rect(px - 2, py + 12, 1.4, 3.5, -12))]
        sx, sy = cz - 4, cy - 1
        ex, ey = px - 2, py + 9
        L = math.hypot(ex - sx, ey - sy)
        out += [("chain", rect((sx + ex) / 2, (sy + ey) / 2, L, 1.8, math.degrees(math.atan2(ey - sy, ex - sx))))]
        out += [("iron", octagon(sx - 2, sy - 2, 2.6))]                               # the ladle's bowl end, held low
    return [(tone if tone not in ("glow", "steam") else (tone, glow if tone == "glow" else steam), p) for tone, p in out]


def front(v):
    """The front view, the Root-Mother: the robe, the hump showing at the shoulders, folded sleeves, the head and nose,
    the hat, the cauldron below."""
    hem = v["hem"]
    flare = 22 if v["flare"] else 15
    cy = v["chest"][1]
    sy = v["shoulder"][1]
    hy = v["head"][1] - (4 if v["tilt"] > 20 else 2)
    out = []
    out.append(("robe", [(-flare, hem), (flare, hem), (11, sy - 4), (9, sy + 3), (-9, sy + 3), (-11, sy - 4)] ))
    out.append(("robe", octagon(0, v["neck"][1] - 2, 15, 9)))                     # the hump rising round the head
    out.append(("root", [(-flare, hem), (flare, hem), (flare - 1, hem + 4), (-flare + 1, hem + 4)]))
    out.append(("sleeve", rect(0, cy - 2, 22, 7)))
    out.append(("skin", rect(0, hy, 13, 15)))
    out.append(("eye", rect(-3, hy + 2.5, 2, 1.6)))
    out.append(("eye", rect(3, hy + 2.5, 2, 1.6)))
    out.append(("skin", rect(0, hy + 4.4, 11, 1.6)))
    out.append(("nose", rect(0.6, hy - 2.5, 3, 8, -6)))
    out.append(("wart", rect(1.6, hy - 3.5, 1.8, 1.8)))
    top = hy + 7.5
    out.append(("hat", rect(0, top + 1.2, 25, 2.4)))
    out.append(("band", rect(0, top + 3.4, 14, 2.2)))
    out.append(("hat", [(-7, top + 2.4), (7, top + 2.4), (5, top + 12), (4.5, top + 18), (9, top + 23), (6, top + 24),
                        (0.5, top + 19), (-2, top + 12)]))
    glow, steam = ROLE["green"]
    x, y = 0, cy - 13
    out += [("chain", rect(-6, y + 9, 1.2, 8)), ("chain", rect(6, y + 9, 1.2, 8))]
    out += [("iron", octagon(x, y, 11, 7)), ("iron_dark", rect(x, y + 6.5, 24, 2.6)), (("glow", glow), rect(x, y + 8.2, 18, 1.4))]
    return out


SISTERS = [("The Root-Mother", "cauldron", "green"), ("The Briar", "censer", "purple"), ("The Crook", "pot", "red")]


def draw_row(v, mode):
    W, H = 1520, 330
    img = Image.new("RGB", (W, H), (52, 50, 60) if mode == "value" else (244, 241, 234))
    d = ImageDraw.Draw(img)
    oy = H - 30
    if mode == "value":
        d.rectangle((0, oy, W, H), fill=(44, 42, 50))
    d.line((0, oy, W, oy), fill=(120, 116, 110), width=2)

    def poly(points, ox, tone):
        if mode == "sil":
            col = SIL
        elif isinstance(tone, tuple) and isinstance(tone[1], tuple):
            col = tone[1]
        else:
            col = TONE[tone]
        d.polygon([(ox + p[0] * S, oy - p[1] * S) for p in points], fill=col)

    for i, (name, kind, role) in enumerate(SISTERS):
        ox = 150 + i * 320
        parts = []
        if kind == "pot":
            parts += body(v) + head_and_hat(v)
            parts = vessel(kind, v, role)[:5] + parts + vessel(kind, v, role)[5:]   # the pot sits behind, the ladle in front
        else:
            parts += body(v) + head_and_hat(v) + vessel(kind, v, role)
        for tone, p in parts:
            poly(p, ox, tone)
    ox = 1150
    for tone, p in front(v):
        poly(p, ox, tone)
    # the player: 1.8 blocks
    px, ph, pw = 1420, 28.8 * S, 7.2 * S
    d.rectangle((px - pw / 2, oy - ph * 0.75, px + pw / 2, oy), fill=PLAYER)
    d.rectangle((px - pw * 0.55, oy - ph, px + pw * 0.55, oy - ph * 0.75), fill=PLAYER)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        font, small = (ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 28),
                       ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 18))
    except OSError:
        font = small = ImageFont.load_default()
    pad, top, lab, rh = 12, 60, 36, 330
    rows = [(k, m) for k in VARIANTS for m in ("sil", "value")]
    sheet = Image.new("RGB", (1520 + 2 * pad, top + len(VARIANTS) * (lab + 2 * (rh + pad))), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 14), "Witch Coven - the shared body, three takes (Root-Mother, Briar, Crook from the side; the front; a player)",
            font=small, fill=INK)
    y = top
    for key, v in VARIANTS.items():
        dr.text((pad, y + 4), f"{key}  {v['title']}", font=font, fill=INK)
        y += lab
        for mode in ("sil", "value"):
            img = draw_row(v, mode)
            img.save(OUT / f"{key}_{mode}.png")
            sheet.paste(img, (pad, y))
            y += rh + pad
    sheet.save(OUT / "lineup.png")
    print("wrote", OUT / "lineup.png")


if __name__ == "__main__":
    main()
