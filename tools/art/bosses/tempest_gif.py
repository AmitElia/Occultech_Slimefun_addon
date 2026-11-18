"""Tempest: a lit, fully textured GIF of the seal going from broken (the frozen blast) to whole and back.

Every frame is the real painted model (session 6's neutral atlas, tinted like the fight does) posed from session 7's
`volley` clip, rendered in Blender with the textured renderer (light, shading, full-bright glows). As the seal locks the
glyphs and heart ease from calm sea teal to the near-white tell; as it breaks again they ease back.

Run from the repository root, after tempest_s7.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/tempest_gif.py <folder>
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import pivot_matrix  # noqa: E402
from bosses import archevoker_s6 as a6, volley_crone_s4 as v4  # noqa: E402
from bosses.volley_crone_s7 import matrices  # noqa: E402
from bosses import tempest_s4 as s4, tempest_s6 as s6, tempest_s7 as s7  # noqa: E402

OUT = ROOT / "docs/art/bosses/tempest/overhaul/s8_ship/seal_gif"
FRAMES = 16                    # broken -> whole over the volley clip's first 0.75 s
HOLD_WHOLE, HOLD_BROKEN = 8, 6
VIEW = {"name": "frame", "location": (10.5, 14.5, 7.4), "target": (0, 0, 4.3), "scale": 11.5, "player": False,
        "res": (720, 640)}


def lerp(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def frame_job(i, t, model, bones, bb, atlas, tint_mask, eyes):
    mats = matrices(model, bones, t)
    boxes = []
    for j, c in enumerate(model.cubes):
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        boxes.append({"corners": (m @ pts)[:3].T.tolist(), "from": c.frm, "to": c.to, "glow": c.mat in s4.GLOWING,
                      "uv": bb["elements"][j]["faces"]})
    k = float(np.clip((t - 0.25) / 0.3, 0, 1))            # calm -> tell as the seal locks
    colour = lerp(s6.STATES["calm"], s6.STATES["tell"], k)
    img = a6.tinted(atlas, tint_mask, colour)
    tex = a6.save(img, OUT / "_tmp" / f"atlas_{i:02d}.png")
    out = OUT / "_tmp" / f"f{i:02d}"
    out.mkdir(parents=True, exist_ok=True)
    job = out / "job.json"
    job.write_text(json.dumps({"texture": str(tex), "out": out.as_posix(), "boxes": boxes, "views": [VIEW]}), encoding="utf-8")
    r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)], capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
    return out / "frame.png"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = s7.rest()
    s4.zone_materials(model)
    clip = s7.clips()["volley"]
    bones = s7.tracks(clip, "volley")
    bb = json.loads((s7.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    atlas = np.array(Image.open(s6.OUT / f"{s4.NAME}.png")).astype(float)
    tint_mask, eyes, _ = s6.masks(atlas.shape[:2])
    times = [0.75 * i / (FRAMES - 1) for i in range(FRAMES)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(lambda it: frame_job(it[0], it[1], model, bones, bb, atlas, tint_mask, eyes), enumerate(times)))
    frames = [Image.open(p).convert("RGB") for p in paths]
    seq = [frames[0]] * HOLD_BROKEN + frames + [frames[-1]] * HOLD_WHOLE + frames[::-1]
    pal = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
    pal[0].save(OUT / "tempest_seal_broken_to_whole.gif", save_all=True, append_images=pal[1:], duration=60, loop=0,
                disposal=2)
    frames[0].save(OUT / "broken.png")
    frames[-1].save(OUT / "whole.png")
    for f in (OUT / "_tmp").rglob("*"):
        if f.is_file():
            f.unlink()
    print("gif:", OUT / "tempest_seal_broken_to_whole.gif", len(seq), "frames")


if __name__ == "__main__":
    main()
