#!/usr/bin/env python3
"""
Builds the website logo (dark and light versions) from the olive branch of the
original logo plus a GFS Didot wordmark.  Needs Pillow.
    python tools/make_logo.py
Writes src/assets/img/logo.png/.webp (dark text, for light backgrounds) and
logo-light.png/.webp (cream text, for photos and the dark footer).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "photos-originals" / "logo.png"
OUT = ROOT / "src" / "assets" / "img"
DIDOT = str(ROOT / "tools" / "fonts" / "GFSDidot-Latin.ttf")
SANS = str(ROOT / "tools" / "fonts" / "Commissioner-Latin.ttf")

W, H = 1120, 584                      # drawn at 2x, shown at 560x292 or smaller
GOLD = (190, 156, 84, 255)


def branch():
    im = Image.open(SRC).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
    w, h = im.size
    cut = int(h * 0.585)
    b = im.crop((0, 0, w, cut))
    # soften the bottom edge so cut leaf tips fade instead of stopping hard
    a = b.getchannel("A")
    fade = Image.linear_gradient("L").resize((w, cut)).point(lambda v: 255 if v < 215 else int(255 * (255 - v) / 40))
    b.putalpha(Image.composite(a, Image.new("L", a.size, 0), fade))
    tw = 860
    return b.resize((tw, round(cut * tw / w)), Image.LANCZOS)


def tracked(draw, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track


def width(draw, text, font, track):
    return sum(draw.textlength(c, font=font) for c in text) + track * (len(text) - 1)


def make(word_color, name, glow=None):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    br = branch()
    canvas.alpha_composite(br, ((W - br.width) // 2 + 40, 6))
    d = ImageDraw.Draw(canvas)

    f_word = ImageFont.truetype(DIDOT, 178)
    word, t1 = "Markopoulos", 2
    ww = width(d, word, f_word, t1)
    tracked(d, ((W - ww) / 2, 282), word, f_word, word_color, t1)

    f_sub = ImageFont.truetype(SANS, 40)
    f_sub.set_variation_by_axes([500])
    sub, t2 = "OLIVE OIL", 15
    sw = width(d, sub, f_sub, t2)
    sx, sy = (W - sw) / 2, 500
    tracked(d, (sx, sy), sub, f_sub, GOLD, t2)
    line_y = sy + 27
    d.line((sx - 230, line_y, sx - 34, line_y), fill=GOLD, width=3)
    d.line((sx + sw + 34, line_y, sx + sw + 230, line_y), fill=GOLD, width=3)
    for cx in (sx - 22, sx + sw + 22):          # small diamonds at the rule ends
        d.polygon([(cx, line_y - 7), (cx + 7, line_y), (cx, line_y + 7), (cx - 7, line_y)], fill=GOLD)

    if glow:  # faint dark halo keeps cream text legible on bright photos
        halo = canvas.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .35))
        shadow = Image.new("RGBA", canvas.size, glow)
        shadow.putalpha(halo)
        shadow.alpha_composite(canvas)
        canvas = shadow

    canvas.save(OUT / f"{name}.png", optimize=True)
    canvas.save(OUT / f"{name}.webp", quality=92, method=6)
    print("  ok", name)


if __name__ == "__main__":
    make((38, 52, 28, 255), "logo")
    make((246, 241, 226, 255), "logo-light", glow=(10, 14, 6, 255))
