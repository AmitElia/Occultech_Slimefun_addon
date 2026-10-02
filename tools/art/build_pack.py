"""Build Occultech's resource pack from the finished art.

For every item in docs/recipes.yml it looks for that item's texture in the art sessions (A, C-F) by the slug of its
display name, and writes - all in Occultech's own `occultech` namespace, so no vanilla item is ever retextured:

    assets/occultech/items/<key>.json          item model definition (what the `item_model` component points at)
    assets/occultech/models/item/<key>.json    the model (generated, handheld for weapons, the bow's own for bows)
    assets/occultech/textures/item/<key>.png   the texture; animated icons become a vertical strip + .png.mcmeta

The pack is written to src/main/pack/occultech-pack.zip (packaged into the plugin jar, unfiltered) together with
occultech-pack-items.txt, the item ids that have a model - the plugin only sets `item_model` on those.

Run: python tools/art/build_pack.py
"""
import io
import json
import os
import sys
import zipfile

import yaml
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
ART = os.path.join(ROOT, "docs", "art")
OUT = os.path.join(ROOT, "src", "main", "pack")
SESSIONS = ["session-a", "session-c", "session-d", "session-e", "session-f"]
PACK_FORMAT = 88          # resource pack format of Minecraft 26.2 (from the server jar's version.json)
FRAMETIME = 4             # ticks per animation frame (0.2 s)
NS = "occultech"
HANDHELD = {"weapon"}     # held like a tool in third person
BOW_STATES = ["standby", "pulling_0", "pulling_1", "pulling_2"]
FIXED_DATE = (2026, 1, 1, 0, 0, 0)   # deterministic zip: same art, same bytes, same hash


def slug(name):
    return name.lower().replace("'", "").replace(":", "").replace(" ", "_")


def find_art(name):
    """('static', path) | ('frames', [paths]) | ('bow', {state: path}) | None"""
    s = slug(name)
    for session in SESSIONS:
        d = os.path.join(ART, session)
        if os.path.exists(os.path.join(d, f"{s}_{BOW_STATES[0]}.png")):
            return "bow", {st: os.path.join(d, f"{s}_{st}.png") for st in BOW_STATES}
        frames = []
        while os.path.exists(os.path.join(d, f"{s}_{len(frames)}.png")):
            frames.append(os.path.join(d, f"{s}_{len(frames)}.png"))
        if frames:
            return "frames", frames
        if os.path.exists(os.path.join(d, f"{s}.png")):
            return "static", os.path.join(d, f"{s}.png")
    return None


def png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def model_ref(key):
    return f"{NS}:item/{key}"


def plain_definition(key):
    return {"model": {"type": "minecraft:model", "model": model_ref(key)}}


def bow_definition(key):
    """Like the vanilla bow's: the standby model, and while drawing the three pulling models by draw time."""
    m = lambda suffix: {"type": "minecraft:model", "model": model_ref(key + suffix)}  # noqa: E731
    return {"model": {
        "type": "minecraft:condition", "property": "minecraft:using_item",
        "on_false": m(""),
        "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                    "fallback": m("_pulling_0"),
                    "entries": [{"threshold": 0.65, "model": m("_pulling_1")}, {"threshold": 0.9, "model": m("_pulling_2")}]},
    }}


def main():
    with open(os.path.join(ROOT, "docs", "recipes.yml"), encoding="utf-8") as f:
        items = yaml.safe_load(f)["items"]
    files = {}
    with_models, without = [], []
    for item_id, item in items.items():
        key = item_id.lower()
        art = find_art(item["name"])
        if art is None:
            without.append(f"T{item.get('tier')} {item_id} ({item.get('cat')})")
            continue
        kind, src = art
        parent = "minecraft:item/handheld" if item.get("cat") in HANDHELD else "minecraft:item/generated"
        if kind == "bow":
            files[f"assets/{NS}/items/{key}.json"] = bow_definition(key)
            for st in BOW_STATES:
                suffix = "" if st == "standby" else "_" + st
                files[f"assets/{NS}/models/item/{key}{suffix}.json"] = {
                    "parent": "minecraft:item/bow", "textures": {"layer0": model_ref(key + suffix)}}
                files[f"assets/{NS}/textures/item/{key}{suffix}.png"] = png_bytes(Image.open(src[st]).convert("RGBA"))
        else:
            files[f"assets/{NS}/items/{key}.json"] = plain_definition(key)
            files[f"assets/{NS}/models/item/{key}.json"] = {"parent": parent, "textures": {"layer0": model_ref(key)}}
            if kind == "static":
                img = Image.open(src).convert("RGBA")
                assert img.size == (16, 16), (src, img.size)
                files[f"assets/{NS}/textures/item/{key}.png"] = png_bytes(img)
            else:
                frames = [Image.open(p).convert("RGBA") for p in src]
                for p, fr in zip(src, frames):
                    assert fr.size == (16, 16), (p, fr.size)
                strip = Image.new("RGBA", (16, 16 * len(frames)))
                for i, fr in enumerate(frames):
                    strip.paste(fr, (0, 16 * i))
                files[f"assets/{NS}/textures/item/{key}.png"] = png_bytes(strip)
                files[f"assets/{NS}/textures/item/{key}.png.mcmeta"] = {"animation": {"frametime": FRAMETIME}}
        with_models.append(item_id)

    # blocks (Session G): each model folder becomes a block model + its textures; the item definition (used by the
    # block's item in the inventory and by the skin display over the placed block) points at that model
    skins = {}
    gdir = os.path.join(ART, "session-g")
    for key in sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []:
        mpath = os.path.join(gdir, key, "model.json")
        if not os.path.exists(mpath):
            continue
        with open(mpath, encoding="utf-8") as f:
            model = json.load(f)
        files[f"assets/{NS}/models/block/{key}.json"] = model
        plain = {"type": "minecraft:model", "model": f"{NS}:block/{key}"}
        if os.path.isdir(os.path.join(gdir, key + "_inventory")):
            # the placed skin (an item display, context "none") and the inventory show different models: e.g. the
            # Guardian Eye's column alone (its eye is a separate, turning display) vs the column with its eye
            plain = {"type": "minecraft:select", "property": "minecraft:display_context",
                     "cases": [{"when": "none", "model": plain}],
                     "fallback": {"type": "minecraft:model", "model": f"{NS}:block/{key}_inventory"}}
        files[f"assets/{NS}/items/{key}.json"] = {"model": plain}
        for tex_ref in set(model["textures"].values()):
            name = tex_ref.split("/")[-1][len(key) + 1:]
            single = os.path.join(gdir, key, f"{name}.png")
            frames = []
            while os.path.exists(os.path.join(gdir, key, f"{name}_{len(frames)}.png")):
                frames.append(os.path.join(gdir, key, f"{name}_{len(frames)}.png"))
            target = f"assets/{NS}/textures/block/{key}_{name}.png"
            if os.path.exists(single):
                files[target] = png_bytes(Image.open(single).convert("RGBA"))
            elif frames:
                strip = Image.new("RGBA", (16, 16 * len(frames)))
                for i, p in enumerate(frames):
                    strip.paste(Image.open(p).convert("RGBA"), (0, 16 * i))
                files[target] = png_bytes(strip)
                files[target + ".mcmeta"] = {"animation": {"frametime": FRAMETIME}}
            else:
                raise SystemExit(f"{key}: texture {name} has no image")
        if os.path.exists(os.path.join(gdir, key, "part.txt")):
            continue   # a part the plugin shows itself (the Guardian Eye's eye, coloured fire), not a block skin
        base = key.split("_v")[0] if "_v" in key and key.rsplit("_v", 1)[1].isdigit() else key
        skins[base] = skins.get(base, 0) + 1
        if base == key and key.upper() in items and key.upper() not in with_models:
            with_models.append(key.upper())
            without[:] = [w for w in without if f" {key.upper()} " not in w]

    files["pack.mcmeta"] = {"pack": {
        "description": "Occultech - occult rituals, bosses and relics",
        "min_format": PACK_FORMAT, "max_format": PACK_FORMAT, "pack_format": PACK_FORMAT}}
    icon = Image.open(os.path.join(ART, "session-a", "hollow_sigil.png")).convert("RGBA").resize((64, 64), Image.NEAREST)
    files["pack.png"] = png_bytes(icon)

    os.makedirs(OUT, exist_ok=True)
    zip_path = os.path.join(OUT, "occultech-pack.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            data = files[name]
            if not isinstance(data, bytes):
                data = (json.dumps(data, indent=2) + "\n").encode("utf-8")
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    with open(os.path.join(OUT, "occultech-pack-items.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# item ids with a model in occultech-pack.zip (generated by tools/art/build_pack.py)\n")
        f.write("\n".join(with_models) + "\n")

    with open(os.path.join(OUT, "occultech-pack-skins.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# block skins: <ITEM_ID> <variants> (generated by tools/art/build_pack.py)\n")
        f.write("".join(f"{k.upper()} {n}\n" for k, n in sorted(skins.items())))

    print(f"{zip_path}: {len(with_models)} items with models ({len(skins)} blocks skinned), {os.path.getsize(zip_path)} bytes")
    print(f"{len(without)} items without art yet (blocks and held models are Session G):")
    for line in without:
        print("  " + line)


if __name__ == "__main__":
    sys.exit(main())
