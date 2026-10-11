"""Volley's amethyst ward, condensed pass: blockout, paint and animation of concept A (the geode spire).

The ward is a prop, so sessions 2-7 run in one pass, on the same tools as Volley:
- the blockout: concept A with whole-texel cubes;
- the paint: the session 5 painter (Volley's ramps, baked ambient occlusion, faceted amethyst, a hot glowing core) on
  a 128 x 128 atlas;
- the clips: rise, idle, hit, shatter.

Hits stay on the server's own invisible hitbox (BossFight.FightObject, resized to the model in session 8), so the
model has no hitbox bone. The 4 hits show on the model: hits 1-3 hide `shard_0`, `shard_1`, `shard_2` (BetterModel
part visibility, wired in session 8), and the 4th plays `shatter`. The beam to Volley leaves from the core's tip, about
1.8 blocks up.

Output: docs/art/bosses/volley/wards/s2_ward/ and `occultech_volley_ward` for the test server.
Run from the repository root: python tools/art/bosses/volley_ward_s2.py
"""
import base64
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, _uuid  # noqa: E402
from bosskit import sheet  # noqa: E402
from bosses import volley_crone_s2 as s2, volley_crone_s3 as s3, volley_crone_s4 as s4  # noqa: E402
from bosses import volley_crone_s5 as s5, volley_crone_s7 as s7, volley_ward_s1 as w1  # noqa: E402

OUT = ROOT / "docs/art/bosses/volley/wards/s2_ward"
MODEL_ID = "occultech_volley_ward"
TIP = 1.8                    # blocks: where the beam to Volley leaves the core


def build():
    model = w1.geode_spire()
    model.name = MODEL_ID
    s2.snap(model)
    return model


def clips():
    zero, one = (0, 0, 0), (1, 1, 1)

    def k(*keys, interp="catmullrom"):
        return [(t, v, interp) for t, v in keys]

    grow = lambda start, end: {"scale": k((0, (0.05,) * 3), (start, (0.05,) * 3), (end, (1.15,) * 3),
                                          (end + 0.15, one))}
    rise = {"base": {"position": k((0, (0, -10, 0)), (0.35, zero)), "scale": k((0, (0.6,) * 3), (0.35, one))},
            "glow_core": grow(0.3, 0.85)}
    for i in range(4):
        rise[f"shard_{i}"] = grow(0.15 + 0.08 * i, 0.55 + 0.08 * i)
    idle = {"glow_core": {"scale": k((0, one), (1.0, (1.06, 1.06, 1.06)), (2.0, one))}}
    for i in range(4):
        sway = (2 if i % 2 else -2, 0, 2 if i < 2 else -2)
        idle[f"shard_{i}"] = {"rotation": k((0, zero), (1.0 + i * 0.1, sway), (2.0, zero))}
    hit = {"base": {"rotation": k((0, zero), (0.05, (0, 0, 5)), (0.12, (0, 0, -4)), (0.2, (0, 0, 2)), (0.3, zero),
                                  interp="linear")},
           "glow_core": {"scale": k((0, one), (0.06, (1.2, 1.2, 1.2)), (0.3, one))}}
    shatter = {"glow_core": {"scale": k((0, one), (0.12, (1.35, 1.35, 1.35)), (0.4, (0.05,) * 3))},
               "base": {"scale": k((0, one), (0.3, one), (0.6, (0.7, 0.4, 0.7)))}}
    for i, d in enumerate(((8, 0), (0, 8), (-8, 0), (0, -8))):
        shatter[f"shard_{i}"] = {"position": k((0, zero), (0.35, (d[0], 6, d[1]))),
                                 "rotation": k((0, zero), (0.35, (40 * (1 if i % 2 else -1), 0, 30))),
                                 "scale": k((0, one), (0.2, one), (0.45, (0.05,) * 3))}
    return {"rise": (1.0, "once", rise), "idle": (2.0, "loop", idle), "hit": (0.3, "once", hit),
            "shatter": (0.6, "hold", shatter)}


def views():
    """Blender views for a 2-block prop (blocks, Z up, front at +Y)."""
    return [{"name": "hero", "location": (3.2, 4.2, 2.6), "target": (0, 0, 0.9), "scale": 3.4, "player": False},
            {"name": "front", "location": (0, 6, 1.0), "target": (0, 0, 1.0), "scale": 2.8, "player": False},
            {"name": "player_eye", "location": (-2.6, 4, 1.62), "target": (0, 0, 1.0), "scale": 3.0, "player": False},
            {"name": "with_volley_scale", "location": (6, 8, 3), "target": (1.5, 0.8, 1.0), "scale": 6.5,
             "player": True},
            {"name": "ten_blocks", "location": (-3, 11, 1.62), "target": (0, 0, 1.0), "scale": 8.5, "player": True,
             "res": (640, 480)}]


def main():
    model = build()
    old = (s4.SIZE, s4.HEIGHT)
    s4.SIZE, s4.HEIGHT = 128, 128
    try:
        rects = [((i, f), *s4.face_size(c, f)) for i, c in enumerate(model.cubes) for f in FACES]
        positions, used = s4.pack(rects)
        atlas = s5.paint(model, positions)
    finally:
        size = (s4.SIZE, s4.HEIGHT)
        s4.SIZE, s4.HEIGHT = old
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_path = OUT / f"{MODEL_ID}.png"
    atlas.save(atlas_path)
    atlas.resize((size[0] * 4, size[1] * 4), Image.NEAREST).save(OUT / "atlas_preview.png")

    texture = {"name": atlas_path.name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": size[0], "height": size[1], "uv_width": size[0], "uv_height": size[1], "particle": False,
               "use_as_default": True, "layers_enabled": False, "render_mode": "default", "render_sides": "auto",
               "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
               "visible": True, "internal": True, "saved": False, "uuid": _uuid(MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(atlas_path.read_bytes()).decode()}
    bb = model.to_bbmodel(texture_size=size, textures=(texture,))
    for i, element in enumerate(bb["elements"]):
        for f in FACES:
            x, y, w, h = positions[(i, f)]
            element["faces"][f] = {"uv": [x, y, x + w, y + h], "texture": 0}
        if s4.zone_for(model.cubes[i]) == "glow":
            element["light_emission"] = 15
    clip_set = clips()
    bb["animations"] = s7.blockbench_animations(model, clip_set, MODEL_ID)
    path = OUT / f"{MODEL_ID}.bbmodel"
    path.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    if s3.SERVER_MODELS.is_dir():
        shutil.copyfile(path, s3.SERVER_MODELS / path.name)

    # painted renders, and the hit states: after 1, 2 and 3 hits a ring shard is gone
    s4.render(model, bb, atlas_path, OUT / "renders", views())
    gifs = OUT / "gifs"
    gifs.mkdir(exist_ok=True)
    for name, (length, loop, bones) in clip_set.items():
        frames = [s7.frame(model, bones, t, yaw=-30, pitch=18, size=(360, 360), scale=7.5)
                  for t in np.arange(0, length + 1e-6, 1 / 20)]
        frames[0].save(gifs / f"{name}.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
    states = Image.new("RGB", (4 * 262, 300), sheet.BG)
    dr = ImageDraw.Draw(states)
    for hits in range(4):
        gone = {f"shard_{i}" for i in range(hits)}
        im = s7.frame(model, {}, 0, yaw=-30, pitch=18, size=(260, 260), scale=5.5,
                      only=lambda c: not any(s7.s6.in_group(c, g) for g in gone))
        states.paste(im, (hits * 262, 0))
        dr.text((hits * 262 + 8, 266), f"after {hits} hit{'s' if hits != 1 else ''}", font=sheet._font(17),
                fill=sheet.DIM)
    states.save(OUT / "hit_states.png")

    names = [v["name"] for v in views()]
    tw, th, pad, top = 470, 352, 10, 54
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 32 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Volley's ward - the geode spire, painted", font=sheet._font(26), fill=sheet.INK)
    tiles = [(OUT / "renders" / f"{n}.png", n.replace("_", " ")) for n in names] + [(OUT / "hit_states.png", "hit states")]
    for k, (p, label) in enumerate(tiles):
        x, y = pad + (k % 3) * (tw + pad), top + (k // 3) * (th + 32 + pad)
        img.paste(sheet._tile(p, tw, th), (x, y))
        dr.text((x, y + th + 5), label, font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "sheet.png")
    print(json.dumps({"atlas": list(size), "rows_used": used, "cubes": len(model.cubes),
                      "displays": s3.display_count(model)[0], "size_blocks": model.stats()["size_blocks"],
                      "beam_tip_blocks": TIP}))


if __name__ == "__main__":
    main()
