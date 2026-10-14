"""The Masquerade: a hero shot of the fight - the Magus with his reflections round him in different poses, and
Jack-in-the-Boxes popped up on the ground in front.

Every figure is a posed copy of the shipped models (his session 5 paint, the jack's), placed in one scene: each copy's
corners are turned and moved into place, and the two atlases are stacked into one texture for the renderer.

Run from the repository root: python tools/art/bosses/magus_hero.py
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import magus_s2 as s2, magus_s4 as s4, magus_s5 as s5, magus_jack as jack  # noqa: E402
from bosses import volley_crone_s4 as v4  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s8_ship"

# (pose, turn in degrees, x, z in blocks; -z is towards the camera; a negative turn faces the camera's side): the real
# Magus front and centre, staring out; his reflections round and behind him, each in another pose
MAGI = [("idle", -18, 0.0, 0.0), ("prism", -8, -5.6, 4.6), ("laugh", -34, 5.6, 3.8), ("curtsey", -14, -2.4, 9.2),
        ("throw", -40, 3.2, 9.6)]
JACKS = [(dict(stretch=16.0), -32, -3.8, -4.4), (dict(stretch=16.0, nod=-22.5, throw=True), -8, 3.9, -3.8)]


def posed_magus(key):
    m = s2.build(f"hero_{key}")
    s2.finish(m)
    s2.pose(m, key)
    return m


def posed_jack(kw):
    m = jack.build(**kw)
    s2.finish(m)
    jack.settle(m)
    return m


def boxes(model, bb, v_offset, turn, dx, dz):
    a = math.radians(turn)
    rot = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    shift = np.array([dx * 16, 0, dz * 16])
    out = []
    for i, c in enumerate(model.cubes):
        faces = {}
        for f, face in bb["elements"][i]["faces"].items():
            u0, v0, u1, v1 = face["uv"]
            faces[f] = dict(face, uv=[u0, v0 + v_offset, u1, v1 + v_offset])
        corners = (c.corners() @ rot.T) + shift
        out.append({"corners": corners.tolist(), "from": c.frm, "to": c.to,
                    "glow": s4.zone_for(c).startswith(s4.GLOWING), "uv": faces})
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s2.MASK = "clown"
    model, keys, positions, used, height, atlas = s5.painted()
    tmp = OUT / "hero_magus_atlas.png"
    atlas.save(tmp)
    bb, _ = s4.rig_bbmodel(model, keys, positions, tmp, height, {})
    build = s2.build
    s2.build = lambda name: jack.build()
    try:
        jmodel, jkeys, jpositions, _, jheight, jatlas = s5.painted()
    finally:
        s2.build = build
    jack.settle(jmodel)
    jtmp = OUT / "hero_jack_atlas.png"
    jatlas.save(jtmp)
    jbb, _ = s4.rig_bbmodel(jmodel, jkeys, jpositions, jtmp, jheight, {})
    combined = Image.new("RGBA", (max(atlas.width, jatlas.width), atlas.height + jatlas.height), (0, 0, 0, 0))
    combined.paste(atlas, (0, 0))
    combined.paste(jatlas, (0, atlas.height))
    texture = OUT / "hero_atlas.png"
    combined.save(texture)
    tmp.unlink()
    jtmp.unlink()

    scene = []
    for key, turn, dx, dz in MAGI:
        scene += boxes(posed_magus(key), bb, 0, turn, dx, dz)
    for kw, turn, dx, dz in JACKS:
        scene += boxes(posed_jack(kw), jbb, atlas.height, turn, dx, dz)
    views = [{"name": "hero_scene", "location": (7, 18, 5.6), "target": (2.4, 2.2, 3.0), "scale": 19.5,
              "player": False, "res": (1600, 1000)}]
    job = OUT / "hero_job.json"
    job.write_text(json.dumps({"texture": str(texture), "out": OUT.as_posix(), "boxes": scene, "views": views,
                               "player_at": (0, 0)}), encoding="utf-8")
    result = subprocess.run([str(v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                            capture_output=True, text=True)
    job.unlink()
    texture.unlink()
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    shot = OUT / "hero_scene.png"
    img = Image.open(shot)
    img.crop((0, 0, img.width, int(img.height * 0.95))).save(shot)          # past the floor's edge
    print(len(scene), "cubes in the scene")


if __name__ == "__main__":
    main()
