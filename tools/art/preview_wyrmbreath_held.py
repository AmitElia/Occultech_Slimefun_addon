"""Wyrmbreath's 3D held model as a turntable GIF: the session-g scepter (true 3D through render3d), its animated
dragon-fire orb glowing (the orb is light_emission 15 in game), embers drifting up from it.

    python tools/art/preview_wyrmbreath_held.py [out.gif]
"""
import copy
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import render3d  # noqa: E402
import session_g  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 480, 560
SS = 2                    # supersampling
SCALE = 24
CENTER = (8, 6.6, 8)
PITCH = 18
FRAMES = 96               # one full turn, 40 ms a frame
ORB = (8, 13.4, 8)        # the orb's centre in model space
BG_TOP, BG_BOTTOM = (30, 18, 34), (12, 8, 16)


def view(p, yaw, pitch):
    """render3d's camera: the model point p in screen pixels (supersampled)."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    x, y, z = (p[i] - CENTER[i] for i in range(3))
    x, z = x * cy - z * sy, x * sy + z * cy
    y, z = y * cp - z * sp, y * sp + z * cp
    return W * SS / 2 + x * SCALE * SS, H * SS / 2 - y * SCALE * SS


def backdrop():
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line((0, y, W, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)))
    halo = Image.new("L", (W, H))
    ImageDraw.Draw(halo).ellipse((W / 2 - 170, 70, W / 2 + 170, 410), fill=70)
    halo = halo.filter(ImageFilter.GaussianBlur(70))
    bg = Image.composite(Image.new("RGB", (W, H), (120, 46, 22)), bg, halo)
    return bg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "art", "previews", "wyrmbreath-held-3d.gif")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    model = session_g.wyrmbreath_held(True)
    glowing = copy.copy(model)
    glowing.elements = [e for e in model.elements if e.get("light_emission")]
    bg = backdrop()
    rng = random.Random(11)
    embers = []
    frames = []
    for i in range(FRAMES):
        yaw = 360 * i / FRAMES
        bob = math.sin(i / FRAMES * math.tau * 2) * 6        # a slow float, two bobs a turn
        orb_frame = i // 3
        size = (W * SS, H * SS)
        body = render3d.render(model, frame=orb_frame, yaw=yaw, pitch=PITCH, s=SCALE * SS, size=size, bg=(0, 0, 0, 0),
                               center=CENTER)
        glow = render3d.render(glowing, frame=orb_frame, yaw=yaw, pitch=PITCH, s=SCALE * SS, size=size, bg=(0, 0, 0, 0),
                               center=CENTER)
        body = body.resize((W, H), Image.LANCZOS)
        glow = glow.resize((W, H), Image.LANCZOS)

        f = bg.copy()
        # a soft shadow on the "floor", breathing with the bob
        sh = Image.new("L", (W, H))
        r = 70 - bob * 1.5
        ImageDraw.Draw(sh).ellipse((W / 2 - r, 492 - r * 0.18, W / 2 + r, 492 + r * 0.18), fill=190)
        f = Image.composite(Image.new("RGB", (W, H), (6, 4, 8)), f, sh.filter(ImageFilter.GaussianBlur(10)))

        # embers: born at the orb, drifting up and out, flickering, cooling from white-gold to red
        ox, oy = view(ORB, yaw, PITCH)
        ox, oy = ox / SS, oy / SS - bob
        flicker = 0.85 + 0.15 * math.sin(i * 1.7) * math.sin(i * 0.63)
        for _ in range(2 if rng.random() < 0.6 else 1):
            embers.append([ox + rng.gauss(0, 14), oy + rng.gauss(0, 10), rng.gauss(0, 0.5), -rng.uniform(1.0, 2.2), 0,
                           rng.randint(26, 50), rng.choice((2, 3, 3, 4))])
        ember_layer = Image.new("RGBA", (W, H))
        ed = ImageDraw.Draw(ember_layer)
        alive = []
        for e in embers:
            e[0] += e[2] + math.sin((e[4] + e[1]) * 0.15) * 0.4
            e[1] += e[3]
            e[3] *= 0.985
            e[4] += 1
            if e[4] >= e[5]:
                continue
            alive.append(e)
            t = e[4] / e[5]
            col = (255, int(235 - 170 * t), int(150 - 140 * t), int(255 * (1 - t * t)))
            s = e[6] * (1 - t * 0.5)
            ed.rectangle((e[0] - s / 2, e[1] - s / 2, e[0] + s / 2, e[1] + s / 2), fill=col)
        embers = alive

        # the model, floating
        f.paste(body.convert("RGB"), (0, int(-bob)), body)
        glow_full = Image.new("RGBA", (W, H))
        glow_full.alpha_composite(glow, (0, int(-bob)))
        glow_full.alpha_composite(ember_layer)
        f.paste(ember_layer.convert("RGB"), (0, 0), ember_layer)

        # bloom: the orb and embers light the air around them
        bloom = glow_full.convert("RGB")
        wide = bloom.filter(ImageFilter.GaussianBlur(34)).point(lambda v: min(255, int(v * 0.75 * flicker)))
        tight = bloom.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.16))
        warm = Image.new("RGB", (W, H), (255, 140, 60))
        f = ImageChops.add(f, ImageChops.multiply(wide, warm))
        f = ImageChops.add(f, ImageChops.multiply(tight, Image.new("RGB", (W, H), (255, 200, 120))))
        frames.append(f)

    sample = Image.new("RGB", (W, H * 4))
    for k in range(4):
        sample.paste(frames[k * FRAMES // 4], (0, H * k))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=40, loop=0, optimize=False, disposal=1)
    print(out, len(q), "frames", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
