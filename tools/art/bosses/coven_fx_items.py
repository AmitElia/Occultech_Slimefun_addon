"""Witch Coven effects, E3: the throwables and the dropped hat as resource-pack item models.

E1's models (coven_fx_models.py) become item models the plugin shows on an item display:
  coven_fx_glob, coven_fx_bottle, coven_fx_wave   the throwables, riding (and spinning) on each real splash potion
  coven_fx_hat                                     the hat dropped beside a dead witch

Each cube becomes an element, centred on the model's origin (8, 8, 8), keeping its single-axis turn. Only the brew's
faces carry tintindex 0, so the dye tint (the role colour) colours the brew and leaves the glass, cork and felt as
painted. The brew glows (light 15). They are saved with the other plugin-shown parts in docs/art/session-g, which
build_pack.py packs.

Run from the repository root (after coven_fx_models.py): python tools/art/bosses/coven_fx_items.py
"""
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import FACES  # noqa: E402
import blockkit  # noqa: E402
import session_g as g  # noqa: E402
from bosses import coven_fx_models as fx, coven_s5 as s5  # noqa: E402

AXES = "xyz"


def item_model(name, model, keys, positions, atlas):
    m = blockkit.Model(f"coven_fx_{name}")
    m.part = True
    tex = m.texture("atlas", atlas)
    lo = np.min([np.min(c.corners(), 0) for c in model.cubes], 0)
    hi = np.max([np.max(c.corners(), 0) for c in model.cubes], 0)
    shift = np.array([8, 8, 8]) - (lo + hi) / 2
    su, sv = 16 / atlas.width, 16 / atlas.height
    tinted = False
    for i, c in enumerate(model.cubes):
        glow = s5.zone_for(c) in s5.TINTED
        faces = {}
        for f in FACES:
            key = keys.get((i, f))
            if key is None:
                continue
            x, y, w, h = positions[key]
            faces[f] = (tex, [x * su, y * sv, (x + w) * su, (y + h) * sv])
        if not faces:
            continue
        frm = (np.array(c.frm) + shift).round(3).tolist()
        to = (np.array(c.to) + shift).round(3).tolist()
        turned = [(AXES[k], v) for k, v in enumerate(c.rotation) if abs(v) > 1e-6]
        if len(turned) > 1:
            raise SystemExit(f"{name}/{c.name}: an item model element turns on one axis only")
        el = m.box(frm, to, faces, shade=not glow, light=15 if glow else 0,
                   rotation=turned[0] if turned else None)
        if turned:
            el["rotation"]["origin"] = (np.array(c.origin) + shift).round(3).tolist()
        if glow:
            for face in el["faces"].values():
                face["tintindex"] = 0
            tinted = True
        for v in frm + to:
            if not -16 <= v <= 32:
                raise SystemExit(f"{name}/{c.name}: outside -16..32")
    return m, tinted


def main():
    models, keys, positions, atlas = fx.painted()
    for name, model in models.items():
        m, tinted = item_model(name, model, keys[name], positions, atlas)
        g.save(m)
        if tinted:
            open(os.path.join(g.OUT, m.key, "tint.txt"), "w").write("dye\n")
        print(m.key, len(m.elements), "elements", "tinted" if tinted else "")


if __name__ == "__main__":
    main()
