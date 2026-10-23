"""ooxml_clean.py — normalise package boilerplate inherited from the library default templates.

The default python-docx / python-pptx templates ship Office theme font lists
for many scripts and a ``themeFontLang`` East Asian language that is unrelated to the document.
After saving, this module rewrites the package (and every embedded workbook) so that:

* theme font lists keep only the scripts relevant to the six supported locales
  (Latin, Cyrillic via the Latin slot, Simplified Chinese ``Hans``);
* ``w:themeFontLang/@w:eastAsia`` is ``zh-CN`` for Chinese documents and absent otherwise.

Usage: ``clean_package("deck.pptx", locale="zh")``; CLI: ``python ooxml_clean.py FILE [--locale zh]``.
"""
from __future__ import annotations

import argparse
import io
import re
import zipfile

KEEP_SCRIPTS = {"Hans"}
_SCRIPT_FONT = re.compile(rb'<a:font script="([A-Za-z]+)" typeface="[^"]*"\s*/>')
_THEME_LANG = re.compile(rb'(<w:themeFontLang\b[^>]*?)\s+w:eastAsia="[^"]*"')


def _clean_theme(xml: bytes) -> bytes:
    return _SCRIPT_FONT.sub(lambda m: m.group(0) if m.group(1).decode() in KEEP_SCRIPTS else b"", xml)


def _clean_settings(xml: bytes, zh: bool) -> bytes:
    xml = _THEME_LANG.sub(rb"\1", xml)
    if zh:
        xml = re.sub(rb"<w:themeFontLang\b", b'<w:themeFontLang w:eastAsia="zh-CN"', xml, count=1)
    return xml


def clean_bytes(data: bytes, zh: bool = False) -> bytes:
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            b = src.read(info.filename)
            name = info.filename.lower()
            if re.search(r"theme/theme\d*\.xml$", name):
                b = _clean_theme(b)
            elif name.endswith("word/settings.xml"):
                b = _clean_settings(b, zh)
            elif name.endswith((".xlsx", ".docx", ".pptx")):
                b = clean_bytes(b, zh)
            dst.writestr(info, b)
    return out.getvalue()


def clean_package(path: str, locale: str | None = None) -> None:
    """Rewrite ``path`` in place (docx / pptx / xlsx)."""
    with open(path, "rb") as f:
        data = f.read()
    cleaned = clean_bytes(data, zh=(locale or "").lower().startswith("zh"))
    with open(path, "wb") as f:
        f.write(cleaned)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--locale", default=None)
    a = ap.parse_args()
    clean_package(a.file, a.locale)
    print(a.file)
