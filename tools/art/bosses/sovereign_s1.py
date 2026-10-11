"""Gelatinous Sovereign redesign, session 1 (take 2): three directions, each in both of its forms.

The brief (2026-10-11), after the drowned-king take was rejected:
- two forms: (1) normal: big and jumpy; (2) compressed: small, dense, toxic and angry;
- the vanilla slime, buff and mutated;
- visibly radioactive;
- a large crown.

Every direction is built from the vanilla slime's own parts, scaled up: a see-through outer cube, an opaque 6/8 core
inside it, two 2x2x2 dark eye cubes with a black pupil and a black 1x1x1 mouth standing half a pixel proud of the
core's face. The radioactive light (drawn bright here; full-bright glow bones in game) is lime-yellow.

  A  The Brute         buff: a squat, heavy body with muscle swelling over its back and two huge jelly arms planted
                       on their knuckles like a gorilla's, glowing veins down them. Compressed: the arms pulled in,
                       fists clenched at its sides.
  B  The Swollen King  mutated: bulges straining out of every face like a bag about to burst, glowing veins standing
                       out, smaller slimes budding out of it, each with its own little face. Compressed: the buds have
                       torn away (they can be the shards it splits off at 66%), leaving glowing wounds.
  C  The Crystal King  radioactive: glowing uranium-green crystals grow out of its back and shoulders, threads of light
                       to its core, crystal shards drifting in the jelly; its crown's points are crystals. Compressed:
                       crystals forced out of it all over, like spines.

Phase 2 of every direction: squeezed into a dense, nearly opaque, sickly cube about 2.5 blocks across, the face scowling
with its mouth open on the glow, light cracking through its skin, glowing acid running off it, the same big crown
jammed on askew.

Run from the repository root: python tools/art/bosses/sovereign_s1.py
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s1 as b1, volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/gelatinous_sovereign/overhaul/s1_concepts"
PALETTE = {
    "jelly": (70, 150, 40, 120),          # vanilla's green, murkier, so the radioactive light pops through it
    "jelly_toxic": (120, 170, 20, 175),   # compressed: thick, sickly yellow-green, nearly opaque
    "bud": (80, 165, 50, 150),
    "core": (60, 128, 44), "core_dark": (32, 78, 28), "face": (18, 34, 14), "pupil": (8, 8, 8),
    "glow": (170, 255, 0), "glow_hot": (232, 255, 120),
    "crystal": (150, 255, 40), "crystal_dark": (90, 190, 20),
    "crust": (66, 72, 60), "crust_dark": (42, 46, 40),
    "gold": (232, 178, 46), "gold_dark": (168, 116, 24), "gem": (170, 255, 0),
}
DIRECTIONS = {"A": "The Brute", "B": "The Swollen King", "C": "The Crystal King"}


# ---- shared parts --------------------------------------------------------------------------------------------------

def vanilla_face(g, name, centre, k, angry=False, core_mat="core"):
    """The vanilla slime's inner core (6 x 6 x 6 vanilla pixels) and face, k model units per vanilla pixel: eye cubes
    2 x 2 x 2 with a black pupil, the mouth 1 x 1 x 1, half a pixel proud of the core. Angry: a heavy brow slanting
    over each eye and the mouth torn wide open on the glow inside."""
    cx, cy, cz = centre
    s = 3 * k                                  # the core's half size
    b1.rounded_box(g, f"{name}_core", (cx, cy, cz), (6 * k, 6 * k, 6 * k), core_mat, max(1.0, k * 0.5))
    face_z = cz - s
    for side in (-1, 1):                       # eyes: vanilla x 1.25..3.25, y 4..6 of 8, z half a pixel proud
        ex = cx + side * 2.25 * k
        g.box(f"{name}_eye_{side}", (ex, cy + 1 * k, face_z - 0.25 * k), (2 * k, 2 * k, 2 * k), "face")
        g.box(f"{name}_pupil_{side}", (ex - side * 0.5 * k, cy + 0.5 * k, face_z - 1.3 * k), (k, k, 0.2 * k), "pupil")
        if angry:
            g.box(f"{name}_brow_{side}", (ex, cy + 2.4 * k, face_z - 1.2 * k), (2.6 * k, 0.8 * k, 0.8 * k), "face",
                  rotation=(0, 0, side * 22.5))
    if angry:
        g.box(f"{name}_mouth", (cx, cy - 1.6 * k, face_z - 0.3 * k), (3 * k, 1.6 * k, 1.2 * k), "pupil")
        g.box(f"{name}_mouth_glow", (cx, cy - 1.6 * k, face_z + 0.1 * k), (2.4 * k, 1.0 * k, 1.0 * k), "glow_hot")
    else:
        g.box(f"{name}_mouth", (cx + 0.5 * k, cy - 1.5 * k, face_z - 0.25 * k), (k, k, k), "pupil")


def crown(g, name, centre, r, h, tilt=0.0, crystals=False):
    """A big, chunky Minecraft crown: a thick band with a darker rim, blocky stepped points (a wide foot, a narrower
    tip) at the corners and the middle of each side, a big glowing radioactive gem in the front and smaller ones round
    the band. With crystals, the points are glowing crystals instead of gold."""
    x, y, z = centre
    c = g.group(name, (x, y, z), (0, 0, tilt))
    t = max(3.0, r * 0.18)
    for sd in (-1, 1):
        c.box(f"{name}_band_x{sd}", (x + sd * (r - t / 2), y, z), (t, h, 2 * r), "gold")
        c.box(f"{name}_band_z{sd}", (x, y, z + sd * (r - t / 2)), (2 * r - 2 * t, h, t), "gold")
        c.box(f"{name}_rim_x{sd}", (x + sd * (r - t / 2), y - h / 2 + 1, z), (t + 1.5, 2, 2 * r + 1.5), "gold_dark")
        c.box(f"{name}_rim_z{sd}", (x, y - h / 2 + 1, z + sd * (r - t / 2)), (2 * r - 2 * t, 2, t + 1.5), "gold_dark")
    spots = ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0))
    for i, (dx, dz) in enumerate(spots):
        corner = bool(dx and dz)
        px, pz = x + dx * (r - t / 2), z + dz * (r - t / 2)
        foot, tall = (t * 1.6, h * (1.0 if corner else 0.75))
        if crystals:
            c.box(f"{name}_crystal_{i}", (px, y + h / 2 + tall * 0.6, pz), (t * 1.1, tall * 1.3, t * 1.1),
                  "crystal" if i % 2 else "crystal_dark", rotation=(0, 45, 0))
            continue
        c.box(f"{name}_point_{i}", (px, y + h / 2 + tall * 0.3, pz), (foot, tall * 0.6, foot), "gold")
        c.box(f"{name}_point_tip_{i}", (px, y + h / 2 + tall * 0.75, pz), (t * 0.9, tall * 0.5, t * 0.9), "gold")
        c.box(f"{name}_point_ball_{i}", (px, y + h / 2 + tall * 1.05, pz), (t * 0.7, t * 0.7, t * 0.7), "gold_dark")
        if dz and not dx:
            c.box(f"{name}_gem_{i}", (px, y, pz + dz * (t / 2 + 0.5)), (t * 1.4, t * 1.4, 1.5), "gem")
        elif dx and not dz:
            c.box(f"{name}_gem_{i}", (px + dx * (t / 2 + 0.5), y, pz), (1.5, t, t), "gem")
    # the big front stone
    c.box(f"{name}_front_gem", (x, y + 0.5, z - r - 1), (t * 2.2, t * 2.2, 2), "glow_hot")
    return c


def bubbles(g, name, centre, spread, n, rnd, size=(2, 4)):
    """Radioactive bubbles rising through the jelly: small glowing cubes, more of them near the top."""
    cx, cy, cz = centre
    sx, sy, sz = spread
    for i in range(n):
        f = rnd.random() ** 0.6
        s = rnd.uniform(*size)
        g.box(f"{name}_{i}", (cx + rnd.uniform(-sx, sx), cy - sy + 2 * sy * f, cz + rnd.uniform(-sz, sz)), (s, s, s),
              "glow" if i % 3 else "glow_hot")


def drips(g, name, centre, half, top, n, rnd, mat="glow"):
    """Glowing goo running down the sides from `top`, ragged lengths."""
    cx, cz = centre[0], centre[2]
    for i in range(n):
        side = i % 4
        t = rnd.uniform(-half + 3, half - 3)
        x, z = ((cx + half + 0.5, cz + t), (cx - half - 0.5, cz + t), (cx + t, cz + half + 0.5), (cx + t, cz - half - 0.5))[side]
        length = rnd.uniform(4, top * 0.7)
        g.box(f"{name}_{i}", (x, top - length / 2, z), (2, length, 2), mat)


def puddle(g, name, centre, w, d, mat="glow"):
    x, _, z = centre
    g.box(f"{name}_puddle", (x, 0.5, z), (w, 1, d), "jelly")
    g.box(f"{name}_puddle_glow", (x, 0.25, z), (w * 0.7, 0.5, d * 0.7), mat)


def veins(g, name, centre, half, y0, y1, n, rnd, mat="glow"):
    """Glowing veins standing out on the skin of a cube: short bars at odd angles on its four sides."""
    cx, cz = centre[0], centre[2]
    for i in range(n):
        side = i % 4
        t = rnd.uniform(-half * 0.8, half * 0.8)
        y = rnd.uniform(y0, y1)
        pos = ((cx + half + 0.6, y, cz + t), (cx - half - 0.6, y, cz + t), (cx + t, y, cz + half + 0.6),
               (cx + t, y, cz - half - 0.6))[side]
        size = (1.2, rnd.uniform(6, 14), 1.6) if side < 2 else (1.6, rnd.uniform(6, 14), 1.2)
        rot = rnd.choice((22.5, -22.5, 45, -45, 0))
        g.box(f"{name}_{i}", pos, size, mat, rotation=(rot, 0, 0) if side < 2 else (0, 0, rot))


def angry_cube(body, rnd, k=4.6, size=40, core_mat="core"):
    """Phase 2, shared: squeezed into a dense, nearly opaque, sickly cube about 2.5 blocks across; the face scowls, the
    mouth open on the glow; light cracks through its skin; glowing acid runs off it into a puddle."""
    half = size / 2
    jelly = body.group("jelly", (0, half, 0))
    b1.rounded_box(jelly, "jelly_cube", (0, half, 0), (size, size - 2, size), "jelly_toxic", 3)
    core = body.group("core", (0, half, 0))
    vanilla_face(core, "core", (0, half, 0), k, angry=True, core_mat=core_mat)
    veins(body, "crack", (0, 0, 0), half, 6, size - 6, 14, rnd, mat="glow_hot")
    drips(body, "drip", (0, 0, 0), half, size * 0.7, 12, rnd)
    puddle(body, "acid", (0, 0, 0), size + 30, size + 28)
    return half


# ---- A: The Brute: buff, two huge jelly arms on their knuckles ----------------------------------------------------

def arm(g, name, side, shoulder, fist, thick, rnd):
    """A thick pseudopod arm: a swelling shoulder, an upper arm and forearm (beams), a big fist planted on its
    knuckles, glowing veins down it."""
    sx, sy, sz = shoulder
    fx, fy, fz = fist
    elbow = ((sx + fx) / 2 + side * thick * 0.6, (sy + fy) / 2 + thick * 0.2, (sz + fz) / 2 + 4)
    g.blob(f"{name}_shoulder", shoulder, (thick * 0.75, thick * 0.7, thick * 0.75), "jelly", layers=5, axes=("y", "z"))
    v1.beam(g, f"{name}_upper", shoulder, elbow, thick, "jelly")
    v1.beam(g, f"{name}_fore", elbow, fist, thick * 1.1, "jelly")
    b1.rounded_box(g, f"{name}_fist", fist, (thick * 1.5, thick * 1.1, thick * 1.5), "jelly", 3)
    for i in range(3):                                       # knuckles
        g.box(f"{name}_knuckle_{i}", (fx + side * 2 + (i - 1) * thick * 0.4, fy - thick * 0.45, fz - thick * 0.6),
              (thick * 0.35, thick * 0.3, thick * 0.35), "jelly")
    for i in range(3):                                       # a glowing vein running down the arm
        f = (i + 0.5) / 3
        p = tuple(shoulder[j] + (fist[j] - shoulder[j]) * f for j in range(3))
        g.box(f"{name}_vein_{i}", (p[0] + side * thick * 0.45, p[1], p[2] - thick * 0.2), (1.5, thick * 0.9, 1.5), "glow",
              rotation=(0, 0, side * 22.5))
    b1.rounded_box(g, f"{name}_core", fist, (thick * 0.6, thick * 0.5, thick * 0.6), "core_dark", 1)


def brute(model, phase):
    rnd = random.Random(10 + phase)
    body = model.group("root_body", (0, 0, 0))
    if phase == 2:
        half = angry_cube(body, rnd)
        for s in (-1, 1):                                    # the arms pulled in tight, fists clenched at its sides
            b1.rounded_box(body, f"fist_{s}", (s * (half + 5), 12, -4), (12, 14, 14), "jelly_toxic", 2)
            body.box(f"fist_{s}_vein", (s * (half + 11.2), 13, -4), (1.2, 10, 1.6), "glow_hot", rotation=(22.5, 0, 0))
        bubbles(body, "bubble", (0, half, 0), (14, 12, 14), 10, rnd, size=(1.5, 3))
        crown(body, "crown", (2, half * 2 + 6, 0), 20, 10, tilt=-22.5)
        return
    jelly = body.group("jelly", (0, 34, 0))
    b1.rounded_box(jelly, "jelly_cube", (0, 34, 2), (54, 48, 52), "jelly", 4)          # a squat, heavy body
    b1.rounded_box(jelly, "jelly_hump", (0, 54, 8), (44, 10, 36), "jelly", 3)          # muscle swelling over the back
    core = body.group("core", (0, 34, 0))
    vanilla_face(core, "core", (0, 34, 0), 5.6)
    veins(body, "vein", (0, 0, 2), 27, 16, 54, 12, rnd)
    for s in (-1, 1):
        arm(body, f"arm_{s}", s, (s * 30, 46, 0), (s * 42, 9, -18), 14, rnd)
    bubbles(body, "bubble", (0, 36, 2), (22, 20, 22), 16, rnd)
    drips(body, "drip", (0, 0, 2), 27, 40, 10, rnd)
    puddle(body, "jelly", (0, 0, 0), 92, 76)
    crown(body, "crown", (0, 66, 4), 21, 11)


# ---- B: The Swollen King: mutated, bulging, veined, budding -------------------------------------------------------

BUDS = ((-31, 44, 10, 2.2), (30, 28, 14, 1.9), (8, 60, 24, 1.7), (-24, 12, -28, 1.5))


def swollen_king(model, phase):
    rnd = random.Random(20 + phase)
    body = model.group("root_body", (0, 0, 0))
    if phase == 2:
        half = angry_cube(body, rnd)
        for i, (x, y, z, k) in enumerate(BUDS):              # where the buds tore away (the 66% shards): open wounds
            d = math.sqrt(x * x + z * z) or 1
            wx, wz = (half + 0.6) * x / d, (half + 0.6) * z / d
            body.box(f"wound_{i}_rim", (wx, 8 + (y / 60) * 26, wz), (k * 5, k * 5, k * 5), "core_dark")
            body.box(f"wound_{i}", (wx * 1.04, 8 + (y / 60) * 26, wz * 1.04), (k * 3.4, k * 3.4, k * 3.4), "glow_hot")
        crown(body, "crown", (-2, half * 2 + 6, 0), 19, 10, tilt=22.5)
        return
    jelly = body.group("jelly", (0, 30, 0))
    b1.rounded_box(jelly, "jelly_cube", (0, 30, 0), (54, 54, 54), "jelly", 4)
    # bulges straining out of every face, like a bag about to burst
    for i, (x, y, z, r) in enumerate(((0, 30, -26, 16), (-26, 34, 4, 14), (27, 26, -4, 15), (0, 36, 26, 15),
                                      (-14, 50, -12, 11), (16, 12, -22, 10))):
        jelly.blob(f"jelly_bulge_{i}", (x, y, z), (r, r * 0.9, r), "jelly", layers=5, axes=("y", "z"))
    core = body.group("core", (0, 30, 0))
    vanilla_face(core, "core", (0, 30, 0), 5.4)
    veins(body, "vein", (0, 0, 0), 27, 8, 54, 22, rnd)
    for i, (x, y, z, k) in enumerate(BUDS):                  # smaller slimes budding out of it, each with a face
        bud = body.group(f"bud_{i}", (x, y, z))
        b1.rounded_box(bud, f"bud_{i}_jelly", (x, y, z), (8 * k, 8 * k, 8 * k), "bud", 1.5)
        vanilla_face(bud, f"bud_{i}", (x, y, z), k * 0.9)
    bubbles(body, "bubble", (0, 30, 0), (22, 20, 22), 14, rnd)
    puddle(body, "jelly", (0, 0, 0), 80, 80)
    crown(body, "crown", (0, 63, 0), 20, 11)


# ---- C: The Crystal King: radioactive crystals grow out of it -----------------------------------------------------

def crystal(g, name, base, height, width, lean, mat):
    """A glowing radioactive crystal: a tall prism (turned 45 about its axis) with a narrower tip, leaning out."""
    x, y, z = base
    c = g.group(name, (x, y, z), lean)
    c.box(f"{name}_body", (x, y + height * 0.4, z), (width, height * 0.8, width), mat, rotation=(0, 45, 0))
    c.box(f"{name}_tip", (x, y + height * 0.88, z), (width * 0.55, height * 0.3, width * 0.55), "glow_hot",
          rotation=(0, 45, 0))


def crystal_king(model, phase):
    rnd = random.Random(30 + phase)
    body = model.group("root_body", (0, 0, 0))
    if phase == 2:
        half = angry_cube(body, rnd, core_mat="glow")
        # crystals forced out of it all over, like spines
        spots = [(half, 26, -6, (0, 0, -45)), (-half, 22, 8, (0, 0, 45)), (6, 30, -half, (45, 0, 0)),
                 (-8, 28, half, (-45, 0, 0)), (half - 4, 34, half - 6, (-22.5, 0, -22.5)),
                 (-half + 3, 36, -half + 6, (22.5, 0, 22.5)), (12, 2 * half - 1, 4, (0, 0, -22.5)),
                 (-10, 2 * half - 1, -6, (22.5, 0, 0)), (half, 10, 12, (0, 0, -67.5)), (-half, 12, -10, (0, 0, 67.5))]
        for i, (x, y, z, lean) in enumerate(spots):
            crystal(body, f"spine_{i}", (x, y, z), rnd.uniform(14, 22), rnd.uniform(4, 6), lean,
                    "crystal" if i % 2 else "crystal_dark")
        crown(body, "crown", (0, half * 2 + 6, 0), 20, 10, tilt=-22.5, crystals=True)
        return
    jelly = body.group("jelly", (0, 30, 0))
    b1.rounded_box(jelly, "jelly_cube", (0, 31, 0), (60, 56, 58), "jelly", 5)
    b1.rounded_box(jelly, "jelly_base", (0, 5, 0), (66, 10, 64), "jelly", 3)
    core = body.group("core", (0, 30, 0))
    vanilla_face(core, "core", (0, 30, 0), 5.6, core_mat="core")
    # crystals growing out of its back and shoulders, rooted at the core
    spots = [(-18, 52, 18, (-22.5, 0, 22.5), 30, 9), (6, 56, 22, (-22.5, 0, 0), 36, 10), (22, 48, 14, (-22.5, 0, -22.5), 26, 8),
             (-28, 36, 2, (0, 0, 45), 22, 7), (29, 30, 6, (0, 0, -45), 20, 7), (-12, 58, 4, (0, 0, 22.5), 18, 6),
             (16, 20, 28, (-45, 0, -22.5), 18, 6)]
    for i, (x, y, z, lean, h, w) in enumerate(spots):
        crystal(body, f"crystal_{i}", (x, y, z), h, w, lean, "crystal" if i % 2 else "crystal_dark")
        body.box(f"crystal_{i}_root", (x * 0.6, y * 0.8, z * 0.6), (2, 2, 2), "glow")   # light threads to the core
    for i in range(6):                                       # little crystals floating inside the jelly
        p = (rnd.uniform(-22, 22), rnd.uniform(10, 50), rnd.uniform(-22, 22))
        body.box(f"shard_{i}", p, (2, 5, 2), "glow", rotation=(0, 45, rnd.choice((22.5, -22.5))))
    bubbles(body, "bubble", (0, 34, 0), (24, 22, 24), 10, rnd)
    drips(body, "drip", (0, 0, 0), 30, 44, 10, rnd)
    puddle(body, "jelly", (0, 0, 0), 82, 80)
    crown(body, "crown", (0, 66, -4), 21, 11, crystals=True)


BUILD = {"A": brute, "B": swollen_king, "C": crystal_king}


def build(key, phase):
    model = Model(f"occultech_gelatinous_sovereign_{key.lower()}{phase}")
    BUILD[key](model, phase)
    return model


VIEWS = b1.VIEWS


def main():
    for old in OUT.glob("*"):
        if old.is_dir():
            shutil.rmtree(old)
    items = []
    for key, title in DIRECTIONS.items():
        for phase in (1, 2):
            out = OUT / f"{key}{phase}"
            out.mkdir(parents=True, exist_ok=True)
            model = build(key, phase)
            model.write_bbmodel(out / f"{model.name}.bbmodel")
            v2.run_blender(model.render_json(PALETTE), out, VIEWS)
            stats = model.stats()
            (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
            label = f"{title}, {'big' if phase == 1 else 'compressed'}"
            sheet.direction_sheet(out, f"Gelatinous Sovereign - {key} {label}", stats, out / "sheet.png")
            items.append((f"{key}{phase}", label))
            print(key, phase, stats["size_blocks"], stats["cubes"])
    sheet.compare_sheet(OUT, items, OUT / "compare.png",
                        heading="Gelatinous Sovereign - three directions, big and compressed (session 1, take 2)",
                        views=("flat_34", "sil_side", "clay_34"))
    sheet.compare_sheet(OUT, items, OUT / "compare_front.png", heading="Gelatinous Sovereign - the face and the crown",
                        views=("flat_front", "flat_side"))


if __name__ == "__main__":
    main()
