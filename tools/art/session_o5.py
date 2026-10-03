"""Session O5, phase 1: effects in the air - beams, chains and bolts for boss fights.

Their textures are seamless loops that scroll along the effect, so it doesn't matter where the game's global
animation clock is when one appears; the motion that marks a start (a beam shooting out, a bolt dropping) is the
display's own interpolated movement, done by each player's client. Drawn in shaded light tones and tinted per effect
(the item model's dye tint), crisp pixels, glowing.

Models are parts the plugin shows: `python tools/art/session_o5.py`.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image  # noqa: E402
import session_g as g  # noqa: E402
from session_o4 import GREY, rgba  # noqa: E402

N = 16
FRAMES = 4


def blank():
    return Image.new("RGBA", (N, N), (0, 0, 0, 0))


def beam(f):
    """An energy beam seen side-on, its length running down the texture: a white-hot core, a bright sheath, and crackle
    flickering out along its edges - scrolling a quarter of the tile each frame, so it seems to pour toward the target."""
    img = blank()
    for y in range(N):
        yy = (y + f * 4) % N
        for x in range(N):
            d = abs(x - 7.5)
            if d < 1.0:
                img.putpixel((x, y), rgba(GREY[5]))
            elif d < 2.0:
                img.putpixel((x, y), rgba(GREY[4], 230))
            elif d < 3.0:
                img.putpixel((x, y), rgba(GREY[3], 150))
        # crackle: short jagged sparks leaving the sheath, two per tile per side, at fixed places in the scrolling tile
        for side in (-1, 1):
            for (sy, length) in ((2, 3), (9, 4)):
                k = (yy - sy - (3 if side > 0 else 0)) % N
                if k < length:
                    x = int(7.5 + side * (3 + k + (k % 2)))
                    if 0 <= x < N:
                        img.putpixel((x, y), rgba(GREY[4] if k < 2 else GREY[3], 220))
    return img


def chain(f):
    """A chain of soul light: oval links, alternately face-on and edge-on, with a glow that runs along it."""
    img = blank()
    for y in range(N):
        link = y // 8
        yy = y % 8
        for x in range(N):
            if link == 0:   # face-on: an oval ring
                dx, dy = (x - 7.5) / 3.6, (yy - 3.5) / 3.6
                r = math.hypot(dx, dy)
                on = 0.62 < r < 1.0
            else:           # edge-on: a bar
                on = abs(x - 7.5) < 1.0
            if on:
                lit = (y + f * 4) % N < 4
                img.putpixel((x, y), rgba(GREY[5] if lit else GREY[4] if x < 8 else GREY[3]))
    return img


def bolt_shape(seed):
    """A jagged plasma bolt from the top of the tile to the bottom, with a short fork - a white core in a bright sheath."""
    rnd = random.Random(seed)
    pts, x = [], 7.5
    for y in range(N):
        x = min(11.5, max(4.5, x + rnd.choice((-1.5, -1, 0, 1, 1.5))))
        pts.append((x, y))
    fork_at = rnd.randrange(5, 9)
    fx, fork = pts[fork_at][0], []
    side = rnd.choice((-1, 1))
    for k in range(1, 5):
        fork.append((fx + side * k * 0.9, fork_at + k))
    img = blank()
    for (px, py) in pts:
        for x in range(N):
            d = abs(x - px)
            if d < 0.75:
                img.putpixel((x, py), rgba(GREY[5]))
            elif d < 1.75 and img.getpixel((x, py))[3] == 0:
                img.putpixel((x, py), rgba(GREY[4], 220))
    for (px, py) in fork:
        x = int(px)
        if 0 <= x < N and py < N:
            img.putpixel((x, int(py)), rgba(GREY[4]))
    return img


def bolt(seed):
    """A bolt flickers: the same shape, its sheath brighter and dimmer by turns."""
    base = bolt_shape(seed)
    frames = []
    for f in range(FRAMES):
        img = base.copy()
        if f % 2:
            for y in range(N):
                for x in range(N):
                    p = img.getpixel((x, y))
                    if 0 < p[3] < 255:
                        img.putpixel((x, y), rgba(GREY[3], 170))
        frames.append(img)
    return frames


def streak(key, textures, segments):
    """Two crossed planes along the model's y axis (0..16), the texture repeating `segments` times along it - a beam
    or chain, stretched by the plugin between two points. Glowing, unshaded, tinted."""
    m = g.Model(key)
    m.part = True
    t = m.texture("streak", textures)
    step = 16 / segments
    for i in range(segments):
        y0, y1 = i * step, (i + 1) * step
        for e in (m.box((0, y0, 8), (16, y1, 8), {"north": (t, [0, 0, 16, 16]), "south": (t, [0, 0, 16, 16])}, shade=False, light=15),
                  m.box((8, y0, 0), (8, y1, 16), {"east": (t, [0, 0, 16, 16]), "west": (t, [0, 0, 16, 16])}, shade=False, light=15)):
            for face in e["faces"].values():
                face["tintindex"] = 0
    m.tinted = True
    return m


def models():
    out = [streak("air_beam", [beam(f) for f in range(FRAMES)], 8),
           streak("air_chain", [chain(f) for f in range(FRAMES)], 8)]
    for i, seed in enumerate((3, 17, 42)):
        out.append(streak(f"air_bolt_{i}", bolt(seed), 1))
    return out


def save(m):
    g.save(m)
    open(os.path.join(g.OUT, m.key, "tint.txt"), "w").write("dye\n")


if __name__ == "__main__":
    ms = models()
    for m in ms:
        save(m)
    sheet = Image.new("RGBA", (len(ms) * 90 + 10, 4 * 70 + 10), (34, 32, 40, 255))
    tints = [(120, 230, 210), (110, 200, 255), (190, 150, 255), (190, 150, 255), (190, 150, 255)]
    for i, m in enumerate(ms):
        frames = m.textures["streak"]
        for f, img in enumerate(frames if isinstance(frames, list) else [frames]):
            tinted = Image.new("RGBA", img.size)
            for y in range(N):
                for x in range(N):
                    p = img.getpixel((x, y))
                    c = tints[i]
                    tinted.putpixel((x, y), (p[0] * c[0] // 255, p[1] * c[1] // 255, p[2] * c[2] // 255, p[3]))
            sheet.alpha_composite(tinted.resize((64, 64), Image.NEAREST), (10 + i * 90, 10 + f * 70))
    path = os.path.join(g.OUT, "review-o5.png")
    sheet.save(path)
    print(path, len(ms), "models")
