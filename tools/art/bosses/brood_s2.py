"""Brood Mother redesign, session 2: design lock and blockout.

Chosen in the session 1 review: B's body (the brute: the heaviest head, thorax and abdomen, the biggest wax load) on
C's legs (the stalker's: long, the knees far above her back). Added in the review:
- tarantula fur as 2D hair: flat cards (zero-thickness cubes), two crossed along each leg segment, fringes down
  the flanks of the thorax and abdomen and a beard round the jaws, to carry an alpha hair texture in session 5;
- melted candles on the rest of her too: on the head, the thorax and three knees, and two stuck into her flank.

On top of that this session:
- snaps every cube to whole texels (one texel per model unit, 16 per block; hair cards keep their zero thickness);
- puts the candles of an area in one bone and their flames in one glow_ bone (take 3 had a bone per candle);
- sets the hitbox (an invisible ob_hitbox bone);
- poses the key moments (pounce, bite, egg sac, web) as silhouettes;
- lists every part.

Run from the repository root: python tools/art/bosses/brood_s2.py
"""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, add_hitbox, leg  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s1 as s1, volley_crone_s2 as v2  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s2_design"
PALETTE = dict(s1.PALETTE, hair=RAMPS["leather"][2], hitbox=(220, 60, 60))
v2.PALETTE = PALETTE   # v2's renderer and hitbox box read its module palette

HEAD, THORAX, ABDOMEN, THORAX_Y = (23, 20, 22), (25, 17, 20), (37, 28, 38), 18   # B
LEG_LEN, LEG_THICK, FEMUR = 1.25, 1.05, 66                                       # C's reach, a little thicker
WAX = 22
SEGMENTS = ("coxa", "femur", "patella", "tibia", "metatarsus", "tarsus")
# hair length past the chitin per segment; the coxa and the tarsus stay bare
LEG_HAIR = {1: 3.0, 2: 3.0, 3: 2.5, 4: 2.0}
KNEE_CANDLES = ("leg_r1", "leg_l0", "leg_l2")


def candle(body, glow, name, base, height, width, tilt=(0, 0, 0), melted=False):
    """A candle as cubes in the area's bone, its flame in the area's glow bone. A lean is a cube rotation about the
    candle's foot (one axis, 22.5 degrees: free for BetterModel). A melted candle is short, sits in a puddle and runs
    over."""
    x, y, z = base
    pivot = (x, y, z)
    body.box(f"{name}_body", (x, y + height / 2 - 1, z), (width, height + 2, width), "candle", tilt, pivot)
    body.box(f"{name}_collar", (x, y + height - 1.5, z), (width + 1, 1, width + 1), "wax", tilt, pivot)
    body.box(f"{name}_drip", (x + width / 2 + 0.5, y + height - 3.5, z), (1, 4, 1), "wax", tilt, pivot)
    body.box(f"{name}_wick", (x, y + height + 0.5, z), (1, 2, 1), "wick", tilt, pivot)
    glow.box(f"{name}_flame", (x, y + height + 2.5, z), (2, 3, 2), "flame", tilt, pivot)
    if melted:
        body.box(f"{name}_puddle", (x + 0.5, y + 0.5, z - 0.5), (width + 4, 1, width + 3), "wax")
        body.box(f"{name}_run", (x - width / 2 - 0.5, y + height * 0.4, z + 0.5), (1, height * 0.8, 2), "wax", tilt, pivot)


def wax_mountain(abdomen, top_y, cz, half_w, half_d, side_h, height, seed):
    """Take 3's heap of melted wax lumps with flows down the flanks; the cap now sits inside the abdomen's bevel, so no
    flat ledge shows. All candles in one bone, all flames in one glow bone."""
    rnd = random.Random(seed)
    pile = abdomen.group("wax_pile", (0, top_y, cz))
    glow = pile.group("glow_pile_flames", (0, top_y + height, cz))
    pile.box("wax_cap", (0, top_y, cz), (2 * half_w - 8, 2, 2 * half_d - 8), "wax_old")
    spots = [(0.05, 0.22, 0.62, 0.62, 0.55), (-0.3, 0.45, 0.42, 0.85, 0.36), (0.38, 0.5, 0.36, 0.55, 0.32),
             (0.45, -0.3, 0.4, 0.42, 0.34), (-0.48, -0.15, 0.4, 0.5, 0.36), (-0.05, -0.5, 0.42, 0.34, 0.3),
             (0.12, 0.62, 0.3, 1.0, 0.26), (-0.55, 0.62, 0.3, 0.4, 0.28)]
    lumps = []
    for i, (fx, fz, frx, fh, frz) in enumerate(spots):
        x, z = fx * half_w + rnd.uniform(-1, 1), cz + fz * half_d + rnd.uniform(-1, 1)
        r = (frx * half_w, fh * height * 0.55, frz * half_d)
        y = top_y + 1 + (fh * height * 0.35 if fh > 0.8 else 0)
        pile.blob(f"wax_lump_{i}", (x, y, z), r, "wax" if i % 3 else "wax_old", layers=6, axes=("y",))
        lumps.append((x, y, z, r))
    for i, (side, f) in enumerate(((1, 0.1), (1, 0.6), (-1, -0.2), (-1, 0.45), (0, 1), (1, -0.5), (-1, 0.85))):
        drop, width, out = side_h * rnd.uniform(0.45, 0.8), rnd.uniform(5, 8), rnd.uniform(0.5, 1.0)
        for j, (wf, hf) in enumerate(((1.0, 0.3), (0.72, 0.4), (0.45, 0.3))):
            seg_top = top_y + 1 - drop * (0, 0.3, 0.7)[j]
            h = drop * hf + 1
            if side:
                c, sz = (side * (half_w + out + j), seg_top - h / 2, cz + f * half_d), (2, h, width * wf)
            else:
                c, sz = (rnd.uniform(-0.4, 0.4) * half_w, seg_top - h / 2, cz + half_d + out + j), (width * wf, h, 2)
            pile.box(f"wax_flow_{i}_{j}", c, sz, "wax" if j else "wax_old")
    k = 0
    for i, (x, y, z, r) in enumerate(lumps):
        count = 1 + (i % 3) + (1 if r[1] > height * 0.4 else 0)
        tall = 4 + r[1] * 0.75
        for j in range(count):
            if j == 0:
                cx, cz2, h, f = x, z, tall, 0.0
            else:
                a = seed + j * 2.4 + i
                f = rnd.uniform(0.35, 0.6)
                cx, cz2, h = x + math.cos(a) * r[0] * f, z + math.sin(a) * r[2] * f, tall * rnd.uniform(0.3, 0.65)
            tilt = (0, 0, 0) if j == 0 or rnd.random() < 0.6 else rnd.choice(((22.5, 0, 0), (-22.5, 0, 0), (0, 0, 22.5)))
            candle(pile, glow, f"candle_{k}", (cx, y + r[1] * math.sqrt(1 - f * f) - 1.8, cz2), max(3, h),
                   4 if j == 0 else rnd.choice((3, 3, 4)), tilt)
            k += 1


def comb(group, name, along, fixed, y_range, length, out_axis, spacing, rnd):
    """A fringe of fur down a flat side: overlapping hair cards (zero-thickness planes) a hand's width each, hung just
    off the surface from a ragged top line and flared out at the bottom (a 22.5 degree turn about the card's top).
    With the alpha hair texture each card is a curtain of hairs. along: (axis, from, to); fixed: the surface
    coordinate on out_axis (its sign is the way out)."""
    axis, a0, a1 = along
    sign = 1 if fixed > 0 else -1
    pos, i = a0, 0
    while pos < a1:
        piece = min(rnd.uniform(4, 6), a1 - pos + 1)
        top = rnd.uniform(*y_range)
        drop = length * rnd.uniform(1.1, 1.6)
        mid = pos + piece / 2
        off = fixed + sign * (0.5 + (i % 2) * 0.5)   # alternate planes: neighbouring cards never share one
        if out_axis == "x":
            c, sz, rot, pivot = (off, top - drop / 2, mid), (0, drop, piece), (0, 0, sign * 22.5), (off, top, mid)
        else:
            c, sz, rot, pivot = (mid, top - drop / 2, off), (piece, drop, 0), (-sign * 22.5, 0, 0), (mid, top, off)
        group.box(f"{name}_{i}", c, sz, "hair", rot, pivot)
        pos += piece * 0.8
        i += 1


def hairy_leg(thorax, name, hip, yaw, segs, rnd):
    """C's long leg on B's body, furred like a tarantula's: on the femur, patella, tibia and metatarsus two hair cards
    the length of the segment cross along its axis (an X in section, turned 45 degrees about it), standing out past
    the chitin on every side, so the leg has a fuzzy outline from every angle once the alpha texture is on."""
    bones = leg(thorax, name, hip, yaw, segs, ground=0.0, mat="chitin", knuckle_mat="chitin_lit", joint_scale=1.25,
                bristles=0)
    x = hip[0]
    for i, (length, _, t) in enumerate(segs):
        if i in LEG_HAIR and length:
            hl = LEG_HAIR[i]
            span = t + 2 * hl
            for r in (45, -45):
                bones[i + 1].box(f"{name}_{i}_fur_{'a' if r > 0 else 'b'}", (x + length / 2, hip[1], hip[2]),
                                 (length - 1, span, 0), "hair", (r, 0, 0))
        x += length or 0
    return bones


def knee_candle(bones, name, hip, segs):
    """A melted candle on top of the knee (the patella, which lies level), wax set round the joint and run down the
    leg; its flame in a small glow bone of its own so it moves with the knee."""
    x = hip[0] + segs[0][0] + segs[1][0]
    length, _, t = segs[2]
    patella = bones[3]
    top = hip[1] + t / 2
    glow = patella.group(f"glow_{name}_knee", (x + length / 2, top + 6, hip[2]))
    candle(patella, glow, f"{name}_knee_candle", (x + length / 2, top - 0.5, hip[2]), 5, 3, melted=True)
    patella.box(f"{name}_knee_wax", (x, top - 0.5, hip[2]), (t * 1.6, 3, t * 1.6), "wax")
    patella.box(f"{name}_knee_drip", (x + length * 0.8, hip[1] - t / 2 - 2, hip[2]), (2, 6, 2), "wax_old")


def legs(thorax, ty, tw, td, rnd):
    for side in (1, -1):
        for i in range(4):
            yaw = (52, 22, -14, -48)[i]
            ls = (1.0, 0.88, 0.8, 0.95)[i] * LEG_LEN
            hip = (side * (tw / 2 - 1.5), ty - 1.5, -td * 0.33 + i * td * 0.22)
            segs = [(4 * ls, 18, 5.6 * LEG_THICK), (26 * ls, FEMUR, 5.6 * LEG_THICK), (6 * ls, 4, 5.0 * LEG_THICK),
                    (22 * ls, -34, 4.2 * LEG_THICK), (18 * ls, -60, 3.0 * LEG_THICK), (None, -76, 2.0 * LEG_THICK)]
            name = f"leg_{'r' if side > 0 else 'l'}{i}"
            bones = hairy_leg(thorax, name, hip, yaw if side > 0 else 180 - yaw, segs, rnd)
            if name in KNEE_CANDLES:
                knee_candle(bones, name, hip, segs)


def build():
    rnd = random.Random(7)
    (hw, hh, hd), (tw, th, td), (aw, ah, ad), ty = HEAD, THORAX, ABDOMEN, THORAX_Y
    model = Model("occultech_brood_mother")
    body = model.group("root_body", (0, ty, 0))
    thorax = body.group("thorax", (0, ty, 0))
    s1.rounded_box(thorax, "thorax", (0, ty, 0), (tw, th, td), "chitin", 1.5)
    thorax.box("thorax_plate", (0, ty + th / 2 + 0.5, -1), (tw * 0.55, 1, td * 0.7), "plate")
    for s in (-1, 1):
        thorax.box(f"hump_{s}", (s * tw * 0.26, ty + th / 2 + 1, -td * 0.15), (tw * 0.32, 3, td * 0.5), "chitin_lit")
    # melted candles on the carapace, between the humps
    tglow = thorax.group("glow_thorax_flames", (0, ty + th / 2 + 8, 2))
    for i, (x, z, h, w) in enumerate(((0, 3, 6, 3), (-3, 6, 4, 3), (3, 7, 3, 3))):
        candle(thorax, tglow, f"thorax_candle_{i}", (x, ty + th / 2 + 1, z), h, w, melted=True)
    for s in (-1, 1):   # hair along the thorax flanks, under the leg roots
        comb(thorax, f"thorax_hair_{s}", ("z", -td / 2 + 2, td / 2 - 2), s * tw / 2, (ty - th / 2 + 1, ty - th / 2 + 4),
             4, "x", 3, rnd)
    legs(thorax, ty, tw, td, rnd)

    az, ay = td / 2 + ad / 2 + 1, ty + ah * 0.28
    abdomen = body.group("abdomen", (0, ty, td / 2))
    abdomen.box("pedicel", (0, ty + 1, td / 2 + 1), (tw * 0.4, th * 0.5, 5), "chitin_lit")
    s1.rounded_box(abdomen, "abdomen", (0, ay, az), (aw, ah, ad), "chitin", 3)
    s1.rounded_box(abdomen, "abdomen_swell", (aw * 0.14, ay - ah * 0.12, az + ad * 0.1), (aw * 0.9, ah * 0.72, ad * 0.6),
                   "chitin_lit", 2)
    abdomen.box("spinnerets", (0, ay - ah * 0.22, az + ad / 2 + 1), (aw * 0.26, ah * 0.26, 3), "chitin_lit")
    for i in range(3):
        abdomen.box(f"flank_plate_{i}", (-aw / 2 - 0.5, ay - ah * 0.05 - i * 2.5, az - ad * 0.2 + i * ad * 0.2),
                    (1, 2, ad * 0.16), "plate")
    # the tarantula's fur: two combs down each flank under the wax, one round the back above the spinnerets
    for s in (-1, 1):
        edge = s * (aw / 2 + (2 if s > 0 else 0))   # the swelling bulges the right flank out
        comb(abdomen, f"abdomen_hair_{s}_low", ("z", az - ad / 2 + 3, az + ad / 2 - 3), edge,
             (ay - ah / 2 + 3, ay - ah * 0.15), 5, "x", 3, rnd)
        comb(abdomen, f"abdomen_hair_{s}_high", ("z", az - ad / 2 + 4, az + ad / 2 - 4), s * aw / 2,
             (ay - ah * 0.05, ay + ah * 0.25), 4, "x", 4, rnd)
    comb(abdomen, "abdomen_hair_back", ("x", -aw / 2 + 3, aw / 2 - 3), az + ad / 2, (ay - ah * 0.05, ay + ah * 0.3), 4,
         "z", 3.5, rnd)
    # two candles stuck into her left flank, melted and drooping, their flames in one glow bone
    fglow = abdomen.group("glow_flank_flames", (-aw / 2 - 6, ay + 4, az))
    for i, (z, y, h) in enumerate(((az - 6, ay + 3, 7), (az + 7, ay - 2, 5))):
        candle(abdomen, fglow, f"flank_candle_{i}", (-aw / 2 + 1, y, z), h, 3, (0, 0, 45), melted=False)
        abdomen.box(f"flank_candle_{i}_wax", (-aw / 2 - 1, y - 1, z), (3, 6, 5), "wax")
    wax_mountain(abdomen, ay + ah / 2 - 1, az, aw / 2, ad / 2, ah, WAX, seed=ord("B"))

    hz, hy = -td / 2 - hd / 2 + 2, ty - hh * 0.12
    head = thorax.group("h_head", (0, hy, -td / 2))
    head.box("head", (0, hy, hz), (hw, hh, hd), "chitin")
    head.box("head_brow", (0, hy + hh * 0.4, hz - hd * 0.06), (hw + 1, hh * 0.16, hd * 0.9), "chitin_lit")
    s1.eyes(head, hy, hz - hd / 2 - 0.2, hw, hh)
    s1.jaws(head, hy, hz - hd / 2, hw, hh)
    for s in (-1, 1):   # the beard: hair round the jaws and down the cheeks
        comb(head, f"cheek_hair_{s}", ("z", hz - hd / 2 + 2, hz + hd / 2 - 3), s * hw / 2, (hy - hh / 2 + 2, hy - hh * 0.1),
             4, "x", 3, rnd)
    comb(head, "jaw_beard", ("x", -hw / 2 + 2, hw / 2 - 2), hz - hd / 2, (hy - hh / 2 + 1, hy - hh / 2 + 4), 4, "z", 3, rnd)
    # melted candles on the back corners of the head, wax run down over its sides; clear of the eyes
    hglow = head.group("glow_head_flames", (0, hy + hh / 2 + 8, hz + hd * 0.3))
    for i, (s, h) in enumerate(((1, 5), (-1, 3))):
        x, z = s * hw * 0.32, hz + hd * 0.28
        candle(head, hglow, f"head_candle_{i}", (x, hy + hh / 2 + 1, z), h, 3, melted=True)
        head.box(f"head_wax_run_{i}", (s * (hw / 2 + 0.5), hy + hh / 2 - 4, z), (1, 8, 3), "wax")
    snap(model)
    return model


def snap(model):
    """Whole-texel cube sizes, so each face maps to whole texels; hair cards keep their zero thickness."""
    for c in model.cubes:
        lo, hi = np.array(c.frm), np.array(c.to)
        center, size = (lo + hi) / 2, np.round(hi - lo)
        size = np.where(hi - lo < 0.01, 0, np.maximum(1, size))
        c.frm, c.to = (center - size / 2).tolist(), (center + size / 2).tolist()


def hitbox_bounds(model):
    """One square column over the body's mass, from the floor to the top of the abdomen: 5 blocks across, so the
    face, the thorax and the abdomen are inside. One hitbox, not one per body part, so a sweep can never hit
    her twice. The legs' outer reach, the wax and the candles are outside."""
    names = {c.name: c for c in model.cubes}
    head, abdomen = names["head"], names["abdomen_v"]
    front, back = head.frm[2], abdomen.to[2]
    cz = float(np.round((front + back) / 2))
    half = 40.0
    return (-half, 0.0, cz - half), (half, float(np.ceil(abdomen.to[1])), cz + half)


def rotate(groups, name, delta):
    g = groups[name]
    g.rotation = [g.rotation[i] + delta[i] for i in range(3)]


def front_legs(groups, femur, tibia, metatarsus=0):
    for leg_name in ("leg_r0", "leg_l0"):
        rotate(groups, f"{leg_name}_1", (0, 0, femur))
        rotate(groups, f"{leg_name}_3", (0, 0, tibia))
        rotate(groups, f"{leg_name}_4", (0, 0, metatarsus))


def jaws_open(groups, angle):
    rotate(groups, "mandible_r", (0, -angle, 0))
    rotate(groups, "mandible_l", (0, angle, 0))


POSES = {
    "idle": "idle: crouched in the cage of her legs",
    "pounce": "pounce warning (1 s): head up, front legs raised high, jaws wide",
    "bite": "bite: lunging, front legs stabbing down, jaws snapped shut",
    "egg_sac": "egg sac: the abdomen pumps down to lay at her feet",
    "web": "web: the abdomen tipped up, spinnerets aimed back",
}


def pose(model, key):
    groups = {g.name: g for g in model.groups}
    if key == "pounce":
        rotate(groups, "h_head", (14, 0, 0))
        front_legs(groups, 16, 26, 8)
        jaws_open(groups, 28)
    elif key == "bite":
        rotate(groups, "h_head", (-10, 0, 0))
        front_legs(groups, -4, -8, 4)
        jaws_open(groups, -6)
    elif key == "egg_sac":
        rotate(groups, "abdomen", (14, 0, 0))
    elif key == "web":
        rotate(groups, "abdomen", (-22, 0, 0))


VIEWS = s1.VIEWS
POSE_VIEWS = [
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "sil_eye", "mode": "silhouette", "camera": "persp", "yaw": 23, "height": 1.62, "dist": 10, "player": False},
    {"name": "clay_34", "mode": "clay", "camera": "persp", "yaw": 35, "height": 4.5, "dist": 10},
]
HITBOX_VIEWS = [
    {"name": "hitbox_front", "mode": "flat", "camera": "ortho_front"},
    {"name": "hitbox_side", "mode": "flat", "camera": "ortho_side"},
]


def bone_count(model):
    return sum(1 for g in model.groups if any(not hasattr(c, "children") for c in g.children))


def main():
    model = build()
    frm, to = hitbox_bounds(model)
    bb = model.to_bbmodel()
    add_hitbox(bb, frm, to)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "occultech_brood_mother_blockout.bbmodel").write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")

    v2.run_blender(model.render_json(PALETTE), OUT, VIEWS)
    stats = model.stats()
    stats["hitbox_blocks"] = [round((t - f) / 16, 2) for f, t in zip(frm, to)]
    stats["bones_with_cubes"] = bone_count(model)
    stats["hair_cards"] = sum(1 for c in model.cubes if c.mat == "hair")
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    sheet.direction_sheet(OUT, "Brood Mother - design lock", stats, OUT / "sheet.png")

    boxes = model.render_json(PALETTE) + [v2.box_json("hitbox", frm, to, "hitbox")]
    for b in boxes[:-1]:
        b["color"] = [v * 0.55 + 0.4 for v in b["color"]]
    v2.run_blender(boxes, OUT / "hitbox", HITBOX_VIEWS)
    views = [Image.open(OUT / "hitbox" / f"{v['name']}.png") for v in HITBOX_VIEWS]
    pair = Image.new("RGB", (sum(v.width for v in views), max(v.height for v in views)))
    pair.paste(views[0], (0, 0))
    pair.paste(views[1], (views[0].width, 0))
    pair.save(OUT / "hitbox.png")

    for key in POSES:
        posed = build()
        pose(posed, key)
        v2.run_blender(posed.render_json(PALETTE), OUT / "poses" / key, POSE_VIEWS)
    sheet.compare_sheet(OUT / "poses", [(k, "") for k in POSES], OUT / "poses.png",
                        heading="Brood Mother - key poses (session 2)")
    (OUT / "parts.md").write_text("# Brood Mother blockout parts (session 2)\n\nGenerated by `tools/art/bosses/brood_s2.py`."
                                  " Cube sizes are whole texels; hair cards are zero thick.\n\n" + v2.parts_list(model) + "\n",
                                  encoding="utf-8")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
