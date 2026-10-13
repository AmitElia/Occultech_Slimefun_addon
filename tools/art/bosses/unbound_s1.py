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
HEAD_TOP = 4.5 * 16                        # where the top of his head lands (model pixels; 3.25 blocks until the user asked for him far bigger)
PALETTE = dict(uf.PALETTE, boot=(40, 34, 32), steel=(156, 162, 168), spine=(104, 108, 114), blood=(100, 22, 20),
               haft=(88, 62, 40), wrap=(70, 50, 34), chain=(132, 132, 140), hole=(24, 22, 26))


CHAIN_W = 4.8      # a link's width (pre-scale; 4 texels once scaled and snapped: room for its hole)


def chain_planes(g, name, centre, length, axis):
    """A run of chain as two crossed planes along axis ('y' hanging, 'z' lying), the way vanilla draws its chain:
    the planes are painted with cut-out links that alternate between face-on rings and side-on links."""
    x, y, z = centre
    if axis == "y":
        g.box(f"{name}_a", (x, y, z), (CHAIN_W, length, 0), "chain")
        g.box(f"{name}_b", (x, y, z), (0, length, CHAIN_W), "chain")
    else:
        g.box(f"{name}_a", (x, y, z), (0, CHAIN_W, length), "chain")
        g.box(f"{name}_b", (x, y - CHAIN_W / 2 + 0.3, z), (CHAIN_W, 0, length), "chain")


def chain(g, name, top, drop, trail, step=2.8):
    """A chain hanging from a shackle to the ground, then lying along it, trailing back (trail: its x, z lean)."""
    x, y, z = top
    chain_planes(g, f"{name}_hang", (x, y / 2 + 0.3, z), max(1.0, y - 0.6), "y")
    length = max(1, int(drop)) * step + 4
    chain_planes(g, f"{name}_lie", (x + trail[0] * length / 2, CHAIN_W / 2, z + length / 2), length, "z")


def shackle(g, name, c, size):
    """A heavy iron cuff round a wrist or ankle, with a ring hanging off the front."""
    w, h, d = size
    g.box(name, c, (w + 2.6, h, d + 2.6), "iron")
    g.box(f"{name}_lip", (c[0], c[1] + h / 2 - 0.4, c[2]), (w + 3.0, 0.8, d + 3.0), "iron_lit")


def cleaver(g, grip, rot, k=1.15):
    """The Frenzy Cleaver at his size: a butcher's cleaver, not a plate on a stick. A wrapped handle with a pommel and
    a bolster; then a long rectangular blade (about 1.6 blocks long, 0.8 tall) whose thick spine runs on in line
    with the handle, the bloody edge along the far side, the hanging hole near the tip.
    In its own frame the handle runs up +y from the grip (the origin) and the blade's edge faces -z. rot turns it:
    rot x = 90 + a lays it back and a degrees down (the drag: spine on the ground, edge up); rot x = 90 - a, back
    and a degrees up (over the shoulder: edge up, so the chop comes down edge first)."""
    c = g.group("cleaver", grip, rot)
    x, y, z = grip
    L, H, y0 = 26 * k, 13 * k, y + 10.5 * k                # blade length and height; where the blade starts
    c.box("pommel", (x, y - 1.6 * k, z), (3.2 * k, 2.2 * k, 3.2 * k), "spine")
    c.box("handle", (x, y + 4.2 * k, z), (2.6 * k, 10 * k, 2.6 * k), "wrap")
    c.box("bolster", (x, y + 9.8 * k, z), (3.0 * k, 1.8 * k, 3.4 * k), "spine")
    c.box("blade", (x, y0 + L / 2, z + 1.2 * k - H / 2), (1.2 * k, L, H), "steel")
    c.box("spine", (x, y0 + L / 2, z + 0.3 * k), (2.2 * k, L, 2.2 * k), "spine")
    c.box("tip", (x, y0 + L - 1.0 * k, z + 1.2 * k - H / 2 - 0.5 * k), (1.3 * k, 2.4 * k, H + 0.6 * k), "spine")
    c.box("edge_blood", (x, y0 + L / 2 + 1 * k, z + 1.2 * k - H + 0.6 * k), (1.4 * k, L - 2 * k, 1.4 * k), "blood")
    for i, (t, ln, w) in enumerate(((0.38, 4.5, 3.2), (0.7, 2.5, 1.6))):    # two uneven runs in from the edge
        c.box(f"blood_run_{i}", (x, y0 + L * t, z + 1.2 * k - H + ln * k / 2), (1.4 * k, w * k, ln * k), "blood")
    c.box("hole", (x, y0 + L - 4.5 * k, z - 2.4 * k), (1.4 * k, 2.6 * k, 2.6 * k), "hole")
    return c


def arm(torso, name, sx, upper_rot, fore_rot):
    """An arm from the shoulder: the upper arm, then the forearm, fist and wrist shackle at the elbow."""
    sh = torso.group(f"arm_{name}", (sx * 16.5, 43, 0.5), upper_rot)
    sh.box(f"upper_arm_{name}", (sx * 18.5, 35, 0), (10, 15, 10.5), "skin_dark")
    sh.box(f"arm_band_{name}", (sx * 18.5, 38.5, 0), (11, 2.6, 11.5), "strap")      # a restraint round the upper arm
    sh.box(f"arm_band_stud_{name}", (sx * 18.5, 38.5, -6.05), (1.0, 1.0, 0.6), "stud")
    sh.box(f"arm_band_buckle_{name}", (sx * 24.25, 38.5, 0), (0.7, 3.2, 2.4), "iron_lit")
    fore = sh.group(f"forearm_{name}", (sx * 19.3, 28, 0), fore_rot)
    fore.box(f"forearm_{name}_box", (sx * 19.6, 20, -0.4), (10.5, 15, 10.5), "skin")
    fore.box(f"fist_{name}", (sx * 19.8, 10.2, -0.8), (10, 7, 10), "skin_dark")
    shackle(fore, f"wrist_shackle_{name}", (sx * 19.6, 15.6, -0.4), (10.5, 4, 10.5))


def drop_cube(model, name):
    cube = next(c for c in model.cubes if c.name == name)
    model.cubes.remove(cube)
    cube.group.children.remove(cube)


def center(model, name):
    pts = next(c for c in model.cubes if c.name == name).corners()
    return tuple(float(v) for v in pts.mean(0))


ATTACK_ARM = ((100, 0, 40), (130, 0, -30))          # the wind-up: upper arm, forearm


def build(model, pose="walk"):
    root = uf.bust(model, "MIX", "PIECE")
    torso = next(g for g in model.groups if g.name == "torso")
    for sx in (-1, 1):
        drop_cube(model, f"upper_arm_{sx}")                  # the arms are rebuilt below, posable
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
    # the left arm hangs (the hunch undone so it hangs straight)
    arm(torso, "left", -1, (-uf.HUNCH, 0, -6), (4, 0, -3))
    if pose == "walk":
        arm(torso, "right", 1, (-uf.HUNCH - 14, 0, 6), (-6, 0, 3))          # a little back, dragging
    else:
        # the cleave's wind-up: the elbow out at his side, the forearm up, the cleaver over his shoulder
        arm(torso, "right", 1, *ATTACK_ARM)
    # chains from the wrist shackles: hanging to the ground (world space); none from the raised wrist
    for name in ("left", "right"):
        if pose != "walk" and name == "right":
            continue
        cuff = next(c for c in model.cubes if c.name == f"wrist_shackle_{name}").corners()
        x, z = cuff[:, 0].mean(), cuff[:, 2].mean()
        chain(root, f"wrist_chain_{name}", (x, cuff[:, 1].min(), z), 4, (0.2 if name == "right" else -0.2, 0.95))
    grip = center(model, "fist_right")
    if pose == "walk":
        # dragged behind: back and down, its spine on the ground, the bloody edge up
        c = cleaver(root, grip, (100, 0, 0))
        for down in [d / 2 for d in range(0, 120)]:
            c.rotation[0] = 90 + down
            low = min(cube.corners()[:, 1].min() for cube in model.cubes if cube.group is c)
            if low <= 0.6:
                break
    else:
        # over the shoulder: back and up, the blade behind his head, its edge up, ready to come down edge first
        cleaver(root, grip, (62, -28, 0))
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


POSES = {"walk": "walking: the cleaver dragged, spine down", "attack": "the cleave's wind-up: over his shoulder"}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    uf.PALETTE.update(PALETTE)
    k = None
    for pose in POSES:
        out = OUT / pose
        out.mkdir(parents=True, exist_ok=True)
        model = Model(f"occultech_unbound_blockout_{pose}")
        build(model, pose)
        if k is None:                                   # the same scale for both poses, set by the walking head
            head = next(c for c in model.cubes if c.name == "head")
            k = HEAD_TOP / float(head.corners()[:, 1].max())
        scale(model, k)
        model.write_bbmodel(out / f"{model.name}.bbmodel")
        uf.render_glowing(model, out, VIEWS, {"player_at": [-2.6, 0.0]})       # the player beside him, to his left
        stats = dict(model.stats(), scale=round(k, 3))
        (out / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        print(pose, stats)
    items = list(POSES.items())
    sheet.compare_sheet(OUT, items, OUT / "views_a.png", heading="The Unbound - blockout (session 1, step 3)",
                        views=("front", "three_quarter", "side", "back"))
    sheet.compare_sheet(OUT, items, OUT / "views_b.png", heading="The Unbound - blockout, more views",
                        views=("player_eye", "clay", "sil_front", "sil_side"))


if __name__ == "__main__":
    main()
