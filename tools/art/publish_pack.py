"""Publish the resource pack into the occultech-pack folder (the public texture-pack repository).

Copies the pack built by build_pack.py (src/main/pack/occultech-pack.zip - the very file packaged in the plugin jar)
into the pack repository's clone (occultech_texture_pack_v1.0/occultech_texture_pack_v1.0), unzips it next to it (so textures can be browsed and diffed on GitHub) and refreshes the README
with the pack's SHA-1. The server checks that hash, so the uploaded zip must be this exact file.

Players download it from the raw link:
    https://raw.githubusercontent.com/AmitElia/occultech_texture_pack_v1.0/main/occultech-pack.zip
(resource-pack.external-url in the server's plugins/Occultech/config.yml).

Run after build_pack.py, then commit and push that clone:
    python tools/art/build_pack.py && python tools/art/publish_pack.py
"""
import datetime
import hashlib
import os
import shutil
import zipfile

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SRC = os.path.join(ROOT, "src", "main", "pack")
DEST = os.path.join(ROOT, "occultech_texture_pack_v1.0", "occultech_texture_pack_v1.0")   # the pack repository's clone
REPO = "AmitElia/occultech_texture_pack_v1.0"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/occultech-pack.zip"


def main():
    zip_src = os.path.join(SRC, "occultech-pack.zip")
    data = open(zip_src, "rb").read()
    sha1 = hashlib.sha1(data).hexdigest()
    os.makedirs(DEST, exist_ok=True)
    shutil.copyfile(zip_src, os.path.join(DEST, "occultech-pack.zip"))

    unpacked = os.path.join(DEST, "pack")
    if os.path.isdir(unpacked):
        shutil.rmtree(unpacked)
    with zipfile.ZipFile(zip_src) as z:
        z.extractall(unpacked)
        names = z.namelist()

    items = [l.strip() for l in open(os.path.join(SRC, "occultech-pack-items.txt"), encoding="utf-8")
             if l.strip() and not l.startswith("#")]
    skins = [l.split()[0] for l in open(os.path.join(SRC, "occultech-pack-skins.txt"), encoding="utf-8")
             if l.strip() and not l.startswith("#")]
    textures = sum(1 for n in names if n.endswith(".png") and "/textures/" in n)
    animated = sum(1 for n in names if n.endswith(".png.mcmeta"))

    readme = f"""# Occultech texture pack

The resource pack of **Occultech**, a Slimefun addon of occult rituals, summoned bosses and relics (Minecraft 26.2).
Everything lives in its own `occultech` namespace: no vanilla item or block is retextured, so it works alongside any
other pack.

**This repository is generated - don't edit it by hand.** It is published from the addon's art pipeline
(`tools/art/build_pack.py` and `tools/art/publish_pack.py`).

| | |
|---|---|
| Download (what the server sends players) | `{RAW}` |
| SHA-1 | `{sha1}` |
| Size | {len(data) // 1024} KiB |
| Item models | {len(items)} ({len(skins)} placed blocks with 3D skins) |
| Textures | {textures} ({animated} animated) |
| Pack format | 88 (Minecraft 26.2) |
| Published | {datetime.date.today().isoformat()} |

## Layout
- `occultech-pack.zip` - the pack itself; the server's `resource-pack.external-url` points at its raw link above.
  The server verifies the SHA-1, so this must be exactly the file built with the plugin.
- `pack/` - the same pack unzipped, for browsing textures and seeing what changed between versions.

## Server setup
In `plugins/Occultech/config.yml`:
```yaml
resource-pack:
  external-url: "{RAW}"
```
After an update, push the new zip and wait a few minutes (GitHub caches raw files briefly) before restarting the
server.
"""
    open(os.path.join(DEST, "README.md"), "w", encoding="utf-8", newline="\n").write(readme)
    attrs = "*.zip binary\n*.png binary\n*.mcmeta text eol=lf\n*.json text eol=lf\n"
    open(os.path.join(DEST, ".gitattributes"), "w", encoding="utf-8", newline="\n").write(attrs)
    print(f"published to {os.path.normpath(DEST)}: sha1 {sha1}, {len(items)} item models, {textures} textures")
    print(f"raw link: {RAW}")


if __name__ == "__main__":
    main()
