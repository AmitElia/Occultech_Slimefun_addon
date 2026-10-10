"""Volley session 1 revision: a humanoid arbalest bearer, in native Blockbench cuboids.

Run from the repository root: python tools/art/bosses/volley_s1.py
"""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Group, Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s1_silhouettes"
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe")
PALETTE = {
    "iron": RAMPS["iron"][2],
    "bone": RAMPS["bone"][3],
    "chitin": RAMPS["ash"][1],
    "silk": RAMPS["twine"][2],
    "wax": RAMPS["wax"][3],
    "glow": RAMPS["ember"][4],
    "chalk": RAMPS["chalk"][3],
    "flesh": RAMPS["dusk"][2],
}


def beam(group, name, a, b, width, material):
    """Square-section beam pointing along the vector from a to b."""
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    roll = math.degrees(math.atan2(dy, dx))
    yaw = math.degrees(math.atan2(-dz, math.hypot(dx, dy)))
    center = tuple((a[i] + b[i]) / 2 for i in range(3))
    return group.box(name, center, (math.sqrt(dx * dx + dy * dy + dz * dz), width, width), material,
                     rotation=(0, yaw, roll))


def make_leg(body, side):
    s = side
    word = "left" if s < 0 else "right"
    hip = (s * 5.3, 25.5, 0)
    knee = (s * 7.5, 13.2, -1.2)
    ankle = (s * 7.5, 3.5, -2.5)
    thigh = body.group(f"leg_{word}_thigh", hip)
    thigh.box(f"{word}_cuiss", (s * 5.5, 20, 0), (8, 14, 8), "iron")
    thigh.box(f"{word}_upper_bone", (s * 5.5, 18, -4.4), (4.2, 11, 1.4), "bone")
    shin = thigh.group(f"leg_{word}_shin", knee)
    shin.box(f"{word}_knee_guard", knee, (8.8, 5, 9.5), "bone")
    beam(shin, f"{word}_shin", knee, ankle, 5, "iron")
    shin.box(f"{word}_greave_face", (s * 7.5, 8, -5.1), (5.7, 7.5, 1.8), "bone")
    foot = shin.group(f"leg_{word}_foot", ankle)
    foot.box(f"{word}_boot", (s * 7.5, 2.4, -6), (8, 4.8, 14), "iron")
    foot.box(f"{word}_toe_cap", (s * 7.5, 2.1, -12), (8.4, 4.2, 5), "bone")


def make_arm(torso, side):
    s = side
    word = "left" if s < 0 else "right"
    shoulder = (s * 11.5, 44, -0.5)
    # The left arm rests at his side; the right hand grips the off-center stock.
    elbow = (-17, 34, -1) if s < 0 else (19, 35, -5.5)
    wrist = (-14, 23, -2) if s < 0 else (24, 29, -13)
    upper = torso.group(f"arm_{word}_upper", shoulder)
    upper.box(f"{word}_pauldron", (s * 13, 43, -0.5), (10, 8.5, 12), "iron")
    upper.box(f"{word}_pauldron_rim", (s * 13, 46.5, -1), (11, 2.4, 12.5), "bone")
    beam(upper, f"{word}_bicep", shoulder, elbow, 6.2, "chitin")
    forearm = upper.group(f"arm_{word}_forearm", elbow)
    forearm.box(f"{word}_elbow", elbow, (7.5, 7.5, 8), "bone")
    beam(forearm, f"{word}_forearm", elbow, wrist, 5.4, "iron")
    hand = forearm.group(f"arm_{word}_hand", wrist)
    hand.box(f"{word}_grip", wrist, (6.4, 5.5, 5.5), "bone")
    hand.box(f"{word}_wrist_binding", (wrist[0], wrist[1] + 2.4, wrist[2] + 2.4),
             (6.8, 2.2, 2.4), "silk")


def make_lantern(yoke, side):
    s = side
    word = "left" if s < 0 else "right"
    x = s * 18
    lamp = yoke.group(f"ward_lantern_{word}", (x, 58, 7))
    for i in range(3):
        lamp.box(f"{word}_chain_{i}", (x, 56.5 - 2.5 * i, 7), (1.4, 2.7, 1.4), "iron")
    lamp.box(f"{word}_lamp_roof", (x, 49, 7), (8.5, 2, 7), "iron")
    lamp.box(f"{word}_lamp_base", (x, 39, 7), (7.5, 2.5, 6.5), "iron")
    for sx in (-1, 1):
        for sz in (-1, 1):
            lamp.box(f"{word}_lamp_bar_{sx}_{sz}", (x + sx * 3.4, 44, 7 + sz * 2.6),
                     (1.1, 9, 1.1), "iron")
    glow = lamp.group(f"glow_ward_{word}", (x, 44, 7))
    glow.box(f"{word}_wisp", (x, 44, 7), (3.6, 5, 3.6), "glow")
    lamp.box(f"{word}_wax_seal", (x, 45, 3.2), (2.4, 2.4, 0.8), "wax")


def make_crossbow(torso):
    bow = torso.group("bow_aim", (0, 30, -18))
    bow.box("stock", (0, 30, -24), (7.5, 6, 31), "iron")
    bow.box("stock_bone_spine", (0, 34, -25), (3.2, 2.2, 30), "bone")
    bow.box("muzzle", (0, 30, -40), (8.5, 7, 7), "bone")
    bow.box("trigger_housing", (0, 26, -11), (8, 7, 8), "iron")
    limbs = bow.group("bow_draw", (0, 31, -30))
    limbs.box("bow_center", (0, 31, -30), (13, 7, 8), "iron")
    for s in (-1, 1):
        beam(limbs, f"limb_{s}_inner", (s * 5, 31, -30), (s * 14, 33, -30), 4.2, "bone")
        beam(limbs, f"limb_{s}_outer", (s * 14, 33, -30), (s * 24, 38, -27), 3.4, "bone")
        limbs.box(f"limb_{s}_cap", (s * 24, 38, -27), (4, 5, 5), "iron")
        beam(limbs, f"tendon_{s}", (s * 24, 38, -27), (0, 30, -12), 1.2, "silk")
    limbs.box("string_latch", (0, 30, -12), (5, 4, 4), "bone")
    limbs.box("loaded_bolt", (0, 35, -29), (1.8, 1.8, 30), "bone")
    limbs.box("bolt_head", (0, 35, -45), (3.4, 2.5, 4), "iron")
    for s in (-1, 1):
        limbs.box(f"fletching_{s}", (s * 2.7, 35, -15), (5.2, 2, 4), "silk", rotation=(0, s * 25, 0))
    # Blockbench uses rest-space coordinates, so move both pivots and cuboids.
    move_subtree(bow, (26, 0, 0))
    bow.rotation[1] = -12  # muzzle points slightly outward, away from the chest


def move_subtree(group, offset):
    group.origin = [v + d for v, d in zip(group.origin, offset)]
    for child in group.children:
        if isinstance(child, Group):
            move_subtree(child, offset)
        else:
            child.frm = [v + d for v, d in zip(child.frm, offset)]
            child.to = [v + d for v, d in zip(child.to, offset)]
            child.origin = [v + d for v, d in zip(child.origin, offset)]


def build():
    model = Model("occultech_volley_humanoid")
    body = model.group("root_body", (0, 27, 0))
    torso = body.group("torso", (0, 35, 0))
    torso.box("coat_body", (0, 35, 0), (18, 21, 10), "chitin")
    torso.box("breastplate", (0, 37, -5.3), (15, 16, 2.5), "iron")
    torso.box("sternum", (0, 37, -7), (3.4, 15, 1.6), "bone")
    torso.box("collar", (0, 47, -1), (17, 4, 11), "bone")
    torso.box("waist_belt", (0, 26, -1), (20, 3.2, 11.5), "iron")
    torso.box("pelvis", (0, 23.5, 0), (15, 7.5, 10), "iron")
    for s in (-1, 1):
        torso.box(f"coat_tail_{s}", (s * 6, 19, 5), (5, 12, 2.4), "chitin",
                  rotation=(s * 5, 0, s * 8))
        beam(torso, f"chest_binding_{s}", (s * 7, 43, -6.8), (0, 31, -7), 2.3, "silk")
        make_leg(body, s)
        make_arm(torso, s)

    head = torso.group("h_head", (0, 52, 0))
    head.box("neck", (0, 49.5, 0), (5.5, 5, 5.5), "bone")
    head.box("skull", (0, 57, -1), (11, 11, 10), "bone")
    head.box("brow", (0, 59.5, -6.4), (12, 2.4, 2.4), "iron")
    head.box("left_socket", (-2.6, 56.5, -6.5), (3.6, 2.9, 1), "chitin")
    head.box("right_socket", (2.6, 56.5, -6.5), (3.6, 2.9, 1), "chitin")
    eye = head.group("glow_sight", (0, 56.5, -7.1))
    eye.box("sight_ember", (0, 56.5, -7.1), (2.2, 2, 0.8), "glow")
    head.box("nose_bridge", (0, 54, -7), (2.6, 3.5, 2), "bone")
    jaw = head.group("jaw_counter", (0, 52.5, -1))
    jaw.box("mandible", (0, 51.8, -5), (8.5, 2.4, 6), "bone")
    for s in (-1, 1):
        jaw.box(f"jaw_hinge_{s}", (s * 4.2, 53.2, -1), (1.7, 2.6, 2), "bone")
    head.box("iron_crown", (0, 63.3, -1), (12.5, 2.4, 10), "iron")
    for s in (-1, 1):
        head.box(f"crown_point_{s}", (s * 4.2, 66.5, -1), (2.4, 5, 3), "iron")

    yoke = torso.group("binding_yoke", (0, 60, 7))
    yoke.box("back_post", (0, 49, 7), (4.5, 30, 5.5), "iron")
    yoke.box("yoke_crossbar", (0, 62, 7), (38, 4.5, 5.5), "iron")
    yoke.box("central_seal", (0, 62.4, 3.6), (7, 7, 1.5), "wax")
    yoke.box("seal_ember", (0, 62.4, 2.6), (2, 2, 0.8), "glow")
    for s in (-1, 1):
        make_lantern(yoke, s)
    make_crossbow(torso)
    return model


VIEWS = [
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front"},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_top", "mode": "silhouette", "camera": "ortho_top", "player": False},
    {"name": "sil_eye", "mode": "silhouette", "camera": "persp", "yaw": 23, "height": 1.62,
     "dist": 9, "player": False},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": 30, "height": 5.5, "dist": 10},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": -22, "height": 1.62,
     "dist": 8, "player": False},
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": 30, "height": 5.5, "dist": 10},
]


def main():
    if not BLENDER.is_file():
        raise SystemExit(f"Blender not found: {BLENDER}")
    OUT.mkdir(parents=True, exist_ok=True)
    model = build()
    model.write_bbmodel(OUT / "occultech_volley_humanoid.bbmodel")
    job = {"boxes": model.render_json(PALETTE), "out": OUT.as_posix(),
           "views": VIEWS, "res": [900, 700]}
    job_file = OUT / "render_job.json"
    job_file.write_text(json.dumps(job), encoding="utf-8")
    result = subprocess.run([str(BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()
    stats = model.stats()
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    sheet.direction_sheet(OUT, "Volley - humanoid arbalest bearer", stats, OUT / "sheet.png")
    print(stats)


if __name__ == "__main__":
    main()
