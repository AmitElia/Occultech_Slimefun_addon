"""The Elder of Ash, session 1 step 1, take 2: B with a bigger, taller toad and beefier limbs.

The user picked B (balanced) and asked for the toad's body to be bigger (taller), not as flat, with beefier limbs and
large fingers. Two body heights are shown next to step 1's B:
  B   step 1 as shown
  B2  the body a quarter taller, a rounder back and belly, thick limbs, big fingers and toes
  B3  the body nearly half again as tall: a barrel of a toad

The shape helpers, tones and the cone come from ash_silhouettes.py. Units are model pixels (16 = one block), y up.

Run from the repository root: python tools/art/bosses/ash_s1_take2.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import ash_silhouettes as s1
from ash_silhouettes import rect, octo, limb, mirror, stream, cone, plume, TONE, SIL, PAPER, PLAYER, SMOKE, BG, INK, DIM

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s1_take2"
S = 2.1
SS = 2

VARIANTS = {
    "B2": dict(T=1.25, cx=8, base_w=64, top=98, crater=16, lean=0.03, name="B2  a quarter taller"),
    "B3": dict(T=1.45, cx=8, base_w=66, top=110, crater=17, lean=0.03, name="B3  half again as tall"),
}


def scaled(parts, T):
    return [(t, [(x, y * T) for x, y in p]) for t, p in parts]


# ---- side view (facing left) -----------------------------------------------------------------------------------

BACK = [(-54, 22), (-50, 29), (-44, 34), (-38, 38), (-30, 38), (-22, 39), (-12, 43), (0, 46.5), (12, 47), (24, 44),
        (33, 38), (40, 29), (43, 19)]


def back_y(x, T):
    for (x0, y0), (x1, y1) in zip(BACK, BACK[1:]):
        if x0 <= x <= x1:
            return (y0 + (y1 - y0) * (x - x0) / (x1 - x0)) * T
    return 20 * T


def finger(base, tip, w, pad):
    """A thick toad finger ending in a round pad."""
    w, pad = w * 1.3, pad * 1.3
    return [("toe", limb(base, tip, w, w * 0.9)), ("toe_pad", octo(tip[0], tip[1] + pad * 0.3, pad * 1.15, pad, 0.4))]


def toad_side(T):
    # the far legs (darker), just showing past the near ones
    far = [("far", limb((-18, 26 * T), (-14, 12), 13, 12)), ("far", limb((-14, 12), (-26, 4), 12, 10)),
           ("far", octo(-30, 3.2, 14, 6.4, 0.35))]
    far += [("far", limb((-32, 2.5), (-44, 1.6), 4.6, 4.2)), ("far", octo(-45, 2.2, 5.4, 4.4, 0.4))]
    far += [("far", octo(20, 19 * T, 30, 26 * T, 0.3, -12)), ("far", octo(10, 3, 30, 6, 0.3))]
    # the body: the back domed over the shoulders, the rump round, the belly deep
    outline = [(-54, 16), (-54, 22), (-50, 29), (-44, 32), (-38, 33), (-30, 34), (-22, 39), (-12, 43), (0, 46.5),
               (12, 47), (24, 44), (33, 38), (40, 29), (43, 19), (42, 10), (34, 4.5), (10, 3.5), (-16, 4.5),
               (-30, 5.5), (-40, 6.5), (-48, 9.5), (-53, 13)]
    body = scaled([("flank", outline)], T)
    body += scaled([("belly", [(-54, 16), (-53, 13), (-48, 9.5), (-40, 6.5), (-30, 5.5), (-16, 4.5), (10, 3.5),
                               (18, 4.2), (4, 10), (-16, 12.5), (-30, 13.6), (-42, 15), (-50, 16.6)])], T)
    body += scaled([("skin", [(-50, 29), (-44, 32), (-38, 33), (-30, 34), (-22, 39), (-12, 43), (0, 46.5), (12, 47),
                              (24, 44), (33, 38), (38, 31), (24, 37), (8, 40), (-8, 37), (-20, 32), (-34, 28),
                              (-46, 26)])], T)
    body += [("wart", octo(x, y * T, 4.2, 3.4, 0.35)) for x, y in ((-8, 26), (8, 24), (24, 26), (-26, 24), (32, 28),
                                                                    (-14, 33), (16, 33))]
    # the head: the wide down-turned mouth, the gland, the eye's dome with the heavy brow on it
    head = scaled([("lip", [(-54, 19.6), (-44, 19.4), (-32, 18.6), (-24.5, 15.6), (-23, 12.2), (-24.6, 12.0),
                            (-27, 15.4), (-34, 17.0), (-44, 17.6), (-54, 18.0)]),
                   ("gland", octo(-17, 37.5, 12, 7, 0.35, -10))], T)
    ey = 35.5 * T
    head += [("lid", octo(-36, ey + 1.5, 14, 10.5, 0.4, -4)),
             ("eye", rect(-39.4, ey + 0.8, 5.8, 2.6)), ("pupil", rect(-39.4, ey + 0.8, 3.9, 0.9)),
             ("lid", [(-42.6, ey + 2.4), (-36.2, ey + 3.4), (-35, ey + 2.0), (-36.4, ey + 2.3), (-42.6, ey + 1.6)]),
             ("brow", [(-44.4, ey + 2.0), (-42.4, ey + 4.4), (-39, ey + 6.0), (-35, ey + 6.8), (-29, ey + 6.0), (-29.2, ey + 4.2),
                       (-35, ey + 4.4), (-41.6, ey + 2.6)])]
    # the near front leg: a thick upper arm, a heavy forearm, a broad hand with big fingers
    sh = (-22, 27 * T)
    near = [("limb", limb(sh, (-17, 13), 16, 14)), ("limb", limb((-17, 13), (-30, 5), 14, 12)),
            ("limb", octo(-17, 13, 13, 12, 0.4)),                                      # the elbow
            ("toe", octo(-33, 3.6, 15, 7.2, 0.35))]                                     # the palm
    for tip, w in (((-52, 1.8), 5.4), ((-48, 1.6), 5.0), ((-43.5, 1.4), 4.6)):
        near += finger((-34, 3.2), tip, w, w + 1.2)
    # the near hind leg: a huge thigh, the shin folded under it, a long foot with big toes
    near += [("limb", octo(26, 19 * T, 32, 28 * T, 0.32, -14)), ("skin", octo(28, 25 * T, 21, 11, 0.35, -14)),
             ("limb", limb((40, 10), (26, 5), 12, 10)),
             ("toe", octo(14, 3.4, 26, 6.8, 0.3))]
    for tip, w in (((-6, 1.8), 5.4), ((-1, 1.6), 5.0)):
        near += finger((4, 3.2), tip, w, w + 1.0)
    return far + body + near + head


def pipe_side(T):
    m = (-26, 15.0 * T)
    bowl_x, bowl_y = -76, 11 * T - 1
    return [("pipe", limb(m, (bowl_x + 3.5, bowl_y + 1.4), 2.4, 2.2)), ("pipe_metal", rect(m[0] - 1.5, m[1], 2.4, 3.2, -6)),
            ("pipe_metal", [(bowl_x - 4, bowl_y), (bowl_x + 4, bowl_y), (bowl_x + 4.5, bowl_y + 8), (bowl_x - 4.5, bowl_y + 8)]),
            ("pipe", rect(bowl_x, bowl_y + 8.2, 8.0, 1.1)), ("lava_hot", rect(bowl_x, bowl_y + 8.2, 5.0, 0.9))], \
        (bowl_x, bowl_y + 9)


def face_path(v, base_y, tx, u, wiggle, phase, steps=7):
    top = v["top"]
    pts = []
    for i in range(steps + 1):
        t = i / steps
        y = top - 1 - (top - 1 - base_y) * t
        half = v["crater"] / 2 + (v["base_w"] / 2 - v["crater"] / 2) * (1 - (1 - t) ** 1.7)
        pts.append((tx + (u + wiggle * math.sin(phase + t * 5.0)) * half * 0.8, y))
    return pts


def volcano_side(v):
    T = v["T"]
    base = 34 * T
    outline, rim, crater = cone(v["cx"], base, v["top"], v["base_w"], v["crater"], v["lean"])
    out = [("basalt", outline),
           ("basalt_lit", [outline[2], outline[7], (outline[7][0] + 4, outline[7][1]), (outline[2][0] + 8, outline[2][1])])]
    x0 = max(-24, v["cx"] - v["base_w"] / 2 - 8)
    x1 = min(40, v["cx"] + v["base_w"] / 2 + 8)
    xs = [x0 + (x1 - x0) * i / 12 for i in range(13)]
    up = [(x, back_y(x, T) + (2 + 5 * ((i * 5) % 3) / 2) * math.sin(math.pi * i / 12)) for i, x in enumerate(xs)]
    low = [(x, back_y(x, T) - (3 + 5 * ((i * 7) % 3) / 2)) for i, x in enumerate(xs)][::-1]
    out.append(("ash", up + low))
    for i, x in enumerate(xs[1:-1:2]):
        out.append(("ash_dark", octo(x, back_y(x, T) - 1.5 - (i % 2) * 1.5, 5.4, 4.2, 0.35, 10 * (i % 3 - 1))))
    out += [("lava", rect(crater[0], crater[1] + 0.4, v["crater"] * 0.5, 2.4)),
            ("lava_hot", rect(crater[0], crater[1] + 0.6, v["crater"] * 0.3, 1.2))]
    a = face_path(v, base, crater[0], -0.45, 0.18, 0.0) + [(-16, back_y(-16, T) - 4), (-13, 30 * T), (-11, 19 * T)]
    b = face_path(v, base, crater[0], 0.3, 0.15, 1.8) + [(28, back_y(28, T) - 4), (32, 30 * T)]
    c = face_path(v, base, crater[0], -0.05, 0.2, 3.1, steps=4)[2:]
    out += stream(a, 3.6, 2.2) + stream(b, 3.2, 2.0) + stream(c, 2.4, 1.7)
    return out, crater


# ---- front view ------------------------------------------------------------------------------------------------

def toad_front(T):
    half = []
    # the hind leg's thigh and foot out at the side, behind the front leg
    half += [("far", octo(50, 17 * T, 20, 24 * T, 0.32)), ("far", octo(62, 3, 18, 6, 0.3))]
    # the body behind the head: broad shoulders sloping up into the back
    half += scaled([("flank", [(0, 4), (34, 5), (43, 12), (45, 25), (41, 34), (28, 40), (0, 42)])], T)
    # the front leg, drawn over the body: the upper arm out to an elbow standing clear of the body, a heavy forearm
    # down, a broad hand with four big splayed fingers
    sh, el, wr = (36, 24 * T), (57, 15 * T), (52, 5)
    half += [("limb", limb(sh, el, 17, 15)), ("limb", limb(el, wr, 15, 13)), ("limb", octo(el[0], el[1], 14, 13, 0.4)),
             ("toe", octo(52, 3.4, 17, 7, 0.35))]
    for tip, w in (((37, 1.8), 5.0), ((45, 1.4), 5.6), ((59, 1.4), 5.6), ((67, 1.8), 5.0)):
        half += finger((52, 3), tip, w, w + 1.2)
    # the head: wide, the throat below the mouth
    half += scaled([("skin", [(0, 9), (28, 10), (35, 15), (36, 26), (32, 33), (20, 35), (0, 35.5)]),
                    ("belly", [(0, 5), (24, 6), (31, 10.4), (32, 15), (0, 15)]),
                    ("lip", [(0, 16.4), (26, 16.2), (33, 13), (34, 14.2), (27, 17.8), (0, 18)])], T)
    ey = 35.5 * T
    half += [("gland", octo(33, ey - 1.5, 10, 8, 0.35)),
             ("lid", octo(22, ey + 4.5, 15, 13, 0.4)),
             ("eye", rect(22, ey + 3.5, 7.6, 2.8)), ("pupil", rect(22, ey + 3.5, 5.2, 1.0)),
             ("lid", [(16, ey + 5.3), (28.6, ey + 6.3), (28.6, ey + 4.9), (16, ey + 4.3)]),
             ("brow", [(12.4, ey + 5.1), (18, ey + 9.5), (27, ey + 11.5), (30.4, ey + 9.1), (22, ey + 7.3), (14.4, ey + 4.1)])]
    half += [("wart", octo(x, y * T, 3.8, 3.2, 0.35)) for x, y in ((41, 22), (42, 32), (8, 30), (12, 24))]
    return half + mirror(half)


def volcano_front(v):
    T = v["T"]
    base = 40 * T
    outline, rim, crater = cone(0, base, v["top"], v["base_w"], v["crater"], 0)
    w = min(46, v["base_w"] / 2 + 6)
    out = [("ash", [(-w, 36 * T), (-w + 5, 43 * T), (0, 46 * T), (w - 5, 43 * T), (w, 36 * T), (0, 40 * T)]),
           ("basalt", outline),
           ("basalt_lit", [outline[2], outline[7], (outline[7][0] + 3, outline[7][1]), (outline[2][0] + 7, outline[2][1])]),
           ("lava", rect(crater[0], crater[1] + 0.4, v["crater"] * 0.5, 2.4)),
           ("lava_hot", rect(crater[0], crater[1] + 0.6, v["crater"] * 0.3, 1.2))]
    out += stream(face_path(v, base, 0, -0.5, 0.15, 0.4), 3.6, 2.2) + stream(face_path(v, base, 0, 0.42, 0.18, 2.2), 3.4, 2.0)
    out += stream(face_path(v, base, 0, 0.05, 0.22, 4.0, steps=5), 2.6, 1.7)
    return out, crater


def flank_lava_front(T):
    return (stream([(-38, 41 * T), (-43, 33 * T), (-45.5, 25 * T), (-46, 17 * T)], 3.4, 2.0)
            + stream([(38, 41 * T), (43, 32 * T), (45, 26 * T), (46, 20 * T)], 3.2, 1.9))


def pipe_front(T):
    m = (-28, 16.4 * T)
    bx, by = -58, 9 * T - 2
    return [("pipe", limb(m, (bx + 3, by + 1.5), 2.6, 2.2)), ("pipe_metal", rect(m[0] - 1, m[1], 2.6, 3.2, 15)),
            ("pipe_metal", [(bx - 4, by), (bx + 4, by), (bx + 4.5, by + 8), (bx - 4.5, by + 8)]),
            ("pipe", rect(bx, by + 8.2, 8.0, 1.1)), ("lava_hot", rect(bx, by + 8.2, 5.0, 0.9))], (bx, by + 9)


# ---- drawing ---------------------------------------------------------------------------------------------------

def draw_view(v, view, mode, w, h):
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), (104, 110, 124, 255) if mode == "value" else PAPER + (255,))
    d = ImageDraw.Draw(img)
    oy = H - 22 * SS
    ox = (240 if view == "side" else 200) * SS
    if mode == "value":
        d.rectangle((0, oy, W, H), fill=(78, 80, 88))
    d.line((0, oy, W, oy), fill=(120, 116, 110), width=2 * SS)
    k = S * SS
    T = v["T"]
    if view == "side":
        vol, crater = volcano_side(v)
        pipe, bowl = pipe_side(T)
        parts = toad_side(T) + vol + pipe
    else:
        vol, crater = volcano_front(v)
        pipe, bowl = pipe_front(T)
        parts = vol + toad_front(T) + flank_lava_front(T) + pipe
    for tone, p in parts:
        col = SIL if mode == "sil" else TONE.get(tone, (150, 120, 84))
        d.polygon([(ox + x * k, oy - y * k) for x, y in p], fill=col)
    if mode == "value":
        smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(smoke)
        for x, y, r, a in plume(crater, 9, v["crater"] * 0.55, 26 if view == "side" else 10, 46, 0.5) + plume(bowl, 5, 3.2, 8, 18, 2.0):
            cx, cy = ox + x * k, oy - y * k
            sd.ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), fill=SMOKE + (a,))
        img = Image.alpha_composite(img, smoke)
        d = ImageDraw.Draw(img)
    px = W - 30 * SS
    ph, pw = 28.8 * k, 7.2 * k
    d.rectangle((px - pw / 2, oy - ph * 0.75, px + pw / 2, oy), fill=PLAYER)
    d.rectangle((px - pw * 0.55, oy - ph, px + pw * 0.55, oy - ph * 0.75), fill=PLAYER)
    return img.convert("RGB").resize((w, h), Image.LANCZOS)


def draw_step1(view, mode, w, h):
    """Step 1's B at this sheet's scale, for comparison."""
    old_s = s1.S
    s1.S = S
    try:
        return s1.draw_view(s1.VARIANTS["B"], view, mode, w, h)
    finally:
        s1.S = old_s


TONE["toe_pad"] = (150, 122, 84)
TONE["limb"] = (126, 102, 66)


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
    cols = [("B", "B  step 1")] + [(k, v["name"]) for k, v in VARIANTS.items()]
    cw, ch, pad, top, lab = 430, 360, 10, 50, 30
    sheet = Image.new("RGB", (len(cols) * (cw + pad) + pad, top + lab + len(rows) * (ch + pad)), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 12), "The Elder of Ash - step 1, take 2: a bigger, taller toad with beefier limbs", font=font, fill=INK)
    for i, (key, name) in enumerate(cols):
        dr.text((pad + i * (cw + pad), top), name, font=small, fill=DIM)
    for r, (view, mode) in enumerate(rows):
        for i, (key, _) in enumerate(cols):
            img = draw_step1(view, mode, cw, ch) if key == "B" else draw_view(VARIANTS[key], view, mode, cw, ch)
            if key != "B":
                img.save(OUT / f"{key}_{view}_{mode}.png")
            sheet.paste(img, (pad + i * (cw + pad), top + lab + r * (ch + pad)))
    sheet.save(OUT / "silhouettes.png")
    for key, v in VARIANTS.items():
        print(key, "back", round(47 * v["T"] / 16, 2), "blocks; crater", round(v["top"] / 16, 2), "blocks")
    print("wrote", OUT / "silhouettes.png")


if __name__ == "__main__":
    main()
