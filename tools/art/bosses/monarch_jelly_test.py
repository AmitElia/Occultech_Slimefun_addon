"""A tiny in-game test (made for the Gelatinous Sovereign, now the Mire Monarch): does see-through jelly with solid things inside it draw right as a
BetterModel model? BetterModel draws each bone as its own item display, and translucent faces of separate entities are
not depth-sorted against each other, so things inside the jelly may vanish or show through it from some angles.

The model `occultech_jelly_test`: a 2-block see-through jelly cube (its own bone) around an opaque core with a gold
crown on it (another bone) and a loose bone (a third). Copied to the test servers' BetterModel models folder; it is
never shipped.

  /bm reload
  /bm spawn occultech_jelly_test

Walk round it and look from above and below: the core, crown and bone should always show through the jelly, and the
jelly should never vanish behind them.

Run from the repository root: python tools/art/bosses/sovereign_jelly_test.py
"""
import base64
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES, Model, _uuid  # noqa: E402

MODEL_ID = "occultech_jelly_test"
SERVERS = [ROOT / "run/plugins/BetterModel/models", ROOT / "run-mythic-b/plugins/BetterModel/models"]
# 4 x 4 swatches on a 16 x 16 texture: see-through jelly, opaque core, gold, bone
SWATCH = {"jelly": ((0, 0), (108, 196, 60, 110)), "core": ((4, 0), (31, 90, 34, 255)),
          "gold": ((8, 0), (214, 162, 48, 255)), "bone": ((12, 0), (205, 187, 152, 255))}


def main():
    model = Model(MODEL_ID)
    root = model.group("root", (0, 0, 0))
    jelly = root.group("jelly", (0, 16, 0))
    jelly.box("jelly", (0, 16, 0), (32, 32, 32), "jelly")
    core = root.group("core", (0, 14, 0))
    core.box("core", (0, 14, 0), (14, 14, 14), "core")
    core.box("crown", (0, 23, 0), (10, 4, 10), "gold")
    loose = root.group("loose_bone", (8, 24, -6))
    loose.box("bone", (8, 24, -6), (3, 3, 12), "bone", rotation=(0, 22.5, 0))

    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x, y), rgba in SWATCH.values():
        img.paste(Image.new("RGBA", (4, 4), rgba), (x, y))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    texture = {"name": f"{MODEL_ID}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "",
               "width": 16, "height": 16, "uv_width": 16, "uv_height": 16, "particle": False, "use_as_default": True,
               "layers_enabled": False, "render_mode": "default", "render_sides": "auto", "frame_time": 1,
               "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False, "visible": True,
               "internal": True, "saved": False, "uuid": _uuid(MODEL_ID + "/atlas"),
               "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}
    bb = model.to_bbmodel(texture_size=(16, 16), textures=(texture,))
    for element, cube in zip(bb["elements"], model.cubes):
        (x, y), _ = SWATCH[cube.mat]
        for f in FACES:
            element["faces"][f] = {"uv": [x + 1, y + 1, x + 3, y + 3], "texture": 0}
    out = ROOT / "docs/art/bosses/mire_monarch/overhaul/s1_concepts" / f"{MODEL_ID}.bbmodel"
    out.write_text(json.dumps(bb, indent=1) + "\n", encoding="utf-8")
    for folder in SERVERS:
        if folder.is_dir():
            shutil.copyfile(out, folder / out.name)
    print("ok", out)


if __name__ == "__main__":
    main()
