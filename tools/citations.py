"""citations.py — bibliographic references and in-text citations for all locales.

Styles (``style``):
  * ``gost``     — ГОСТ Р 7.0.5-2008 «Библиографическая ссылка» (ru default; footnotes)
  * ``apa``      — APA 7th edition, author-date (en default)
  * ``chicago``  — Chicago Manual of Style, author-date variant (en alternative)
  * ``gbt7714``  — GB/T 7714-2015 《信息与文献 参考文献著录规则》, numeric 顺序编码制 (zh default)

Source record (all fields optional except ``id`` and ``title``)::

  {"id": "nasa_trl", "type": "web",            # web | book | article | report | standard | law | dataset
   "authors": ["Doe J. A."] | "org": "NASA",
   "title": "Technology Readiness Levels", "container": "NASA.gov", "publisher": "...", "place": "...",
   "year": 2023, "date": "2023-09-27", "volume": "", "issue": "", "pages": "", "number": "",
   "url": "https://...", "doi": "", "accessed": "2026-10-20",
   "text": "verbatim reference, used as-is for every style", "text_gost": "... used only for gost"}

CLI: python citations.py --style gbt7714 --input sources.json      (prints formatted list)
"""
from __future__ import annotations

import datetime as _dt
import json
import sys

STYLE_FOR_LOCALE = {"ru": "gost", "en": "apa", "zh": "gbt7714"}
INLINE_FOR_STYLE = {"gost": "footnotes", "apa": "author_date", "chicago": "author_date", "gbt7714": "numeric"}
GBT_TYPE = {"book": "M", "article": "J", "report": "R", "standard": "S", "law": "Z", "web": "EB",
            "dataset": "DS", "newspaper": "N", "thesis": "D", "patent": "P"}
GOST_TYPE = {"web": "[Электронный ресурс]", "dataset": "[Электронный ресурс]"}


def _d(s):
    if not s:
        return None
    if isinstance(s, _dt.date):
        return s
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _authors(src) -> list[str]:
    a = src.get("authors")
    if isinstance(a, str):
        a = [a]
    if a:
        return list(a)
    return [src["org"]] if src.get("org") else []


def _year(src):
    if src.get("year"):
        return str(src["year"])
    d = _d(src.get("date"))
    return str(d.year) if d else None


def _end(s: str) -> str:
    s = s.strip()
    return s if s.endswith((".", "。", "?", "!")) else s + "."


def surname(name: str) -> str:
    n = name.strip()
    if "," in n:
        return n.split(",")[0].strip()
    parts = n.split()
    # "Doe J. A." -> Doe ; "Jane A. Doe" -> Doe ; organisations stay whole
    if len(parts) > 1 and all(len(p.rstrip(".")) <= 2 for p in parts[1:]):
        return parts[0]
    if len(parts) > 1 and all(len(p.rstrip(".")) <= 2 for p in parts[:-1]):
        return parts[-1]
    return n


def format_reference(src: dict, style: str = "gost") -> str:
    if src.get(f"text_{style}"):
        return src[f"text_{style}"]
    if src.get("text"):
        return src["text"]
    return {"gost": _gost, "apa": _apa, "chicago": _chicago, "gbt7714": _gbt}.get(style, _apa)(src)


def _gost(s):
    au = _authors(s) if s.get("authors") else []
    t = s.get("title", "")
    typ = s.get("type", "web")
    head = (", ".join(au).rstrip(".") + ". ") if au else ""
    out = f"{head}{t}"
    if typ in GOST_TYPE and s.get("url"):
        out += f" {GOST_TYPE[typ]}"
    if s.get("subtitle"):
        out += f" : {s['subtitle']}"
    if s.get("org") and not s.get("authors"):
        out += f" / {s['org']}"
    if s.get("container"):
        out += f" // {s['container']}"
    y = _year(s)
    if typ in ("book", "report", "standard") and (s.get("place") or s.get("publisher")):
        out += ". " + " : ".join(x for x in (s.get("place"), s.get("publisher")) if x)
        if y:
            out += f", {y}"
    elif y:
        out += f". {y}"
    if s.get("volume"):
        out += f". Т. {s['volume']}"
    if s.get("issue"):
        out += f", № {s['issue']}"
    if s.get("pages"):
        out += f". С. {s['pages']}"
    if s.get("url"):
        acc = _d(s.get("accessed"))
        out += f". URL: {s['url']}" + (f" (дата обращения: {acc.strftime('%d.%m.%Y')})" if acc else "")
    return _end(out)


def _apa_author(a: str) -> str:
    p = a.split()
    if len(p) > 1 and all(len(x.rstrip(".")) <= 2 for x in p[1:]):   # "Doe J. A." -> "Doe, J. A."
        return f"{p[0]}, {' '.join(p[1:])}"
    return a


def _apa(s):
    au = _authors(s)
    if len(au) > 1:
        names = ", ".join(_apa_author(a) for a in au[:-1]) + ", & " + _apa_author(au[-1])
    else:
        names = _apa_author(au[0]) if au else ""
    y = _year(s) or "n.d."
    d = _d(s.get("date"))
    date = f"{y}, {d.strftime('%B')} {d.day}" if d and s.get("type") in ("web", "newspaper") else y
    title = s.get("title", "")
    out = (f"{names}{'' if names.endswith('.') else '.'} ({date}). " if names else f"{_end(title)} ({date}). ")
    if names:
        out += f"{_end(title)} "
    if s.get("type") == "article" and s.get("container"):
        out += f"{s['container']}"
        if s.get("volume"):
            out += f", {s['volume']}"
        if s.get("issue"):
            out += f"({s['issue']})"
        if s.get("pages"):
            out += f", {s['pages']}"
        out += ". "
    elif s.get("container") and s.get("container") not in names:
        out += f"{_end(s['container'])} "
    elif s.get("publisher") and s.get("publisher") not in names:
        out += f"{_end(s['publisher'])} "
    if s.get("doi"):
        out += f"https://doi.org/{s['doi']}"
    elif s.get("url"):
        acc = _d(s.get("accessed"))
        if acc and s.get("type") in ("web", "dataset", "law"):
            out += f"Retrieved {acc.strftime('%B')} {acc.day}, {acc.year}, from {s['url']}"
        else:
            out += s["url"]
    return out.strip()


def _chicago(s):
    au = _authors(s)
    names = (au[0] if len(au) == 1 else ", ".join(au[:-1]) + (", and " if len(au) > 2 else " and ") + au[-1]) if au else ""
    y = _year(s) or "n.d."
    title = s.get("title", "")
    q = f"\u201c{title}.\u201d" if s.get("type") in ("article", "web", "newspaper") else f"{_end(title)}"
    out = f"{_end(names)} {y}. {q}" if names else f"{q} {y}."
    if s.get("container"):
        out += f" {s['container']}"
        if s.get("volume"):
            out += f" {s['volume']}"
        if s.get("issue"):
            out += f" ({s['issue']})"
        if s.get("pages"):
            out += f": {s['pages']}"
        out += "."
    elif s.get("publisher"):
        out += " " + _end(": ".join(x for x in (s.get("place"), s.get("publisher")) if x))
    acc = _d(s.get("accessed"))
    if acc and s.get("url"):
        out += f" Accessed {acc.strftime('%B')} {acc.day}, {acc.year}."
    if s.get("doi"):
        out += f" https://doi.org/{s['doi']}."
    elif s.get("url"):
        out += f" {s['url']}."
    return out.strip()


def _gbt(s):
    au = _authors(s)
    names = ", ".join(a.rstrip(".") for a in au[:3]) + (", 等" if len(au) > 3 and _is_cjk(au[0]) else ", et al" if len(au) > 3 else "")
    online = bool(s.get("url") or s.get("doi"))
    typ = GBT_TYPE.get(s.get("type", "web"), "Z")
    if s.get("type") == "law" and online:
        typ = "EB"
    mark = f"[{typ}/OL]" if online else f"[{typ}]"
    out = f"{names}. " if names else ""
    out += f"{s.get('title', '')}{mark}"
    if s.get("type") == "article" and s.get("container"):
        out += f". {s['container']}, {_year(s) or ''}"
        if s.get("volume"):
            out += f", {s['volume']}"
        if s.get("issue"):
            out += f"({s['issue']})"
        if s.get("pages"):
            out += f": {s['pages']}"
    elif s.get("publisher") or s.get("place"):
        out += ". " + ": ".join(x for x in (s.get("place"), s.get("publisher")) if x)
        if _year(s):
            out += f", {_year(s)}"
    elif s.get("type") not in ("web", "law", "dataset") and _year(s):
        out += f". {_year(s)}"
    pub = _d(s.get("date"))
    acc = _d(s.get("accessed"))
    if online:
        dates = (f"({pub.isoformat()})" if pub else "") + (f"[{acc.isoformat()}]" if acc else "")
        out += f". {dates}" if dates else ""
        out += f". {s['url']}" if s.get("url") else ""
        if s.get("doi"):
            out += f". DOI: {s['doi']}"
    return _end(out)


def _is_cjk(t: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in t)


def inline_citation(srcs: list[dict], style: str, numbers: list[int] | None = None) -> str:
    """In-text citation. numeric -> '[1, 3]'; author-date -> '(NASA, 2023; Doe, 1995)'."""
    if INLINE_FOR_STYLE.get(style) == "numeric" or numbers:
        return "[" + ",".join(str(n) for n in (numbers or [])) + "]"
    parts = []
    for s in srcs:
        au = _authors(s)
        who = surname(au[0]) if au else s.get("title", "")[:40]
        if len(au) == 2:
            who += (" & " if style == "apa" else " and ") + surname(au[1])
        elif len(au) > 2:
            who += " et al."
        y = _year(s) or "n.d."
        parts.append(f"{who}, {y}" if style == "apa" else f"{who} {y}")
    return "(" + "; ".join(parts) + ")"


def sort_key(src: dict, style: str):
    """Reference-list order: author-date styles sort alphabetically; gost/numeric keep citation order."""
    au = _authors(src)
    return ((surname(au[0]) if au else src.get("title", "")).lower(), _year(src) or "")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default="gost", choices=["gost", "apa", "chicago", "gbt7714"])
    ap.add_argument("--input", "-i", required=True)
    a = ap.parse_args(argv)
    with open(a.input, encoding="utf-8") as fh:
        data = json.load(fh)
    srcs = data.get("sources", data) if isinstance(data, dict) else data
    for i, s in enumerate(srcs, 1):
        pre = f"[{i}] " if a.style == "gbt7714" else f"{i}. " if a.style == "gost" else ""
        print(pre + format_reference(s, a.style))
    return 0


if __name__ == "__main__":
    sys.exit(main())
