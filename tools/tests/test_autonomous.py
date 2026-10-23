"""Tests for the autonomous data mode, pitch patterns, themes and the QA completeness gate.

Run from the repository root:  python -m unittest discover -s tools/tests -v
Everything is written to temporary directories; the repository is never modified.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import auto_pitch as AP  # noqa: E402
import estimator as E  # noqa: E402
import market_definer as MD  # noqa: E402
import metrics_calc as M  # noqa: E402
import product_profiler as PP  # noqa: E402
import research_ledger as RL  # noqa: E402
from build_pptx import build_pptx  # noqa: E402
from pitch_story import Story  # noqa: E402
from qa_check import Findings, completeness, run_qa  # noqa: E402

EXA = os.path.join(ROOT, "examples", "autonomous_shiftlyra")
LOCS = ["ru", "en", "zh", "vi", "id", "ms"]


def brief(lang="ru"):
    with open(os.path.join(EXA, f"brief_{lang}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def jload(*p):
    with open(os.path.join(*p), encoding="utf-8") as fh:
        return json.load(fh)


def sourced(id_, key, value, year=2025, url="https://rosstat.gov.ru/statistics", **kw):
    return dict(id=id_, key=key, value=value, type="sourced", confidence="high", source_url=url,
                source_name="official statistics", year=year, **kw)


class TestProfilerAndDefiner(unittest.TestCase):
    def test_profile_infers_category_and_statuses(self):
        for lang, cur in (("ru", "RUB"), ("en", "USD")):
            b = brief(lang)
            d = PP.profile(b["text"], b["name"], b["market"])
            self.assertEqual(d["profile"]["category"], "workforce_management")
            self.assertEqual(d["profile"]["currency"], cur)
            statuses = {c["status"] for c in d["checklist"]}
            self.assertTrue(statuses <= {"from_text", "inferred", "default", "to_confirm"})
            self.assertGreater(d["coverage"], 0.5)

    def test_overrides_win(self):
        d = PP.profile("A tool for teams", "X", "en", {"category": "devtools"})
        self.assertEqual(d["profile"]["category"], "devtools")

    def test_market_definition_has_segments_queries_sources(self):
        b = brief("ru")
        m = MD.define(PP.profile(b["text"], b["name"], "ru"), "ru", 2026)
        self.assertTrue(m["segments"])
        self.assertTrue(all({"id", "size_band", "isic", "name"} <= set(s) for s in m["segments"]))
        self.assertTrue(any(q["lang"] == "ru" for q in m["queries"]))
        self.assertTrue(any(q["lang"] == "en" for q in m["queries"]))
        self.assertTrue(m["official_sources"])
        self.assertIn("ОКВЭД", m["definition"]["classification"]["name"])
        for mk in ("ru", "en", "zh", "vn", "id", "my"):
            md = MD.define(PP.profile("Shift scheduling app for cafes, per location per month", "X", mk), mk, 2026)
            self.assertTrue(md["research_plan"], mk)
            self.assertTrue(md["queries"], mk)


class TestLedger(unittest.TestCase):
    def test_validation_rules(self):
        self.assertTrue(RL.validate_fact({"id": "a", "key": "k", "value": 1, "type": "sourced", "confidence": "high"}))
        self.assertTrue(RL.validate_fact({"id": "b", "key": "k", "value": 1, "type": "estimate", "confidence": "low"}))
        self.assertEqual(RL.validate_fact(sourced("c", "k", 1)), [])

    def test_add_rejects_unsourced_fact(self):
        L = RL.new_ledger("RUB", 2026)
        with self.assertRaises(Exception):
            RL.add_fact(L, {"id": "x", "key": "k", "value": 1, "type": "sourced", "confidence": "high"})

    def test_resolve_prefers_sourced_and_flags_conflict(self):
        L = RL.new_ledger("RUB", 2026)
        RL.add_fact(L, sourced("a", "count.x", 100))
        RL.add_fact(L, {"id": "b", "key": "count.x", "value": 130, "type": "estimate", "confidence": "low",
                        "method": "proxy", "formula": "n * s", "year": 2025})
        r = RL.resolve(L)
        self.assertEqual(r["values"]["count.x"]["id"], "a")
        self.assertEqual(len(r["conflicts"]), 1)
        ex = RL.export(L)
        self.assertEqual(ex["values"]["count_x"]["value"], 100)
        self.assertEqual(ex["stats"]["sourced"], 1)
        self.assertEqual(ex["stats"]["estimates"], 1)
        self.assertTrue(ex["sources"])

    def test_example_ledgers_valid(self):
        for f in ("ledger_ru.json", "ledger_en.json"):
            L = jload(EXA, f)
            v = RL.validate(L)
            self.assertTrue(v["ok"], (f, v["errors"]))
            for fact in L["facts"]:
                if fact["type"] == "sourced":
                    self.assertTrue(fact["source_url"].startswith("https://"), fact["id"])
                else:
                    self.assertTrue(fact.get("formula") or fact.get("method"), fact["id"])


class TestEstimator(unittest.TestCase):
    def test_expr_corners(self):
        r = E.expr("a * b", {"a": {"low": 1, "base": 2, "high": 3}, "b": 10})
        self.assertEqual((r["low"], r["base"], r["high"]), (10, 20, 30))
        self.assertEqual(r["fact"]["type"], "estimate")
        r2 = E.expr("a / b", {"a": 10, "b": {"low": 2, "base": 5, "high": 10}})
        self.assertEqual((r2["low"], r2["high"]), (1, 5))

    def test_expr_is_safe(self):
        with self.assertRaises(Exception):
            E.expr("__import__('os').system('true')", {})

    def test_bottom_up_and_triangulate(self):
        bu = E.bottom_up([{"id": "s", "units": 1000, "price": 100, "serviceable": 0.5, "obtainable": 0.1}])
        self.assertEqual(bu["totals"]["TAM"]["base"], 100000)
        self.assertEqual(bu["totals"]["SAM"]["base"], 50000)
        self.assertAlmostEqual(bu["totals"]["SOM"]["base"], 5000)
        self.assertTrue(E.triangulate({"bu": 100, "td": 180})["verdict"].startswith("acceptable"))
        self.assertTrue(E.triangulate({"bu": 100, "td": 140})["verdict"].startswith("consistent"))
        self.assertTrue(E.triangulate({"bu": 100, "td": 300})["verdict"].startswith("inconsistent"))

    def test_unit_economics_identity(self):
        u = E.unit_economics("smb", 1000)
        b = E.load_benchmarks()["segments"]["smb"]
        churn, pb = b["monthly_logo_churn"]["base"], b["cac_payback_months"]["base"]
        self.assertAlmostEqual(u["ltv_cac"]["base"], 1 / (churn * pb))
        self.assertLess(u["ltv_cac"]["low"], u["ltv_cac"]["base"])
        self.assertLess(u["ltv_cac"]["base"], u["ltv_cac"]["high"])

    def test_cagr_from_drivers(self):
        r = E.cagr_from_drivers(0.05, 0.1, 0.2, 5)
        self.assertAlmostEqual(r["base"], 1.05 * 2 ** 0.2 - 1)
        self.assertIn("formula", r)

    def test_benchmarks_are_labelled(self):
        self.assertIn("RULES OF THUMB", json.dumps(E.load_benchmarks())[:3000].upper())


class TestCustomerMetrics(unittest.TestCase):
    def test_customer_roi(self):
        r = M.customer_roi(annual_benefit=120, annual_cost=20, one_off_cost=10, years=3)
        self.assertGreater(r["value"], 0)
        self.assertGreater(r["payback_months"], 0)
        self.assertIn("formula", r)

    def test_customer_tco(self):
        r = M.customer_tco(years=3, subscription_per_year=10, implementation=5, alternative_cost_per_year=30)
        self.assertAlmostEqual(r["value"], 35)
        self.assertAlmostEqual(r["alternative_tco"], 90)
        self.assertAlmostEqual(r["saving"], 55)

    def test_smb_monthly_value(self):
        r = M.smb_monthly_value(price_per_month=1000, hours_saved_per_month=10, hourly_cost=500)
        self.assertAlmostEqual(r["monthly_saving"], 5000)
        self.assertAlmostEqual(r["value"], 5)


class TestQACompleteness(unittest.TestCase):
    FULL = "TAM 10 bn, SAM 3 bn, SOM 100 mn; CAGR 12%; LTV/CAC 5x, CAC payback 8 months"

    def test_passes_with_all_metrics(self):
        f = Findings()
        completeness(self.FULL, "", f)
        self.assertEqual(f.count("error"), 0)

    def test_fails_without_sizing_cagr_ue(self):
        for missing, code in (("TAM 10 bn, SAM 3 bn, SOM 100 mn", "no_market_sizing"), ("CAGR 12%", "no_cagr"),
                              ("LTV/CAC 5x, CAC payback 8 months", "no_unit_economics")):
            f = Findings()
            completeness(self.FULL.replace(missing, "x"), "", f)
            self.assertIn(code, [i["check"] for i in f.items])

    def test_fails_on_gap_placeholders(self):
        for txt in ("Market: no data", "Цена — нет данных", "市场规模：数据缺口", "TBD", "Harga: tiada data",
                    "Giá: thiếu dữ liệu", "Giá: chưa có dữ liệu", "Harga: belum ada data", "Цена: данных нет", "Harga: kekurangan data", "[[gap]]"):
            f = Findings()
            completeness(self.FULL + ". " + txt, "", f)
            self.assertIn("data_gap_placeholder", [i["check"] for i in f.items], txt)

    def test_customer_pattern_needs_roi(self):
        pat = AP.select_pattern("corporate")
        f = Findings()
        completeness("TAM 10 bn, SAM 3 bn; CAGR 12%; LTV/CAC 5x", "", f, pat)
        self.assertIn("no_customer_roi", [i["check"] for i in f.items])
        f = Findings()
        completeness(self.FULL + "; ROI 300%, TCO 1 mn, payback 2 months", "", f, pat)
        self.assertEqual(f.count("error"), 0)

    def test_templates_and_examples_free_of_gap_wording(self):
        pat = re.compile(r"нет данных|данных нет|暂无数据|tiada data|belum ada data|chưa có dữ liệu|\"no data\"")
        for base in ("templates", "examples"):
            for dp, _, fs in os.walk(os.path.join(ROOT, base)):
                for fn in fs:
                    if fn.endswith("_spec.json") or fn.endswith(".template.json"):
                        with open(os.path.join(dp, fn), encoding="utf-8") as fh:
                            self.assertIsNone(pat.search(fh.read()), os.path.join(dp, fn))


class TestPatterns(unittest.TestCase):
    def setUp(self):
        self.P = jload(ROOT, "patterns", "patterns.json")

    def test_patterns_complete(self):
        need = {"label_en", "label_ru", "kind", "theme", "deck_length", "slide_order", "mandatory_metrics", "charts",
                "cta_en", "cta_ru", "scoring", "red_team_en", "audience_keywords"}
        self.assertTrue({"large_investor", "small_investor", "corporate", "smb", "government"} <= set(self.P["patterns"]))
        themes = jload(ROOT, "config", "themes.json")
        for k, p in self.P["patterns"].items():
            self.assertTrue(need <= set(p), (k, need - set(p)))
            self.assertIn(p["theme"], themes)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "patterns", f"{k}.md")), k)
            for sid in p["slide_order"]:
                self.assertTrue(hasattr(Story, f"s_{sid}"), (k, sid))
            for t in p.get("mandatory_terms", []):
                re.compile(t)

    def test_auto_selection(self):
        self.assertEqual(AP.select_pattern("auto", "бизнес-ангелы и посевные фонды")["id"], "small_investor")
        self.assertEqual(AP.select_pattern("auto", "growth fund investment committee")["id"], "large_investor")
        self.assertEqual(AP.select_pattern("auto", "владельцы кафе и магазинов")["id"], "smb")
        self.assertEqual(AP.select_pattern("auto", "грант института развития")["id"], "government")
        self.assertEqual(AP.select_pattern(None, "")["id"], self.P["default"])
        self.assertEqual(AP.select_pattern("corporate")["selected_by"], "explicit")
        with self.assertRaises(KeyError):
            AP.select_pattern("nope")


class TestThemes(unittest.TestCase):
    NEW = ("comet", "editorial", "corporate", "warm")
    KEYS = {"bg", "text", "muted", "accent", "accent2", "grid", "panel", "palette", "font_heading", "font_body",
            "title_style", "cover_style", "table_header_bg", "table_header_text", "positive", "negative", "fonts"}

    def test_definitions(self):
        T = jload(ROOT, "config", "themes.json")
        for name in self.NEW:
            self.assertTrue(self.KEYS <= set(T[name]), (name, self.KEYS - set(T[name])))
            self.assertTrue(T[name]["fonts"]["zh"].get("font_ea"), name)
            self.assertGreaterEqual(len(T[name]["palette"]), 4)

    def test_each_theme_builds_and_passes_qa(self):
        spec = jload(EXA, "output_themes_ru", "deck_spec.json")
        facts = jload(EXA, "output_themes_ru", "facts.json")
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        for name in self.NEW + ("light", "dark", "academic_light"):
            s = json.loads(json.dumps(spec))
            s["meta"]["theme"] = name
            out = os.path.join(tmp, f"{name}.pptx")
            build_pptx(s, out, theme=name, facts=facts, locale="ru")
            q = run_qa(pptx=out, facts=facts, locale="ru", completeness_check=False)
            self.assertEqual(q["summary"]["errors"], 0, (name, [x for x in q["findings"] if x["severity"] == "error"]))


class TestAutoPitch(unittest.TestCase):
    def _run(self, b, pattern=None, plan_only=False):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        if b.get("ledger"):
            shutil.copy(os.path.join(EXA, b["ledger"]), tmp)
        p = os.path.join(tmp, "brief.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(b, fh, ensure_ascii=False)
        res = AP.run(p, pattern=pattern, out_dir="out", plan_only=plan_only)
        return os.path.join(tmp, "out"), res

    def test_plan_only(self):
        out, r = self._run(brief("ru"), plan_only=True)
        plan = jload(out, "research_plan.json")
        self.assertTrue(plan["queries"])
        self.assertEqual(r["pattern"], "small_investor")
        self.assertFalse(os.path.exists(os.path.join(out, "deck.pptx")))

    def test_full_run_with_ledger_all_patterns(self):
        for pat in ("large_investor", "corporate", "smb", "government"):
            out, _ = self._run(brief("ru"), pat)
            s = jload(out, "auto_summary.json")
            for theme, q in s["qa"].items():
                self.assertEqual(q["errors"], 0, (pat, theme))
            k = s["key_numbers"]
            self.assertGreater(k["tam_bu"], k["sam"])
            self.assertGreater(k["sam"], k["som_horizon"])
            self.assertLessEqual(k["cagr"][0], k["cagr"][1])
            self.assertLessEqual(k["cagr"][1], k["cagr"][2])
            self.assertTrue(RL.validate(jload(out, "ledger_full.json"))["ok"])
            self.assertLessEqual(len(s["to_confirm"]), 7)
            self.assertFalse(s["offline"])

    def test_offline_run_completes_with_watermark(self):
        b = brief("en")
        b.pop("ledger", None)
        out, _ = self._run(b, "small_investor")
        s = jload(out, "auto_summary.json")
        self.assertTrue(s["offline"])
        for q in s["qa"].values():
            self.assertEqual(q["errors"], 0)
        self.assertIn("offline", json.dumps(jload(out, "deck_spec.json")["meta"]).lower())

    def test_every_estimate_is_labelled(self):
        out, _ = self._run(brief("en"), "large_investor")
        for f in jload(out, "ledger_full.json")["facts"]:
            if f["type"] == "estimate":
                self.assertTrue(f.get("method"), f["id"])
                self.assertTrue(f.get("formula") or f.get("range"), f["id"])
                self.assertIn(f["confidence"], ("high", "medium", "low"))


class TestPrompts(unittest.TestCase):
    def test_research_loop_in_all_locales(self):
        for loc in LOCS:
            p = os.path.join(ROOT, "prompts", loc, "research_loop.md")
            self.assertTrue(os.path.exists(p), loc)
            with open(p, encoding="utf-8") as fh:
                txt = fh.read()
            self.assertIn("auto_pitch.py", txt)
            self.assertIn("research_ledger", txt)


if __name__ == "__main__":
    unittest.main()
