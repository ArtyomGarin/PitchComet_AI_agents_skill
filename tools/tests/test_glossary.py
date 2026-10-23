"""Tests for the "What the numbers mean" glossary (config/glossary.json, tools/glossary.py).

Run from the repository root:  python -m unittest discover -s tools/tests -v
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import glossary as G  # noqa: E402
from build_docx import build_docx  # noqa: E402
from build_pptx import build_pptx  # noqa: E402
from qa_check import GAP_PATTERNS, run_qa  # noqa: E402

LOCS = ["ru", "en", "zh", "vi", "id", "ms"]

DECK_TEXT = {
    "ru": ("Рынок: TAM, SAM и SOM", "CAGR 18% и LTV/CAC 5,0x", "Окупаемость CAC 8 мес., валовая маржа 65%"),
    "en": ("Market: TAM, SAM and SOM", "CAGR 18% and LTV/CAC 5.0x", "CAC payback 8 months, gross margin 65%"),
    "zh": ("市场：TAM、SAM和SOM", "CAGR 18%，LTV/CAC 5.0倍", "获客成本回收期8个月，毛利率65%"),
    "vi": ("Thị trường: TAM, SAM và SOM", "CAGR 18% và LTV/CAC 5,0 lần", "Thời gian hoàn vốn CAC 8 tháng, biên lợi nhuận gộp 65%"),
    "id": ("Pasar: TAM, SAM dan SOM", "CAGR 18% dan LTV/CAC 5,0x", "Payback CAC 8 bulan, margin kotor 65%"),
    "ms": ("Pasaran: TAM, SAM dan SOM", "CAGR 18% dan LTV/CAC 5,0x", "Tempoh pulangan CAC 8 bulan, margin kasar 65%"),
}
EXPECTED = ["tam", "sam", "som", "cagr", "gross_margin", "cac", "ltv", "ltv_cac", "payback"]


def deck_spec(lang, glossary=True):
    a, b, c = DECK_TEXT[lang]
    src = {"ru": "Источник: тест", "en": "Source: test", "zh": "资料来源：测试", "vi": "Nguồn: thử nghiệm",
           "id": "Sumber: uji", "ms": "Sumber: ujian"}[lang]
    return {"meta": {"locale": lang, "title": "T", "glossary": glossary},
            "slides": [{"layout": "title", "title": "PitchComet test deck", "subtitle": "x"},
                       {"layout": "bullets", "title": a + " — " + b, "bullets": [b, c], "source": src, "notes": "n"},
                       {"layout": "bullets", "title": c + " " + a, "bullets": [c], "source": src, "notes": "n"}]}


def report_spec(lang, glossary=True):
    a, b, c = DECK_TEXT[lang]
    return {"meta": {"locale": lang, "title": "T", "glossary": glossary},
            "blocks": [{"type": "title_page"}, {"type": "page_break"},
                       {"type": "heading", "level": 1, "text": "1. " + a},
                       {"type": "paragraph", "text": b + ". " + c + "."},
                       {"type": "heading", "level": 1, "text": "2. " + c}]}


class TestGlossaryData(unittest.TestCase):
    def test_every_metric_in_six_locales(self):
        g = G.load()
        ids = [m["id"] for m in g["metrics"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 25)
        for m in g["metrics"]:
            for l in LOCS:
                self.assertTrue(m["term"].get(l), (m["id"], l))
                d = m["def"].get(l, "")
                self.assertTrue((5 if l == "zh" else 10) <= len(d) <= 200, (m["id"], l, len(d)))
                if l != "en":   # written natively, not copied from English
                    self.assertNotEqual(d, m["def"]["en"], (m["id"], l))
        for key, vals in g["labels"].items():
            for l in LOCS:
                self.assertTrue(vals.get(l), (key, l))

    def test_definitions_have_no_gap_placeholders(self):
        import re
        for m in G.load()["metrics"]:
            for l in LOCS:
                for p in GAP_PATTERNS:
                    self.assertIsNone(re.search(p, m["def"][l], re.I), (m["id"], l, p))

    def test_implied_ids_exist(self):
        ids = set(G.order())
        for m in G.load()["metrics"]:
            for i in m.get("implies", []):
                self.assertIn(i, ids)


class TestDetect(unittest.TestCase):
    def test_detect_all_locales(self):
        for l in LOCS:
            self.assertEqual(G.detect(" ".join(DECK_TEXT[l]), l), EXPECTED, l)

    def test_ratio_implies_parts_and_order(self):
        self.assertEqual(G.detect("LTV/CAC 4x", "en"), ["cac", "ltv", "ltv_cac"])

    def test_no_match_inside_words(self):
        self.assertEqual(G.detect("TAMBAHAN data SAMPLE SOMETHING", "id"), [])
        self.assertIn("tam", G.detect("市场规模TAM约80亿元", "zh"))

    def test_term_lookup(self):
        self.assertEqual(G.term_to_id("Валовая маржа", "ru"), "gross_margin")
        self.assertEqual(G.term_to_id("毛利率"), "gross_margin")


class TestGlossaryInDocuments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pc_gloss_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_deck_and_report_all_locales(self):
        from pptx import Presentation
        for l in LOCS:
            p, d = os.path.join(self.tmp, f"{l}.pptx"), os.path.join(self.tmp, f"{l}.docx")
            rep = build_pptx(deck_spec(l), p, theme="light", locale=l)
            self.assertEqual(rep["glossary"], EXPECTED, l)
            prs = Presentation(p)
            slides, ids = G.pptx_glossary_ids(prs)
            self.assertEqual(slides, [2], l)
            self.assertEqual(ids, EXPECTED, l)
            r2 = build_docx(report_spec(l), d, locale=l)
            self.assertEqual(r2["glossary"], EXPECTED, l)
            with open(d, "rb") as fh:
                parts = G.docx_parts(fh.read())
            self.assertTrue(parts["has_glossary"])
            self.assertEqual(parts["headings_before"], 0)
            self.assertEqual([G.term_to_id(t, l) for t in parts["terms"]], EXPECTED)
            qa = run_qa(pptx=p, docx=d, language=l, completeness_check=False)
            gl = [x for x in qa["findings"] if x["check"].startswith("glossary") or x["severity"] == "error"]
            self.assertEqual(gl, [], (l, gl))

    def test_missing_glossary_fails_qa(self):
        p, d = os.path.join(self.tmp, "x.pptx"), os.path.join(self.tmp, "x.docx")
        build_pptx(deck_spec("en", glossary=False), p, theme="light", locale="en")
        build_docx(report_spec("en", glossary=False), d, locale="en")
        qa = run_qa(pptx=p, docx=d, language="en", completeness_check=False)
        checks = [(x["where"], x["check"]) for x in qa["findings"] if x["severity"] == "error"]
        self.assertIn(("deck", "glossary_missing"), checks)
        self.assertIn(("report", "glossary_missing"), checks)

    def test_incomplete_glossary_fails_qa(self):
        p = os.path.join(self.tmp, "inc.pptx")
        spec = deck_spec("en", glossary=False)
        spec["slides"].insert(1, {"layout": "glossary", "title": "What the numbers mean", "notes": "n",
                                  "source": "Source: test", "items": G.entries(["tam"], "en")})
        build_pptx(spec, p, theme="light", locale="en")
        qa = run_qa(pptx=p, language="en", completeness_check=False)
        errs = [x for x in qa["findings"] if x["check"] == "glossary_incomplete"]
        self.assertEqual(len(errs), 1)
        self.assertIn("ltv_cac", errs[0]["message"])

    def test_full_glossary_fits_every_locale_and_theme(self):
        """All metrics at once: at most 12 per slide, no text overflow, in every locale; every theme builds."""
        import math
        n = len(G.order())
        for l in LOCS:
            specs = G.slide_specs(G.order(), l)
            self.assertEqual(len(specs), math.ceil(n / 12))
            spec = {"meta": {"locale": l, "glossary": False},
                    "slides": [{"layout": "title", "title": "Cover", "subtitle": "x"}] + specs}
            p = os.path.join(self.tmp, f"full_{l}.pptx")
            rep = build_pptx(spec, p, theme="light", locale=l)
            self.assertFalse([w for w in rep["warnings"] if "overflow" in w], (l, rep["warnings"]))
            qa = run_qa(pptx=p, language=l, completeness_check=False, glossary_check=False)
            bad = [x for x in qa["findings"] if x["severity"] in ("error", "warning")]
            self.assertEqual(bad, [], (l, bad))
        with open(os.path.join(ROOT, "config", "themes.json"), encoding="utf-8") as fh:
            themes = [k for k, v in json.load(fh).items() if isinstance(v, dict) and not k.startswith("_")]
        for th in themes:
            p = os.path.join(self.tmp, f"th_{th}.pptx")
            build_pptx(deck_spec("zh"), p, theme=th, locale="zh")
            qa = run_qa(pptx=p, language="zh", completeness_check=False)
            self.assertEqual(qa["summary"]["errors"], 0, (th, qa["findings"]))


if __name__ == "__main__":
    unittest.main()
