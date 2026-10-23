#!/usr/bin/env python3
"""product_profiler.py — build a product profile from a free-text description, README or web page text.

The profile is the starting point of the autonomous mode: the agent never asks the founder for
fields it can infer. Every field gets a status:
  from_text  — stated in the text (quoted evidence kept);
  inferred   — derived by a keyword heuristic (config/market_taxonomy.json), with the matched words;
  default    — a neutral default that the pipeline can work with (and that is shown as an assumption);
  to_confirm — cannot be inferred; it goes to the short 'to confirm with the founder' list and never
               blocks the deck.

Input (JSON): {"text": "...", "name": "optional", "market": "optional ru|en|zh|vn|id|my",
               "overrides": {"field": value}}   (or --text-file README.md / page.txt)
Output: {"profile": {...}, "checklist": [{field, status, value, evidence}], "to_confirm": [...]}

CLI:
  python product_profiler.py --text-file README.md [--name X] [--market en] [--out profile.json]
  python product_profiler.py --json '{"text": "..."}'
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

try:
    from fmt_utils import dump_json, load_json
except ImportError:  # pragma: no cover
    from .fmt_utils import dump_json, load_json  # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
TAX_PATH = os.path.join(HERE, "..", "config", "market_taxonomy.json")

FIELDS = ["name", "one_liner", "category", "buyer_segment", "buyer_industries", "buyer_roles", "user_roles",
          "pricing_model", "price_points", "deployment", "geography", "ai_heavy", "stage", "traction",
          "value_drivers", "unit"]

GEO_RULES = [
    ("ru", [r"[₽]", r"\bруб", r"\bRUB\b", r"росси", r"\bРФ\b", r"russia"]),
    ("en", [r"\$\s?\d", r"\bUSD\b", r"united states", r"\bU\.?S\.?A?\b", r"america"]),
    ("zh", [r"[¥￥]", r"\bCNY\b", r"\bRMB\b", r"元", r"中国", r"\bchina\b"]),
    ("vn", [r"₫", r"\bVND\b", r"việt nam", r"vietnam", r"\bđồng\b"]),
    ("id", [r"\bRp\.?\s?\d", r"\bIDR\b", r"indonesia"]),
    ("my", [r"\bRM\s?\d", r"\bMYR\b", r"malaysia"]),
]
CURRENCY_OF = {"ru": "RUB", "en": "USD", "zh": "CNY", "vn": "VND", "id": "IDR", "my": "MYR"}
LOCALE_OF_MARKET = {"ru": "ru", "en": "en", "zh": "zh", "vn": "vi", "id": "id", "my": "ms"}
STAGE_RULES = [
    ("growth", [r"\barr\b", r"\bmrr\b", r"paying customers", r"платящ", r"выручк", r"revenue of", r"\d+\s*(customers|клиент)"]),
    ("pilot", [r"pilot", r"пилот", r"beta", r"бета", r"\bloi\b", r"试点", r"thí điểm", r"uji coba", r"perintis"]),
    ("prototype", [r"prototype", r"mvp", r"прототип", r"demo", r"демо", r"原型", r"nguyên mẫu", r"prototipe"]),
    ("idea", [r"\bidea\b", r"concept", r"идея", r"концепц", r"想法", r"ý tưởng", r"ide\b"]),
]
PRICE_RE = re.compile(
    r"(?P<cur>\$|₽|¥|￥|£|₫|RM|Rp|USD|RUB|CNY|VND|IDR|MYR)?\s?(?P<num>\d[\d\s.,]*\d|\d)\s?(?P<cur2>\$|₽|руб\.?|USD|RUB|元|₫|đ)?"
    r"\s?(?P<per>/\s?(?:mo|month|мес|月|tháng|bulan)|per month|в месяц|a month|/\s?(?:user|seat|location|точк|пользоват)"
    r"[a-zа-я]*(?:\s?/\s?(?:mo|month|мес))?|per (?:user|seat|location|store|employee)[a-z ]*(?:per month|/month)?"
    r"|за (?:точку|пользователя|сотрудника)[а-я ]*(?:в месяц)?)", re.I)


def _load_tax(path=None):
    return load_json(path or TAX_PATH)


def _hits(text: str, words: list[str]) -> list[str]:
    t = text.lower()
    return [w for w in words if w.lower() in t]


def _name(text: str) -> str | None:
    m = re.search(r"^\s*#\s+([^\n#]{2,60})$", text, re.M)
    if m:
        return re.split(r"[—:\-–|]", m.group(1))[0].strip()
    m = re.search(r"\b([A-Z][A-Za-z0-9]{2,30})\b\s+(?:is|—|-|–|это)\s", text)
    return m.group(1) if m else None


def _one_liner(text: str) -> str:
    body = re.sub(r"^\s*#.*$", "", text, flags=re.M).strip()
    sent = re.split(r"(?<=[.!?。])\s+", body)
    return (sent[0] if sent else body)[:240].strip()


def _price_points(text: str) -> list[dict]:
    out = []
    for m in PRICE_RE.finditer(text):
        cur = m.group("cur") or m.group("cur2")
        if not cur:
            continue
        raw = m.group("num").replace(" ", "").replace("\u00a0", "")
        if raw.count(",") and not raw.count("."):
            raw = raw.replace(",", ".") if len(raw.split(",")[-1]) <= 2 else raw.replace(",", "")
        else:
            raw = raw.replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        out.append({"value": val, "currency_symbol": cur, "per": m.group("per").strip(), "evidence": m.group(0).strip()})
    return out


def _numbers(text: str, patterns: list[str]) -> list[dict]:
    out = []
    for p in patterns:
        for m in re.finditer(p, text, re.I):
            out.append({"evidence": m.group(0), "value": float(re.sub(r"[^\d.]", "", m.group(1)) or 0)})
    return out


def profile(text: str, name: str | None = None, market: str | None = None, overrides: dict | None = None,
            taxonomy: dict | None = None) -> dict:
    tax = taxonomy or _load_tax()
    t = text or ""
    tl = t.lower()
    chk, P = [], {}

    def put(field, value, status, evidence=None, confidence="medium"):
        P[field] = value
        chk.append({"field": field, "status": status, "value": value, "evidence": evidence, "confidence": confidence})

    nm = name or _name(t)
    put("name", nm or "Product", "from_text" if nm else "to_confirm", None, "high" if nm else "low")
    put("one_liner", _one_liner(t), "from_text", None, "medium")

    # category
    scores = {}
    for cid, c in tax["categories"].items():
        h = _hits(t, c["keywords"])
        if h:
            scores[cid] = (len(h), h)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1][0])
    if ranked:
        cid, (n, h) = ranked[0]
        put("category", cid, "inferred", h, "high" if n >= 3 else "medium")
        P["category_candidates"] = [{"id": k, "hits": v[0]} for k, v in ranked[:4]]
    else:
        cid = "ai_assistant" if re.search(r"\bai\b|\bии\b|llm|人工智能|\bai\b", tl) else "data_analytics"
        put("category", cid, "default", None, "low")
    cat = tax["categories"][P["category"]]

    # buyer segment
    seg_hits = {s: _hits(t, w) for s, w in tax["buyer_keywords"].items()}
    seg_hits = {k: v for k, v in seg_hits.items() if v}
    if seg_hits:
        order = sorted(seg_hits, key=lambda s: -len(seg_hits[s]))
        put("buyer_segment", order, "inferred", sum(seg_hits.values(), []), "medium")
    else:
        put("buyer_segment", ["smb", "mid_market"], "default", None, "low")
    put("buyer_industries", cat["buyer_industries"], "inferred", f"category {P['category']}", "medium")
    put("buyer_roles", cat["buyer_roles"], "inferred", f"category {P['category']}", "medium")
    put("user_roles", cat["user_roles"], "inferred", f"category {P['category']}", "medium")
    put("value_drivers", cat["value_drivers"], "inferred", f"category {P['category']}", "medium")
    put("unit", cat["unit"], "inferred", cat["price_metric"], "medium")

    # pricing
    pm = {k: _hits(t, w) for k, w in tax["pricing_keywords"].items()}
    pm = {k: v for k, v in pm.items() if v}
    pp = _price_points(t)
    if pm:
        put("pricing_model", sorted(pm, key=lambda k: -len(pm[k])), "inferred", sum(pm.values(), []), "medium")
    else:
        put("pricing_model", ["subscription"], "default", "B2B software default", "low")
    if pp:
        put("price_points", pp, "from_text", [p["evidence"] for p in pp], "high")
    else:
        put("price_points", [], "to_confirm", "no price in text — estimated from competitor pricing and value-based price",
            "low")

    dep = {k: _hits(t, w) for k, w in tax["deployment_keywords"].items()}
    dep = {k: v for k, v in dep.items() if v}
    put("deployment", sorted(dep, key=lambda k: -len(dep[k])) if dep else ["cloud_saas"],
        "inferred" if dep else "default", sum(dep.values(), []) if dep else None, "medium" if dep else "low")

    # geography
    geo = []
    for mk, pats in GEO_RULES:
        if any(re.search(p, t, re.I) for p in pats):
            geo.append(mk)
    if market:
        geo = [market] + [g for g in geo if g != market]
        put("geography", geo, "from_text", "given", "high")
    elif geo:
        put("geography", geo, "inferred", "currency / country words", "medium")
    else:
        cyr = len(re.findall(r"[а-яё]", tl)) > len(re.findall(r"[a-z]", tl)) * 0.3
        cjk = len(re.findall(r"[\u4e00-\u9fff]", t)) > 10
        g = "ru" if cyr else ("zh" if cjk else "en")
        put("geography", [g], "default", "language of the text", "low")
    P["currency"] = CURRENCY_OF.get(P["geography"][0], "USD")
    P["locale"] = LOCALE_OF_MARKET.get(P["geography"][0], "en")

    ai_w = _hits(t, ["ai", " ии ", "ии-", "llm", "machine learning", "нейросет", "generative", "ml ", "人工智能", "模型",
                     "trí tuệ nhân tạo", "kecerdasan buatan", "kecerdasan buatan"])
    ai_core = bool(re.search(r"\b(ai|llm|gpt|ml)\b|нейросет|ии-|\bии\b|人工智能|大模型", t, re.I))
    put("ai_heavy", ai_core, "inferred", ai_w or None, "medium")

    stage = None
    for st, pats in STAGE_RULES:
        if any(re.search(p, t, re.I) for p in pats):
            stage = st
            break
    put("stage", stage or "prototype", "inferred" if stage else "default", None, "medium" if stage else "low")

    trac = _numbers(t, [r"(\d[\d,.\s]*)\s*(?:paying\s+)?(?:customers|clients|клиент\w*|заказчик\w*|客户)",
                        r"(\d[\d,.\s]*)\s*(?:pilots?|пилот\w*)", r"mrr\s*(?:of\s*)?\$?\s?(\d[\d,.]*)",
                        r"(\d[\d,.\s]*)\s*(?:locations|stores|shops|caf[eé]s|restaurants|точ\w*|магазин\w*|кафе|ресторан\w*)"])
    put("traction", trac, "from_text" if trac else "to_confirm",
        None if trac else "no traction in text — model starts from zero customers", "medium" if trac else "low")

    for k, v in (overrides or {}).items():
        P[k] = v
        chk.append({"field": k, "status": "from_text", "value": v, "evidence": "override", "confidence": "high"})
    seen, checklist = set(), []
    for c in reversed(chk):
        if c["field"] not in seen:
            seen.add(c["field"])
            checklist.append(c)
    checklist.reverse()
    to_confirm = [c["field"] for c in checklist if c["status"] == "to_confirm"]
    for f in FIELDS:
        P.setdefault(f, None)
    return {"profile": P, "checklist": checklist, "to_confirm": to_confirm,
            "coverage": sum(1 for c in checklist if c["status"] in ("from_text", "inferred")) / max(len(checklist), 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text-file")
    ap.add_argument("--json", "-j")
    ap.add_argument("--input", "-i")
    ap.add_argument("--name")
    ap.add_argument("--market")
    ap.add_argument("--out", "-o")
    a = ap.parse_args(argv)
    payload = json.loads(a.json) if a.json else (load_json(a.input) if a.input else {})
    if a.text_file:
        with open(a.text_file, encoding="utf-8") as fh:
            payload["text"] = fh.read()
    res = profile(payload.get("text", ""), a.name or payload.get("name"), a.market or payload.get("market"),
                  payload.get("overrides"))
    print(dump_json(res, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
