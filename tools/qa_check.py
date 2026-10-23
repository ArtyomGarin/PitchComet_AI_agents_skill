#!/usr/bin/env python3
"""qa_check.py — quality gate for the strategy deck (.pptx) and report (.docx).

Checks
  PPTX: estimated text overflow, shapes off-slide, tiny fonts, action titles (not labels),
        source line on every data slide (chart / table / big number / numeric claims),
        charts are native (graphicFrame + embedded workbook) and not pictures, word density,
        speaker notes, banned/unverifiable phrases, unresolved {{placeholders}}.
  DOCX: native charts (c:chart part + embedded xlsx), pictures that may be chart images,
        source line after each table/chart, footnotes, headings, fonts, banned phrases,
        unresolved placeholders.
  Consistency: key facts (from facts.json) must appear identically in both files; numbers
        with units on slides must also appear in the report.

CLI:
  python qa_check.py --pptx deck.pptx --docx report.docx [--facts facts.json --key-facts keys.json]
                     [--banned ../config/banned_phrases.json] [--locale ru|en|zh|vi|id|ms] [--out qa.json]
  keys.json: [{"path": "market.sam_2030", "fmt": "money_bn"}, ...]  (or "key_facts" inside facts.json)
Exit code 1 if any error.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmt_utils import NBSP, dump_json, format_value, get_path, load_json  # noqa: E402
from locales import get_locale, is_cjk_locale, norm_locale  # noqa: E402
from textfit import has_cjk, text_height_in, text_units  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BANNED_DEFAULT = os.path.join(HERE, "..", "config", "banned_phrases.json")
SRC_WORDS = r"(Источник|Источники|Source|Sources|Данные|Data|资料来源|数据来源|来源|Nguồn|Sumber)"
SOURCE_RE = re.compile(r"^\s*" + SRC_WORDS + r"\s*[:：]", re.I)
SOURCE_ANY_RE = re.compile(SRC_WORDS + r"\s*[:：]", re.I)
# number + unit; the look-behind excludes only Latin letters/digits so that numbers inside Chinese text match
NUM_UNIT_RE = re.compile(
    r"(?<![0-9A-Za-z.,%])(?:Rp|RM|US\$|\$)?[+\-−–]?\d{1,3}(?:[ \u00a0,.]\d{3})*(?:[.,]\d+)?[ \u00a0]?"
    r"(?:%|x|×|млрд|млн|трлн|тыс\.|₽|\$|мес\.|п\.\s?п\.|bn|mn|K|M|B|万亿|亿元|万元|亿|万|元|倍|个百分点|个月"
    r"|nghìn tỷ|tỷ|triệu|₫|lần|điểm %|tháng|triliun|miliar|juta|bilion|ribu|bulan)"
)
EMU_PER_IN = 914400


def norm(s: str) -> str:
    return re.sub(r"[ \u00a0\u202f]+", " ", s or "").replace("−", "-").replace("–", "-").strip().lower()


class Findings:
    def __init__(self):
        self.items = []

    def add(self, severity, where, check, message):
        self.items.append({"severity": severity, "where": where, "check": check, "message": message})

    def count(self, sev):
        return sum(1 for i in self.items if i["severity"] == sev)


def load_banned(path, lang):
    """Banned phrases for the locale + English (English hype words also appear in RU/ZH decks)."""
    cfg = load_json(path)
    lang = norm_locale(lang)
    phrases = cfg.get(lang, []) + (cfg.get("en", []) if lang != "en" else [])
    allow = cfg.get("allow_if_sourced", [])
    if isinstance(allow, dict):
        allow = allow.get(lang, []) + (allow.get("en", []) if lang != "en" else [])
    return [p.lower() for p in phrases], [p.lower() for p in allow]


def _phrase_re(ph):
    # CJK has no word boundaries: plain substring; otherwise require a non-word char before the phrase
    return re.escape(ph) if has_cjk(ph) else r"(?<![\w])" + re.escape(ph)


def check_banned(text, banned, where, f: Findings, has_source=False, allow=None):
    t = norm(text)
    for ph in banned:
        if re.search(_phrase_re(ph), t):
            f.add("warning", where, "banned_phrase", f"unverifiable / hype phrase: '{ph}' — replace with a measured claim")
    if allow and not has_source:
        for ph in allow:
            if re.search(_phrase_re(ph), t):
                f.add("info", where, "claim_needs_source", f"'{ph}' is acceptable only with a source on the same slide/paragraph")


# ----------------------------------------------------------------------------- PPTX
def _drawing_ea_stats(slide):
    """(runs with text, runs whose rPr carries an <a:ea> typeface) on one slide."""
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    n = n_ea = 0
    for r in slide.shapes._spTree.iter(f"{A}r"):
        t = r.find(f"{A}t")
        if t is None or not (t.text or "").strip():
            continue
        n += 1
        rpr = r.find(f"{A}rPr")
        if rpr is not None and rpr.find(f"{A}ea") is not None:
            n_ea += 1
    return n, n_ea


def qa_pptx(path, banned, lang, f: Findings, allow=None) -> dict:
    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation(path)
    sw, sh = prs.slide_width / EMU_PER_IN, prs.slide_height / EMU_PER_IN
    stats = {"slides": 0, "native_charts": 0, "charts_with_workbook": 0, "pictures": 0, "tables": 0,
             "data_slides": 0, "data_slides_with_source": 0, "runs": 0, "runs_with_ea_font": 0, "text": []}
    cjk = is_cjk_locale(lang)
    for idx, slide in enumerate(prs.slides, 1):
        stats["slides"] += 1
        where = f"slide {idx}"
        texts, title, has_source, has_chart, has_table, has_big = [], None, False, False, False, False
        n_pics, words, bullets = 0, 0, 0
        is_glossary = any((s_.name or "").startswith("GlossaryTerm") for s_ in slide.shapes)
        if is_glossary:
            stats["glossary_slides"] = stats.get("glossary_slides", 0) + 1
        for shp in slide.shapes:
            x, y = (shp.left or 0) / EMU_PER_IN, (shp.top or 0) / EMU_PER_IN
            w, h = (shp.width or 0) / EMU_PER_IN, (shp.height or 0) / EMU_PER_IN
            if shp.rotation in (0, 0.0) and (x < -0.01 or y < -0.01 or x + w > sw + 0.01 or y + h > sh + 0.01):
                f.add("warning", where, "off_slide", f"shape '{shp.name}' extends beyond the slide")
            if shp.has_chart if hasattr(shp, "has_chart") else False:
                has_chart = True
                stats["native_charts"] += 1
                try:
                    if shp.chart.part.chart_workbook.xlsx_part is not None:
                        stats["charts_with_workbook"] += 1
                    else:
                        f.add("error", where, "chart_no_data", "chart has no embedded workbook (not editable)")
                except Exception:
                    f.add("warning", where, "chart_no_data", "could not verify embedded workbook")
                continue
            if shp.shape_type is not None and int(shp.shape_type) == 13:  # PICTURE
                n_pics += 1
                stats["pictures"] += 1
                nm = (shp.name or "").lower()
                if any(k in nm for k in ("chart", "graph", "диаграм", "график", "plot")):
                    f.add("error", where, "chart_as_image", f"picture '{shp.name}' looks like a chart image — use a native chart")
                continue
            if getattr(shp, "has_table", False) and shp.has_table:
                has_table = True
                stats["tables"] += 1
                for row in shp.table.rows:
                    for cell in row.cells:
                        texts.append(cell.text)
                continue
            if not shp.has_text_frame:
                continue
            txt = shp.text_frame.text
            if not txt.strip():
                continue
            name = shp.name or ""
            if name == "Title" and title is None:
                title = txt
            if name == "Source" or SOURCE_RE.match(txt):
                has_source = True
            if name == "BigNumber":
                has_big = True
            if name not in ("PageNumber", "Watermark", "Source", "Disclaimer", "Verdict"):
                texts.append(txt)
                # scorecard rows are a structured list, not prose: score values do not count as words
                if name != "ScoreValue":
                    words += text_units(txt)
            sizes = [r.font.size.pt for p in shp.text_frame.paragraphs for r in p.runs if r.font.size]
            maxpt = max(sizes) if sizes else 18
            minpt = min(sizes) if sizes else 18
            bold = any(r.font.bold for p in shp.text_frame.paragraphs for r in p.runs)
            font = next((r.font.name for p in shp.text_frame.paragraphs for r in p.runs if r.font.name), None)
            npara = len(shp.text_frame.paragraphs)
            if name in ("Body", "Takeaway"):
                bullets = max(bullets, npara)
            est = text_height_in(txt, maxpt, w, font, bold, para_space_pt=maxpt * 0.5 if npara > 1 else 0)
            if h > 0 and est > h * 1.08:
                sev = "error" if est > h * 1.35 else "warning"
                f.add(sev, where, "text_overflow",
                      f"'{name}' text needs ~{est:.2f} in, box is {h:.2f} in ({maxpt:.0f} pt) — shorten or split")
            if minpt < 10 and name not in ("Source", "PageNumber", "Watermark", "Disclaimer", "Verdict"):
                f.add("warning", where, "small_font", f"'{name}' uses {minpt:.0f} pt (< 10 pt is unreadable in a room)")
        all_text = "\n".join(texts + ([title] if title and title not in texts else []))
        stats["text"].append(all_text)
        # title rules
        _decor = {"PageNumber", "Watermark", "Source", "Disclaimer", "Verdict", "Byline", "Motif", "Contact",
                  "TitleBar", "TitleRule", "TitleBand", "Rule", "NumberLabel", "NumberContext"}
        n_content = sum(1 for s_ in slide.shapes if (s_.name or "") not in _decor)
        is_cover = (idx == 1 or n_content <= 2) and not (has_chart or has_table or has_big)
        if not title:
            f.add("warning", where, "no_title", "slide has no title")
        elif not is_cover and not is_glossary:
            nw = text_units(title)   # words; CJK: characters / 2
            if nw < 4:
                f.add("warning", where, "label_title", f"title '{title}' is a label — write an action title (claim + number)")
            if nw > 22:
                f.add("warning", where, "long_title", f"title has ~{nw:.0f} words — keep action titles ≤ 2 lines")
        numeric_claims = len(NUM_UNIT_RE.findall(all_text))
        is_data = has_chart or has_table or has_big or numeric_claims >= 2
        if is_data and not is_cover:
            stats["data_slides"] += 1
            if has_source:
                stats["data_slides_with_source"] += 1
            else:
                f.add("error", where, "missing_source", "data slide without a source line ('Source: …' / 'Источник: …' / '资料来源：…')")
        if n_pics and not has_chart and is_data:
            f.add("warning", where, "picture_on_data_slide", "picture on a data slide — confirm it is not a chart screenshot")
        if words > 130 and not is_glossary:
            f.add("warning", where, "dense", f"{words} words on slide — move detail to notes or the report")
        if bullets > 7:
            f.add("warning", where, "too_many_bullets", f"{bullets} bullet paragraphs in one text box — max 5–6")
        if "{{" in all_text:
            f.add("error", where, "placeholder", "unresolved {{placeholder}}")
        if re.search(r"lorem ipsum|xx[,.]x|\?\?\?|TODO|TBD", all_text, re.I):
            f.add("error", where, "dummy_text", "dummy text / TODO left on slide")
        check_banned(all_text, banned, where, f, has_source, allow)
        nr, nea = _drawing_ea_stats(slide)
        stats["runs"] += nr
        stats["runs_with_ea_font"] += nea
        if cjk and has_cjk(all_text) and nea < nr:
            f.add("error", where, "cjk_font", f"{nr - nea} text run(s) without an East Asian font (<a:ea>) — CJK may render with a fallback font")
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        if not notes.strip() and not is_cover:
            f.add("info", where, "no_notes", "no speaker notes")
    return stats


# ----------------------------------------------------------------------------- DOCX
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W, "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
      "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _ptext(p):
    return "".join(t.text or "" for t in p.iter(f"{{{W}}}t"))


def qa_docx(path, banned, lang, f: Findings, expected_font=None, allow=None) -> dict:
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read("word/document.xml"))
    rels = etree.fromstring(z.read("word/_rels/document.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    body = doc.find(f"{{{W}}}body")
    stats = {"charts_native": 0, "charts_with_workbook": 0, "pictures": 0, "tables": 0, "footnotes": 0,
             "headings": 0, "objects_without_source": 0, "text": ""}
    elems = list(body)
    texts = []
    for i, el in enumerate(elems):
        tag = etree.QName(el).localname
        if tag == "p":
            t = _ptext(el)
            texts.append(t)
            sty = el.find("w:pPr/w:pStyle", NS)
            if sty is not None and sty.get(f"{{{W}}}val", "").lower().startswith("heading"):
                stats["headings"] += 1
                if not t.strip():
                    f.add("warning", f"paragraph {i}", "empty_heading", "empty heading")
            charts = el.findall(".//c:chart", NS)
            pics = el.findall(".//pic:pic", NS)
            for c in charts:
                stats["charts_native"] += 1
                target = rmap.get(c.get(f"{{{NS['r']}}}id"), "")
                cpath = "word/" + target.lstrip("/").replace("word/", "") if not target.startswith("/") else target.lstrip("/")
                crels = cpath.replace("charts/", "charts/_rels/") + ".rels"
                if crels in z.namelist() and b"package" in z.read(crels):
                    stats["charts_with_workbook"] += 1
                else:
                    f.add("error", f"chart in paragraph {i}", "chart_no_data", "Word chart without embedded workbook")
            for pc in pics:
                stats["pictures"] += 1
                dp = el.find(".//wp:docPr", NS)
                descr = ((dp.get("descr") or "") + " " + (dp.get("name") or "")).lower() if dp is not None else ""
                if any(k in descr for k in ("chart", "graph", "диаграм", "график", "plot")):
                    f.add("error", f"paragraph {i}", "chart_as_image", "picture looks like a chart image — use a native chart")
            if charts or pics:
                nxt = " ".join(_ptext(e) for e in elems[i + 1:i + 4] if etree.QName(e).localname == "p")
                if not SOURCE_ANY_RE.search(nxt):
                    stats["objects_without_source"] += 1
                    f.add("error", f"figure after paragraph {i}", "missing_source", "chart/figure without a source line")
        elif tag == "tbl":
            stats["tables"] += 1
            texts.append(" ".join(_ptext(p) for p in el.iter(f"{{{W}}}p")))
            nxt = " ".join(_ptext(e) for e in elems[i + 1:i + 3] if etree.QName(e).localname == "p")
            # key-figure panels and call-outs (1–2 rows) are exempt unless they contain numbers
            rows = el.findall("w:tr", NS)
            cells_text = " ".join(_ptext(p) for p in el.iter(f"{{{W}}}p"))
            numeric = bool(NUM_UNIT_RE.search(cells_text)) or bool(re.search(r"\d", cells_text))
            if len(rows) >= 2 and numeric and not SOURCE_ANY_RE.search(nxt):
                stats["objects_without_source"] += 1
                f.add("warning", f"table {stats['tables']}", "missing_source", "numeric table without a source line")
    if "word/footnotes.xml" in z.namelist():
        fx = etree.fromstring(z.read("word/footnotes.xml"))
        stats["footnotes"] = sum(1 for fn in fx.findall("w:footnote", NS) if int(fn.get(f"{{{W}}}id")) > 0)
    full = "\n".join(texts)
    stats["text"] = full
    if "{{" in full:
        f.add("error", "document", "placeholder", "unresolved {{placeholder}} in report")
    if re.search(r"lorem ipsum|\?\?\?|TODO|TBD", full, re.I):
        f.add("error", "document", "dummy_text", "dummy text / TODO in report")
    for i, para in enumerate(texts):
        nxt = texts[i + 1] if i + 1 < len(texts) else ""
        check_banned(para, banned, f"report paragraph {i}", f, bool(SOURCE_ANY_RE.search(para + " " + nxt)), allow)
    if stats["headings"] == 0:
        f.add("warning", "document", "no_headings", "no Heading styles — navigation pane and TOC will be empty")
    fonts = set(re.findall(rb'w:ascii="([^"]+)"', z.read("word/document.xml")))
    stats["fonts"] = sorted(x.decode() for x in fonts)
    styles = z.read("word/styles.xml") if "word/styles.xml" in z.namelist() else b""
    ea = set(re.findall(rb'<w:rFonts\b[^>]*?w:eastAsia="([^"]+)"', z.read("word/document.xml") + styles))
    stats["fonts_east_asian"] = sorted(x.decode() for x in ea)
    stats["lang_east_asia"] = bool(re.search(rb'w:eastAsia="zh-CN"', styles))
    if is_cjk_locale(lang):
        latin_only = {"Times New Roman", "Arial", "Calibri", "Cambria"}
        if not (set(stats["fonts_east_asian"]) - latin_only):
            f.add("error", "document", "cjk_font", "no East Asian font (w:eastAsia) set — Chinese text may render with a fallback font")
        if not stats["lang_east_asia"]:
            f.add("warning", "document", "cjk_lang", "Normal style lacks w:lang eastAsia=zh-CN (line breaking/proofing)")
    if expected_font and stats["fonts"] and any(x != expected_font for x in stats["fonts"]):
        f.add("info", "document", "mixed_fonts", f"fonts used: {stats['fonts']}")
    if stats["charts_native"] == 0 and stats["pictures"] > 0:
        f.add("warning", "document", "no_native_charts", "report has pictures but no native charts")
    return stats


# ----------------------------------------------------------------------------- consistency
def consistency(deck_text, report_text, facts, keys, lang, currency, f: Findings) -> dict:
    out = {"key_facts_checked": 0, "key_facts_missing": [], "deck_numbers": 0, "deck_numbers_not_in_report": []}
    nd, nr = norm(deck_text), norm(report_text)
    for k in keys or []:
        try:
            val = format_value(get_path(facts, k["path"]), k.get("fmt"), {"locale": lang, "currency": currency})
        except Exception as e:
            f.add("warning", "facts", "key_fact_path", f"{k.get('path')}: {e}")
            continue
        out["key_facts_checked"] += 1
        v = norm(val)
        miss = [name for name, txt in (("deck", nd), ("report", nr)) if v not in txt]
        if miss:
            out["key_facts_missing"].append({"path": k["path"], "value": val, "missing_in": miss})
            f.add("warning", "consistency", "key_fact_missing", f"{k['path']} = '{val}' not found in: {', '.join(miss)}")
    nums = {norm(m.group(0)) for m in NUM_UNIT_RE.finditer(deck_text)}
    out["deck_numbers"] = len(nums)
    for n in sorted(nums):
        if n in nr:
            continue
        bare = re.search(r"[+\-]?\d[\d ]*(?:[.,]\d+)?", n)
        if bare and re.search(r"(?<![\d,.])" + re.escape(bare.group(0).strip()) + r"(?![\d])", nr):
            out.setdefault("deck_numbers_matched_without_unit", []).append(n)
            continue
        out["deck_numbers_not_in_report"].append(n)
    if out["deck_numbers_not_in_report"]:
        f.add("warning", "consistency", "deck_number_not_in_report",
              f"{len(out['deck_numbers_not_in_report'])} number(s) on slides not found in the report: "
              + ", ".join(out["deck_numbers_not_in_report"][:12]))
    return out



# ---------------------------------------------------------------- completeness (autonomous data mode)
GAP_PATTERNS = [
    r"\bdata gaps?\b", r"\bmissing data\b", r"\bmarked as gaps?\b", r"\bno data\b", r"\bTBD\b", r"\bTBC\b",
    r"\[\[\s*gap\s*\]\]", r"\bgaps? in (?:the )?data\b", r"\binsufficient data\b", r"\bdata (?:is|are) (?:not available|unavailable)\b",
    r"нет данных", r"пробел\w* в данных", r"\bпробел\w*\b", r"недостающ\w* данн\w*", r"отсутству\w* данн\w*",
    r"данн\w* отсутству\w*", r"нет информации", r"данных нет",
    r"数据缺口", r"缺少数据", r"暂无数据", r"数据不足", r"待补充",
    r"thiếu dữ liệu", r"không có dữ liệu", r"chưa có dữ liệu", r"khoảng trống dữ liệu",
    r"kekurangan data", r"tidak ada data", r"data tidak tersedia", r"kesenjangan data", r"jurang data", r"tiada data", r"belum ada data",
]
SIZING_TERMS = [r"\bTAM\b", r"\bSAM\b", r"\bSOM\b"]
CAGR_TERMS = [r"\bCAGR\b", r"среднегодов\w* темп", r"复合(?:年)?增长率", r"tăng trưởng kép", r"pertumbuhan majemuk",
              r"kadar pertumbuhan tahunan kompaun"]
UE_TERMS = [r"LTV\s*/\s*CAC", r"\bCAC\b", r"юнит-экономик\w*", r"unit economics", r"单位经济", r"kinh tế đơn vị",
            r"ekonomi unit"]
ROI_TERMS = [r"\bROI\b", r"\bpayback\b", r"окупаемост\w*", r"回本", r"投资回报", r"hoàn vốn", r"pengembalian modal",
             r"tempoh bayar balik", r"balik modal", r"\bTCO\b"]


def _has(text, pats):
    return [p for p in pats if re.search(p, text, re.I)]


def completeness(deck_text: str, report_text: str, f: "Findings", pattern: dict | None = None,
                 n_slides: int | None = None) -> dict:
    """FAIL when the pitch has no market sizing, no CAGR, no unit economics, or contains data-gap placeholders.
    For customer patterns (corporate / smb) a deck checked alone must carry customer ROI / payback instead."""
    both = (deck_text or "") + "\n" + (report_text or "")
    customer = bool(pattern and pattern.get("kind") == "customer")
    res = {"sizing": _has(both, SIZING_TERMS), "cagr": _has(both, CAGR_TERMS), "unit_economics": _has(both, UE_TERMS),
           "roi": _has(both, ROI_TERMS), "gaps": []}
    deck_only = bool(deck_text) and not report_text
    if len(res["sizing"]) < 2 and not (customer and deck_only):
        f.add("error", "pitch", "no_market_sizing", "no TAM/SAM/SOM found — run estimator.py (top-down + bottom-up) "
              "and put the sizing in the deck or report")
    if not res["cagr"] and not (customer and deck_only):
        f.add("error", "pitch", "no_cagr", "no CAGR found — estimate it (estimator.cagr_from_drivers) and show it")
    if not res["unit_economics"] and not (customer and deck_only):
        f.add("error", "pitch", "no_unit_economics", "no unit economics (LTV/CAC, CAC, payback) — use "
              "estimator.unit_economics with benchmark ranges labelled as estimates")
    if customer and not res["roi"]:
        f.add("error", "pitch", "no_customer_roi", "customer pattern without customer ROI / payback / TCO "
              "(metrics_calc.customer_roi / customer_tco)")
    for where, txt in (("deck", deck_text), ("report", report_text)):
        for p in GAP_PATTERNS:
            for m in re.finditer(p, txt or "", re.I):
                ctx = (txt[max(0, m.start() - 40): m.end() + 40]).replace("\n", " ")
                res["gaps"].append({"where": where, "match": m.group(0), "context": ctx})
                f.add("error", where, "data_gap_placeholder",
                      f"data-gap placeholder '{m.group(0)}' — estimate the figure with a stated method instead "
                      f"(…{ctx}…)")
    if pattern and deck_text:
        for term in pattern.get("mandatory_terms", []):
            if not re.search(term, deck_text, re.I):
                f.add("error", "deck", "pattern_mandatory_metric",
                      f"pattern '{pattern.get('id')}' requires '{term}' in the deck")
        dl = pattern.get("deck_length") or {}
        if n_slides and dl:
            if n_slides < dl.get("min", 0) or n_slides > dl.get("max", 999):
                f.add("warning", "deck", "pattern_deck_length",
                      f"{n_slides} slides; pattern '{pattern.get('id')}' expects {dl.get('min')}–{dl.get('max')}")
    return res


def qa_glossary(pptx=None, docx=None, lang="en", f: "Findings" = None) -> dict:
    """The glossary must exist and cover every metric the document shows (config/glossary.json)."""
    import glossary as G
    res = {}
    if pptx:
        from pptx import Presentation
        prs = Presentation(pptx)
        shown = G.detect([t for _, g, t in G.pptx_slide_texts(prs) if not g], lang)
        slides, ids = G.pptx_glossary_ids(prs)
        missing = [m for m in shown if m not in ids]
        res["pptx"] = {"shown": shown, "listed": ids, "slides": slides, "missing": missing}
        if shown and not slides:
            f.add("error", "deck", "glossary_missing",
                  f"no 'What the numbers mean' slide, but the deck shows {', '.join(shown)} — rebuild with build_pptx")
        elif missing:
            f.add("error", "deck", "glossary_incomplete", f"glossary does not explain: {', '.join(missing)}")
        if slides and slides[0] != 2:
            f.add("warning", f"slide {slides[0]}", "glossary_position", "glossary should follow the title slide")
    if docx:
        with open(docx, "rb") as fh:
            parts = G.docx_parts(fh.read())
        shown = G.detect(parts["text"], lang)
        listed = [G.term_to_id(t, lang) or G.term_to_id(t) for t in parts["terms"]]
        missing = [m for m in shown if m not in listed]
        res["docx"] = {"shown": shown, "listed": listed, "missing": missing}
        if shown and not parts["has_glossary"]:
            f.add("error", "report", "glossary_missing",
                  f"no 'What the numbers mean' section, but the report shows {', '.join(shown)} — rebuild with build_docx")
        elif missing:
            f.add("error", "report", "glossary_incomplete", f"glossary section does not explain: {', '.join(missing)}")
        if parts["has_glossary"] and parts["headings_before"] > 1:
            f.add("warning", "report", "glossary_position", "glossary section should come before the main sections")
    return res


def load_pattern(pattern):
    """Pattern id or dict → dict (patterns/patterns.json)."""
    if not pattern:
        return None
    if isinstance(pattern, dict):
        return pattern
    here = os.path.dirname(os.path.abspath(__file__))
    pj = load_json(os.path.join(here, "..", "patterns", "patterns.json"))
    p = dict(pj["patterns"][pattern])
    p["id"] = pattern
    return p


def run_qa(pptx=None, docx=None, facts=None, key_facts=None, banned=None, language="ru", currency=None,
           expected_font=None, locale=None, pattern=None, completeness_check=True, glossary_check=True) -> dict:
    language = norm_locale(locale or language)
    pat = load_pattern(pattern)
    currency = currency or get_locale(language)["currency"]
    f = Findings()
    banned_list, allow = load_banned(banned or BANNED_DEFAULT, language)
    res = {"locale": language}
    if pptx:
        res["pptx"] = qa_pptx(pptx, banned_list, language, f, allow)
    if docx:
        res["docx"] = qa_docx(docx, banned_list, language, f, expected_font, allow)
    if pptx and docx:
        fx = load_json(facts) if facts else {}
        keys = load_json(key_facts) if key_facts else fx.get("key_facts", [])
        res["consistency"] = consistency("\n".join(res["pptx"]["text"]), res["docx"]["text"], fx, keys,
                                         language, currency, f)
    if completeness_check and (pptx or docx):
        res["completeness"] = completeness("\n".join(res["pptx"]["text"]) if pptx else "",
                                           res["docx"]["text"] if docx else "", f, pat,
                                           (res["pptx"].get("slides") - res["pptx"].get("glossary_slides", 0)) if pptx else None)
    if glossary_check and (pptx or docx):
        res["glossary"] = qa_glossary(pptx, docx, language, f)
    for k in ("pptx", "docx"):
        if k in res:
            res[k].pop("text", None)
    res["findings"] = f.items
    res["summary"] = {"errors": f.count("error"), "warnings": f.count("warning"), "info": f.count("info"),
                      "pass": f.count("error") == 0}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pptx")
    ap.add_argument("--docx")
    ap.add_argument("--facts")
    ap.add_argument("--key-facts")
    ap.add_argument("--banned")
    ap.add_argument("--locale", "-l", "--language", dest="language", default="ru", choices=["ru", "en", "zh", "vi", "id", "ms"])
    ap.add_argument("--currency", help="default: locale currency (RUB / USD / CNY)")
    ap.add_argument("--font")
    ap.add_argument("--pattern", help="pitch pattern id (patterns/patterns.json): mandatory metrics, deck length")
    ap.add_argument("--no-completeness", action="store_true", help="skip the market sizing / CAGR / unit economics / gap check")
    ap.add_argument("--no-glossary", action="store_true", help="skip the 'What the numbers mean' coverage check")
    ap.add_argument("--out", "-o")
    a = ap.parse_args(argv)
    res = run_qa(a.pptx, a.docx, a.facts, a.key_facts, a.banned, a.language, a.currency, a.font,
                 pattern=a.pattern, completeness_check=not a.no_completeness, glossary_check=not a.no_glossary)
    print(dump_json(res, a.out))
    return 1 if res["summary"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
