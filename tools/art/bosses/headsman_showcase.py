"""Hollow Warlord: one showcase GIF that plays the fight's story in a single take.

He rises from the floor, stands, winds up and cuts the soul sweep, raises and drops the chop, calls his warband, breaks
into the enrage, burns in the low guard and falls. Every frame is rendered like headsman_gif.py's (the real painted
model, tinted as the fight tints it) but from one fixed camera, so the clips run on as one take.

Run from the repository root, after headsman_s7.py, with the folder holding assets/ from the 26.2 client as the
argument: python tools/art/bosses/headsman_showcase.py <folder>
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bosses import headsman_gif as hg, headsman_s3 as s3, headsman_s4 as s4, headsman_s6 as s6  # noqa: E402
from bosses import headsman_s7 as s7, headsman_study as st  # noqa: E402

OUT = hg.ROOT / "docs/art/bosses/hollow_warlord/overhaul/s8_ship/warlord_showcase.gif"
FPS = hg.FPS
SIZE = (540, 420)                                          # rendered at 720x560
VIEW = {"location": (-10, 13, 6.2), "target": (0, 0, 4.1), "scale": 18.0}
# (clip, start s, end s or None for the whole clip, frames to hold the last one)
REEL = [("spawn", 0, None, 3), ("idle", 0, 2.0, 0), ("windup", 0, None, 0), ("sweep", 0, None, 2),
        ("idle", 0, 0.6, 0), ("attack", 0, None, 2), ("call", 0, None, 2), ("enrage", 0, None, 0),
        ("idle_enraged", 0, 2.4, 0), ("death", 0, None, 12)]


def main(folder):
    st.SKIN = Image.open(Path(folder) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    for c in s7.CLIPS:
        hg.VIEWS[c] = dict(VIEW)
    hg.OUT.mkdir(parents=True, exist_ok=True)
    model = s3.rest_model()
    s4.zone_materials(model)
    bb = json.loads((s7.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    atlas = np.array(Image.open(s6.OUT / f"{s4.NAME}.png")).astype(float)
    groups, _ = s6.masks(atlas.shape[:2])
    out = []
    for clip, start, end, hold in REEL:
        end = s7.CLIPS[clip][0] if end is None else end
        bones = s7.tracks(clip)
        times = [float(t) for t in np.arange(start, end + 1e-6, 1 / FPS)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            paths = list(pool.map(lambda it: hg.frame_job(clip, it[0], it[1], model, bones, bb, atlas, groups),
                                  enumerate(times)))
        seq = [Image.open(p).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS) for p in paths]
        out += seq + [seq[-1]] * hold
        for f in (hg.OUT / "_tmp" / clip).rglob("*"):
            if f.is_file():
                f.unlink()
        print(clip, len(seq), "frames", flush=True)
    pal = [f.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in out]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, disposal=2)
    print("showcase:", OUT, len(out), "frames,", round(len(out) / FPS, 1), "s,", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1])
