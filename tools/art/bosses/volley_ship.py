"""Volley redesign, session 8: ship the Amethyst Crone and his ward.

- src/main/models/occultech_volley.bbmodel: the session 7 rig (painted, variants, hitbox, the eight clips), without
  the six held test poses of session 3;
- src/main/models/occultech_volley_ward.bbmodel: the ward;
- the muzzle: where the bolt leaves the arbalest in the aim pose (the burst clip at the first shot), in blocks in the
  carrier's frame (x to its left, y up, z forward). Volley.java launches the real arrows from there.

Run from the repository root after the session scripts: python tools/art/bosses/volley_ship.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import pivot_matrix  # noqa: E402
from bosses import volley_crone_s3 as s3, volley_crone_s6 as s6, volley_crone_s7 as s7, volley_ward_s2 as ward  # noqa: E402

MODELS = ROOT / "src/main/models"
RIG = ROOT / "docs/art/bosses/volley/overhaul/s7_animation" / f"{s3.MODEL_ID}.bbmodel"


def muzzle():
    """The bolt tip's far end at the first shot of the burst, in the carrier's frame (blocks)."""
    model = s6.build()
    _, _, bones = s7.clips(model)["burst"]
    mats = s7.matrices(model, bones, s7.SHOTS[0])
    tip = next(c for c in model.cubes if c.name == "bolt_tip")
    m = mats[tip.group.name] @ pivot_matrix(tip.origin, tip.rotation)
    lo, hi = np.array(tip.frm), np.array(tip.to)
    end = np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2, 1.0])   # the point: the -Y end, down the stock
    p = (m @ end)[:3] / 16
    # BetterModel turns Blockbench's model round (X and Z negated): its front (-Z) faces the entity's forward
    return {"x": round(float(-p[0]), 3), "y": round(float(p[1]), 3), "z": round(float(-p[2]), 3)}


def main():
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["name"] = "occultech_volley"
    clips = set(s7.clips(s6.build()))
    # the held test poses go; the clips that share a name with one (idle, wards, stagger) replaced it in session 7
    rig["animations"] = [a for a in rig["animations"] if a["name"] in clips]
    (MODELS / "occultech_volley.bbmodel").write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    ward_src = ward.OUT / f"{ward.MODEL_ID}.bbmodel"
    (MODELS / f"{ward.MODEL_ID}.bbmodel").write_bytes(ward_src.read_bytes())
    tip = muzzle()
    out = ROOT / "docs/art/bosses/volley/overhaul/s8_ship"
    out.mkdir(parents=True, exist_ok=True)
    (out / "muzzle.json").write_text(json.dumps({"aim_pose_muzzle_blocks": tip}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"animations": [a["name"] for a in rig["animations"]], "muzzle": tip}))


if __name__ == "__main__":
    main()
