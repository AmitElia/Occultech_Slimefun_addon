"""Review sheet: each icon at real size in an inventory slot, at 2x, at 8x on dark and light, its silhouette and its
value (grayscale) - the views the self-critique checklist needs."""
from PIL import Image, ImageDraw

SLOT_BG = (139, 139, 139)
INVENTORY = (198, 198, 198)


def slot(icon, scale=1):
    """A Minecraft-like inventory slot (bevelled) with the icon inside, at a given GUI scale."""
    s = 18 * scale
    im = Image.new("RGB", (s, s), INVENTORY)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, s - 1, s - 1), fill=SLOT_BG)
    d.line((0, 0, s - 1, 0), fill=(55, 55, 55), width=scale)
    d.line((0, 0, 0, s - 1), fill=(55, 55, 55), width=scale)
    d.line((0, s - scale, s - 1, s - scale), fill=(255, 255, 255), width=scale)
    d.line((s - scale, 0, s - scale, s - 1), fill=(255, 255, 255), width=scale)
    big = icon.resize((16 * scale, 16 * scale), Image.NEAREST)
    im.paste(big, (scale, scale), big)
    return im


def on(color, icon, scale):
    im = Image.new("RGB", (icon.width * scale, icon.height * scale), color)
    big = icon.resize(im.size, Image.NEAREST)
    im.paste(big, (0, 0), big)
    return im


def silhouette(icon, scale):
    sil = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    for y in range(icon.height):
        for x in range(icon.width):
            if icon.getpixel((x, y))[3] > 0:
                sil.putpixel((x, y), (20, 20, 24, 255))
    return on((235, 235, 240), sil, scale)


def values(icon, scale):
    gray = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    for y in range(icon.height):
        for x in range(icon.width):
            r, g, b, a = icon.getpixel((x, y))
            if a:
                v = int(0.299 * r + 0.587 * g + 0.114 * b)
                gray.putpixel((x, y), (v, v, v, 255))
    return on((80, 60, 90), gray, scale)


def sheet(icons, path, scale=8):
    """icons: [(name, PIL image)]"""
    cols = ["slot 1x (GUI 2)", "slot 2x (GUI 4)", "dark", "light", "silhouette", "values"]
    cell = 16 * scale
    pad = 14
    width = 160 + len(cols) * (cell + pad)
    height = 30 + len(icons) * (cell + pad)
    out = Image.new("RGB", (width, height), (34, 32, 40))
    d = ImageDraw.Draw(out)
    for c, title in enumerate(cols):
        d.text((160 + c * (cell + pad), 8), title, fill=(200, 200, 210))
    for r, (name, icon) in enumerate(icons):
        y = 30 + r * (cell + pad)
        d.text((8, y + cell // 2 - 6), name, fill=(230, 230, 240))
        views = [slot(icon, 2), slot(icon, 4), on((24, 22, 30), icon, scale), on((215, 210, 200), icon, scale),
                 silhouette(icon, scale), values(icon, scale)]
        for c, view in enumerate(views):
            out.paste(view, (160 + c * (cell + pad), y))
    out.save(path)
    return path
