"""The Unbound redesign, session 1 step 2: the face study (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

A bust of the take-2 silhouette (the bare, buff, hunched brute): his chest, traps and shoulders, the straps and the
burning chest piece, and the head, which is what this step decides. The head is vanilla's illager head (8x10x8, the
2x4x2 nose hanging one pixel below the chin; IllagerModel in the 26.2 client) at 1.5x, sunk low between the traps.

Three heads on the same bust:
  F1  The blindfolded vindicator  vanilla's face exactly; a neat red band over the eyes, knotted behind, its ends
                                  trailing; his left eye burns cyan through a tear in it; bull horns out from the
                                  temples, then up
  F2  The scowl                   a heavy brow pushed down into a scowl over the band, a broader nose, a square jaw
                                  with an underbite; the band ragged and slipping askew, the eye burning through a
                                  scorched hole with cyan wisps rising off it; the horns sweep forward like a charging
                                  bull's
  F3  The bull                    a heavy horn boss across the top of the skull, the horns out, down and up like a
                                  buffalo's; an iron ring through the big nose; the band bound tight, its long ends
                                  hanging over his shoulder; the eye's cyan bleeding through the weave around it

Units are model pixels (16 = one block). The front is -z; his left is -x.
Run from the repository root: python tools/art/bosses/unbound_face.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s1_face"
K = 1.5
PALETTE = {
    "skin": (122, 128, 126), "skin_dark": (98, 104, 104), "nose": (112, 118, 116), "brow": (58, 60, 62),
    "pants": (50, 50, 58), "cloth": (150, 34, 34), "cloth_dark": (108, 24, 26), "scorch": (40, 22, 22),
    "horn": (208, 196, 164), "horn_dark": (164, 150, 116), "horn_root": (128, 116, 92),
    "strap": (88, 60, 40), "stud": (206, 210, 218), "iron": (70, 66, 72), "iron_lit": (120, 116, 124),
    "fire": (255, 132, 36), "fire_hot": (255, 214, 120),
    "eye": (90, 230, 255), "eye_hot": (220, 252, 255), "eye_dim": (60, 150, 176),
}
FACES = {"F1": "The blindfolded vindicator", "F2": "The scowl", "F3": "The bull"}
HUNCH = -20                                       # the upper body leans forward over the hips


def horn(g, name, points, widths, tilt=0.0, mats=("horn_root", "horn", "horn", "horn_dark")):
    """A bull's horn: tapering beams along a curve drawn flat in the x-y plane (the root's depth), so no piece
    twists; tilt swings the whole horn forward (negative) or back about its root."""
    z = points[0][2]
    hg = g.group(name, points[0], (tilt, 0, 0))
    for i in range(len(points) - 1):
        a, b = (points[i][0], points[i][1], z), (points[i + 1][0], points[i + 1][1], z)
        d = [b[j] - a[j] for j in range(3)]
        n = sum(v * v for v in d) ** 0.5 or 1
        ext = widths[i] * 0.45 / n                              # run each piece into the next so the joints close
        a2 = tuple(a[j] - d[j] * ext for j in range(3))
        b2 = tuple(b[j] + d[j] * ext for j in range(3))
        m1.beam(hg, f"{name}_{i}", a2, b2, widths[i], mats[min(i, len(mats) - 1)])


def bust(model, face):
    root = model.group("root", (0, 0, 0))
    root.box("waist", (0, 25, 0), (19, 8, 12), "pants")
    root.box("belt", (0, 28.4, 0), (20, 2.4, 13), "strap")
    torso = root.group("torso", (0, 26, 0), (HUNCH, 0, 0))
    # the bare torso: a deep, wide chest; lats tapering to the waist; deltoids; traps rising round the low head
    m1.octo(torso, "chest", (0, 40, 0), (30, 20, 17), "skin", 0.12)
    torso.box("abdomen", (0, 31, 0), (21, 9, 13), "skin")
    torso.box("traps", (0, 49, 2.5), (20, 5, 11), "skin")
    for sx in (-1, 1):
        torso.box(f"delt_{sx}", (sx * 16.5, 45, 0.5), (10, 10, 12), "skin", rotation=(0, 0, sx * -10))
        torso.box(f"trap_slope_{sx}", (sx * 11.5, 47.5, 2), (8, 4, 10), "skin", rotation=(0, 0, sx * -26))
        torso.box(f"upper_arm_{sx}", (sx * 18.5, 35, 0), (10, 15, 10.5), "skin_dark", rotation=(0, 0, sx * 6))
        torso.box(f"pec_line_{sx}", (sx * 5.5, 35.6, -8.6), (9, 1.0, 0.6), "skin_dark", rotation=(0, 0, sx * 6))
    # the straps crossing the chest, studded, and the burning chest piece where they cross
    for sx in (-1, 1):
        a, b = (sx * 13.5, 47, -7.6), (-sx * 8.5, 29, -7.4)
        m1.beam(torso, f"strap_{sx}", a, b, 2.6, "strap")
        for i in range(6):
            t = (i + 0.5) / 6
            p = tuple(a[j] + (b[j] - a[j]) * t for j in range(3))
            torso.box(f"stud_{sx}_{i}", (p[0], p[1], p[2] - 1.2), (1.0, 1.0, 0.6), "stud")
    torso.box("chest_piece", (0, 38, -9.0), (11, 10, 1.4), "iron")
    torso.box("chest_fire", (0, 38, -9.8), (6, 5.4, 0.4), "fire")
    torso.box("chest_fire_hot", (0, 37.4, -10.0), (1.4, 1.6, 0.3), "fire_hot")
    for dx in (-1.6, 0, 1.6):
        torso.box(f"grate_{dx}", (dx, 38, -10.1), (0.8, 6.4, 0.4), "iron")
    torso.box("chest_rim", (0, 43.4, -9.2), (11.6, 1.2, 1.6), "iron_lit")
    # the head, low and forward between the traps, lifted so he looks ahead
    head = torso.group("hi_head", (0, 49, -4), (-HUNCH - 6, 0, 0))
    hw, hh = 8 * K, 10 * K
    hc = (0, 49 + hh / 2, -5)
    head.box("head", hc, (hw, hh, hw), "skin")
    HEADS[face](head, hc, hw, hh, hc[2] - hw / 2)
    return root


def vanilla_face(h, hc, hw, hh, f, brow=True):
    """Vanilla's illager face: the unibrow, the long nose hanging a pixel below the chin."""
    x, y, z = hc
    bottom = y - hh / 2
    h.box("nose", (x, bottom + 1 * K, f - 1 * K), (2 * K, 4 * K, 2 * K), "nose")
    if brow:
        h.box("brow", (x, bottom + 8 * K, f - 0.3), (8 * K, 1.2 * K, 0.6), "brow")
    return bottom


def band(h, hc, hw, y, height=4.2, tilt=0.0, mat="cloth"):
    """The red cloth wrapped round the head over the eyes."""
    x, _, z = hc
    h.box("band", (x, y, z), (hw + 0.9, height, hw + 0.9), mat, rotation=(0, 0, tilt))


def tails(h, hc, hw, y, long=False):
    """The knot behind and its two trailing ends."""
    x, _, z = hc
    back = z + hw / 2 + 0.6
    h.box("knot", (x, y, back + 0.6), (2.6, 2.6, 1.6), "cloth_dark")
    n = 9 if long else 5.5
    h.box("tail_a", (x - 1.2, y - n / 2 - 0.6, back + 1.6), (2.2, n, 0.6), "cloth_dark", rotation=(-24, 0, 8))
    h.box("tail_b", (x + 1.0, y - n / 2 - 1.4, back + 1.2), (1.8, n * 0.8, 0.6), "cloth_dark", rotation=(-16, 0, -10))
    if long:
        h.box("tail_c", (x - 4.5, y - 7, back - 1), (2.0, 10, 0.6), "cloth_dark", rotation=(-8, 30, 18))


def face_blindfold(h, hc, hw, hh, f):
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f)
    eye_y = bottom + 6 * K
    band(h, hc, hw, eye_y)
    tails(h, hc, hw, eye_y)
    # the tear and the left eye burning through it
    h.box("tear", (-2.4 * K, eye_y + 0.2, f - 0.55), (3.6, 1.6, 0.3), "scorch", rotation=(0, 0, -8))
    h.box("tear_b", (-2.4 * K + 1.2, eye_y - 0.5, f - 0.55), (1.6, 1.0, 0.3), "scorch")
    h.box("eye", (-2.4 * K, eye_y + 0.2, f - 0.7), (2.6, 0.8, 0.3), "eye", rotation=(0, 0, -8))
    h.box("eye_core", (-2.4 * K, eye_y + 0.2, f - 0.85), (1.0, 0.5, 0.2), "eye_hot")
    # bull horns from the temples, above the band: out, then up, the tips turned a little in
    for sx in (-1, 1):
        horn(h, f"horn_{sx}", [(sx * (hw / 2 - 1), eye_y + 4.6, z), (sx * (hw / 2 + 3.5), eye_y + 5.6, z),
                               (sx * (hw / 2 + 7), eye_y + 8.2, z - 0.6), (sx * (hw / 2 + 8), eye_y + 12, z - 1.4),
                               (sx * (hw / 2 + 6.8), eye_y + 14.6, z - 2)], [4.8, 4.0, 3.0, 2.0], tilt=-12)


def face_scowl(h, hc, hw, hh, f):
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f, brow=False)
    eye_y = bottom + 6 * K
    # a heavy brow pushed down in the middle, a broader nose over it, a square jaw with an underbite
    for sx in (-1, 1):
        h.box(f"brow_{sx}", (sx * 2.6, eye_y + 3.4, f - 0.9), (5.6, 2.2, 1.8), "brow", rotation=(0, 0, sx * 14))
    h.box("nose_wide", (x, bottom + 2.2, f - 1.2), (3.6, 4.4, 2.4), "nose")
    h.box("jaw", (x, bottom + 1.2, f - 0.4), (hw - 0.6, 2.4, 1.6), "skin_dark")
    for sx in (-1, 1):
        h.box(f"tusk_{sx}", (sx * 3.4, bottom + 2.8, f - 1.0), (1.0, 1.6, 0.8), "horn")
    band(h, hc, hw, eye_y, 4.4, tilt=7)
    tails(h, hc, hw, eye_y)
    h.box("rag", (2.6, eye_y - 2.6, f - 0.5), (3.0, 1.8, 0.4), "cloth", rotation=(0, 0, 12))   # a torn flap hanging
    h.box("hole", (-2.4 * K, eye_y + 0.1, f - 0.55), (3.6, 2.4, 0.3), "scorch", rotation=(0, 0, 10))
    h.box("eye", (-2.4 * K, eye_y + 0.1, f - 0.7), (2.6, 0.8, 0.3), "eye", rotation=(0, 0, -10))
    h.box("eye_core", (-2.4 * K, eye_y + 0.1, f - 0.85), (0.8, 0.6, 0.2), "eye_hot")
    for i, (dx, dy, s) in enumerate(((-0.6, 2.6, 1.0), (0.4, 4.2, 0.8), (-0.2, 5.8, 0.6))):     # wisps rising off it
        h.box(f"wisp_{i}", (-2.4 * K + dx, eye_y + dy, f - 1.2 - i * 0.3), (s, s * 1.4, s), "eye_dim")
    # the horns sweep forward like a charging bull's
    for sx in (-1, 1):
        horn(h, f"horn_{sx}", [(sx * (hw / 2 - 1), eye_y + 4.6, z + 1), (sx * (hw / 2 + 4), eye_y + 5.4, z),
                               (sx * (hw / 2 + 6.5), eye_y + 7, z - 3.5), (sx * (hw / 2 + 7), eye_y + 9.2, z - 7),
                               (sx * (hw / 2 + 5.4), eye_y + 11, z - 9)], [4.8, 4.0, 3.0, 2.0], tilt=-50)


def face_bull(h, hc, hw, hh, f):
    x, y, z = hc
    bottom = vanilla_face(h, hc, hw, hh, f)
    eye_y = bottom + 6 * K
    band(h, hc, hw, eye_y, 4.0)
    tails(h, hc, hw, eye_y, long=True)
    h.box("halo", (-2.4 * K, eye_y + 0.1, f - 0.55), (4.2, 2.2, 0.3), "eye_dim")                # cyan through the weave
    h.box("eye", (-2.4 * K, eye_y + 0.1, f - 0.7), (2.6, 0.8, 0.3), "eye")
    h.box("eye_core", (-2.4 * K, eye_y + 0.1, f - 0.85), (0.8, 0.6, 0.2), "eye_hot")
    # an iron ring through the big nose
    nz = f - 2 * K - 0.4
    h.box("ring_l", (-1.7, bottom - 1.6, nz), (0.8, 2.6, 0.8), "iron_lit")
    h.box("ring_r", (1.7, bottom - 1.6, nz), (0.8, 2.6, 0.8), "iron_lit")
    h.box("ring_b", (0, bottom - 2.9, nz), (4.2, 0.8, 0.8), "iron_lit")
    # a heavy horn boss across the top of the skull; the horns out, down a little, then up, like a buffalo's
    h.box("boss", (x, y + hh / 2 + 0.6, z + 0.4), (hw + 1.4, 2.4, 6.4), "horn_root")
    for sx in (-1, 1):
        horn(h, f"horn_{sx}", [(sx * (hw / 2 - 0.5), y + hh / 2 + 0.2, z + 0.4), (sx * (hw / 2 + 5), y + hh / 2 - 1.2, z),
                               (sx * (hw / 2 + 8.5), y + hh / 2, z - 0.4), (sx * (hw / 2 + 10.5), y + hh / 2 + 4, z - 1.2),
                               (sx * (hw / 2 + 9.6), y + hh / 2 + 7.4, z - 2)], [5.4, 4.4, 3.2, 2.2], tilt=-8)


HEADS = {"F1": face_blindfold, "F2": face_scowl, "F3": face_bull}
VIEWS = [
    {"name": "face", "mode": "flat", "camera": "persp", "yaw": -24, "height": 3.25, "dist": 2.9, "target_z": 3.35, "player": False},
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.1, "dist": 4.2, "target_z": 2.8, "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": -40, "height": 3.3, "dist": 4.4, "target_z": 2.8,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -14, "height": 1.62, "dist": 3.4, "target_z": 3.0,
     "lens": 24, "player": False},
    {"name": "profile", "mode": "flat", "camera": "persp", "yaw": 90, "height": 3.35, "dist": 3.2, "target_z": 3.3, "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    items = []
    for key, title in FACES.items():
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = Model(f"occultech_unbound_face_{key.lower()}")
        bust(model, key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        items.append((key, title))
        print(key, stats["cubes"], stats["size_blocks"])
    sheet.compare_sheet(OUT, items, OUT / "faces.png", heading="The Unbound - three heads (session 1, step 2)",
                        views=("face", "front", "three_quarter", "player_eye"))


if __name__ == "__main__":
    main()
