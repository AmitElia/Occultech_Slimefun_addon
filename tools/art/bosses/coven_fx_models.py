"""Witch Coven effects, E1: the throwables and the dropped hat (plan.md, "Effects and deeper attacks").

Each witch throws her own thing. The real splash potion stays the invisible carrier, so the hit logic doesn't change;
a model rides on it:
  glob   the cauldron witch: a glob of brew scooped from the cauldron, lumpy, dripping, a bubble breaking out of it
  bottle the bottle witch: one of her belt's bottles (the same bottle, so it reads as hers), tumbling end over end
  wave   the pot witch: the pot's contents heaved out in one heavy wave, a curling crest, trailing tendrils and drops
  hat    the death: the witch's hat comes off as she slumps and lands by her

The brew parts are painted in session 5's neutral greys so the role tint colours them, like the witches' brew. Everything
is painted with session 5's painters at one texel per unit into one small atlas.

Run from the repository root: python tools/art/bosses/coven_fx_models.py
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, Model  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import brood_s4 as b4, brood_s5 as b5, coven_s2 as s2, coven_s5 as s5, coven_s7 as s7  # noqa: E402
from bosses import volley_crone_s4 as v4, volley_crone_s7 as v7  # noqa: E402
from bosses.coven_set import bottle  # noqa: E402
from bosses.coven_study import hat  # noqa: E402

OUT = ROOT / "docs/art/bosses/witch_coven/overhaul/fx_models"


def glob(m):
    """Flying towards -z: a rounded glob, lumps on its back, a tail of brew streaming behind it, drops flung off."""
    g = m.group("glob", (0, 4, 0))
    s2.chamfered(g, "glob_core", (0, 4, 0), (7, 6, 7), "glow_g", 0.3)
    g.box("glob_lump_0", (2, 6, 1), (4, 3, 4), "glow_g", rotation=(0, 22.5, 0))
    g.box("glob_lump_1", (-2, 6.5, -1), (3, 2, 3), "glow_g", rotation=(0, -22.5, 0))
    g.box("glob_tail", (0, 4, 5.5), (4, 3, 4), "glow_g")                                 # the tail streaming behind
    g.box("glob_tail_end", (0, 4.5, 8.5), (2, 2, 3), "glow_g")
    g.box("drip_0", (3.5, 3, 3), (1, 1, 3), "glow_g")                                    # drops flung off the sides
    g.box("drip_1", (-3.5, 5, 4), (1, 1, 2), "glow_g")
    g.box("bubble_0", (1.5, 8, 0), (2, 2, 2), "hot_g")
    g.box("bubble_1", (-1.5, 3, 10.5), (1, 1, 1), "hot_g")


def thrown_bottle(m):
    g = m.group("bottle", (0, 4, 0))
    bottle(g, "bottle_0", (0, 3, 0), "g", 1.2)


def wave(m):
    """Flying towards -z: a thin sheet of brew heaved out of the pot, its crest curling over at the front, spray and
    tendrils flung back behind it."""
    g = m.group("wave", (0, 4, 0))
    g.box("wave_body", (0, 3.5, 0), (12, 3, 8), "glow_g", rotation=(-10, 0, 0))
    g.box("wave_crest", (0, 6, -4), (10, 3, 3), "glow_g", rotation=(-35, 0, 0))         # the crest rising...
    g.box("wave_lip", (0, 8, -5.5), (8, 2, 3), "glow_g", rotation=(-70, 0, 0))          # ...and curling over
    g.box("wave_tail_0", (-4, 3, 6), (2, 1, 5), "glow_g", rotation=(0, 22.5, 0))        # tendrils trailing behind
    g.box("wave_tail_1", (3.5, 3.5, 6.5), (2, 1, 6), "glow_g", rotation=(0, -22.5, 0))
    g.box("wave_tail_2", (0, 2.5, 5.5), (3, 1, 3), "glow_g")
    for i, (x, y, z, s) in enumerate(((-6.5, 6, -3, 2), (6.5, 5, -2, 1), (2, 10, -5, 1), (-2, 5, 9, 2), (4, 4, 10, 1))):
        g.box(f"bubble_{i}", (x, y, z), (s, s, s), "hot_g")                              # spray


def dropped_hat(m):
    g = m.group("hat_prop", (0, 0, 0))
    hat(g, 0, 0)


BUILD = {"glob": glob, "bottle": thrown_bottle, "wave": wave, "hat": dropped_hat}
TITLE = {"glob": "the cauldron witch's glob", "bottle": "the bottle witch's bottle", "wave": "the pot witch's wave",
         "hat": "the dropped hat"}


def build(key):
    m = Model(f"occultech_coven_fx_{key}")
    BUILD[key](m)
    for c in m.cubes:                               # session 2's texel snap
        lo, hi = np.array(c.frm), np.array(c.to)
        centre, size = (lo + hi) / 2, np.maximum(1, np.round(hi - lo))
        c.frm, c.to = (centre - size / 2).tolist(), (centre + size / 2).tolist()
    return m


def render(model, keys, positions, atlas_path, out, views):
    out.mkdir(parents=True, exist_ok=True)
    boxes = []
    for i, c in enumerate(model.cubes):
        uv = {}
        for f in FACES:
            key = keys.get((i, f))
            x, y, w, h = positions[key] if key else (0, 0, 0, 0)
            uv[f] = {"uv": [x, y, x + w, y + h]}
        boxes.append({"corners": c.corners().tolist(), "from": c.frm, "to": c.to,
                      "glow": s5.zone_for(c) in s5.TINTED, "uv": uv})
    job = out / "render_job.json"
    job.write_text(json.dumps({"texture": str(atlas_path), "out": out.as_posix(), "boxes": boxes, "views": views,
                               "player": False}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                            capture_output=True, text=True)
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    job.unlink()


def spin_gif(model, path, role, axis="y"):
    """A tumble in flight (the bottle end over end, the rest turning), from the software previewer."""
    frames = []
    for k in range(24):
        a = 360 * k / 24
        r = (a, 0, 0) if axis == "x" else (0, a, a * 0.3)
        bones = {model.groups[0].name: {"rotation": [(0, r, "linear")]}}
        frames.append(s7.frame(model, bones, 0, "green", yaw=-30, pitch=18, size=(240, 240), scale=13))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=50, loop=0)


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    models, keys, sizes = {}, {}, {}
    for key in BUILD:
        m = build(key)
        k = {}
        for i, c in enumerate(m.cubes):
            for f in FACES:
                w, h = v4.face_size(c, f)
                if not w or not h or b4.hidden(c, f):
                    continue
                k[(i, f)] = (key,) + s5.island_key(c, f, w, h)
                sizes[k[(i, f)]] = (w, h)
        models[key], keys[key] = m, k
    positions, used, _ = b4.pack(sizes)
    height = 64 if used <= 64 else 128
    atlas = Image.new("RGBA", (256, height), (0, 0, 0, 0))
    owner = {}
    for key, k in keys.items():
        for (i, f), isl in k.items():
            owner.setdefault(isl, (key, i, f))
    solids = {key: b5.solids_of(m) for key, m in models.items()}
    for isl, (x, y, w, h) in positions.items():
        key, i, f = owner[isl]
        patch = Image.fromarray(s5.paint_face(models[key], i, f, w, h, solids[key], solids[key]), "RGBA")
        atlas.paste(patch.resize((w + 2, h + 2), Image.NEAREST), (x - 1, y - 1))
        atlas.paste(patch, (x, y))
    atlas_path = OUT / "occultech_coven_fx.png"
    atlas.save(atlas_path)
    atlas.resize((atlas.width * 3, atlas.height * 3), Image.NEAREST).save(OUT / "atlas_preview.png")
    tinted = {}
    for role in ("green", "purple", "red"):
        img = np.array(atlas).astype(int)
        for isl, (x, y, w, h) in positions.items():
            if isl[5] in s5.TINTED:
                img[y - 1:y + h + 1, x - 1:x + w + 1, :3] = img[y - 1:y + h + 1, x - 1:x + w + 1, :3] * \
                    np.array(s5.ROLE_TINT[role]) // 255
        tinted[role] = OUT / f"occultech_coven_fx_{role}.png"
        Image.fromarray(img.astype(np.uint8), "RGBA").save(tinted[role])

    def views(key):
        k = 2.0 if key == "hat" else 1.15
        z = 0.75 if key == "hat" else 0.3
        return [{"name": "close", "location": (1.3 * k, 1.6 * k, 0.6 + 0.5 * k), "target": (0, 0, z), "scale": k,
                 "player": False},
                {"name": "side", "location": (2.2 * k, -0.1, z + 0.1), "target": (0, -0.1, z), "scale": k, "player": False}]
    tiles = []
    for key, m in models.items():
        m.write_bbmodel(OUT / f"{m.name}.bbmodel")
        roles = ("green", "purple", "red") if key != "hat" else ("green",)
        for role in roles:
            render(m, keys[key], positions, tinted[role], OUT / "renders" / key / role, views(key))
        spin_gif(m, OUT / f"{key}_tumble.gif", "green", axis="x" if key == "bottle" else "y")
        tiles.append((key, roles))
        print(key, len(m.cubes), "cubes")
    tw, th, pad, top, left = 300, 225, 8, 56, 250
    img = Image.new("RGB", (left + 3 * (tw + pad), top + len(tiles) * (th + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Witch Coven - throwables and the dropped hat (effects E1), in each role's tint",
            font=sheet._font(26), fill=sheet.INK)
    for r, (key, roles) in enumerate(tiles):
        y = top + r * (th + pad)
        dr.text((pad, y + th // 2 - 10), TITLE[key], font=sheet._font(18), fill=sheet.INK)
        for c, role in enumerate(roles):
            img.paste(sheet._tile(OUT / "renders" / key / role / "close.png", tw, th), (left + c * (tw + pad), y))
    img.save(OUT / "sheet.png")


if __name__ == "__main__":
    main()
