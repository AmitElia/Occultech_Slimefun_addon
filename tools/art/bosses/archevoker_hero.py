"""The Archevoker: a hero shot. The painted priest on his throne with the ring, his two casting hands raised beside
him in their spell circles, from a low three-quarter angle (a perspective camera near a player's eye height).

The priest and both hands share one texture for the render: the priest's 512 x 256 atlas with the two hands' 64 x 128
atlases set under it. Output: docs/art/bosses/archevoker/overhaul/s8_ship/hero.png

Run from the repository root: python tools/art/bosses/archevoker_hero.py (after archevoker_s5.py)
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosses import archevoker_s2 as s2, archevoker_s3 as s3, archevoker_s4 as s4, archevoker_s5 as s5  # noqa: E402
from bosses import archevoker_s6 as s6  # noqa: E402

OUT = ROOT / "docs/art/bosses/archevoker/overhaul/s8_ship"
# conducting: legs planted apart, leaning in, both arms raised forward with the palms out, looking down at you
POSE = {"legs": "spread", "torso": (-8, 0, 0), "head": (-4, 0, 0),
        "arm": {"right": ((30, 86, -4), (36, 98, -18), (0, 0, -1))}}
HANDS = {"cyan": ((58, 104, -20), (6, -30, -14)), "purple": ((-60, 96, -26), (6, -30, 14))}
VIEW = [{"name": "hero", "location": (4.6, 7.4, 1.7), "target": (0.1, 0, 4.9), "scale": 12, "lens": 20,
         "player": False, "res": (1500, 1125)}]


def placed_hand(colour, centre, rot):
    """A painted casting hand (eyelid left out) turned and moved to where the pose puts it."""
    hm = s6.hand_with_lid(colour)
    for c in [c for c in hm.cubes if c.name.startswith("eyelid")]:
        hm.cubes.remove(c)
        c.group.children.remove(c)
    hm.name = f"hero_hand_{colour}"
    keys, positions, height, atlas = s5.painted(hm, s4.HAND_SIZE)
    hand = next(g for g in hm.groups if g.name == "hand")
    hand.rotation = list(rot)
    s2.translate(hm, hand, (centre[0], centre[1] - 24, centre[2]))
    return hm, keys, positions, height, atlas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = s2.rig("hero_priest")
    s2.pose(model, POSE)
    s2.finish(model)
    s3.fold_quarter_turns(model)
    model.name = "hero_priest"
    keys, positions, height, atlas = s5.painted(model, s4.SIZE)
    parts = [(model, keys, positions, 0)]
    sheet_h = height
    hand_atlases = []
    for colour, (centre, rot) in HANDS.items():
        hm, hkeys, hpos, hh, hatlas = placed_hand(colour, centre, rot)
        parts.append((hm, hkeys, hpos, sheet_h))
        hand_atlases.append((hatlas, sheet_h))
        sheet_h += hh
    combined = Image.new("RGBA", (s4.SIZE, sheet_h), (0, 0, 0, 0))
    combined.paste(atlas, (0, 0))
    x = 0
    for img, top in hand_atlases:
        combined.paste(img, (x, top))
    texture = OUT / "hero_atlas.png"
    combined.save(texture)
    boxes = []
    for m, k, pos, top in parts:
        for i, c in enumerate(m.cubes):
            faces = {}
            for f in ("north", "east", "south", "west", "up", "down"):
                key = k.get((i, f))
                if key is None:
                    faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
                    continue
                px, py, w, h = pos[key]
                faces[f] = {"uv": [px, py + top, px + w, py + top + h], "texture": 0}
            boxes.append({"corners": c.corners().tolist(), "from": c.frm, "to": c.to, "glow": c.mat in s4.GLOWING,
                          "uv": faces})
    job = OUT / "hero_job.json"
    job.write_text(json.dumps({"texture": str(texture), "out": OUT.as_posix(), "boxes": boxes, "views": VIEW,
                               "player_at": (5.0, 3.0)}), encoding="utf-8")
    result = subprocess.run([str(s4.v4.BLENDER), "-b", "--factory-startup", "--python",
                             str(ROOT / "tools/art/bosskit/blender_texture_render.py"), "--", str(job)],
                            capture_output=True, text=True)
    job.unlink()
    texture.unlink()
    if result.returncode or "TEXTURED_RENDER_DONE" not in result.stdout:
        raise SystemExit(result.stdout[-3000:] + result.stderr[-3000:])
    print("hero rendered:", OUT / "hero.png")


if __name__ == "__main__":
    main()
