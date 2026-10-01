"""Session B: sigils, runes, footprints and crown pieces (grayscale, tintable, exact symmetry where it belongs)."""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from glyphkit import Glyph, asymmetry, star, star_outline, style, tint  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "art", "session-b")
os.makedirs(OUT, exist_ok=True)

TINTS = {"T0 ember": (255, 170, 90), "T1 violet": (190, 130, 255), "T2 teal": (90, 225, 210), "T3 crimson": (235, 60, 70)}
C = 32.0  # centre of a 64 px sigil


# ------------------------------------------------------------------ sigils (64 x 64)

def pentagram_a():
    g = Glyph(64)
    g.ring(C, C, 29.6, 2.6)
    g.ring(C, C, 24.8, 2.0)
    pts = star(C, C, 24.6)
    g.polyline([pts[i] for i in (0, 2, 4, 1, 3)], 2.6, closed=True)
    # ticks between the rings, halfway between the points
    for i in range(5):
        a = -math.pi / 2 + math.pi / 5 + i * 2 * math.pi / 5
        g.line((C + 25.8 * math.cos(a), C + 25.8 * math.sin(a)), (C + 28.6 * math.cos(a), C + 28.6 * math.sin(a)), 2.2)
    return g


def pentagram_b():
    g = Glyph(64)
    g.ring(C, C, 28.5, 4.0)
    g.polygon(star_outline(C, C, 25.5, 10.4))
    g.erase_disc(C, C, 4.6)
    return g


def hexagram_a():
    g = Glyph(64)
    g.ring(C, C, 29.5, 2.6)
    up = star(C, C, 24.6, n=3)
    down = star(C, C, 24.6, n=3, rot=math.pi / 2)
    g.polyline(up, 2.6, closed=True)
    g.polyline(down, 2.6, closed=True)
    g.ring(C, C, 8.0, 1.8)
    return g


def hexagram_b():
    g = Glyph(64)
    g.ring(C, C, 28.5, 4.0)
    g.polygon(star_outline(C, C, 25.5, 14.7, n=6))
    g.erase_polygon(star(C, C, 8.5, n=6, rot=-math.pi / 2))
    return g


def sigil_initiate():
    g = Glyph(64)
    g.ring(C, C, 28.5, 3.0)
    g.line((C, C - 22), (C, C + 22), 3.0)
    g.line((C - 22, C), (C + 22, C), 3.0)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        g.disc(C + 18.5 * math.cos(a), C + 18.5 * math.sin(a), 3.2)
    g.disc(C, C, 5.2)
    return g


def sigil_bound():
    g = Glyph(64)
    g.ring(C, C, 27.5, 3.0)
    tri = star(C, C, 27.5, n=3)
    g.polyline(tri, 3.0, closed=True)
    # clamps where the triangle seals the circle
    for (x, y) in tri:
        a = math.atan2(y - C, x - C)
        tx, ty = -math.sin(a), math.cos(a)
        g.line((x - tx * 4.5, y - ty * 4.5), (x + tx * 4.5, y + ty * 4.5), 3.6)
    g.ring(C, C, 7.0, 2.4)
    g.disc(C, C, 2.6)
    return g


def sigil_abyssal():
    g = Glyph(64)
    g.ring(C, C, 28.5, 3.0)
    upper = [(C + dx, C - 3 - 9.0 * math.cos(dx / 17.0 * math.pi / 2)) for dx in [i - 17 for i in range(35)]]
    lower = [(C + dx, C - 3 + 9.0 * math.cos(dx / 17.0 * math.pi / 2)) for dx in [i - 17 for i in range(35)]]
    g.polyline(upper, 2.8)
    g.polyline(lower, 2.8)
    g.disc(C, C - 3, 4.8)
    for k, y0 in enumerate((C + 12.5, C + 18.5)):
        width = 15 - k * 3
        wave = [(C + dx, y0 + 2.4 * math.cos(dx / 3.0)) for dx in [i * 0.5 - width for i in range(int(width * 4) + 1)]]
        g.polyline(wave, 2.8)
    return g


def sigil_hollow():
    g = Glyph(64)
    g.ring(C, C + 1.5, 24.5, 3.0)
    g.polygon(star_outline(C, C + 1.5, 20.5, 8.4))
    g.erase_disc(C, C + 1.5, 3.8)
    # a crown of spikes rising from the ring, in line with the star's points
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        tip = (C + 31.2 * math.cos(a), C + 1.5 + 31.2 * math.sin(a))
        l = (C + 24.5 * math.cos(a - 0.2), C + 1.5 + 24.5 * math.sin(a - 0.2))
        r = (C + 24.5 * math.cos(a + 0.2), C + 1.5 + 24.5 * math.sin(a + 0.2))
        g.polygon([tip, l, r])
    return g


SIGILS = [("pentagram A (lines)", pentagram_a), ("pentagram B (bold)", pentagram_b), ("hexagram A (lines)", hexagram_a),
          ("hexagram B (bold)", hexagram_b), ("sigil T0 Initiate", sigil_initiate), ("sigil T1 Bound", sigil_bound),
          ("sigil T2 Abyssal", sigil_abyssal), ("sigil T3 Hollow", sigil_hollow)]


# ------------------------------------------------------------------ review sheet for glyphs

def sheet(items, path, scale=2):
    """items: [(name, image)]. Each row: native 1x, on dark and light, then tinted per tier on dark; with asymmetry."""
    biggest = max(max(i.width, i.height) for _, i in items)
    cell = biggest * scale
    pad = 10
    cols = ["1x", "dark", "light"] + list(TINTS)
    width = 200 + len(cols) * (cell + pad)
    height = 28 + len(items) * (cell + pad)
    out = Image.new("RGB", (width, height), (30, 28, 36))
    d = ImageDraw.Draw(out)
    for c, title in enumerate(cols):
        d.text((200 + c * (cell + pad), 8), title, fill=(200, 200, 210))
    for r, (name, img) in enumerate(items):
        y = 28 + r * (cell + pad)
        d.text((8, y + cell // 2 - 12), name, fill=(232, 232, 240))
        d.text((8, y + cell // 2 + 2), f"asymmetry: {asymmetry(img)}", fill=(150, 150, 165))
        views = [(img, 1, (24, 22, 30)), (img, scale, (24, 22, 30)), (img, scale, (214, 208, 198))]
        views += [(tint(img, t), scale, (24, 22, 30)) for t in TINTS.values()]
        for c, (im, s, bg) in enumerate(views):
            panel = Image.new("RGB", (cell, cell), bg)
            big = im.resize((im.width * s, im.height * s), Image.NEAREST)
            panel.paste(big, ((cell - big.width) // 2, (cell - big.height) // 2), big)
            out.paste(panel, (200 + c * (cell + pad), y))
    out.save(path)
    return path


def render(group, version):
    made = []
    for name, make in group:
        img = style(make().pixels(mirror=True))
        img.save(os.path.join(OUT, name.split(" (")[0].replace(" ", "_").lower() + ("_" + name.split("(")[1][0].lower() if "(" in name else "") + ".png"))
        made.append((name, img))
    return made


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "sigils"
    version = sys.argv[2] if len(sys.argv) > 2 else "v1"
    if which == "sigils":
        print(sheet(render(SIGILS, version), os.path.join(OUT, f"review-sigils-{version}.png")))
