#!/usr/bin/env python3
"""make_assets.py — build the README images in docs/ from the example renders.

  python docs/make_assets.py              # gallery images + social_preview.png
  python docs/make_assets.py --social     # only the 1280x640 social preview

Inputs are the contact sheets written by tools/render_preview.py (run the examples with
--render first). Needs Pillow. Output images are palette PNGs to keep the repository small.
"""
from __future__ import annotations

import argparse
import math
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
EX = os.path.join(ROOT, "examples")
AUTO = os.path.join(EX, "autonomous_shiftlyra")

NAVY, INK, MUTED, WHITE, CYAN, GRID = "#0B1530", "#F1F5FF", "#A3B1D6", "#FFFFFF", "#5CC8FF", "#2B3D70"
FONT_CANDIDATES = {
    True: ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
           "C:/Windows/Fonts/arialbd.ttf"],
    False: ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf"],
}


def font(size: int, bold: bool = False):
    for p in FONT_CANDIDATES[bold]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def save(im: Image.Image, name: str, colors: int = 192) -> str:
    path = os.path.join(DOCS, name)
    im.convert("RGB").quantize(colors=colors, dither=Image.Dither.NONE).save(path, optimize=True)
    return path


def tiles(sheet_path: str, n: int | None = None) -> list[Image.Image]:
    """Cut the slide thumbnails back out of a contact sheet (layout of render_preview.py)."""
    sh = Image.open(sheet_path).convert("RGB")
    tw = 400
    # 16:9 decks: 4 columns; portrait report pages: 6 columns
    cols = 4 if (sh.width - 10) // (tw + 10) == 4 else 6
    probe = sh.crop((10, 10, 10 + tw, sh.height))
    th = 225 if cols == 4 else int(tw * 297 / 210)
    rows = (sh.height - 10) // (th + 10)
    out = []
    for r in range(rows):
        for c in range(cols):
            x, y = 10 + c * (tw + 10), 10 + r * (th + 10)
            t = sh.crop((x, y, x + tw, y + th))
            if t.getextrema() == ((255, 255), (255, 255), (255, 255)):  # empty cell
                continue
            out.append(t)
    del probe
    return out[:n] if n else out


def grid(images, labels, cols, pad=16, label_h=34, bg=NAVY, fg=INK) -> Image.Image:
    w, h = images[0].size
    rows = math.ceil(len(images) / cols)
    im = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + label_h) + pad), bg)
    d = ImageDraw.Draw(im)
    f = font(18, True)
    for i, (t, lab) in enumerate(zip(images, labels)):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + pad + label_h)
        d.text((x, y + 4), lab, font=f, fill=fg)
        im.paste(t, (x, y + label_h))
        d.rectangle((x - 1, y + label_h - 1, x + w, y + label_h + h), outline=GRID)
    return im


def gallery() -> list[str]:
    made = []
    # 1. one full deck (large investor, English, comet theme) and its report
    for src, dst in ((os.path.join(AUTO, "output_large_investor_en", "renders", "deck", "contact_sheet.png"), "deck_large_investor_en.png"),
                     (os.path.join(AUTO, "output_large_investor_en", "renders", "report", "contact_sheet.png"), "report_en.png")):
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(DOCS, dst))
            made.append(dst)
    # 2. five pitch patterns: first four slides of each
    pats = ["large_investor", "small_investor", "corporate", "smb", "government"]
    rows, labs = [], []
    for p in pats:
        cs = os.path.join(AUTO, f"output_{p}_ru", "renders", "deck", "contact_sheet.png")
        if os.path.exists(cs):
            ts = tiles(cs, 4)
            rows += ts
            labs += [p] + [""] * (len(ts) - 1)
    if rows:
        save(grid(rows, labs, 4), "patterns.png")
        made.append("patterns.png")
    # 3. seven themes: title slide + one chart slide
    themes = ["light", "dark", "academic_light", "comet", "editorial", "corporate", "warm"]
    ims, labs = [], []
    for th in themes:
        d = "deck" if th == "light" else f"deck_{th}"
        cs = os.path.join(AUTO, "output_themes_ru", "renders", d, "contact_sheet.png")
        if os.path.exists(cs):
            ts = tiles(cs)
            ims.append(ts[0])
            labs.append(th)
    if ims:
        save(grid(ims, labs, 4), "themes.png")
        made.append("themes.png")
    # 4. the glossary slide in six locales
    ims, labs = [], []
    for loc in ["ru", "en", "zh", "vi", "id", "ms"]:
        cs = os.path.join(EX, f"example_{loc}", "output", "renders", "deck", "contact_sheet.png")
        if os.path.exists(cs):
            ims.append(tiles(cs, 2)[1])
            labs.append(loc)
    if ims:
        save(grid(ims, labs, 3), "glossary_locales.png")
        made.append("glossary_locales.png")
    return made


def social(path: str | None = None) -> str:
    W, H = 1280, 640
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im, "RGBA")
    # faint grid
    for x in range(0, W, 64):
        d.line((x, 0, x, H), fill=(43, 61, 112, 70))
    for y in range(0, H, 64):
        d.line((0, y, W, y), fill=(43, 61, 112, 70))
    # comet: a tail of fading dots ending in a bright head
    hx, hy = 1130, 120
    for i in range(140):
        t = i / 140
        x = hx - 370 * (1 - t)
        y = hy + 140 * (1 - t) ** 1.2
        r = 2 + 16 * t ** 2
        a = int(20 + 160 * t ** 1.5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(92, 200, 255, a // 2) if i % 3 else (255, 255, 255, a))
    for r, a in ((54, 30), (38, 60), (26, 120)):
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=(255, 255, 255, a))
    d.ellipse((hx - 17, hy - 17, hx + 17, hy + 17), fill=WHITE)
    # small rising bar chart, bottom right
    bx, by = 900, 560
    for i, v in enumerate([40, 62, 88, 120, 165, 220]):
        d.rectangle((bx + i * 52, by - v, bx + i * 52 + 34, by), fill=(255, 255, 255, 235) if i == 5 else (92, 200, 255, 150))
    d.line((bx - 10, by, bx + 6 * 52, by), fill=MUTED, width=2)
    # text
    x0 = 80
    d.text((x0, 150), "PitchComet", font=font(104, True), fill=WHITE)
    d.text((x0, 282), "Product description  \u2192  computed pitch deck + report", font=font(36), fill=INK)
    chips = ["TAM \u00b7 SAM \u00b7 SOM", "Unit economics", "NPV \u00b7 IRR \u00b7 MOIC", "QA gate", "6 languages"]
    x, y = x0, 370
    f = font(24, True)
    for c in chips:
        w = d.textlength(c, font=f) + 36
        if x + w > 860:
            x, y = x0, y + 62
        d.rounded_rectangle((x, y, x + w, y + 46), radius=23, outline=WHITE, width=2, fill=(255, 255, 255, 18))
        d.text((x + 18, y + 9), c, font=f, fill=WHITE)
        x += w + 14
    d.text((x0, 506), "Russian  \u00b7  English  \u00b7  Chinese  \u00b7  Vietnamese  \u00b7  Indonesian  \u00b7  Malay", font=font(24, True), fill=WHITE)
    d.text((x0, 556), "Agent skill  \u00b7  Python toolkit  \u00b7  editable .pptx and .docx", font=font(24), fill=MUTED)
    path = path or os.path.join(DOCS, "social_preview.png")
    im.convert("RGB").quantize(colors=255, dither=Image.Dither.NONE).save(path, optimize=True)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--social", action="store_true", help="only the social preview")
    a = ap.parse_args(argv)
    made = [] if a.social else gallery()
    made.append(os.path.basename(social()))
    print("\n".join(os.path.join("docs", m) for m in made))


if __name__ == "__main__":
    main()
