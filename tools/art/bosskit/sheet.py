"""Review sheets for boss model sessions: renders from blender_render.py laid out with labels."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/georgia.ttf"
BG = (24, 22, 28)
INK = (236, 228, 214)
DIM = (150, 142, 132)


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def _tile(path, w, h):
    im = Image.open(path).convert("RGB")
    im.thumbnail((w, h), Image.LANCZOS)
    tile = Image.new("RGB", (w, h), BG)
    tile.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return tile


def direction_sheet(d, title, stats, out):
    d = Path(d)
    tw, th, pad, top = 450, 350, 14, 70
    rows = [["sil_front", "sil_side", "sil_top", "sil_eye"], ["clay_34", "clay_eye", "flat_34"]]
    labels = {"sil_front": "front", "sil_side": "side", "sil_top": "top", "sil_eye": "player's eye",
              "clay_34": "clay, three-quarter", "clay_eye": "clay, player's eye", "flat_34": "flat material zones"}
    W = pad + 4 * (tw + pad)
    H = top + 2 * (th + 34 + pad)
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 14), title, font=_font(34), fill=INK)
    sz = stats["size_blocks"]
    dr.text((pad + 620, 26), f"{sz[0]} x {sz[1]} x {sz[2]} blocks (w x h x d)   {stats['cubes']} cubes, "
                              f"{stats['bones_with_geometry']} bones with geometry   blue figure = player",
            font=_font(17), fill=DIM)
    for r, row in enumerate(rows):
        for c, name in enumerate(row):
            x, y = pad + c * (tw + pad), top + r * (th + 34 + pad)
            img.paste(_tile(d / f"{name}.png", tw, th), (x, y))
            dr.text((x, y + th + 6), labels[name], font=_font(18), fill=DIM)
    img.save(out)


def compare_sheet(root, items, out, subject="Boss", views=("sil_eye", "sil_side", "clay_34"), heading=None):
    root = Path(root)
    tw, th, pad, top = 520, 400, 14, 64
    W = pad + len(items) * (tw + pad)
    H = top + len(views) * (th + pad) + 10
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 12), heading or f"{subject} - silhouette study (session 1)", font=_font(32), fill=INK)
    for c, (key, title) in enumerate(items):
        x = pad + c * (tw + pad)
        for r, name in enumerate(views):
            img.paste(_tile(root / key / f"{name}.png", tw, th), (x, top + r * (th + pad)))
        dr.rectangle((x, top, x + 300, top + 34), fill=BG)
        dr.text((x + 8, top + 4), f"{key}  {title}".strip(), font=_font(22), fill=INK)
    img.save(out)
