"""The Hollow Warlord (the Headsman), session 1 step 2: the helm study and the sword study, on take 2's A, the Plate.

The skulls carry the real wither skeleton pixels from the 26.2 client (wither_skeleton.png) at 2x, one cube per
texel, with the eyes lit soul cyan. On the vanilla face the eyes are texel row 4 (from the top), the nose row 5, the
teeth row 6: at 2x the eyes sit 6..8 above the skull's underside, the teeth 2..4. Every helm is fitted to that.

Helms:
  H1 Sallet      a low rounded dome, its brow just over the eyes, swept back into a two-lame tail; the face bare
  H2 Barbute     closed round the whole skull but for a T cut over the eyes and down to the teeth
  H3 Kettle Hat  a high dome with a wide, downturned brim; the eyes glow in its shadow; the face bare

Swords (all square-guarded, the brand down the fuller):
  S1 Executioner's  broad, square-ended, a short downturned guard
  S2 Flamberge      a wavy blade, parrying lugs above a leather ricasso
  S3 Greatsword     long and straight, tapering to a point, a wide guard

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/headsman_study.py <folder>
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import headsman_take2 as h2, volley_crone_s2 as v2  # noqa: E402
from bosses.headsman_silhouettes import _n, octo  # noqa: E402
from bosses.tide_silhouettes import euler, frame, obox  # noqa: E402
from bosskit.bbmodel import rotation_matrix  # noqa: E402

OUT = ROOT / "docs/art/bosses/hollow_warlord/overhaul/s1_study"
SKIN = None
EYE = (90, 236, 244)
K = 2.0


def px(rgb):
    name = "px_%02x%02x%02x" % tuple(rgb[:3])
    v2.PALETTE.setdefault(name, tuple(rgb[:3]))
    return name


def skin(u, v, eyes):
    rgb = SKIN.getpixel((u, v))[:3]
    if eyes and v == 12 and (u - 8) in (1, 2, 5, 6):       # the face's row 4: the eye texels
        return EYE
    return rgb


def pixel_skull(g, c, rot=(0, 0, 0), eyes=True, name="px"):
    """A 16-unit cube showing the wither skeleton head's front, sides and top, one 2x2 tile per texel.
    c = the cube's centre; rot turns the whole skull about c (the model faces -z, its right is +x)."""
    c = np.array(c, float)
    half, t = 8.0, 0.15
    g.box(name + "_core", tuple(c), (15.9, 15.9, 15.9), "skull", rotation=rot, origin=tuple(c))
    for r in range(8):
        for col in range(8):
            y = half - (r + 0.5) * K
            a = half - (col + 0.5) * K
            for tag, off, size, uv in (
                    ("f", (a, y, -half), (K, K, t), (8 + col, 8 + r)),          # front: viewer's left = +x
                    ("r", (half, y, half - (col + 0.5) * K), (t, K, K), (col, 8 + r)),
                    ("l", (-half, y, -half + (col + 0.5) * K), (t, K, K), (16 + col, 8 + r)),
                    ("t", (a, half, half - (r + 0.5) * K), (K, t, K), (8 + col, r))):
                g.box(f"{name}_{tag}{col}{r}", tuple(c + np.array(off)), size, px(skin(*uv, eyes and tag == "f")),
                      rotation=rot, origin=tuple(c))


# ---- the helms (in the head group; the skull centred at z -1, from base to base + 16, as take 2 authored them) ----

def drop_teeth(h):
    for ch in list(h.children):
        if getattr(ch, "name", "") in ("skull", "teeth"):
            h.children.remove(ch)
            h.model.cubes.remove(ch)


def face(h, base):
    drop_teeth(h)
    pixel_skull(h, (0, base + 8, -1))


def helm_sallet(h, base):
    face(h, base)
    octo(h, "sallet", (0, base + 13.6, -0.6), 9.9, 9.6, "plate")              # brow at base + 8.8, just over the eyes
    octo(h, "sallet_crown", (0, base + 19.1, -0.2), 7.8, 1.6, "plate_lit")
    octo(h, "sallet_cap", (0, base + 20.3, 0), 4.6, 1, "plate")
    h.box("sallet_brow", (0, base + 9.4, -10.4), (17.4, 1.6, 2), "plate_lit")  # a rolled brow edge
    h.box("sallet_comb", (0, base + 20, 0.5), (2.2, 1.8, 17), "plate_lit")
    for s in (-1, 1):                                                          # cheeks down past the ears
        h.box(f"sallet_cheek{s}", (s * 9.4, base + 7.2, 2.6), (1.8, 6, 10), "plate", rotation=(0, -s * 6, 0))
    h.box("sallet_tail0", (0, base + 9.6, 10.2), (18.6, 2.6, 8), "plate", rotation=(22, 0, 0))
    h.box("sallet_tail1", (0, base + 6.6, 15.6), (17, 2.4, 7), "plate_lit", rotation=(34, 0, 0))


def helm_barbute(h, base):
    face(h, base)
    lo, hi, r = base - 1, base + 18, 9.8
    side = 2 * r * math.tan(math.pi / 8)
    zc = -1
    hgt = hi - lo
    yc = (lo + hi) / 2
    h.box("barbute_a", (0, yc, zc + 1), (2 * r, hgt, side + 1.8), "plate")     # the shell without its front face
    h.box("barbute_c", (0, yc, zc), (2 * r - 0.04, hgt - 0.04, side), "plate", rotation=(0, 45, 0))
    h.box("barbute_d", (0, yc, zc), (side - 0.02, hgt - 0.06, 2 * r - 0.04), "plate", rotation=(0, 45, 0))
    h.box("barbute_back", (0, yc, zc + r - 1), (side, hgt - 0.02, 2), "plate")
    zf = zc - 9.6
    h.box("barbute_brow", (0, base + 13.9, zf), (side + 4, 8.6, 1.6), "plate")      # above the T
    for s in (-1, 1):
        h.box(f"barbute_cheek{s}", (s * 4.9, base + 2.1, zf), (5.6, 6.2, 1.6), "plate")  # beside the T's stem
        h.box(f"barbute_temple{s}", (s * 7.1, base + 7, zf + 0.4), (2, 2.6, 1.6), "plate")
    for r in range(8):           # the face seen through the T: its texels brought forward into the opening
        for col in range(8):
            x, y = 8 - (col + 0.5) * K, base + 16 - (r + 0.5) * K
            in_bar = abs(x) < 6.2 and 5.0 < y < 9.6
            in_stem = abs(x) < 2.2 and y < 5.2
            if in_bar or in_stem:
                h.box(f"t_window{col}{r}", (x, y, zf - 0.3), (K, K, 0.2), px(skin(8 + col, 8 + r, True)))
    h.box("barbute_rim", (0, base + 10.0, zf - 0.6), (side + 4.4, 1.2, 1), "plate_lit")  # the T's top edge
    h.box("barbute_ridge", (0, base + 18.6, zc), (2.2, 1.8, 2 * r - 2), "plate_lit")
    octo(h, "barbute_top", (0, hi + 0.6, zc), 7.4, 1.2, "plate_lit")


def helm_kettle(h, base):
    face(h, base)
    octo(h, "kettle_dome", (0, base + 15.2, -1), 9.4, 7.6, "plate")
    octo(h, "kettle_crown", (0, base + 19.6, -1), 7.2, 1.6, "plate_lit")
    octo(h, "kettle_cap", (0, base + 20.8, -1), 3.6, 1, "plate")
    octo(h, "kettle_band", (0, base + 11.9, -1), 9.8, 1.4, "plate_lit")
    # the brim: eight plates round the dome, sloping down and out
    for i in range(8):
        a = math.radians(i * 45)
        out = np.array([math.sin(a), 0, -math.cos(a)])
        c = np.array([0, base + 10.0, -1]) + out * 12.0
        h.box(f"kettle_brim{i}", tuple(c), (10.2, 1.4, 7.8), "plate", rotation=brim_rot(i))
    h.box("kettle_comb", (0, base + 20.2, -1), (2.2, 2.6, 15), "plate_lit")   # a ridge front to back: a war hat
    h.box("kettle_shadow", (0, base + 8.9, -10.2), (14, 1.6, 0.4), "socket")   # the brim's shadow over the eyes


def brim_rot(i):
    """A brim plate's rotation: its long side along the dome, tipped 16 degrees down and out (bosskit X, Y, Z)."""
    return euler(rotation_matrix((0, -i * 45, 0)) @ rotation_matrix((-26, 0, 0)))


HELMS = {"H1": ("Sallet", helm_sallet), "H2": ("Barbute", helm_barbute), "H3": ("Kettle Hat", helm_kettle)}


# ---- the swords: sword(g, grip, tip_dir, flat_normal) from the middle of the grip; returns the tip -------------------

def _frame(tip_dir, flat_normal):
    a = _n(tip_dir)
    w = _n(np.cross(flat_normal, a))
    return a, w, frame(a, w)


def sword_executioner(g, grip, tip_dir, flat_normal):
    a, w, m = _frame(tip_dir, flat_normal)
    p = np.array(grip, float)
    obox(g, "grip", p, (15, 3.6, 3.6), m, "grip")
    obox(g, "pommel", p - a * 9.6, (4.6, 6, 6), m, "guard")
    gd = p + a * 9.1
    obox(g, "guard", gd, (3.2, 14, 4.6), m, "guard")
    for s in (-1, 1):                                    # the quillons, turned down towards the hands
        obox(g, f"quillon{s}", gd + w * s * 9 - a * 2, (3, 7, 4), frame(a, _n(w * s * 0.8 - a * 0.6)), "guard")
    mid = gd + a * (1.6 + 26)
    for i, sgn in enumerate((-1, 1)):                   # two halves: an item model holds at most 48 units
        obox(g, f"blade_{'low' if i == 0 else 'high'}", mid + a * sgn * 13, (26, 12.5, 2), m, "blade")
    obox(g, "blade_end", gd + a * (1.6 + 52 + 0.8), (1.6, 12.5, 2), m, "guard")      # the squared, thickened end
    obox(g, "brand", mid - a * 4, (36, 2.6, 2.4), m, "brand")
    return gd + a * 55


def sword_flamberge(g, grip, tip_dir, flat_normal):
    a, w, m = _frame(tip_dir, flat_normal)
    p = np.array(grip, float)
    obox(g, "grip", p, (15, 3.6, 3.6), m, "grip")
    obox(g, "pommel", p - a * 9.6, (5, 5, 5), m, "guard")
    gd = p + a * 9.1
    obox(g, "guard", gd, (3.2, 24, 4.4), m, "guard")
    obox(g, "ricasso", gd + a * 6.6, (10, 6.4, 3), m, "leather_dark")
    for s in (-1, 1):
        obox(g, f"lug{s}", gd + a * 12 + w * s * 5, (2.4, 4, 2.4), m, "guard")
    start = gd + a * 11.6
    for i in range(9):                                   # the wave: segments stepped side to side
        off = (1.6 if i % 2 else -1.6) * (1 - i / 12)
        width = 9.6 - i * 0.45
        obox(g, f"wave{i}", start + a * (3 + i * 5.6) + w * off, (6, width, 1.9), m, "blade")
    obox(g, "tip", start + a * (3 + 9 * 5.6), (5, 3.6, 1.9), m, "blade")
    obox(g, "brand", start + a * 22, (34, 2.4, 2.3), m, "brand")
    return start + a * 56


def sword_greatsword(g, grip, tip_dir, flat_normal):
    a, w, m = _frame(tip_dir, flat_normal)
    p = np.array(grip, float)
    obox(g, "grip", p, (17, 3.6, 3.6), m, "grip")
    obox(g, "pommel", p - a * 10.6, (5.4, 5.4, 5.4), m, "guard")
    gd = p + a * 10.1
    obox(g, "guard", gd, (3, 30, 4), m, "guard")
    for s in (-1, 1):
        obox(g, f"guard_end{s}", gd + w * s * 15 + a * 2, (6, 3, 4.4), m, "guard")
    obox(g, "blade", gd + a * 27, (50, 10, 2), m, "blade")
    obox(g, "taper", gd + a * 55, (8, 6, 1.9), m, "blade")
    obox(g, "point", gd + a * 60, (4, 2.6, 1.8), m, "blade")
    obox(g, "brand", gd + a * 24, (34, 2.4, 2.4), m, "brand")
    return gd + a * 62


SWORDS = {"S1": ("Executioner's", sword_executioner), "S2": ("Flamberge", sword_flamberge),
          "S3": ("Greatsword", sword_greatsword)}


# ---- textured floating skulls ------------------------------------------------------------------------------------

def taken_skull(g, name, c, yaw=0.0, lit=True, roll=0.0):
    pixel_skull(g, c, (0, yaw, roll), eyes=lit, name=name)
    c = np.array(c, float)
    if lit:
        for i, (wd, hh) in enumerate(((9, 3.4), (4.4, 3.4))):
            g.box(f"{name}_fire{i}", tuple(c + [0, -9.6 - i * 3.2, 2 + i * 1.6]), (wd, hh, wd), "flame",
                  rotation=(0, 45 * (i % 2) + yaw, 0))


# ---- rendering ----------------------------------------------------------------------------------------------------

HEAD_VIEWS = [
    {"name": "head_front", "mode": "flat", "camera": "ortho_front", "player": False},
    {"name": "head_34", "mode": "flat", "camera": "persp", "yaw": 32, "height": 4.9, "dist": 5.2, "target_z": 4.7,
     "player": False},
]
SIDE_VIEW = [{"name": "head_side", "mode": "flat", "camera": "ortho_side", "player": False}]
BODY_VIEWS = [
    {"name": "body_34", "mode": "flat", "camera": "persp", "yaw": 30, "height": 2.6, "dist": 13.5, "target_z": 3.4},
]


def build(helm, sword_key, pose):
    h2.helm_sallet = HELMS[helm][1]                 # take 2's build calls helm_sallet for take A
    h2.sword = SWORDS[sword_key][1]
    h2.taken_skull = taken_skull
    return h2.build("A", pose)


def head_boxes(m, below):
    """Only the parts above `below` (model units): the head, the shoulders, the floating skulls."""
    boxes = m.render_json(v2.PALETTE)
    return [b for b in boxes if min(p[1] for p in b["corners"]) > below and not b["name"].startswith("taken")]


def render_helms(only=None):
    for key in (only or HELMS):
        m = build(key, "S1", h2.REST)
        v2.run_blender(head_boxes(m, h2.HIP + 22), OUT / key, HEAD_VIEWS)
        column = [b for b in head_boxes(m, h2.HIP + 28) if max(abs(p[0]) for p in b["corners"]) < 16]
        v2.run_blender(column, OUT / key, SIDE_VIEW)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, BODY_VIEWS)


SWORD_VIEW = [{"name": "sword", "mode": "flat", "camera": "ortho_front", "player": False}]


def render_swords():
    from bosskit.bbmodel import Model
    for key, (_, fn) in SWORDS.items():
        s = Model("sword_" + key)
        fn(s.group("sword", (0, 0, 0)), (0, 9, 0), (0, 1, 0), (0, 0, -1))
        v2.run_blender(s.render_json(v2.PALETTE), OUT / key, SWORD_VIEW)
        m = build("H1", key, h2.SWEEP)
        v2.run_blender(m.render_json(v2.PALETTE), OUT / key, [dict(BODY_VIEWS[0], name="sweep_34", yaw=8,
                                                                    height=2.4, dist=15)])


def sheets():
    tw, th, pad, top = 430, 360, 14, 64
    cols = [("head_front", "front"), ("head_34", "three-quarter"), ("head_side", "side"), ("body_34", "on him")]
    img = Image.new("RGB", (pad + 4 * (tw + pad), top + 3 * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Hollow Warlord, the Plate - helm study (real wither skeleton pixels, eyes lit)",
            font=sheet._font(28), fill=sheet.INK)
    for r, (key, (title, _)) in enumerate(HELMS.items()):
        for c, (v, lab) in enumerate(cols):
            x, y = pad + c * (tw + pad), top + r * (th + 30 + pad)
            img.paste(sheet._tile(OUT / key / f"{v}.png", tw, th), (x, y))
            dr.text((x + 6, y + th + 4), f"{key} {title}: {lab}", font=sheet._font(18), fill=sheet.DIM)
    img.save(OUT / "helms.png")
    tw2, th2 = 300, 560
    img = Image.new("RGB", (pad + 3 * (tw2 + pad) + 3 * (520 + pad), top + th2 + 40), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Hollow Warlord - sword study (each one swung in the sweep, with H1)", font=sheet._font(28),
            fill=sheet.INK)
    for i, (key, (title, _)) in enumerate(SWORDS.items()):
        x = pad + i * (tw2 + pad)
        img.paste(sheet._tile(OUT / key / "sword.png", tw2, th2), (x, top))
        dr.text((x + 6, top + th2 + 6), f"{key} {title}", font=sheet._font(18), fill=sheet.DIM)
        x2 = pad + 3 * (tw2 + pad) + i * (520 + pad)
        img.paste(sheet._tile(OUT / key / "sweep_34.png", 520, th2), (x2, top))
        dr.text((x2 + 6, top + th2 + 6), f"{key} {title}: the sweep", font=sheet._font(18), fill=sheet.DIM)
    img.save(OUT / "swords.png")


def main():
    global SKIN
    SKIN = Image.open(Path(sys.argv[1]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(h2.PALETTE)
    if "--helms" in sys.argv:
        render_helms()
    elif "--swords" in sys.argv:
        render_swords()
    else:
        render_helms()
        render_swords()
    sheets()


if __name__ == "__main__":
    main()
