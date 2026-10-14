"""The Mirrored Magus, session 8: his thrown playing card as a resource-pack item model (occultech:magus_card).

The card fans (his and the Jack-in-the-Boxes') fly as snowballs carrying this item, which the game draws facing the
camera: a white card with a thin dark edge, a big red diamond and its corner pips, on both sides (a thrown card is
seen from either side). It is saved with the other plugin-shown parts in docs/art/session-g, which build_pack.py packs.

Run from the repository root: python tools/art/bosses/magus_fx_items.py
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/art/session-g/magus_card"

PAPER, EDGE = (240, 234, 222), (70, 62, 58)
RED, DARK_RED = (196, 30, 44), (130, 14, 26)
W, H = 8, 12                      # the card's face, in texels (it is drawn 8 x 12 pixels of the model)


def face():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            edge = x in (0, W - 1) or y in (0, H - 1)
            img.putpixel((x, y), EDGE + (255,) if edge else PAPER + (255,))
    # the big diamond in the middle
    cx, cy = (W - 1) / 2, (H - 1) / 2
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if abs(x - cx) / 2.6 + abs(y - cy) / 3.6 <= 1.0:
                img.putpixel((x, y), (RED if abs(x - cx) / 2.6 + abs(y - cy) / 3.6 < 0.7 else DARK_RED) + (255,))
    img.putpixel((1, 1), RED + (255,))                 # the corner pips
    img.putpixel((W - 2, H - 2), RED + (255,))
    return img


def model():
    face_uv = [0, 0, W, H]
    edge_uv = [0, 0, 1, H]
    return {
        "parent": "minecraft:block/block",
        "textures": {"atlas": "occultech:block/magus_card_atlas", "particle": "occultech:block/magus_card_atlas"},
        "elements": [{
            "from": [4, 2, 7.8], "to": [12, 14, 8.2], "shade": False,
            "faces": {"north": {"texture": "#atlas", "uv": face_uv}, "south": {"texture": "#atlas", "uv": face_uv},
                      "east": {"texture": "#atlas", "uv": edge_uv}, "west": {"texture": "#atlas", "uv": edge_uv},
                      "up": {"texture": "#atlas", "uv": [0, 0, W, 1]}, "down": {"texture": "#atlas", "uv": [0, 0, W, 1]}},
        }],
        # a thrown item is drawn in the ground context, which the block parent shrinks to a quarter
        "display": {"ground": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]}},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    face().save(OUT / "atlas.png")
    (OUT / "model.json").write_text(json.dumps(model(), indent=2) + "\n", encoding="utf-8")
    (OUT / "part.txt").write_text("shown by the plugin, not a block skin\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
