"""Shared helpers: locale-aware number formatting (ru / en / zh / vi / id / ms), JSON I/O, placeholder resolution.

Placeholders inside any string of a spec:
    {{path.to.value}}            -> formatted with default formatter
    {{path.to.value|pct1}}       -> formatted with a named formatter
A dict {"$ref": "path.to.value"} is replaced by the raw object (lists for charts).

Formatters: int, num0, num1, num2, pct0, pct1, pp1 (percentage points), x1 (multiple, e.g. 3,2x / 3.2x / 3.2倍),
money (auto scale), money_mn, money_bn (zh: 万 / 亿), money_wan, money_yi, raw. Locale and currency come from ctx
({"locale": "ru"|"en"|"zh", "currency": "RUB"|"USD"|"CNY"}; "language" is accepted as an alias).
"""
from __future__ import annotations

import json
import math
import re
import sys
from typing import Any

NBSP = "\u00a0"

try:
    from locales import LOCALES, get_locale, norm_locale
except ImportError:  # pragma: no cover
    from .locales import LOCALES, get_locale, norm_locale  # type: ignore

SCALE_WORDS = {k: {sc: w for sc, (_, w) in v["scales"].items()} for k, v in LOCALES.items()}
CURRENCY_SIGNS = {"RUB": "₽", "USD": "$", "CNY": "¥", "GBP": "£", "VND": "₫", "IDR": "Rp", "MYR": "RM",
                  "SGD": "S$"}
ZH_CURRENCY_WORD = {"CNY": "元", "USD": "美元", "RUB": "卢布"}


def load_json(path_or_obj: Any) -> Any:
    if isinstance(path_or_obj, (dict, list)):
        return path_or_obj
    with open(path_or_obj, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(obj: Any, path: str | None = None) -> str:
    txt = json.dumps(obj, ensure_ascii=False, indent=2, default=_json_default)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(txt + "\n")
    return txt


def _json_default(o: Any):
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return str(o)


def fmt_number(x: float | int | None, decimals: int = 1, lang: str = "ru") -> str:
    """12345.6 -> '12 345,6' (ru, NBSP) · '12,345.6' (en, zh)."""
    loc = get_locale(lang)
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return loc["na"]
    s = f"{x:,.{decimals}f}"
    if loc["decimal"] != "." or loc["thousands"] != ",":
        s = s.replace(",", "\0").replace(".", loc["decimal"]).replace("\0", loc["thousands"])
    return s


def fmt_pct(x: float | None, decimals: int = 1, lang: str = "ru", ratio: bool = True) -> str:
    """0.153 -> '15,3%' (ru) / '15.3%' (en, zh). Input is a fraction when ratio=True."""
    if x is None:
        return fmt_number(None, lang=lang)
    v = x * 100 if ratio else x
    return f"{fmt_number(v, decimals, lang)}%"


def fmt_pp(x: float | None, decimals: int = 1, lang: str = "ru") -> str:
    """Change of a share in percentage points: 0.13 -> '13 п.п.' / '13 pp' / '13个百分点'."""
    if x is None:
        return fmt_number(None, lang=lang)
    loc = get_locale(lang)
    sep = "" if norm_locale(lang) == "zh" else NBSP
    return f"{fmt_number(x * 100, decimals, lang)}{sep}{loc['pp']}"


def fmt_multiple(x: float | None, decimals: int = 1, lang: str = "ru") -> str:
    """1.58 -> '1,6x' (ru) / '1.6x' (en) / '1.6倍' (zh)."""
    if x is None:
        return fmt_number(None, lang=lang)
    return f"{fmt_number(x, decimals, lang)}{get_locale(lang)['multiple']}"


def fmt_money(x: float | None, currency: str | None = None, lang: str = "ru", scale: str = "auto",
              decimals: int = 1) -> str:
    """Money with a locale scale word.

    ru: 3,0 млрд ₽ · en: $3.0B (RUB 3.0 bn for roubles) · zh: 3.0亿元 / 3600万元 (万 = 1e4, 亿 = 1e8) ·
    vi: 3,0 tỷ ₫ · id: Rp3,0 miliar · ms: RM3.0 bilion.
    Scale codes are semantic (k < mn < bn); each locale maps them onto its customary units
    (zh: mn -> 万, bn -> 亿; vi: mn -> tỷ, bn -> nghìn tỷ; id: mn -> miliar, bn -> triliun).
    """
    loc = get_locale(lang)
    code = norm_locale(lang)
    currency = currency or loc["currency"]
    if x is None:
        return fmt_number(None, lang=lang)
    a = abs(x)
    scales = loc["scales"]
    if scale in ("auto", None):
        if code == "zh":
            scale = "tn" if a >= 1e12 else "bn" if a >= 1e8 else "mn" if a >= 1e4 else ""
        else:   # largest of k/mn/bn/tn whose divisor fits (k only from 10 units of its divisor)
            scale = ""
            for sc in ("tn", "bn", "mn", "k"):
                dv = scales.get(sc, (0,))[0]
                if dv and a >= dv * (10 if sc == "k" else 1):
                    scale = sc
                    break
    div, word = scales.get(scale, (1, "")) if scale else (1, "")
    num = fmt_number(a / div, decimals if scale else 0, lang)
    neg = x < 0 and any(ch in "123456789" for ch in num)
    body = _money_body(num, word, scale, currency, code)
    return ("-" + body) if neg else body


def _money_body(num: str, word: str, scale: str, currency: str, code: str) -> str:
    """Place the currency sign/word around an unsigned number (the sign of the amount is added by the caller)."""
    sign = CURRENCY_SIGNS.get(currency, currency)
    if code == "ru":
        return f"{num}{NBSP}{word}{NBSP}{sign}".replace(NBSP + NBSP, NBSP)
    if code == "zh":
        return f"{num}{word}{ZH_CURRENCY_WORD.get(currency, currency)}"
    if code == "vi":
        return f"{num}{NBSP}{word}{NBSP}{sign}".replace(NBSP + NBSP, NBSP)
    if code in ("id", "ms"):
        return f"{sign}{num}{(NBSP + word) if word else ''}"
    if currency == "RUB":  # English convention for roubles: "RUB 3.0 bn"
        w = {"k": "k", "mn": "m", "bn": "bn", "tn": "tn"}.get(scale, "")
        return f"RUB{NBSP}{num}{(NBSP + w) if w else ''}"
    if sign in ("$", "¥", "£"):
        return f"{sign}{num}{word}"
    return f"{num}{word} {sign}"


def _ctx_locale(ctx: dict) -> str:
    return norm_locale(ctx.get("locale") or ctx.get("language") or "ru")


def format_value(v: Any, fmt: str | None, ctx: dict | None = None) -> str:
    """Named formatters: int, numN, pctN, ppN, xN, money[_k|_mn|_bn|_tn|_wan|_yi][N], raw, auto."""
    ctx = ctx or {}
    lang = _ctx_locale(ctx)
    cur = ctx.get("currency") or get_locale(lang)["currency"]
    if isinstance(v, str) or v is None or isinstance(v, bool):
        return "" if v is None else str(v)
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    f = fmt or "auto"
    if f == "raw":
        return str(v)
    if f == "int":
        return fmt_number(round(v), 0, lang)
    m = re.fullmatch(r"num(\d)", f)
    if m:
        return fmt_number(v, int(m.group(1)), lang)
    m = re.fullmatch(r"pct(\d)", f)
    if m:
        return fmt_pct(v, int(m.group(1)), lang)
    m = re.fullmatch(r"pp(\d)", f)
    if m:
        return fmt_pp(v, int(m.group(1)), lang)
    m = re.fullmatch(r"x(\d)", f)
    if m:
        return fmt_multiple(v, int(m.group(1)), lang)
    m = re.fullmatch(r"money(?:_(k|mn|bn|tn|wan|yi|trieu|ty|juta|miliar))?(\d)?", f)
    if m:
        return fmt_money(v, cur, lang, m.group(1) or "auto", int(m.group(2)) if m.group(2) else 1)
    # auto
    if float(v).is_integer() and 1800 <= v <= 2200:
        return str(int(v))  # calendar years: no thousands separator
    if isinstance(v, int) or float(v).is_integer():
        return fmt_number(v, 0, lang)
    return fmt_number(v, 1, lang)


def get_path(data: Any, path: str) -> Any:
    cur = data
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"placeholder path not found: {path} (missing '{part}')")
            cur = cur[part]
        else:
            raise KeyError(f"placeholder path not found: {path}")
    return cur


_PH = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*(?:\|\s*([A-Za-z0-9_]+)\s*)?\}\}")


def resolve_placeholders(obj: Any, facts: dict, ctx: dict | None = None, strict: bool = True) -> Any:
    """Recursively replace {{path|fmt}} in strings and {"$ref": path} dicts using facts."""
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$ref"}:
            return get_path(facts, obj["$ref"])
        return {k: resolve_placeholders(v, facts, ctx, strict) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_placeholders(v, facts, ctx, strict) for v in obj]
    if isinstance(obj, str) and "{{" in obj:
        def rep(m):
            try:
                return format_value(get_path(facts, m.group(1)), m.group(2), ctx)
            except (KeyError, IndexError, ValueError):
                if strict:
                    raise
                return m.group(0)
        return _PH.sub(rep, obj)
    return obj


def cli_io(argv: list[str] | None = None):
    """Parse '--input file.json' | '--json "{...}"' | stdin, plus '--locale ru|en|zh|vi|id|ms' (stored in payload["locale"]).
    Returns (payload, out_path, rest)."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--input", "-i")
    ap.add_argument("--json", "-j")
    ap.add_argument("--out", "-o")
    ap.add_argument("--locale", "-l", choices=sorted(LOCALES) + ["ru-RU", "en-US", "zh-CN"])
    a, rest = ap.parse_known_args(argv)
    if a.json:
        payload = json.loads(a.json)
    elif a.input:
        payload = load_json(a.input)
    elif not sys.stdin.isatty():
        txt = sys.stdin.read().strip()
        payload = json.loads(txt) if txt else {}
    else:
        payload = {}
    if a.locale and isinstance(payload, dict):
        payload["locale"] = norm_locale(a.locale)
    return payload, a.out, rest
