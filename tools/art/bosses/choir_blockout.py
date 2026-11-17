"""The Blaze Choir redesign, session 1 step 3: the full blockout, with everything picked.

  Soprano  the wind chime of organ pipes; Chime Fringe on its head
  Alto     the great cymbals round a tower of small ones; a cantor's cap and Finger Cymbals on its head
  Bass     the Great Bell with its fire clapper; the Bell Wheel and yoke on its head (the wheel rocks as the bell swings)
All three have vanilla's blaze head with the singing mouth. Each is shown idle and playing; the trio stands at the
spacing it has in the fight.

Run from the repository root, with the folder holding assets/ from the 26.2 client as the argument:
python tools/art/bosses/choir_blockout.py <folder>
"""
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import choir_heads as h, choir_silhouettes as cs, volley_crone_s2 as v2  # noqa: E402

OUT = ROOT / "docs/art/bosses/blaze_choir/overhaul/s1_blockout"
PLAY = cs.PLAY
SPACING = 137                                   # 8.6 blocks: three singers on the fight's orbit of 5
_pose = "idle"


def bell_wheel(g, x, y, k):
    """The wheel behind the head with the bell rope in its rim, a slim yoke over the head."""
    cx, cy, cz = x, y - 8, 16
    r = 26
    w = g.group("wheel", (cx, cy, cz), (0, 0, -24 if _pose == PLAY else 0))
    for i in range(16):
        a = 360 * i / 16
        ar = math.radians(a)
        w.box(f"wheel_{i}", (cx + r * math.sin(ar), cy + r * math.cos(ar), cz), (r * 0.42, 3.6, 3), "wood", rotation=(0, 0, -a))
        w.box(f"rope_{i}", (cx + (r + 2.1) * math.sin(ar), cy + (r + 2.1) * math.cos(ar), cz), (r * 0.44, 0.9, 1.1), "cord",
              rotation=(0, 0, -a))
    for i in range(8):                               # half-spokes: one cube across the wheel would pass the 48-unit limit
        a = 22.5 + 45 * i
        ar = math.radians(a)
        w.box(f"spoke_{i}", (cx + r / 2 * math.sin(ar), cy + r / 2 * math.cos(ar), cz), (2.4, r, 2.2), "wood", rotation=(0, 0, -a))
    w.box("hub", (cx, cy, cz), (9, 9, 4), "brass_dark", rotation=(0, 0, 45))
    g.box("yoke", (x, y + 2.5, 0), (32, 4, 6), "wood")
    for sx in (-1, 1):
        g.box(f"yoke_strap_{sx}", (x + sx * 9, y + 2.5, 0), (2, 4.6, 6.6), "brass_dark")
        g.box(f"yoke_end_{sx}", (x + sx * 17, y + 2.5, 0), (2.4, 2.8, 2.8), "brass_dark")
    g.box("axle", (x, cy, 12.5), (3, 3, 9), "brass_dark")
    g.box("axle_post", (x, y + 2.5, 8), (3, 3, 13), "brass_dark")
    g.box("axle_drop", (x, y - 3, 14.5), (3, y - cy + 12, 3), "brass_dark")


def dish(g, name, c, apex, r, mat, across=(0, 1, 0), boss=None):
    if name == "nimbus":
        h.finger_cymbals(g, c)
        return None
    return h.ORIGINAL_DISH(g, name, c, apex, r, mat, across, boss)


def setup():
    cs.head = h.textured_head("sing")
    cs.fan_crown = h.chime_fringe
    cs.spiked_crown = bell_wheel
    cs.dish = dish


def place(root, singer, x, pose):
    global _pose
    _pose = pose
    if singer == "soprano":
        cs.soprano(root, x, pose)
    elif singer == "alto":
        cs.alto(root, x, pose)
    else:
        cs.bell(root.group("bass", (x, 0, 0)), x, pose)


def single(singer, pose):
    m = Model(f"{singer}_{pose}")
    place(m.group("root", (0, 0, 0)), singer, 0, pose)
    return m


def trio():
    m = Model("trio")
    root = m.group("root", (0, 0, 0))
    place(root, "soprano", -SPACING, "idle")
    place(root, "alto", 0, "idle")
    place(root, "bass", SPACING, "idle")
    return m


VIEWS = [
    {"name": "flat_34", "mode": "flat", "camera": "persp", "yaw": -28, "height": 3.0, "dist": 11, "target_z": 3.2},
    {"name": "sil_front", "mode": "silhouette", "camera": "ortho_front", "player": False},
    {"name": "sil_side", "mode": "silhouette", "camera": "ortho_side", "player": False},
    {"name": "clay_eye", "mode": "clay", "camera": "persp", "yaw": 24, "height": 1.62, "dist": 9.5, "target_z": 3.6, "player": False},
]
PLAY_VIEW = [dict(VIEWS[0])]
TRIO_VIEW = [{"name": "trio", "mode": "flat", "camera": "persp", "yaw": -14, "height": 3.2, "dist": 25, "target_z": 3.2}]
SINGERS = ("soprano", "alto", "bass")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v2.PALETTE.update(cs.PALETTE)
    setup()
    for s in SINGERS:
        for p, vs in (("idle", VIEWS), (PLAY, PLAY_VIEW)):
            if (OUT / s / p).exists():
                shutil.rmtree(OUT / s / p)
            m = single(s, p)
            v2.run_blender(m.render_json(v2.PALETTE), OUT / s / p, vs)
            if p == "idle":
                lo, hi = m.bounds()
                print(s, "size (blocks)", [round(float(v) / 16, 2) for v in hi - lo], "cubes", len(m.cubes))
    v2.run_blender(trio().render_json(v2.PALETTE), OUT / "trio", TRIO_VIEW)
    tw, th, pad, top = 340, 300, 10, 56
    cols = (("idle", "flat_34", "three-quarter"), ("idle", "sil_front", "front"), ("idle", "sil_side", "side"),
            ("idle", "clay_eye", "a player's eye"), (PLAY, "flat_34", "playing"))
    wide = pad + len(cols) * (tw + pad)
    trio_h = int(wide * 0.42)
    img = Image.new("RGB", (wide, top + trio_h + 36 + 3 * (th + 30 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Blaze Choir: the blockout", font=sheet._font(26), fill=sheet.INK)
    img.paste(sheet._tile(OUT / "trio/trio.png", wide - 2 * pad, trio_h), (pad, top))
    dr.text((pad, top + trio_h + 6), "at the spacing of the fight", font=sheet._font(17), fill=sheet.DIM)
    y0 = top + trio_h + 36
    for r, s in enumerate(SINGERS):
        for c, (p, v, label) in enumerate(cols):
            x, y = pad + c * (tw + pad), y0 + r * (th + 30 + pad)
            img.paste(sheet._tile(OUT / s / p / f"{v}.png", tw, th), (x, y))
            dr.text((x, y + th + 5), f"{s}: {label}", font=sheet._font(16), fill=sheet.DIM)
    img.save(OUT / "blockout.png")


if __name__ == "__main__":
    main()
