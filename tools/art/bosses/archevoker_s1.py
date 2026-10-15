"""The Archevoker redesign, session 1 step 3: the full blockout.

Everything locked so far, in one model (docs/art/bosses/archevoker/overhaul/plan.md and the session 1 READMEs):
- B take 2's floating rose-window throne and its ring of free gilded hands (archevoker_silhouettes.py), now decorated
  as a woodland-mansion piece: carved side panels under the armrests, gold capitals on the posts, gold leaf round the
  crest's emerald, a carved apron, and a small cyan rune ring under the base's point that holds it up;
- the dark priest: M2's face (the light scowl, sunken sockets, glowing slit eyes) in the mitred hood, the standing
  collar, sloped shoulders and the chain of office (archevoker_face.py);
- the eye in the palm on every gilded hand: the two casting hands (cyan on his right, purple on his left, each a real
  right or left hand) and the ring's twelve.
Three poses: resting (arms on the armrests, legs crossed), casting (arms raised, legs spread, the cyan hand drawing
on the floor, the purple hand raised) and arms folded. Model units: 16 = one block, y up, the face towards -z.

Run from the repository root: python tools/art/bosses/archevoker_s1.py
"""
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import archevoker_face as f, archevoker_silhouettes as s1, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s1_blockout"
PALETTE = dict(f.PALETTE)
SEAT = s1.SEAT
BACK_TOP, RING = s1.TAKES["B"][1]["back_top"], s1.TAKES["B"][1]["ring"]
POSES = (("rest", "resting"), ("cast", "casting"), ("fold", "arms folded"))
HANDS = {   # (centre, rotation) of the cyan (his right) and purple (his left) casting hands
    "rest": (((48, 74, -12), (0, -14, -6)), ((-48, 74, -12), (0, 14, 6))),
    "fold": (((48, 74, -12), (0, -14, -6)), ((-48, 74, -12), (0, 14, 6))),
    "cast": (((14, 22, -84), (-35, 0, 0)), ((-58, 116, -8), (8, 18, 12))),
}


def decorate_throne(t):
    """The woodland mansion's carving and gold leaf on the plain throne, and the rune ring that floats it."""
    for sx in (-1, 1):
        t.box(f"side_panel_{sx}", (sx * 25, SEAT + 5, 5), (3.4, 10, 28), "oak_dark")
        t.box(f"side_inlay_{sx}", (sx * 26.8, SEAT + 5, 5), (0.6, 6, 22), "velvet")
        for i, y in enumerate((70, 100)):                    # gold capitals on the posts
            t.box(f"post_capital_{sx}_{i}", (sx * 25, y, 24), (8.6, 2.4, 9.6), "gold")
        t.box(f"crest_leaf_{sx}", (sx * 6.5, BACK_TOP - 1.5, 20.8), (3.2, 3.2, 1), "gold", rotation=(0, 0, 45))
        t.box(f"crest_leaf_low_{sx}", (sx * 3.2, BACK_TOP - 5.5, 20.8), (2.2, 2.2, 1), "gold", rotation=(0, 0, 45))
    for i, x in enumerate((-13, 0, 13)):                     # the apron's carving
        t.box(f"apron_leaf_{i}", (x, SEAT - 8, -18.9), (3.4, 3.4, 1), "gold", rotation=(0, 0, 45))
    t.box("apron", (0, SEAT - 8, -18.2), (44, 5, 1.4), "oak_dark")
    t.box("base_tip", (0, 9.5, 0), (4, 4, 4), "gold", rotation=(0, 45, 45))
    # the back of the throne: a carved panel in a gold frame, an emerald in a gold diamond
    bh = BACK_TOP - SEAT
    t.box("back_panel", (0, SEAT + bh / 2 + 1, 27.4), (34, bh - 14, 0.8), "oak_dark")
    for sx in (-1, 1):
        t.box(f"back_frame_v_{sx}", (sx * 17.5, SEAT + bh / 2 + 1, 27.5), (1.4, bh - 14, 0.8), "gold")
    for sy in (-1, 1):
        t.box(f"back_frame_h_{sy}", (0, SEAT + bh / 2 + 1 + sy * ((bh - 14) / 2 - 0.7), 27.5), (36.4, 1.4, 0.8), "gold")
    t.box("back_diamond", (0, SEAT + bh * 0.6, 27.7), (11, 11, 0.8), "gold", rotation=(0, 0, 45))
    t.box("back_gem", (0, SEAT + bh * 0.6, 28.2), (5.5, 5.5, 0.8), "emerald", rotation=(0, 0, 45))
    for i in range(8):                                       # the rune ring under the point, flat, spirit cyan
        a = 360 * i / 8
        r = 8.5
        t.box(f"rune_ring_{i}", (r * math.sin(math.radians(a)), 6, r * math.cos(math.radians(a))),
              (2 * r * math.tan(math.pi / 8) * 0.86, 0.6, 1.1), "cyan", rotation=(0, a, 0))


def build(pose):
    s1.evoker_head = lambda g, base, k=f.K: f.face_cardinal(g)
    s1.small_hand = f.small_hand_eye
    m = Model(f"occultech_archevoker_blockout_{pose}")
    root = m.group("root", (0, 0, 0))
    s1.throne(root, BACK_TOP)
    decorate_throne(next(g for g in m.groups if g.name == "throne"))
    s1.hand_ring(root, *RING)
    torso = s1.priest(root, pose)
    head = next(g for g in m.groups if g.name == "head")
    f.hood_draped(head, torso)
    f.neck_and_shoulders(torso)
    f.chain_draped(torso)
    f.drop(m, {"pendant", "collar"})
    casting = root.group("casting", (0, 0, 0))
    (cc, cr), (pc, pr) = HANDS[pose]
    f.hand_eye(casting, "hand_cyan", cc, cr, "cyan")
    f.hand_eye(casting, "hand_purple", pc, pr, "purple", mirror=True)
    return m


VIEWS = [
    {"name": "front", "mode": "flat", "camera": "persp", "yaw": 0, "height": 3.4, "dist": 11, "target_z": 4.2,
     "player": False},
    {"name": "three_quarter", "mode": "flat", "camera": "persp", "yaw": 35, "height": 3.6, "dist": 11,
     "target_z": 4.2},
    {"name": "side", "mode": "flat", "camera": "persp", "yaw": 90, "height": 3.4, "dist": 11, "target_z": 4.2,
     "player": False},
    {"name": "back", "mode": "flat", "camera": "persp", "yaw": 160, "height": 4.2, "dist": 11, "target_z": 4.2,
     "player": False},
    {"name": "player_eye", "mode": "flat", "camera": "persp", "yaw": -25, "height": 1.62, "dist": 10, "target_z": 4.4,
     "player": False},
    {"name": "clay", "mode": "clay", "camera": "persp", "yaw": 35, "height": 3.6, "dist": 11, "target_z": 4.2,
     "player": False},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
]
LABELS = {"front": "front", "three_quarter": "three-quarter", "side": "side", "back": "back three-quarter",
          "player_eye": "a player's eye", "clay": "clay", "sil_front": "silhouette, front",
          "sil_side": "silhouette, side"}


def grid(rows, title, out, tw=420, th=330):
    pad, top = 12, 60
    cols = max(len(r) for r in rows)
    img = Image.new("RGB", (pad + cols * (tw + pad), top + len(rows) * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 14), title, font=sheet._font(26), fill=sheet.INK)
    for r, row in enumerate(rows):
        for c, (path, label) in enumerate(row):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(path, tw, th), (x, y))
            dr.text((x, y + th + 6), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.rglob("*"):                               # files only: an open folder can't be removed
        if old.is_file() and old.name != "README.md":
            old.unlink()
    v2.PALETTE.update(PALETTE)
    for pose, _ in POSES:
        m = build(pose)
        views = VIEWS if pose == "rest" else VIEWS[:2] + VIEWS[4:5]
        v2.run_blender(m.render_json(v2.PALETTE), OUT / pose, views)
        if pose == "rest":
            stats = m.stats()
            (OUT / pose / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
            m.write_bbmodel(OUT / pose / "occultech_archevoker_blockout.bbmodel")
            print("rest", stats)
        else:
            print(pose, "cubes", len(m.cubes))
    r = OUT / "rest"
    grid([[(r / f"{n}.png", LABELS[n]) for n in ("front", "three_quarter", "side", "back")]],
         "Archevoker blockout, resting: front, three-quarter, side, back", OUT / "views_a.png")
    grid([[(r / f"{n}.png", LABELS[n]) for n in ("player_eye", "clay", "sil_front", "sil_side")]],
         "Archevoker blockout, resting: player's eye, clay, silhouettes", OUT / "views_b.png")
    grid([[(OUT / p / f"{n}.png", f"{label}: {LABELS[n]}") for n in ("three_quarter", "front", "player_eye")]
          for p, label in POSES], "Archevoker blockout: the three poses", OUT / "poses.png")


if __name__ == "__main__":
    main()
