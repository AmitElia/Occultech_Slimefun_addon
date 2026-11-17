"""Turntable GIFs of the held 3D weapon models (session g): each model stood upright, turned a full circle, its glowing
parts (light_emission) blooming in the weapon's colour and motes drifting off it (embers, souls, bubbles, blood).

    python tools/art/preview_held_turntables.py [key ...]      -> docs/art/previews/<key>-held-3d.gif
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import render3d  # noqa: E402
import session_g as g  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "art", "previews")
W, H = 480, 560
SS = 2
FRAMES = 96


def undiagonal(m):
    """Stands a model laid on a sprite's diagonal (session_g.diagonal) back upright."""
    for e in m.elements:
        r = e.get("rotation")
        if r and r["axis"] == "z" and list(r["origin"]) == [8, 8, 8] and abs(r["angle"]) == 45:
            del e["rotation"]
    return m


def hand_frame(p):
    """Models built in the hand's frame (+y ahead, +z up): turn +z to up."""
    x, y, z = p
    return x, z, 16 - y


def lance_stretch(p):
    """Vanilla draws a spear 1.7x in its plane and 0.85x deep; the model is built twice as deep to come out round."""
    x, y, z = p
    return 8 + (x - 8) * 1.7, 8 + (y - 8) * 1.7, 8 + (z - 8) * 0.85


# key: (model, pre-transform, pitch, bloom colour, motes)
WEAPONS = {
    "wyrmbreath": (lambda: g.wyrmbreath_held(True), None, 18, (255, 140, 60), "embers"),
    "guardians_gaze": (lambda: g.guardians_gaze_held(True), None, 18, (90, 230, 215), "bubbles"),
    "soulfire_censer": (lambda: g.soulfire_censer_held(True), hand_frame, 16, (70, 200, 255), "souls"),
    "abyssal_anchor": (lambda: undiagonal(g.abyssal_anchor_held()), None, 16, (90, 230, 215), "bubbles"),
    "dreadlance": (lambda: undiagonal(g.dreadlance_held()), lance_stretch, 14, (150, 90, 255), "motes"),
    "frenzy_cleaver": (lambda: undiagonal(g.frenzy_cleaver_held()), None, 16, (200, 30, 30), "blood"),
    "bone_scepter": (lambda: undiagonal(g.bone_scepter_held()), None, 16, (120, 255, 90), "wisps"),
    "lichs_grimoire": (g.lichs_grimoire_held, hand_frame, 38, (80, 200, 255), "lich_souls"),
}

MOTES = {   # colour ramp (birth -> death), drift (vx, vy px/frame), size, where they're born
    "embers": ([(255, 235, 150), (255, 80, 10)], (0, -1.6), 3, "glow"),
    "bubbles": ([(200, 255, 250), (60, 160, 170)], (0, -1.2), 3, "glow"),
    "souls": ([(190, 250, 255), (40, 120, 200)], (0, -1.3), 3, "glow"),
    "motes": ([(230, 200, 255), (90, 40, 170)], (0, -0.8), 2, "glow"),
    "blood": ([(200, 20, 20), (90, 0, 10)], (0, 1.8), 3, "blade"),
    "wisps": ([(220, 255, 180), (60, 170, 40)], (0, -1.2), 3, "glow"),
    "lich_souls": ([(190, 240, 255), (50, 120, 210)], (0, -1.3), 3, "glow"),
}


def rotp(p, r):
    return render3d.rot(p, r) if r else p


def corners(e):
    f, t = e["from"], e["to"]
    return [(x, y, z) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]


def render(model, frame, yaw, pitch, s, size, center, pre, only_glow=False):
    """render3d.render with a pre-transform applied to every point after the element's own rotation."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    pre = pre or (lambda p: p)

    def view(p):
        x, y, z = (p[i] - center[i] for i in range(3))
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return x, y, z

    quads = []
    for e in model.elements:
        if only_glow and not e.get("light_emission"):
            continue
        r = e.get("rotation")
        for d, face in e["faces"].items():
            o, du, dv = render3d.face_frame(d, e["from"], e["to"])
            # the face's real normal after both transforms: from three of its corners
            p0 = view(pre(rotp(o, r)))
            p1 = view(pre(rotp(tuple(o[k] + du[k] for k in range(3)), r)))
            p2 = view(pre(rotp(tuple(o[k] + dv[k] for k in range(3)), r)))
            a = [p1[k] - p0[k] for k in range(3)]
            b = [p2[k] - p0[k] for k in range(3)]
            nz = a[0] * b[1] - a[1] * b[0]
            # face_frame's u x v points inward for MC uv order, so the face looks at us when the cross's z is negative
            if nz >= -1e-9:
                continue
            img = model.frame(face["texture"].lstrip("#"), frame).convert("RGBA")
            u0, v0, u1, v1 = face["uv"]
            kx = img.width / 16
            nu = max(1, math.ceil(abs(u1 - u0) * kx - 1e-6))
            nv = max(1, math.ceil(abs(v1 - v0) * img.width / 16 - 1e-6))
            light = 1.0 if (not e.get("shade", True) or e.get("light_emission")) else render3d.SHADE[d]
            for i in range(nu):
                for j in range(nv):
                    uu = u0 + (u1 - u0) * (i + 0.5) / nu
                    vv = v0 + (v1 - v0) * (j + 0.5) / nv
                    c = img.getpixel((min(img.width - 1, int(uu * img.width / 16)), min(img.height - 1, int(vv * img.height / 16))))
                    if c[3] < 128:
                        continue
                    pts = []
                    for (aa, bb) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                        p = tuple(o[k] + du[k] * aa / nu + dv[k] * bb / nv for k in range(3))
                        pts.append(view(pre(rotp(p, r))))
                    depth = sum(q[2] for q in pts) / 4
                    col = tuple(int(c[k] * light) for k in range(3)) + (255,)
                    quads.append((depth, [(size[0] / 2 + q[0] * s, size[1] / 2 - q[1] * s) for q in pts], col))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(out)
    for depth, pts, col in sorted(quads, key=lambda q: q[0]):
        dr.polygon(pts, fill=col, outline=col)
    return out


def fit(model, pre, pitch):
    """Rotation axis, scale and centre that keep the whole turn in frame."""
    pre = pre or (lambda p: p)
    pts = [pre(rotp(c, e.get("rotation"))) for e in model.elements for c in corners(e)]
    xs, ys, zs = zip(*pts)
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    r = max(math.hypot(x - cx, z - cz) for x, _, z in pts)
    y0, y1 = min(ys), max(ys)
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    tall = (y1 - y0) * cp + 2 * r * sp
    s = min((W - 90) / (2 * r), (H - 150) / tall)
    return (cx, (y0 + y1) / 2, cz), s, tall * s


def backdrop(tint):
    top, bottom = (24, 16, 30), (10, 8, 14)
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line((0, y, W, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    halo = Image.new("L", (W, H))
    ImageDraw.Draw(halo).ellipse((W / 2 - 170, 70, W / 2 + 170, 410), fill=60)
    halo = halo.filter(ImageFilter.GaussianBlur(70))
    return Image.composite(Image.new("RGB", (W, H), tuple(int(c * 0.45) for c in tint)), bg, halo)


def turntable(key):
    make, pre, pitch, tint, mote_kind = WEAPONS[key]
    model = make()
    center, s, tall = fit(model, pre, pitch)
    floor = H / 2 + tall / 2 + 26
    has_glow = any(e.get("light_emission") for e in model.elements)
    ramp, drift, msize, origin = MOTES[mote_kind]
    bg = backdrop(tint)
    rng = random.Random(hash(key) & 0xffff)
    motes, frames = [], []
    for i in range(FRAMES):
        yaw = 360 * i / FRAMES
        bob = math.sin(i / FRAMES * math.tau * 2) * 6
        size = (W * SS, H * SS)
        body = render(model, i // 3, yaw, pitch, s * SS, size, center, pre).resize((W, H), Image.LANCZOS)
        glow = render(model, i // 3, yaw, pitch, s * SS, size, center, pre, only_glow=True).resize((W, H), Image.LANCZOS) \
            if has_glow else Image.new("RGBA", (W, H))

        f = bg.copy()
        sh = Image.new("L", (W, H))
        r = 70 - bob * 1.5
        ImageDraw.Draw(sh).ellipse((W / 2 - r, floor - r * 0.18, W / 2 + r, floor + r * 0.18), fill=190)
        f = Image.composite(Image.new("RGB", (W, H), (6, 4, 8)), f, sh.filter(ImageFilter.GaussianBlur(10)))

        # motes are born on the glowing parts (or anywhere on the model) and drift away
        src = glow if (origin == "glow" and has_glow) else body
        alpha = src.split()[3]
        bbox = alpha.getbbox()
        if bbox and rng.random() < 0.8:
            for _ in range(8):
                x, y = rng.uniform(bbox[0], bbox[2]), rng.uniform(bbox[1], bbox[3])
                if alpha.getpixel((int(x), int(y))) > 128:
                    motes.append([x, y - bob, rng.gauss(0, 0.35), drift[1] * rng.uniform(0.6, 1.2), 0, rng.randint(24, 46),
                                  msize + rng.choice((-1, 0, 0, 1))])
                    break
        mote_layer = Image.new("RGBA", (W, H))
        md = ImageDraw.Draw(mote_layer)
        alive = []
        for m in motes:
            m[0] += m[2] + math.sin((m[4] + m[1]) * 0.15) * (0.4 if drift[1] < 0 else 0)
            m[1] += m[3]
            m[3] = m[3] * 0.985 if drift[1] < 0 else m[3] + 0.08     # blood falls, everything else floats up
            m[4] += 1
            if m[4] >= m[5] or m[1] > floor:
                continue
            alive.append(m)
            t = m[4] / m[5]
            col = tuple(int(a + (b - a) * t) for a, b in zip(*ramp)) + (int(255 * (1 - t * t)),)
            sz = m[6] * (1 - t * 0.4)
            md.rectangle((m[0] - sz / 2, m[1] - sz / 2, m[0] + sz / 2, m[1] + sz / 2), fill=col)
        motes = alive

        f.paste(body.convert("RGB"), (0, int(-bob)), body)
        f.paste(mote_layer.convert("RGB"), (0, 0), mote_layer)
        glow_full = Image.new("RGBA", (W, H))
        glow_full.alpha_composite(glow, (0, int(-bob)))
        if origin == "glow":
            glow_full.alpha_composite(mote_layer)
        bloom = glow_full.convert("RGB")
        flicker = 0.85 + 0.15 * math.sin(i * 1.7) * math.sin(i * 0.63)
        wide = bloom.filter(ImageFilter.GaussianBlur(34)).point(lambda v: min(255, int(v * 0.75 * flicker)))
        tight = bloom.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.16))
        f = ImageChops.add(f, ImageChops.multiply(wide, Image.new("RGB", (W, H), tint)))
        f = ImageChops.add(f, ImageChops.multiply(tight, Image.new("RGB", (W, H), tuple(min(255, c + 60) for c in tint))))
        frames.append(f)

    sample = Image.new("RGB", (W, H * 4))
    for k in range(4):
        sample.paste(frames[k * FRAMES // 4], (0, H * k))
    pal = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    out = os.path.join(OUT, f"{key.replace('_', '-')}-held-3d.gif")
    q[0].save(out, save_all=True, append_images=q[1:], duration=40, loop=0, optimize=False, disposal=1)
    print(out, os.path.getsize(out) // 1024, "KB")
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for key in sys.argv[1:] or [k for k in WEAPONS if k != "wyrmbreath"]:
        turntable(key)
