"""The Mirrored Magus redesign, session 5: the horror clown's face (take 2 of the mask study).

The user rejected all three masks of the study (magus_masks.py): "much more pronounced, detailed and full of depth...
focus on the face. It should be a horror clown face." So no mask: his own face, sculpted out from the illager's head
(magus_s2.mask_clown) and painted (magus_s5.paint_face_paint and friends). Renders it close up from the front, in
three-quarter, from the side and below, and on the whole figure.

Run from the repository root: python tools/art/bosses/magus_clown.py
"""
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit import sheet  # noqa: E402
from bosses import magus_s2 as s2, magus_s3 as s3, magus_s4 as s4, magus_s5 as s5  # noqa: E402

OUT = ROOT / "docs/art/bosses/mirrored_magus/overhaul/s5_clown"
VIEWS = [
    {"name": "face", "location": (0.3, 5, 5.15), "target": (0, -0.2, 5.05), "scale": 1.5, "player": False},
    {"name": "face_34", "location": (3.4, 4, 5.4), "target": (0, -0.2, 5.05), "scale": 1.65, "player": False},
    {"name": "face_side", "location": (5, 0.6, 5.1), "target": (0, -0.3, 5.05), "scale": 1.6, "player": False},
    {"name": "face_below", "location": (1.5, 4, 3.6), "target": (0, -0.2, 5.0), "scale": 1.8, "player": False},
    {"name": "front", "location": (0, 12, 3.6), "target": (0, 0, 3.6), "scale": 8.4, "player": False},
    {"name": "hero", "location": (6, 8, 4.6), "target": (0, 0, 3.8), "scale": 8.6, "player": True},
]
LABELS = {"face": "his face", "face_34": "three-quarter", "face_side": "side", "face_below": "from a player's eye",
          "front": "front", "hero": "hero"}


def main():
    if OUT.exists():
        for old in OUT.iterdir():
            if old.is_dir():
                shutil.rmtree(old)
            elif old.name != "README.md":
                old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    s2.MASK = "clown"
    model, keys, positions, used, height, atlas = s5.painted()
    atlas_path = OUT / "atlas.png"
    atlas.save(atlas_path)
    bb, _ = s4.rig_bbmodel(model, keys, positions, atlas_path, height, s3.pose_table())
    s4.render(model, bb, atlas_path, OUT, VIEWS, player_at=(2.2, 1.2))
    tw, th, pad, top = 440, 330, 12, 60
    img = Image.new("RGB", (pad + 3 * (tw + pad), top + 2 * (th + 34 + pad)), sheet.BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), "Mirrored Magus - the horror clown's face", font=sheet._font(26), fill=sheet.INK)
    for k, v in enumerate(VIEWS):
        x, y = pad + (k % 3) * (tw + pad), top + (k // 3) * (th + 34 + pad)
        img.paste(sheet._tile(OUT / f"{v['name']}.png", tw, th), (x, y))
        dr.text((x, y + th + 6), LABELS[v["name"]], font=sheet._font(17), fill=sheet.DIM)
    img.save(OUT / "clown.png")
    print(len(model.cubes), "cubes")


if __name__ == "__main__":
    main()
