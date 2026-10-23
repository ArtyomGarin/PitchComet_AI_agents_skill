#!/usr/bin/env python3
"""auto_pitch.py — one command from a short product description to a computed pitch.

  profile (product_profiler) → market definition (market_definer) → research ledger
  (research_ledger: facts the agent found on the web, with links) → estimates (estimator:
  TAM/SAM/SOM top-down + bottom-up + value-based, CAGR, price, unit economics, customer ROI/TCO,
  valuation) → financial model → scoring → pitch pattern → deck.pptx + report.docx → QA.

It never stops at "missing data": a figure that is not in the ledger is estimated with an explicit
method (benchmark range, proxy, value theory) and logged as an estimate with formula, range and
confidence. Only things that cannot be estimated go to a short "to confirm with the founders" list.

RESEARCH HOOK. Run `--plan-only` first: it writes research_plan.json with the ledger keys and the
web-search queries for the market. The agent researches them with its own web tools, writes facts
into the ledger (research_ledger.py add …) and runs auto_pitch again. Offline (empty ledger) the
command still completes with low-confidence assumptions and watermarks the deck "offline draft".

brief.json:
{"name": "Shiftlyra", "text": "short description", "market": "ru", "locale": "ru",
 "pattern": "auto" | "large_investor" | "small_investor" | "corporate" | "smb" | "government",
 "audience": "who will see the pitch (used when pattern = auto)", "themes": ["comet"],
 "ledger": "ledger.json", "fictional": true, "segments": [...optional...],
 "story": {"tagline": "...", "features": [...], "today": [...], "alternatives": [...], "drivers": [...]},
 "assumptions": {"tax_rate": 0.2, "cash_start": 0}}

Ledger keys read (see prompts/*/research_loop.md): count.<segment_id>, industry.revenue.<ISIC>,
share.size_band.<ISIC>, industry.growth, wage.hourly, wage.monthly, wage.developer_annual,
pricing.price_month, value.hours_saved_month, adoption.current, adoption.horizon,
adoption.serviceable, share.obtainable, macro.inflation, macro.risk_free,
valuation.peer_ev_revenue, share.it_spend, share.category_of_it, deal.units.

CLI:
  python auto_pitch.py --brief brief.json [--pattern smb] [--theme warm] [--locale en] [--out DIR]
                       [--plan-only] [--no-render]
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import estimator as E  # noqa: E402
import research_ledger as RL  # noqa: E402
from financial_model import build as fin_build  # noqa: E402
from fmt_utils import dump_json, fmt_money, fmt_multiple, fmt_number, fmt_pct, load_json  # noqa: E402
from locales import get_locale, norm_locale  # noqa: E402
from market_definer import COUNTRY, LANG_OF, define  # noqa: E402
from metrics_calc import METRICS  # noqa: E402
from pitch_story import STORY_LOCALES, build_specs  # noqa: E402
from product_profiler import CURRENCY_OF, profile as make_profile  # noqa: E402

ROOT = os.path.join(HERE, "..")
PATTERNS = os.path.join(ROOT, "patterns", "patterns.json")
MONTHS_RU = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]


# ----------------------------------------------------------------------------- patterns
def load_patterns() -> dict:
    return load_json(PATTERNS)


def select_pattern(pattern: str | None, audience: str | None = None) -> dict:
    """Explicit id wins; 'auto' or None → keyword match on the audience description."""
    pj = load_patterns()
    P = pj["patterns"]
    pid = pattern if pattern and pattern != "auto" else None
    why = "explicit"
    if not pid:
        text = (audience or "").lower()
        scores = {k: sum(1 for w in v.get("audience_keywords", []) if w.lower() in text) for k, v in P.items()}
        best = max(scores, key=lambda k: scores[k]) if scores else None
        if best and scores[best] > 0:
            pid, why = best, f"audience keywords ({scores[best]} hits)"
        else:
            pid, why = pj.get("default", "small_investor"), "default (no audience keywords matched)"
    if pid not in P:
        raise KeyError(f"unknown pattern '{pid}' (one of {', '.join(P)})")
    out = copy.deepcopy(P[pid])
    out["id"], out["selected_by"] = pid, why
    return out


# ----------------------------------------------------------------------------- ledger access
class Inputs:
    """Look up ledger values; when absent, fall back to a labelled estimate and log it."""

    def __init__(self, ledger: dict, currency: str, base_year: int, market: str):
        self.ledger = ledger
        self.cur, self.year, self.market = currency, base_year, market
        self.exp = RL.export(ledger, currency, base_year)
        self.added: list[dict] = []
        self.offline = False
        self.used: dict[str, dict] = {}
        self.bench = E.load_benchmarks()

    GEO = {"ru": "RU", "en": "US", "zh": "CN", "vn": "VN", "id": "ID", "my": "MY"}

    def _lookup(self, key: str):
        """Plain key first; then the same key tagged with the market's geo (facts with "geo" resolve as key@GEO);
        then any single geo-tagged variant."""
        vals, k = self.exp["values"], key.replace(".", "_")
        if k in vals:
            return vals[k]
        g = self.GEO.get(self.market, "")
        if f"{k}_{g}" in vals:
            return vals[f"{k}_{g}"]
        alts = [v for kk, v in vals.items() if re.fullmatch(re.escape(k) + r"_[A-Z]{2,3}", kk)]
        return alts[0] if len(alts) == 1 else None

    def get(self, key: str):
        f = self._lookup(key)
        if not f:
            return None
        r = {"base": f["value"], "low": (f.get("range") or {}).get("low", f["value"]),
             "high": (f.get("range") or {}).get("high", f["value"]), "id": f["id"], "type": f["type"],
             "confidence": f["confidence"], "source_url": f.get("source_url")}
        self.used[key] = f
        return r

    def _log(self, key, rng, method, formula, label, unit=None, confidence="low", inputs=None):
        fid = RL._slug(f"auto_{key}")
        fact = {"id": fid, "key": key, "label": label, "value": rng["base"],
                "range": {"low": rng["low"], "high": rng["high"]}, "type": "estimate", "method": method,
                "formula": formula, "confidence": confidence, "unit": unit, "inputs": inputs or [], "year": self.year}
        if not any(f["id"] == fid for f in self.added):
            self.added.append(fact)
        return {**rng, "id": fid, "type": "estimate", "confidence": confidence}

    def bench_rng(self, section: str, name: str, key: str, label: str, unit=None):
        b = self.bench[section][name]
        r = {"low": b["low"], "base": b["base"], "high": b["high"]}
        return self._log(key, r, "benchmark_rule_of_thumb", f"rule of thumb: config/benchmarks.json {section}.{name}",
                         label, unit)

    def offline_rng(self, name: str, key: str, label: str, unit=None, scale: float = 1.0):
        self.offline = True
        b = self.bench["offline_defaults"][name]
        r = {k: b[k] * scale for k in ("low", "base", "high")}
        return self._log(key, r, "assumption", "OFFLINE assumption (config/benchmarks.json offline_defaults) — replace by research",
                         label, unit)

    def need(self, key, fallback):
        v = self.get(key)
        return v if v is not None else fallback()

    def add_estimate(self, est: dict, key: str, label: str, unit=None):
        f = dict(est["fact"])
        f.update({"id": RL._slug(f"auto_{key}"), "key": key, "label": label, "unit": unit, "year": self.year})
        f.pop("input_values", None)
        self.added = [x for x in self.added if x["id"] != f["id"]] + [f]
        return {"low": est["low"], "base": est["base"], "high": est["high"], "id": f["id"], "type": "estimate",
                "confidence": est["confidence"]}


def _r(x):
    return {"low": x["low"], "base": x["base"], "high": x["high"]}


def _round_price(p: float) -> float:
    if p <= 0:
        return p
    mag = 10 ** (math.floor(math.log10(p)) - 1)
    return round(p / mag) * mag


# ----------------------------------------------------------------------------- core computation
def compute(brief: dict, ledger: dict, pattern: dict, profile_doc: dict, mdef: dict, base_year: int) -> dict:
    P = profile_doc["profile"]
    mk = mdef["definition"]["market"]
    cur = brief.get("currency") or CURRENCY_OF.get(mk, "USD")
    A = brief.get("assumptions", {})
    I = Inputs(ledger, cur, base_year, mk)
    bseg_name = (P.get("buyer_segment") or ["smb"])[0]
    bseg = {"smb": "smb", "mid_market": "mid_market", "enterprise": "enterprise", "consumer": "consumer"}.get(bseg_name, "smb")
    ai = bool(P.get("ai_heavy"))
    years = int(brief.get("years", I.bench["finance_defaults"]["years"]))
    horizon = base_year + years
    usd = 1.0
    if cur != "USD":
        fx = I.get("fx.usd")    # units of local currency per USD (needed only for offline USD defaults)
        usd = fx["base"] if fx else None

    # ---------------- value inputs
    hours = I.need("value.hours_saved_month", lambda: I.bench_rng("value_defaults", "hours_saved_per_unit_month",
                                                                   "value.hours_saved_month", "hours saved per unit per month", "hours"))
    loaded = I.bench_rng("value_defaults", "loaded_cost_factor", "value.loaded_cost_factor", "employer cost over gross wage", "x")
    wage_h = I.get("wage.hourly")
    if wage_h is None:
        wm = I.get("wage.monthly")
        if wm is not None:
            hpm = I.bench_rng("value_defaults", "hours_per_month", "value.hours_per_month", "paid hours per month", "hours")
            wage_h = I.add_estimate(E.expr("w / h", {"w": wm, "h": hpm}), "wage.hourly",
                                    "hourly wage = monthly wage / paid hours", cur)
        else:
            scale = usd if usd else 1.0
            wage_h = I.offline_rng("hourly_cost_usd", "wage.hourly", "hourly wage (offline)", cur, scale)
    hourly_cost = I.add_estimate(E.expr("w * k", {"w": wage_h, "k": loaded}), "value.hourly_cost",
                                 "loaded hourly cost = hourly wage × loaded-cost factor", cur)
    capture = I.bench_rng("value_defaults", "value_capture_share", "value.capture_share", "share of value the vendor charges", "fraction")
    price = I.get("pricing.price_month")
    price_basis_key = "sourced" if price and price["type"] == "sourced" else ("ledger" if price else "value")
    if price is None:
        vp = E.value_price(hours, hourly_cost, capture)
        pr = _round_price(vp["base"])
        price = I.add_estimate({**vp, "base": pr, "fact": {**vp["fact"], "value": pr,
                                "formula": vp["formula"] + " (rounded to 2 significant digits)"}},
                               "pricing.price_month", "price per unit per month (value-based)", cur)
    price_year = I.add_estimate(E.expr("p * 12", {"p": price}), "pricing.price_year", "annual price per unit", cur)

    # ---------------- segments & bottom-up
    segs = brief.get("segments") or mdef["segments"]
    serviceable = I.need("adoption.serviceable", lambda: I.bench_rng("adoption", "serviceable_share", "adoption.serviceable",
                                                                       "serviceable share of the segment", "fraction"))
    obtainable = I.need("share.obtainable", lambda: I.bench_rng("adoption", "obtainable_share_5y", "share.obtainable",
                                                                  "obtainable share at the horizon", "fraction"))
    bu_in, seg_rows = [], []
    for s in segs:
        u = I.get(f"count.{s['id']}")
        if u is None:
            u = I.offline_rng("units_per_segment", f"count.{s['id']}", f"units in segment {s['id']} (offline)", "units")
        bu_in.append({"name": s.get("name", s["id"]), "units": u, "price": price_year, "serviceable": serviceable,
                      "obtainable": obtainable})
        seg_rows.append({"id": s["id"], "name": s.get("name", s["id"]), "units": u, "isic": s.get("isic")})
    bu = E.bottom_up(bu_in)
    units_total = sum(r["units"]["base"] for r in seg_rows)
    tam_bu = bu["totals"]["TAM"]
    for f in bu["facts"]:
        f2 = dict(f)
        f2["id"] = RL._slug("auto_" + f["key"])
        f2["year"] = base_year
        f2["unit"] = cur
        I.added.append(f2)

    # ---------------- top-down (industry sales × size-band share × IT share × category share)
    it_share = I.need("share.it_spend", lambda: I.bench_rng("rules", "it_spend_share_of_revenue", "share.it_spend",
                                                              "IT spend as share of revenue", "fraction"))
    cat_share = I.need("share.category_of_it", lambda: I.bench_rng("rules", "category_share_of_it_spend", "share.category_of_it",
                                                                     "category share of IT spend", "fraction"))
    inds = sorted({s.get("isic") for s in segs if s.get("isic")})
    td_total = None
    td_parts = {}
    for ind in inds:
        rev = I.get(f"industry.revenue.{ind}")
        if rev is None:
            continue
        band = I.get(f"share.size_band.{ind}") or {"low": 1.0, "base": 1.0, "high": 1.0}
        td_parts[ind] = E.expr("r * b", {"r": rev, "b": band})
    tam_td = None
    if td_parts:
        td_total = {k: sum(v[k] for v in td_parts.values()) for k in ("low", "base", "high")}
        td_total["confidence"] = min((v["confidence"] for v in td_parts.values()), key=["low", "medium", "high"].index)
        tdr = E.expr("total * it * cat", {"total": td_total, "it": it_share, "cat": cat_share}, method="top_down")
        tam_td = I.add_estimate(tdr, "market.td.tam", "TAM top-down = industry sales (target size band) × IT share × category share", cur)

    # ---------------- value theory
    annual_value = E.expr("h * c * 12", {"h": hours, "c": hourly_cost})
    vt = E.value_theory({"low": sum(r["units"]["low"] for r in seg_rows), "base": units_total,
                         "high": sum(r["units"]["high"] for r in seg_rows)}, _r(annual_value), capture)
    tam_vt = I.add_estimate(vt, "market.vt.tam", "TAM value-based = units × annual value created × capture share", cur)
    tri = E.triangulate({"bottom_up": tam_bu, **({"top_down": _r(tam_td)} if tam_td else {}), "value_theory": _r(tam_vt)})
    I.added.append({**tri["fact"], "id": "auto_market_tam_triangulated", "year": base_year, "unit": cur})

    # ---------------- CAGR
    growth = I.get("industry.growth")
    if growth is None:
        infl = I.get("macro.inflation")
        growth = (I.add_estimate(E.expr("i + 0.02", {"i": infl}), "industry.growth", "industry nominal growth ≈ inflation + 2 pp real (rule of thumb)", "fraction")
                  if infl else I.offline_rng("industry_growth", "industry.growth", "industry nominal growth (offline)", "fraction"))
    pen0 = I.need("adoption.current", lambda: I._log("adoption.current", {"low": 0.15, "base": 0.2, "high": 0.25},
                                                     "benchmark_rule_of_thumb", "rule of thumb: young category, 15–25 % of segment uses category software",
                                                     "category penetration today", "fraction"))
    pen1 = I.need("adoption.horizon", lambda: I._log("adoption.horizon", {"low": 0.25, "base": 0.32, "high": 0.4},
                                                     "benchmark_rule_of_thumb", "rule of thumb: penetration at the horizon",
                                                     "category penetration at the horizon", "fraction"))
    # penetration today is held at its base value so the range reflects growth and the horizon level
    cg = E.cagr_from_drivers(growth, {"base": pen0["base"], "id": pen0.get("id"), "confidence": pen0.get("confidence")}, pen1, years)
    cagr = I.add_estimate(cg, "market.cagr", "category CAGR = (1 + industry growth) × penetration growth^(1/years) − 1", "fraction")

    # ---------------- unit economics
    ue = E.unit_economics(bseg, price, ai=ai)
    for f in ue["facts"]:
        I.added.append({**{k: v for k, v in f.items() if k != "input_values"}, "id": RL._slug("auto_" + f["key"]), "year": base_year})
    for nm in ("gross_margin", "monthly_logo_churn", "cac_payback_months", "nrr"):
        bf = E.bench_fact(bseg, nm, ai and nm == "gross_margin")
        if not any(x["id"] == bf["id"] for x in I.added):
            I.added.append(bf)

    # ---------------- customer value (per unit, then per corporate deal)
    automation = I.bench_rng("value_defaults", "automation_share_of_manual_time", "value.automation_share", "share of manual time removed", "fraction")
    ramp = I.bench_rng("value_defaults", "first_year_ramp", "value.first_year_ramp", "year-1 benefit ramp", "fraction")
    deal_units = I.need("deal.units", lambda: I.bench_rng("value_defaults", "deal_units", "deal.units", "units per corporate deal", "units"))
    saving_month = annual_value["base"] / 12
    manual_hours = hours["base"] / automation["base"]
    impl_share = E.benchmark("mid_market", "implementation_share_of_acv")["base"]
    du = deal_units["base"]
    roi = METRICS["customer_roi"](annual_benefit=annual_value["base"] * du, annual_cost=price_year["base"] * du,
                                  one_off_cost=impl_share * price_year["base"] * du, years=3, ramp_first_year=ramp["base"])
    tco = METRICS["customer_tco"](years=3, subscription_per_year=price_year["base"] * du, implementation=impl_share * price_year["base"] * du,
                                  internal_staff_per_year=(manual_hours - hours["base"]) * hourly_cost["base"] * 12 * du,
                                  alternative_cost_per_year=manual_hours * hourly_cost["base"] * 12 * du)
    smb_v = METRICS["smb_monthly_value"](price_per_month=price["base"], hours_saved_per_month=hours["base"], hourly_cost=hourly_cost["base"])

    # ---------------- discount rate, multiples
    rf = I.get("macro.risk_free") or I.offline_rng("risk_free", "macro.risk_free", "risk-free rate (offline)", "fraction")
    vprem = I.bench_rng("finance_defaults", "venture_risk_premium", "valuation.venture_premium", "early-stage risk premium", "fraction")
    disc = I.add_estimate(E.expr("rf + vp", {"rf": rf, "vp": vprem}), "valuation.discount_rate", "discount rate = risk-free + early-stage premium", "fraction")
    mult = I.get("valuation.peer_ev_revenue") or I.offline_rng("peer_ev_revenue", "valuation.peer_ev_revenue", "peer EV/Revenue (offline)", "x")
    mlow = I.get("valuation.peer_ev_revenue_low")
    if mlow:
        mult = {**mult, "low": min(mult["low"], mlow["base"])}
    pdisc = I.bench_rng("valuation", "private_discount", "valuation.private_discount", "private / early-stage discount to listed peers", "fraction")
    extra = (I.bench["finance_defaults"].get("market_discount_extra") or {}).get(mk)
    if extra:
        mdisc = I._log("valuation.market_discount", {k: extra[k] for k in ("low", "base", "high")}, "benchmark_rule_of_thumb",
                       "rule of thumb: " + extra.get("_note", ""), "extra market discount to US peer multiples", "fraction")
        eff = E.expr("m * (1 - d) * (1 - x)", {"m": mult, "d": pdisc, "x": mdisc})
    else:
        mdisc = None
        eff = E.expr("m * (1 - d)", {"m": mult, "d": pdisc})
    exit_mult = I.add_estimate(eff, "valuation.exit_multiple", "exit EV/Revenue = peer multiple × (1 − private discount)" + (" × (1 − market discount)" if mdisc else ""), "x")

    # ---------------- finance input
    FD = I.bench["finance_defaults"]
    infl = I.get("macro.inflation")
    arpa_growth = min(infl["base"], 0.08) if infl else 0.03
    churn_m = ue["monthly_churn"]
    churn_a = {k: 1 - (1 - churn_m[k]) ** 12 for k in ("low", "base", "high")}
    curve = FD["new_customer_curve"][:years] + [FD["new_customer_curve"][-1]] * max(0, years - len(FD["new_customer_curve"]))
    # SOM at the horizon in revenue → customers at the horizon (customers × ARPA_horizon)
    sam_bu = bu["totals"]["SAM"]["base"]
    som_h_base_y0 = bu["totals"]["SOM"]["base"]
    cagr_b = cagr["base"]
    som_h = som_h_base_y0 * (1 + cagr_b) ** years
    arpa_h = price_year["base"] * (1 + arpa_growth) ** (years - 1)
    target_cust = som_h / arpa_h
    c0 = float(A.get("customers_start", 0))

    def end_customers(k):
        cust = c0
        for w in curve:
            cust = cust * (1 - churn_a["base"]) + k * w
        return cust
    k = (target_cust - end_customers(0)) / (end_customers(1) - end_customers(0)) if end_customers(1) != end_customers(0) else 0
    new = [max(0.0, round(k * w)) for w in curve]
    cac = ue["cac"]["base"]
    dev = I.get("wage.developer_annual")
    if dev is None:
        wm = I.get("wage.monthly")
        dvf = I.bench_rng("finance_defaults", "developer_cost_vs_avg_wage", "cost.developer_factor", "developer wage over average wage", "x")
        if wm:
            dev = I.add_estimate(E.expr("w * 12 * f", {"w": wm, "f": dvf}), "wage.developer_annual", "developer wage = average monthly wage × 12 × factor", cur)
        else:
            dev = I.add_estimate(E.expr("h * 165 * 12 * f", {"h": wage_h, "f": dvf}), "wage.developer_annual", "developer wage = hourly wage × 165 × 12 × factor", cur)
    dev_loaded = dev["base"] * loaded["base"]
    start_year = base_year + 1
    # team plan: default FTE ramp, scaled down when the horizon revenue cannot carry it
    # (R&D ≤ rd_share_of_revenue_final × last-year revenue, never below rd_fte_min)
    pre = {"currency": cur, "start_year": start_year, "years": years,
           "revenue": {"customers_start": c0, "new_customers": new, "churn_annual": churn_a["base"],
                       "arpa_start": price_year["base"], "arpa_growth": arpa_growth},
           "costs": {"cogs_pct": 0.0, "rd": [0.0] * years, "sm": [0.0] * years, "ga": [0.0] * years, "capex": [0.0] * years},
           "tax_rate": 0.0, "cash_start": 0.0, "discount_rate": disc["base"]}
    rev_pre = [r["revenue"] for r in fin_build(pre)["base"]["rows"]]
    fte_def = (FD["rd_fte"] + [FD["rd_fte"][-1]] * years)[:years]
    fte_min = (FD.get("rd_fte_min", [2]) + [FD.get("rd_fte_min", [2])[-1]] * years)[:years]
    rd_share = I.bench_rng("finance_defaults", "rd_share_of_revenue_final", "cost.rd_share_final", "R&D as share of last-year revenue (cap)", "fraction")
    cap_fte = rd_share["base"] * rev_pre[-1] / dev_loaded if dev_loaded else fte_def[-1]
    scale = min(1.0, cap_fte / fte_def[-1]) if fte_def[-1] else 1.0
    fte = [max(m, round(f * scale, 1)) for f, m in zip(fte_def, fte_min)]
    I.added.append({"id": "auto_team_rd_fte", "key": "team.rd_fte", "label": "R&D team, FTE by year (scaled to the market)",
                    "value": fte[-1], "type": "estimate", "method": "derived", "confidence": "low", "unit": "FTE", "year": start_year + years - 1,
                    "formula": "FTE_y = max(min_y, default_y × min(1, R&D share × revenue_last / (default_last × loaded developer cost)))",
                    "inputs": [rd_share["id"], dev["id"]], "range": {"low": fte[0], "high": fte[-1]},
                    "note": "default ramp " + "/".join(str(x) for x in fte_def) + "; scaled " + "/".join(str(x) for x in fte)})
    rd = [f * dev_loaded for f in fte]
    ga_fte = (FD["ga_fixed_fte"] + [FD["ga_fixed_fte"][-1]] * years)[:years]
    ga_fixed = [max(0.5, g * scale) * dev_loaded * 0.8 for g in ga_fte]
    fin = {"currency": cur, "start_year": start_year, "years": years,
           "revenue": {"customers_start": c0, "new_customers": new, "churn_annual": churn_a["base"],
                       "arpa_start": price_year["base"], "arpa_growth": arpa_growth},
           "costs": {"cogs_pct": 1 - ue["gross_margin"]["base"], "rd": rd, "sm": [n * cac for n in new], "ga": ga_fixed,
                     "capex": [0.0] * years},
           "working_capital_pct": FD["working_capital_pct"], "tax_rate": float(A.get("tax_rate", 0.2)),
           "cash_start": float(A.get("cash_start", 0.0)), "funding": [], "discount_rate": disc["base"],
           "terminal": {"method": "exit_multiple", "multiple": exit_mult["base"], "metric": "revenue"},
           "scenarios": {"bear": {"new_customers_mult": 0.6, "arpa_mult": 0.9, "churn_annual": churn_a["high"], "exit_multiple": exit_mult["low"]},
                         "base": {},
                         "bull": {"new_customers_mult": 1.3, "arpa_mult": 1.1, "churn_annual": churn_a["low"], "exit_multiple": exit_mult["high"]}},
           "sensitivity": {"output": "npv", "x": {"param": "arpa_mult", "values": [0.8, 0.9, 1.0, 1.1, 1.2]},
                           "y": {"param": "new_customers_mult", "values": [0.6, 0.8, 1.0, 1.2, 1.4]}}}
    # GA: add a revenue share on top of the fixed team via a first pass
    r0 = fin_build(fin)
    revs = [r["revenue"] for r in r0["base"]["rows"]]
    fin["costs"]["ga"] = [g + FD["ga_share_of_revenue"] * rv for g, rv in zip(ga_fixed, revs)]
    fin["costs"]["capex"] = [FD["capex_share_of_revenue"] * rv for rv in revs]
    r1 = fin_build(fin)
    min_cash = min(r["cash_end"] for r in r1["base"]["rows"])
    ask = _round_price(max(-min_cash, 0) * (1 + FD["cash_buffer"])) if min_cash < 0 else 0.0
    exit_ev = revs[-1] * exit_mult["base"]
    post = exit_ev / (1 + disc["base"]) ** (years - 1) if exit_ev > 0 else ask * 4
    post = max(post, ask * 2.5)
    if ask > 0:
        fin["funding"] = [{"year": start_year, "amount": ask}]
        fin["investor"] = {"investment": ask, "pre_money": post - ask, "entry_year": start_year,
                           "exit_year": start_year + years - 1, "exit_multiple": exit_mult["base"],
                           "exit_metric": "revenue", "later_dilution": FD["later_dilution"]}
    vc_fact = {"id": "auto_valuation_post_money_vc", "key": "valuation.post_money", "label": "post-money by the venture-capital method",
               "value": post, "type": "estimate", "method": "derived", "confidence": "low", "unit": cur, "year": start_year,
               "formula": "post-money = revenue(exit) × exit multiple / (1 + discount rate)^(years − 1), at least 2.5 × ask",
               "inputs": [exit_mult["id"], disc["id"]]}
    I.added.append(vc_fact)
    ask_fact = {"id": "auto_funding_ask", "key": "funding.ask", "label": "funding ask = −(minimum cash without funding) × (1 + buffer)",
                "value": ask, "type": "estimate", "method": "derived", "confidence": "medium", "unit": cur, "year": start_year,
                "formula": "−min(cash) × 1.2, rounded", "inputs": []}
    I.added.append(ask_fact)
    rev_last = revs[-1]
    ev = E.comparables(rev_last, mult, private_discount=pdisc)
    if mdisc:
        ev = E.expr("rev * m * (1 - d) * (1 - x)", {"rev": rev_last, "m": mult, "d": pdisc, "x": mdisc}, method="derived")
    ev_r = I.add_estimate(ev, "valuation.ev_comparables", "EV by comparables on last-year revenue", cur)

    be = r1["base"]["summary"].get("ebitda_breakeven_year")
    return {"breakeven_year": be, "I": I, "cur": cur, "base_year": base_year, "horizon": horizon, "years": years, "segments": seg_rows,
            "bu": bu, "tam_bu": tam_bu, "tam_td": tam_td, "tam_vt": tam_vt, "tri": tri, "units_total": units_total,
            "serviceable": serviceable, "obtainable": obtainable, "growth": growth, "pen0": pen0, "pen1": pen1, "cagr": cagr,
            "price": price, "price_year": price_year, "price_basis_key": price_basis_key, "hours": hours, "hourly_cost": hourly_cost,
            "ue": ue, "ue_seg": bseg, "churn_a": churn_a, "roi": roi, "tco": tco, "smb_v": smb_v, "deal_units": deal_units, "ramp": ramp,
            "manual_hours": manual_hours, "saving_month": saving_month, "annual_value": annual_value,
            "rf": rf, "disc": disc, "mult": mult, "pdisc": pdisc, "mdisc": mdisc, "exit_mult": exit_mult, "ev": ev_r,
            "ask": ask, "post": post, "fin": fin, "td_total": td_total, "it_share": it_share, "cat_share": cat_share,
            "som_h": som_h, "target_customers": target_cust, "team_fte": fte, "team_scale": scale,
             "rev_last": revs[-1] if revs else None}


# ----------------------------------------------------------------------------- facts, tables, charts
def _fmt_val(v, unit, cur, lang):
    if v is None:
        return "—"
    u = (unit or "").lower()
    if u in ("fraction", "share", "rate", "fraction per year"):
        return fmt_pct(v, 1, lang)
    if u in ("x",):
        return fmt_multiple(v, 2, lang)
    if unit and len(unit) == 3 and unit.isupper():
        return fmt_money(v, unit, lang, "auto", 1 if abs(v) >= 1e4 else 0)
    return fmt_number(v, 0 if abs(v) >= 100 else 2, lang)


def build_auto_facts(C: dict, brief: dict, pattern: dict, profile_doc: dict, mdef: dict, locale: str, full_ledger: dict) -> dict:
    lang = locale
    sl = lang if lang in STORY_LOCALES else "en"
    T = (lambda ru, en: ru if sl == "ru" else en)
    cur = C["cur"]
    ue = C["ue"]
    I = C["I"]
    money0 = lambda v: fmt_money(v, cur, lang, "auto", 0)
    money1 = lambda v: fmt_money(v, cur, lang, "auto", 1)
    pct = lambda v: fmt_pct(v, 0, lang)
    x1 = lambda v: fmt_multiple(v, 1, lang)
    rb = lambda r, f: [f(r["low"]), f(r["base"]), f(r["high"])]
    bench_lbl = T("эталонный диапазон SaaS (эмпирическое правило)", "SaaS benchmark range (rule of thumb)")
    ue_rows = [
        [T("Цена в месяц (ARPA)", "Price per month (ARPA)")] + rb(C["price"], money0) + [T("оценка по ценности" if C["price_basis_key"] == "value" else "реестр", "value-based estimate" if C["price_basis_key"] == "value" else "ledger")],
        [T("Валовая маржа", "Gross margin")] + rb(ue["gross_margin"], pct) + [bench_lbl],
        [T("Отток в месяц", "Monthly churn")] + [fmt_pct(ue["monthly_churn"][k], 1, lang) for k in ("low", "base", "high")] + [bench_lbl],
        ["CAC"] + rb(ue["cac"], money0) + [T("срок окупаемости × ARPA × маржа", "payback months × ARPA × margin")],
        ["LTV"] + rb(ue["ltv"], money0) + [T("ARPA × маржа / отток", "ARPA × margin / churn")],
        ["LTV/CAC"] + rb(ue["ltv_cac"], x1) + [T("1 / (отток × срок окупаемости)", "1 / (churn × payback months)")],
        [T("Окупаемость CAC, мес.", "CAC payback, months")] + [fmt_number(ue["cac_payback_months"][k], 0, lang) for k in ("low", "base", "high")] + [bench_lbl],
        ["NRR"] + [pct(ue["nrr"][k]) for k in ("low", "base", "high")] + [bench_lbl]]
    mm = [[T("Снизу вверх", "Bottom-up"), T("Σ единиц × цена в год", "Σ units × annual price")] + rb(C["tam_bu"], money1)]
    if C["tam_td"]:
        mm.append([T("Сверху вниз", "Top-down"), T("оборот отраслей × доля ИТ × доля категории", "industry sales × IT share × category share")] + rb(C["tam_td"], money1))
    mm.append([T("По ценности", "Value-based"), T("единиц × годовая ценность × доля захвата", "units × annual value × capture share")] + rb(C["tam_vt"], money1))
    mm.append([T("Триангуляция", "Triangulated"), T("среднее геометрическое; разброс ", "geometric mean; spread ") + x1(C["tri"]["ratio"])] + rb(C["tri"], money1))
    roi, tco = C["roi"], C["tco"]
    du = C["deal_units"]["base"]
    tco_rows = [[T("Подписка за 3 года", "Subscription, 3 years"), money1(0), money1(C["price_year"]["base"] * du * 3)],
                [T("Внедрение и обучение", "Implementation and training"), money1(0), money1(tco["one_off"])],
                [T("Время сотрудников на задачу", "Staff time on the task"), money1(tco["alternative_tco"]), money1(tco["inputs"]["internal_staff_per_year"] * 3)],
                [T("Итого TCO", "Total TCO"), money1(tco["alternative_tco"]), money1(tco["value"])]]
    risks = [[T("Пользователи не внедряют продукт", "Users do not adopt the product"), T("доля активных пользователей < 70 % через 30 дней", "active users < 70% after 30 days"), T("онбординг, напоминания, обучение ключевых пользователей", "onboarding, nudges, champion training")],
             [T("Отток выше эталона", "Churn above benchmark"), T("отток > {0} в месяц", "churn > {0} a month").format(fmt_pct(ue["monthly_churn"]["high"], 1, lang)), T("годовые тарифы, интеграции с системами клиента", "annual plans, integrations with the customer's systems")],
             [T("CAC выше модели", "CAC above the model"), T("CAC > {0}", "CAC > {0}").format(money0(ue["cac"]["high"])), T("партнёрский канал, реферальная программа", "partner channel, referral programme")],
             [T("Ценовое давление конкурентов", "Price pressure from competitors"), T("конверсия пробного периода < 10 %", "trial conversion < 10%"), T("ценность в деньгах на экране продукта", "show value in money inside the product")],
             [T("Дорогие деньги", "Expensive capital"), T("безрисковая ставка > {0}", "risk-free rate > {0}").format(fmt_pct(C["rf"]["base"], 1, lang)), T("путь к безубыточности без следующего раунда", "a path to break-even without the next round")]]
    rows_led, ledger_table = [], RL.export(full_ledger, cur, C["base_year"])["table"]
    tlab = {"sourced": T("источник", "sourced"), "estimate": T("оценка", "estimate")}
    clab = {"high": T("высокая", "high"), "medium": T("средняя", "medium"), "low": T("низкая", "low")}
    for r in ledger_table:
        rows_led.append([str(r["label"])[:70], _fmt_val(r["value"], r.get("unit"), cur, lang), tlab[r["type"]], clab[r["confidence"]], str(r["basis"] or "")[:110]])
    val_rows = [[T("Аналоги (EV/Revenue)", "Comparables (EV/Revenue)")] + rb(C["ev"], money1) + [T("выручка {0} × мультипликатор × (1 − дисконт)", "revenue {0} × multiple × (1 − discount)").format(C["fin"]["start_year"] + C["years"] - 1)],
                [T("Мультипликатор выхода", "Exit multiple")] + rb(C["exit_mult"], lambda v: fmt_multiple(v, 1, lang)) + [T("сопоставимые компании после дисконта", "listed peers after discount")],
                [T("Ставка дисконтирования", "Discount rate")] + rb(C["disc"], pct) + [T("безрисковая + премия ранней стадии", "risk-free + early-stage premium")]]
    S = Inputs  # noqa: F841
    sources = RL.to_sources(full_ledger)
    # source labels by kind
    def names(prefixes):
        out = []
        for k, f in I.used.items():
            if f.get("type") == "sourced" and any(k.startswith(p) for p in prefixes):
                nm = next((s["org"] for s in sources if s["url"] == f.get("source_url")), None)
                lbl = f"{nm} ({f.get('year')})" if nm else None
                if lbl and lbl not in out:
                    out.append(lbl)
        return out
    sbk = {"market": names(["count.", "industry.revenue", "share.size_band"]), "growth": names(["industry.growth", "macro.inflation"]),
           "customer": names(["wage."]), "pricing": names(["pricing.", "wage."]), "ue": [], "problem": names(["count.", "wage."]),
           "valuation": names(["valuation.", "macro.risk_free"])}
    n_est = sum(1 for f in full_ledger["facts"] if f["type"] == "estimate")
    n_all = len(full_ledger["facts"])
    auto = {
        "name": brief.get("name") or profile_doc["profile"]["name"],
        "price_month": C["price"]["base"], "price_year": C["price_year"]["base"], "price_year_discounted": C["price"]["base"] * 10,
        "price_basis": {"value": T("оценка по ценности: экономия × доля захвата", "value-based estimate: saving × capture share"),
                        "ledger": T("цена из реестра", "price from the ledger"), "sourced": T("цена из источника", "sourced price")}[C["price_basis_key"]],
        "ask": C["ask"],
        "breakeven_phrase": (T("EBITDA положительна в {0}", "EBITDA positive in {0}").format(C["breakeven_year"]) if C["breakeven_year"]
                             else T("EBITDA выходит в плюс после {0}", "EBITDA turns positive after {0}").format(C["fin"]["start_year"] + C["years"] - 1)),
        "market": {"tam_bu": C["tam_bu"]["base"], "tam_td": (C["tam_td"] or {}).get("base"), "tam_vt": C["tam_vt"]["base"],
                   "tam_tri": C["tri"]["base"], "tam_ratio": C["tri"]["ratio"],
                   "verdict": {"consistent": T("согласованы", "consistent"), "acceptable": T("допустимо", "acceptable")}.get(C["tri"]["verdict"], T("требует проверки", "needs review")),
                   "units_total": C["units_total"], "industry_growth": C["growth"]["base"], "pen_start": C["pen0"]["base"], "pen_end": C["pen1"]["base"],
                   "cagr_low": C["cagr"]["low"], "cagr_base": C["cagr"]["base"], "cagr_high": C["cagr"]["high"],
                   "serviceable": C["serviceable"]["base"], "obtainable": C["obtainable"]["base"]},
        "ue": {"cac": ue["cac"]["base"], "cac_low": ue["cac"]["low"], "cac_high": ue["cac"]["high"], "ltv": ue["ltv"]["base"],
               "ltv_cac": ue["ltv_cac"]["base"], "ltv_cac_low": ue["ltv_cac"]["low"], "ltv_cac_high": ue["ltv_cac"]["high"],
               "payback": ue["cac_payback_months"]["base"], "gm": ue["gross_margin"]["base"], "gm_low": ue["gross_margin"]["low"],
               "gm_high": ue["gross_margin"]["high"], "churn_m": ue["monthly_churn"]["base"], "annual_churn": C["churn_a"]["base"],
               "nrr": ue["nrr"]["base"], "segment": C["ue_seg"]},
        "val": {"ev_low": C["ev"]["low"], "ev_base": C["ev"]["base"], "ev_high": C["ev"]["high"], "peer_multiple": C["mult"]["base"],
                "exit_multiple": C["exit_mult"]["base"], "discount_rate": C["disc"]["base"], "risk_free": C["rf"]["base"], "post_money_vc": C["post"]},
        "cust": {"hours_saved_month": C["hours"]["base"], "hourly_cost": C["hourly_cost"]["base"], "saving_month": C["saving_month"],
                 "value_ratio": C["smb_v"]["value"], "net_month": C["smb_v"]["net_monthly_gain"],
                 "price_share_of_value": C["price"]["base"] / C["saving_month"] if C["saving_month"] else None,
                 "manual_cost_month": C["manual_hours"] * C["hourly_cost"]["base"],
                 "roi": roi["value"], "payback_months": roi["payback_months"], "deal_units": du, "ramp": C["ramp"]["base"],
                 "benefit_year_deal": roi["inputs"]["annual_benefit"], "cost_year_deal": roi["inputs"]["annual_cost"],
                 "tco": tco["value"], "tco_deal": tco["value"], "alt_tco_deal": tco["alternative_tco"], "saving_3y_deal": tco["saving"],
                 "saving_3y": tco["saving"]},
        "public": {"customers": C["target_customers"], "hours_year": C["target_customers"] * C["hours"]["base"] * 12,
                   "value_year": C["target_customers"] * C["hours"]["base"] * 12 * C["hourly_cost"]["base"]},
        "ledger": {"n": n_all, "sourced": n_all - n_est, "estimates": n_est, "estimate_share": n_est / n_all if n_all else 0},
        "tables": {"ue": ue_rows, "market_methods": mm, "tco": tco_rows, "risks": risks, "ledger": rows_led, "valuation": val_rows},
        "charts": {
            "cust_roi": {"type": "column", "categories": [T("Год 1", "Year 1"), T("Год 2", "Year 2"), T("Год 3", "Year 3")],
                         "scale": get_locale(lang)["chart_scale_mn"], "number_format": "#,##0.0",
                         "series": [{"name": T("Выгода", "Benefit"), "values": [roi["inputs"]["annual_benefit"] * (C["ramp"]["base"] if i == 0 else 1) for i in range(3)]},
                                    {"name": T("Затраты", "Cost"), "values": [roi["inputs"]["annual_cost"] + (roi["inputs"]["one_off_cost"] if i == 0 else 0) for i in range(3)]}]},
            "smb_value": {"type": "column", "categories": [T("Цена в месяц", "Price per month"), T("Экономия в месяц", "Saving per month")],
                          "number_format": "#,##0", "series": [{"name": cur, "values": [C["price"]["base"], C["saving_month"]]}], "highlight_index": 1}},
        "sources_by_kind": sbk,
    }
    auto["verdicts"] = _verdicts(C, auto, sl, lang)
    return auto


def _verdicts(C: dict, auto: dict, sl: str, lang: str) -> dict:
    """One plain-language verdict per metric slide: what was counted, the result, and whether it is
    good or bad for the product. Keyed by slide id; pitch_story attaches it to each slide."""
    def g(ru, en):
        return ru if sl == "ru" else en
    money1 = lambda v: fmt_money(v, C["cur"], lang, "auto", 1)
    pct = lambda v: fmt_pct(v, 0, lang)
    x1 = lambda v: fmt_multiple(v, 1, lang)
    num0 = lambda v: fmt_number(v, 0, lang)

    cagr = C["cagr"]["base"]
    cagr_q = g("хорошо" if cagr >= 0.10 else ("средне" if cagr >= 0.05 else "слабо"),
               "good" if cagr >= 0.10 else ("moderate" if cagr >= 0.05 else "weak"))
    ltv = C["ue"]["ltv_cac"]["base"]
    ltv_q = g("хорошо" if ltv >= 3 else ("средне" if ltv >= 1.5 else "слабо"),
              "good" if ltv >= 3 else ("moderate" if ltv >= 1.5 else "weak"))
    pay = C["ue"]["cac_payback_months"]["base"]
    pay_q = g("хорошо" if pay <= 18 else ("приемлемо" if pay <= 24 else "слабо"),
              "good" if pay <= 18 else ("acceptable" if pay <= 24 else "weak"))
    gm = C["ue"]["gross_margin"]["base"]
    gm_q = g("хорошо" if gm >= 0.70 else "средне", "good" if gm >= 0.70 else "moderate")
    roi = C["roi"]["value"]
    roi_q = g("хорошо" if roi >= 1.0 else "средне", "good" if roi >= 1.0 else "moderate")
    tri_q = g({"consistent": "согласованы", "acceptable": "допустимо"}.get(C["tri"]["verdict"], "требует проверки"),
              {"consistent": "consistent", "acceptable": "acceptable"}.get(C["tri"]["verdict"], "needs review"))
    sam = C["bu"]["totals"]["SAM"]["base"]

    v = {
        "hook": g(
            f"Считали доступный рынок (SAM) снизу вверх и юнит-экономику по эталонам SaaS. SAM {money1(sam)}, CAGR {pct(cagr)}, LTV/CAC {x1(ltv)} — LTV/CAC это {ltv_q} (эталон ≥ 3×).",
            f"Counted the serviceable market (SAM) bottom-up and unit economics from SaaS benchmarks. SAM {money1(sam)}, CAGR {pct(cagr)}, LTV/CAC {x1(ltv)} — LTV/CAC is {ltv_q} (benchmark ≥ 3×)."),
        "customer_hook": g(
            f"Считали ROI клиента от сэкономленных часов. ROI за 3 года {pct(roi)}, окупаемость {num0(C['roi']['payback_months'])} мес. — это {roi_q} для заказчика.",
            f"Counted the customer ROI from saved hours. 3-year ROI {pct(roi)}, payback {num0(C['roi']['payback_months'])} months — {roi_q} for the buyer."),
        "market_sizing": g(
            f"Считали рынок тремя методами и свели их. Расхождение {x1(C['tri']['ratio'])} — методы {tri_q}.",
            f"Sized the market three ways and triangulated them. Spread {x1(C['tri']['ratio'])} — methods are {tri_q}."),
        "market_growth": g(
            f"Считали CAGR рынка из роста отраслей и проникновения. {pct(cagr)} в год — это {cagr_q} для растущего рынка.",
            f"Estimated market CAGR from industry growth and penetration. {pct(cagr)} a year — {cagr_q} for a growing market."),
        "unit_economics": g(
            f"Считали юнит-экономику по эталонным диапазонам. LTV/CAC {x1(ltv)} ({ltv_q}), окупаемость CAC {num0(pay)} мес. ({pay_q}), валовая маржа {pct(gm)} ({gm_q}).",
            f"Built unit economics from benchmark ranges. LTV/CAC {x1(ltv)} ({ltv_q}), CAC payback {num0(pay)} months ({pay_q}), gross margin {pct(gm)} ({gm_q})."),
        "business_model": g(
            f"Считали цену и валовую маржу. Валовая маржа {pct(gm)} — это {gm_q} для SaaS.",
            f"Counted the price and gross margin. Gross margin {pct(gm)} is {gm_q} for SaaS."),
        "customer_roi": g(
            f"Считали выгоду клиента от сэкономленных часов. ROI {pct(roi)}, окупаемость {num0(C['roi']['payback_months'])} мес. — {roi_q}.",
            f"Counted the customer's benefit from saved hours. ROI {pct(roi)}, payback {num0(C['roi']['payback_months'])} months — {roi_q}."),
        "financials": g(
            f"Считали путь клиентов к SOM и P&L. Выручка к {C['fin']['start_year'] + C['years'] - 1} г. — {money1(C.get('rev_last') or 0)}; точка безубыточности из модели.",
            f"Modelled the customer path to SOM and the P&L. Revenue by {C['fin']['start_year'] + C['years'] - 1} — {money1(C.get('rev_last') or 0)}; break-even from the model."),
        "public_effect": g(
            f"Считали общественный эффект как высвобожденные часы × стоимость часа при выходе на SOM.",
            f"Counted the public effect as freed hours × hourly cost at SOM."),
    }
    return {k: s for k, s in v.items() if s}


def to_confirm_list(C: dict, profile_doc: dict, lang: str) -> list[str]:
    T = (lambda ru, en: ru if lang == "ru" else en)
    out = []
    if C["price_basis_key"] == "value":
        out.append(T("Фактическая цена и скидки (сейчас — оценка по ценности)", "Actual price and discounts (now a value-based estimate)"))
    if C["hours"]["type"] != "sourced":
        out.append(T("Замер экономии времени на 3–5 клиентах", "Time-saving baseline measured at 3–5 customers"))
    out.append(T("Когорты оттока и CAC по каналам после 2 кварталов", "Churn cohorts and CAC by channel after two quarters"))
    out.append(T("Команда, план найма и стоимость разработки", "Team, hiring plan and development cost"))
    out.append(T("Денежные средства и налоговый режим компании", "Cash on hand and the company's tax regime"))
    return out


# ----------------------------------------------------------------------------- orchestration
def run(brief_path: str, pattern: str | None = None, themes: list[str] | None = None, locale: str | None = None,
        out_dir: str | None = None, plan_only: bool = False, render: bool = False) -> dict:
    bdir = os.path.dirname(os.path.abspath(brief_path))
    brief = load_json(brief_path)
    P = lambda x: x if os.path.isabs(x) else os.path.join(bdir, x)
    mk = brief.get("market") or "en"
    lang = norm_locale(locale or brief.get("locale") or LANG_OF.get(mk, "en"))
    base_year = int(brief.get("base_year", _dt.date.today().year))
    pat = select_pattern(pattern or brief.get("pattern"), brief.get("audience"))
    out = P(out_dir or brief.get("out_dir", f"output_{pat['id']}_{lang}"))
    os.makedirs(out, exist_ok=True)
    text = brief.get(f"text_{lang}") or brief.get("text", "")
    prof = make_profile(text, brief.get("name"), mk, brief.get("profile_overrides"))
    mdef = define(prof, mk, base_year)
    if brief.get("segments"):
        mdef["segments"] = brief["segments"]
    dump_json(prof, os.path.join(out, "profile.json"))
    dump_json(mdef, os.path.join(out, "market_definition.json"))
    ledger_path = P(brief["ledger"]) if brief.get("ledger") else None
    ledger = load_json(ledger_path) if ledger_path and os.path.exists(ledger_path) else RL.new_ledger(CURRENCY_OF.get(mk, "USD"), base_year)
    need = [f"count.{s['id']}" for s in mdef["segments"]] + ["industry.revenue.<ISIC>", "industry.growth", "wage.hourly|wage.monthly",
                                                            "macro.inflation", "macro.risk_free", "valuation.peer_ev_revenue"]
    plan = {"pattern": pat["id"], "pattern_selected_by": pat["selected_by"], "ledger_keys_needed": need,
            "research_plan": mdef["research_plan"], "queries": mdef["queries"], "official_sources": mdef["official_sources"],
            "segments": mdef["segments"]}
    dump_json(plan, os.path.join(out, "research_plan.json"))
    if plan_only:
        return {"plan": os.path.relpath(os.path.join(out, "research_plan.json"), bdir), "pattern": pat["id"]}

    C = compute(brief, ledger, pat, prof, mdef, base_year)
    I = C["I"]
    full = copy.deepcopy(ledger)
    known = {f["id"] for f in full["facts"]}
    for f in I.added:
        if f["id"] not in known:
            f = {k: v for k, v in f.items() if v is not None or k in ("value",)}
            full["facts"].append(f)
            known.add(f["id"])
    val = RL.validate(full)
    dump_json(full, os.path.join(out, "ledger_full.json"))
    auto = build_auto_facts(C, brief, pat, prof, mdef, lang, full)
    sl = lang if lang in STORY_LOCALES else "en"
    tc = to_confirm_list(C, prof, sl)
    auto["to_confirm"] = tc

    # ---------------- inputs for the standard pipeline
    seg_list = C["segments"]
    market_input = {"currency": C["cur"], "base_year": base_year, "horizon_year": base_year + C["years"], "primary": "bottom_up",
                    "bottom_up": {"segments": [{"name": s["name"], "units": s["units"]["base"], "arpa": C["price_year"]["base"],
                                                "sam_share": C["serviceable"]["base"], "som_share": C["obtainable"]["base"],
                                                "source": "research ledger"} for s in seg_list]},
                    "growth": {"cagr": {"bear": C["cagr"]["low"], "base": C["cagr"]["base"], "bull": C["cagr"]["high"]}},
                    "som_ramp": "s_curve", "som_share_multiplier": {"bear": 0.6, "base": 1.0, "bull": 1.4}}
    if C["td_total"]:
        market_input["top_down"] = {"total_market": C["td_total"]["base"], "total_market_label": "industry sales (target size band)",
                                    "source": "research ledger",
                                    "filters": [{"name": "IT spend share", "share": C["it_share"]["base"]},
                                                {"name": "category share of IT spend", "share": C["cat_share"]["base"], "level": "TAM"},
                                                {"name": "serviceable share", "share": C["serviceable"]["base"], "level": "SAM"},
                                                {"name": "obtainable share", "share": C["obtainable"]["base"], "level": "SOM"}]}
    stage = prof["profile"].get("stage") or "prototype"
    lc = C["ue"]["ltv_cac"]["base"]
    est_conf = "B" if any(v.get("type") == "sourced" for k, v in I.used.items() if k.startswith("count.")) else "C"
    scores = {"market": {"score": 4.0 if C["cagr"]["base"] >= 0.15 else 3.5 if C["cagr"]["base"] >= 0.1 else 3.0, "evidence": est_conf, "note": "auto: SAM and CAGR from the ledger"},
              "problem": {"score": 4.0 if C["smb_v"]["value"] >= 3 else 3.0, "evidence": "C", "note": "auto: value ratio"},
              "trl": {"score": {"idea": 1.5, "prototype": 2.5, "pilot": 3.5, "growth": 4.5}.get(stage, 2.5), "evidence": "C", "note": "auto: stage"},
              "moat": {"score": 2.5, "evidence": "C", "note": "auto: to confirm"},
              "team": {"score": 2.5, "evidence": "C", "note": "auto: to confirm"},
              "traction": {"score": {"idea": 0.5, "prototype": 1.0, "pilot": 2.0, "growth": 3.5}.get(stage, 1.0), "evidence": "C", "note": "auto: stage"},
              "unit_economics": {"score": 3.5 if lc >= 3 else 2.5 if lc >= 1.5 else 1.5, "evidence": "C", "note": "auto: benchmark LTV/CAC"},
              "gtm": {"score": 2.5, "evidence": "C", "note": "auto"}, "regulatory": {"score": 3.0, "evidence": "C", "note": "auto"},
              "scalability": {"score": 3.5, "evidence": "C", "note": "auto"}, "risk": {"score": 3.0, "evidence": "C", "note": "auto"}}
    scoring_input = {"stage": stage if stage in ("idea", "prototype", "pilot", "growth") else "prototype",
                     "audience": pat["scoring"]["audience"], "locale": lang, "market": mk, "scores": scores,
                     "weights_override": pat["scoring"].get("weights_override")}
    loc = get_locale(lang)
    today = _dt.date.today()
    date = (MONTHS_RU[today.month - 1].capitalize() + f" {today.year}") if sl == "ru" else today.strftime("%B %Y")
    fiction = brief.get("fiction_note") or (("ВЫМЫШЛЕННЫЙ ПРОДУКТ. Рыночные данные — реальные, со ссылками; данные о продукте, цене и команде — оценки."
                                             if sl == "ru" else "FICTIONAL PRODUCT. Market data are real and linked; product, price and team figures are estimates.")
                                            if brief.get("fictional") else "")
    wm = None
    if I.offline:
        wm = "ЧЕРНОВИК БЕЗ ИССЛЕДОВАНИЯ — масштаб условный" if sl == "ru" else "OFFLINE DRAFT — run the research loop"
    elif brief.get("fictional"):
        wm = "ВЫМЫШЛЕННЫЙ ПРОДУКТ · реальные данные рынка" if sl == "ru" else "FICTIONAL PRODUCT · real market data"
    st = brief.get(f"story_{lang}") or brief.get("story") or {}
    pf = prof["profile"]
    cat_label = mdef["definition"]["category_label"]
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 10]
    tax_seg = {"smb": T2(sl, "малый бизнес", "small businesses"), "mid_market": T2(sl, "средние компании и сети", "mid-size companies and chains"),
               "enterprise": T2(sl, "крупные компании", "large companies"), "consumer": T2(sl, "потребители", "consumers")}
    ctx = {"name": auto["name"], "tagline": st.get("tagline") or (pf.get("one_liner") or "")[:80],
           "features": st.get("features") or [s[:110] for s in sents[1:5]] or [pf.get("one_liner", "")],
           "today": st.get("today") or [T2(sl, "Вручную: ", "Manual: ") + d for d in pf.get("value_drivers", [])][:4],
           "alternatives": st.get("alternatives") or [T2(sl, "Таблицы и мессенджеры", "Spreadsheets and messengers"), T2(sl, "Бумага и ручной труд", "Paper and manual work"), T2(sl, "Корпоративные системы", "Enterprise suites")],
           "drivers": st.get("drivers") or pf.get("value_drivers", []),
           "country_label": COUNTRY.get(mk, {}).get(sl) or COUNTRY.get(mk, {}).get("en", mk), "date": brief.get("date") or date,
           "author": brief.get("author", "PitchComet"), "contact": brief.get("contact", ""), "currency": C["cur"],
           "theme": (themes or brief.get("themes") or [pat.get("theme", "light")])[0], "report_theme": pat.get("report_theme", "light"),
           "watermark": wm, "fiction_note": fiction, "category": pf.get("category"), "category_label": cat_label,
           "buyer": ", ".join(tax_seg.get(s, s) for s in pf.get("buyer_segment") or []),
           "pricing_model": ", ".join(pf.get("pricing_model") or []), "deployment": ", ".join(pf.get("deployment") or []),
           "unit": pf.get("unit") or "company", "to_confirm": tc, "sources": RL.to_sources(full),
           "sources_by_kind": auto["sources_by_kind"],
            "verdicts": auto.get("verdicts", {}),
           "market_sentence": st.get("market_sentence") or (T2(sl, "Рынок: ", "Market: ") + mdef["definition"]["sentence_en"]),
           "icp_text": st.get("icp") or ", ".join(mdef["icp"]["industries"]) + "; " + "; ".join(mdef["icp"]["pains"][:3]),
           "kicker": brief.get("kicker", "PitchComet")}
    deck, report = build_specs(ctx, pat, lang)
    for name, obj in (("market_input.json", market_input), ("finance_input.json", C["fin"]), ("scoring_input.json", scoring_input),
                      ("deck_spec.json", deck), ("report_spec.json", report), ("auto_facts.json", {"auto": auto})):
        dump_json(obj, os.path.join(out, name))
    th = themes or brief.get("themes") or [pat.get("theme", "light")]
    key_facts = ([{"path": "market.sam_base", "fmt": "money1"}, {"path": "market.cagr_base", "fmt": "pct0"},
                  {"path": "auto.ue.ltv_cac", "fmt": "x1"}] if pat["kind"] != "customer" else
                 [{"path": "auto.cust.payback_months", "fmt": "num0"}] + ([{"path": "auto.cust.roi", "fmt": "pct0"}] if pat["id"] == "corporate" else
                                                                         [{"path": "auto.price_month", "fmt": "money0"}]))
    project = {"name": auto["name"], "locale": lang, "currency": C["cur"], "market_profile": mk, "market": "market_input.json",
               "finance": "finance_input.json", "scoring": "scoring_input.json", "report_spec": "report_spec.json",
               "deck_spec": "deck_spec.json", "out_dir": ".", "themes": th, "render": render, "key_facts": key_facts,
               "extra_facts": ["auto_facts.json"], "pattern": pat["id"]}
    if brief.get("fictional"):
        project["_EXAMPLE_DATA"] = fiction
    pj = os.path.join(out, "project.json")
    dump_json(project, pj)
    from run_pipeline import run as run_pipe
    res = run_pipe(pj, lang, render)
    summary = {"pattern": pat["id"], "pattern_selected_by": pat["selected_by"], "locale": lang, "themes": th,
               "narrative_locale": sl, "offline": I.offline, "ledger_validation": val, "qa": res.get("qa"),
               "to_confirm": tc, "warnings": ([] if sl == lang else [f"narrative text in English for locale '{lang}' — localize the story"]) + I.exp.get("warnings", []),
               "key_numbers": {"tam_bu": C["tam_bu"]["base"], "tam_td": (C["tam_td"] or {}).get("base"), "tam_vt": C["tam_vt"]["base"],
                               "tam_ratio": C["tri"]["ratio"], "sam": C["bu"]["totals"]["SAM"]["base"], "som_horizon": C["som_h"],
                               "cagr": [C["cagr"]["low"], C["cagr"]["base"], C["cagr"]["high"]], "price_month": C["price"]["base"],
                               "ltv_cac": [C["ue"]["ltv_cac"]["low"], C["ue"]["ltv_cac"]["base"], C["ue"]["ltv_cac"]["high"]],
                               "cac": C["ue"]["cac"]["base"], "payback_months": C["ue"]["cac_payback_months"]["base"],
                               "customer_roi": C["roi"]["value"], "customer_payback_months": C["roi"]["payback_months"],
                               "ask": C["ask"], "post_money": C["post"], "ev_comparables": [C["ev"]["low"], C["ev"]["base"], C["ev"]["high"]],
                               "discount_rate": C["disc"]["base"]}}
    dump_json(summary, os.path.join(out, "auto_summary.json"))
    return summary


def T2(lang, ru, en):
    return ru if lang == "ru" else en


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--pattern", help="large_investor | small_investor | corporate | smb | government | auto")
    ap.add_argument("--theme", action="append", help="theme name (repeatable): light, dark, comet, editorial, corporate, warm, academic_light")
    ap.add_argument("--locale", "-l", choices=["ru", "en", "zh", "vi", "id", "ms"])
    ap.add_argument("--out", "-o")
    ap.add_argument("--plan-only", action="store_true", help="write research_plan.json (queries, ledger keys) and stop")
    ap.add_argument("--render", action="store_true", help="render PNG previews with LibreOffice")
    ap.add_argument("--no-render", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    print(dump_json(run(a.brief, a.pattern, a.theme, a.locale, a.out, a.plan_only, a.render and not a.no_render)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
