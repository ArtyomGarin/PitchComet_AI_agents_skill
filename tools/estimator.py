#!/usr/bin/env python3
"""estimator.py — explicit, reproducible estimates when a figure cannot be found.

Every result is a low / base / high triple plus the formula, the inputs (with their ledger ids)
and a confidence. Nothing is guessed silently: inputs come from the research ledger (sourced) or
from config/benchmarks.json (RULES OF THUMB, always labelled 'benchmark_rule_of_thumb', confidence
low). Ranges are computed over every corner of the input ranges, so division and subtraction are
handled correctly.

Methods
  * expr(formula, inputs)            — generic: "units * price * adoption" over ranged inputs
  * top_down(total, filters)         — total market × share filters (TAM → SAM → SOM)
  * bottom_up(segments)              — Σ units × price; SAM = × serviceable share; SOM = × obtainable share
  * value_theory(units, value, capture) — value created per customer × capture share (price ceiling)
  * triangulate(estimates)           — combines methods, reports the spread (ratio max/min)
  * cagr_from_drivers(...)           — category growth = (1 + industry nominal growth) × penetration growth
  * value_price(...)                 — price from hours saved × hourly cost × capture share
  * unit_economics(segment, arpa)    — CAC, LTV, LTV/CAC, payback from benchmark ranges (or overrides)
  * comparables(revenue, multiple)   — EV range = revenue × listed-peer multiple × (1 − private discount)
  * benchmark(segment, metric)       — a labelled rule-of-thumb range

CLI:
  python estimator.py expr --json '{"formula": "a*b", "inputs": {"a": {"low": 1, "base": 2, "high": 3}, "b": 10}}'
  python estimator.py unit_economics --json '{"segment": "smb", "arpa_month": 60}'
  python estimator.py benchmarks                    # print the library
"""
from __future__ import annotations

import ast
import itertools
import math
import operator
import os
import sys

try:
    from fmt_utils import cli_io, dump_json, load_json
except ImportError:  # pragma: no cover
    from .fmt_utils import cli_io, dump_json, load_json  # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_PATH = os.path.join(HERE, "..", "config", "benchmarks.json")
CONF_ORDER = ["low", "medium", "high"]
_BENCH = None


def load_benchmarks(path: str | None = None) -> dict:
    global _BENCH
    if path:
        return load_json(path)
    if _BENCH is None:
        _BENCH = load_json(BENCH_PATH)
    return _BENCH


def rng(x) -> dict:
    """Normalize an input to {low, base, high, id?, confidence?}."""
    if isinstance(x, dict):
        base = x.get("base", x.get("value"))
        lo = x.get("low", (x.get("range") or {}).get("low", base))
        hi = x.get("high", (x.get("range") or {}).get("high", base))
        out = {"low": float(lo), "base": float(base), "high": float(hi)}
        for k in ("id", "confidence", "type", "method", "source_url"):
            if x.get(k) is not None:
                out[k] = x[k]
        return out
    v = float(x)
    return {"low": v, "base": v, "high": v}


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {"min": min, "max": max, "sqrt": math.sqrt, "log": math.log, "exp": math.exp}


def _eval(node, env):
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise KeyError(f"unknown input '{node.id}'")
        return env[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left, env), _eval(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand, env))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a, env) for a in node.args])
    raise ValueError(f"unsupported expression element: {ast.dump(node)[:60]}")


def _min_conf(confs):
    cs = [c for c in confs if c in CONF_ORDER]
    return min(cs, key=CONF_ORDER.index) if cs else "low"


def expr(formula: str, inputs: dict, key: str | None = None, method: str = "derived", label: str | None = None,
         unit: str | None = None, confidence: str | None = None, year=None, geo=None, currency=None) -> dict:
    """Evaluate `formula` at base and at every corner of the input ranges → low/base/high + ledger fact."""
    tree = ast.parse(formula, mode="eval")
    R = {k: rng(v) for k, v in inputs.items()}
    base = _eval(tree, {k: v["base"] for k, v in R.items()})
    ranged = [k for k, v in R.items() if v["low"] != v["high"]]
    vals = [base]
    if len(ranged) <= 10:
        for combo in itertools.product(*[("low", "high")] * len(ranged)):
            env = {k: v["base"] for k, v in R.items()}
            env.update({k: R[k][c] for k, c in zip(ranged, combo)})
            try:
                vals.append(_eval(tree, env))
            except ZeroDivisionError:
                pass
    else:  # pragma: no cover - too many ranged inputs: all-low / all-high only
        vals += [_eval(tree, {k: v["low"] for k, v in R.items()}), _eval(tree, {k: v["high"] for k, v in R.items()})]
    conf_in = [v.get("confidence", "medium" if v.get("type") == "sourced" else "low") for v in R.values()
               if "confidence" in v or "type" in v]
    conf = confidence or _min_conf(conf_in or ["low"])
    if method == "benchmark_rule_of_thumb":
        conf = "low"
    fact = {"key": key or "estimate", "label": label or key or formula, "value": base,
            "range": {"low": min(vals), "high": max(vals)}, "type": "estimate", "method": method,
            "formula": formula, "inputs": [v["id"] for v in R.values() if v.get("id")],
            "input_values": {k: {kk: R[k][kk] for kk in ("low", "base", "high")} for k in R},
            "confidence": conf, "unit": unit, "year": year, "geo": geo, "currency": currency}
    return {"low": min(vals), "base": base, "high": max(vals), "formula": formula, "confidence": conf, "fact": fact}


def benchmark(segment: str, metric: str, ai: bool = False, bench: dict | None = None) -> dict:
    """A rule-of-thumb range from the benchmark library (always type estimate, confidence low)."""
    B = bench or load_benchmarks()
    seg = B["segments"].get(segment) or B["segments"]["smb"]
    if metric not in seg:
        raise KeyError(f"no benchmark '{metric}' for segment '{segment}'")
    r = {k: seg[metric][k] for k in ("low", "base", "high")}
    if ai and metric == "gross_margin":
        d = B["ai_adjustments"]["gross_margin_delta"]
        r = {"low": r["low"] + d["low"], "base": r["base"] + d["base"], "high": r["high"] + d["high"]}
    return {**r, "type": "estimate", "method": "benchmark_rule_of_thumb", "confidence": "low",
            "label": f"{metric} ({segment}) — rule of thumb", "id": f"bench_{segment}_{metric}{'_ai' if ai else ''}"}


def bench_fact(segment: str, metric: str, ai: bool = False) -> dict:
    """Ledger record for a benchmark value (so every rule of thumb used is visible in the ledger)."""
    b = benchmark(segment, metric, ai)
    return {"id": b["id"], "key": f"benchmark.{metric}", "label": b["label"], "value": b["base"],
            "range": {"low": b["low"], "high": b["high"]}, "type": "estimate", "method": "benchmark_rule_of_thumb",
            "formula": "rule-of-thumb range from config/benchmarks.json (not a sourced fact)", "confidence": "low",
            "geo": None, "year": None, "unit": "fraction" if metric not in ("acv", "cac_payback_months", "sales_cycle_days") else
            {"acv": "USD/year", "cac_payback_months": "months", "sales_cycle_days": "days"}[metric]}


def top_down(total, filters: list[dict], key_prefix: str = "market.td") -> dict:
    """total × Π shares. filters: [{"name", "share": x | {low,base,high,id}, "level": "TAM"|"SAM"|"SOM"}]."""
    env, formula, levels, facts = {"total": total}, "total", {}, []
    for i, f in enumerate(filters):
        n = f"s{i}"
        env[n] = f["share"]
        formula += f" * {n}"
        if f.get("level"):
            r = expr(formula, env, key=f"{key_prefix}.{f['level'].lower()}", method="top_down",
                     label=f"{f['level']} top-down: " + " × ".join(["total"] + [x["name"] for x in filters[:i + 1]]))
            levels[f["level"]] = r
            facts.append(r["fact"])
    return {"levels": levels, "facts": facts}


def bottom_up(segments: list[dict], key_prefix: str = "market.bu") -> dict:
    """segments: [{"name", "units", "price" (per unit per year), "serviceable", "obtainable"}] (values or ranges)."""
    rows, tot = [], {"TAM": [0, 0, 0], "SAM": [0, 0, 0], "SOM": [0, 0, 0]}
    for s in segments:
        env = {"units": s["units"], "price": s["price"], "serviceable": s.get("serviceable", 1.0),
               "obtainable": s.get("obtainable", 0.0)}
        tam = expr("units * price", env, method="bottom_up")
        sam = expr("units * price * serviceable", env, method="bottom_up")
        som = expr("units * price * serviceable * obtainable", env, method="bottom_up")
        rows.append({"segment": s.get("name", s.get("id", "")), "TAM": tam, "SAM": sam, "SOM": som,
                     "units": rng(s["units"]), "price": rng(s["price"])})
        for lvl, r in (("TAM", tam), ("SAM", sam), ("SOM", som)):
            for i, k in enumerate(("low", "base", "high")):
                tot[lvl][i] += r[k]
    facts = []
    for lvl in ("TAM", "SAM", "SOM"):
        lo, b, hi = tot[lvl]
        ids = sorted({i for r in rows for i in r[lvl]["fact"]["inputs"]})
        facts.append({"key": f"{key_prefix}.{lvl.lower()}", "label": f"{lvl} bottom-up (Σ segments)", "value": b,
                      "range": {"low": lo, "high": hi}, "type": "estimate", "method": "bottom_up",
                      "formula": {"TAM": "Σ units × price", "SAM": "Σ units × price × serviceable share",
                                  "SOM": "Σ units × price × serviceable × obtainable share"}[lvl],
                      "inputs": ids, "confidence": _min_conf([r[lvl]["confidence"] for r in rows])})
    return {"segments": rows, "totals": {k: dict(zip(("low", "base", "high"), v)) for k, v in tot.items()},
            "facts": facts}


def value_theory(units, value_per_unit, capture_share, key: str = "market.vt.tam") -> dict:
    """Value-based ceiling: customers × annual value created × share the vendor can capture."""
    return expr("units * value * capture", {"units": units, "value": value_per_unit, "capture": capture_share},
                key=key, method="value_theory", label="TAM value-theory: units × value created × capture share")


def triangulate(estimates: dict, key: str = "market.tam") -> dict:
    """estimates: {"top_down": {low,base,high}, "bottom_up": {...}, "value_theory": {...}} → combined range.
    Base = geometric mean of method bases; range = [min lows, max highs]; ratio = max/min of bases."""
    items = {k: rng(v) for k, v in estimates.items() if v}
    bases = [v["base"] for v in items.values() if v["base"] > 0]
    gm = math.exp(sum(math.log(b) for b in bases) / len(bases)) if bases else 0.0
    ratio = max(bases) / min(bases) if len(bases) > 1 else 1.0
    verdict = "consistent" if ratio <= 1.5 else ("acceptable" if ratio <= 2.0 else "inconsistent — revisit inputs")
    return {"base": gm, "low": min(v["low"] for v in items.values()), "high": max(v["high"] for v in items.values()),
            "ratio": ratio, "verdict": verdict, "methods": items,
            "fact": {"key": key, "label": f"{key} triangulated ({', '.join(items)})", "value": gm,
                     "range": {"low": min(v["low"] for v in items.values()), "high": max(v["high"] for v in items.values())},
                     "type": "estimate", "method": "triangulation", "formula": "geometric mean of method bases",
                     "inputs": [], "confidence": "medium" if ratio <= 1.5 and len(items) >= 2 else "low",
                     "note": f"spread max/min = {ratio:.2f} ({verdict})"}}


def cagr_from_drivers(industry_growth, penetration_start, penetration_end, years: int,
                      key: str = "market.cagr") -> dict:
    """Category CAGR ≈ (1 + industry nominal growth) × (penetration_end / penetration_start)^(1/years) − 1."""
    return expr(f"(1 + g) * (p1 / p0) ** (1 / {int(years)}) - 1",
                {"g": industry_growth, "p0": penetration_start, "p1": penetration_end},
                key=key, method="triangulation", unit="fraction per year",
                label="CAGR = industry nominal growth × penetration growth")


def value_price(hours_saved_month, hourly_cost, capture_share=None, key: str = "pricing.value_price_month") -> dict:
    """Monthly price ceiling from value: hours saved per month × loaded hourly cost × capture share (10–30 %)."""
    cap = capture_share if capture_share is not None else {"low": 0.1, "base": 0.2, "high": 0.3,
                                                           "method": "benchmark_rule_of_thumb", "confidence": "low"}
    return expr("hours * cost * capture", {"hours": hours_saved_month, "cost": hourly_cost, "capture": cap},
                key=key, method="value_theory", unit="money per month",
                label="value-based price = hours saved × hourly cost × capture share")


def unit_economics(segment: str, arpa_month, ai: bool = False, gross_margin=None, monthly_churn=None,
                   cac_payback_months=None, cac=None) -> dict:
    """Unit economics from ARPA + benchmark ranges (any input can be overridden with a sourced value).
    CAC = payback months × ARPA × GM (if CAC not given); LTV = ARPA × GM / churn (monthly)."""
    gm = gross_margin if gross_margin is not None else benchmark(segment, "gross_margin", ai)
    ch = monthly_churn if monthly_churn is not None else benchmark(segment, "monthly_logo_churn")
    out = {"inputs": {"arpa_month": rng(arpa_month), "gross_margin": rng(gm), "monthly_churn": rng(ch)}}
    if cac is None:
        pb = cac_payback_months if cac_payback_months is not None else benchmark(segment, "cac_payback_months")
        out["inputs"]["cac_payback_months"] = rng(pb)
        c = expr("pb * arpa * gm", {"pb": pb, "arpa": arpa_month, "gm": gm}, key="ue.cac", method="benchmark_rule_of_thumb",
                 label="CAC = payback months × ARPA × gross margin")
    else:
        c = expr("cac", {"cac": cac}, key="ue.cac", method="derived")
    ltv = expr("arpa * gm / churn", {"arpa": arpa_month, "gm": gm, "churn": ch}, key="ue.ltv",
               method="benchmark_rule_of_thumb", label="LTV = ARPA × GM / monthly churn")
    lifetime = expr("1 / churn", {"churn": ch}, key="ue.lifetime_months", method="benchmark_rule_of_thumb")
    # LTV/CAC with correlated inputs: compute from the scenario corners explicitly.
    ratio_env = {"arpa": arpa_month, "gm": gm, "churn": ch}
    if cac is None:
        ratio_env["pb"] = out["inputs"]["cac_payback_months"]
        r = expr("1 / (churn * pb)", {"churn": ch, "pb": ratio_env["pb"]}, key="ue.ltv_cac",
                 method="benchmark_rule_of_thumb", label="LTV/CAC = 1 / (churn × payback months)")
        pbk = rng(ratio_env["pb"])
    else:
        r = expr("arpa * gm / churn / cac", {**ratio_env, "cac": cac}, key="ue.ltv_cac", method="derived")
        pbk = rng(expr("cac / (arpa * gm)", {"cac": cac, "arpa": arpa_month, "gm": gm})["base"])
    nrr = benchmark(segment, "nrr")
    out.update({"cac": c, "ltv": ltv, "ltv_cac": r, "lifetime_months": lifetime, "cac_payback_months": pbk,
                "gross_margin": rng(gm), "monthly_churn": rng(ch), "nrr": nrr,
                "annual_churn": expr("1 - (1 - churn) ** 12", {"churn": ch}, key="ue.annual_churn",
                                     method="derived", label="annual churn = 1 − (1 − monthly)^12"),
                "verdict": "healthy" if r["base"] >= 3 else ("borderline" if r["base"] >= 1.5 else "weak"),
                "label": "rules of thumb unless overridden by sourced inputs"})
    out["facts"] = [x["fact"] for x in (c, ltv, r, lifetime, out["annual_churn"])]
    return out


def comparables(revenue, multiple, private_discount=None, key: str = "valuation.ev_comparables") -> dict:
    """EV = revenue × listed-peer EV/Revenue × (1 − private/stage discount)."""
    pdisc = private_discount if private_discount is not None else {
        **{k: load_benchmarks()["valuation"]["private_discount"][k] for k in ("low", "base", "high")},
        "method": "benchmark_rule_of_thumb", "confidence": "low", "id": "bench_private_discount"}
    return expr("rev * mult * (1 - disc)", {"rev": revenue, "mult": multiple, "disc": pdisc}, key=key,
                method="derived", label="EV by comparables = revenue × peer EV/Revenue × (1 − private discount)")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv.pop(0)
    if cmd == "benchmarks":
        print(dump_json(load_benchmarks()))
        return 0
    payload, out, _ = cli_io(argv)
    payload.pop("locale", None)
    fn = {"expr": expr, "top_down": top_down, "bottom_up": bottom_up, "value_theory": value_theory,
          "triangulate": triangulate, "cagr_from_drivers": cagr_from_drivers, "value_price": value_price,
          "unit_economics": unit_economics, "comparables": comparables, "benchmark": benchmark}[cmd]
    print(dump_json(fn(**payload), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
