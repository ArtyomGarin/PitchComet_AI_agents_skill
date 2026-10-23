#!/usr/bin/env python3
"""research_ledger.py — the evidence ledger: every number used in a pitch, with its provenance.

Each fact is either SOURCED (value from a page/report/dataset with a URL) or an ESTIMATE
(value derived by an explicit formula from other facts or from labelled rules of thumb).
Nothing else is allowed: a number without a URL or a formula fails validation.

Fact record::

  {"id": "us_food_estab_2025", "key": "establishments.food_service",   # key = what it measures
   "label": "Private food-service establishments (NAICS 722)",
   "value": 728580, "unit": "establishments", "currency": null, "year": 2025, "geo": "US",
   "type": "sourced" | "estimate", "confidence": "high" | "medium" | "low",
   "source_url": "https://...", "source_name": "U.S. Bureau of Labor Statistics", "retrieved": "2026-10-20",
   "method": "proxy | triangulation | benchmark_rule_of_thumb | value_theory | top_down | bottom_up",
   "formula": "establishments × adoption × price", "inputs": ["fact ids"], "range": {"low": .., "high": ..},
   "note": "..."}

Ledger file: {"meta": {"currency": "USD", "base_year": 2026, "fx": {"USD/RUB": {"value": 80, "year": 2026,
"source_url": "..."}}, "inflation": {"RUB": {"2025": 0.056}}}, "facts": [ ... ]}

What the module does
  * validate()  — required fields, URL for sourced facts, formula/method for estimates, ranges ordered;
  * dedup()     — identical key+year+geo with values within 0.5 % → one fact, sources merged;
  * normalize() — converts money to the ledger currency (meta.fx) and to a target year (meta.inflation);
  * resolve()   — one value per key+geo: sourced > estimate, then confidence, then source rank
                  (official statistics > regulators/legal databases > other), then most recent year;
                  conflicts (spread > 10 %) are reported with every candidate;
  * export()    — {"ledger": {key: {...}}, "sources": [...citations records...], "table": rows} for the pipeline.

CLI:
  python research_ledger.py validate --input ledger.json
  python research_ledger.py resolve  --input ledger.json [--out resolved.json]
  python research_ledger.py add --input ledger.json --json '{"key": "...", ...}' --out ledger.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import statistics
import sys
from urllib.parse import urlparse

try:
    from fmt_utils import dump_json, load_json
except ImportError:  # pragma: no cover
    from .fmt_utils import dump_json, load_json  # type: ignore

TYPES = ("sourced", "estimate")
CONF = {"high": 3, "medium": 2, "low": 1}
CONF_NUM = {"high": 0.85, "medium": 0.6, "low": 0.35}
METHODS = ("proxy", "triangulation", "benchmark_rule_of_thumb", "value_theory", "top_down", "bottom_up",
           "derived", "founder_input", "assumption")

# Domain patterns ranked as official statistics / central banks / regulators (rank 3),
# legal databases and international organisations (rank 2), everything else (rank 1).
OFFICIAL = [r"\.gov(\.[a-z]{2})?$", r"(^|\.)gov\.[a-z]{2}$", r"rosstat", r"(^|\.)cbr\.ru$", r"(^|\.)nalog\.(gov\.)?ru$",
            r"census", r"bls\.gov", r"bea\.gov", r"stats\.gov\.cn", r"pbc\.gov\.cn", r"gso\.gov\.vn", r"sbv\.gov\.vn",
            r"bps\.go\.id", r"bi\.go\.id", r"dosm\.gov\.my", r"bnm\.gov\.my", r"treasury\.gov", r"federalreserve\.gov",
            r"(^|\.)go\.id$", r"(^|\.)gov\.my$", r"(^|\.)gov\.vn$"]
SECONDARY = [r"consultant\.ru", r"garant\.ru", r"pravo\.gov\.ru", r"oecd\.org", r"worldbank\.org", r"imf\.org",
             r"un\.org", r"ilo\.org", r"\.edu$", r"sec\.gov", r"itu\.int", r"acort\.ru"]


def source_rank(url: str | None) -> int:
    if not url:
        return 0
    host = (urlparse(url).hostname or "").lower()
    if any(re.search(p, host) for p in OFFICIAL):
        return 3
    if any(re.search(p, host) for p in SECONDARY):
        return 2
    return 1


def _is_url(u) -> bool:
    try:
        p = urlparse(str(u))
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60] or "fact"


def new_ledger(currency: str = "USD", base_year: int | None = None) -> dict:
    return {"meta": {"currency": currency, "base_year": base_year or _dt.date.today().year, "fx": {}, "inflation": {}},
            "facts": []}


def validate_fact(f: dict) -> list[str]:
    e = []
    fid = f.get("id") or f.get("key") or "?"
    for k in ("key", "value", "type", "confidence"):
        if f.get(k) is None:
            e.append(f"{fid}: missing '{k}'")
    if f.get("type") not in TYPES:
        e.append(f"{fid}: type must be one of {TYPES}")
    if f.get("confidence") not in CONF:
        e.append(f"{fid}: confidence must be high|medium|low")
    if not isinstance(f.get("value"), (int, float)) or isinstance(f.get("value"), bool):
        e.append(f"{fid}: value must be a number")
    if f.get("type") == "sourced":
        if not _is_url(f.get("source_url")):
            e.append(f"{fid}: a sourced fact needs a valid source_url (http/https)")
        if f.get("year") is None:
            e.append(f"{fid}: a sourced fact needs the year the value refers to")
    if f.get("type") == "estimate":
        if not (f.get("formula") or f.get("method")):
            e.append(f"{fid}: an estimate needs a method and a formula")
        if f.get("method") and f["method"] not in METHODS:
            e.append(f"{fid}: unknown method '{f['method']}' (use one of {', '.join(METHODS)})")
        if f.get("method") == "benchmark_rule_of_thumb" and f.get("confidence") == "high":
            e.append(f"{fid}: a rule-of-thumb benchmark cannot have high confidence")
    r = f.get("range")
    if r:
        lo, hi = r.get("low"), r.get("high")
        if lo is not None and hi is not None and lo > hi:
            e.append(f"{fid}: range low > high")
    return e


def validate(ledger: dict) -> dict:
    errors, ids = [], set()
    facts = ledger.get("facts", [])
    for f in facts:
        errors += validate_fact(f)
        if f.get("id") in ids:
            errors.append(f"duplicate id '{f['id']}'")
        ids.add(f.get("id"))
    for f in facts:
        for i in f.get("inputs", []) or []:
            if i not in ids:
                errors.append(f"{f.get('id')}: input '{i}' is not in the ledger")
    n_s = sum(1 for f in facts if f.get("type") == "sourced")
    return {"ok": not errors, "errors": errors, "n_facts": len(facts), "n_sourced": n_s, "n_estimates": len(facts) - n_s}


def add_fact(ledger: dict, fact: dict, strict: bool = True) -> dict:
    f = dict(fact)
    f.setdefault("id", _slug(f"{f.get('key', 'fact')}_{f.get('geo', '')}_{f.get('year', '')}"))
    base, n = f["id"], 2
    while any(x.get("id") == f["id"] for x in ledger["facts"]):
        f["id"] = f"{base}_{n}"
        n += 1
    f.setdefault("retrieved", _dt.date.today().isoformat() if f.get("type") == "sourced" else None)
    errs = validate_fact(f)
    if errs and strict:
        raise ValueError("; ".join(errs))
    ledger["facts"].append(f)
    return f


def _close(a, b, tol=0.005):
    if a == b:
        return True
    d = max(abs(a), abs(b))
    return d > 0 and abs(a - b) / d <= tol


def dedup(ledger: dict) -> dict:
    """Merge facts with the same key/year/geo/unit whose values agree within 0.5 %."""
    out, merged = [], 0
    for f in ledger["facts"]:
        hit = next((g for g in out if g["key"] == f["key"] and g.get("year") == f.get("year")
                    and g.get("geo") == f.get("geo") and g.get("unit") == f.get("unit")
                    and g.get("type") == f.get("type") and _close(g["value"], f["value"])), None)
        if hit:
            alt = hit.setdefault("also_sources", [])
            if f.get("source_url") and f.get("source_url") != hit.get("source_url"):
                alt.append(f["source_url"])
            if CONF[f["confidence"]] > CONF[hit["confidence"]]:
                hit["confidence"] = f["confidence"]
            merged += 1
        else:
            out.append(dict(f))
    return {**ledger, "facts": out, "dedup_merged": merged}


def _fx_rate(meta: dict, frm: str, to: str):
    if frm == to:
        return 1.0
    fx = meta.get("fx", {})
    for k, v in fx.items():
        a, b = k.split("/")
        val = v["value"] if isinstance(v, dict) else v
        if (a, b) == (frm, to):
            return float(val)
        if (a, b) == (to, frm):
            return 1.0 / float(val)
    return None


def inflate_factor(meta: dict, currency: str, from_year: int, to_year: int) -> float:
    """Cumulative price index between two years from meta.inflation[currency][year] (fraction per year).
    Missing years count as 0 % and are reported by normalize()."""
    series = (meta.get("inflation") or {}).get(currency, {})
    k = 1.0
    if to_year >= from_year:
        for y in range(from_year + 1, to_year + 1):
            k *= 1 + float(series.get(str(y), series.get(y, 0.0)))
    else:
        for y in range(to_year + 1, from_year + 1):
            k /= 1 + float(series.get(str(y), series.get(y, 0.0)))
    return k


def normalize(ledger: dict, currency: str | None = None, year: int | None = None) -> dict:
    """Return a copy where money facts are in `currency` and in prices of `year` (if given)."""
    meta = ledger.get("meta", {})
    cur = currency or meta.get("currency")
    warnings, out = [], []
    for f in ledger["facts"]:
        g = dict(f)
        c = f.get("currency")
        if c and cur and c != cur:
            r = _fx_rate(meta, c, cur)
            if r is None:
                warnings.append(f"{f['id']}: no FX rate {c}/{cur} in meta.fx — left in {c}")
            else:
                g["value"] = f["value"] * r
                if f.get("range"):
                    g["range"] = {k: (v * r if v is not None else None) for k, v in f["range"].items()}
                g["currency"] = cur
                g["normalized"] = g.get("normalized", "") + f" fx {c}->{cur} ×{r:.4g}"
        if year and g.get("currency") and g.get("year") and int(g["year"]) != int(year) and f.get("deflate", True) \
                and f.get("unit_kind", "flow") != "count":
            series = (meta.get("inflation") or {}).get(g["currency"], {})
            yrs = range(min(int(g["year"]), int(year)) + 1, max(int(g["year"]), int(year)) + 1)
            missing = [y for y in yrs if str(y) not in series and y not in series]
            k = inflate_factor(meta, g["currency"], int(g["year"]), int(year))
            g["value"] = g["value"] * k
            if g.get("range"):
                g["range"] = {kk: (v * k if v is not None else None) for kk, v in g["range"].items()}
            g["normalized"] = g.get("normalized", "") + f" prices {g['year']}->{year} ×{k:.4g}"
            if missing:
                warnings.append(f"{f['id']}: no inflation for {g['currency']} in {missing} — assumed 0 %")
        out.append(g)
    return {**ledger, "facts": out, "normalize_warnings": warnings}


def _rank(f: dict):
    return (1 if f["type"] == "sourced" else 0, CONF[f["confidence"]], source_rank(f.get("source_url")),
            int(f.get("year") or 0))


def resolve(ledger: dict, conflict_tol: float = 0.10) -> dict:
    """Pick one value per key (and geo). Returns {"values": {key: fact}, "conflicts": [...]}."""
    groups: dict[str, list] = {}
    for f in ledger["facts"]:
        k = f["key"] if not f.get("geo") else f"{f['key']}@{f['geo']}"
        groups.setdefault(k, []).append(f)
    values, conflicts = {}, []
    for k, fs in groups.items():
        fs_sorted = sorted(fs, key=_rank, reverse=True)
        best = dict(fs_sorted[0])
        if len(fs) > 1:
            vals = [x["value"] for x in fs if x.get("year") == best.get("year") and x.get("unit") == best.get("unit")]
            if len(vals) > 1:
                spread = (max(vals) - min(vals)) / max(abs(statistics.median(vals)), 1e-12)
                if spread > conflict_tol:
                    conflicts.append({"key": k, "chosen": best["id"], "spread": spread,
                                      "candidates": [{"id": x["id"], "value": x["value"], "type": x["type"],
                                                      "confidence": x["confidence"], "source_url": x.get("source_url")}
                                                     for x in fs_sorted],
                                      "rule": "sourced > estimate, then confidence, then official source, then latest year"})
            best["alternatives"] = [x["id"] for x in fs_sorted[1:]]
        values[k] = best
    return {"values": values, "conflicts": conflicts}


def to_sources(ledger: dict, accessed: str | None = None) -> list[dict]:
    """Citation records (citations.py format) — one per distinct source URL of sourced facts."""
    seen, out = {}, []
    for f in ledger["facts"]:
        if f.get("type") != "sourced":
            continue
        for url in [f.get("source_url")] + list(f.get("also_sources", []) or []):
            if not url or url in seen:
                continue
            sid = "src_" + _slug(f.get("source_id") or (urlparse(url).hostname or "") + "_" + str(len(out) + 1))
            rec = {"id": sid, "type": "dataset" if f.get("dataset") else "web",
                   "org": f.get("source_name") or (urlparse(url).hostname or ""),
                   "title": f.get("source_title") or f.get("label") or f["key"],
                   "url": url, "accessed": f.get("retrieved") or accessed or _dt.date.today().isoformat()}
            if f.get("year"):
                rec["year"] = f["year"]
            seen[url] = sid
            out.append(rec)
    for f in ledger["facts"]:
        if f.get("source_url") in seen:
            f["source_id"] = seen[f["source_url"]]
    return out


def export(ledger: dict, currency: str | None = None, year: int | None = None) -> dict:
    """Everything the pipeline needs: validated, deduplicated, normalized, resolved facts + sources."""
    v = validate(ledger)
    led = normalize(dedup(ledger), currency, year)
    sources = to_sources(led)
    res = resolve(led)
    flat = {}
    for k, f in res["values"].items():
        flat[k.replace("@", "_").replace(".", "_")] = {
            "value": f["value"], "unit": f.get("unit"), "currency": f.get("currency"), "year": f.get("year"),
            "type": f["type"], "confidence": f["confidence"], "source_url": f.get("source_url"),
            "source_id": f.get("source_id"), "formula": f.get("formula"), "method": f.get("method"),
            "range": f.get("range"), "label": f.get("label"), "id": f["id"]}
    table = [{"id": f["id"], "key": f["key"], "label": f.get("label") or f["key"], "value": f["value"],
              "unit": f.get("unit"), "year": f.get("year"), "type": f["type"], "confidence": f["confidence"],
              "basis": f.get("source_url") or f.get("formula") or f.get("method")} for f in led["facts"]]
    n_e = sum(1 for f in led["facts"] if f["type"] == "estimate")
    return {"validation": v, "values": flat, "conflicts": res["conflicts"], "sources": sources, "table": table,
            "warnings": led.get("normalize_warnings", []),
            "stats": {"facts": len(led["facts"]), "sourced": len(led["facts"]) - n_e, "estimates": n_e,
                      "estimate_share": n_e / len(led["facts"]) if led["facts"] else None,
                      "merged_duplicates": led.get("dedup_merged", 0)}}


def get(ledger_or_export: dict, key: str, default=None):
    """Value lookup by key (export()['values'] or a raw ledger)."""
    vals = ledger_or_export.get("values")
    if vals is None:
        vals = {kk.replace("@", "_").replace(".", "_"): f for kk, f in resolve(ledger_or_export)["values"].items()}
    f = vals.get(key.replace("@", "_").replace(".", "_"))
    return f["value"] if f else default


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["validate", "resolve", "export", "add", "new"])
    ap.add_argument("--input", "-i")
    ap.add_argument("--json", "-j", help="fact JSON for 'add'")
    ap.add_argument("--out", "-o")
    ap.add_argument("--currency")
    ap.add_argument("--year", type=int)
    a = ap.parse_args(argv)
    if a.cmd == "new":
        print(dump_json(new_ledger(a.currency or "USD", a.year), a.out))
        return 0
    led = load_json(a.input) if a.input else json.load(sys.stdin)
    if a.cmd == "validate":
        r = validate(led)
        print(dump_json(r, a.out))
        return 0 if r["ok"] else 1
    if a.cmd == "add":
        add_fact(led, json.loads(a.json))
        print(dump_json(led, a.out or a.input))
        return 0
    if a.cmd == "resolve":
        print(dump_json(resolve(normalize(dedup(led), a.currency, a.year)), a.out))
        return 0
    print(dump_json(export(led, a.currency, a.year), a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
