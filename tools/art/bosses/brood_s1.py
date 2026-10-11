"""Brood Mother redesign, session 1 (take 3): three proportion studies as Blockbench cuboid blockouts.

The brief: the vanilla spider, buffed and mutated. Long predator legs with several joints. On her back, a mountain of
melted wax and lit candles. No mask; large mandibles instead.

Take 2 had a small body on stilts and a wax tower. These keep a real spider's threat: the body low and heavy, the big
head carried low, a fat abdomen raised behind; the legs arch high over the back and then reach far out and down, so she
crouches inside a cage of her own legs. The wax is poured over the abdomen and runs down its sides; candles stand in
clusters on broad lumps.

  A  Huntress  a wolf spider's build: balanced, low, thick legs of middle length
  B  Brute     a tarantula's build: the heaviest body and abdomen, short thick legs, the biggest wax load
  C  Stalker   a huntsman's build: a flatter body on very long legs, the knees far above her back

All three keep the vanilla spider's parts (the square head with the red eye pattern, a thorax, a boxy abdomen).

Run from the repository root: python tools/art/bosses/brood_s1.py
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model, leg  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s1 as v1, volley_crone_s2 as v2  # noqa: E402
from palettes import RAMPS  # noqa: E402

OUT = ROOT / "docs/art/bosses/brood_mother/overhaul/s1_concepts"
PALETTE = {
    "chitin": RAMPS["ash"][1], "chitin_lit": RAMPS["ash"][2], "plate": RAMPS["ash"][3], "mandible": RAMPS["bone"][1],
    "fang": RAMPS["bone"][3], "eye": RAMPS["crimson"][4], "eye_small": RAMPS["crimson"][3],
    "wax": RAMPS["wax"][3], "wax_old": RAMPS["wax"][2], "candle": RAMPS["wax"][4],
    "wick": RAMPS["ink"][0], "flame": RAMPS["ember"][2],
}
# sizes in model pixels (16 per block): head, thorax, abdomen as (w, h, d); thorax_y is the thorax centre
DIRECTIONS = {
    "A": {"title": "Huntress", "head": (20, 18, 20), "thorax": (21, 14, 18), "abdomen": (30, 24, 34), "thorax_y": 17,
          "leg_len": 1.0, "leg_thick": 1.0, "femur": 58, "wax": 18},
    "B": {"title": "Brute", "head": (23, 20, 22), "thorax": (25, 17, 20), "abdomen": (37, 28, 38), "thorax_y": 18,
          "leg_len": 0.86, "leg_thick": 1.3, "femur": 50, "wax": 22},
    "C": {"title": "Stalker", "head": (18, 15, 18), "thorax": (19, 12, 17), "abdomen": (28, 20, 32), "thorax_y": 16,
          "leg_len": 1.25, "leg_thick": 0.85, "femur": 66, "wax": 16},
}


def rounded_box(group, name, center, size, mat, bevel):
    """A box with its edges bevelled: three overlapping boxes, each a bevel short on two axes."""
    (x, y, z), (w, h, d), b = center, size, bevel
    group.box(f"{name}", (x, y, z), (w, h - 2 * b, d - 2 * b), mat)
    group.box(f"{name}_v", (x, y, z), (w - 2 * b, h, d - 2 * b), mat)
    group.box(f"{name}_d", (x, y, z), (w - 2 * b, h - 2 * b, d), mat)


def candle(parent, name, base, height, width, tilt=(0, 0, 0)):
    """One candle standing at base (its foot sunk into the wax), with a collar of melted wax, a drip, a wick and a
    flame. Each candle is its own bone, so it can lean; the flame is a glow_ bone for full-bright and flicker."""
    x, y, z = base
    g = parent.group(name, (x, y, z), tilt)
    g.box(f"{name}_body", (x, y + height / 2 - 1, z), (width, height + 2, width), "candle")
    g.box(f"{name}_collar", (x, y + height - 1.4, z), (width + 1.0, 1.2, width + 1.0), "wax")
    g.box(f"{name}_drip", (x + width / 2 + 0.3, y + height - 3.4, z), (1.0, 4, 1.0), "wax")
    g.box(f"{name}_wick", (x, y + height + 0.6, z), (0.6, 1.6, 0.6), "wick")
    g.group(f"glow_{name}", (x, y + height + 2, z)).box(f"{name}_flame", (x, y + height + 2.5, z), (1.8, 3.2, 1.8), "flame")


def wax_mountain(parent, top_y, cz, half_w, half_d, side_h, height, seed):
    """Melted wax heaped on the abdomen: a cluster of rounded lumps of every size run together (the biggest set back
    over the rear), a few thick flows of wax tonguing down her flanks with thin drips between them, and candles in
    clusters on the lumps, the tallest on the highest lump."""
    rnd = random.Random(seed)
    pile = parent.group("wax_pile", (0, top_y, cz))
    pile.box("wax_cap", (0, top_y + 0.5, cz), (2 * half_w - 3, 2, 2 * half_d - 3), "wax_old")
    # the lumps: (x, z, radius x, height, radius z) as fractions of the abdomen top and the pile height
    spots = [(0.05, 0.22, 0.62, 0.62, 0.55), (-0.3, 0.45, 0.42, 0.85, 0.36), (0.38, 0.5, 0.36, 0.55, 0.32),
             (0.45, -0.3, 0.4, 0.42, 0.34), (-0.48, -0.15, 0.4, 0.5, 0.36), (-0.05, -0.5, 0.42, 0.34, 0.3),
             (0.12, 0.62, 0.3, 1.0, 0.26), (-0.55, 0.62, 0.3, 0.4, 0.28)]
    lumps = []
    for i, (fx, fz, frx, fh, frz) in enumerate(spots):
        x = fx * half_w + rnd.uniform(-1, 1)
        z = cz + fz * half_d + rnd.uniform(-1, 1)
        r = (frx * half_w, fh * height * 0.55, frz * half_d)
        y = top_y + 1 + (fh * height * 0.35 if fh > 0.8 else 0)   # the tallest lumps sit on the others
        pile.blob(f"wax_lump_{i}", (x, y, z), r, "wax" if i % 3 else "wax_old", layers=6, axes=("y",))
        lumps.append((x, y, z, r))
    # thick flows down the flanks and back: each a tongue narrowing as it runs down, with a bead at its end
    flows = [(1, 0.1), (1, 0.6), (-1, -0.2), (-1, 0.45), (0, 1), (1, -0.5), (-1, 0.85)]
    for i, (side, f) in enumerate(flows):
        drop = side_h * rnd.uniform(0.45, 0.8)
        width = rnd.uniform(5, 8)
        out = rnd.uniform(0.5, 1.0)
        for j, (wf, hf) in enumerate(((1.0, 0.3), (0.72, 0.4), (0.45, 0.3))):
            seg_top = top_y + 1 - drop * (0, 0.3, 0.7)[j]
            h = drop * hf + 1
            if side:
                c, sz = (side * (half_w + out - j * 0.15), seg_top - h / 2, cz + f * half_d), (1.8 + 0.2 * j, h, width * wf)
            else:
                c, sz = (rnd.uniform(-0.4, 0.4) * half_w, seg_top - h / 2, cz + half_d + out - j * 0.15), (width * wf, h, 1.8 + 0.2 * j)
            pile.box(f"wax_flow_{i}_{j}", c, sz, "wax" if j else "wax_old")
    for i in range(10):   # thin drips between the flows
        side = (1, -1)[i % 2]
        f = rnd.uniform(-0.9, 0.9)
        drop = rnd.uniform(2.5, side_h * 0.35)
        pile.box(f"wax_drip_{i}", (side * (half_w + rnd.uniform(0.3, 0.8)), top_y + 1 - drop / 2, cz + f * half_d),
                 (1.4, drop, 1.6), "wax")
    # candle clusters: tallest at the top of each lump, shorter round it, some burnt to stubs, some leaning
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
            base = y + r[1] * math.sqrt(1 - f * f) - 1.8
            tilt = (0, 0, 0) if j == 0 or rnd.random() < 0.6 else (rnd.choice((-22.5, 22.5)), 0, 0)
            candle(pile, f"candle_{k}", (cx, base, cz2), max(2.5, h), 4.2 if j == 0 else rnd.uniform(2.6, 3.6), tilt)
            k += 1


def eyes(head, hy, z, hw, hh):
    """The vanilla spider face: two big red eyes in the middle row, smaller ones round them; plus a mutated cluster
    spilling down one cheek."""
    u, v = hw / 8, hh / 8   # one vanilla pixel across and up
    for s in (-1, 1):
        head.box(f"eye_big_{s}", (s * 1.5 * u, hy + 0.5 * v, z), (2 * u, 1.2 * v, 0.8), "eye")
        head.box(f"eye_upper_{s}", (s * 0.6 * u, hy + 2 * v, z), (0.9 * u, 0.9 * v, 0.8), "eye_small")
        head.box(f"eye_outer_{s}", (s * 3.0 * u, hy + 1.6 * v, z), (0.9 * u, 0.9 * v, 0.8), "eye_small")
        head.box(f"eye_low_{s}", (s * 2.5 * u, hy - 0.8 * v, z), (0.9 * u, 0.9 * v, 0.8), "eye_small")
    for i, (ex, ey) in enumerate(((-3.3, -2.0), (-2.4, -2.7), (-3.4, -3.3))):
        head.box(f"eye_mutant_{i}", (ex * u, hy + ey * v, z), (0.7 * u, 0.7 * v, 0.8), "eye_small")


def jaws(head, hy, face_z, hw, hh):
    """Large mandibles under the face, reaching forward and curling in like pincers, with teeth inside and a hooked
    fang; a pair of short pedipalps beside them."""
    bottom = hy - hh / 2
    for s in (-1, 1):
        name = f"mandible_{'r' if s > 0 else 'l'}"
        root = (s * hw * 0.24, bottom + hh * 0.2, face_z + 2)
        g = head.group(name, root)
        bend = (s * hw * 0.42, bottom - hh * 0.02, face_z - hw * 0.35)
        tip = (s * hw * 0.26, bottom - hh * 0.06, face_z - hw * 0.72)
        hook = (s * hw * 0.02, bottom + hh * 0.0, face_z - hw * 0.8)
        v1.beam(g, f"{name}_base", root, bend, hw * 0.28, "mandible", depth=hw * 0.26)
        v1.beam(g, f"{name}_arm", bend, tip, hw * 0.2, "mandible", depth=hw * 0.17)
        v1.beam(g, f"{name}_fang", tip, hook, hw * 0.1, "fang")
        for t in range(3):
            f = (t + 1) / 4
            p = tuple(bend[i] + (tip[i] - bend[i]) * f for i in range(3))
            g.box(f"{name}_tooth_{t}", (p[0] - s * hw * 0.1, p[1] + 0.5, p[2]), (hw * 0.06, hw * 0.07, hw * 0.06), "fang")
        palp = head.group(f"palp_{'r' if s > 0 else 'l'}", (s * hw * 0.44, bottom + 1, face_z + 1))
        knee = (s * hw * 0.56, bottom + hh * 0.05, face_z - hw * 0.22)
        v1.beam(palp, f"palp_{s}_0", (s * hw * 0.44, bottom + 1, face_z + 1), knee, hw * 0.12, "chitin_lit")
        v1.beam(palp, f"palp_{s}_1", knee, (s * hw * 0.5, bottom - hh * 0.25, face_z - hw * 0.4), hw * 0.09, "chitin_lit")


def legs(thorax, d, ty, tw, td):
    """Eight legs, six segments each (coxa, femur, patella, tibia, metatarsus, tarsus) in one vertical plane, yawed
    round Y (positive yaw turns a leg to the front, -Z). The femur climbs steeply to a knee above her back, the tibia
    reaches far out and down, the last segments plant the foot. Front legs longest and turned forward, rear legs back."""
    length, thick, femur = d["leg_len"], d["leg_thick"], d["femur"]
    for side in (1, -1):
        for i in range(4):
            yaw = (52, 22, -14, -48)[i]
            ls = (1.0, 0.88, 0.8, 0.95)[i] * length
            hip = (side * (tw / 2 - 1.5), ty - 1.5, -td * 0.33 + i * td * 0.22)
            segs = [(4 * ls, 18, 5.6 * thick), (26 * ls, femur, 5.6 * thick), (6 * ls, 4, 5.0 * thick),
                    (22 * ls, -34, 4.2 * thick), (18 * ls, -60, 3.0 * thick), (None, -76, 2.0 * thick)]
            leg(thorax, f"leg_{'r' if side > 0 else 'l'}{i}", hip, yaw if side > 0 else 180 - yaw, segs, ground=0.0,
                mat="chitin", knuckle_mat="chitin_lit", joint_scale=1.25, bristles=1, bristle_mat="chitin_lit")


def build(key):
    d = DIRECTIONS[key]
    (hw, hh, hd), (tw, th, td), (aw, ah, ad), ty = d["head"], d["thorax"], d["abdomen"], d["thorax_y"]
    model = Model(f"occultech_brood_mother_{key.lower()}")
    body = model.group("root_body", (0, ty, 0))
    # thorax: the vanilla neck block, swollen with muscle
    thorax = body.group("thorax", (0, ty, 0))
    rounded_box(thorax, "thorax", (0, ty, 0), (tw, th, td), "chitin", 1.5)
    thorax.box("thorax_plate", (0, ty + th / 2 + 0.5, -1), (tw * 0.55, 1.4, td * 0.7), "plate")
    for s in (-1, 1):   # muscle humps behind the head
        thorax.box(f"hump_{s}", (s * tw * 0.26, ty + th / 2 + 1.2, -td * 0.15), (tw * 0.32, 3.0, td * 0.5), "chitin_lit")
    legs(thorax, d, ty, tw, td)
    # abdomen: fat and raised behind a short waist; mutated with a swelling and split flank plates
    az = td / 2 + ad / 2 + 1
    ay = ty + ah * 0.28
    abdomen = body.group("abdomen", (0, ty, td / 2))
    abdomen.box("pedicel", (0, ty + 1, td / 2 + 1), (tw * 0.4, th * 0.5, 5), "chitin_lit")
    rounded_box(abdomen, "abdomen", (0, ay, az), (aw, ah, ad), "chitin", 3)
    rounded_box(abdomen, "abdomen_swell", (aw * 0.14, ay - ah * 0.12, az + ad * 0.1), (aw * 0.9, ah * 0.72, ad * 0.6),
                "chitin_lit", 2)
    abdomen.box("spinnerets", (0, ay - ah * 0.22, az + ad / 2 + 1), (aw * 0.26, ah * 0.26, 3), "chitin_lit")
    for i in range(3):
        abdomen.box(f"flank_plate_{i}", (-aw / 2 - 0.4, ay - ah * 0.05 - i * 2.4, az - ad * 0.2 + i * ad * 0.2),
                    (1.2, 2.4, ad * 0.16), "plate")
    wax_mountain(abdomen, ay + ah / 2 - 1, az, aw / 2, ad / 2, ah, d["wax"], seed=ord(key))
    # head: the vanilla cube, big and carried low
    hz = -td / 2 - hd / 2 + 2
    hy = ty - hh * 0.12
    head = thorax.group("h_head", (0, hy, -td / 2))
    head.box("head", (0, hy, hz), (hw, hh, hd), "chitin")
    head.box("head_brow", (0, hy + hh * 0.4, hz - hd * 0.06), (hw + 1, hh * 0.16, hd * 0.9), "chitin_lit")
    eyes(head, hy, hz - hd / 2 - 0.2, hw, hh)
    jaws(head, hy, hz - hd / 2, hw, hh)
    return model


VIEWS = v1.VIEWS + [
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": -18, "height": 1.9, "dist": 9, "player": False},
]


def main():
    for old in OUT.glob("*"):   # earlier takes stay in git history
        if old.is_dir():
            shutil.rmtree(old)
    for key in DIRECTIONS:
        out = OUT / key
        out.mkdir(parents=True, exist_ok=True)
        model = build(key)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        v2.run_blender(model.render_json(PALETTE), out, VIEWS)
        stats = model.stats()
        (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        sheet.direction_sheet(out, f"Brood Mother - {key} {DIRECTIONS[key]['title']}", stats, out / "sheet.png")
        print(key, stats["size_blocks"], stats["cubes"])
    items = [(k, v["title"]) for k, v in DIRECTIONS.items()]
    sheet.compare_sheet(OUT, items, OUT / "compare.png", heading="Brood Mother - three proportion studies (session 1, take 3)")
    sheet.compare_sheet(OUT, items, OUT / "compare_material.png", heading="Brood Mother - material zones",
                        views=("flat_front", "flat_34", "flat_side"))


if __name__ == "__main__":
    main()
