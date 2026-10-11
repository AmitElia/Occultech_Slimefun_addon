"""Volley redesign, session 2: design lock and blockout of the Amethyst Crone.

The chosen direction combines A's deep curved stoop, B's cracked geode on the hump and C's heavy arms. On top of
session 1 this session:
- snaps every cube to whole texels (one texel per model unit, 16 per block);
- carries the arbalest at hip height;
- sets the hitbox (an invisible `ob_hitbox` bone);
- poses the key moments as silhouettes;
- lists every part.

Run from the repository root: python tools/art/bosses/volley_crone_s2.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as s1  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/overhaul/s2_design"
BLENDER = s1.BLENDER
PALETTE = dict(s1.PALETTE, hitbox=(220, 60, 60))

BEND = 46                    # A's stoop, split over the curved spine
BODY, ARMS, LEGS = 1.2, 1.45, 1.15
ARBALEST = 1.45   # the weapon is scaled up about the fist: a 3-block prod, a 2.7-block stock


def make_arm(torso, s):
    word = "left" if s < 0 else "right"
    sx = 17 * BODY + 2
    shoulder, elbow, wrist = (s * sx, 46, 3), (s * (sx + 1), 30, 3), (s * (sx + 1), 15, 3)
    pose = (BEND + 18, 0, s * 8) if s < 0 else (BEND + 6, 0, s * 12)
    upper = torso.group(f"arm_{word}_upper", shoulder, pose)
    upper.box(f"{word}_shoulder_ball", shoulder, (9 * ARMS, 9, 9 * ARMS), "bone")
    s1.beam(upper, f"{word}_humerus", shoulder, elbow, 6.5 * ARMS, "bone")
    upper.box(f"{word}_spur", (s * (sx + 5 * ARMS), 38, 4), (2, 5, 2), "bone", rotation=(0, 0, s * 30))
    # the weapon forearm swings up so the fist rides at the hip, not at the shin
    fore = upper.group(f"arm_{word}_forearm", elbow, (12, 0, 0) if s < 0 else (68, 0, 6))
    fore.box(f"{word}_elbow", elbow, (8.5 * ARMS, 8, 8.5 * ARMS), "bone")
    s1.beam(fore, f"{word}_ulna", elbow, wrist, 6 * ARMS, "bone")
    hand = fore.group(f"arm_{word}_hand", wrist)
    hand.box(f"{word}_palm", (wrist[0], wrist[1] - 3, wrist[2]), (9 * ARMS, 6, 9 * ARMS), "bone")
    for i, dz in enumerate((-3, 0, 3)):
        hand.box(f"{word}_finger_{i}", (wrist[0] + s, wrist[1] - 8, wrist[2] + dz * ARMS), (3, 5, 3), "bone")
    if s > 0:
        fore.box("right_bracer", (wrist[0], 22, 3), (9 * ARMS, 9, 9 * ARMS), "iron")
        fore.box("right_bracer_rim", (wrist[0], 26.5, 3), (10 * ARMS, 2, 10 * ARMS), "chain")
        s1.make_arbalest(hand, wrist, tilt=12, k=ARBALEST)
    else:
        s1.make_pauldron(upper, shoulder, ARMS, False)


def snap(model):
    """Whole-texel cube sizes: each face then maps to a whole number of texels (positions may sit on half units)."""
    for c in model.cubes:
        lo, hi = np.array(c.frm), np.array(c.to)
        center, size = (lo + hi) / 2, np.maximum(1, np.round(hi - lo))
        c.frm, c.to = (center - size / 2).tolist(), (center + size / 2).tolist()


def build():
    b = BODY
    model = Model("occultech_volley")
    body = model.group("root_body", (0, 21, 2))
    body.box("pelvis", (0, 22, 2), (15 * b, 5, 9 * b), "bone")
    body.box("tailbone", (0, 19, 6), (3, 5, 3), "bone", rotation=(25, 0, 0))
    for s in (-1, 1):
        s1.make_leg(body, s, LEGS)
    waist = body.group("waist", (0, 26, 3), (-BEND * 0.35, 0, 0))
    waist.box("lumbar", (0, 29, 4), (5, 8, 5), "bone")
    waist.box("ribcage_low", (0, 35, 3), (16 * b, 7, 10 * b), "marrow")
    for i in range(2):
        waist.box(f"rib_{i}", (0, 33 + i * 4, 3), (20 * b, 2, 13 * b), "bone")
    torso = waist.group("torso", (0, 37, 3), (-BEND * 0.65, 0, 0))
    # the dark core stops a texel under the collarbones and gorget: their tops no longer share a plane (the neck flicker)
    torso.box("ribcage_core", (0, 42.5, 3), (17 * b, 10, 11 * b), "marrow")
    for i in range(2, 4):
        torso.box(f"rib_{i}", (0, 33 + i * 4, 3), (21 * b, 2, 14 * b), "bone")
    torso.box("sternum", (0, 43, 3 - 7.2 * b), (3, 10, 2), "bone")
    torso.box("spine_ridge", (0, 40, 3 + 7.4 * b), (4, 18, 2), "bone")
    torso.box("collarbones", (0, 47, 3), (34 * b + 4, 3, 6), "bone")
    torso.blob("hump", (0, 45, 9), (9 * b, 7, 6), "bone", layers=5, axes=("y",))
    for s in (-1, 1):
        torso.box(f"scapula_{s}", (s * 7 * b, 44, 10 + 2 * b), (8 * b, 10, 3), "bone", rotation=(0, s * 15, 0))
    torso.box("breastplate", (-2 * b, 42, 3 - 7.6 * b), (13 * b, 10, 2), "iron", rotation=(0, 0, 6))
    # the collar sits low and behind the neck, clear of the skull and jaw hanging forward of it
    torso.box("gorget", (0, 47, 5.5), (15 * b, 5, 14), "iron")
    s1.beam(torso, "baldric", (-6 * b, 47, 3 - 7.8 * b), (8 * b, 33, 3 - 7.8 * b), 2, "string", depth=1)
    for s in (-1, 1):
        make_arm(torso, s)
    s1.make_head(torso, {"bend": BEND})
    s1.make_crystals(torso, {"crystals": "geode"}, b)
    # the crystal bones turn and grow from the geode's root, so a flare scales them out of the hump
    root = [0.0, 46.0, s1.back_surface(46, b) - 1]
    for g in model.groups:
        if g.name in ("crystals_back", "glow_crystals"):
            g.origin = list(root)
    snap(model)
    return model


def in_subtree(cube, names):
    g = cube.group
    while g is not None:
        if g.name in names:
            return True
        g = g.parent
    return False


def hitbox_bounds(model):
    """A square column over the body's mass, from the feet to the top of the hump; arbalest and crystals left out.

    The arms and the pauldron reach past it, but the hunched chest, head and hump are inside, so every part a player
    aims at in the middle of the fight counts.
    """
    pts = np.vstack([c.corners() for c in model.cubes if not in_subtree(c, {"arbalest", "crystals_back"})])
    lo, hi = pts.min(0), pts.max(0)
    cz = float(np.round((lo[2] + hi[2]) / 2))
    half = 20.0                                   # 2.5 blocks across
    return (-half, 0.0, cz - half), (half, float(np.ceil(hi[1])), cz + half)


POSES = {
    "idle": ("idle: the arbalest carried at the hip", {}),
    "aim": ("aim: the volley (arbalest raised, braced on the left forearm)", {
        "arm_right_upper": (BEND + 70, 0, 4), "arm_right_forearm": (14, 0, 0), "arbalest": (6, 0, 0),
        "arm_left_upper": (BEND + 62, 0, 22), "arm_left_forearm": (48, 0, 0), "h_head": (BEND * 0.55, 0, 0)}),
    "wards": ("wards: he rears up and the geode flares", {
        "waist": (-BEND * 0.12, 0, 0), "torso": (-BEND * 0.4, 0, 0), "h_head": (BEND * 0.75, 0, 0),
        "arm_left_upper": (BEND * 0.55, 0, -55), "arm_right_upper": (BEND * 0.55, 0, 48),
        "arm_left_forearm": (25, 0, 0), "arm_right_forearm": (75, 0, 6)}),

}

VIEWS = s1.VIEWS
POSE_VIEWS = [
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_eye", "mode": "silhouette", "camera": "persp", "yaw": 23, "height": 1.62, "dist": 9, "player": False},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": 35, "height": 4.5, "dist": 9},
]
HITBOX_VIEWS = [
    {"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
    {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"},
]


def run_blender(boxes, out, views):
    out.mkdir(parents=True, exist_ok=True)
    job_file = out / "render_job.json"
    job_file.write_text(json.dumps({"boxes": boxes, "out": out.as_posix(), "views": views, "res": [900, 700]}),
                        encoding="utf-8")
    result = subprocess.run([str(BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_render.py"), "--", str(job_file)],
                            capture_output=True, text=True)
    if result.returncode or "RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job_file.unlink()


def box_json(name, frm, to, mat):
    lo, hi = np.array(frm), np.array(to)
    corners = [[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    return {"name": name, "mat": mat, "color": [v / 255 for v in PALETTE[mat][:3]], "corners": corners}


def parts_list(model):
    rows = []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            rows.append(f"| `{g.name}` | {g.parent.name if g.parent.name != 'root' else '-'} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


def main():
    if not BLENDER.is_file():
        raise SystemExit(f"Blender not found: {BLENDER}")
    model = build()
    frm, to = hitbox_bounds(model)
    bb = model.to_bbmodel()
    add_hitbox(bb, frm, to)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "occultech_volley_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")

    run_blender(model.render_json(PALETTE), OUT, VIEWS)
    stats = model.stats()
    stats["hitbox_blocks"] = [round((t - f) / 16, 2) for f, t in zip(frm, to)]
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    sheet.direction_sheet(OUT, "Volley - design lock", stats, OUT / "sheet.png")

    # the hitbox drawn as a solid red box over the model, front and side
    boxes = model.render_json(PALETTE) + [box_json("hitbox", frm, to, "hitbox")]
    for b in boxes[:-1]:
        b["color"] = [v * 0.55 + 0.4 for v in b["color"]]
    run_blender(boxes, OUT / "hitbox", HITBOX_VIEWS)

    for key, (title, rotations) in POSES.items():
        posed = build()
        groups = {g.name: g for g in posed.groups}
        for name, rot in rotations.items():
            groups[name].rotation = [float(v) for v in rot]
        run_blender(posed.render_json(PALETTE), OUT / "poses" / key, POSE_VIEWS)
    sheet.compare_sheet(OUT / "poses", [(k, "") for k in POSES], OUT / "poses.png",
                        heading="Volley - key poses (session 2)")
    (OUT / "parts.md").write_text("# Volley blockout parts (session 2)\n\nGenerated by `tools/art/bosses/volley_crone_s2.py`."
                                  " Cube sizes are whole texels.\n\n" + parts_list(model) + "\n", encoding="utf-8")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
