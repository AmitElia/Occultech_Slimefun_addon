"""Volley redesign, session 1: the Amethyst Crone - three silhouette directions as Blockbench cuboid blockouts.

A buff, mutated vanilla skeleton: the vanilla face on a 16-unit skull, a crone's stoop, armour on the upper body
only, amethyst growing out of the hump, and a steel arbalest (windlass crank, amethyst-tipped bolt) in the right hand.

  A  Crone archer  deepest stoop, crystals as a ridge down the spine, moderate bulk
  B  Geode back    medium stoop, one cracked geode erupting from the hump
  C  Mutant brute  slight stoop, the heaviest shoulders, crystals breaking through the left pauldron as well

Run from the repository root: python tools/art/bosses/volley_crone_s1.py
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, rotation_matrix  # noqa: E402
from bosskit import sheet  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s1_crone"
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe")
PALETTE = {
    "bone": (200, 200, 196),            # vanilla skeleton bone: cool grey-white
    "marrow": RAMPS["ash"][2],          # the dark inside of the ribcage, eye sockets, nose and mouth
    "iron": RAMPS["iron"][2],
    "chain": RAMPS["iron"][3],
    "wood": RAMPS["wood"][1],
    "string": RAMPS["twine"][3],
    "basalt": RAMPS["ash"][1],          # geode layers, outside in: basalt, calcite, amethyst
    "calcite": RAMPS["chalk"][4],
    "crystal": RAMPS["violet"][3],
    "glow": RAMPS["violet"][5],
}

DIRECTIONS = {
    "A": {"title": "Crone archer", "bend": 46, "bulk": 1.15, "crystals": "ridge"},
    "B": {"title": "Geode back", "bend": 36, "bulk": 1.25, "crystals": "geode"},
    "C": {"title": "Mutant brute", "bend": 20, "bulk": 1.45, "crystals": "brute"},
}


def beam(group, name, a, b, width, material, depth=None):
    """Square-section bone from a to b (rest space)."""
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    roll = math.degrees(math.atan2(dy, dx))
    yaw = math.degrees(math.atan2(-dz, math.hypot(dx, dy)))
    center = tuple((a[i] + b[i]) / 2 for i in range(3))
    return group.box(name, center, (math.dist(a, b), width, depth or width), material, rotation=(0, yaw, roll))


def crystal(group, name, base, pitch, side, length, width, material):
    """An amethyst shard rooted at base, growing back (+Z) tilted up by pitch and sideways by side, with a point."""
    rot = (-pitch, side, 0)
    axis = rotation_matrix(rot) @ np.array([0.0, 0.0, 1.0])
    body = length * 0.78
    center = np.array(base, float) + axis * body / 2
    group.box(name, center, (width, width, body), material, rotation=rot)
    tip = np.array(base, float) + axis * (body + length * 0.11)
    group.box(name + "_tip", tip, (width * 0.55, width * 0.55, length * 0.22), material, rotation=rot)


def geode_patch(group, name, center, size):
    """Where the crystals break out: a basalt crust with a calcite layer inside it."""
    w, h = size
    group.box(name + "_basalt", center, (w, h, 3), "basalt")
    group.box(name + "_calcite", (center[0], center[1], center[2] + 1.2), (w * 0.7, h * 0.7, 2), "calcite")


def make_leg(body, s, b):
    word = "left" if s < 0 else "right"
    hip, knee, ankle = (s * 6, 21, 2), (s * 9.5, 11, -3), (s * 8.5, 3, 0)
    thigh = body.group(f"leg_{word}_thigh", hip)
    beam(thigh, f"{word}_femur", hip, knee, 5 * b, "bone")
    shin = thigh.group(f"leg_{word}_shin", knee)
    shin.box(f"{word}_knee", knee, (7 * b, 6, 7 * b), "bone")
    beam(shin, f"{word}_tibia", knee, ankle, 4.5 * b, "bone")
    foot = shin.group(f"leg_{word}_foot", ankle)
    foot.box(f"{word}_heel", (s * 8.5, 2, 1), (6.5 * b, 4, 5), "bone")
    for i, dx in enumerate((-2.2, 0, 2.2)):
        foot.box(f"{word}_toe_{i}", (s * 8.5 + dx * b, 1.5, -5), (1.9 * b, 3, 8), "bone")


def make_arm(torso, s, d, b):
    """Long ape arms, laid out hanging straight down in rest space; the shoulder undoes the stoop, then poses."""
    word = "left" if s < 0 else "right"
    bend = d["bend"]
    sx = 17 * b
    shoulder, elbow, wrist = (s * sx, 46, 3), (s * (sx + 1), 30, 3), (s * (sx + 1), 15, 3)
    pose = (bend + 18, 0, s * 8) if s < 0 else (bend + 4, 0, s * 14)
    upper = torso.group(f"arm_{word}_upper", shoulder, pose)
    upper.box(f"{word}_shoulder_ball", shoulder, (8 * b, 8, 8 * b), "bone")
    beam(upper, f"{word}_humerus", shoulder, elbow, 6 * b, "bone")
    upper.box(f"{word}_spur", (s * (sx + 4.5 * b), 38, 4), (2, 5, 2), "bone", rotation=(0, 0, s * 30))
    fore = upper.group(f"arm_{word}_forearm", elbow, (12, 0, 0) if s < 0 else (25, 0, 10))
    fore.box(f"{word}_elbow", elbow, (8 * b, 7, 8 * b), "bone")
    beam(fore, f"{word}_ulna", elbow, wrist, 5.5 * b, "bone")
    hand = fore.group(f"arm_{word}_hand", wrist)
    hand.box(f"{word}_palm", (wrist[0], wrist[1] - 3, wrist[2]), (8 * b, 6, 8 * b), "bone")
    for i, dz in enumerate((-2.6, 0, 2.6)):
        hand.box(f"{word}_finger_{i}", (wrist[0] + s * 1, wrist[1] - 8, wrist[2] + dz * b), (2, 5, 2), "bone")
    if s > 0:
        fore.box("right_bracer", (wrist[0], 22, 3), (8.5 * b, 9, 8.5 * b), "iron")
        fore.box("right_bracer_rim", (wrist[0], 26.5, 3), (9.5 * b, 2, 9.5 * b), "chain")
        make_arbalest(hand, wrist)
    else:
        make_pauldron(upper, shoulder, b, d["crystals"] == "brute")
    return upper


def make_pauldron(upper, shoulder, b, cracked):
    x, y, z = shoulder
    upper.box("left_pauldron", (x - 2 * b, y + 3, z), (15 * b, 9, 17 * b), "iron")
    upper.box("left_pauldron_lame", (x - 3 * b, y - 3, z), (14 * b, 4, 15 * b), "iron")
    upper.box("left_pauldron_rim", (x - 2 * b, y + 8, z), (13 * b, 2, 15 * b), "chain")
    if cracked:
        for i, (dx, dz, p, sd, L, w) in enumerate(((-3, -2, 70, -25, 12, 3.5), (1, 3, 80, 10, 9, 3), (-6, 4, 55, -45, 7, 2.5))):
            crystal(upper, f"pauldron_crystal_{i}", (x + dx * b, y + 8, z + dz), p, sd, L, w, "crystal")


def make_arbalest(hand, wrist, tilt=55):
    """Built along -Y from the fist (the forearm points it forward): stock, steel prod at the muzzle, windlass at the butt."""
    x, y, z = wrist
    # the fist turns the weapon level: it points ahead from the hip instead of continuing the hanging forearm
    bow = hand.group("arbalest", (x, y - 3, z), (tilt, 0, 0))
    bow.box("stock", (x, y - 9, z - 3), (5, 30, 5), "wood")
    bow.box("lath_rail", (x, y - 10, z - 6), (2.5, 24, 1.5), "iron")
    bow.box("trigger_lever", (x, y + 1, z + 1), (1.5, 6, 3), "iron")
    bow.box("stirrup", (x, y - 25, z - 3), (9, 3, 2), "iron")
    prod = bow.group("arbalest_prod", (x, y - 21, z - 3))
    prod.box("prod_center", (x, y - 21, z - 3), (8, 3, 4), "iron")
    for s in (-1, 1):
        beam(prod, f"prod_limb_{s}", (x + s * 4, y - 21, z - 3), (x + s * 17, y - 18, z - 3), 3, "iron")
        prod.box(f"prod_nock_{s}", (x + s * 17, y - 18, z - 3), (2.5, 2.5, 3), "iron")
        beam(prod, f"string_{s}", (x + s * 17, y - 18, z - 3), (x, y - 5, z - 6), 0.8, "string")
    bow.box("bolt", (x, y - 16, z - 7.5), (1.4, 24, 1.4), "wood")
    bow.box("bolt_tip", (x, y - 30, z - 7.5), (3, 5, 3), "glow")
    crank = bow.group("windlass", (x, y + 8, z - 3))
    crank.box("windlass_drum", (x, y + 8, z - 3), (9, 4, 4), "iron")
    crank.box("windlass_arm", (x + 6, y + 8, z - 3), (2, 2, 9), "iron")
    crank.box("windlass_handle", (x + 6, y + 8, z + 2), (4, 1.6, 1.6), "wood")


def make_head(torso, d):
    """16-unit skull, vanilla face pixel-doubled; the jaw is the vanilla mouth row and chin."""
    head = torso.group("h_head", (0, 47, -4), (d["bend"] * 0.35, 0, 0))
    beam(head, "neck", (0, 46, -2), (0, 50, -9), 6, "bone")
    head.box("skull", (0, 57, -14), (16, 12, 16), "bone")
    head.box("eye_left", (-4, 54, -22.1), (4, 2, 0.6), "marrow")
    head.box("eye_right", (4, 54, -22.1), (4, 2, 0.6), "marrow")
    head.box("nose", (0, 52, -22.1), (4, 2, 0.6), "marrow")
    jaw = head.group("jaw_counter", (0, 51, -7))
    jaw.box("jaw", (0, 49, -14), (15.5, 4, 15.5), "bone")
    jaw.box("mouth", (0, 50, -21.9), (12, 2, 0.6), "marrow")
    for s in (-1, 1):
        head.box(f"coif_{s}", (s * 8.6, 54, -11), (1.4, 10, 9), "chain")
    head.box("coif_back", (0, 54, -5.6), (14, 10, 1.4), "chain")


def back_surface(y, b):
    """Rest-space Z of the back at height y: the ribcage plus the crone's hump."""
    return 3 + 6.5 * b + 6 * max(0.0, 1 - ((y - 45) / 8) ** 2)


def make_crystals(torso, d, b):
    kind = d["crystals"]
    back = torso.group("crystals_back", (0, 45, 10))
    glow = back.group("glow_crystals", (0, 46, 14))
    if kind == "ridge":
        # an uneven crest down the spine: staggered sideways, alternating tilt, biggest at the top of the hump
        offsets = (-1.5, 3.5, -4, 1, 4.5, -3, 0, 3, -4.5, 1.5)
        tilts = (-10, 28, -34, 6, 38, -22, 2, 24, -40, 12)
        for i, y in enumerate(range(28, 58, 3)):
            peak = math.exp(-((y - 47) / 6.5) ** 2)
            lit = peak > 0.8
            crystal(glow if lit else back, f"ridge_{i}", (offsets[i] * b, y, back_surface(y, b) - 0.5),
                    25 + 40 * peak + (i % 3) * 5, tilts[i], 4 + 16 * peak + (i % 2) * 2, 2 + 3.4 * peak,
                    "glow" if lit else "crystal")
            if 0.2 < peak and i % 2 == 0:
                geode_patch(back, f"ridge_crust_{i}", (offsets[i] * b * 0.5, y, back_surface(y, b) - 1), (10, 5))
    elif kind == "geode":
        c = (0, 46, back_surface(46, b) - 1)
        for i, a in enumerate(range(0, 360, 45)):
            r = math.radians(a)
            back.box(f"geode_rim_{i}", (c[0] + math.cos(r) * 9, c[1] + math.sin(r) * 7.5, c[2] + 0.5),
                     (7, 6 + (i % 3) * 2, 5 + (i % 2) * 2), "basalt", rotation=(0, 0, a))
        back.box("geode_calcite", c, (15, 12, 4), "calcite")
        shards = ((0, 2, 62, 0, 22, 6, True), (-4, -1, 45, -30, 18, 5, True), (4.5, 0, 50, 32, 17, 5, True),
                  (-2, 5, 78, -12, 14, 4, False), (3, 5, 75, 18, 13, 4, False), (-6, -4, 30, -45, 11, 3.5, False),
                  (6, -4, 32, 48, 10, 3.5, False), (0, -5, 25, 4, 9, 3, False))
        for i, (dx, dy, p, sd, L, w, lit) in enumerate(shards):
            crystal(glow if lit else back, f"geode_shard_{i}", (dx, c[1] + dy, c[2] + 1), p, sd, L, w,
                    "glow" if lit else "crystal")
        for i, (x, y, p, sd) in enumerate(((-2, 33, 30, -20), (3, 36, 35, 25), (9, 50, 60, 40))):
            crystal(back, f"stray_bud_{i}", (x, y, back_surface(y, b) - 0.5), p, sd, 5, 2, "crystal")
    else:  # brute: a smaller cluster on a lower hump; the pauldron carries the rest
        c = (0, 45, back_surface(45, b) - 1)
        geode_patch(back, "brute_crust", c, (14, 9))
        for i, (dx, dy, p, sd, L, w, lit) in enumerate(((0, 1, 60, 0, 16, 5, True), (-4.5, -1, 40, -30, 12, 4, True),
                                                       (4.5, 0, 45, 30, 12, 4, False), (0, 5, 80, 10, 9, 3, False),
                                                       (-2, -4, 25, -10, 7, 2.5, False))):
            crystal(glow if lit else back, f"brute_shard_{i}", (dx, c[1] + dy, c[2] + 1), p, sd, L, w,
                    "glow" if lit else "crystal")


def build(key):
    d = DIRECTIONS[key]
    b = d["bulk"]
    model = Model(f"occultech_volley_crone_{key.lower()}")
    body = model.group("root_body", (0, 21, 2))
    body.box("pelvis", (0, 22, 2), (15 * b, 5, 9 * b), "bone")
    body.box("tailbone", (0, 19, 6), (3, 5, 3), "bone", rotation=(25, 0, 0))
    for s in (-1, 1):
        make_leg(body, s, b)
    # a curved spine: the lower back bends a little, the chest a lot more, so the back rounds into a hump
    waist = body.group("waist", (0, 26, 3), (-d["bend"] * 0.35, 0, 0))
    waist.box("lumbar", (0, 29, 4), (5, 8, 5), "bone")
    waist.box("ribcage_low", (0, 35, 3), (16 * b, 7, 10 * b), "marrow")
    for i in range(2):
        waist.box(f"rib_{i}", (0, 33 + i * 4, 3), (20 * b, 2.2, 13 * b), "bone")
    torso = waist.group("torso", (0, 37, 3), (-d["bend"] * 0.65, 0, 0))
    torso.box("ribcage_core", (0, 43, 3), (17 * b, 11, 11 * b), "marrow")
    for i in range(2, 4):
        torso.box(f"rib_{i}", (0, 33 + i * 4, 3), (21 * b, 2.2, 14 * b), "bone")
    torso.box("sternum", (0, 41, 3 - 7.2 * b), (3, 14, 1.6), "bone")
    torso.box("spine_ridge", (0, 40, 3 + 7.4 * b), (4, 18, 2), "bone")
    torso.box("collarbones", (0, 47, 3), (34 * b, 3, 6), "bone")
    torso.blob("hump", (0, 45, 9), (9 * b, 7, 6), "bone", layers=4)
    for s in (-1, 1):
        torso.box(f"scapula_{s}", (s * 7 * b, 44, 10 + 2 * b), (8 * b, 10, 3), "bone", rotation=(0, s * 15, 0))
    torso.box("breastplate", (-2 * b, 42, 3 - 7.6 * b), (13 * b, 10, 2), "iron", rotation=(0, 0, 6))
    torso.box("gorget", (0, 49.5, 2), (15 * b, 4, 13 * b), "iron")
    beam(torso, "baldric", (-6 * b, 47, 3 - 7.8 * b), (8 * b, 33, 3 - 7.8 * b), 2, "string", depth=1)
    for s in (-1, 1):
        make_arm(torso, s, d, b)
    make_head(torso, d)
    make_crystals(torso, d, b)
    return model


VIEWS = [
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front"},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top", "player": False},
    {"name": "sil_eye", "mode": "silhouette", "camera": "persp", "yaw": 23, "height": 1.62, "dist": 9, "player": False},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": 35, "height": 4.5, "dist": 9},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -22, "height": 1.62, "dist": 8, "player": False},
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 30, "height": 4.5, "dist": 9},
    {"name": "flat_back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 4.5, "dist": 9},
    {"name": "flat_side", "mode": "flat", "camera": "persp", "yaw": 95, "height": 2.2, "dist": 9},
]


def render(key):
    out = OUT / key
    out.mkdir(parents=True, exist_ok=True)
    model = build(key)
    model.write_bbmodel(out / f"occultech_volley_crone_{key.lower()}.bbmodel")
    job = {"boxes": model.render_json(PALETTE), "out": out.as_posix(), "views": VIEWS, "res": [900, 700]}
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps(job), encoding="utf-8")
    result = subprocess.run([str(BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()
    stats = model.stats()
    (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    sheet.direction_sheet(out, f"Volley - {key} {DIRECTIONS[key]['title']}", stats, out / "sheet.png")
    return stats


def main():
    if not BLENDER.is_file():
        raise SystemExit(f"Blender not found: {BLENDER}")
    for key in DIRECTIONS:
        print(key, render(key))
    sheet.compare_sheet(OUT, [(k, v["title"]) for k, v in DIRECTIONS.items()], OUT / "compare.png", subject="Volley")
    sheet.compare_sheet(OUT, [(k, v["title"]) for k, v in DIRECTIONS.items()], OUT / "compare_material.png",
                        subject="Volley", views=("flat_side", "flat_34", "flat_back"))


if __name__ == "__main__":
    main()
