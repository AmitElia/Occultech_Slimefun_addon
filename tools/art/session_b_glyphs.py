"""Session B: runes (an original Occultech alphabet) and the paw print - flat glyphs with outline and glow (both kept from round 1 on the user's review)."""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from glyphkit import Glyph, asymmetry, style, tint  # noqa: E402
from session_b import OUT  # noqa: E402

TINTS = {"T0 ember": (255, 170, 90), "T1 violet": (190, 130, 255), "T2 teal": (90, 225, 210), "T3 crimson": (235, 60, 70)}


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

# ------------------------------------------------------------------ runes (16 x 16)
# (name, strokes, symmetric). Strokes are polylines in 16 px space; the centre staff is x = 8.

RUNE_W = 2.0
RUNES = [
    ("ascend", [[(8, 2.5), (8, 14)], [(4, 7.5), (8, 2.5), (12, 7.5)]], True),
    ("root", [[(8, 2), (8, 9)], [(4, 14), (8, 9), (12, 14)]], True),
    ("eye", [[(8, 2.5), (13, 8), (8, 13.5), (3, 8), (8, 2.5)]], True),
    ("bind", [[(3.5, 2.5), (12.5, 2.5), (3.5, 13.5), (12.5, 13.5), (3.5, 2.5)]], True),
    ("gate", [[(4.5, 2), (4.5, 14)], [(11.5, 2), (11.5, 14)], [(4.5, 5), (8, 9), (11.5, 5)]], True),
    ("flame", [[(4, 2.5), (8, 7), (12, 2.5)], [(8, 7), (8, 14)]], True),
    ("hook", [[(9, 2), (9, 11), (8, 13.5), (5.5, 13.5), (4, 11)], [(9, 4.5), (12, 2.5)]], False),
    ("tide", [[(2.5, 6), (5.5, 3), (8.5, 6), (11.5, 3), (13.5, 5)], [(2.5, 12), (5.5, 9), (8.5, 12), (11.5, 9), (13.5, 11)]], False),
    ("moon", "moon", False),
    ("sun", "sun", True),
    ("ward", [[(8, 2), (8, 14)], [(3, 5.5), (13, 5.5)], [(3, 10.5), (13, 10.5)]], True),
    ("chain", "chain", True),
    ("spirit", "spirit", True),
    ("bone", [[(8, 4.5), (8, 11.5)], [(4.5, 2), (8, 4.5), (11.5, 2)], [(4.5, 14), (8, 11.5), (11.5, 14)]], True),
    ("thorn", [[(6, 2), (6, 14)], [(6, 4.5), (11.5, 8), (6, 11.5)]], False),
    ("star", [[(8, 2), (8, 14)], [(3, 5), (13, 11)], [(13, 5), (3, 11)]], True),
    ("seal", [[(3.5, 3.5), (12.5, 3.5), (12.5, 12.5), (3.5, 12.5), (3.5, 3.5)], [(8, 6.5), (8, 9.5)]], True),
    ("descend", [[(8, 2), (8, 13.5)], [(4, 9.5), (8, 13.5), (12, 9.5)]], True),
    ("crown", [[(3, 3), (5, 9), (8, 4.5), (11, 9), (13, 3)], [(4, 13), (12, 13)]], True),
    ("storm", [[(10.5, 2), (6, 8), (10, 8), (5.5, 14)]], False),
    ("twin", "twin", True),
    ("hollow", "hollow", True),
    ("key", "key", False),
    ("veil", [[(4, 3.5), (8, 7.5), (12, 3.5)], [(4, 9), (8, 13), (12, 9)]], True),
]


def rune(strokes):
    g = Glyph(16)
    if strokes == "moon":
        g.ring(9, 8, 5.2, RUNE_W)
        g.erase_disc(12.2, 6.8, 4.6)
    elif strokes == "twin":
        g.polyline([(4.5, 2.5), (4.5, 13.5), (11.5, 13.5), (11.5, 2.5)], RUNE_W)
        g.disc(8, 6.5, 1.6)
    elif strokes == "chain":
        g.ring(5.6, 8, 3.2, RUNE_W)
        g.ring(10.4, 8, 3.2, RUNE_W)
    elif strokes == "sun":
        g.ring(8, 8, 3.0, RUNE_W)
        for (a, b) in (((8, 1.5), (8, 3.6)), ((8, 12.4), (8, 14.5)), ((1.5, 8), (3.6, 8)), ((12.4, 8), (14.5, 8))):
            g.line(a, b, RUNE_W)
    elif strokes == "spirit":
        g.ring(8, 5, 2.8, RUNE_W)
        g.line((8, 7.8), (8, 13.5), RUNE_W)
        g.line((4.5, 13.5), (11.5, 13.5), RUNE_W)
    elif strokes == "hollow":
        g.ring(8, 8, 5.0, RUNE_W)
        g.line((8, 1.5), (8, 14.5), RUNE_W)
    elif strokes == "key":
        g.ring(8, 4.5, 2.6, RUNE_W)
        g.line((8, 7.1), (8, 14), RUNE_W)
        g.line((8, 10.5), (11.5, 10.5), RUNE_W)
        g.line((8, 13.5), (11, 13.5), RUNE_W)
    else:
        for stroke in strokes:
            g.polyline(stroke, RUNE_W)
    return g


# ------------------------------------------------------------------ footprints (16 x 16, left foot; the right is mirrored)

def footprint_paw():
    g = Glyph(16)
    g.d.ellipse((4.6 * 8, 8.8 * 8, 11.4 * 8, 14.8 * 8), fill=255)
    for (x, y) in ((2.8, 7.0), (5.6, 3.4), (10.4, 3.4), (13.2, 7.0)):
        g.disc(x, y, 1.45)
    return g.pixels(mirror=True)


PRINTS = [("footprint paw", footprint_paw, False)]  # boot and bare prints were dropped (see session_b_steps.py)


def rune_sheet(runes, path, scale=4):
    """All runes in a grid (each tinted by a tier in turn, 4x and 1x), plus the alphabet as a line of text."""
    cols = 6
    cell = 16 * scale + 24
    rows = (len(runes) + cols - 1) // cols
    out = Image.new("RGB", (cols * (cell + 70) + 20, rows * (cell + 30) + 120), (30, 28, 36))
    d = ImageDraw.Draw(out)
    tints = list(TINTS.values())
    for i, (name, img) in enumerate(runes):
        x = 20 + (i % cols) * (cell + 70)
        y = 20 + (i // cols) * (cell + 30)
        big = tint(img, tints[i % 4]).resize((16 * scale, 16 * scale), Image.NEAREST)
        out.paste(big, (x, y), big)
        out.paste(img, (x + 16 * scale + 8, y + 16 * scale - 16), img)
        sym = asymmetry(img)
        d.text((x, y + 16 * scale + 4), name + (" (sym)" if sym == 0 else ""), fill=(220, 220, 230))
    y = 20 + rows * (cell + 30)
    d.text((20, y), "as a line of text, 1x and 2x:", fill=(180, 180, 190))
    for i, (_, img) in enumerate(runes):
        out.paste(img, (20 + i * 17, y + 20), img)
        big = img.resize((32, 32), Image.NEAREST)
        out.paste(big, (20 + i * 34, y + 44), big)
    out.save(path)
    return path


if __name__ == "__main__":
    which = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "final"
    if which == "runes":
        made = []
        for name, strokes, symmetric in RUNES:
            img = style(rune(strokes).pixels(mirror=symmetric))
            img.save(os.path.join(OUT, "rune_" + name + ".png"))
            made.append((name, img))
        print(rune_sheet(made, os.path.join(OUT, f"review-runes{'' if version == 'final' else '-' + version}.png")))
    elif which == "prints":
        made = []
        for name, make, mirrored in PRINTS:
            img = style(make())
            img.save(os.path.join(OUT, name.replace(" ", "_") + ".png"))
            made.append((name, img))
            if mirrored:
                right = img.transpose(Image.FLIP_LEFT_RIGHT)
                right.save(os.path.join(OUT, name.replace(" ", "_") + "_right.png"))
                made.append((name + " (right)", right))
        print(sheet(made, os.path.join(OUT, f"review-prints{'' if version == 'final' else '-' + version}.png"), scale=4))
