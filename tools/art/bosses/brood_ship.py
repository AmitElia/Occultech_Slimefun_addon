"""Brood Mother redesign, session 8: ship her.

- src/main/models/occultech_brood_mother.bbmodel: the session 7 rig (painted, glowing eyes and flames, hair cards,
  hitbox, the nine clips), without the six held test poses of session 3.
- Refuses to ship if any two faces share a plane (they flicker in game; bosskit.checks.flicker_pairs).

Run from the repository root after the session scripts: python tools/art/bosses/brood_ship.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "art"))
from bosskit.bbmodel import rename_group  # noqa: E402
from bosskit.checks import flicker_pairs  # noqa: E402
from bosses import brood_s3 as s3, brood_s4 as s4, brood_s7 as s7  # noqa: E402

MODELS = ROOT / "src/main/models"
MODEL_ID = "occultech_brood_mother"
RIG = ROOT / "docs/art/bosses/brood_mother/overhaul/s7_animation" / f"{s3.MODEL_ID}.bbmodel"


def main():
    clash = flicker_pairs(s4.rig().cubes)
    if clash:
        raise SystemExit(f"{MODEL_ID}: faces that would flicker in game: {clash[:5]}")
    rig = json.loads(RIG.read_text(encoding="utf-8"))
    rig["name"] = MODEL_ID
    clips = set(s7.clips())
    rig["animations"] = [a for a in rig["animations"] if a["name"] in clips]   # the held test poses stay in review
    # BetterModel's "h" tag turns only the head bone; "hi" (head with children) turns what hangs off it too, so the
    # eyes, jaws and anything else on the head follow where she looks
    rename_group(rig, "h_head", "hi_head")
    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / f"{MODEL_ID}.bbmodel").write_text(json.dumps(rig, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"model": MODEL_ID, "animations": [a["name"] for a in rig["animations"]],
                      "elements": len(rig["elements"])}))


if __name__ == "__main__":
    main()
