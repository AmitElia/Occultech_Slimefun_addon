"""Drowned Elder: lit, fully textured GIFs of the session 7 clips.

Every frame is the real painted model (session 6's neutral atlas, tinted the way the fight will tint it) posed from the
clip's tracks and rendered in Blender with the textured renderer, at 10 frames a second. The eyes change with the
clip: the beam eyes go from calm to the white lock in the last 0.75 s before the beams fire, the head's eye glares
through the stare, and every eye dims as it dies. The surge is the dive and the emerge played back to back.

Run from the repository root, after drowned_s7.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/drowned_gif.py [clip ...] <folder>
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
from bosses import drowned_s3 as s3, drowned_s4 as s4, drowned_s6 as s6, drowned_s7 as s7  # noqa: E402

OUT = s7.OUT / "lit"
FPS = 10
BEAM, HEAD = s6.BEAM, s6.HEAD


def mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def tints(clip, t):
    """(beam-eye colour, head-eye colour) at time t."""
    sm = s7.smooth
    if clip == "aim":
        k = sm(s7.span(t, 1.25, 1.4)) * (1 - sm(s7.span(t, 2.15, 2.4)))
        return mix(BEAM["calm"], BEAM["lock"], k), HEAD["calm"]
    if clip == "stare":
        k = sm(s7.span(t, 0.5, 0.9)) * (1 - sm(s7.span(t, 2.0, 2.4)))
        return BEAM["calm"], mix(HEAD["calm"], HEAD["stare"], k)
    if clip == "spawn":
        k = sm(s7.span(t, 2.55, 2.75)) * (1 - sm(s7.span(t, 3.1, 3.5)))
        return BEAM["calm"], mix(HEAD["calm"], HEAD["stare"], k)
    if clip == "death":
        k = sm(s7.span(t, 1.3, 2.4))
        return mix(BEAM["calm"], BEAM["dead"], k), mix(HEAD["calm"], HEAD["dead"], k)
    return BEAM["calm"], HEAD["calm"]


# Blender coordinates (blocks, z up); the swimming head faces +y, the body runs back along -y. Orthographic.
VIEWS = {
    "idle": {"location": (11, 7, 15), "target": (0, -8, 2.0), "scale": 24.0},
    "spawn": {"location": (17, 10, 11), "target": (0, -1, 7.0), "scale": 28.0},
    "aim": {"location": (10, 6, 17), "target": (0, -7, 2.0), "scale": 24.0},
    "stare": {"location": (14, 12, 5), "target": (0, -3, 5.5), "scale": 25.0},
    "surge": {"location": (26, 6, 12), "target": (0, 2.5, 5.0), "scale": 30.0},
    "death": {"location": (12, 12, 10), "target": (0, -4, 4.0), "scale": 24.0},
    "flinch": {"location": (12, 9, 6), "target": (0, -6, 2.6), "scale": 20.0},
    "shed": {"location": (12, 9, 6), "target": (0, -6, 2.6), "scale": 20.0},
}


def frame_job(tag, i, clip, t, model, bones, bb, atlas, masks):
    mats = matrices(model, bones, t)
    boxes = []
    for j, c in enumerate(model.cubes):
        if c.mat == "hitbox":
            continue
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        world = (m @ pts)[:3]
        if world[1].max() < -1:                            # wholly under the floor: the floor hides it in game
            continue
        boxes.append({"corners": world.T.tolist(), "from": c.frm, "to": c.to, "glow": c.mat in ("glow", "eye"),
                      "uv": bb["elements"][j]["faces"]})
    beam_c, head_c = tints(clip, t)
    img = np.array(atlas).astype(float)
    img[masks[0], :3] *= np.array(beam_c) / 255
    img[masks[1], :3] *= np.array(head_c) / 255
    tex = a6.save(img, OUT / "_tmp" / tag / f"atlas_{i:03d}.png")
    out = OUT / "_tmp" / tag / f"f{i:03d}"
    out.mkdir(parents=True, exist_ok=True)
    view = dict(VIEWS[tag], name="frame", player=False, res=(760, 560))
    job = out / "job.json"
    job.write_text(json.dumps({"texture": str(tex), "out": out.as_posix(), "boxes": boxes, "views": [view]}),
                   encoding="utf-8")
    r = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                        str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                       capture_output=True, text=True)
    if r.returncode or "TEXTURED_RENDER_DONE" not in r.stdout:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
    return out / "frame.png"


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    model = s3.rest_model()
    s4.zone_materials(model)
    bb = json.loads((s7.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    atlas = np.array(Image.open(s6.OUT / f"{s4.NAME}.png")).astype(float)
    masks = s6.masks(atlas.shape[:2])
    tags = [a for a in argv if a in VIEWS] or ["idle", "spawn", "aim", "stare", "surge", "death"]
    for tag in tags:
        parts = [("dive", s7.CLIPS["dive"][0]), ("emerge", s7.CLIPS["emerge"][0])] if tag == "surge" \
            else [(tag, s7.CLIPS[tag][0])]
        jobs = []
        for clip, length in parts:
            bones = s7.tracks(clip)
            for t in np.arange(0, length + 1e-6, 1 / FPS):
                jobs.append((clip, float(t), bones))
        with ThreadPoolExecutor(max_workers=6) as pool:
            paths = list(pool.map(lambda it: frame_job(tag, it[0], it[1][0], it[1][1], model, it[1][2], bb, atlas,
                                                       masks), enumerate(jobs)))
        frames = [Image.open(p).convert("RGB") for p in paths]
        hold = [frames[-1]] * (6 if tag in ("death", "surge") else 2)
        seq = frames + hold
        pal = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
        gif = OUT / f"drowned_{tag}.gif"
        pal[0].save(gif, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, disposal=2)
        for f in (OUT / "_tmp" / tag).rglob("*"):
            if f.is_file():
                f.unlink()
        print("gif:", gif, len(seq), "frames", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:-1])
