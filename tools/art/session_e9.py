"""Session E9: the Staff Raid's art.

- S4MURAI's katana (`s4murai_katana`, boss-only, held): a long, slightly curved blade of black steel with a dark
  crimson hamon, its cutting edge a crimson glow with a glint sweeping along it (animated); a crimson habaki, a black
  octagonal tsuba rimmed in crimson, a crimson-on-black diamond-wrapped grip and a black kashira. Built upright and laid
  on a sword's diagonal with vanilla's handheld transforms, like the Frenzy Cleaver.
- Two floor symbols in Session O4's style (light greys, tinted by the game): `floor_mark_soak` (three figures gathered
  - stand in it together) and `floor_mark_target` (a reticle - you're marked).
- `raid_wall`: an energy pane for walls and sweeping barriers - a see-through, glowing field of rising hexagonal cells
  between two bright rails, drawn in greys so each wall takes its own tint (animated).

Run: python tools/art/session_e9.py  -> parts in docs/art/session-g/, review sheet docs/art/session-e9/review-e9.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import hexes  # noqa: E402
from PIL import Image  # noqa: E402
import render3d  # noqa: E402
import session_g as g  # noqa: E402
import session_o4 as o4  # noqa: E402

REVIEW = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-e9")
os.makedirs(REVIEW, exist_ok=True)

# black steel with a violet lean in the shadows and a cold highlight; crimson that warms toward white as it brightens
BLACK = hexes("#0b090e", "#17131b", "#251f2b", "#373040", "#524a5c", "#7d7488")
CRIMSON = hexes("#2a0508", "#560a10", "#8c1018", "#c41d22", "#ee4a36", "#ffb48c")


def solid(ramp, idx):
    img = g.blank()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), ramp[idx])
    return img


# The blade is painted, not built: one 64 px texture holds its silhouette as an 8 x 64 strip (u 0-2, v 0-16 of the
# model's uv), 0.3 units a texel. Row 0 is the base at the habaki, row 63 the tip (the image is drawn tip up).
BLADE_W, BLADE_ROWS, TEXEL = 8, 64, 0.3


def blade_shape(r):
    """Where the blade is on row r (0 = base, 63 = tip): (spine, edge) in texels across the strip. The whole blade bows
    toward the spine side as it nears the tip (sori), narrows a little, and in the last rows the edge sweeps up to meet
    the spine in the point (the kissaki)."""
    t = r / (BLADE_ROWS - 1)
    spine = 2.0 - 2.0 * t * t
    width = 6.0 - 2.0 * t
    if r >= BLADE_ROWS - 9:
        k = (BLADE_ROWS - 1 - r) / 8
        width = max(0.9, width * k ** 0.6)
    return spine, spine + width


def hamon(r):
    """The temper line's place across the blade (0 = spine, 1 = edge): wavy, like a gunome hamon."""
    return 0.6 + 0.07 * math.sin(r * 0.22)


def blade_texture():
    """The blade's flat, both faces: a dark spine, the shinogi ridge catching the light, black steel, the crimson
    hamon, polished hardened steel up to the edge (the edge itself glows on its own overlay)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for r in range(BLADE_ROWS):
        spine, edge = blade_shape(r)
        y = BLADE_ROWS - 1 - r
        for c in range(BLADE_W):
            mid = c + 0.5
            if not (spine <= mid < edge):
                continue
            f = (mid - spine) / (edge - spine)
            h = hamon(r)
            if f < 0.17:
                col = BLACK[1]                                         # the spine
            elif f < 0.34:
                col = BLACK[4]                                         # the shinogi ridge, one clean line of light
            elif abs(f - h) < 0.08:
                col = CRIMSON[1]                                       # the hamon: a long, slow, dark crimson wave
            elif f < h:
                col = BLACK[2]                                         # the flat
            elif f < 0.84:
                col = BLACK[3]                                         # hardened steel, a step brighter than the flat
            else:
                col = CRIMSON[3]                                       # the edge (glows on the overlay)
            img.putpixel((c, y), col)
    return img


def blade_glow(n=8):
    """The glowing edge on its own (everything else clear): crimson, hottest at the edge, with a white-hot glint
    sweeping from the habaki to the tip over the frames (the tip burns brightest)."""
    out = []
    for fr in range(n):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        glint = fr * BLADE_ROWS / n
        for r in range(BLADE_ROWS):
            spine, edge = blade_shape(r)
            y = BLADE_ROWS - 1 - r
            near = abs(((r - glint + BLADE_ROWS / 2) % BLADE_ROWS) - BLADE_ROWS / 2)
            tip = r >= BLADE_ROWS - 9
            for c in range(BLADE_W):
                mid = c + 0.5
                if not (spine <= mid < edge):
                    continue
                f = (mid - spine) / (edge - spine)
                if f < 0.84 and not (tip and f > 0.5):
                    continue
                base = 4 if tip else 3
                if near < 1.5:
                    base = 5
                elif near < 4:
                    base = max(base, 4)
                img.putpixel((c, y), CRIMSON[base])
        out.append(img)
    return out


def wrap():
    """Tsukamaki: crimson cord crossing over a black ray-skin core, in diamonds (lit from the top-left)."""
    img = g.blank()
    for y in range(16):
        for x in range(16):
            a = (x + y) % 8
            b = (x - y) % 8
            if a in (0, 1) or b in (0, 1):
                c = CRIMSON[3] if (a == 0 or b == 0) else CRIMSON[2]
            else:
                c = BLACK[2] if (x + y) % 3 else BLACK[1]
            img.putpixel((x, y), c)
    return img


def katana_held():
    """S4MURAI's katana in the hand (boss-only)."""
    m = g.Model("s4murai_katana")
    m.part = True
    t_black = m.texture("black", g.metal(BLACK, 991, tone=2))
    t_black_lit = m.texture("black_lit", g.metal(BLACK, 992, tone=3))
    t_crimson = m.texture("crimson", g.metal(CRIMSON, 993, tone=3))
    t_wrap = m.texture("wrap", wrap())
    # handle: kashira, wrapped grip; then the guard and collar
    g.prism(m, 1.5, -4.6, -4.0, t_black_lit)                         # kashira (pommel cap)
    g.prism(m, 1.25, -4.0, 1.4, (t_wrap, [0, 0, 2, 6]))              # the wrapped grip
    g.prism(m, 3.6, 1.4, 2.0, t_black, d=3.6)                        # tsuba (guard), octagonal: two crossed plates
    g.prism(m, 2.6, 1.42, 1.98, t_black_lit, d=4.4)
    g.prism(m, 4.4, 1.42, 1.98, t_black_lit, d=2.6)
    g.prism(m, 3.8, 1.55, 1.85, t_crimson, d=3.8)                    # its crimson rim
    g.prism(m, 1.15, 2.0, 2.9, t_crimson, d=0.9)                     # habaki (collar)
    # the blade: two painted planes 0.3 apart (front and back), the glowing edge on a plane over each
    t_blade = m.texture("blade", blade_texture())
    t_glow = m.texture("glow", blade_glow())
    m.mcmeta["glow"] = {"animation": {"frametime": 2, "interpolate": True}}
    width, length = BLADE_W * TEXEL, BLADE_ROWS * TEXEL
    x0, y0 = 8 - 4.5 * TEXEL, 2.9                                    # the base's middle over the habaki
    front, back = [0, 0, 2, 16], [2, 0, 0, 16]
    m.box((x0, y0, 8.15), (x0 + width, y0 + length, 8.15), {"south": (t_blade, front)})
    m.box((x0, y0, 7.85), (x0 + width, y0 + length, 7.85), {"north": (t_blade, back)})
    m.box((x0, y0, 8.17), (x0 + width, y0 + length, 8.17), {"south": (t_glow, front)}, shade=False, light=15)
    m.box((x0, y0, 7.83), (x0 + width, y0 + length, 7.83), {"north": (t_glow, back)}, shade=False, light=15)
    m.display = g.HANDHELD_DISPLAY
    return g.diagonal(m)


SOAK = [   # three figures gathered round: stand in it together
    "................",
    "......####......",
    "......#OO#......",
    "......####......",
    ".....######.....",
    ".....######.....",
    "................",
    "..####....####..",
    "..#OO#....#OO#..",
    "..####....####..",
    ".######..######.",
    ".######..######.",
    "................",
    "................",
    "................",
    "................",
]
def reticle():
    """A reticle: a ring, four ticks pointing in, a dot in the middle (you're marked)."""
    rows = []
    for y in range(16):
        row = ""
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            axis = abs(x + 0.5 - 8) < 1 or abs(y + 0.5 - 8) < 1
            if d < 1.2:
                row += "O"
            elif 6.0 <= d < 7.2:
                row += "#"
            elif axis and 3.8 <= d < 6.0:
                row += "#"
            else:
                row += "."
        rows.append(row)
    return rows


TARGET = reticle()


def wall_frames(n=6):
    """An energy pane in greys (tinted per wall): bright rails top and bottom, a see-through field that glows more toward
    the rails, faint upright streaks, and a band of light rising through it over the frames."""
    out = []
    for f in range(n):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        band = (16 - f * 16 / n) % 16
        for y in range(16):
            for x in range(16):
                if y in (0, 15):
                    img.putpixel((x, y), o4.rgba(o4.GREY[5]))           # the rails
                    continue
                rail = min(y, 15 - y)                                    # 1 next to a rail .. 7 in the middle
                near = abs(((y - band + 8) % 16) - 8)
                lift = 2 if near < 1.0 else 1 if near < 2.5 else 0
                streak = x % 4 == (f + y // 5) % 4                      # faint upright streaks, drifting
                tone = min(5, (5 if rail == 1 else 4 if rail <= 3 else 3) + lift + (1 if streak else 0))
                alpha = min(230, (190 if rail == 1 else 110 if rail <= 3 else 55) + 50 * lift + (40 if streak else 0))
                img.putpixel((x, y), o4.rgba(o4.GREY[tone], alpha))
        out.append(img)
    return out


def raid_wall():
    """An upright pane, 16 units square through the model's centre, the field on both faces, glowing, tinted."""
    m = g.Model("raid_wall")
    m.part = True
    t = m.texture("field", wall_frames())
    m.mcmeta["field"] = {"animation": {"frametime": 2, "interpolate": False}}
    e = m.box((0, 0, 8), (16, 16, 8), {"south": (t, [0, 0, 16, 16]), "north": (t, [16, 0, 0, 16])}, shade=False, light=15)
    for face in e["faces"].values():
        face["tintindex"] = 0
    m.tinted = True
    return m


def models():
    return [katana_held(), o4.plane("floor_mark_soak", o4.symbol(SOAK), tint=True, light=15),
            o4.plane("floor_mark_target", o4.symbol(TARGET), tint=True, light=15), raid_wall()]


def review(ms):
    katana = ms[0]
    # the katana in the hand's frame is laid on the diagonal; render it lying flat from a few angles, edge frames too
    views = [render3d.render(katana, frame=f, yaw=yaw, pitch=pitch, s=18, size=(520, 520), center=(8, 9, 8))
             for (yaw, pitch, f) in ((0, 0, 0), (30, 25, 2), (330, 20, 5))]
    sheet = Image.new("RGBA", (520 * 3 + 40, 520 + 260), (40, 38, 46, 255))
    for i, v in enumerate(views):
        sheet.alpha_composite(v, (10 + i * 530, 10))
    # floor symbols tinted like the game would, the wall field over a floor
    tints = [(80, 220, 110), (240, 170, 40), (255, 60, 60), (200, 60, 230)]
    x = 10
    for m, tint in ((ms[1], tints[0]), (ms[1], tints[1]), (ms[2], tints[3]), (ms[2], tints[2])):
        img = m.textures["face"].resize((160, 160), Image.NEAREST)
        px = img.load()
        for yy in range(160):
            for xx in range(160):
                r, gg, b, a = px[xx, yy]
                px[xx, yy] = (r * tint[0] // 255, gg * tint[1] // 255, b * tint[2] // 255, a)
        sheet.alpha_composite(img, (x, 540))
        x += 180
    for fi, fr in enumerate(ms[3].textures["field"][:3]):
        for tint in ((120, 200, 255),):
            img = fr.resize((160, 160), Image.NEAREST)
            px = img.load()
            for yy in range(160):
                for xx in range(160):
                    r, gg, b, a = px[xx, yy]
                    px[xx, yy] = (r * tint[0] // 255, gg * tint[1] // 255, b * tint[2] // 255, a)
            sheet.alpha_composite(img, (x + fi * 180, 540))
    path = os.path.join(REVIEW, "review-e9.png")
    sheet.save(path)
    frames = [render3d.render(katana, frame=f, yaw=30, pitch=25, s=18, size=(420, 420), center=(8, 9, 8)).convert("RGB") for f in range(8)]
    frames[0].save(os.path.join(REVIEW, "preview-katana.gif"), save_all=True, append_images=frames[1:], duration=100, loop=0)
    return path


if __name__ == "__main__":
    ms = models()
    for m in ms:
        o4.save(m)
    print(review(ms))
