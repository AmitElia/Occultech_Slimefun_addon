"""The Unbound redesign, session 1 step 3: the full blockout (plan: docs/art/bosses/the_unbound/overhaul/plan.md).

The whole figure from cuboids, built on the face study's bust (unbound_face.bust: the locked head and the burning
chest piece) and the take-2 silhouette:
- hunched 20 degrees forward over his hips, bare and buff above the waist, dark trousers and boots;
- long arms hanging past his knees; heavy iron shackles on both wrists and both ankles, chains hanging from the
  wrists to the ground and trailing, chains dragging behind the ankles;
- walking: the Frenzy Cleaver (its held model's design at his size: a broad butcher's blade, a thick spine, the
  haft up through it, blood along the edge) dragged behind him in his right hand, its blade sliding flat on the
  ground.

It is built in the bust's frame and then scaled so the top of his head is about 3.25 blocks (the take-2 size).
Units are model pixels (16 = one block). The front is -z; his right is +x.

Run from the repository root: python tools/art/bosses/unbound_s1.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import monarch_s1 as m1, unbound_face as uf  # noqa: E402

OUT = ROOT / "docs/art/bosses/the_unbound/overhaul/s1_blockout"
HEAD_TOP = 3.25 * 16                       # where the top of his head should land (model pixels)
PALETTE = dict(uf.PALETTE, boot=(40, 34, 32), steel=(156, 162, 168), spine=(104, 108, 114), blood=(100, 22, 20),
               haft=(88, 62, 40), wrap=(70, 50, 34), chain=(132, 132, 140))


def chain(g, name, top, drop, trail, step=2.8):
    """Links hanging straight down from a shackle to the ground, then lying along it towards trail (x, z)."""
    x, y, z = top
    i = 0
    while y - step / 2 > 0.8:
        y -= step
        size = (2.4, 3.2, 1.0) if i % 2 else (1.0, 3.2, 2.4)
        g.box(f"{name}_{i}", (x, y + step / 2, z), size, "chain")
        i += 1
    tx, tz = trail
    n = max(1, int(drop))
    for j in range(n):
        x += tx * step
        z += tz * step
        size = (3.2, 1.0, 2.4) if (i + j) % 2 else (3.2, 2.4, 1.0)
        if abs(tz) > abs(tx):
            size = (size[2], size[1], size[0])
        g.box(f"{name}_ground_{j}", (x, 0.6 if size[1] < 2 else 1.2, z), size, "chain")


def shackle(g, name, c, size):
    """A heavy iron cuff round a wrist or ankle, with a ring hanging off the front."""
    w, h, d = size
    g.box(name, c, (w + 2.6, h, d + 2.6), "iron")
    g.box(f"{name}_lip", (c[0], c[1] + h / 2 - 0.4, c[2]), (w + 3.0, 0.8, d + 3.0), "iron_lit")


def cleaver(g, grip, rise=6.0, k=1.2):
    """The Frenzy Cleaver dragged behind him on its edge: the haft runs back from his fist, rising a little, and the
    blade hangs below it, upright, its bloody edge's front corner dragging on the ground. In its own frame the haft
    runs up +y and the blade hangs off it along +z; the group turns that so the haft points back (+z)."""
    c = g.group("cleaver", grip, (90 - rise, 0, 0))
    x, y, z = grip
    c.box("pommel", (x, y - 3.5 * k, z), (3 * k, 2 * k, 3 * k), "spine")
    c.box("grip", (x, y, z), (2.2 * k, 5 * k, 2.2 * k), "wrap")
    c.box("haft", (x, y + 15 * k, z), (2.2 * k, 25 * k, 2.2 * k), "haft")
    c.box("blade", (x, y + 18.5 * k, z + 9 * k), (1.2 * k, 17 * k, 17 * k), "steel")
    c.box("spine", (x, y + 18.5 * k, z + 0.6 * k), (1.8 * k, 18 * k, 2.2 * k), "spine")
    c.box("edge_blood", (x, y + 18.5 * k, z + 17.2 * k), (1.4 * k, 17 * k, 1.6 * k), "blood")
    c.box("blood_run", (x, y + 14 * k, z + 13 * k), (1.4 * k, 5 * k, 4 * k), "blood")
    c.box("collar", (x, y + 27.2 * k, z), (3.2 * k, 2.4 * k, 3.2 * k), "spine")
    return c


def build(model):
    root = uf.bust(model, "MIX", "PIECE")
    torso = next(g for g in model.groups if g.name == "torso")
    # hips, legs, boots; shackles and chains on the ankles
    root.box("pelvis", (0, 20, 0.5), (19, 7, 12.5), "pants")
    for sx, name in ((-1, "left"), (1, "right")):
        hip = (sx * 5.5, 21, 0.5)
        thigh = root.group(f"leg_{name}", hip, (-8, 0, sx * -3))
        thigh.box(f"thigh_{name}", (sx * 5.8, 15.5, 0), (9, 12, 9.5), "pants")
        shin = thigh.group(f"shin_{name}", (sx * 5.8, 10, 0), (12, 0, 0))
        shin.box(f"shin_{name}_box", (sx * 5.8, 6, 0.2), (8.4, 9, 8.6), "pants")
        shin.box(f"boot_{name}", (sx * 5.8, 1.5, -1.0), (9.4, 3, 11.5), "boot")
        shackle(shin, f"ankle_shackle_{name}", (sx * 5.8, 5.2, 0.2), (8.4, 3.2, 8.6))
        chain(root, f"ankle_chain_{name}", (sx * 7.5, 4.5, 5.2), 3, (sx * 0.15, 0.95))
    # the forearms hang straight down from the elbows (the hunch undone at the elbow)
    for sx, name in ((-1, "left"), (1, "right")):
        elbow = (sx * 19.3, 28, 0)
        # the left hangs; the right reaches back, dragging the cleaver
        swing = -uf.HUNCH + 4 if sx < 0 else -uf.HUNCH - 42
        fore = torso.group(f"forearm_{name}", elbow, (swing, 0, sx * 3))
        fore.box(f"forearm_{name}_box", (sx * 19.6, 20, -0.4), (10.5, 15, 10.5), "skin")
        fore.box(f"fist_{name}", (sx * 19.8, 10.2, -0.8), (10, 7, 10), "skin_dark")
        shackle(fore, f"wrist_shackle_{name}", (sx * 19.6, 15.6, -0.4), (10.5, 4, 10.5))
    # chains from the wrist shackles to the ground (world space: they hang straight)
    for name in ("left", "right"):
        cuff = next(c for c in model.cubes if c.name == f"wrist_shackle_{name}").corners()
        x, z = cuff[:, 0].mean(), cuff[:, 2].mean()
        chain(root, f"wrist_chain_{name}", (x, cuff[:, 1].min(), z), 4, (0.2 if name == "right" else -0.2, 0.95))
    # the cleaver in his right fist, its blade's lower corner on the ground
    fist = next(c for c in model.cubes if c.name == "fist_right").corners()
    grip = (fist[:, 0].mean() + 0.5, fist[:, 1].mean(), fist[:, 2].mean())
    c = cleaver(root, grip)
    low = min(cube.corners()[:, 1].min() for cube in model.cubes if cube.group is c)
    c.origin[1] -= 0                                         # (kept: the grip stays in the fist)
    if low < 0 or low > 2:
        # tilt the haft until the blade's lower corner just meets the ground
        for rise in [r / 2 for r in range(-40, 60)]:
            c.rotation[0] = 90 - rise
            low = min(cube.corners()[:, 1].min() for cube in model.cubes if cube.group is c)
            if 0 <= low <= 0.8:
                break
    return root


def scale(model, k):
    """Scales the whole model about the origin (rotations are unchanged, so it stays the same shape)."""
    for g in model.groups:
        g.origin = [v * k for v in g.origin]
    for c in model.cubes:
        c.frm = [v * k for v in c.frm]
        c.to = [v * k for v in c.to]
        c.origin = [v * k for v in c.origin]


VIEWS = [
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front"},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side"},
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 2.2, "dist": 8, "target_z": 1.7},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.2, "dist": 8.5, "target_z": 1.6},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 2.2, "dist": 8.5, "target_z": 1.6,
     "player": False},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 150, "height": 3.4, "dist": 8.5, "target_z": 1.4,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -20, "height": 1.62, "dist": 5.5, "target_z": 2.0,
     "lens": 24, "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": -30, "height": 2.8, "dist": 8, "target_z": 1.6,
     "player": False},
]


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    out = OUT / "blockout"
    out.mkdir(parents=True, exist_ok=True)
    model = Model("occultech_unbound_blockout")
    build(model)
    head = next(c for c in model.cubes if c.name == "head")
    k = HEAD_TOP / float(head.corners()[:, 1].max())
    scale(model, k)
    model.write_bbmodel(out / f"{model.name}.bbmodel")
    uf.PALETTE.update(PALETTE)
    uf.render_glowing(model, out, VIEWS, {"player_at": [-2.6, 0.0]})       # beside him, to his left
    stats = dict(model.stats(), scale=round(k, 3))
    (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(stats)
    sheet.compare_sheet(OUT, [("blockout", "walking, the cleaver dragged")], OUT / "views_a.png",
                        heading="The Unbound - blockout (session 1, step 3)", views=("front", "three_quarter", "side", "back"))
    sheet.compare_sheet(OUT, [("blockout", "")], OUT / "views_b.png", heading="The Unbound - blockout, more views",
                        views=("player_eye", "clay", "sil_front", "sil_side"))


if __name__ == "__main__":
    main()
