#!/usr/bin/env python3
"""run_pipeline.py — end-to-end: market sizing → financial model → scoring → facts.json →
report.docx + deck.pptx (light & dark) → QA → optional render.

project.json (paths relative to the project file):
{"name": "...", "locale": "ru"|"en"|"zh"|"vi"|"id"|"ms", "currency": "RUB"|"USD"|"CNY"|"VND"|"IDR"|"MYR", "market_profile": "ru"|"en"|"zh"|"vn"|"id"|"my",
 "market": "market_input.json", "finance": "finance_input.json", "scoring": "scoring_input.json",
 "report_spec": "report_spec.json", "deck_spec": "deck_spec.json", "out_dir": "output",
 "themes": ["light", "dark"], "render": true, "key_facts": [{"path": "market.sam_base", "fmt": "money_bn"}]}

facts.json is the single source of truth: every number in the report and the deck is a
{{placeholder}} resolved from it, so the two documents cannot drift apart.

CLI: python run_pipeline.py --project ../examples/example_en/project.json [--locale en] [--no-render]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_docx import build_docx  # noqa: E402
from build_pptx import build_pptx  # noqa: E402
from financial_model import build as fin_build  # noqa: E402
from fmt_utils import dump_json, fmt_money, fmt_multiple, fmt_number, fmt_pct, load_json  # noqa: E402
from locales import norm_market, get_locale, locale_of  # noqa: E402
from market_sizing import size_market  # noqa: E402
from qa_check import run_qa  # noqa: E402
from scoring import load_model, score  # noqa: E402

def SCN_COLORS(keys):
    """Palette index per scenario: base = accent (0), bear = muted (1), bull = third colour (2)."""
    m = {"base": 0, "bear": 1, "bull": 2}
    return [m.get(k, i + 3) for i, k in enumerate(keys)]


def units(lang: str, cur: str) -> dict:
    """Axis/caption units matching the chart scales of the locale."""
    loc = get_locale(lang)
    if lang == "zh":
        w = {"CNY": "元", "USD": "美元", "RUB": "卢布"}.get(cur, cur)
        return {"mn": f"万{w}", "bn": f"亿{w}"}
    if lang == "ru":
        sign = {"RUB": "₽", "USD": "$", "CNY": "¥"}.get(cur, cur)
        return {"mn": f"млн {sign}", "bn": f"млрд {sign}"}
    if cur == loc.get("currency") or (lang == "en" and cur == "USD"):
        return {"mn": loc["unit_mn"], "bn": loc["unit_bn"]}
    return {"mn": f"{cur} M", "bn": f"{cur} B"}


def build_facts(project: dict, market: dict, fin: dict, sc: dict, sc_all: dict) -> dict:
    lang = locale_of(project)
    loc = get_locale(lang)
    cur = project.get("currency") or loc["currency"]
    Lb = loc["labels"]
    S = Lb["scn"]
    s_mn, s_bn = loc["chart_scale_mn"], loc["chart_scale_bn"]
    m = {"base_year": market["base_year"], "horizon_year": market["horizon_year"]}
    for lvl in ("TAM", "SAM", "SOM"):
        m[f"{lvl.lower()}_base"] = market["base"][lvl]
        if market.get("top_down"):
            m[f"{lvl.lower()}_td"] = market["top_down"][lvl]
        if market.get("bottom_up"):
            m[f"{lvl.lower()}_bu"] = market["bottom_up"][lvl]
    m["td_bu_ratio_tam"] = market["triangulation"].get("TAM_ratio")
    for k, v in market["projection"]["scenarios"].items():
        m[f"cagr_{k}"] = v["cagr"]
        m[f"tam_horizon_{k}"] = v["TAM_horizon"]
        m[f"sam_horizon_{k}"] = v["SAM_horizon"]
        m[f"som_horizon_{k}"] = v["SOM_horizon"]
        if "real_cagr" in v:
            m[f"real_cagr_{k}"] = v["real_cagr"]
    m["warnings"] = market["warnings"]

    base = fin["base"]
    s = base["summary"]
    last = base["rows"][-1]
    f = {"start_year": base["years"][0], "end_year": base["years"][-1],
         "revenue_first": s["revenue_first"], "revenue_last": s["revenue_last"], "revenue_cagr": s["revenue_cagr"],
         "ebitda_last": last["ebitda"], "ebitda_margin_last": last["ebitda_margin"], "gm_last": last["gross_margin"],
         "ltv_cac_last": last["ltv_cac"], "cac_payback_last": last["cac_payback_months"],
         "customers_last": last["customers_end"], "arr_last": last["arr_end"], "rule40_last": last["rule_of_40"],
         "burn_multiple_first": base["rows"][0]["burn_multiple"], "funding_total": s["cumulative_funding"],
         "min_cash": s["min_cash"], "tv_share": s["tv_share"], "discount_rate": s["discount_rate"],
         "revenue_to_som": s["revenue_last"] / m["som_horizon_base"] if m.get("som_horizon_base") else None,
         "post_money": (base.get("investor") or {}).get("post_money"),
         "ownership_entry": (base.get("investor") or {}).get("ownership_at_entry"),
         "ownership_exit": (base.get("investor") or {}).get("ownership_at_exit"),
         "warnings": base["warnings"]}
    after = Lb["after"] + ("" if lang == "zh" else " ")
    for k, v in fin["scenarios"].items():
        ss = v["summary"]
        f[f"npv_{k}"] = ss["npv"]
        f[f"moic_{k}"] = ss.get("moic")
        f[f"irr_{k}"] = ss.get("investor_irr")
        f[f"revenue_last_{k}"] = ss["revenue_last"]
        f[f"min_cash_{k}"] = ss["min_cash"]
        f[f"breakeven_{k}"] = str(ss["ebitda_breakeven_year"]) if ss["ebitda_breakeven_year"] else f"{after}{f['end_year']}"
    f["breakeven_year"] = f["breakeven_base"]

    scores = {"total": sc["total"], "grade": sc["grade"], "grade_label": sc["grade_label"],
              "range_lo": sc["range"][0], "range_hi": sc["range"][1], "confidence": sc["confidence"],
              "stage": sc["stage"], "audience": sc["audience"],
              "red_flags": [r["message"] for r in sc["red_flags"]], "top_gaps": sc["top_gaps"],
              "top_strengths": sc["top_strengths"], "market": sc.get("market", ""),
              "regulatory_definition": sc.get("regulatory_definition", ""),
              "by_audience": {a: v["total"] for a, v in sc_all.items()}}

    # ---------------- charts (scaled, localized)
    years_m = [str(y) for y in market["projection"]["years"]]
    scn_m = market["projection"]["scenarios"]
    yrs_f = [str(y) for y in base["years"]]
    charts = {
        "tam_sam_som": {"type": "bar", "categories": ["TAM", "SAM", "SOM"], "scale": s_bn, "number_format": "#,##0.00",
                        "series": [{"name": str(market["base_year"]),
                                    "values": [market["base"]["TAM"], market["base"]["SAM"], market["base"]["SOM"]]}],
                        "highlight_index": 1},
        "sam_scenarios": {"type": "line_markers", "categories": years_m, "scale": s_bn, "number_format": "#,##0.0",
                          "series": [{"name": S[k], "values": v["SAM"]} for k, v in scn_m.items()],
                          "series_color_index": SCN_COLORS(list(scn_m))},
        "som_scenarios": {"type": "column", "categories": years_m[1:], "scale": s_mn, "number_format": "#,##0",
                          "series": [{"name": S[k], "values": v["SOM"][1:]} for k, v in scn_m.items()],
                          "series_color_index": SCN_COLORS(list(scn_m))},
        "revenue_ebitda": {"type": "column", "categories": yrs_f, "scale": s_mn, "number_format": "#,##0",
                           "y_min": None, "series": [
                               {"name": Lb["revenue"], "values": [r["revenue"] for r in base["rows"]]},
                               {"name": "EBITDA", "values": [r["ebitda"] for r in base["rows"]]}]},
        "revenue_scenarios": {"type": "line_markers", "categories": yrs_f, "scale": s_mn, "number_format": "#,##0",
                              "series": [{"name": S[k], "values": [r["revenue"] for r in
                                          fin["scenarios"][k]["rows"]]} for k in fin["scenarios"]],
                              "series_color_index": SCN_COLORS(list(fin["scenarios"]))},
        "cash": {"type": "column", "categories": yrs_f, "scale": s_mn, "number_format": "#,##0",
                 "series": [{"name": Lb["cash"],
                             "values": [r["cash_end"] for r in base["rows"]]}]},
        "score": {"type": "bar", "categories": [r["name"] for r in sc["breakdown"]], "number_format": "0.0",
                  "y_max": 5, "series": [{"name": Lb["score"], "values": [r["score"] for r in sc["breakdown"]]}]},
        "segments_sam": {"type": "bar", "categories": [r["segment"] for r in market["bottom_up"]["segments"]],
                         "scale": s_mn, "number_format": "#,##0",
                         "series": [{"name": "SAM", "values": [r["SAM"] for r in market["bottom_up"]["segments"]]}]},
    }

    # ---------------- tables (pre-formatted strings → identical in report and deck)
    mn = lambda v: fmt_money(v, cur, lang, "mn", 0)
    bn = lambda v: fmt_money(v, cur, lang, "bn", 2)
    pct = lambda v: fmt_pct(v, 0, lang) if v is not None else "—"
    tables = {
        "segments": [[r["segment"], fmt_number(r["units"], 0, lang), fmt_money(r["arpa"], cur, lang, None, 1),
                      bn(r["TAM"]), bn(r["SAM"]), mn(r["SOM"])] for r in market["bottom_up"]["segments"]],
        "market_scenarios": [[S[k], pct(v["cagr"]), fmt_money(v["TAM_horizon"], cur, lang, "bn", 1),
                              fmt_money(v["SAM_horizon"], cur, lang, "bn", 1), mn(v["SOM_horizon"])]
                             for k, v in scn_m.items()],
        "pnl": [
            [Lb["customers"]] + [fmt_number(r["customers_end"], 0, lang) for r in base["rows"]],
            [Lb["revenue"]] + [mn(r["revenue"]) for r in base["rows"]],
            [Lb["gross_margin"]] + [pct(r["gross_margin"]) for r in base["rows"]],
            ["EBITDA"] + [mn(r["ebitda"]) for r in base["rows"]],
            [Lb["fcf"]] + [mn(r["fcf"]) for r in base["rows"]],
            [Lb["cash"]] + [mn(r["cash_end"]) for r in base["rows"]],
            ["LTV/CAC"] + [fmt_multiple(r["ltv_cac"], 1, lang) if r["ltv_cac"] else "—" for r in base["rows"]],
            [Lb["cac_payback"]] + [fmt_number(r["cac_payback_months"], 1, lang) if r["cac_payback_months"] else "—" for r in base["rows"]],
        ],
        "pnl_columns": [Lb["metric"]] + yrs_f,
        "fin_scenarios": [[S[k], mn(v["summary"]["revenue_last"]), v["summary"]["ebitda_breakeven_year"] and str(v["summary"]["ebitda_breakeven_year"]) or f"{after}{f['end_year']}",
                           mn(v["summary"]["npv"]), fmt_multiple(v["summary"].get("moic"), 1, lang),
                           pct(v["summary"].get("investor_irr"))] for k, v in fin["scenarios"].items()],
        "scorecard": [{"name": r["name"], "weight": r["weight"], "score": r["score"], "note": r["note"]} for r in sc["breakdown"]],
        "by_audience": [[Lb["aud"].get(a, a), fmt_number(v["total"], 0, lang), v["grade"]]
                        for a, v in sc_all.items()],
    }
    sens = fin.get("sensitivity")
    if sens:
        tables["sensitivity_columns"] = [Lb["sens_axis"]] + [fmt_pct(x - 1, 0, lang) if x != 1 else "0%" for x in sens["x_values"]]
        tables["sensitivity"] = [[(fmt_pct(y - 1, 0, lang) if y != 1 else "0%")] + [mn(v) for v in row]
                                 for y, row in zip(sens["y_values"], sens["grid"])]
    return {"_EXAMPLE_DATA": project.get("_EXAMPLE_DATA", ""), "project": {"name": project.get("name"), "locale": lang,
            "language": lang, "currency": cur, "units": units(lang, cur),
            "market_profile": project.get("market_profile") or norm_market(lang)}, "market": m, "fin": f, "score": scores, "charts": charts, "tables": tables,
            "key_facts": project.get("key_facts", [])}


def _rel(path: str, base: str) -> str:
    return os.path.relpath(path, base).replace(os.sep, "/")


def _relativize(obj, base):
    """Make every absolute path inside a result relative to the output folder (portable, no local paths)."""
    if isinstance(obj, dict):
        return {k: _relativize(v, base) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_relativize(v, base) for v in obj]
    if isinstance(obj, str) and os.path.isabs(obj) and os.path.exists(os.path.dirname(obj) or "/"):
        return _rel(obj, base)
    return obj


def run(project_path: str, locale: str | None = None, render: bool | None = None,
        themes: list[str] | None = None, pattern: str | None = None) -> dict:
    pdir = os.path.dirname(os.path.abspath(project_path))
    P = lambda x: os.path.join(pdir, x)
    project = load_json(project_path)
    if locale:
        project["locale"] = locale
    lang = locale_of(project)
    project["locale"] = lang
    if render is not None:
        project["render"] = render
    if themes:
        project["themes"] = list(themes)
    if pattern:
        project["pattern"] = pattern
    out = P(project.get("out_dir", "output"))
    os.makedirs(out, exist_ok=True)
    market = size_market(load_json(P(project["market"])))
    fin_spec = load_json(P(project["finance"]))
    fin = fin_build(fin_spec)
    sc_in = load_json(P(project["scoring"]))
    sc_in.setdefault("locale", lang)
    sc_in.setdefault("market", project.get("market_profile") or norm_market(lang))
    sc_in.setdefault("facts", {})["ltv_cac"] = fin["base"]["rows"][-1]["ltv_cac"]
    sc = score(sc_in)
    sc_all = {a: score({**sc_in, "audience": a}) for a in ("investor", "government", "corporate", "academic")}
    facts = build_facts(project, market, fin, sc, sc_all)
    if project.get("metrics"):
        from metrics_calc import run_batch
        facts["metrics"] = run_batch(project["metrics"])["results"]
    for ef in project.get("extra_facts", []) or []:   # e.g. auto_facts.json from auto_pitch.py (namespace "auto")
        facts.update(load_json(P(ef)) if isinstance(ef, str) else ef)
    if project.get("pattern"):
        facts["project"]["pattern"] = project["pattern"]
    dump_json(market, os.path.join(out, "market_result.json"))
    dump_json(fin, os.path.join(out, "finance_result.json"))
    dump_json(sc, os.path.join(out, "scoring_result.json"))
    facts_path = os.path.join(out, "facts.json")
    dump_json(facts, facts_path)
    results = {"facts": facts_path, "builds": {}, "qa": {}}
    if project.get("report_spec"):
        rp = os.path.join(out, "report.docx")
        results["builds"]["report"] = build_docx(P(project["report_spec"]), rp, facts=facts, locale=lang)
    for th in project.get("themes", ["light"]):
        dp = os.path.join(out, "deck.pptx" if th == (project.get("themes") or ["light"])[0] else f"deck_{th}.pptx")
        results["builds"][f"deck_{th}"] = build_pptx(P(project["deck_spec"]), dp, theme=th, facts=facts, locale=lang)
        q = run_qa(pptx=dp, docx=os.path.join(out, "report.docx") if project.get("report_spec") else None,
                   facts=facts_path, language=lang, currency=facts["project"]["currency"],
                   pattern=project.get("pattern"))
        dump_json(q, os.path.join(out, f"qa_{th}.json"))
        results["qa"][th] = q["summary"]
    if project.get("render"):
        from render_preview import render
        results["renders"] = {
            "report": render(os.path.join(out, "report.docx"), os.path.join(out, "renders", "report")),
        }
        for th in project.get("themes", ["light"]):
            name = "deck" if th == (project.get("themes") or ["light"])[0] else f"deck_{th}"
            results["renders"][name] = render(os.path.join(out, f"{name}.pptx"), os.path.join(out, "renders", name))
    results = _relativize(results, out)
    results["locale"] = lang
    dump_json(results, os.path.join(out, "pipeline_summary.json"))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--locale", "-l", choices=["ru", "en", "zh", "vi", "id", "ms"], help="overrides project.locale")
    ap.add_argument("--no-render", action="store_true", help="skip LibreOffice renders")
    ap.add_argument("--theme", action="append", help="theme (repeatable); overrides project.themes")
    ap.add_argument("--pattern", help="pitch pattern id for QA (patterns/patterns.json)")
    a = ap.parse_args(argv)
    print(dump_json(run(a.project, a.locale, False if a.no_render else None, a.theme, a.pattern)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
