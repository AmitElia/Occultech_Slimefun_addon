"""The Elder of Ash (was the Mire Monarch), session 1 step 1: how big the volcano is against the toad.

The brief (user, 2026-10-14; plan: docs/art/bosses/elder_of_ash/overhaul/plan.md): a giant elder toad sage, crouched
low, a volcano growing out of its back (skin -> ash-grey crust -> basalt cone), brown/green/ash-grey toad, clear lava
streams down its sides, a pipe in its mouth with smoke, smoke from the crater. No crown, no rope.

Three proportions of one toad:
  A  the toad dominates: the cone is a hump on its back
  B  balanced: the cone rises about as high again as the toad
  C  the mountain dominates: its slopes run down the flanks, the toad carries it

Shapes are angular polygons, so whatever is picked can be built from cuboids. Units are model pixels (16 = one block),
y up, the ground at 0. Side views face left. The blue figure is a player (1.8 blocks).

Run from the repository root: python tools/art/bosses/ash_silhouettes.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s1_silhouettes"
S = 2.5                     # screen pixels per model pixel
SS = 2                      # supersampling
BG, INK, DIM = (24, 22, 28), (236, 228, 214), (150, 142, 132)
PAPER = (244, 241, 234)
SIL = (34, 33, 40)
PLAYER = (150, 178, 222)
TONE = {"far": (58, 52, 38), "skin": (96, 88, 56), "flank": (112, 90, 60), "belly": (170, 146, 102),
        "wart": (80, 74, 46), "gland": (86, 80, 50), "lip": (62, 50, 36), "brow": (74, 68, 44), "lid": (82, 76, 50),
        "eye": (255, 186, 60), "pupil": (40, 22, 14),
        "ash": (128, 124, 118), "ash_dark": (100, 96, 92), "basalt": (60, 56, 60), "basalt_lit": (82, 78, 82),
        "lava": (255, 120, 30), "lava_hot": (255, 214, 110), "crust": (70, 40, 30),
        "pipe": (92, 60, 36), "pipe_metal": (150, 140, 120), "toe": (130, 104, 70)}
SMOKE = (196, 192, 188)

# ---- shape helpers (model units, y up) ---------------------------------------------------------------------------


def rect(cx, cy, w, h, ang=0.0):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return [(cx + dx * c - dy * s, cy + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2),
                                                                         (w / 2, h / 2), (-w / 2, h / 2))]


def octo(cx, cy, w, h, cut=0.3, ang=0.0):
    """A chamfered box: the cuboid-buildable rounded mass."""
    a, b = w / 2, h / 2
    k = min(a, b) * cut * 2
    pts = [(-a + k, -b), (a - k, -b), (a, -b + k), (a, b - k), (a - k, b), (-a + k, b), (-a, b - k), (-a, -b + k)]
    r = math.radians(ang)
    c, s = math.cos(r), math.sin(r)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def limb(a, b, w0, w1=None):
    w1 = w0 if w1 is None else w1
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    return [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
            (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]


def mirror(parts):
    return [(t, [(-x, y) for x, y in p]) for t, p in parts]


def stream(points, w0, w1, tone="lava"):
    """A lava stream along a polyline, tapering; a hot core along its upper half."""
    out = []
    n = len(points) - 1
    for i in range(n):
        a, b = points[i], points[i + 1]
        wa, wb = w0 + (w1 - w0) * i / n, w0 + (w1 - w0) * (i + 1) / n
        out.append((tone, limb(a, b, wa, wb)))
    for i in range(max(1, n // 2)):
        a, b = points[i], points[i + 1]
        out.append(("lava_hot", limb(a, b, w0 * 0.35, w0 * 0.3)))
    end = points[-1]
    out.append((tone, octo(end[0], end[1] - w1 * 0.4, w1 * 1.5, w1 * 1.8, 0.35)))      # the drip at its end
    return out


# ---- the volcano -------------------------------------------------------------------------------------------------

def cone(cx, base_y, top_y, base_w, crater_w, lean=0.0):
    """The cone's outline: concave slopes (steep near the top, spreading at the base), a jagged rim with the crater's
    notch. Returns (outline, rim points left->right, the crater's centre)."""
    h = top_y - base_y
    left, right = [], []
    for i in range(9):
        t = i / 8                                            # 0 at the base, 1 at the rim
        spread = (1 - t) ** 1.7
        y = base_y + h * t
        half = crater_w / 2 + (base_w / 2 - crater_w / 2) * spread
        x = cx + lean * t * h
        left.append((x - half, y))
        right.append((x + half, y))
    tx = cx + lean * h
    # the rim: two broken teeth either side of the crater's notch
    rim = [(tx - crater_w / 2, top_y), (tx - crater_w * 0.36, top_y + 3.2), (tx - crater_w * 0.2, top_y + 1.0),
           (tx - crater_w * 0.1, top_y - 2.4), (tx + crater_w * 0.12, top_y - 2.0), (tx + crater_w * 0.26, top_y + 1.6),
           (tx + crater_w * 0.4, top_y + 2.4), (tx + crater_w / 2, top_y)]
    outline = left + rim + right[::-1]
    return outline, rim, (tx, top_y - 1.0)


VARIANTS = {
    #       cone base centre x, base width, top y, crater width, lean (x per y), ash band extent
    "A": dict(cx=10, base_w=40, top=62, crater=12, lean=0.03, name="A  the toad dominates (a hump)"),
    "B": dict(cx=8, base_w=62, top=82, crater=16, lean=0.03, name="B  balanced"),
    "C": dict(cx=6, base_w=96, top=108, crater=22, lean=0.02, name="C  the mountain dominates"),
}


# ---- the toad, side view (facing left) -------------------------------------------------------------------------

def back_y(x):
    """The toad's back line (side view): the snout, the eye's bulge, over the hump behind the shoulders, to the rump."""
    pts = [(-54, 22), (-48, 30), (-42, 36), (-36, 40), (-29, 39), (-24, 37), (-14, 40), (-4, 44), (8, 46), (20, 43),
           (30, 36), (38, 26), (41, 18)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return 20


def toad_side():
    far = [("far", limb((-20, 24), (-17, 11), 10, 9)), ("far", limb((-17, 11), (-26, 3), 9, 7)),
           ("far", [(-40, 0), (-22, 0), (-22, 3), (-30, 5), (-40, 2.6)]),
           ("far", octo(20, 16, 26, 22, 0.3, -12)), ("far", [(-4, 0), (24, 0), (24, 3.5), (2, 4), (-4, 2.2)])]
    outline = [(-54, 17), (-54, 22), (-48, 30), (-42, 33), (-36, 34), (-29, 35), (-24, 37), (-14, 40), (-4, 44),
               (8, 46), (20, 43), (30, 36), (38, 26), (41, 18), (40, 10), (32, 5), (8, 4), (-16, 5), (-30, 6),
               (-40, 7), (-48, 10), (-53, 14)]
    body = [("flank", outline)]
    body += [("belly", [(-54, 17), (-53, 14), (-48, 10), (-40, 7), (-30, 6), (-16, 5), (8, 4), (16, 4.6), (2, 9),
                        (-16, 11), (-30, 12.4), (-42, 14.4), (-50, 16.4)])]                 # the pale throat and belly
    body += [("skin", [(-48, 30), (-42, 33), (-36, 34), (-29, 35), (-24, 37), (-14, 40), (-4, 44), (8, 46), (20, 43),
                       (30, 36), (35, 30), (22, 36), (6, 39), (-8, 36), (-20, 31), (-34, 28), (-46, 26)])]
    body += [("wart", octo(x, y, 3.8, 3.0, 0.35)) for x, y in ((-10, 24), (6, 22), (22, 24), (-26, 22), (30, 26))]
    # the head: a mouth as wide as the head is long, its corner turned down; the gland behind the eye;
    # the eye's bulge standing up off the skull; the heavy brow over a half-shut lid
    head = [("lip", [(-54, 19.6), (-44, 19.4), (-32, 18.6), (-24.5, 15.6), (-23, 12.2), (-24.6, 12.0), (-27, 15.4),
                     (-34, 17.0), (-44, 17.6), (-54, 18.0)]),
            ("gland", octo(-17, 36.5, 12, 7, 0.35, -10)),
            ("lid", octo(-35, 37.0, 14, 10, 0.4, -4)),                                 # the eye's bulge
            ("eye", rect(-38.6, 36.6, 5.6, 2.4)), ("pupil", rect(-38.6, 36.6, 3.8, 0.9)),
            ("lid", [(-42, 38.0), (-35.6, 39.0), (-34.4, 37.6), (-35.8, 37.9), (-42, 37.2)]),   # the heavy upper lid
            ("brow", [(-43.6, 37.6), (-40, 40.8), (-34, 42.2), (-28.4, 41.4), (-28.6, 39.6), (-34, 40.0), (-41, 38.2)])]
    near = [("flank", limb((-22, 24), (-19, 11), 11, 9.5)), ("flank", limb((-19, 11), (-30, 3), 9.5, 7.5)),
            ("toe", [(-50, 0), (-26, 0), (-25, 3.2), (-32, 5.4), (-44, 4.0), (-50, 1.8)])]
    near += [("toe", rect(-49, 1.0, 2.6, 2.0)), ("toe", rect(-44.5, 1.0, 2.6, 2.4)), ("toe", rect(-40, 1.0, 2.6, 2.2))]
    near += [("flank", octo(25, 17, 28, 24, 0.32, -14)), ("skin", octo(27, 23, 19, 10, 0.35, -14)),
             ("toe", [(-2, 0), (30, 0), (32, 4), (10, 4.8), (0, 3.6), (-3, 1.8)])]
    near += [("toe", rect(-1.5, 1.0, 2.6, 2.2)), ("toe", rect(3, 1.0, 2.6, 2.4))]
    return far + body + near + head


def pipe_side():
    """A long sage's pipe from the mouth's corner, forward and a little down, its metal bowl turned up."""
    return [("pipe", limb((-26, 15.0), (-72, 10), 2.2, 2.0)), ("pipe_metal", rect(-27.5, 14.8, 2.2, 3.0, -6)),
            ("pipe_metal", [(-75, 8.6), (-68, 8.6), (-67.5, 16), (-75.5, 16)]),
            ("pipe", rect(-71.5, 16.2, 7.2, 1.0)), ("lava_hot", rect(-71.5, 16.2, 4.4, 0.8))]


def face_path(v, base_y, u, wiggle, phase, steps=7):
    """Points down the cone's face at u (-1..1 of its half width), meandering."""
    top = v["top"]
    tx = v.get("_tx", v["cx"])
    pts = []
    for i in range(steps + 1):
        t = i / steps
        y = top - 1 - (top - 1 - base_y) * t
        half = v["crater"] / 2 + (v["base_w"] / 2 - v["crater"] / 2) * (1 - (1 - t) ** 1.7)
        x = tx + (u + wiggle * math.sin(phase + t * 5.0)) * half * 0.8
        pts.append((x, y))
    return pts


def volcano_side(v):
    base = 32
    outline, rim, crater = cone(v["cx"], base, v["top"], v["base_w"], v["crater"], v["lean"])
    out = []
    out.append(("basalt", outline))
    out.append(("basalt_lit", [outline[2], outline[7], (outline[7][0] + 4, outline[7][1]), (outline[2][0] + 8, outline[2][1])]))
    # the ash skirt: the warts hardening into crust where the cone grows out of the back (only over the toad's back),
    # its top edge climbing jaggedly into the basalt, its lower edge breaking up into the skin
    x0 = max(-24, v["cx"] - v["base_w"] / 2 - 8)
    x1 = min(38, v["cx"] + v["base_w"] / 2 + 8)
    xs = [x0 + (x1 - x0) * i / 12 for i in range(13)]
    up = [(x, back_y(x) + (2 + 5 * ((i * 5) % 3) / 2) * math.sin(math.pi * i / 12)) for i, x in enumerate(xs)]
    low = [(x, back_y(x) - (3 + 5 * ((i * 7) % 3) / 2)) for i, x in enumerate(xs)][::-1]
    out.append(("ash", up + low))
    for i, x in enumerate(xs[1:-1:2]):
        out.append(("ash_dark", octo(x, back_y(x) - 1.5 - (i % 2) * 1.5, 5.0, 4.0, 0.35, 10 * (i % 3 - 1))))
    out.append(("lava", rect(crater[0], crater[1] + 0.4, v["crater"] * 0.5, 2.4)))
    out.append(("lava_hot", rect(crater[0], crater[1] + 0.6, v["crater"] * 0.3, 1.2)))
    v = dict(v, _tx=crater[0])
    # two streams on the near face: one runs forward over the shoulder and down behind the front leg, one back
    # over the thigh; a short third forks off the first
    a = face_path(v, base, -0.45, 0.18, 0.0)
    a += [(-16, back_y(-16) - 4), (-14, 26), (-12, 16)]
    b = face_path(v, base, 0.3, 0.15, 1.8)
    b += [(26, back_y(26) - 4), (30, 28)]
    c = face_path(v, base, -0.05, 0.2, 3.1, steps=4)[2:]
    out += stream(a, 3.4, 2.0) + stream(b, 3.0, 1.8) + stream(c, 2.2, 1.6)
    return out


# ---- the toad, front view --------------------------------------------------------------------------------------

def toad_front():
    half = []
    half += [("far", octo(46, 15, 15, 22, 0.32)), ("far", [(40, 0), (62, 0), (62, 3), (52, 4.4), (40, 3.4)])]
    half += [("flank", [(0, 5), (34, 6), (43, 14), (45, 28), (41, 36), (30, 39), (0, 40)])]
    # the front leg: elbow out, a broad webbed hand
    half += [("flank", limb((32, 24), (45, 14), 11, 9.5)), ("flank", limb((45, 14), (42, 3), 9.5, 7.5)),
             ("toe", [(30, 0), (54, 0), (54, 2.4), (48, 4.6), (34, 4.6), (30, 2.2)])]
    half += [("toe", rect(x, 1.0, 2.6, 2.4)) for x in (32, 38, 44, 50)]
    # the head: wide and flat, the throat below the mouth
    half += [("skin", [(0, 9), (28, 10), (35, 15), (36, 26), (32, 33), (20, 35), (0, 35.5)]),
             ("belly", [(0, 6), (24, 7), (31, 11), (32, 15), (0, 15)]),
             ("lip", [(0, 16.4), (26, 16.2), (33, 13), (34, 14.2), (27, 17.8), (0, 18)])]
    # the eye stands up off the head's corner, the gland behind it, the heavy brow over it (inner end low: a scowl)
    half += [("gland", octo(33, 34, 10, 8, 0.35)),
             ("lid", octo(22, 40, 15, 13, 0.4)),
             ("eye", rect(22, 39.0, 7.6, 2.8)), ("pupil", rect(22, 39.0, 5.2, 1.0)),
             ("lid", [(16, 40.8), (28.6, 41.8), (28.6, 40.4), (16, 39.8)]),
             ("brow", [(12.4, 40.6), (18, 45.0), (27, 47.0), (30.4, 44.6), (22, 42.8), (14.4, 39.6)])]
    half += [("wart", octo(x, y, 3.6, 3.0, 0.35)) for x, y in ((39, 22), (40, 32), (8, 30), (12, 24))]
    return half + mirror(half)


def volcano_front(v):
    base = 38
    outline, rim, crater = cone(0, base, v["top"], v["base_w"], v["crater"], 0)
    out = []
    w = min(44, v["base_w"] / 2 + 6)
    out.append(("ash", [(-w, 34), (-w + 5, 43), (0, 47), (w - 5, 43), (w, 34), (0, 38)]))
    out.append(("basalt", outline))
    out.append(("basalt_lit", [outline[2], outline[7], (outline[7][0] + 3, outline[7][1]), (outline[2][0] + 7, outline[2][1])]))
    out.append(("lava", rect(crater[0], crater[1] + 0.4, v["crater"] * 0.5, 2.4)))
    out.append(("lava_hot", rect(crater[0], crater[1] + 0.6, v["crater"] * 0.3, 1.2)))
    v = dict(v, cx=0, _tx=0)
    # streams down the cone's face, over the shoulders beside the head and down the flanks
    a = face_path(v, base, -0.5, 0.15, 0.4)
    b = face_path(v, base, 0.42, 0.18, 2.2)
    c = face_path(v, base, 0.05, 0.22, 4.0, steps=5)
    out += stream(a, 3.4, 2.0) + stream(b, 3.2, 1.8) + stream(c, 2.4, 1.6)
    return out


def flank_lava_front():
    """The streams that come round behind the head and run down the flanks, over the toad."""
    return (stream([(-36, 39), (-40, 33), (-43, 25), (-43.5, 17)], 3.2, 1.9)
            + stream([(36, 39), (40.5, 32), (42, 26), (43, 20)], 3.0, 1.8))


def pipe_front():
    """The pipe from the boss's right mouth corner (the viewer's left), angled out and down, the bowl up."""
    return [("pipe", limb((-28, 16.4), (-52, 9), 2.4, 2.0)), ("pipe_metal", rect(-29, 16.2, 2.4, 3.0, 15)),
            ("pipe_metal", [(-56, 7.6), (-49, 7.6), (-48.5, 15), (-56.5, 15)]),
            ("pipe", rect(-52.5, 15.2, 7.2, 1.0)), ("lava_hot", rect(-52.5, 15.2, 4.4, 0.8))]


# ---- smoke -----------------------------------------------------------------------------------------------------

def plume(base, n, size, drift, rise, seed):
    """Puffs rising from base, growing, drifting back, getting lighter (x, y, radius, alpha)."""
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        wob = math.sin(seed + i * 1.7) * size * 0.5
        out.append((base[0] + drift * t + wob, base[1] + rise * t + size * 0.5, size * (0.5 + 1.1 * t), int(170 - 110 * t)))
    return out


# ---- drawing ---------------------------------------------------------------------------------------------------

def draw_view(v, view, mode, w=430, h=380):
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (104, 110, 124, 255) if mode == "value" else PAPER + (255,))
    d = ImageDraw.Draw(img)
    oy = H - 22 * SS
    ox = (245 if view == "side" else 215) * SS
    if mode == "value":
        d.rectangle((0, oy, W, H), fill=(78, 80, 88))
    d.line((0, oy, W, oy), fill=(120, 116, 110), width=2 * SS)
    k = S * SS

    def P(p):
        return [(ox + x * k, oy - y * k) for x, y in p]

    if view == "side":
        parts = toad_side() + volcano_side(v) + pipe_side()
        crater = cone(v["cx"], 32, v["top"], v["base_w"], v["crater"], v["lean"])[2]
        bowl = (-71.5, 17)
    else:
        parts = volcano_front(v) + toad_front() + flank_lava_front() + pipe_front()
        crater = (0, v["top"] - 1)
        bowl = (-52.5, 16)
    for tone, p in parts:
        d.polygon(P(p), fill=SIL if mode == "sil" else TONE[tone])
    if mode == "value":
        smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(smoke)
        puffs = plume(crater, 9, v["crater"] * 0.55, 26 if view == "side" else 10, 46, 0.5)
        puffs += plume(bowl, 5, 3.0, 8, 16, 2.0)
        for x, y, r, a in puffs:
            cx, cy = ox + x * k, oy - y * k
            sd.ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), fill=SMOKE + (a,))
        img = Image.alpha_composite(img, smoke)
        d = ImageDraw.Draw(img)
    # the player for scale
    px = W - 34 * SS
    ph, pw = 28.8 * k, 7.2 * k
    d.rectangle((px - pw / 2, oy - ph * 0.75, px + pw / 2, oy), fill=PLAYER)
    d.rectangle((px - pw * 0.55, oy - ph, px + pw * 0.55, oy - ph * 0.75), fill=PLAYER)
    return img.convert("RGB").resize((w, h), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 22)
        small = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 17)
    except OSError:
        font = small = ImageFont.load_default()
    rows = [("side", "sil"), ("side", "value"), ("front", "sil"), ("front", "value")]
    cw, ch, pad, top, lab = 430, 380, 10, 50, 30
    sheet = Image.new("RGB", (3 * cw + 4 * pad, top + lab + len(rows) * (ch + pad)), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 12), "The Elder of Ash - session 1 step 1: how big the volcano is against the toad", font=font, fill=INK)
    for i, key in enumerate("ABC"):
        dr.text((pad + i * (cw + pad), top), VARIANTS[key]["name"], font=small, fill=DIM)
    for r, (view, mode) in enumerate(rows):
        for i, key in enumerate("ABC"):
            img = draw_view(VARIANTS[key], view, mode, cw, ch)
            img.save(OUT / f"{key}_{view}_{mode}.png")
            sheet.paste(img, (pad + i * (cw + pad), top + lab + r * (ch + pad)))
    sheet.save(OUT / "silhouettes.png")
    for key, v in VARIANTS.items():
        print(key, "crater at", round(v["top"] / 16, 2), "blocks; cone base", round(v["base_w"] / 16, 2), "blocks wide")
    print("wrote", OUT / "silhouettes.png")


if __name__ == "__main__":
    main()
