"""The Night Matriarch redesign, session 1 step 2: the Phantom Queen, take 2.

The user picked B (the Phantom Queen) over C, and asked for far more character and story (2026-10-12):
  1. incredibly large
  2. visibly injured: torn wings, bones showing
  3. half her flesh gone, a zombified phantom
  4. sculk growing over and infesting her, with sculk tendrils; bones breaking out of her forehead like a crown; two
     giant sculk tendrils (the warden's horns) at the sides of her head, flowing back like feathers
  5. an owl's tail
  6. a creepier face

So: vanilla's PhantomModel at 4.5x (a 12-block wingspan). Her right side still has its hide; on her left the flesh has
rotted away to the ribcage, and half her head is bare skull with an empty socket where a sculk light glows. Her wings
are torn: ragged trailing edges, holes, whole strips gone to the finger bones. Sculk spreads over her back and wing
roots, its sensor tendrils sprouting. Jagged bone spikes erupt from her brow, and the two warden horns sweep back from
her temples in three flat, curving blades with a glowing core. Behind, a broad owl's fan of a tail, one feather
broken to its shaft. Her face: a heavy brow, a hanging jaw full of fangs, a phantom-green eye on the flesh side.

Shown circling (9 blocks up), diving and grounded like take 1, plus her head close up. Model units: 16 = one block,
y up, her head towards -z. The blue figure is a player (1.8 blocks). Colours are blockout zones, not the palette.

Run from the repository root: python tools/art/bosses/matriarch_queen.py
"""
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s1_queen"
PALETTE = {
    "hide": (66, 78, 122), "hide_dark": (48, 56, 92), "belly": (168, 170, 158), "flesh": (92, 48, 54),
    "bone": (214, 206, 182), "membrane": (58, 62, 96), "membrane_dark": (40, 42, 70), "feather": (92, 94, 124),
    "feather_dark": (64, 66, 94), "sculk": (16, 46, 58), "sculk_glow": (50, 225, 240), "eye": (140, 255, 120),
    "hole": (14, 12, 18),
}
U = 4.5                                         # one PhantomModel pixel
ALTITUDE = {"circling": 150, "diving": 80, "grounded": 0}
L, W, H = 9 * U, 5 * U, 3 * U                   # her body: 40.5 long, 22.5 wide, 13.5 tall
FRONT = -L / 2


def beam(g, name, a, b, w, mat):
    return v1.beam(g, name, a, b, w, mat)


def blade(g, name, base, size, mat, rotation, along="y"):
    """A box standing on its base point and turned about it (spikes, tendrils, feathers)."""
    x, y, z = base
    w, h, d = size
    centre = (x, y + h / 2, z) if along == "y" else (x, y, z + d / 2)
    return g.box(name, centre, size, mat, rotation=rotation, origin=base)


# ---- the body: hide on her right, the ribcage open on her left ---------------------------------------------------

def body_parts(body):
    body.box("innards", (0, 0, 0), (12, 11, L - 3), "flesh")
    body.box("flank_right", (6.75, 0, 0), (9, H, L), "hide")
    body.box("flank_left_front", (-6.75, 0, FRONT + 6), (9, H, 12), "hide")      # what's left of her left side
    body.box("belly_right", (5.5, -H / 2 - 0.75, 0), (11, 1.5, L - 4), "belly")
    for i in range(5):                                                          # her ribs, bare
        z = -7 + i * 5.6
        body.box(f"rib_top_{i}", (-6.5, H / 2 - 1, z), (10, 2, 2), "bone")
        body.box(f"rib_side_{i}", (-11.5, 0, z), (2, H - 1, 2), "bone")
        body.box(f"rib_low_{i}", (-6.5, -H / 2 + 1, z + 1), (10, 2, 2), "bone")
    body.box("spine", (0, H / 2 + 1, 0), (3.2, 2.5, L + 4), "bone")
    for i, h in enumerate((6, 8, 7, 6, 4, 3)):
        blade(body, f"vertebra_{i}", (0, H / 2 + 2, FRONT + 4 + i * 6.6), (2.6, h, 2.6), "bone", (32, 0, 0))
    # sculk spreading over her back, its sensor tendrils sprouting
    body.box("sculk_back", (5.5, H / 2 + 0.4, -3), (10, 1, 20), "sculk")
    body.box("sculk_back_2", (-2.5, H / 2 + 0.5, 10), (9, 1, 12), "sculk")
    body.box("sculk_flank", (11.6, 1, 4), (1, 9, 16), "sculk")
    body.box("sculk_belly", (4, -H / 2 - 1.7, 6), (12, 1, 22), "sculk")
    for i, (x, z, h) in enumerate(((7, 2, 8), (2.5, 10, 11), (8, 14, 6))):          # tendrils hanging from her belly
        blade(body, f"hanging_tendril_{i}", (x, -H / 2 - 1.9, z), (1.2, h, 1.2), "sculk", (180 - 20, 0, 0))
        blade(body, f"hanging_tip_{i}", (x, -H / 2 - 1.9 - h * 0.92, z + h * 0.35), (1.6, 2, 1.6), "sculk_glow",
              (180 - 20, 0, 0))
    for i, (x, z, h, lean) in enumerate(((6, -9, 9, -10), (8.5, -7, 7, 14), (-3, 11, 8, -12), (-0.5, 13, 6, 10),
                                         (9.5, 6, 6, 0))):
        blade(body, f"tendril_{i}", (x, H / 2 + 0.8, z), (1.2, h, 1.2), "sculk", (-14, 0, lean))
        blade(body, f"tendril_tip_{i}", (x - lean * h / 60, H / 2 + 0.8 + h * 0.95, z - h * 0.24), (1.6, 2, 1.6),
              "sculk_glow", (-14, 0, lean))


# ---- the head: half hide, half bare skull; the brow, the jaw, the crown and the warden horns ----------------------------

def head_parts(head, jaw_open):
    hl, hw, hh = 5 * U, 7 * U, 3 * U                  # 22.5 long, 31.5 wide, 13.5 tall
    zc = FRONT - hl / 2
    zf = FRONT - hl                                    # her face
    head.box("head_right", (hw / 4, 0, zc), (hw / 2, hh, hl), "hide")
    head.box("skull_left", (-hw / 4, -0.5, zc + 0.5), (hw / 2, hh - 1, hl - 1), "bone")
    # the face: a scowling brow in a V over sunken eyes; the phantom's long green eye on her flesh side, a deep empty
    # socket on the bare side with the sculk's light far inside it
    for sx in (-1, 1):
        head.box(f"brow_{sx}", (sx * 8, hh / 2 - 1.2, zf + 1.6), (15, 3, 4), "hide_dark" if sx > 0 else "bone",
                 rotation=(0, 0, sx * 16))
    head.box("eye_right", (8.5, 0.6, zf - 0.3), (9, 2.2, 0.6), "eye", rotation=(0, 0, 16))
    head.box("eye_right_pit", (8.5, 0.6, zf + 0.3), (11, 4.5, 0.6), "hole", rotation=(0, 0, 16))
    head.box("socket_left", (-8.5, 0.4, zf + 0.8), (9, 6.5, 1.6), "hole")
    head.box("socket_light", (-8.5, 0.4, zf + 0.4), (1.6, 1.6, 0.6), "sculk_glow")
    head.box("nose_pit", (0, -2.0, zf - 0.1), (3, 3.5, 0.4), "hole")
    head.box("mouth", (0, -hh / 2 + 0.5, zc + 1), (hw - 6, 1, hl - 4), "hole")          # the dark roof of her mouth
    for i, (x, h) in enumerate(((-11.5, 8), (-6, 4), (5.5, 5), (11, 9))):           # long, uneven upper fangs
        blade(head, f"fang_{i}", (x, -hh / 2 + 0.5, zf + 2), (2, h, 2), "bone", (180 + 8, 0, 0))
    jaw = head.group("jaw", (0, -hh / 2, zc + hl / 2 - 3), (jaw_open, 0, 0))
    jaw.box("jaw_right", (hw / 4 - 2, -hh / 2 - 1.5, zc - 1.5), (hw / 2 - 4, 3, hl - 2), "hide_dark")
    jaw.box("jaw_left", (-hw / 4 + 2, -hh / 2 - 1.5, zc - 1.5), (hw / 2 - 4, 3, hl - 2), "bone")
    jaw.box("tongue", (0, -hh / 2 + 0.2, zc - 1), (8, 1, hl - 6), "flesh")
    for i, (x, h) in enumerate(((-10, 7), (-4, 4), (3.5, 5), (9.5, 6))):            # the lower fangs
        blade(jaw, f"low_fang_{i}", (x, -hh / 2, zf + 3), (2, h, 2), "bone", (-10, 0, 0))
    # the crown: bone broken out through her brow - a few big jagged shards and smaller splinters, uneven, leaning
    # back and out like a crown, each big shard in two pieces
    for i, (x, z, h, back, lean) in enumerate(((-11, 5, 7, 40, 34), (-6, 2.5, 15, 22, 16), (0.5, 1.5, 20, 16, -2),
                                               (6.5, 3, 12, 28, -18), (11.5, 6, 6, 44, -36), (-2.5, 7, 6, 50, 8),
                                               (3.5, 8, 5, 55, -10))):
        base = (x, hh / 2 + 0.5, zf + z)
        blade(head, f"crown_{i}", base, (3.2 if h > 10 else 2.4, h, 3.2 if h > 10 else 2.4), "bone", (back, 0, lean))
        if h > 10:
            blade(head, f"crown_{i}_spur", base, (2, h * 0.45, 2), "bone", (back - 20, 0, lean + (20 if x < 0 else -20)))
    # the warden horns: three flat blades a side, from her temples back along her head and past it, curling in at the
    # end like feathers; a glowing core down each
    for sx in (-1, 1):
        word = "left" if sx < 0 else "right"
        base = [sx * (hw / 2 + 0.5), 3.5, zf + 5]
        g = head
        for j, (seg, hgt, yaw, pitch) in enumerate(((20, 12, 16, -4), (18, 10, 4, 6), (16, 7, -10, 10))):
            g = g.group(f"horn_{word}_{j}", tuple(base), (pitch, sx * yaw, 0))
            g.box(f"horn_{word}_{j}_blade", (base[0], base[1], base[2] + seg / 2), (1.6, hgt, seg), "sculk")
            g.box(f"horn_{word}_{j}_core", (base[0] + sx * 0.9, base[1], base[2] + seg / 2 - 1),
                  (0.4, hgt * 0.4, seg - 3), "sculk_glow")
            base = [base[0], base[1], base[2] + seg - 1]


# ---- the wings: torn, holed, bare to the bone in places ----------------------------------------------------------------

def wing(parent, side, rot, elbow_rot):
    sx = side
    word = "left" if sx < 0 else "right"
    x0, y0, z0 = sx * W / 2, 3.0, FRONT + 2
    g = parent.group(f"wing_{word}", (x0, y0, z0), rot)
    chord = 9 * U
    # (strip width, membrane chord, hole (from, to) along the chord or None); a chord of 0: the strip is gone
    if sx > 0:
        inner = [(9, 40, None), (9, 34, (14, 22)), (9, 38, None)]
        outer = [(8, 36, None), (8, 24, (9, 15)), (7, 0, None), (8, 31, (18, 25)), (7, 16, None), (7, 11, None),
                 (6, 0, None), (7.5, 7, None)]
    else:
        inner = [(9, 39, None), (9, 26, None), (9, 37, (20, 30))]
        outer = [(8, 33, (12, 20)), (8, 0, None), (7, 28, None), (8, 18, None), (7, 0, None), (7, 22, (6, 13)),
                 (6, 9, None), (7.5, 0, None)]
    span = 0.0
    for part, (length, spar, strips) in enumerate(((6 * U, 4, inner), (13 * U, 3, outer))):
        if part == 1:
            g = g.group(f"wing_{word}_tip", (x0 + sx * span, y0, z0), elbow_rot)
        a = (x0 + sx * span, y0, z0)
        beam(g, f"wing_{word}_{part}_spar", a, (x0 + sx * (span + length), y0, z0), spar, "bone")
        s = span
        for j, (w, c, hole) in enumerate(strips):
            cx = x0 + sx * (s + w / 2)
            mat = "membrane" if j % 2 else "membrane_dark"
            if c and hole:
                g.box(f"wing_{word}_{part}_m{j}a", (cx, y0, z0 + hole[0] / 2), (w, 1, hole[0]), mat)
                g.box(f"wing_{word}_{part}_m{j}b", (cx, y0, z0 + (hole[1] + c) / 2), (w, 1, c - hole[1]), mat)
            elif c:
                g.box(f"wing_{word}_{part}_m{j}", (cx, y0, z0 + c / 2), (w, 1, c), mat)
            s += w
        if part == 0:
            beam(g, f"wing_{word}_inner_finger", (x0 + sx * span, y0, z0), (x0 + sx * (span + length), y0, z0 + chord * 0.85),
                 2.2, "bone")
            if sx > 0:
                g.box(f"wing_{word}_sculk", (x0 + sx * 10, y0 + 0.9, z0 + 12), (16, 1, 18), "sculk")
                g.box(f"wing_{word}_sculk_under", (x0 + sx * 13, y0 - 0.9, z0 + 18), (20, 1, 14), "sculk")
                g.box(f"wing_{word}_sculk_vein", (x0 + sx * 30, y0 - 0.9, z0 + 8), (26, 1, 2.4), "sculk")
        else:
            for k, (f, c) in enumerate(((0.3, 36), (0.62, 30), (0.95, 18))):
                beam(g, f"wing_{word}_finger_{k}", a, (x0 + sx * (span + length * f), y0, z0 + c), 2.2, "bone")
        span += length


# ---- the owl's tail -----------------------------------------------------------------------------------------------------

def tail_parts(tail):
    z0 = L / 2
    tail.box("tail_root", (3, 0, z0 + 4), (8, 8, 8), "hide")
    tail.box("tail_vertebrae", (-2.5, 0.5, z0 + 4.5), (4, 4, 9), "bone")
    for i, (yaw, length) in enumerate(((-60, 32), (-40, 40), (-20, 44), (0, 46), (20, 43), (40, 38), (60, 30))):
        g = tail.group(f"feather_{i}", (0, 0, z0 + 7), (0, yaw, 0))
        if i == 1:                                                          # broken off: the bare shaft
            g.box(f"feather_{i}_shaft", (0, 0, z0 + 7 + 13), (1.4, 1.4, 26), "bone")
            continue
        mat = "feather" if i % 2 else "feather_dark"
        g.box(f"feather_{i}_vane", (0, 0, z0 + 7 + (length - 5) / 2), (11, 1, length - 5), mat)
        g.box(f"feather_{i}_tip", (0, 0, z0 + 7 + length - 2.5), (7.5, 1, 5), mat)    # a rounded end
        g.box(f"feather_{i}_quill", (0, 0.8, z0 + 7 + length / 2 - 2), (1, 0.6, length - 6), "bone")


# ---- the poses ----------------------------------------------------------------------------------------------------------

POSES = {
    "circling": {"body": (4, 0, 16), "head": -8, "jaw": -26, "tail": -4,
                 "wing": lambda sx: ((0, 0, sx * 8), (0, -sx * 12, sx * 5))},
    "diving": {"body": (-40, 0, 0), "head": -4, "jaw": -40, "tail": 12,
               "wing": lambda sx: ((0, -sx * 60, sx * 14), (0, -sx * 28, sx * 6))},
    "grounded": {"body": (0, 0, 5), "head": -14, "jaw": -24, "tail": -2,
                 "wing": lambda sx: ((0, sx * 4, -sx * 8), (0, 0, -sx * 10))},
}


def queen(pose):
    p = POSES[pose]
    m = Model(f"matriarch_queen_{pose}")
    body = m.group("body", (0, 0, 0), p["body"])
    body_parts(body)
    head = body.group("hi_head", (0, 0, FRONT), (p["head"], 0, 0))
    head_parts(head, p["jaw"])
    tail = body.group("tail", (0, 0, L / 2), (p["tail"], 0, 0))
    tail_parts(tail)
    for sx in (-1, 1):
        wing(body, sx, *p["wing"](sx))
    lo, _ = m.bounds()
    dy = ALTITUDE[pose] - float(lo[1])
    for g in m.groups:
        g.origin[1] += dy
    for c in m.cubes:
        c.frm[1] += dy
        c.to[1] += dy
        c.origin[1] += dy
    return m


def head_only(model):
    """The head's cubes alone (the close-up renders orbit the boxes' middle)."""
    def under(c):
        g = c.group
        while g is not None:
            if g.name == "hi_head":
                return True
            g = g.parent
        return False
    return [b for b, c in zip(model.render_json(v2.PALETTE), model.cubes) if under(c)]


def views(pose, model):
    lo, hi = model.bounds()
    mid = float(lo[1] + hi[1]) / 32
    if pose == "circling":
        return [{"name": "sil_below", "mode": "silhouette", "camera": "persp", "yaw": 25, "height": 1.62, "dist": 9,
                 "target_z": mid, "lens": 30},
                {"name": "flat_below", "mode": "flat", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 8,
                 "target_z": mid, "lens": 30},
                {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": mid + 5, "dist": 15,
                 "target_z": mid - 0.6}]
    if pose == "diving":
        return [{"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
                {"name": "flat_below", "mode": "flat", "camera": "persp", "yaw": -20, "height": 1.62, "dist": 8,
                 "target_z": mid, "lens": 30},
                {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": mid + 3, "dist": 14,
                 "target_z": mid - 0.3}]
    return [{"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
            {"name": "flat_eye", "mode": "flat", "camera": "persp", "yaw": 15, "height": 1.62, "dist": 11,
             "target_z": 1.0},
            {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -35, "height": 6, "dist": 15, "target_z": 0.8}]


FACE_VIEWS = [{"name": "face_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 1.0, "dist": 6,
               "target_z": 0.9, "player": False},
              {"name": "face_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 2.2, "dist": 6,
               "target_z": 0.9, "player": False},
              {"name": "face_side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 1.6, "dist": 6.5,
               "target_z": 1.0, "player": False}]
LABELS = {"sil_below": "from below, silhouette (a player's eye)", "flat_below": "from below (a player's eye)",
          "flat_34": "three-quarter", "sil_side": "side, silhouette", "flat_eye": "a player's eye", "clay_34": "clay",
          "face_front": "her face", "face_34": "her head, three-quarter", "face_side": "her head, side"}
ROWS = ("circling", "diving", "grounded", "face")


def make_sheet(stats):
    tw, th, pad, top = 460, 350, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + len(ROWS) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"Night Matriarch: the Phantom Queen, take 2  -  span {stats['span']} blocks, "
                       f"{stats['length']} long", font=sheet._font(26), fill=sheet.INK)
    for r, row in enumerate(ROWS):
        names = [v["name"] for v in (FACE_VIEWS if row == "face" else views(row, queen(row)))]
        for c, name in enumerate(names):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / row / f"{name}.png", tw, th), (x, y))
            label = LABELS[name] if row == "face" else f"{row}: {LABELS[name]}"
            dr.text((x, y + th + 6), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "phantom_queen_take2.png")


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    stats = {}
    for pose in ("circling", "diving", "grounded"):
        model = queen(pose)
        if pose == "circling":
            lo, hi = model.bounds()
            stats = {"span": round(float(hi[0] - lo[0]) / 16, 1), "length": round(float(hi[2] - lo[2]) / 16, 1),
                     "cubes": len(model.cubes)}
        v2.run_blender(model.render_json(v2.PALETTE), OUT / pose, views(pose, model))
    v2.run_blender(head_only(queen("grounded")), OUT / "face", FACE_VIEWS)
    make_sheet(stats)
    print(stats)


if __name__ == "__main__":
    main()
