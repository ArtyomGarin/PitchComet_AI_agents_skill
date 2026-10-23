#!/usr/bin/env python3
"""market_sizing.py — TAM/SAM/SOM top-down & bottom-up, triangulation, CAGR projections, scenarios.

Input JSON (all money in one currency; shares are fractions):
{
  "currency": "RUB" | "USD" | "CNY", "base_year": 2025, "horizon_year": 2030,
  "top_down": {
     "total_market": 250e9, "total_market_label": "Рынок ПО для аналитики, РФ", "source": "...",
     "filters": [ {"name": "доля NLP/LLM-решений", "share": 0.12, "level": "TAM", "rationale": "..."},
                  {"name": "доступные сегменты (B2G+B2B крупные)", "share": 0.40, "level": "SAM"},
                  {"name": "достижимая доля к горизонту", "share": 0.06, "level": "SOM"} ]
  },
  "bottom_up": {
     "segments": [ {"name": "Корпорации", "units": 900, "arpa": 3.6e6, "sam_share": 0.35, "som_share": 0.07,
                    "source": "..."} ]
  },
  "growth": {"cagr": {"bear": 0.08, "base": 0.15, "bull": 0.22}},   # TAM growth by scenario
  "som_ramp": "s_curve",            # or "linear"
  "som_share_multiplier": {"bear": 0.6, "base": 1.0, "bull": 1.4},
  "inflation": 0.0                   # optional: >0 => also report real (deflated) TAM
}
Output: base-year sizes (top-down, bottom-up, triangulated), per-scenario yearly series and
chart-ready blocks, warnings, and an assumptions log.

CLI: python market_sizing.py [--locale ru|en|zh|vi|id|ms] --input market.json [--out result.json]
"""
from __future__ import annotations

import math
import sys

try:
    from fmt_utils import cli_io, dump_json
except ImportError:  # pragma: no cover
    from .fmt_utils import cli_io, dump_json  # type: ignore


def top_down(total_market: float, filters: list[dict]) -> dict:
    """Chain multiplicative filters. Each filter has level TAM|SAM|SOM marking the size after it."""
    value = total_market
    levels, log = {}, []
    for f in filters:
        value *= f["share"]
        log.append({"step": f["name"], "share": f["share"], "result": value, "rationale": f.get("rationale", "")})
        if f.get("level"):
            levels[f["level"].upper()] = value
    return {"TAM": levels.get("TAM", total_market), "SAM": levels.get("SAM"), "SOM": levels.get("SOM"),
            "steps": log, "total_market": total_market}


def bottom_up(segments: list[dict]) -> dict:
    """TAM = Σ units × ARPA; SAM = Σ TAM_seg × sam_share; SOM = Σ SAM_seg × som_share."""
    rows, tam, sam, som = [], 0.0, 0.0, 0.0
    for s in segments:
        t = s["units"] * s["arpa"]
        sa = t * s.get("sam_share", 1.0)
        so = sa * s.get("som_share", 0.0)
        tam, sam, som = tam + t, sam + sa, som + so
        rows.append({"segment": s["name"], "units": s["units"], "arpa": s["arpa"], "TAM": t, "SAM": sa, "SOM": so,
                     "customers_at_som": s["units"] * s.get("sam_share", 1.0) * s.get("som_share", 0.0),
                     "source": s.get("source", "")})
    return {"TAM": tam, "SAM": sam, "SOM": som, "segments": rows}


def triangulate(td: dict | None, bu: dict | None) -> dict:
    out, warnings = {}, []
    for lvl in ("TAM", "SAM", "SOM"):
        a = td.get(lvl) if td else None
        b = bu.get(lvl) if bu else None
        if a and b:
            ratio = max(a, b) / min(a, b)
            out[lvl] = math.sqrt(a * b)  # geometric mean of two independent estimates
            out[f"{lvl}_ratio"] = ratio
            if ratio > 2:
                warnings.append(f"{lvl}: top-down and bottom-up differ {ratio:.1f}x (>2x) — revisit assumptions; "
                                "present the bottom-up figure as primary")
        else:
            out[lvl] = a or b
    return {"values": out, "warnings": warnings}


def _ramp(t: int, n: int, kind: str) -> float:
    if n <= 0:
        return 1.0
    x = t / n
    if kind == "linear":
        return x
    # logistic normalized to 0 at t=0 and 1 at t=n
    k = 8.0
    f = lambda z: 1 / (1 + math.exp(-k * (z - 0.6)))
    return (f(x) - f(0)) / (f(1) - f(0))


def project(base: dict, cagr_by_scn: dict, base_year: int, horizon_year: int, ramp: str = "s_curve",
            som_mult: dict | None = None, inflation: float = 0.0) -> dict:
    years = list(range(base_year, horizon_year + 1))
    n = len(years) - 1
    sam_ratio = (base["SAM"] / base["TAM"]) if base.get("SAM") and base.get("TAM") else None
    som_share_of_sam = (base["SOM"] / base["SAM"]) if base.get("SOM") and base.get("SAM") else None
    scen = {}
    for name, g in cagr_by_scn.items():
        tam = [base["TAM"] * (1 + g) ** t for t in range(n + 1)]
        sam = [x * sam_ratio for x in tam] if sam_ratio else None
        m = (som_mult or {}).get(name, 1.0)
        som = [sam[t] * som_share_of_sam * m * _ramp(t, n, ramp) for t in range(n + 1)] if (sam and som_share_of_sam) else None
        row = {"cagr": g, "years": years, "TAM": tam, "SAM": sam, "SOM": som,
               "TAM_horizon": tam[-1], "SAM_horizon": sam[-1] if sam else None, "SOM_horizon": som[-1] if som else None}
        if inflation:
            row["TAM_real"] = [v / (1 + inflation) ** t for t, v in enumerate(tam)]
            row["real_cagr"] = (1 + g) / (1 + inflation) - 1
        scen[name] = row
    return {"years": years, "scenarios": scen}


def size_market(spec: dict) -> dict:
    td = top_down(spec["top_down"]["total_market"], spec["top_down"].get("filters", [])) if spec.get("top_down") else None
    bu = bottom_up(spec["bottom_up"]["segments"]) if spec.get("bottom_up") else None
    tri = triangulate(td, bu)
    primary = spec.get("primary", "bottom_up" if bu else "top_down")
    base = {"bottom_up": bu, "top_down": td, "triangulated": tri["values"]}[primary] or tri["values"]
    base = {k: base.get(k) for k in ("TAM", "SAM", "SOM")}
    growth = spec.get("growth", {}).get("cagr", {"base": 0.0})
    proj = project(base, growth, spec.get("base_year", 2025), spec.get("horizon_year", 2030),
                   spec.get("som_ramp", "s_curve"), spec.get("som_share_multiplier"), spec.get("inflation", 0.0))
    warnings = list(tri["warnings"])
    if base.get("TAM") and base.get("SOM") and base["SOM"] / base["TAM"] > 0.1:
        warnings.append("SOM > 10% of TAM — unusually aggressive for a new entrant; justify with pipeline evidence")
    for name, g in growth.items():
        if g > 0.4:
            warnings.append(f"scenario '{name}': CAGR {g:.0%} > 40% — label as speculative and cite source")
    sc = proj["scenarios"]
    chart_tam_sam_som = {"type": "bar", "categories": ["TAM", "SAM", "SOM"],
                         "series": [{"name": str(spec.get("base_year", "")), "values": [base["TAM"], base["SAM"], base["SOM"]]}]}
    chart_tam_scen = {"type": "line", "categories": [str(y) for y in proj["years"]],
                      "series": [{"name": k, "values": v["TAM"]} for k, v in sc.items()]}
    chart_som = {"type": "column", "categories": [str(y) for y in proj["years"]],
                 "series": [{"name": k, "values": v["SOM"]} for k, v in sc.items() if v.get("SOM")]}
    return {"currency": spec.get("currency") or _default_currency(spec), "primary_method": primary, "base_year": spec.get("base_year"),
            "horizon_year": spec.get("horizon_year"), "base": base, "top_down": td, "bottom_up": bu,
            "triangulation": tri["values"], "projection": proj, "warnings": warnings,
            "charts": {"tam_sam_som": chart_tam_sam_som, "tam_scenarios": chart_tam_scen, "som_scenarios": chart_som},
            "assumptions": {"growth_cagr": growth, "som_ramp": spec.get("som_ramp", "s_curve"),
                            "som_share_multiplier": spec.get("som_share_multiplier"),
                            "sources": [spec.get("top_down", {}).get("source")] +
                                       [s.get("source") for s in spec.get("bottom_up", {}).get("segments", [])]}}


def _default_currency(spec):
    from locales import get_locale
    return get_locale(spec.get("locale") or "ru")["currency"]


def main(argv=None):
    payload, out, _ = cli_io(argv)
    if not payload:
        print(__doc__)
        return 1
    res = size_market(payload)
    loc = payload.get("locale")
    if loc:   # human-readable figures in the requested locale (RU 3,0 млрд ₽ · EN $3.0B · ZH 30.1亿元)
        from fmt_utils import fmt_money, fmt_pct
        cur = res["currency"]
        res["display"] = {"locale": loc, **{k: fmt_money(v, cur, loc) for k, v in res["base"].items()
                                            if isinstance(v, (int, float))},
                          **{f"cagr_{k}": fmt_pct(v["cagr"], 1, loc) for k, v in res["projection"]["scenarios"].items()}}
    print(dump_json(res, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
