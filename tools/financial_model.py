#!/usr/bin/env python3
"""financial_model.py — compact multi-year model for an IT product: P&L, cash, unit economics,
NPV/IRR (project), investor MOIC/IRR, scenarios and a 2-D sensitivity table.

Input JSON (money in one currency, nominal; rates are fractions; lists are per model year):
{
  "currency": "RUB" | "USD" | "CNY", "start_year": 2026, "years": 5,
  "revenue": {"customers_start": 4, "new_customers": [8,16,28,40,52], "churn_annual": 0.10,
              "arpa_start": 2.4e6, "arpa_growth": 0.08,          # or "arpa": [..] per year
              "other_revenue": [12e6, 15e6, 15e6, 12e6, 10e6]},   # pilots/services, optional
  "costs": {"cogs_pct": 0.30, "rd": [60e6, 80e6, 95e6, 110e6, 120e6],
            "sm_pct": 0.35,  # or "sm": [..]
            "ga": [20e6, 25e6, 30e6, 34e6, 38e6], "capex": [10e6, 8e6, 8e6, 10e6, 12e6]},
  "working_capital_pct": 0.10,      # of revenue increase
  "tax_rate": 0.05,                 # with loss carry-forward (simplified)
  "cash_start": 40e6,
  "funding": [{"year": 2026, "amount": 150e6}],
  "discount_rate": 0.30,
  "terminal": {"method": "exit_multiple", "multiple": 4.0, "metric": "revenue"},  # or {"method":"gordon","growth":0.04}
  "investor": {"investment": 150e6, "pre_money": 450e6, "entry_year": 2026, "exit_year": 2030,
               "exit_multiple": 4.0, "exit_metric": "revenue", "later_dilution": 0.15},
  "scenarios": {"bear": {"new_customers_mult": 0.6, "arpa_mult": 0.9, "churn_annual": 0.18, "exit_multiple": 2.5},
                "base": {},
                "bull": {"new_customers_mult": 1.3, "arpa_mult": 1.1, "churn_annual": 0.07, "exit_multiple": 5.0}},
  "sensitivity": {"output": "npv", "x": {"param": "arpa_mult", "values": [0.8,0.9,1.0,1.1,1.2]},
                  "y": {"param": "new_customers_mult", "values": [0.6,0.8,1.0,1.2,1.4]}}
}
Scenario/sensitivity params: new_customers_mult, arpa_mult, churn_annual, cogs_pct, sm_mult, rd_mult,
exit_multiple, discount_rate.

CLI: python financial_model.py --input fin.json [--out result.json]
"""
from __future__ import annotations

import copy
import math
import sys

try:
    from fmt_utils import cli_io, dump_json
    from metrics_calc import _irr
except ImportError:  # pragma: no cover
    from .fmt_utils import cli_io, dump_json  # type: ignore
    from .metrics_calc import _irr  # type: ignore


def _series(val, n, growth=0.0, start=None):
    if isinstance(val, list):
        if len(val) < n:
            val = val + [val[-1]] * (n - len(val))
        return [float(v) for v in val[:n]]
    if val is None and start is not None:
        return [start * (1 + growth) ** t for t in range(n)]
    return [float(val or 0.0)] * n


def run_model(spec: dict, params: dict | None = None) -> dict:
    p = dict(params or {})
    s = copy.deepcopy(spec)
    n = int(s.get("years", 5))
    y0 = int(s.get("start_year", 2026))
    years = [y0 + t for t in range(n)]
    rv, cs = s["revenue"], s["costs"]

    new = [v * p.get("new_customers_mult", 1.0) for v in _series(rv.get("new_customers", 0), n)]
    churn = p.get("churn_annual", rv.get("churn_annual", 0.1))
    arpa = _series(rv.get("arpa"), n, rv.get("arpa_growth", 0.0), rv.get("arpa_start"))
    arpa = [a * p.get("arpa_mult", 1.0) for a in arpa]
    other = _series(rv.get("other_revenue", 0.0), n)
    cogs_pct = p.get("cogs_pct", cs.get("cogs_pct", 0.3))
    rd = [v * p.get("rd_mult", 1.0) for v in _series(cs.get("rd", 0.0), n)]
    ga = _series(cs.get("ga", 0.0), n)
    capex = _series(cs.get("capex", 0.0), n)
    tax_rate = s.get("tax_rate", 0.2)
    wc_pct = s.get("working_capital_pct", 0.0)
    disc = p.get("discount_rate", s.get("discount_rate", 0.25))
    funding_by_year = {}
    for f in s.get("funding", []):
        funding_by_year[int(f["year"])] = funding_by_year.get(int(f["year"]), 0.0) + f["amount"]

    rows, cust = [], float(rv.get("customers_start", 0))
    cash = float(s.get("cash_start", 0.0))
    loss_cf, prev_rev, prev_arr = 0.0, None, cust * arpa[0]
    for t in range(n):
        begin = cust
        churned = begin * churn
        end = begin - churned + new[t]
        avg = (begin + end) / 2
        recurring = avg * arpa[t]
        revenue = recurring + other[t]
        cogs = revenue * cogs_pct
        gp = revenue - cogs
        sm = (_series(cs["sm"], n)[t] if "sm" in cs else revenue * cs.get("sm_pct", 0.3)) * p.get("sm_mult", 1.0)
        opex = rd[t] + sm + ga[t]
        ebitda = gp - opex
        taxable = ebitda - loss_cf if ebitda > 0 else 0.0
        if ebitda <= 0:
            loss_cf += -ebitda
        else:
            loss_cf = max(loss_cf - ebitda, 0.0)
        tax = max(taxable, 0.0) * tax_rate
        net_income = ebitda - tax
        d_wc = (revenue - (prev_rev if prev_rev is not None else revenue)) * wc_pct
        fcf = ebitda - tax - capex[t] - d_wc
        fund = funding_by_year.get(years[t], 0.0)
        cash = cash + fcf + fund
        arr_end = end * arpa[t]
        net_new_arr = arr_end - prev_arr
        cac = sm / new[t] if new[t] else None
        ltv = (arpa[t] * (1 - cogs_pct) / churn) if churn > 0 else None
        ltv_cap = min(ltv, arpa[t] * (1 - cogs_pct) * 5) if ltv else None  # cap lifetime at 5 years
        growth = revenue / prev_rev - 1 if prev_rev else None
        rows.append({
            "year": years[t], "customers_begin": begin, "new_customers": new[t], "churned": churned,
            "customers_end": end, "arpa": arpa[t], "recurring_revenue": recurring, "other_revenue": other[t],
            "revenue": revenue, "revenue_growth": growth, "cogs": cogs, "gross_profit": gp,
            "gross_margin": gp / revenue if revenue else None, "rd": rd[t], "sm": sm, "ga": ga[t], "opex": opex,
            "ebitda": ebitda, "ebitda_margin": ebitda / revenue if revenue else None, "tax": tax,
            "net_income": net_income, "capex": capex[t], "delta_wc": d_wc, "fcf": fcf, "funding": fund,
            "cash_end": cash, "arr_end": arr_end, "net_new_arr": net_new_arr,
            "cac": cac, "ltv": ltv_cap, "ltv_cac": (ltv_cap / cac) if (ltv_cap and cac) else None,
            "cac_payback_months": (cac / (arpa[t] / 12 * (1 - cogs_pct))) if cac else None,
            "rule_of_40": (growth + ebitda / revenue) if (growth is not None and revenue) else None,
            "burn_multiple": ((-fcf) / net_new_arr) if (fcf < 0 and net_new_arr > 0) else None,
        })
        prev_rev, cust, prev_arr = revenue, end, arr_end

    # valuation
    term = s.get("terminal", {"method": "exit_multiple", "multiple": 3.0, "metric": "revenue"})
    last = rows[-1]
    if term.get("method") == "gordon":
        g = term.get("growth", 0.03)
        tv = last["fcf"] * (1 + g) / (disc - g) if disc > g else float("nan")
    else:
        mult = p.get("exit_multiple", term.get("multiple", 3.0))
        tv = mult * last[term.get("metric", "revenue")]
    fcfs = [r["fcf"] for r in rows]
    pv_fcf = sum(c / (1 + disc) ** (i + 1) for i, c in enumerate(fcfs))
    pv_tv = tv / (1 + disc) ** n
    npv_val = pv_fcf + pv_tv
    project_irr = _irr([0.0] + fcfs[:-1] + [fcfs[-1] + tv]) if any(c < 0 for c in fcfs) else None

    inv = s.get("investor")
    investor = None
    if inv:
        exit_year = int(inv.get("exit_year", years[-1]))
        er = next((r for r in rows if r["year"] == exit_year), rows[-1])
        mult = p.get("exit_multiple", inv.get("exit_multiple", 3.0))
        exit_ev = mult * er[inv.get("exit_metric", "revenue")]
        exit_equity = exit_ev + er["cash_end"]  # no debt assumed
        post = inv["pre_money"] + inv["investment"]
        own = inv["investment"] / post * (1 - inv.get("later_dilution", 0.0))
        proceeds = exit_equity * own
        hold = exit_year - int(inv.get("entry_year", years[0]))
        moic = proceeds / inv["investment"]
        investor = {"post_money": post, "ownership_at_entry": inv["investment"] / post, "ownership_at_exit": own,
                    "exit_year": exit_year, "exit_ev": exit_ev, "exit_equity": exit_equity, "proceeds": proceeds,
                    "moic": moic, "irr": (moic ** (1 / hold) - 1) if hold > 0 and moic > 0 else None,
                    "holding_years": hold, "exit_multiple": mult}

    first_pos = next((r["year"] for r in rows if r["ebitda"] > 0), None)
    min_cash = min(r["cash_end"] for r in rows)
    rev0, revN = rows[0]["revenue"], rows[-1]["revenue"]
    summary = {
        "revenue_first": rev0, "revenue_last": revN,
        "revenue_cagr": (revN / rev0) ** (1 / (n - 1)) - 1 if rev0 > 0 and n > 1 else None,
        "ebitda_breakeven_year": first_pos, "min_cash": min_cash,
        "funding_gap": -min_cash if min_cash < 0 else 0.0,
        "cumulative_funding": sum(funding_by_year.values()),
        "npv": npv_val, "pv_fcf": pv_fcf, "pv_terminal": pv_tv, "terminal_value": tv,
        "tv_share": pv_tv / npv_val if npv_val else None, "project_irr": project_irr,
        "discount_rate": disc, "customers_last": rows[-1]["customers_end"],
        "arr_last": rows[-1]["arr_end"], "gross_margin_last": rows[-1]["gross_margin"],
        "ebitda_margin_last": rows[-1]["ebitda_margin"], "ltv_cac_last": rows[-1]["ltv_cac"],
        "cac_payback_last": rows[-1]["cac_payback_months"],
    }
    if investor:
        summary.update({"moic": investor["moic"], "investor_irr": investor["irr"]})
    warnings = []
    if min_cash < 0:
        warnings.append(f"cash goes negative (min {min_cash:,.0f}): funding gap — add a round or cut burn")
    if summary["tv_share"] and summary["tv_share"] > 0.75:
        warnings.append("terminal value > 75% of NPV: valuation depends on exit assumptions")
    if rows[-1]["ltv_cac"] and rows[-1]["ltv_cac"] < 3:
        warnings.append("LTV/CAC < 3 in final year")
    return {"years": years, "rows": rows, "summary": summary, "investor": investor, "warnings": warnings,
            "params": p}


def run_scenarios(spec: dict) -> dict:
    scn = spec.get("scenarios") or {"base": {}}
    return {name: run_model(spec, ov) for name, ov in scn.items()}


def sensitivity(spec: dict) -> dict | None:
    cfg = spec.get("sensitivity")
    if not cfg:
        return None
    out_key = cfg.get("output", "npv")
    xs, ys = cfg["x"]["values"], cfg["y"]["values"]
    grid = []
    for yv in ys:
        row = []
        for xv in xs:
            r = run_model(spec, {cfg["x"]["param"]: xv, cfg["y"]["param"]: yv})
            row.append(r["summary"].get(out_key))
        grid.append(row)
    return {"output": out_key, "x_param": cfg["x"]["param"], "x_values": xs,
            "y_param": cfg["y"]["param"], "y_values": ys, "grid": grid}


def build(spec: dict) -> dict:
    scen = run_scenarios(spec)
    base = scen.get("base") or next(iter(scen.values()))
    years = [str(y) for y in base["years"]]
    charts = {
        "revenue_ebitda": {"type": "column", "categories": years, "series": [
            {"name": "revenue", "values": [r["revenue"] for r in base["rows"]]},
            {"name": "ebitda", "values": [r["ebitda"] for r in base["rows"]]}]},
        "revenue_scenarios": {"type": "line", "categories": years, "series": [
            {"name": k, "values": [r["revenue"] for r in v["rows"]]} for k, v in scen.items()]},
        "cash": {"type": "line", "categories": years, "series": [
            {"name": "cash", "values": [r["cash_end"] for r in base["rows"]]}]},
    }
    return {"currency": spec.get("currency") or __import__("locales").get_locale(spec.get("locale") or "ru")["currency"], "base": base, "scenarios": {
        k: {"summary": v["summary"], "investor": v["investor"], "warnings": v["warnings"], "rows": v["rows"]}
        for k, v in scen.items()},
        "sensitivity": sensitivity(spec), "charts": charts}


def main(argv=None):
    payload, out, _ = cli_io(argv)
    if not payload:
        print(__doc__)
        return 1
    res = build(payload)
    loc = payload.get("locale")
    if loc:   # formatted summary in the requested locale
        from fmt_utils import fmt_money, fmt_multiple, fmt_pct
        cur = res["currency"]
        res["display"] = {"locale": loc, **{k: {
            "revenue_last": fmt_money(v["summary"]["revenue_last"], cur, loc),
            "npv": fmt_money(v["summary"]["npv"], cur, loc),
            "min_cash": fmt_money(v["summary"]["min_cash"], cur, loc),
            "moic": fmt_multiple(v["summary"].get("moic"), 1, loc) if v["summary"].get("moic") else None,
            "irr": fmt_pct(v["summary"].get("investor_irr"), 0, loc) if v["summary"].get("investor_irr") is not None else None}
            for k, v in res["scenarios"].items()}}
    print(dump_json(res, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
