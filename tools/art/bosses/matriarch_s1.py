"""The Night Matriarch redesign, session 1 step 3: the full blockout (the user skipped the face study).

Take 2 of the Phantom Queen (matriarch_queen.py) with the user's changes (2026-10-12):
  1. the sculk infestation is mostly texture (session 5): only a few small sensor tendrils on her back stay modelled
  2. the tendrils round her head look like the warden's horns, smaller and many: a ruff of them round her face like an
     owl's feathers
  3. the bones on her head stand in several rows and arch backwards
  4. a less scary face, close to vanilla's phantom: the phantom's head and its green eyes, no jaw or fangs
  5. the torn wings are painted (cut-out holes in the texture, like the chains), so the wings are whole panels

Kept from take 2: vanilla's PhantomModel at 4.5x (about an 11.5-block wingspan), the left flank rotted open to the
ribs (her right side keeps its hide; half her head becomes bare skull in the texture), bone spars along the wings'
leading edges, the owl's tail.

Shown gliding (level, wings spread, 9 blocks up) from below, the side, above, the front and three-quarter, grounded,
and her head close up. Model units: 16 = one block, y up, her head towards -z. The blue figure is a player (1.8 blocks).
Colours are blockout zones, not the palette.

Run from the repository root: python tools/art/bosses/matriarch_s1.py
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as v2, volley_s1 as v1  # noqa: E402

OUT = ROOT / "docs/art/bosses/night_matriarch/overhaul/s1_blockout"
PALETTE = {
    "hide": (66, 78, 122), "hide_dark": (48, 56, 92), "belly": (168, 170, 158), "flesh": (92, 48, 54),
    "bone": (214, 206, 182), "membrane": (58, 62, 96), "feather": (92, 94, 124), "feather_dark": (64, 66, 94),
    "sculk": (16, 46, 58), "sculk_glow": (50, 225, 240), "eye": (140, 255, 120),
}
U = 4.5                                         # one PhantomModel pixel
ALTITUDE = {"glide": 150, "grounded": 0}
L, W, H = 9 * U, 5 * U, 3 * U                   # her body: 40.5 long, 22.5 wide, 13.5 tall
FRONT = -L / 2
HL, HW, HH = 5 * U, 7 * U, 3 * U                # her head: 22.5 long, 31.5 wide, 13.5 tall
ZF = FRONT - HL                                 # her face


def blade(g, name, base, size, mat, rotation=(0, 0, 0)):
    """A box standing on its base point (along +y) and turned about it."""
    x, y, z = base
    return g.box(name, (x, y + size[1] / 2, z), size, mat, rotation=rotation, origin=base)


# ---- the body: hide on her right, her left rotted open to the ribs ------------------------------------------------------

def body_parts(body):
    body.box("innards", (0, 0, 0), (12, 11, L - 3), "flesh")
    body.box("flank_right", (6.75, 0, 0), (9, H, L), "hide")
    body.box("flank_left_front", (-6.75, 0, FRONT + 6), (9, H, 12), "hide")
    body.box("belly_right", (5.5, -H / 2 - 0.75, 0), (11, 1.5, L - 4), "belly")
    for i in range(5):
        z = -7 + i * 5.6
        body.box(f"rib_top_{i}", (-6.5, H / 2 - 1, z), (10, 2, 2), "bone")
        body.box(f"rib_side_{i}", (-11.5, 0, z), (2, H - 1, 2), "bone")
        body.box(f"rib_low_{i}", (-6.5, -H / 2 + 1, z + 1), (10, 2, 2), "bone")
    body.box("spine", (0, H / 2 + 1, 0), (3.2, 2.5, L + 4), "bone")
    for i, h in enumerate((5, 7, 6, 5, 4)):
        blade(body, f"vertebra_{i}", (0, H / 2 + 2, FRONT + 6 + i * 7), (2.6, h, 2.6), "bone", (22.5, 0, 0))
    # a few small sculk sensor tendrils on her back (the rest of the sculk is painted)
    for i, (x, z, h) in enumerate(((6, -8, 6), (8.5, -5, 5), (-3, 12, 5))):
        blade(body, f"tendril_{i}", (x, H / 2, z), (1.2, h, 1.2), "sculk")
        blade(body, f"tendril_tip_{i}", (x, H / 2 + h, z), (1.8, 1.8, 1.8), "sculk_glow")


# ---- the head: vanilla's phantom head, a ruff of warden tendrils round her face, rows of bone arching back ------------------

def head_parts(head):
    zc = FRONT - HL / 2
    head.box("head", (0, 0, zc), (HW, HH, HL), "hide")
    for sx in (-1, 1):                                   # the phantom's eyes, at the corners of its face
        head.box(f"eye_{sx}", (sx * (HW / 2 - 5), 1.2, ZF - 0.3), (7, 2.5, 0.6), "eye")
    # the crown: three rows of bones from her brow back over her head, staggered, longer row by row, each one arching
    # back (its base leans back, its tip bends further back), the outer ones leaning out
    rows = ((ZF + 4, ((-7, 0), (0, 0), (7, 0)), 4, 4),
            (ZF + 10, ((-11, 22.5), (-3.5, 0), (3.5, 0), (11, -22.5)), 6, 6),
            (ZF + 16.5, ((-13, 22.5), (-6.5, 0), (0, 0), (6.5, 0), (13, -22.5)), 7, 9))
    for r, (z, bones, h1, h2) in enumerate(rows):
        for i, (x, lean) in enumerate(bones):
            name = f"crown_{r}_{i}"
            base = (x, HH / 2, z)
            g = head.group(name, base, (45, 0, lean))
            blade(g, f"{name}_base", base, (2.6, h1, 2.6), "bone")
            tip = (x, HH / 2 + h1 - 0.4, z)
            t = g.group(f"{name}_arch", tip, (45, 0, 0))
            blade(t, f"{name}_tip", tip, (1.8, h2, 1.8), "bone")
    # the ruff: small warden-horn tendrils round the sides of her face like an owl's facial feathers - broad, tapering,
    # overlapping, fanned round the face and swept back; each glows in its inner part, like the warden's
    for sx in (-1, 1):
        word = "left" if sx < 0 else "right"
        for i, (y, fan, length, width) in enumerate(((4.5, 45, 8, 6), (1.5, 22.5, 10, 7), (-1.5, 0, 10, 7),
                                                     (-4.5, -22.5, 8, 6))):
            name = f"ruff_{word}_{i}"
            base = (sx * (HW / 2 - 1), y, ZF + 2.5 + i * 0.6)
            g = head.group(name, base, (0, 0, sx * fan))
            f = g.group(f"{name}_sweep", base, (0, sx * 45, 0))
            x0 = base[0] + sx * length * 0.35
            f.box(f"{name}_blade", (x0, y, base[2]), (length * 0.7, width, 1), "sculk")
            f.box(f"{name}_tip", (base[0] + sx * length * 0.85, y, base[2]), (length * 0.3, width * 0.55, 1), "sculk")
            f.box(f"{name}_glow", (base[0] + sx * length * 0.3, y, base[2] - 0.6), (length * 0.4, width * 0.45, 0.4),
                  "sculk_glow")


# ---- the wings: vanilla's two panels, whole (the tears are painted), a bone spar along the front -------------------------

def wing(parent, side, rot, elbow_rot):
    sx = side
    word = "left" if sx < 0 else "right"
    x0, y0, z0 = sx * W / 2, 3.0, FRONT + 2
    chord = 9 * U
    g = parent.group(f"wing_{word}", (x0, y0, z0), rot)
    span = 0.0
    for part, (length, spar) in enumerate(((6 * U, 4), (13 * U, 3))):
        if part == 1:
            g = g.group(f"wing_{word}_tip", (x0 + sx * span, y0, z0), elbow_rot)
        cx = x0 + sx * (span + length / 2)
        g.box(f"wing_{word}_{part}_membrane", (cx, y0, z0 + chord / 2), (length, 1, chord), "membrane")
        g.box(f"wing_{word}_{part}_spar", (cx, y0 + 0.5, z0 + spar / 2 - 0.5), (length, spar, spar), "bone")
        span += length


# ---- the owl's tail -----------------------------------------------------------------------------------------------------

def tail_parts(tail):
    z0 = L / 2
    tail.box("tail_root", (3, 0, z0 + 5), (9, 8, 10), "hide")
    tail.box("tail_vertebrae", (-2.5, 0.5, z0 + 5), (4, 4, 11), "bone")
    for i, (yaw, length, x) in enumerate(((-45, 32, -3), (-22.5, 40, -1.5), (0, 44, 0), (22.5, 40, 1.5), (45, 32, 3))):
        base = (x, 0, z0 + 9)
        g = tail.group(f"feather_{i}", base, (0, yaw, 0))
        mat = "feather" if i % 2 else "feather_dark"
        g.box(f"feather_{i}_vane", (x, 0, base[2] + (length - 5) / 2), (12, 1, length - 5), mat)
        g.box(f"feather_{i}_tip", (x, 0, base[2] + length - 2.5), (8, 1, 5), mat)          # a rounded end


# ---- the model ----------------------------------------------------------------------------------------------------------

POSES = {
    "glide": {"head": -6, "tail": -4, "wing": lambda sx: ((0, 0, sx * 8), (0, 0, sx * 4))},
    "grounded": {"head": -12, "tail": -2, "wing": lambda sx: ((0, 0, -sx * 6), (0, 0, -sx * 10))},
}


def build(pose):
    p = POSES[pose]
    m = Model(f"occultech_night_matriarch_{pose}")
    body = m.group("body", (0, 0, 0))
    body_parts(body)
    head = body.group("hi_head", (0, 0, FRONT), (p["head"], 0, 0))
    head_parts(head)
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
    def under(c):
        g = c.group
        while g is not None:
            if g.name == "hi_head":
                return True
            g = g.parent
        return False
    return [b for b, c in zip(model.render_json(v2.PALETTE), model.cubes) if under(c)]


GLIDE_VIEWS = [
    {"name": "flat_below", "mode": "flat", "camera": "persp", "yaw": -30, "height": 1.62, "dist": 8, "target_z": 9.6,
     "lens": 30},
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 35, "height": 14, "dist": 13, "target_z": 9.3},
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 10.5, "dist": 13, "target_z": 9.6},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "sil_below", "mode": "silhouette", "camera": "persp", "yaw": 25, "height": 1.62, "dist": 9,
     "target_z": 9.6, "lens": 30},
]
GROUND_VIEWS = [
    {"name": "flat_eye", "mode": "flat", "camera": "persp", "yaw": 15, "height": 1.62, "dist": 11, "target_z": 1.0},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": -35, "height": 6, "dist": 15, "target_z": 0.8},
]
FACE_VIEWS = [
    {"name": "face_front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 1.0, "dist": 6, "target_z": 0.8,
     "player": False},
    {"name": "face_34", "mode": "flat", "camera": "persp", "yaw": 40, "height": 2.4, "dist": 6, "target_z": 0.8,
     "player": False},
    {"name": "face_side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 1.4, "dist": 6.5, "target_z": 0.9,
     "player": False},
]
CELLS = [("glide", "flat_below", "gliding: from below (a player's eye)"), ("glide", "flat_34", "gliding: three-quarter"),
         ("glide", "flat_front", "gliding: front"), ("glide", "sil_below", "gliding: from below, silhouette"),
         ("glide", "sil_top", "gliding: from above"), ("glide", "sil_side", "gliding: side"),
         ("grounded", "flat_eye", "grounded: a player's eye"), ("grounded", "clay_34", "grounded: clay"),
         ("face", "face_front", "her face"), ("face", "face_34", "her head, three-quarter"),
         ("face", "face_side", "her head, side")]


def make_sheet(stats):
    tw, th, pad, top, cols = 460, 350, 12, 60, 3
    rows = (len(CELLS) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (tw + pad), top + rows * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), f"Night Matriarch - the full blockout (session 1)  -  span {stats['size_blocks'][0]} blocks, "
                       f"{stats['size_blocks'][2]} long, {stats['cubes']} cubes", font=sheet._font(26), fill=sheet.INK)
    for k, (folder, name, label) in enumerate(CELLS):
        x, y = pad + (k % cols) * (tw + pad), top + (k // cols) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / folder / f"{name}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "blockout.png")


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(PALETTE)
    glide = build("glide")
    stats = glide.stats()
    (OUT / "occultech_night_matriarch_blockout.bbmodel").write_text(json.dumps(glide.to_bbmodel(), indent=1) + "\n",
                                                                     encoding="utf-8")
    v2.run_blender(glide.render_json(v2.PALETTE), OUT / "glide", GLIDE_VIEWS)
    grounded = build("grounded")
    v2.run_blender(grounded.render_json(v2.PALETTE), OUT / "grounded", GROUND_VIEWS)
    v2.run_blender(head_only(grounded), OUT / "face", FACE_VIEWS)
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    make_sheet(stats)
    print(stats)


if __name__ == "__main__":
    main()
