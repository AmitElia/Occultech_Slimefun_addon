"""Hollow Warlord: lit, fully textured GIFs of the session 7 clips.

Every frame is the real painted model (session 6's neutral atlas, tinted the way the fight will tint it) posed from the
clip's tracks (the same keys BetterModel plays) and rendered in Blender with the textured renderer at 10 frames a
second. The glows follow the clip: his eyes and brand flare through the windup, the sweep and the raised chop and burn
white-hot from the enrage's slam on; the taken skulls flare at the call and the slam, go dark as they fall at death and
light as they rise at the spawn.

Run from the repository root, after headsman_s7.py, with the folder holding assets/ from the 26.2 client as the last
argument: python tools/art/bosses/headsman_gif.py [clip ...] <folder>
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
from bosses import headsman_s3 as s3, headsman_s4 as s4, headsman_s6 as s6, headsman_s7 as s7  # noqa: E402
from bosses import headsman_study as st  # noqa: E402

OUT = s7.OUT / "lit"
FPS = 10
SOUL, TELL, HOT, DARK = s6.SOUL, s6.HIS["tell"], s6.HIS["enraged"], s6.DARK


def mixc(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def tints(clip, t):
    """(his eyes and brand, {skull: colour}) at time t."""
    sm, sp = s7.smooth, s7.span
    lit = {k: SOUL for k in "clr"}
    if clip == "windup":
        return mixc(SOUL, TELL, sm(sp(t, 0.3, 0.9))), lit
    if clip == "sweep":
        return mixc(TELL, SOUL, sm(sp(t, 0.5, 1.0))), lit
    if clip == "attack":
        return mixc(SOUL, TELL, sm(sp(t, 0.4, 0.62)) * (1 - sm(sp(t, 0.8, 1.2)))), lit
    if clip == "call":
        k = sm(sp(t, 0.55, 0.9)) * (1 - sm(sp(t, 1.4, 1.9)))
        return SOUL, {s: mixc(SOUL, TELL, k) for s in "clr"}
    if clip == "enrage":
        his = mixc(mixc(SOUL, TELL, sm(sp(t, 0.85, 1.05))), HOT, sm(sp(t, 1.05, 1.5)))
        k = sm(sp(t, 1.05, 1.2)) * (1 - sm(sp(t, 1.6, 2.2)))
        return his, {s: mixc(SOUL, TELL, k) for s in "clr"}
    if clip == "idle_enraged":
        return HOT, lit
    if clip == "death":
        return mixc(SOUL, DARK, sm(sp(t, 1.0, 2.2))), {s: mixc(SOUL, DARK, sm(sp(t, 0.9 + d, 1.4 + d)))
                                                       for s, d in (("c", 0), ("l", 0.25), ("r", 0.45))}
    if clip == "spawn":
        return mixc(DARK, SOUL, sm(sp(t, 1.6, 2.6))), {s: mixc(DARK, SOUL, sm(sp(t, 0.6 + d, 1.4 + d)))
                                                       for s, d in (("c", 0), ("l", 0.2), ("r", 0.35))}
    return SOUL, lit


# Blender coordinates (blocks, z up); he faces +y. Orthographic.
WIDE = {"location": (-10, 13, 5.5), "target": (0, 0, 3.4), "scale": 15.0}
VIEWS = {c: dict(WIDE) for c in s7.CLIPS}
VIEWS["sweep"] = {"location": (-6, 15, 7), "target": (0, 0, 3.0), "scale": 17.0}
VIEWS["walk"] = {"location": (-14, 6, 4.5), "target": (0, 0, 3.4), "scale": 15.0}
VIEWS["idle"] = {"location": (-13, 9, 5.0), "target": (0, 0.6, 3.4), "scale": 15.0}   # his right: the hanging sword
VIEWS["enrage"] = {"location": (-10, 13, 6.5), "target": (0, 0, 4.4), "scale": 18.0}
VIEWS["idle_enraged"] = dict(VIEWS["enrage"])
VIEWS["attack"] = {"location": (-12, 11, 5.5), "target": (0, -0.5, 3.9), "scale": 17.0}
VIEWS["call"] = {"location": (-10, 13, 6.0), "target": (0, 0, 4.2), "scale": 17.0}
VIEWS["flinch"] = {"location": (-10, 13, 5.5), "target": (0, 0, 3.8), "scale": 12.0}


def frame_job(tag, i, t, model, bones, bb, atlas, groups):
    mats = matrices(model, bones, t)
    boxes = []
    for j, c in enumerate(model.cubes):
        m = mats[c.group.name] @ pivot_matrix(c.origin, c.rotation)
        lo, hi = np.array(c.frm), np.array(c.to)
        pts = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]).T
        world = (m @ pts)[:3]
        if world[1].max() < -0.5:                          # wholly under the floor: the floor hides it in game
            continue
        boxes.append({"corners": world.T.tolist(), "from": c.frm, "to": c.to, "glow": c.mat in s4.GLOWING,
                      "uv": bb["elements"][j]["faces"]})
    his, skulls = tints(tag, t)
    img = np.array(atlas).astype(float)
    img[groups["his"], :3] *= np.array(his) / 255
    for k, colour in skulls.items():
        img[groups[k], :3] *= np.array(colour) / 255
    tex = a6.save(img, OUT / "_tmp" / tag / f"atlas_{i:03d}.png")
    out = OUT / "_tmp" / tag / f"f{i:03d}"
    out.mkdir(parents=True, exist_ok=True)
    view = dict(VIEWS[tag], name="frame", player=False, res=(720, 560))
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
    st.SKIN = Image.open(Path(sys.argv[-1]) / "assets/minecraft/textures/entity/skeleton/wither_skeleton.png").convert("RGBA")
    OUT.mkdir(parents=True, exist_ok=True)
    model = s3.rest_model()
    s4.zone_materials(model)
    bb = json.loads((s7.OUT / f"{s4.NAME}.bbmodel").read_text(encoding="utf-8"))
    atlas = np.array(Image.open(s6.OUT / f"{s4.NAME}.png")).astype(float)
    groups, _ = s6.masks(atlas.shape[:2])
    tags = [a for a in argv if a in s7.CLIPS] or list(s7.CLIPS)
    for tag in tags:
        length = s7.CLIPS[tag][0]
        bones = s7.tracks(tag)
        times = [float(t) for t in np.arange(0, length + 1e-6, 1 / FPS)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            paths = list(pool.map(lambda it: frame_job(tag, it[0], it[1], model, bones, bb, atlas, groups),
                                  enumerate(times)))
        frames = [Image.open(p).convert("RGB") for p in paths]
        hold = [frames[-1]] * (6 if s7.CLIPS[tag][1] == "hold" else 2 if s7.CLIPS[tag][1] == "once" else 0)
        seq = frames + hold
        pal = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
        gif = OUT / f"warlord_{tag}.gif"
        pal[0].save(gif, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, disposal=2)
        for f in (OUT / "_tmp" / tag).rglob("*"):
            if f.is_file():
                f.unlink()
        print("gif:", gif, len(seq), "frames", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:-1])
