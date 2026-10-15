"""The Elder of Ash, session 8: ship the model.

- src/main/models/occultech_mire_monarch.bbmodel: the final rig from session 7 (the painted atlas with the near-white
  lava, the hitbox, the hidden blown-top bone, the eleven clips). The Mythic carrier OCCULTECH_MIRE_MONARCH wears it
  (MythicBody gives a carrier the model occultech_<id>; the id stays MIRE_MONARCH).
- Refuses to ship if any two faces share a plane (they flicker in game; bosskit.checks.flicker_pairs).

Run from the repository root after the session scripts (through ash_s7.py): python tools/art/bosses/ash_ship.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import ash_s2 as s2, ash_s3 as s3  # noqa: E402

MODEL_ID = "occultech_mire_monarch"
RIG = ROOT / "docs/art/bosses/elder_of_ash/overhaul/s7_animation" / f"{s3.MODEL_ID}.bbmodel"
OUT = ROOT / "src/main/models" / f"{MODEL_ID}.bbmodel"


def main():
    s3.setup()
    model = s2.build("check", decals=False)
    s2.finish(model)
    clash = flicker_pairs(model.cubes)
    if clash:
        raise SystemExit(f"{MODEL_ID}: faces that would flicker in game: {clash[:5]}")
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["name"] = MODEL_ID
    for tex in rig["textures"]:
        tex["name"] = f"{MODEL_ID}.png"
    OUT.write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    hidden = [g["name"] for g in rig["groups"] if not g.get("visibility", True)]
    print(json.dumps({"model": MODEL_ID, "animations": sorted(a["name"] for a in rig["animations"]),
                      "elements": len(rig["elements"]), "hidden_bones": hidden}))


if __name__ == "__main__":
    main()
