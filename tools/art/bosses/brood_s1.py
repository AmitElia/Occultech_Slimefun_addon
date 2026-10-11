"""Brood Mother redesign, session 1 (second take): three directions as Blockbench cuboid blockouts.

The brief: the vanilla spider, buffed and mutated. Long predator legs with several joints. On her back, a mountain of
melted wax and lit candles. No mask; large mandibles instead.

  A  Candle stalker  slung high between very long four-joint legs, knees far above her back; a tall wax spire
  B  Wax hulk        a heavy, muscled spider low to the ground, under a wax mountain that spills down her sides
  C  Ambush hunter   head low, mandibles spread, the front pair held up and folded like scythes, ready to strike

All three keep the vanilla spider's parts and proportions (a big square head, a small thorax, a long boxy abdomen,
the red eye pattern on the face), scaled up and grown out of shape.

Run from the repository root: python tools/art/bosses/brood_s1.py
"""
import json
import math
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
    "wax": RAMPS["wax"][3], "wax_old": RAMPS["wax"][2], "wax_dark": RAMPS["wax"][1], "candle": RAMPS["wax"][4],
    "wick": RAMPS["ink"][0], "flame": RAMPS["ember"][2],
}
# k: vanilla pixel scale (vanilla: head 8, thorax 6, abdomen 10x8x12); buff: extra thorax bulk
DIRECTIONS = {
    "A": {"title": "Candle stalker", "k": 2.0, "buff": 1.1, "body_y": 34, "legs": "stalker",
          "pile": {"height": 30, "spread": 0.85, "candles": 18, "drips": 12, "lean": 0}},
    "B": {"title": "Wax hulk", "k": 2.6, "buff": 1.45, "body_y": 19, "legs": "hulk",
          "pile": {"height": 32, "spread": 1.2, "candles": 28, "drips": 20, "lean": 0}},
    "C": {"title": "Ambush hunter", "k": 2.2, "buff": 1.25, "body_y": 22, "legs": "hunter",
          "pile": {"height": 26, "spread": 1.0, "candles": 20, "drips": 14, "lean": 4}},
}
GOLDEN = math.pi * (3 - math.sqrt(5))


def candle(parent, name, base, height, width, tilt):
    """One candle standing at base (its foot sunk into the wax), with a collar of melted wax, a drip, a wick and a
    flame. Each candle is its own bone, so it can lean."""
    x, y, z = base
    g = parent.group(name, (x, y, z), tilt)
    g.box(f"{name}_body", (x, y + height / 2 - 1, z), (width, height + 2, width), "candle")
    g.box(f"{name}_collar", (x, y + height - 1.6, z), (width + 1.1, 1.4, width + 1.1), "wax")
    g.box(f"{name}_drip", (x + width / 2 + 0.25, y + height - 3.5, z), (0.9, 4, 0.9), "wax")
    g.box(f"{name}_wick", (x, y + height + 0.6, z), (0.5, 1.6, 0.5), "wick")
    g.group(f"glow_{name}", (x, y + height + 2, z)).box(f"{name}_flame", (x, y + height + 2.4, z), (1.8, 3.2, 1.8), "flame")


def wax_mountain(parent, top, radii, p, seed):
    """The mountain of melted wax on her back: lumps of wax run together round one slumped peak, a skirt of wax
    spilling over the edge of the abdomen in drips, and candles of every height stuck all over it, a crown of tall ones
    on the peak. Candles stand on the wax surface (the highest lump under them)."""
    cx, cy, cz = top
    rx, rz = radii[0] * p["spread"], radii[1] * p["spread"]
    pile = parent.group("wax_pile", (cx, cy, cz))
    h = p["height"]
    lumps = []
    # the peak: three mounds stacked, each sliding off the last as if it slumped while hot
    px, pz = cx + rx * 0.12, cz + rz * 0.15
    for t, (f, rise) in enumerate(((0.62, 0.0), (0.42, 0.42), (0.24, 0.78))):
        lumps.append((px + math.sin(seed + t * 2.1) * rx * 0.12 * t, cy + h * rise,
                      pz + p["lean"] * t + math.cos(seed + t) * rz * 0.1 * t, (rx * f, h * 0.36, rz * f)))
    # lumps run together round its foot, of every size
    for i in range(6):
        a = seed + i * GOLDEN * 2
        r = 0.45 + 0.35 * ((i * 3) % 4) / 3
        size = 0.26 + 0.12 * ((i * 5) % 3)
        lumps.append((cx + math.cos(a) * rx * r, cy + h * 0.02, cz + math.sin(a) * rz * r,
                      (rx * size, h * (0.16 + 0.08 * (i % 3)), rz * size)))
    for i, (x, y, z, r) in enumerate(lumps):
        pile.blob(f"wax_lump_{i}", (x, y, z), r, ("wax", "wax_old", "wax")[i % 3], layers=4, axes=("y",))

    def surface(x, z):
        best = cy - 2
        for lx, ly, lz, (lrx, lry, lrz) in lumps:
            f = ((x - lx) / lrx) ** 2 + ((z - lz) / lrz) ** 2
            if f < 0.85:
                best = max(best, ly + lry * math.sqrt(1 - f))
        return best

    # the skirt: wax spilt over the edge of the abdomen, hanging in drips of every length
    for i in range(p["drips"]):
        a = i * 2 * math.pi / p["drips"] + seed
        x, z = cx + math.cos(a) * radii[0] * 1.02, cz + math.sin(a) * radii[1] * 1.02
        length = 3 + (i * 7 % 11) * (1.2 if i % 4 else 1.8)
        pile.box(f"wax_drip_{i}", (x, cy - length / 2 + 1, z), (2.4 - (i % 2) * 0.8, length, 2.4 - (i % 2) * 0.8),
                 "wax_old" if i % 3 else "wax")
    # candles all over the slopes: taller and thicker towards the peak, a few burnt down to stubs, some leaning
    n = p["candles"]
    for i in range(n):
        a = seed + i * GOLDEN
        r = math.sqrt((i + 0.5) / n) * 0.92
        x, z = cx + math.cos(a) * rx * r, cz + math.sin(a) * rz * r
        stub = i % 5 == 4
        height = 2.5 if stub else 5 + (1 - r) * 9 + (i * 7 % 4) * 1.5
        width = 2.6 + (1 - r) * 1.6 + (i % 3) * 0.5
        tilt = (22.5 if i % 6 == 1 else -22.5 if i % 6 == 4 else 0, 0, 22.5 if i % 6 == 2 else 0)
        candle(pile, f"candle_{i}", (x, surface(x, z) - 1.5, z), height, width, tilt)
    tx, ty, tz, tr = lumps[2]
    for j in range(3):
        a = seed + j * 2.1
        x, z = tx + math.cos(a) * tr[0] * 0.35, tz + math.sin(a) * tr[2] * 0.35
        candle(pile, f"candle_top_{j}", (x, surface(x, z) - 1.5, z), 16 - j * 3, 4.2 - j * 0.5, (0, 0, 0))


def eyes(head, hx, hy, z, k):
    """The vanilla spider face: two big red eyes in the middle row, smaller ones round them; plus a mutated cluster
    spilling down one cheek."""
    u = k   # one vanilla pixel
    for s in (-1, 1):
        head.box(f"eye_big_{s}", (hx + s * 1.5 * u, hy + 0.5 * u, z), (2 * u, 1.2 * u, 0.8), "eye")
        head.box(f"eye_upper_{s}", (hx + s * 0.6 * u, hy + 2 * u, z), (0.9 * u, 0.9 * u, 0.8), "eye_small")
        head.box(f"eye_outer_{s}", (hx + s * 3.0 * u, hy + 1.6 * u, z), (0.9 * u, 0.9 * u, 0.8), "eye_small")
        head.box(f"eye_low_{s}", (hx + s * 2.5 * u, hy - 0.8 * u, z), (0.9 * u, 0.9 * u, 0.8), "eye_small")
    for i, (ex, ey) in enumerate(((-3.3, -2.0), (-2.4, -2.7), (-3.4, -3.3))):
        head.box(f"eye_mutant_{i}", (hx + ex * u, hy + ey * u, z), (0.7 * u, 0.7 * u, 0.8), "eye_small")


def mandibles(head, hx, hy, z, k, spread):
    """Big chelicerae under the face: a thick base, an arm curving out and back in, a fang hooked at the tip and a
    row of teeth along the inside."""
    for s in (-1, 1):
        name = f"mandible_{'r' if s > 0 else 'l'}"
        root = (hx + s * 1.8 * k, hy - 2.6 * k, z)
        g = head.group(name, root, (0, -s * spread, 0))
        base_end = (root[0] + s * 1.6 * k, root[1] - 0.6 * k, root[2] - 3.5 * k)   # out and forward, like pincers
        tip = (root[0] + s * 0.6 * k, root[1] - 1.0 * k, root[2] - 7.0 * k)
        hook = (root[0] - s * 1.2 * k, root[1] - 0.9 * k, root[2] - 8.2 * k)
        v1.beam(g, f"{name}_base", root, base_end, 2.6 * k, "mandible", depth=2.4 * k)
        v1.beam(g, f"{name}_arm", base_end, tip, 1.8 * k, "mandible", depth=1.6 * k)
        v1.beam(g, f"{name}_fang", tip, hook, 0.9 * k, "fang")
        for t in range(3):
            f = (t + 1) / 4
            p = tuple(base_end[i] + (tip[i] - base_end[i]) * f for i in range(3))
            g.box(f"{name}_tooth_{t}", (p[0] - s * 0.9 * k, p[1], p[2]), (0.5 * k, 0.5 * k, 0.5 * k), "fang")


def legs(thorax, d, y, td, tw):
    """Eight predator legs, four joints each. A leg is laid along +X and yawed round Y (positive yaw turns it to the
    front, -Z); the segments climb to a high knee and then reach down to the floor."""
    style = d["legs"]
    for side in (1, -1):
        for i in range(4):
            hip = (side * tw * 0.45, y + 1, -td * 0.35 + i * td * 0.24)
            if style == "stalker":   # harvestman: knees towering over her back
                yaw = (66, 28, -14, -52)[i]
                segs = [(17, 64, 4.0), (15, 28, 3.2), (13, -28, 2.6), (None, -82, 2.0)]
            elif style == "hulk":    # thick at the hip, splayed wide to carry the weight
                yaw = (58, 22, -12, -46)[i]
                segs = [(15, 46, 6.0), (12, 8, 4.8), (10, -38, 3.8), (None, -78, 2.8)]
            elif i == 0:             # hunter: the front pair held up and folded, like a mantis's scythes
                yaw = 74
                segs = [(15, 70, 4.8), (16, 18, 3.8), (13, -62, 3.0), (6, -20, 2.0)]
            else:
                yaw = (0, 26, -14, -50)[i]
                segs = [(16, 52, 4.6), (13, 14, 3.6), (11, -34, 2.8), (None, -80, 2.2)]
            ang = yaw if side > 0 else 180 - yaw
            leg(thorax, f"leg_{'r' if side > 0 else 'l'}{i}", hip, ang, segs, ground=0.0, mat="chitin",
                knuckle_mat="chitin_lit", joint_scale=1.3, bristles=4 if style == "hunter" and i == 0 else 2,
                bristle_mat="chitin_lit")


def build(key):
    d = DIRECTIONS[key]
    k, buff, y = d["k"], d["buff"], d["body_y"]
    model = Model(f"occultech_brood_mother_{key.lower()}")
    body = model.group("root_body", (0, y, 0))
    # thorax: the vanilla 6x6x6 neck, swollen with muscle
    tw, th, td = 6 * k * buff, 6 * k * buff * 0.85, 6 * k
    thorax = body.group("thorax", (0, y, 0))
    thorax.box("thorax", (0, y, 0), (tw, th, td), "chitin")
    thorax.box("thorax_plate", (0, y + th / 2 + 0.6, 0), (tw * 0.7, 1.2, td * 0.8), "plate")
    for s in (-1, 1):   # muscle humps behind the head
        thorax.box(f"hump_{s}", (s * tw * 0.27, y + th / 2 + 1.6, -td * 0.1), (tw * 0.34, 3.2, td * 0.55), "chitin_lit")
    legs(thorax, d, y, td, tw)
    # abdomen: the vanilla 10x8x12 box behind, mutated: a lumpy swell and split plates under the wax
    aw, ah, ad = 10 * k, 8 * k, 12 * k
    az = td / 2 + ad / 2 - 1
    ay = y + 0.6 * k
    abdomen = body.group("abdomen", (0, y, td / 2))
    abdomen.box("abdomen", (0, ay, az), (aw, ah, ad), "chitin")
    abdomen.box("abdomen_swell", (aw * 0.12, ay - ah * 0.08, az + ad * 0.12), (aw * 0.9 + 1.5, ah * 0.7, ad * 0.62), "chitin_lit")
    abdomen.box("spinnerets", (0, ay - ah * 0.2, az + ad / 2 + 1), (aw * 0.3, ah * 0.3, 2.4), "chitin_lit")
    for i in range(3):   # plates on the flank, pushed apart by the wax
        abdomen.box(f"flank_plate_{i}", (aw / 2 + 0.6, ay + ah * 0.15 - i * 2.2, az - ad * 0.25 + i * ad * 0.22),
                    (1.2, 2.2, ad * 0.18), "plate")
    wax_mountain(abdomen, (0, ay + ah / 2 - 1, az + 1), (aw * 0.5, ad * 0.5), d["pile"], seed=ord(key))
    # head: the vanilla 8x8x8 cube, a little bigger than the thorax; the hunter carries it low
    hs = 8 * k
    hz = -td / 2 - hs / 2 + 1
    hy = y + (-0.25 * hs if d["legs"] == "hunter" else 0.08 * hs)
    head = thorax.group("h_head", (0, hy, -td / 2))
    head.box("head", (0, hy, hz), (hs, hs, hs), "chitin")
    head.box("head_brow", (0, hy + hs * 0.38, hz - hs * 0.1), (hs + 1, hs * 0.18, hs * 0.85), "chitin_lit")
    eyes(head, 0, hy, hz - hs / 2 - 0.2, k)
    mandibles(head, 0, hy, hz - hs / 2 + 2, k, spread=26 if d["legs"] == "hunter" else 8)
    return model


VIEWS = v1.VIEWS + [
    {"name": "flat_front", "mode": "flat", "camera": "persp", "yaw": -18, "height": 1.9, "dist": 8, "player": False},
]


def main():
    for old in OUT.glob("*"):   # the masked concepts were rejected; they stay in git history
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
    sheet.compare_sheet(OUT, items, OUT / "compare.png", heading="Brood Mother - three directions (session 1, take 2)")
    sheet.compare_sheet(OUT, items, OUT / "compare_material.png", heading="Brood Mother - material zones",
                        views=("flat_front", "flat_side", "flat_back"))


if __name__ == "__main__":
    main()
