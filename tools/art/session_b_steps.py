"""Session B round 3: step marks for the Aura Talisman's step styles (replacing footprint shapes; the paw is kept).

Each mark is 16 x 16 and lives 4 frames (the game swaps the glyph as the mark ages): appear, peak, decay, last trace.
Materials (ash, ink, petals) are lit from the top-left; magic (embers, frost light, runes) is emissive.

Run: python tools/art/session_b_steps.py v1
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from palettes import RAMPS  # noqa: E402
from pixelkit import Icon, Part, _norm  # noqa: E402
from session_b import OUT, frame_sheet  # noqa: E402

FRAMES = 4


def put(icon, pts, color, alpha=255):
    for (x, y) in pts:
        if 0 <= x < icon.w and 0 <= y < icon.h:
            icon.img.putpixel((x, y), color[:3] + (alpha,))


def blob(icon, discs):
    """A lumpy material patch: the union of spheres (each pixel keeps the normal of the sphere it bulges most from)."""
    out = {}
    for (cx, cy, r) in discs:
        for (p, n) in icon.sphere(cx, cy, r).normals.items():
            if p not in out or n[2] > out[p][2]:
                out[p] = n
    return Part(out)


def petal(icon, cx, cy, angle, a, b):
    """An ellipse rotated by `angle` (degrees), domed - a petal or a leaf."""
    out = {}
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    for x, y, px, py in icon._cells():
        dx, dy = px - cx, py - cy
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        d = (u / a) ** 2 + (v / b) ** 2
        if d <= 1:
            nu, nv = u / a, v / b
            out[(x, y)] = _norm((nu * ca - nv * sa, nu * sa + nv * ca, math.sqrt(max(0.0, 1 - d)) + 0.2))
    return Part(out)


# ------------------------------------------------------------------ ember: a charred patch whose cracks cool

CRACKS = [  # pixel paths from the centre outward (crisp, hand-placed)
    [(8, 8), (9, 7), (10, 7), (11, 6), (12, 5), (13, 5)],
    [(7, 8), (7, 7), (6, 6), (6, 5), (5, 4)],
    [(7, 9), (6, 10), (5, 10), (4, 11), (3, 11)],
    [(8, 9), (9, 10), (9, 11), (10, 12), (11, 13)],
    [(10, 7), (11, 8), (12, 9)],
    [(6, 10), (6, 11), (6, 12)],
]


def ember_step(frame):
    icon = Icon(16)
    ash = RAMPS["ash"]
    em = RAMPS["ember"]
    patch = blob(icon, [(8, 8.5, 4.6), (5.5, 10, 2.6), (11, 7, 2.8), (9.5, 11.5, 2.4), (6.5, 6, 2.2)])
    icon.paint(patch, ash, outline=False, bias=-0.32, spec=False)
    reach = [6, 6, 3, 1][frame]                       # how far the glow still runs along each crack
    hot = [(em[5], em[3]), (em[4], em[3]), (em[3], em[2]), (em[2], em[1])][frame]
    for path in CRACKS:
        for i, p in enumerate(path):
            if i < reach:
                put(icon, [p], hot[0] if i < (1 if frame == 0 else 2) else hot[1])
            else:
                put(icon, [p], ash[0])                # cooled: a dark scar
    if frame == 0:                                    # little flames lick up out of the cracks
        put(icon, [(12, 4), (12, 3), (5, 3), (8, 6)], em[4])
        put(icon, [(12, 2), (5, 2)], em[3], 200)
    if frame == 1:
        put(icon, [(12, 4), (5, 3)], em[3], 220)
    if frame >= 2:                                    # smoke drifting off
        put(icon, [(9, 4 - frame), (6, 5 - frame)], ash[4], 150 if frame == 2 else 90)
    if frame <= 1:
        icon.glow(em[2], radius=1.3, strength=0.28)
    return icon


# ------------------------------------------------------------------ frost: an ice crystal blooms and melts

def frost_step(frame):
    icon = Icon(16)
    fr = RAMPS["frost"]
    # an icy sheen on the ground under the crystal
    if frame in (1, 2):
        for y in range(16):
            for x in range(16):
                if math.hypot(x + 0.5 - 8, y + 0.5 - 8) < 5.6:
                    icon.img.putpixel((x, y), fr[2][:3] + (60,))
    arm = [2, 4, 7, 6][frame]
    diag = [0, 2, 4, 3][frame]
    pts = {}
    for (ux, uy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        for d in range(1, arm + 1):
            pts[(8 + ux * d if ux >= 0 else 7 + ux * (d - 1) - 0, 8 + uy * d if uy >= 0 else 7 + uy * (d - 1))] = d
        # side branches (a V) two thirds out
        if arm >= 4:
            b = arm * 2 // 3
            for s in (-1, 1):
                for k in (1, 2):
                    x = (8 + ux * b if ux >= 0 else 7 + ux * (b - 1)) + (s * k if ux == 0 else ux * k)
                    y = (8 + uy * b if uy >= 0 else 7 + uy * (b - 1)) + (s * k if uy == 0 else uy * k)
                    pts[(x, y)] = b + k
    for (ux, uy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        for d in range(1, diag + 1):
            pts[(8 + ux * d if ux > 0 else 7 + ux * (d - 1), 8 + uy * d if uy > 0 else 7 + uy * (d - 1))] = d + 1
    for (x, y), d in pts.items():
        if frame == 3 and (x + y) % 2:               # melting: the crystal breaks up
            continue
        idx = 5 if d <= 1 else 4 if d <= arm // 2 + 1 else 3
        put(icon, [(x, y)], fr[idx], 255 if frame < 3 else 170)
    put(icon, [(7, 7), (8, 7), (7, 8), (8, 8)], fr[5])
    # a dark rim on the light ground side only (ice reads on snow and sand too)
    icon.outline(Part({p: (0, 0, 1) for p in pts if icon.img.getpixel(p)[3] == 255}), [fr[1], fr[1]], over=False)
    if frame == 2:
        icon.twinkle(12, 3, 2, fr)
    if frame == 3:
        put(icon, [(4, 12), (11, 12)], fr[3], 200)   # droplets
    return icon


# ------------------------------------------------------------------ rune: a circle flares, its rune lingers

RUNE_MAPS = {
    "eye": ["..#..", ".#.#.", "#.#.#", ".#.#.", "..#.."],
    "ascend": ["..#..", ".###.", "#.#.#", "..#..", "..#.."],
    "bind": ["#####", ".#.#.", "..#..", ".#.#.", "#####"],
}


def rune_step(frame, rune="eye"):
    icon = Icon(16)
    v = RAMPS["violet"]
    sp = RAMPS["spirit"]
    r = [4.2, 6.2, 6.6, 0][frame]
    if r:
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
                ang = math.degrees(math.atan2(y + 0.5 - 8, x + 0.5 - 8)) % 45
                if abs(d - r) < 0.6 and not (frame == 2 and 15 < ang < 30):   # frame 2: the ring breaks up
                    put(icon, [(x, y)], v[5] if frame == 0 else v[4] if frame == 1 else v[3])
    rows = RUNE_MAPS[rune]
    col = [sp[5], sp[4], sp[3], v[3]][frame]
    alpha = [255, 255, 255, 170][frame]
    put(icon, [(5 + x, 5 + y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "#"], col, alpha)
    if frame == 1:
        put(icon, [(8, 1), (8, 14), (1, 8), (14, 8)], v[4])   # four marks outside the circle
    if frame == 3:
        put(icon, [(4, 3), (11, 2), (12, 6)], sp[4], 180)    # motes rising
    if frame <= 1:
        icon.glow(v[4], radius=1.6, strength=0.35)
    return icon


# ------------------------------------------------------------------ ink: a glossy splash whose tendrils curl, then dries

def ink_step(frame):
    """A flat, glossy ink splat (arms thinning out to droplets); an eye opens in it, stares, closes; the ink dries."""
    icon = Icon(16)
    ink = RAMPS["ink"]
    arms = [1.0, 0.85, 0.8, 0.8][frame]
    discs = [(8, 8.5, 4.3)]
    for k, ang in enumerate((-60, 10, 80, 150, 215)):
        a = math.radians(ang)
        for t, r in ((4.6, 1.5), (6.0, 1.0)):
            d = t * arms + 1.2
            discs.append((8 + d * math.cos(a), 8.5 + d * math.sin(a), r * (0.6 + 0.4 * arms)))
    if frame == 0:
        discs += [(2.2, 2.8, 0.8), (13.6, 13.6, 0.8), (13.8, 4.2, 0.7)]   # droplets flung by the splash
    splat = blob(icon, discs)
    # a puddle is flat: flatten the normals so it shades like a liquid surface, not a ball
    flat = Part({p: _norm((n[0] * 0.45, n[1] * 0.45, n[2] + 0.6)) for p, n in splat.normals.items()})
    icon.paint(flat, ink, outline=False, bias=0.0 if frame < 3 else -0.25, spec=False)
    icon.outline(splat, [ink[0], ink[1]], over=False)
    if frame < 3:   # wet gloss: a hard, curved highlight
        put(icon, [(5, 6), (6, 5), (7, 5)], ink[4])
        put(icon, [(5, 7)], ink[3])
    v, cy = RAMPS["violet"], 9
    if frame == 1:   # the eye half open: a glowing slit
        put(icon, [(6, cy), (7, cy), (8, cy), (9, cy), (10, cy)], v[4])
        put(icon, [(8, cy)], v[5])
    if frame == 2:   # wide open: lids, iris, slit pupil
        put(icon, [(5, cy), (11, cy), (6, cy - 1), (7, cy - 2), (8, cy - 2), (9, cy - 2), (10, cy - 1),
                   (6, cy + 1), (7, cy + 2), (8, cy + 2), (9, cy + 2), (10, cy + 1)], v[3])
        put(icon, [(7, cy - 1), (8, cy - 1), (9, cy - 1), (6, cy), (7, cy), (9, cy), (10, cy), (7, cy + 1), (8, cy + 1), (9, cy + 1)], v[5])
        put(icon, [(8, cy - 1), (8, cy), (8, cy + 1)], ink[0])
        icon.glow(v[4], radius=1.0, strength=0.25)
    return icon


# ------------------------------------------------------------------ blossom: a flower opens where you stepped, then scatters

def blossom_step(frame):
    icon = Icon(16)
    bl = RAMPS["blossom"]
    po = RAMPS["pollen"]
    if frame == 0:   # still closed: small petals folded over the centre
        for i in range(5):
            ang = -90 + i * 72 + 36
            x, y = 8 + 1.6 * math.cos(math.radians(ang)), 8 + 1.6 * math.sin(math.radians(ang))
            icon.paint(petal(icon, x, y, ang, 2.2, 1.6), bl, bias=-0.05, outline_ramp=[bl[0], bl[1]], outline_over=False)
        put(icon, [(8, 7), (7, 8)], bl[4])
        return icon
    dist = [0, 3.0, 4.4, 0][frame]
    spin = [0, 0, 18, 0][frame]
    if frame in (1, 2):
        for i in range(5):
            ang = -90 + i * 72 + spin
            x, y = 8 + dist * math.cos(math.radians(ang)), 8 + dist * math.sin(math.radians(ang))
            part = petal(icon, x, y, ang, 2.9 if frame == 1 else 2.5, 1.9 if frame == 1 else 1.6)
            icon.paint(part, bl, bias=0.08, outline_ramp=[bl[0], bl[1]], outline_over=False)
        if frame == 1:
            icon.paint(icon.sphere(8, 8, 1.7), po, bias=0.2, outline_ramp=[po[0], po[1]], outline_over=False)
            put(icon, [(7, 7)], po[4])
        else:
            put(icon, [(8, 8), (7, 8)], po[3])
            icon.twinkle(13, 13, 2, bl)
    if frame == 3:   # three loose petals drifting, fading
        for (x, y, ang) in ((4, 5, 30), (12, 7, 120), (7, 12, 250)):
            part = petal(icon, x, y, ang, 2.0, 1.3)
            icon.paint(part, bl, bias=0.0, outline=False)
            for p in part.keys():
                c = icon.img.getpixel(p)
                icon.img.putpixel(p, c[:3] + (170,))
    return icon


STEPS = [("Ember step", ember_step), ("Frost step", frost_step), ("Rune step (ascend)", lambda f: rune_step(f, "ascend")),
         ("Rune step (bind)", lambda f: rune_step(f, "bind")), ("Ink step", ink_step), ("Blossom step", blossom_step)]


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    rows = []
    for name, make in STEPS:
        frames = []
        for f in range(FRAMES):
            icon = make(f)
            icon.save(os.path.join(OUT, name.lower().replace(" (", "_").replace(")", "").replace(" ", "_") + f"_{f}.png"))
            frames.append(icon.img)
        rows.append((name, frames))
    print(frame_sheet(rows, os.path.join(OUT, f"review-steps-{version}.png")))
