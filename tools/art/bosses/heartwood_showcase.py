"""Heartwood Horror: one short showcase GIF of the dramatic moves, in colour, from one fixed three-quarter camera.

It unfolds from the circle and roars, rakes with the great arm, slams, goes dark and creaks, strikes from behind,
staggers as its last heart breaks (the sleeper's eyes open, the blooms go red) and collapses. Every frame is the real
painted model posed from the exported tracks and tinted as the fight tints it (heartwood_s7.py's renderer).

Encoding keeps it small and keeps the colour: one 255-colour palette for the whole reel, built so the glow colours
(the orange blooms, the womb, the lantern) get their own entries, and each frame stores only the box that changed.

Run from the repository root, after heartwood_s7.py: python tools/art/bosses/heartwood_showcase.py
"""
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bosses import heartwood_s4 as s4, heartwood_s6 as s6, heartwood_s7 as s7  # noqa: E402
from bosses.heartwood_clips import CLIPS, STATE  # noqa: E402

OUT = s7.OUT / "heartwood_showcase.gif"
FPS = 10
SIZE = (640, 496)                       # rendered at 760x590
# (clip, start s, end s or None for the whole clip, frames to hold the last one)
REEL = [("spawn", 0, None, 3), ("swipe", 0, None, 1), ("slam", 0, None, 1), ("creak", 0, None, 0),
        ("lunge", 0, None, 2), ("stagger", 0, None, 2), ("death", 0, None, 12)]
VIEW = {"location": (11.0, 14.0, 7.4), "target": (0.0, 0.5, 4.5), "scale": 19.0, "res": (760, 590)}


def palette(frames):
    """255 colours for the whole reel: the saturated (glowing) pixels are sampled on their own so the small orange
    blooms and the lantern keep their colours, the rest from a strip of frames."""
    sample = np.concatenate([np.array(f) for f in frames[::4]], axis=0)
    px = sample.reshape(-1, 3).astype(int)
    sat = px.max(1) - px.min(1)
    hot = px[sat > 60]
    rest = Image.fromarray(sample).quantize(colors=191, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = rest.getpalette()[:191 * 3]
    if len(hot):
        side = int(np.ceil(np.sqrt(len(hot))))
        pad = np.zeros((side * side, 3), np.uint8)
        pad[:len(hot)] = hot
        pad[len(hot):] = hot[0]
        hq = Image.fromarray(pad.reshape(side, side, 3)).quantize(colors=64, method=Image.Quantize.MEDIANCUT,
                                                                  dither=Image.Dither.NONE)
        pal += hq.getpalette()[:64 * 3]
    pal = (pal + [0, 0, 0] * 256)[:255 * 3]
    return pal + [0, 0, 0]


def save(frames, path):
    pal = palette(frames)
    pimg = Image.new("P", (1, 1))
    pimg.putpalette(pal)
    out = [f.quantize(palette=pimg, dither=Image.Dither.NONE) for f in frames]
    # one shared palette and a still camera: Pillow stores only the box that changed in each frame
    out[0].save(path, save_all=True, append_images=out[1:], duration=int(1000 / FPS), loop=0, disposal=1)


def main():
    s6.neutral()
    model = s7.s3.model()
    for c in model.cubes:
        if c.name.startswith("lantern_root"):
            c.mat = "bark_dark"
    bb = json.loads((s7.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    atlas = np.array(Image.open(s6.OUT / f"{s4.NAME}.png")).astype(float)
    masks = s6.masks(atlas.shape[:2])
    jobs, cache, k = [], {}, 0
    for clip, start, end, hold in REEL:
        c = CLIPS[clip]
        if clip not in cache:
            cache[clip] = s7.tracks(c)
        end = c.length if end is None else end
        times = [float(t) for t in np.arange(start, end + 1e-6, 1 / FPS)]
        for t in times + [times[-1]] * hold:
            jobs.append((k, clip, t))
            k += 1
    rendered = {}

    def render(job):
        k, clip, t = job
        key = (clip, round(t, 4))
        return k, key, s7.frame_job("showcase", k, t, model, cache[clip], bb, atlas, masks, STATE(clip, t), VIEW)

    unique = list({(c, round(t, 4)): (k, c, t) for k, c, t in reversed(jobs)}.values())
    with ThreadPoolExecutor(max_workers=6) as pool:
        for n, (k, key, path) in enumerate(pool.map(render, unique)):
            rendered[key] = Image.open(path).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)
            if n % 25 == 0:
                print("frame", n, "/", len(unique), flush=True)
    frames = [rendered[(c, round(t, 4))] for _, c, t in jobs]
    frames[len(frames) * 3 // 4].save(s7.OUT / "_tmp" / "showcase_check.png")
    save(frames, OUT)
    shutil.rmtree(s7.OUT / "_tmp" / "showcase", ignore_errors=True)
    print("showcase:", OUT, len(frames), "frames,", round(len(frames) / FPS, 1), "s,", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
