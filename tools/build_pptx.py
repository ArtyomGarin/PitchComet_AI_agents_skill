#!/usr/bin/env python3
"""build_pptx.py — minimalist strategic deck (.pptx, 16:9) from a JSON slide spec.

Native, editable PowerPoint charts with embedded Excel data; source line on data slides;
speaker notes; light/dark (or custom) themes; text auto-fit by estimation.

Spec:
{
  "meta": {"title": "...", "author": "...", "locale": "ru" | "en" | "zh" | "vi" | "id" | "ms", "theme": "light" | "dark" | {...overrides},
           "font_heading": "Arial", "font_body": "Arial", "slide_numbers": true,
           "watermark": "ПРИМЕР · вымышленные данные", "facts": "facts.json"},
  "slides": [
    {"layout": "title", "title": "...", "subtitle": "...", "date": "...", "notes": "..."},
    {"layout": "section", "number": "01", "title": "..."},
    {"layout": "statement", "title": "action title", "text": "...", "source": "..."},
    {"layout": "bullets", "title": "...", "bullets": ["**bold** lead — detail", {"text": "...", "level": 1}]},
    {"layout": "big_number", "title": "...", "numbers": [{"value": "12,4 млрд ₽", "label": "...", "context": "..."}]},
    {"layout": "chart", "title": "...", "chart": {<charts_common spec>}, "takeaway": ["..."], "source": "..."},
    {"layout": "table", "title": "...", "columns": [...], "rows": [[...]], "col_widths": [..], "highlight_row": 0},
    {"layout": "two_column", "title": "...", "left": {"heading": "...", "bullets": [...]}, "right": {...}},
    {"layout": "timeline", "title": "...", "steps": [{"label": "Q1 2026", "title": "...", "text": "..."}]},
    {"layout": "scorecard", "title": "...", "criteria": [{"name": "...", "weight": 14, "score": 3.5}],
     "total": 68.4, "grade": "B", "grade_label": "...", "range": [61, 74]},
    {"layout": "matrix", "title": "...", "x_label": "...", "y_label": "...", "quadrants": ["", "", "", ""],
     "items": [{"name": "...", "x": 0.7, "y": 0.8, "highlight": true}]},
    {"layout": "closing", "title": "...", "bullets": [...], "contact": "..."}
    {"layout": "glossary", "title": "...", "items": [{"id": "tam", "term": "TAM", "text": "..."}]}
       — inserted automatically after the title slide (tools/glossary.py, config/glossary.json):
         only the metrics the deck shows, in plain words; meta.glossary = false switches it off
  ]
}
Placeholders {{path|fmt}} / {"$ref": path} are resolved from meta.facts (see fmt_utils.py).

CLI: python build_pptx.py --input deck_spec.json --out deck.pptx [--theme dark] [--facts facts.json]
Prints a JSON build report (slides, charts, fit warnings).
"""
from __future__ import annotations

import argparse
import copy
import math
import json
import os
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from charts_common import add_ea_fonts, fix_axis_ids, prepare, set_chart_lang, style_chart  # noqa: E402
from fmt_utils import dump_json, fmt_number, load_json, resolve_placeholders  # noqa: E402
from ooxml_clean import clean_package  # noqa: E402
from locales import disclaimer, get_locale, locale_of, verdict_label  # noqa: E402
from textfit import fit_font_size, text_width_em  # noqa: E402
import glossary  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES_FILE = os.path.join(HERE, "..", "config", "themes.json")

W, H = 13.333, 7.5
M = 0.6
TITLE_Y, TITLE_H = 0.45, 1.05
BODY_Y, BODY_B = 1.75, 6.6
FOOT_Y = 6.88
SOURCE_PREFIX_RE = re.compile(r"^(Источник|Источники|Source|Sources|资料来源|来源|数据来源|Nguồn|Sumber)")


def _rgb(h):
    return RGBColor.from_string(h.replace("#", "").upper())


def load_theme(theme, font_heading=None, font_body=None, locale=None) -> dict:
    themes = load_json(THEMES_FILE)
    if isinstance(theme, dict):
        base = copy.deepcopy(themes.get(theme.get("base", "light"), themes["light"]))
        base.update({k: v for k, v in theme.items() if k != "base"})
        t = base
    elif isinstance(theme, str) and os.path.isfile(theme):
        t = load_json(theme)
    else:
        t = copy.deepcopy(themes.get(theme or "light", themes["light"]))
    if locale:   # per-locale font defaults (theme "fonts" → themes.json "locale_fonts" → locales.py)
        lf = dict((themes.get("locale_fonts") or {}).get(locale) or {})
        lf.update((t.get("fonts") or {}).get(locale) or {})
        F = get_locale(locale)["fonts"]
        t.setdefault("font_ea", lf.get("font_ea") or F.get("deck_ea"))
        if lf.get("font_heading"):
            t["font_heading"] = lf["font_heading"]
        if lf.get("font_body"):
            t["font_body"] = lf["font_body"]
    if font_heading:
        t["font_heading"] = font_heading
    if font_body:
        t["font_body"] = font_body
    return t



class DeckBuilder:
    def __init__(self, spec: dict, theme: dict):
        self.spec = spec
        self.meta = spec.get("meta", {})
        self.lang = locale_of(self.meta)
        self.loc = get_locale(self.lang)
        self.L = self.loc["labels"]
        self.t = theme
        self.t.setdefault("font_ea", self.loc["fonts"].get("deck_ea"))
        if self.meta.get("font_ea"):
            self.t["font_ea"] = self.meta["font_ea"]
        self.prs = Presentation()
        self.prs.slide_width = Inches(W)
        self.prs.slide_height = Inches(H)
        self.blank = self.prs.slide_layouts[6]
        self.report = {"slides": [], "warnings": [], "charts": 0}
        self.page = 0

    # ------------------------------------------------------------- primitives
    def _bg(self, slide, color=None):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = _rgb(color or self.t["bg"])

    def _text(self, slide, x, y, w, h, text, size=16, bold=False, color=None, font=None, align="left",
              anchor="top", name=None, min_size=None, para_space=0, italic=False, line_spacing=None):
        font = font or self.t["font_body"]
        if min_size:
            fitted, ok = fit_font_size(text, w, h, size, min_size, font, bold, para_space)
            if not ok:
                self.report["warnings"].append(f"slide {self.page}: text may overflow box '{name or text[:30]}'")
            size = fitted
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        if name:
            tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = Inches(0.0)
        tf.margin_top = tf.margin_bottom = Inches(0.03)
        tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[anchor]
        for i, line in enumerate(str(text).split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
            if para_space and i > 0:
                p.space_before = Pt(para_space)
            if line_spacing:
                p.line_spacing = line_spacing
            self._runs(p, line, size, bold, color or self.t["text"], font, italic)
        return tb

    def _runs(self, p, text, size, bold, color, font, italic=False):
        parts = re.split(r"(\*\*[^*]+\*\*)", text)
        for part in parts:
            if not part:
                continue
            r = p.add_run()
            is_b = part.startswith("**") and part.endswith("**")
            r.text = part[2:-2] if is_b else part
            r.font.size = Pt(size)
            r.font.bold = bold or is_b
            r.font.italic = italic
            r.font.name = font
            r.font.color.rgb = _rgb(color)

    def _bullets(self, slide, x, y, w, h, items, size=18, min_size=13, name="Body", color=None):
        flat = []
        for it in items:
            if isinstance(it, dict):
                flat.append((it.get("text", ""), int(it.get("level", 0))))
            else:
                flat.append((str(it), 0))
        plain = "\n".join(t.replace("**", "") for t, _ in flat)
        size, ok = fit_font_size(plain, w - 0.35, h, size, min_size, self.t["font_body"], False, para_space_pt=size * 0.55)
        if not ok:
            self.report["warnings"].append(f"slide {self.page}: bullet list may overflow; cut text or split slide")
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = Inches(0)
        for i, (text, lvl) in enumerate(flat):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.level = 0
            s = size if lvl == 0 else max(size - 2, min_size)
            if i > 0:
                p.space_before = Pt(size * 0.55)
            pPr = p._p.get_or_add_pPr()
            indent = 0.28 + 0.3 * lvl
            pPr.set("marL", str(int(Inches(indent))))
            pPr.set("indent", str(int(-Inches(0.28))))
            for tag in ("a:buClr", "a:buSzPct", "a:buFont", "a:buChar", "a:buNone"):
                for el in pPr.findall(qn(tag)):
                    pPr.remove(el)
            buClr = pPr.makeelement(qn("a:buClr"), {})
            srgb = buClr.makeelement(qn("a:srgbClr"), {"val": self.t["accent"]})
            buClr.append(srgb)
            pPr.append(buClr)
            pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
            pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "–" if lvl else "•"}))
            self._runs(p, text, s, False, color or (self.t["text"] if lvl == 0 else self.t["muted"]), self.t["font_body"])
        return tb

    def _rect(self, slide, x, y, w, h, color, name=None, shape=MSO_SHAPE.RECTANGLE, line=None):
        s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        s.fill.solid()
        s.fill.fore_color.rgb = _rgb(color)
        if line:
            s.line.color.rgb = _rgb(line)
            s.line.width = Pt(0.75)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        if name:
            s.name = name
        return s

    def _title(self, slide, text, y=TITLE_Y, h=TITLE_H, size=None, min_size=20):
        """Action title. Theme keys: title_style plain | rule | bar | band, title_size, title_color."""
        style = self.t.get("title_style", "plain")
        size = size or self.t.get("title_size", 28)
        color = self.t.get("title_color")
        x, w = M, W - 2 * M
        if style == "band" and y == TITLE_Y:
            self._rect(slide, 0, 0, W, y + h + 0.05, self.t.get("title_band", self.t["accent"]), name="TitleBand")
            color = self.t.get("title_band_text", "FFFFFF")
        elif style == "bar" and y == TITLE_Y:
            self._rect(slide, M, y + 0.06, 0.09, h - 0.2, self.t["accent"], name="TitleBar")
            x, w = M + 0.3, W - 2 * M - 0.3
        elif style == "rule" and y == TITLE_Y:
            self._rect(slide, M, y + h + 0.02, 1.4, 0.05, self.t["accent"], name="TitleRule")
        return self._text(slide, x, y, w, h, text, size=size, bold=True, font=self.t["font_heading"],
                          name="Title", min_size=min_size, anchor="top", line_spacing=0.95, color=color)

    def _footer(self, slide, s):
        src = s.get("source")
        ver = s.get("verdict")
        if ver:
            lab = verdict_label(self.lang)
            sep = "：" if self.lang == "zh" else ": "
            self._rect(slide, M, 6.42, 0.05, 0.42, self.t["accent"], name="VerdictRule")
            self._text(slide, M + 0.2, 6.42, W - 2 * M - 0.2, 0.42, f"**{lab}{sep}** {ver}", size=10,
                       color=self.t["text"], name="Verdict", min_size=8)
        if src:
            lab = self.L["source"]
            sep = "：" if self.lang == "zh" else ": "
            txt = src if SOURCE_PREFIX_RE.match(src) else f"{lab}{sep}{src}"
            self._text(slide, M, FOOT_Y, W - 2 * M - 1.0, 0.42, txt, size=10, color=self.t["muted"], name="Source",
                       min_size=8)
        if self.meta.get("slide_numbers", True) and s.get("layout") not in ("title",):
            self._text(slide, W - M - 0.8, FOOT_Y, 0.8, 0.3, str(self.page), size=10, color=self.t["muted"],
                       align="right", name="PageNumber")
        if self.meta.get("watermark"):
            wm_col = self.t.get("title_band_text", self.t["muted"]) if self.t.get("title_style") == "band" \
                and s.get("layout") not in ("title", "section") else self.t["muted"]
            self._text(slide, W - M - 4.5, 0.12, 4.5, 0.28, self.meta["watermark"], size=9, color=wm_col,
                       align="right", name="Watermark")

    def _notes(self, slide, s):
        notes = s.get("notes", "")
        srcs = s.get("notes_sources") or []
        if srcs:
            notes += ("\n\n" if notes else "") + self.L["sources_inline"] + ("：\n" if self.lang == "zh" else ":\n") + "\n".join(f"- {x}" for x in srcs)
        if notes:
            notes += "\n\n"
        notes += disclaimer(self.lang)
        if notes:
            slide.notes_slide.notes_text_frame.text = notes

    def _chart(self, slide, x, y, w, h, cspec, base_pt=12):
        xl_type, data, norm = prepare(cspec)
        self.t["lang"] = self.lang
        gf = slide.shapes.add_chart(xl_type, Inches(x), Inches(y), Inches(w), Inches(h), data)
        gf.name = "Chart"
        style_chart(gf.chart, norm, self.t, base_pt)
        fix_axis_ids(gf.chart._chartSpace)
        set_chart_lang(gf.chart._chartSpace, self.lang)
        if self.t.get("font_ea"):
            add_ea_fonts(gf.chart._chartSpace, self.t["font_ea"], None, self.t["font_body"])
        self.report["charts"] += 1
        return gf

    # ------------------------------------------------------------- layouts
    def l_title(self, slide, s):
        """Cover. Theme key cover_style: plain (motif line) | full (cover_bg fill) | split (left colour panel)."""
        cs = self.t.get("cover_style", "plain")
        tcol, mcol, x0 = self.t["text"], self.t["muted"], M
        if cs == "full":
            self._bg(slide, self.t.get("cover_bg", self.t["accent"]))
            tcol = self.t.get("cover_text", "FFFFFF")
            mcol = self.t.get("cover_muted", tcol)
            self._rect(slide, M, 2.05, 1.6, 0.1, self.t.get("cover_motif", self.t.get("accent2", tcol)), name="Motif")
        elif cs == "split":
            self._rect(slide, 0, 0, 4.2, H, self.t.get("cover_bg", self.t["accent"]), name="CoverPanel")
            if s.get("kicker"):
                self._text(slide, 0.5, 0.6, 3.2, 1.2, s["kicker"], size=16, bold=True,
                           color=self.t.get("cover_text", "FFFFFF"), name="Kicker", min_size=11)
            x0 = 4.8
            self._rect(slide, x0, 2.05, 1.1, 0.08, self.t["accent"], name="Motif")
        else:
            self._rect(slide, M, 2.05, 1.1, 0.08, self.t["accent"], name="Motif")
        tw = W - x0 - M - (0.5 if cs == "split" else 1)
        self._text(slide, x0, 2.35, tw, 2.0, s["title"], size=self.t.get("cover_title_size", 40), bold=True,
                   font=self.t["font_heading"], name="Title", min_size=26, line_spacing=0.95, color=tcol)
        if s.get("subtitle"):
            self._text(slide, x0, 4.45, tw - (1 if cs != "split" else 0), 1.0, s["subtitle"], size=20, color=mcol,
                       name="Subtitle", min_size=14)
        line = " · ".join(x for x in [s.get("author"), s.get("org"), s.get("date")] if x)
        if line:
            self._text(slide, x0, 6.3, W - x0 - M, 0.4, line, size=12, color=mcol, name="Byline")
        self._text(slide, M, 6.95, W - 2 * M, 0.4, disclaimer(self.lang), size=8, color=mcol, name="Disclaimer",
                   min_size=7)

    def l_section(self, slide, s):
        if s.get("number"):
            self._text(slide, M, 2.0, 3, 1.2, s["number"], size=54, bold=True, color=self.t["accent"],
                       font=self.t["font_heading"], name="SectionNumber")
        self._text(slide, M, 3.25, W - 2 * M - 2, 1.6, s["title"], size=34, bold=True, font=self.t["font_heading"],
                   name="Title", min_size=24)
        if s.get("subtitle"):
            self._text(slide, M, 4.9, W - 2 * M - 3, 1.0, s["subtitle"], size=16, color=self.t["muted"], min_size=12)

    def l_statement(self, slide, s):
        self._title(slide, s["title"])
        self._text(slide, M, BODY_Y + 0.2, W - 2 * M - 1.5, BODY_B - BODY_Y - 0.3, s.get("text", ""), size=24,
                   name="Body", min_size=16, para_space=10, line_spacing=1.05)

    def l_bullets(self, slide, s):
        self._title(slide, s["title"])
        self._bullets(slide, M, BODY_Y, W - 2 * M - 1.0, BODY_B - BODY_Y, s.get("bullets", []))

    def l_big_number(self, slide, s):
        self._title(slide, s["title"])
        nums = s.get("numbers", [])[:4]
        n = max(len(nums), 1)
        gap = 0.45
        cw = (W - 2 * M - gap * (n - 1)) / n
        vsize = int({1: 88, 2: 66, 3: 54, 4: 44}[n] * float(self.t.get("big_number_scale", 1.0)))
        # big numbers stay on one line: shrink the common size until the widest value fits
        fh = self.t.get("font_numbers", self.t["font_heading"])
        # bold glyphs are wider than the regular-width estimate; serif display faces wider still
        serif = any(k in fh.lower() for k in ("georgia", "times", "serif", "garamond", "cambria", "simsun", "song"))
        widest = max((text_width_em(str(it["value"]), fh) * (1.35 if serif else 1.3) for it in nums), default=1.0)
        vsize = max(20, min(vsize, int((cw - 0.6) * 72 / max(widest, 0.1))))
        for i, it in enumerate(nums):
            x = M + i * (cw + gap)
            top = 2.1
            self._rect(slide, x, top, 0.06, 3.6, self.t["accent"] if i == 0 else self.t["grid"], name="Rule")
            self._text(slide, x + 0.3, top, cw - 0.3, 1.45, str(it["value"]), size=vsize, bold=True,
                       color=self.t["accent"] if (i == 0 or self.t.get("big_number_all_accent")) else self.t["text"],
                       font=self.t.get("font_numbers", self.t["font_heading"]), name="BigNumber", min_size=min(30, vsize))
            self._text(slide, x + 0.3, top + 1.6, cw - 0.3, 0.95, it.get("label", ""), size=18, bold=True,
                       name="NumberLabel", min_size=13)
            if it.get("context"):
                self._text(slide, x + 0.3, top + 2.55, cw - 0.3, 1.05, it["context"], size=13, color=self.t["muted"],
                           name="NumberContext", min_size=10)
        if s.get("text"):
            self._text(slide, M, 5.95, W - 2 * M, 0.6, s["text"], size=14, color=self.t["muted"], min_size=11)

    def l_chart(self, slide, s):
        self._title(slide, s["title"])
        tk = s.get("takeaway")
        if tk:
            cw = (W - 2 * M) * 0.64
            self._chart(slide, M - 0.1, BODY_Y, cw, BODY_B - BODY_Y, s["chart"])
            px = M + cw + 0.35
            pw = W - M - px
            if isinstance(tk, str):
                tk = [tk]
            self._rect(slide, px, BODY_Y + 0.1, 0.05, BODY_B - BODY_Y - 0.3, self.t["accent"], name="Rule")
            self._bullets(slide, px + 0.3, BODY_Y + 0.1, pw - 0.3, BODY_B - BODY_Y - 0.3, tk, size=16, min_size=11,
                          name="Takeaway")
        else:
            self._chart(slide, M - 0.1, BODY_Y, W - 2 * M + 0.2, BODY_B - BODY_Y, s["chart"])

    def l_table(self, slide, s):
        self._title(slide, s["title"])
        cols, rows = s["columns"], s["rows"]
        nr, nc = len(rows) + 1, len(cols)
        tw = W - 2 * M
        avail_h = BODY_B - BODY_Y
        rh = min(0.55, avail_h / nr)
        fsz = 14 if nr <= 7 else 12 if nr <= 10 else 10
        gf = slide.shapes.add_table(nr, nc, Inches(M), Inches(BODY_Y), Inches(tw), Inches(rh * nr))
        gf.name = "Table"
        tbl = gf.table
        # drop default table style banding visuals
        tblPr = tbl._tbl.tblPr
        tblPr.set("firstRow", "1")
        tblPr.set("bandRow", "0")
        widths = s.get("col_widths")
        if widths:
            tot = sum(widths)
            for i, wv in enumerate(widths):
                tbl.columns[i].width = Emu(int(Inches(tw) * wv / tot))
        hl = s.get("highlight_row")
        num_re = re.compile(r"^[\s+\-−–]?(?:Rp|RM|\$)?[\d\s.,]+\s*(%|x|×|млрд|млн|тыс\.?|₽|\$|мес\.?|лет|ч|дн\.?|п\.п\.|pp|bn|mn|K|M|B|万元|亿元|万|亿|元|倍|个百分点|个月|年|天|小时|nghìn tỷ|tỷ|triệu|₫|lần|điểm %|tháng|triliun|miliar|juta|bilion|ribu|bulan|hari|jam|giờ|ngày)?[\s\u00a0₽$¥₫]*$")
        num_cols = [c > 0 and all(bool(num_re.match(str(row[c]))) or str(row[c]) in ("", "—", "-") for row in rows)
                    for c in range(nc)]
        for r in range(nr):
            tbl.rows[r].height = Inches(rh)
            for c in range(nc):
                cell = tbl.cell(r, c)
                val = cols[c] if r == 0 else rows[r - 1][c]
                cell.text = ""
                tf = cell.text_frame
                tf.word_wrap = True
                cell.margin_left = cell.margin_right = Inches(0.08)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                p = tf.paragraphs[0]
                is_num = num_cols[c]
                p.alignment = PP_ALIGN.RIGHT if is_num else PP_ALIGN.LEFT
                if r == 0:
                    color, bold, fill = self.t["table_header_text"], True, self.t["table_header_bg"]
                elif hl is not None and r - 1 == hl:
                    color, bold, fill = self.t["text"], True, self.t["panel"]
                else:
                    color, bold, fill = self.t["text"], c == 0, self.t["bg"] if r % 2 else self.t["table_band"]
                self._runs(p, str(val), fsz, bold, color, self.t["font_body"])
                cell.fill.solid()
                cell.fill.fore_color.rgb = _rgb(fill)

    def l_two_column(self, slide, s):
        self._title(slide, s["title"])
        gap = 0.6
        cw = (W - 2 * M - gap) / 2
        for i, side in enumerate([s.get("left", {}), s.get("right", {})]):
            x = M + i * (cw + gap)
            self._rect(slide, x, BODY_Y, cw, 0.05, self.t["accent"] if i == 0 else self.t["muted"], name="Rule")
            self._text(slide, x, BODY_Y + 0.15, cw, 0.6, side.get("heading", ""), size=20, bold=True,
                       name="ColumnHeading", min_size=14)
            self._bullets(slide, x, BODY_Y + 0.85, cw, BODY_B - BODY_Y - 0.85, side.get("bullets", []), size=16,
                          min_size=11)

    def l_timeline(self, slide, s):
        self._title(slide, s["title"])
        steps = s.get("steps", [])[:6]
        n = max(len(steps), 1)
        y_line = 2.75
        self._rect(slide, M, y_line, W - 2 * M, 0.035, self.t["grid"], name="TimelineLine")
        cw = (W - 2 * M) / n
        for i, st in enumerate(steps):
            x = M + i * cw
            self._rect(slide, x, y_line - 0.13, 0.3, 0.3, self.t["accent"] if i == 0 or st.get("highlight") else self.t["accent2"],
                       name="Node", shape=MSO_SHAPE.OVAL)
            self._text(slide, x, 2.0, cw - 0.2, 0.5, st.get("label", ""), size=14, bold=True, color=self.t["accent"],
                       name="StepLabel", min_size=10)
            self._text(slide, x, 3.2, cw - 0.25, 0.9, st.get("title", ""), size=17, bold=True, name="StepTitle",
                       min_size=11)
            self._text(slide, x, 4.15, cw - 0.25, 2.3, st.get("text", ""), size=13, color=self.t["muted"],
                       name="StepText", min_size=10)

    def l_scorecard(self, slide, s):
        self._title(slide, s["title"])
        crit = s.get("criteria", [])
        n = max(len(crit), 1)
        top, bottom = BODY_Y, BODY_B
        rh = (bottom - top) / n
        name_w, bar_x = 4.6, M + 4.75
        bar_w = 4.3
        fsz = 13 if n <= 9 else 11
        for i, c in enumerate(crit):
            y = top + i * rh
            self._text(slide, M, y, name_w, rh, c["name"], size=fsz, name="CriterionName", anchor="middle",
                       min_size=9)
            self._rect(slide, bar_x, y + rh * 0.3, bar_w, rh * 0.4, self.t["panel"] if self.t["panel"] != self.t["bg"] else self.t["grid"],
                       name="BarTrack")
            frac = max(min(float(c["score"]) / 5.0, 1), 0)
            if frac > 0:
                col = self.t["accent"] if frac >= 0.6 else (self.t["muted_fill"] if frac >= 0.4 else self.t["negative"])
                self._rect(slide, bar_x, y + rh * 0.3, bar_w * frac, rh * 0.4, col, name="Bar")
            sc = fmt_number(c["score"], 1, self.lang)
            wt = fmt_number(c["weight"], 0 if float(c["weight"]).is_integer() else 1, self.lang)
            self._text(slide, bar_x + bar_w + 0.15, y, 1.4, rh, f"{sc} / 5 · {wt}%", size=fsz - 1,
                       color=self.t["muted"], name="ScoreValue", anchor="middle")
        px = M + 10.45
        self._text(slide, px, top, W - M - px, 0.62, s.get("total_label", self.L["total_score"]),
                   size=13, color=self.t["muted"], name="TotalLabel")
        tot = s.get("total")
        tot_s = (f"{tot:.0f}" if isinstance(tot, (int, float)) else str(tot))
        self._text(slide, px, top + 0.35, W - M - px, 1.3, tot_s, size=66, bold=True, color=self.t["accent"],
                   font=self.t["font_heading"], name="BigNumber")
        self._text(slide, px, top + 1.65, W - M - px, 0.4, self.L["of_100"], size=13,
                   color=self.t["muted"])
        if s.get("grade"):
            self._text(slide, px, top + 2.2, W - M - px, 0.6, f"{s['grade']}", size=28, bold=True, name="Grade")
        if s.get("grade_label"):
            self._text(slide, px, top + 2.8, W - M - px, 1.0, s["grade_label"], size=12, color=self.t["muted"],
                       min_size=9)
        if s.get("range"):
            lo, hi = s["range"]
            rl = f"{self.L['range']} {lo:.0f}–{hi:.0f}"
            self._text(slide, px, top + 3.85, W - M - px, 0.8, rl, size=12, color=self.t["muted"], min_size=9)

    def l_matrix(self, slide, s):
        self._title(slide, s["title"])
        gx, gy = M + 0.9, BODY_Y + 0.05
        gw, gh = 7.4, BODY_B - BODY_Y - 0.55
        q = s.get("quadrants", ["", "", "", ""])
        for i in range(4):
            qx = gx + (i % 2) * gw / 2
            qy = gy + (i // 2) * gh / 2
            self._rect(slide, qx, qy, gw / 2 - 0.04, gh / 2 - 0.04,
                       self.t["panel"] if i != 1 else self.t["grid"], name="Quadrant")
            if q[i]:
                self._text(slide, qx + 0.12, qy + 0.08, gw / 2 - 0.3, 0.4, q[i], size=11, color=self.t["muted"],
                           name="QuadrantLabel")
        self._text(slide, gx, gy + gh + 0.08, gw, 0.4, s.get("x_label", "") + "  →", size=12, color=self.t["muted"],
                   align="center", name="AxisLabel")
        yl = self._text(slide, M - 0.05, gy, 0.8, gh, s.get("y_label", "") + "  →", size=12, color=self.t["muted"],
                        align="center", anchor="middle", name="AxisLabel")
        yl.rotation = 270
        yl.left, yl.top, yl.width, yl.height = Inches(M + 0.4 - gh / 2), Inches(gy + gh / 2 - 0.2), Inches(gh), Inches(0.4)
        for it in s.get("items", []):
            cx = gx + float(it["x"]) * gw
            cy = gy + (1 - float(it["y"])) * gh
            d = 0.26 if it.get("highlight") else 0.2
            self._rect(slide, cx - d / 2, cy - d / 2, d, d, self.t["accent"] if it.get("highlight") else self.t["accent2"],
                       name="Item", shape=MSO_SHAPE.OVAL)
            self._text(slide, cx + 0.18, cy - 0.17, 2.6, 0.34, it["name"], size=12, bold=bool(it.get("highlight")),
                       name="ItemLabel")
        if s.get("takeaway"):
            px = gx + gw + 0.5
            tk = s["takeaway"] if isinstance(s["takeaway"], list) else [s["takeaway"]]
            self._bullets(slide, px, BODY_Y + 0.1, W - M - px, BODY_B - BODY_Y - 0.3, tk, size=15, min_size=11,
                          name="Takeaway")

    def l_closing(self, slide, s):
        self._title(slide, s["title"], size=32, min_size=22)
        if s.get("bullets"):
            self._bullets(slide, M, BODY_Y + 0.1, W - 2 * M - 2.5, BODY_B - BODY_Y - 0.9, s["bullets"], size=20, min_size=14)
        if s.get("contact"):
            self._text(slide, M, 6.15, W - 2 * M, 0.45, s["contact"], size=13, color=self.t["muted"], name="Contact")
        self._text(slide, M, 6.85, W - 2 * M, 0.5, disclaimer(self.lang), size=8, color=self.t["muted"],
                   name="Disclaimer", min_size=7)

    def l_glossary(self, slide, s):
        """Plain-language metric definitions: two columns, term in bold, one sentence each."""
        self._title(slide, s["title"])
        items = s.get("items", [])
        if not items:
            return
        sep = "：" if self.lang == "zh" else ": "
        gap = 0.5
        ncol = 1 if len(items) <= 4 else 2
        cw = (W - 2 * M - gap) / 2 if ncol == 2 else W - 2 * M - 1.0
        nrow = max(math.ceil(len(items) / ncol), 3)
        rh = min(1.0, (BODY_B - BODY_Y) / nrow)
        texts = [f"**{it['term']}**{sep}{it['text']}" for it in items]
        size = min(fit_font_size(t.replace("**", ""), cw, rh - 0.14, (18 if ncol == 1 else 15), 10.5, self.t["font_body"], True, 0)[0]
                   for t in texts)
        half = math.ceil(len(items) / ncol)
        for i, (it, txt) in enumerate(zip(items, texts)):
            col, row = (0, i) if i < half else (1, i - half)
            x = M + col * (cw + gap)
            y = BODY_Y + row * rh
            self._rect(slide, x, y, cw, 0.012, self.t["grid"], name="GlossaryRule")
            self._text(slide, x, y + 0.08, cw, rh - 0.14, txt, size=size, name=f"GlossaryTerm:{it['id']}",
                       min_size=min(size, 11))

    # ------------------------------------------------------------- build
    def build(self) -> Presentation:
        for s in self.spec["slides"]:
            self.page += 1
            slide = self.prs.slides.add_slide(self.blank)
            self._bg(slide)
            layout = s.get("layout", "bullets")
            fn = getattr(self, f"l_{layout}", None)
            if fn is None:
                self.report["warnings"].append(f"slide {self.page}: unknown layout '{layout}', used bullets")
                fn = self.l_bullets
            fn(slide, s)
            self._footer(slide, s)
            self._notes(slide, s)
            data_slide = layout in ("chart", "table", "big_number", "scorecard", "matrix")
            if data_slide and not s.get("source"):
                self.report["warnings"].append(f"slide {self.page}: data slide without source line")
            self.report["slides"].append({"n": self.page, "layout": layout, "title": s.get("title", "")[:90]})
        cp = self.prs.core_properties
        cp.title = self.meta.get("title", "")
        cp.author = self.meta.get("author", "")
        # never leak library-template defaults (template author, "generated by ...") into metadata
        cp.last_modified_by = self.meta.get("author", "")
        cp.comments = self.meta.get("comments", "")
        cp.keywords = self.meta.get("keywords", "")
        cp.subject = self.meta.get("subject", "")
        cp.revision = 1
        cp.language = self.loc["lang_tag"]
        for sl in self.prs.slides:   # East Asian typeface + language on every run (CJK glyph selection)
            add_ea_fonts(sl.shapes._spTree, self.t.get("font_ea"), self.loc["lang_tag"], self.t["font_body"])
            if sl.has_notes_slide:
                add_ea_fonts(sl.notes_slide.shapes._spTree, self.t.get("font_ea"), self.loc["lang_tag"], None)
        return self.prs


def build_pptx(spec: dict | str, out_path: str, theme: str | dict | None = None, facts: dict | str | None = None,
               locale: str | None = None) -> dict:
    spec = copy.deepcopy(load_json(spec))
    if locale:
        spec.setdefault("meta", {})["locale"] = locale
    meta = spec.get("meta", {})
    loc = locale_of(meta)
    facts_src = facts or meta.get("facts")
    if facts_src:
        f = load_json(facts_src)
        spec = resolve_placeholders(spec, f, {"locale": loc, "currency": meta.get("currency")})
    th = load_theme(theme or meta.get("theme", "light"), meta.get("font_heading"), meta.get("font_body"), loc)
    glossary_ids = []
    if meta.get("glossary", True) and not any(sl.get("layout") == "glossary" and not sl.get("_glossary")
                                              for sl in spec.get("slides", [])):
        # pass 1: build, read the visible text exactly as qa_check does, detect the metrics shown
        probe = DeckBuilder(copy.deepcopy(spec), copy.deepcopy(th)).build()
        glossary_ids = glossary.detect([t for _, g, t in glossary.pptx_slide_texts(probe) if not g], loc)
        if glossary_ids:
            spec = glossary.insert_slides(spec, glossary_ids, loc)
    b = DeckBuilder(spec, th)
    prs = b.build()
    b.report["glossary"] = glossary_ids
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    prs.save(out_path)
    clean_package(out_path, loc)   # drop unrelated template theme fonts / languages
    b.report["output"] = os.path.basename(out_path)
    b.report["theme"] = theme if isinstance(theme, str) and not os.path.isfile(theme) else meta.get("theme", "light")
    b.report["locale"] = loc
    return b.report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", "-i", required=True)
    ap.add_argument("--out", "-o", required=True)
    ap.add_argument("--theme")
    ap.add_argument("--facts")
    ap.add_argument("--locale", "-l", choices=["ru", "en", "zh", "vi", "id", "ms"], help="overrides meta.locale")
    a = ap.parse_args(argv)
    print(dump_json(build_pptx(a.input, a.out, a.theme, a.facts, a.locale)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
