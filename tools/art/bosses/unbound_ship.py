"""The Unbound redesign, session 8: ship the model.

- src/main/models/occultech_the_unbound.bbmodel: the final rig from session 7 (the painted atlas with the near-white
  fire, the hitbox, the hidden flames bone, the twelve clips). The Mythic carrier OCCULTECH_THE_UNBOUND wears it.
- Refuses to ship if any two faces share a plane (they flicker in game; bosskit.checks.flicker_pairs).

Run from the repository root after the session scripts (through unbound_s7.py): python tools/art/bosses/unbound_ship.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import unbound_s2 as s2, unbound_s3 as s3  # noqa: E402

MODEL_ID = "occultech_the_unbound"
RIG = ROOT / "docs/art/bosses/the_unbound/overhaul/s7_animation" / f"{s3.MODEL_ID}.bbmodel"
OUT = ROOT / "src/main/models" / f"{MODEL_ID}.bbmodel"


def main():
    model = s2.build("check")
    s2.finish(model, s3.scale_factor())
    clash = flicker_pairs(model.cubes)
    if clash:
        raise SystemExit(f"{MODEL_ID}: faces that would flicker in game: {clash[:5]}")
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["name"] = MODEL_ID
    for tex in rig["textures"]:
        tex["name"] = f"{MODEL_ID}.png"
    OUT.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"model": MODEL_ID, "animations": sorted(a["name"] for a in rig["animations"]),
                      "elements": len(rig["elements"])}))


if __name__ == "__main__":
    main()
