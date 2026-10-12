"""Witch Coven redesign, session 2: design lock of the three sisters (plan: docs/art/bosses/witch_coven/overhaul/plan.md).

The direction approved after step 3 (s3_set, 2026-10-11) is rebuilt here as a rig. On top of it, this session:
- uses one body with proper bones: the lower robe, the torso (the stoop), the head, each sleeve, the vessel and
  `glow_` bones for the brew;
- snaps every cube to whole texels;
- sets each witch's hitbox (an invisible `ob_hitbox` bone);
- poses the fight's moments for each sister with her own vessel: the role rotation (all three strike their vessels),
  heal, curse, the throw (bomber) and the death slump;
- lists every part.

A sleeve's rest pose hangs straight down from the shoulder. Its rotation swings it: +x forward, and +z outward for
the right sleeve (-z for the left) while it hangs low. The x turn is applied first, so once a sleeve points up the z
turn swings it the other way: a raised right sleeve goes outward with -z (the throw used +z and swung the bottle
through the face).

Run from the repository root: python tools/art/bosses/coven_s2.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, volley_crone_s2 as v2  # noqa: E402
from bosses.coven_study import K, hat, ragged_hem  # noqa: E402
from bosses.coven_set import PALETTE as SET_PALETTE, bottle, face  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/s2_design"
PALETTE = dict(SET_PALETTE, hitbox=(220, 60, 60),
               hot_green=(210, 255, 170), hot_purple=(232, 190, 255), hot_red=(255, 196, 150))
RW, RD = 13, 10                   # the villager robe (8x20x6, inflated 0.5) at 1.45x, in whole texels
HW, HH = 12, 14                   # the villager head (8x10x8) at 1.45x, in whole texels
WAIST, SHOULDER_Y = (0, 21, 0), 35
STOOP = -11
ARM_LEN = 14
SISTERS = [("cauldron", "green", "the cauldron"), ("bottles", "purple", "the bottles"), ("pot", "red", "the pot")]


def regroup(parent, name, pred):
    """Move the cubes of parent that match pred into a new child bone, pivoting at their centre: the brew in a bottle
    gets a bone of its own, so the fight can tint it without tinting the glass, cork and strap."""
    cubes = [c for c in parent.children if not hasattr(c, "children") and pred(c)]
    lo = np.min([c.frm for c in cubes], 0)
    hi = np.max([c.to for c in cubes], 0)
    g = parent.group(name, ((lo + hi) / 2).tolist())
    for c in cubes:
        parent.children.remove(c)
        g.children.append(c)
        c.group = g
    return g


def chamfered(g, name, c, size, mat, cham):
    """A box with its four long (front-to-back) edges cut at 45 degrees, its cubes put straight on g (no extra bone):
    a cross of two boxes and four diagonal plates filling the notches."""
    (x, y, z), (w, h, d) = c, size
    ch = cham * min(w, h)
    t = ch / 2 ** 0.5
    g.box(name + "_h", c, (w, h - 2 * ch, d), mat)
    g.box(name + "_v", c, (w - 2 * ch, h, d - 1), mat)
    for sa in (-1, 1):
        for sb in (-1, 1):
            g.box(f"{name}_c{sa}{sb}", (x + sa * (w / 2 - 0.75 * ch), y + sb * (h / 2 - 0.75 * ch), z),
                  (ch * 2 ** 0.5, t, d - 0.5), mat, rotation=(0, 0, -45 * sa * sb))


def arm(torso, side, rot, vessel, role):
    """A sleeve hanging from the shoulder (rest: straight down), the dark cuff at its end, and what it holds."""
    word = "right" if side > 0 else "left"
    sx = side * (RW / 2 + 3)
    sh = (sx, SHOULDER_Y, -0.5)
    a = torso.group(f"arm_{word}", sh, rot)
    a.box(f"{word}_shoulder", (sx, SHOULDER_Y - 1, -0.5), (7, 6, 7), "sleeve")
    a.box(f"{word}_sleeve", (sx, SHOULDER_Y - ARM_LEN / 2, -0.5), (6, ARM_LEN - 2, 6), "sleeve")
    a.box(f"{word}_cuff", (sx, SHOULDER_Y - ARM_LEN + 1, -0.5), (8, 3, 8), "cuff")
    end = SHOULDER_Y - ARM_LEN
    if side > 0 and vessel == "cauldron":
        g = a.group("glow_cast", (sx, end - 2.5, -0.5))
        g.box("cast", (sx, end - 2.5, -0.5), (3, 3, 3), f"glow_{role}", rotation=(45, 45, 0))
    if side > 0 and vessel == "bottles":
        # the bottle comes out of the sleeve, its cork pointing away from it (upward when the sleeve is raised)
        held = a.group("bottle_held", (sx, end - 1, -0.5), (180, 0, 0))
        bottle(held, "bottle_held_body", (sx, end + 1.75, -0.5), role, 1.1)      # its base in the cuff
        regroup(held, "glow_brew_held", lambda c: c.mat.startswith("glow_"))
    return a


def build(vessel, role, pose=None):
    pose = pose or {}
    model = Model(f"occultech_coven_{vessel}")
    root = model.group("root", (0, 0, 0))
    lower = root.group("robe_lower", (0, 9, 0))
    lower.box("robe_lower_box", (0, 15.5, 0), (RW, 13, RD), "robe")
    ragged_hem(lower, 9, RW / 2, RD / 2)
    lower.box("herb", (-RW / 2 - 1, 15, -1), (2, 6, 3), "herb", rotation=(0, 0, 6))
    lower.box("charm", (-RW / 2 - 1, 11, 2), (2, 2, 2), "bone")
    torso = root.group("torso", WAIST, (pose.get("torso", STOOP), 0, 0))
    chamfered(torso, "robe_upper", (0, 29.5, 0), (RW, 17, RD), "robe", 0.22)
    torso.box("collar", (0, 37.5, -0.5), (RW - 2, 2, RD - 1), "robe_dark")
    if vessel == "pot":
        # two bones: the carry swings from the shoulders (lifting it for the throw), the vessel tips about the pot
        carry = torso.group("pot_carry", (0, SHOULDER_Y, 0), pose.get("carry", (0, 0, 0)))
        v = carry.group("vessel", (0, 18.5, -14), (pose.get("pot", 0), 0, 0))
    else:
        v = torso.group("vessel", VESSEL_PIVOT[vessel])
    VESSEL_BUILD[vessel](torso, v, role)
    arm(torso, 1, pose.get("right", REST[vessel][0]), vessel, role)
    arm(torso, -1, pose.get("left", REST[vessel][1]), vessel, role)
    head = torso.group("h_head", (0, 38, -1.5), (pose.get("head", -4), 0, 0))
    hc = (0, 38 + HH / 2, -1.5)
    head.box("head", hc, (HW, HH, HW), "skin")
    face(head, hc, HW, HH, hc[2] - HW / 2)
    v2.snap(model)
    return model


def rim(v, name, y, cz, w, d, t, h):
    """A lip round the vessel's mouth: four bars t texels thick, open in the middle so the brew fills the mouth."""
    v.box(f"{name}_n", (0, y, cz - d / 2 + t / 2), (w, h, t), "iron_dark")
    v.box(f"{name}_s", (0, y, cz + d / 2 - t / 2), (w, h, t), "iron_dark")
    v.box(f"{name}_w", (-w / 2 + t / 2, y, cz), (t, h, d - 2 * t), "iron_dark")
    v.box(f"{name}_e", (w / 2 - t / 2, y, cz), (t, h, d - 2 * t), "iron_dark")


def brew(g, y, cz, w, d, role, drips):
    """A bubbling brew: a surface a texel under the lip, domed in the middle, bubbles of several sizes breaking out of
    it, glowing drips over the lip, a few puffs of steam. All on the `glow_brew` bone. The popping rings are painted
    into the surface (session 5): as thin bars they drew bright lines across the brew."""
    glow, hot, steam = f"glow_{role}", f"hot_{role}", f"steam_{role}"
    g.box("brew", (0, y, cz), (w, 1, d), glow)
    g.box("brew_dome", (0, y + 1, cz + 1), (w - 8, 1, d - 8), glow)
    for i, (x, z, s) in enumerate(((-w * 0.28, -d * 0.2, 3), (w * 0.22, d * 0.18, 2), (w * 0.05, -d * 0.3, 2),
                                   (-w * 0.12, d * 0.3, 1), (w * 0.34, -d * 0.05, 1))):
        g.box(f"bubble_{i}", (x, y + 0.5 + s / 2 + (i % 2), cz + z), (s, s, s), hot)
    for i, (x, z, ln) in enumerate(drips):                                                  # spilling over the lip
        g.box(f"drip_{i}", (x, y - ln / 2 - 1, cz + z), (1, ln, 1), glow)
        g.box(f"drip_{i}_top", (x, y + 0.5, cz + z - (1 if z < 0 else -1)), (2, 1, 2), glow)
    for i, (x, z) in enumerate(((-w * 0.22, -d * 0.1), (w * 0.2, d * 0.15))):             # steam puffs rising
        for k, (dy, s, dx) in enumerate(((4, 3, 0), (8, 2, 1), (11, 1, 2))):
            g.box(f"steam_{i}_{k}", (x + dx * (1 if i else -1), y + dy, cz + z), (s, s, s), steam)


def cauldron(torso, v, role):
    cz = RD / 2 + 12
    v.box("cauldron", (0, 25, cz), (24, 20, 22), "iron")
    rim(v, "cauldron_lip", 35.5, cz, 26, 24, 2, 3)
    v.box("cauldron_band", (0, 21, cz), (25, 2, 23), "iron_dark")
    for sx in (-1, 1):
        v.box(f"cauldron_ear_{sx}", (sx * 12.5, 30, cz), (2, 4, 6), "iron_dark")
        for sz in (-1, 1):
            v.box(f"cauldron_leg_{sx}{sz}", (sx * 9.5, 13.5, cz + sz * 8.5), (4, 3, 4), "iron_dark")
    # the brew fills the whole mouth inside the rim, a texel under its top
    g = v.group("glow_brew", (0, 36, cz))
    brew(g, 36, cz, 22, 20, role, drips=((-7, -12.5, 7), (5, 12.5, 5), (13.5, 3, 6)))
    for i, y in enumerate((23, 30)):                       # two ropes round her middle and the cauldron
        torso.box(f"rope_front_{i}", (0, y, -RD / 2 - 0.5), (RW + 2, 1, 1), "rope")
        for sd in (-1, 1):
            torso.box(f"rope_side_{i}_{sd}", (sd * (RW / 2 + 0.5), y, cz / 2 - 0.5), (1, 1, cz + RD / 2 + 3), "rope")
        torso.box(f"rope_back_{i}", (0, y, cz + 11.5), (25, 1, 1), "rope")


def bottles(torso, v, role):
    fz = -RD / 2 - 0.5
    v.box("strap_front", (0, 29, fz), (2, 22, 1), "strap", rotation=(0, 0, -38))
    v.box("strap_back", (0, 29, RD / 2 + 0.5), (2, 22, 1), "strap", rotation=(0, 0, 38))
    v.box("buckle", (0, 29, fz - 0.5), (3, 3, 1), "buckle", rotation=(0, 0, -38))
    for i, t in enumerate((-0.55, 0.0, 0.55)):
        bottle(v, f"bottle_{i}", (8 * t, 28 - 9.5 * t, fz - 3), role, 1.05, rot=(0, 0, -10 + i * 8))
    regroup(v, "glow_brew", lambda c: c.mat.startswith("glow_"))


def pot(torso, v, role):
    """The pot, held at her waist in both sleeves."""
    pz = -14
    v.box("pot", (0, 18.5, pz), (14, 9, 12), "iron")
    rim(v, "pot_lip", 23.5, pz, 15, 13, 1.5, 2)
    v.box("pot_base", (0, 13.5, pz), (10, 2, 8), "iron_dark")
    for sd in (-1, 1):
        v.box(f"pot_handle_{sd}", (sd * 8, 21.5, pz), (2, 2, 5), "iron_dark")
    g = v.group("glow_brew", (0, 24, pz))
    brew(g, 23.5, pz, 12, 10, role, drips=((-3, -7, 5), (4, -7, 3)))


VESSEL_BUILD = {"cauldron": cauldron, "bottles": bottles, "pot": pot}
VESSEL_PIVOT = {"cauldron": (0, 30, RD / 2 + 12), "bottles": (0, 29, -RD / 2)}
# the idle pose of each sleeve (right, left)
REST = {"cauldron": ((72, 0, 6), (18, 0, -6)), "bottles": ((105, 0, 10), (16, 0, -6)), "pot": ((62, 0, -14), (62, 0, 14))}

# the fight's moments: rotations per bone (torso pitch, head pitch, pot swing, sleeves)
POSES = {
    "idle": ("idle", {}),
    "rotation": ("the role rotation: she strikes her vessel", {
        "cauldron": {"right": (-150, 0, -16), "head": 6},
        "bottles": {"right": (55, 0, -42), "left": (55, 0, 30)},
        "pot": {"right": (88, 0, -20), "pot": -8}}),
    "heal": ("heal: brew poured towards her sister", {
        "cauldron": {"right": (70, 0, 75), "left": (40, 0, -40)},
        "bottles": {"right": (160, 0, -38), "head": 10},
        "pot": {"carry": (18, 0, 0), "pot": -40, "right": (80, 0, -12), "left": (80, 0, 12), "torso": -14}}),
    "curse": ("curse: cast down onto the marked floor", {
        "cauldron": {"torso": -26, "right": (38, 0, 4), "left": (38, 0, -4), "head": -10},
        "bottles": {"torso": -22, "right": (40, 0, 4), "head": -10},
        "pot": {"torso": -24, "carry": (10, 0, 0), "pot": -80, "right": (72, 0, -12), "left": (72, 0, 12), "head": -10}}),
    "throw": ("the throw (bomber): wound up to hurl (the pot heaved up beside her head)", {
        "cauldron": {"torso": -2, "right": (176, 0, -42), "head": 8},
        "bottles": {"torso": -2, "right": (176, 0, -42), "head": 8},
        "pot": {"torso": -4, "carry": (70, -75, 0), "right": (110, -53, 0), "left": (100, -75, 0), "head": 6}}),
    "death": ("death: she slumps", {
        "cauldron": {"torso": -52, "head": -28, "right": (8, 0, 4), "left": (8, 0, -4)},
        "bottles": {"torso": -52, "head": -28, "right": (8, 0, 4), "left": (8, 0, -4)},
        "pot": {"torso": -52, "head": -28, "right": (14, 0, 4), "left": (14, 0, -4), "carry": (-24, 0, 0), "pot": 28}}),
}


def in_subtree(cube, names):
    g = cube.group
    while g is not None:
        if g.name in names:
            return True
        g = g.parent
    return False


def hitbox_bounds(model):
    """A column over the body from the floor to the top of the head: the robe, torso and head, the same for all
    three. The hat, the sleeves and the vessel are left out, so the cauldron can't be hit from behind for free."""
    pts = np.vstack([c.corners() for c in model.cubes
                     if not in_subtree(c, {"hat", "vessel", "arm_right", "arm_left"})])
    lo, hi = pts.min(0), pts.max(0)
    cz = float(np.round((lo[2] + hi[2]) / 2))
    half = 10.0                                   # 1.25 blocks across
    return (-half, 0.0, cz - half), (half, float(np.ceil(hi[1])), cz + half)


def parts_list(model):
    rows = []
    for g in model.groups:
        cubes = [c for c in g.children if not hasattr(c, "children")]
        if cubes:
            mats = sorted({c.mat for c in cubes})
            rows.append(f"| `{g.name}` | {g.parent.name if g.parent.name != 'root' else '-'} | {len(cubes)} | {', '.join(mats)} |")
    return "\n".join(["| Bone | Parent | Cubes | Materials |", "|---|---|---|---|"] + rows)


POSE_VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": -38, "height": 2.6, "dist": 7, "target_z": 1.9},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
]
MAIN_VIEWS = m1.VIEWS


def main():
    if OUT.exists():                              # regenerate everything but the hand-written README
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name not in ("README.md", "brew.png"):
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    parts = ["# Witch Coven blockout parts (session 2)\n", "Generated by `tools/art/bosses/coven_s2.py`. Cube sizes are "
             "whole texels.\n"]
    hit_boxes, items = [], []
    for i, (vessel, role, title) in enumerate(SISTERS):
        out = OUT / vessel
        model = build(vessel, role)
        frm, to = hitbox_bounds(model)
        bb = model.to_bbmodel()
        add_hitbox(bb, frm, to)
        out.mkdir()
        (out / f"occultech_coven_{vessel}_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
        v2.run_blender(model.render_json(PALETTE), out, MAIN_VIEWS)
        stats = model.stats()
        stats["hitbox_blocks"] = [round((t - f) / 16, 2) for f, t in zip(frm, to)]
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        sheet.direction_sheet(out, f"Witch Coven - {title} (design lock)", stats, out / "sheet.png")
        report[vessel] = stats
        parts += [f"\n## {title.capitalize()}\n\n", parts_list(model) + "\n"]
        # the hitbox drawn as a solid red box over the model
        boxes = model.render_json(PALETTE) + [v2.box_json("hitbox", frm, to, "hitbox")]
        for b in boxes[:-1]:
            b["color"] = [c * 0.55 + 0.4 for c in b["color"]]
        hit_boxes += [dict(b, corners=(np.array(b["corners"]) + [(i - 1) * 40, 0, 0]).tolist()) for b in boxes]
        # the key poses
        for key, (label, per) in POSES.items():
            posed = build(vessel, role, per.get(vessel, {}))
            v2.run_blender(posed.render_json(PALETTE), out / "poses" / key, POSE_VIEWS)
        sheet.compare_sheet(out / "poses", [(k, "") for k in POSES], out / "poses.png",
                            heading=f"Witch Coven - {title}: idle, rotation, heal, curse, throw, death",
                            views=("flat_34", "sil_side"))
        items.append((vessel, title))
        print(vessel, stats["cubes"], stats["bones_with_geometry"], stats["size_blocks"], stats["hitbox_blocks"])
    v2.run_blender(hit_boxes, OUT / "hitbox", [{"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
                                               {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"}])
    sheet.compare_sheet(OUT, items, OUT / "design.png", heading="Witch Coven - design lock (session 2)",
                        views=("flat_34", "flat_front", "sil_side", "clay_34"))
    (OUT / "parts.md").write_text("".join(parts), encoding="utf-8")
    (OUT / "stats.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    from PIL import Image
    a, b = (Image.open(OUT / "hitbox" / f"hitbox_{v}.png") for v in ("front", "side"))
    both = Image.new("RGB", (a.width + b.width + 10, a.height), sheet.BG)
    both.paste(a, (0, 0))
    both.paste(b, (a.width + 10, 0))
    both.save(OUT / "hitbox.png")


if __name__ == "__main__":
    main()
