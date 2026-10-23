#!/usr/bin/env python3
"""render_preview.py — render .pptx/.docx to PDF and PNG pages for visual QA (needs LibreOffice;
pdftoppm from poppler for PNGs; Pillow optional for a contact sheet).

CLI: python render_preview.py deck.pptx --outdir renders/deck [--dpi 80] [--pages 1,3,5]
Returns JSON {pdf, pngs, contact_sheet}. Rendering is a preview: LibreOffice substitutes fonts
that are not installed (e.g. Liberation Serif for Times New Roman) and draws charts slightly
differently from PowerPoint/Word.

CJK: on Linux the Windows/macOS Chinese fonts used by the zh locale (Microsoft YaHei, SimSun,
SimHei, PingFang SC) are usually missing. render() writes a temporary fontconfig file that
aliases them to Noto Sans/Serif CJK SC (package fonts-noto-cjk) so previews show real glyphs.
Disable with --no-cjk-alias. Check with:  fc-list :lang=zh
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile


def find_soffice():
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for p in ("/Applications/LibreOffice.app/Contents/MacOS/soffice", r"C:\Program Files\LibreOffice\program\soffice.exe"):
        if os.path.exists(p):
            return p
    return None


CJK_ALIASES = {
    "Microsoft YaHei": "Noto Sans CJK SC", "微软雅黑": "Noto Sans CJK SC", "PingFang SC": "Noto Sans CJK SC",
    "SimHei": "Noto Sans CJK SC", "黑体": "Noto Sans CJK SC", "DengXian": "Noto Sans CJK SC",
    "SimSun": "Noto Serif CJK SC", "宋体": "Noto Serif CJK SC", "NSimSun": "Noto Serif CJK SC",
    "FangSong": "Noto Serif CJK SC", "仿宋": "Noto Serif CJK SC", "KaiTi": "Noto Serif CJK SC",
}


def cjk_fonts_installed() -> bool:
    if not shutil.which("fc-list"):
        return False
    out = subprocess.run(["fc-list", ":lang=zh", "family"], capture_output=True, text=True).stdout
    return "CJK" in out or bool(out.strip())


def _fontconfig_env(tmpdir: str) -> dict:
    """Environment with a fontconfig file that maps Chinese Office fonts to installed Noto CJK."""
    env = dict(os.environ)
    if not shutil.which("fc-match"):
        return env
    parts = ['<?xml version="1.0"?>', '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">', "<fontconfig>"]
    base = os.environ.get("FONTCONFIG_FILE") or "/etc/fonts/fonts.conf"
    if os.path.exists(base):
        parts.append(f"<include ignore_missing=\"yes\">{base}</include>")
    for src, dst in CJK_ALIASES.items():
        parts.append(f'<match target="pattern"><test name="family" qual="any"><string>{src}</string></test>'
                     f'<edit name="family" mode="prepend" binding="strong"><string>{dst}</string></edit></match>')
    parts.append("</fontconfig>")
    p = os.path.join(tmpdir, "fonts-cjk.conf")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))
    env["FONTCONFIG_FILE"] = p
    return env


def render(path: str, outdir: str, dpi: int = 80, pages: list[int] | None = None, cjk_alias: bool = True) -> dict:
    os.makedirs(outdir, exist_ok=True)
    so = find_soffice()
    if not so:
        return {"error": "LibreOffice (soffice) not found — install it or skip rendering"}
    profile = tempfile.mkdtemp(prefix="lo_profile_")
    env = _fontconfig_env(profile) if cjk_alias else dict(os.environ)
    cmd = [so, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf", "--outdir", outdir, path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300, env=env)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(path))[0] + ".pdf")
    res = {"pdf": pdf, "pngs": [], "cjk_fonts_installed": cjk_fonts_installed()}
    if shutil.which("pdftoppm"):
        stem = os.path.join(outdir, "page")
        args = ["pdftoppm", "-r", str(dpi), "-png"]
        if pages and len(pages) == 1:
            args += ["-f", str(pages[0]), "-l", str(pages[0])]
        subprocess.run(args + [pdf, stem], check=True, timeout=300)
        pngs = sorted(glob.glob(stem + "-*.png"))
        if pages:
            keep = {int(os.path.basename(p).split("-")[-1].split(".")[0]) for p in pngs} & set(pages)
            pngs = [p for p in pngs if int(os.path.basename(p).split("-")[-1].split(".")[0]) in keep]
        res["pngs"] = pngs
        try:
            from PIL import Image
            ims = [Image.open(p) for p in pngs[:24]]
            if ims:
                cols = 4 if ims[0].width > ims[0].height else 6
                tw = 400
                th = int(ims[0].height * tw / ims[0].width)
                rows = (len(ims) + cols - 1) // cols
                sheet = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 10) + 10), "white")
                for i, im in enumerate(ims):
                    sheet.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS), (10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)))
                cs = os.path.join(outdir, "contact_sheet.png")
                # palette PNG keeps repositories small; slides are flat colours, so 192 colours is lossless enough
                sheet.quantize(colors=192, dither=Image.Dither.NONE).save(cs, optimize=True)
                res["contact_sheet"] = cs
        except ImportError:
            pass
    shutil.rmtree(profile, ignore_errors=True)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--dpi", type=int, default=80)
    ap.add_argument("--pages")
    ap.add_argument("--no-cjk-alias", action="store_true", help="do not map Chinese Office fonts to Noto CJK")
    a = ap.parse_args(argv)
    pages = [int(x) for x in a.pages.split(",")] if a.pages else None
    print(json.dumps(render(a.file, a.outdir, a.dpi, pages, not a.no_cjk_alias), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
