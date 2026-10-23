#!/usr/bin/env python3
"""scoring.py — weighted development/product-potential score (0–100) from a 0–5 rubric.

Input JSON:
{
  "stage": "pilot",                 # idea | prototype | pilot | growth | default
  "audience": "government",         # neutral | investor | government | corporate | academic
  "locale": "ru",                   # ru | en | zh — output language (alias: "language")
  "market": "ru",                   # market profile ru | en | zh (defaults to locale): regulatory criterion,
                                    #   currency SAM anchors, weight multipliers, market red-flag rules
  "model": "../config/scoring_model.json",   # optional path; default = bundled config
  "weights_override": {"market": 20},        # optional absolute weights; renormalized to 100
  "scores": {"market": {"score": 3.5, "evidence": "B", "note": "..."}, "...": {}},
  "facts": {"ltv_cac": 3.4, "runway_months": 14, "top_customer_share": 0.3,
            "critical_foreign_dependency": false,
            "registry_eligible": true,                        # ru profile
            "security_attestation": true, "fedramp_path": false, "ai_risk_unassessed": false,   # en
            "xinchuang_adapted": true, "mlps_certified": true, "genai_filing_missing": false},     # zh
  "deck_slides": 16                 # optional: allocate slides by audience deck weights
}
Output: weights used, per-criterion breakdown, total, grade, pessimistic/optimistic range,
evidence confidence, red flags, top strengths / gaps, deck slide allocation, chart data.

CLI:
  python scoring.py --input scores.json [--out result.json]
  python scoring.py --input scores.json --locale zh --market zh
  python scoring.py profiles [--locale ru] [--market ru]   # full stage × audience weight matrix
  python scoring.py template [--market zh]                 # empty scores template
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmt_utils import cli_io, dump_json, fmt_number, fmt_pct, load_json  # noqa: E402
from locales import locale_of, norm_locale, norm_market  # noqa: E402

MISSING = {"ru": "Не оценены критерии: ", "en": "Unscored criteria: ", "zh": "未评分维度：", "vi": "Tiêu chí chưa chấm: ",
           "id": "Kriteria belum dinilai: ", "ms": "Kriteria belum dinilai: "}
SERIES = {"ru": "балл", "en": "score", "zh": "评分", "vi": "điểm", "id": "skor", "ms": "skor"}

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = os.path.join(HERE, "..", "config", "scoring_model.json")


def load_model(path: str | None = None) -> dict:
    return load_json(path or DEFAULT_MODEL)


def _normalize(w: dict) -> dict:
    tot = sum(w.values())
    return {k: v * 100.0 / tot for k, v in w.items()}


def market_profile(model: dict, market: str | None) -> dict:
    if not market:
        return {}
    return (model.get("market_profiles") or {}).get(norm_market(market), {})


def weights_for(model: dict, stage: str = "default", audience: str = "neutral",
                override: dict | None = None, market: str | None = None) -> dict:
    """stage profile → (override) → × audience multipliers → × market multipliers → renormalize to 100."""
    prof = {k: v for k, v in (model["stage_profiles"].get(stage) or model["stage_profiles"]["default"]).items()
            if not k.startswith("_")}
    if override:
        prof.update(override)
    mult = model["audience_multipliers"].get(audience, {})
    mm = market_profile(model, market).get("weight_multipliers", {})
    w = {k: v * mult.get(k, 1.0) * mm.get(k, 1.0) for k, v in prof.items()}
    return _normalize(w)


def criteria_for(model: dict, market: str | None = None) -> dict:
    """Criteria with market-profile overrides (names, definitions, anchors) merged in."""
    crit = {c["id"]: dict(c) for c in model["criteria"]}
    for cid, ov in market_profile(model, market).get("criteria", {}).items():
        if cid in crit:
            crit[cid].update(ov)
    return crit


def _t(obj: dict, key: str, lang: str):
    return obj.get(f"{key}_{lang}", obj.get(f"{key}_en"))


def _grade(model, total, lang):
    for b in model["grade_bands"]:
        if total >= b["min"]:
            return b["grade"], _t(b, "label", lang)
    return "E", ""


def allocate_slides(model: dict, audience: str, n_slides: int, fixed: int = 2) -> dict:
    """Largest-remainder allocation of (n_slides − fixed title/closing) by deck weights."""
    dw = model["deck_weights"].get(audience) or model["deck_weights"]["investor"]
    dw = {k: v for k, v in dw.items() if not k.startswith("_")}
    budget = max(n_slides - fixed, 1)
    raw = {k: v / 100 * budget for k, v in dw.items()}
    alloc = {k: int(v) for k, v in raw.items()}
    rem = budget - sum(alloc.values())
    for k in sorted(raw, key=lambda k: raw[k] - alloc[k], reverse=True)[:rem]:
        alloc[k] += 1
    return {"weights": dw, "slides": alloc, "fixed_slides": fixed, "total": n_slides}


def score(payload: dict) -> dict:
    model = load_model(payload.get("model"))
    lang = locale_of(payload)
    market = norm_market(payload.get("market"), lang)
    stage = payload.get("stage", "default")
    audience = payload.get("audience", "neutral")
    w = weights_for(model, stage, audience, payload.get("weights_override"), market)
    crit = criteria_for(model, market)
    ev_levels = model["evidence_levels"]
    rows, total, lo, hi, conf_num = [], 0.0, 0.0, 0.0, 0.0
    missing = []
    for cid, weight in w.items():
        entry = payload.get("scores", {}).get(cid)
        if entry is None:
            missing.append(cid)
            entry = {"score": 0, "evidence": "C", "note": "not scored"}
        if isinstance(entry, (int, float)):
            entry = {"score": float(entry), "evidence": "B"}
        s = max(0.0, min(5.0, float(entry["score"])))
        ev = entry.get("evidence", "B")
        band = {"A": 0.0, "B": 0.5, "C": 1.0}.get(ev, 1.0)
        contrib = weight * s / 5
        total += contrib
        lo += weight * max(s - band, 0) / 5
        hi += weight * min(s + band, 5) / 5
        conf_num += weight * ev_levels.get(ev, {"confidence": 0.4})["confidence"]
        anchors = _t(crit[cid], "anchors", lang)
        rows.append({"id": cid, "name": _t(crit[cid], "name", lang),
                     "weight": round(weight, 2), "score": s, "evidence": ev,
                     "contribution": round(contrib, 2), "max_contribution": round(weight, 2),
                     "weighted_gap": round(weight - contrib, 2),
                     "anchor": anchors[int(round(s))] if anchors else "", "note": entry.get("note", "")})
    confidence = conf_num / 100.0
    grade, label = _grade(model, total, lang)

    flags = []
    facts = payload.get("facts", {})
    by_id = {r["id"]: r for r in rows}
    for rule in model["red_flag_rules"]:
        if rule.get("markets") and market not in rule["markets"]:
            continue
        t = rule["type"]
        m = _t(rule, "message", lang)
        if t == "score_below_with_weight":
            for r in rows:
                if r["score"] <= rule["score_max"] and r["weight"] >= rule["weight_min"]:
                    flags.append({"id": rule["id"], "severity": rule["severity"], "message": f"{m}: {r['name']}"})
        elif t == "stage_trl":
            if stage in rule["stages"] and by_id.get("trl", {}).get("score", 5) <= rule["trl_score_max"]:
                flags.append({"id": rule["id"], "severity": rule["severity"], "message": m})
        elif t == "fact_below":
            v = facts.get(rule["fact"])
            if v is not None and v < rule["threshold"]:
                flags.append({"id": rule["id"], "severity": rule["severity"], "message": f"{m} ({fmt_number(v, 2, lang)})"})
        elif t == "fact_above":
            v = facts.get(rule["fact"])
            if v is not None and v > rule["threshold"]:
                flags.append({"id": rule["id"], "severity": rule["severity"], "message": f"{m} ({fmt_number(v, 2, lang)})"})
        elif t == "fact_false_for_audience":
            if audience in rule["audiences"] and facts.get(rule["fact"]) is False:
                flags.append({"id": rule["id"], "severity": rule["severity"], "message": m})
        elif t == "fact_true":
            if facts.get(rule["fact"]) is True:
                flags.append({"id": rule["id"], "severity": rule["severity"], "message": m})
        elif t == "confidence_below":
            if confidence < rule["threshold"]:
                flags.append({"id": rule["id"], "severity": rule["severity"], "message": f"{m} ({fmt_pct(confidence, 0, lang)})"})
    # drop the soft LTV/CAC flag when the hard one fired
    ids = {f["id"] for f in flags}
    if "ltv_cac" in ids:
        flags = [f for f in flags if f["id"] != "ltv_cac_soft"]
    if missing:
        flags.append({"id": "missing_scores", "severity": "medium",
                      "message": MISSING.get(lang, MISSING["en"]) + ("、" if lang == "zh" else ", ").join(missing)})

    strengths = sorted(rows, key=lambda r: (r["score"], r["weight"]), reverse=True)[:3]
    gaps = sorted(rows, key=lambda r: r["weighted_gap"], reverse=True)[:3]
    out = {
        "stage": stage, "audience": audience, "locale": lang, "language": lang, "market": market,
        "regulatory_definition": _t(crit["regulatory"], "definition", lang) or "",
        "total": round(total, 1), "range": [round(lo, 1), round(hi, 1)], "grade": grade, "grade_label": label,
        "confidence": round(confidence, 3), "weights": {k: round(v, 2) for k, v in w.items()},
        "breakdown": rows, "red_flags": flags,
        "top_strengths": [r["name"] for r in strengths], "top_gaps": [r["name"] for r in gaps],
        "chart": {"type": "bar", "categories": [r["name"] for r in rows],
                  "series": [{"name": SERIES.get(lang, "score"), "values": [r["score"] for r in rows]}]},
        "scorecard": [{"name": r["name"], "weight": r["weight"], "score": r["score"]} for r in rows],
    }
    if payload.get("deck_slides"):
        out["deck_allocation"] = allocate_slides(model, audience if audience != "neutral" else "investor",
                                                 int(payload["deck_slides"]))
    return out


def profiles(model: dict, lang: str = "en", market: str | None = None) -> dict:
    crit = criteria_for(model, market)
    names = {k: _t(c, "name", lang) for k, c in crit.items()}
    res = {}
    for st in [k for k in model["stage_profiles"] if not k.startswith("_")]:
        for au in [k for k in model["audience_multipliers"] if not k.startswith("_")]:
            res[f"{st}/{au}"] = {names[k]: round(v, 1) for k, v in weights_for(model, st, au, None, market).items()}
    return res


def template(model: dict, lang: str = "en", market: str | None = None) -> dict:
    market = norm_market(market, lang)
    facts = {"ltv_cac": None, "runway_months": None, "top_customer_share": None}
    for f in market_profile(model, market).get("facts", ["critical_foreign_dependency"]):
        facts[f] = None
    return {"stage": "pilot", "audience": "investor", "locale": lang, "market": market,
            "scores": {c["id"]: {"score": None, "evidence": "B", "note": ""} for c in model["criteria"]},
            "facts": facts}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("profiles", "template"):
        cmd = argv.pop(0)
        market = None
        if "--market" in argv:
            i = argv.index("--market")
            market = argv[i + 1]
            del argv[i:i + 2]
        payload, out, _ = cli_io(argv)
        payload = payload if isinstance(payload, dict) else {}
        model = load_model(payload.get("model"))
        lang = "en" if "--en" in argv else locale_of(payload, "en")
        print(dump_json(profiles(model, lang, market or lang) if cmd == "profiles" else template(model, lang, market), out))
        return 0
    if "--market" in argv:
        i = argv.index("--market")
        market = argv[i + 1]
        del argv[i:i + 2]
    else:
        market = None
    payload, out, _ = cli_io(argv)
    if not payload or set(payload) <= {"locale"}:
        print(__doc__)
        return 1
    if market:
        payload["market"] = market
    print(dump_json(score(payload), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
