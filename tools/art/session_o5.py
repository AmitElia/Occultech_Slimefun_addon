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


if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] != "bursts"):
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


# ================================================================== phase 2: hit bursts (frame-exact)
# A burst plays once, from its first frame, so its frames are separate models the server steps through (it sets the
# item's custom-model-data number; the item definition picks the frame) - not an animated texture on the global clock.
# Shown as a sprite that always faces the viewer. 32 px, light tones with a white-hot core, tinted per use.

BN = 32
BC = 16.0
BURST_FRAMES = 5


def bblank():
    return Image.new("RGBA", (BN, BN), (0, 0, 0, 0))


def bput(img, x, y, c, a=255):
    x, y = int(x), int(y)
    if 0 <= x < BN and 0 <= y < BN:
        img.putpixel((x, y), rgba(c, a))


def burst_slash(f):
    """A slash: a crescent sweeping from the upper left down to the lower right - drawn on, then full and bright, then
    thinning and breaking into sparks."""
    img = bblank()
    sweep = [0.45, 1.0, 1.0, 1.0, 1.0][f]
    thick = [2.2, 3.2, 2.6, 1.6, 0.0][f]
    for i in range(160):
        t = i / 159
        if t > sweep:
            break
        a = math.radians(200 + t * 150)
        r = 12.5
        x, y = BC + r * math.cos(a), BC + 3 + r * math.sin(a) * 0.8
        w = thick * math.sin(math.pi * t)                     # thick in the middle, pointed at the ends
        for k in range(-3, 4):
            if abs(k) <= w:
                bput(img, x - k * math.cos(a), y - k * math.sin(a) * 0.8, GREY[5] if abs(k) < w * 0.5 else GREY[4])
    if f >= 2:
        rnd = random.Random(7 + f)
        for _ in range(6 + f * 2):
            t = rnd.random()
            a = math.radians(200 + t * 150)
            r = 12.5 + rnd.uniform(-1, 1) + (f - 2) * 2.5
            bput(img, BC + r * math.cos(a), BC + 3 + r * math.sin(a) * 0.8, GREY[4] if f < 4 else GREY[3])
    return img


def burst_impact(f):
    """An impact: a white-hot point, a star of rays, a ring racing out, sparks scattering."""
    img = bblank()
    core = [2.5, 3.5, 2.5, 1.5, 0][f]
    for y in range(BN):
        for x in range(BN):
            d = math.hypot(x + 0.5 - BC, y + 0.5 - BC)
            if d < core:
                bput(img, x, y, GREY[5])
    ray_len = [5, 11, 14, 9, 0][f]
    for k in range(8):
        a = math.radians(k * 45 + 22.5 * (k % 2))
        length = ray_len * (1.0 if k % 2 == 0 else 0.6)
        for r in range(int(core), int(length)):
            bput(img, BC + r * math.cos(a), BC + r * math.sin(a), GREY[5] if r < length * 0.5 else GREY[4])
    ring = [0, 0, 9.5, 13.0, 15.0][f]
    if ring:
        for i in range(96):
            a = math.radians(i * 3.75)
            bput(img, BC + ring * math.cos(a), BC + ring * math.sin(a), GREY[4] if f < 4 else GREY[3])
    if f >= 3:
        rnd = random.Random(f)
        for _ in range(10):
            a = rnd.uniform(0, math.tau)
            r = rnd.uniform(6, 15)
            bput(img, BC + r * math.cos(a), BC + r * math.sin(a), GREY[3])
    return img


def burst_crackle(f):
    """A crackle of plasma round whoever was struck: jagged forks out from the middle, new forks each frame, growing
    then dying back."""
    img = bblank()
    rnd = random.Random(11 + f * 5)
    reach = [6, 11, 14, 11, 6][f]
    for k in range(5):
        a = rnd.uniform(0, math.tau)
        x, y = BC, BC
        for step in range(reach):
            a += rnd.uniform(-0.7, 0.7)
            x += math.cos(a)
            y += math.sin(a)
            bput(img, x, y, GREY[5] if step < reach * 0.5 else GREY[4])
            if step == reach // 2 and rnd.random() < 0.6:   # a small fork
                fx, fy, fa = x, y, a + rnd.choice((-1, 1)) * 0.9
                for _ in range(3):
                    fx += math.cos(fa)
                    fy += math.sin(fa)
                    bput(img, fx, fy, GREY[4])
    for y in range(BN):                                         # the bright heart
        for x in range(BN):
            if math.hypot(x + 0.5 - BC, y + 0.5 - BC) < [2.0, 2.5, 2.0, 1.5, 1.0][f]:
                bput(img, x, y, GREY[5])
    return img


def burst_soul(f):
    """A soul set free: a bright orb, a ring blooming round it, wisps rising and fading."""
    img = bblank()
    orb = [4.0, 3.0, 2.0, 0, 0][f]
    for y in range(BN):
        for x in range(BN):
            d = math.hypot(x + 0.5 - BC, y + 0.5 - BC)
            if d < orb:
                bput(img, x, y, GREY[5] if d < orb * 0.6 else GREY[4])
    ring = [0, 7.0, 10.5, 13.0, 0][f]
    if ring:
        for i in range(80):
            a = math.radians(i * 4.5)
            bput(img, BC + ring * math.cos(a), BC + ring * math.sin(a) * 0.55 + 4, GREY[4] if f < 3 else GREY[3])
    if f >= 1:
        for k, wx in enumerate((-6, -2, 3, 7)):                 # wisps rising
            top = BC - 2 - f * 3 - (k % 2) * 2
            for j in range(4):
                bput(img, BC + wx + math.sin((top + j) * 0.9) * 0.8, top + j, GREY[5] if j == 0 else GREY[4] if j < 2 else GREY[3])
    return img


def burst_splash(f):
    """A splash bursting in the air: a blob, then droplets flying out and falling."""
    img = bblank()
    blob = [4.5, 2.5, 0, 0, 0][f]
    for y in range(BN):
        for x in range(BN):
            if math.hypot(x + 0.5 - BC, y + 0.5 - BC) < blob:
                bput(img, x, y, GREY[5] if y < BC else GREY[4])
    if f >= 1:
        for k in range(10):
            a = math.radians(k * 36 + 10)
            r = [0, 6, 10, 13, 14][f]
            fall = [0, 0, 1, 3, 6][f] * (1 if math.sin(a) > -0.5 else 0.5)
            x, y = BC + r * math.cos(a), BC + r * math.sin(a) * 0.8 + fall
            size = 1 if f >= 3 else 2
            for dx in range(size):
                for dy in range(size):
                    bput(img, x + dx, y + dy, GREY[5] if f < 3 else GREY[4])
    return img


BURSTS = {"slash": burst_slash, "impact": burst_impact, "crackle": burst_crackle, "soul": burst_soul, "splash": burst_splash}


def sprite(key, image):
    """A flat sprite (both faces) the plugin shows facing the viewer: glowing, unshaded, tinted."""
    m = g.Model(key)
    m.part = True
    t = m.texture("sprite", image)
    e = m.box((0, 0, 8), (16, 16, 8), {"north": (t, [16, 0, 0, 16]), "south": (t, [0, 0, 16, 16])}, shade=False, light=15)
    for face in e["faces"].values():
        face["tintindex"] = 0
    m.tinted = True
    return m


def burst_models():
    return [sprite(f"air_burst_{name}_f{i}", make(i)) for name, make in BURSTS.items() for i in range(BURST_FRAMES)]


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "bursts":
    ms = burst_models()
    for m in ms:
        save(m)
    sheet = Image.new("RGBA", (BURST_FRAMES * 100 + 10, len(BURSTS) * 100 + 10), (34, 32, 40, 255))
    for i, m in enumerate(ms):
        row, col = divmod(i, BURST_FRAMES)
        sheet.alpha_composite(m.textures["sprite"].resize((96, 96), Image.NEAREST), (10 + col * 100, 10 + row * 100))
    path = os.path.join(g.OUT, "review-o5-bursts.png")
    sheet.save(path)
    print(path, len(ms), "models")
