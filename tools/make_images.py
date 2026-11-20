#!/usr/bin/env python3
"""
Create web-ready image sizes from the originals in /photos-originals.

Needs Pillow:  pip install pillow
Run from the project folder:  python tools/make_images.py

For every photo listed in PHOTOS below it writes, into src/assets/img/:
    <name>-800.jpg  <name>-800.webp  <name>-1400.jpg  <name>-1400.webp
To add a new photo: copy it into photos-originals/, add a line to PHOTOS,
run this script, then use it in a page with  {{img:<name>|Alt text}}  (see README).
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "photos-originals"
OUT = ROOT / "src" / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)

# name in site  ->  original file name
PHOTOS = {
    "archive-oil-pour": "archive-oil-pour.jpg",
    "archive-mill-line": "archive-mill-line.jpg",
    "archive-building": "archive-building.jpg",
    "archive-mill-people": "archive-mill-people.jpg",
    "today-line": "today-line.jpg",
}
WIDTHS = (800, 1400, 1800)


def save_pair(im: Image.Image, base: Path):
    im = im.convert("RGB")
    im.save(base.with_suffix(".jpg"), "JPEG", quality=80, optimize=True, progressive=True)
    im.save(base.with_suffix(".webp"), "WEBP", quality=78, method=6)


def photos():
    for name, fname in PHOTOS.items():
        p = SRC / fname
        if not p.exists():
            print(f"  ! missing {p}")
            continue
        im = ImageOps.exif_transpose(Image.open(p))
        for w in WIDTHS:
            if im.width < w:
                r = im.copy()
            else:
                r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            save_pair(r, OUT / f"{name}-{w}")
        print(f"  ok {name} ({im.width}x{im.height})")


def og_image():
    """1200x630 picture used when the site is shared on Facebook/Viber/etc."""
    p = SRC / PHOTOS["archive-oil-pour"]
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    target_ratio = 1200 / 630
    h = round(im.width / target_ratio)
    top = max(0, min(im.height - h, round(im.height * 0.42 - h / 2)))
    crop = im.crop((0, top, im.width, top + h)).resize((1200, 630), Image.LANCZOS)
    crop.save(OUT / "og-image.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    print("  ok og-image.jpg")


def logo_and_icons():
    p = SRC / "logo.png"
    im = Image.open(p).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    im = im.crop(bbox)
    w = 560
    lg = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    lg.save(OUT / "logo.png", "PNG", optimize=True)
    lg.save(OUT / "logo.webp", "WEBP", quality=90, method=6)
    print(f"  ok logo ({lg.width}x{lg.height})")

    # Icon: the olive and nearby leaves, cropped from the logo, on a light tile.
    W, H = im.size
    cx, cy, half = int(W * 0.665), int(H * 0.40), int(H * 0.26)
    olive = im.crop((cx - half, cy - half, cx + half, cy + half))
    for size, name, bg in ((180, "apple-touch-icon.png", (247, 248, 244, 255)),
                           (32, "favicon-32.png", (0, 0, 0, 0))):
        tile = Image.new("RGBA", (size, size), bg)
        inner = round(size * (0.86 if bg[3] else 1.0))
        o = olive.resize((inner, inner), Image.LANCZOS)
        tile.alpha_composite(o, ((size - inner) // 2, (size - inner) // 2))
        tile.save(OUT / name, "PNG", optimize=True)
    fav = Image.open(OUT / "favicon-32.png")
    fav.save(OUT.parent.parent / "static" / "favicon.ico", sizes=[(16, 16), (32, 32)])
    print("  ok icons")


if __name__ == "__main__":
    photos()
    og_image()
    logo_and_icons()


def light_logo():
    """Cream-text version of the logo for dark backgrounds (header over photos, footer)."""
    im = Image.open(OUT / "logo.png").convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if y >= int(h * 0.6):
                if lum < 120:
                    px[x, y] = (244, 240, 226, a)
            elif lum < 45:
                px[x, y] = (200, 205, 170, a)
            else:
                px[x, y] = (min(255, int(r * 1.25)), min(255, int(g * 1.25)), min(255, int(b * 1.1)), a)
    im.save(OUT / "logo-light.png", optimize=True)
    im.save(OUT / "logo-light.webp", quality=90, method=6)
    print("  ok logo-light")


if __name__ == "__main__":
    light_logo()
