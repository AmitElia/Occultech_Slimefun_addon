"""The Mirrored Magus redesign, session 5: a mask study.

The user loves the painted body, arms, legs and hat, and disliked the panelled porcelain mask entirely (2026-10-13).
Three new masks on the same painted body, so one can be picked (magus_s2.MASKS, painted in magus_s5.paint_mask):
  volto      a clean one-piece porcelain face, a black harlequin diamond through one eye and a black tear under the
             other, small blood-red lips in a thin grin, a hairline crack
  colombina  a black-and-crimson diamond domino over his eyes only, swept wings, gold trim; below it the illager's own
             long nose and grey face, a grin stitched across it
  comedy     the theatre's comedy mask: arched brows, raised cheeks, crescent eyes that smile, a huge grinning void

Run from the repository root: python tools/art/bosses/magus_masks.py
"""
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import magus_s2 as s2, magus_s3 as s3, magus_s4 as s4, magus_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s5_masks"
VARIANTS = (("volto", "volto: one clean porcelain face"), ("colombina", "colombina: a domino over the eyes"),
            ("comedy", "comedy: the theatre's grinning mask"))
VIEWS = [
    {"name": "face", "location": (0.4, 5, 5.15), "target": (0, -0.1, 5.1), "scale": 1.45, "player": False},
    {"name": "face_34", "location": (3.2, 4, 5.3), "target": (0, -0.1, 5.1), "scale": 1.6, "player": False},
    {"name": "front", "location": (0, 12, 3.6), "target": (0, 0, 3.6), "scale": 8.4, "player": False},
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for key, _ in VARIANTS:
        s2.MASK = key
        model, keys, positions, used, height, atlas = s5.painted()
        out = OUT / key
        out.mkdir()
        atlas_path = out / "atlas.png"
        atlas.save(atlas_path)
        bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
        s4.render(model, bb, atlas_path, out, VIEWS)
        print(key, "rendered")
    tw, th, pad, top = 440, 330, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 3 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Mirrored Magus - three masks on the painted body", font=sheet._font(26), fill=sheet.INK)
    for r, v in enumerate(VIEWS):
        for c, (key, label) in enumerate(VARIANTS):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(sheet._tile(OUT / key / f"{v['name']}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), label if r == 0 else "", font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "masks.png")


if __name__ == "__main__":
    main()
