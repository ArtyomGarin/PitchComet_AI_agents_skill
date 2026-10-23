"""charts_common.py — one chart spec → native, editable OOXML chart (python-pptx engine).

Used by build_pptx.py (slide charts) and build_docx.py (Word charts: the same chartSpace XML
plus an embedded .xlsx workbook, so the chart is editable in Word via 'Edit data').

Chart spec:
{
  "type": "column" | "bar" | "stacked_column" | "stacked_bar" | "line" | "line_markers" | "area" |
          "pie" | "doughnut" | "waterfall" | "scatter",
  "categories": ["2025", "2026"],
  "series": [{"name": "TAM", "values": [1.0, 2.0]}],      # scatter: {"name", "points": [[x, y], ...]}
  "scale": 1e9,                 # optional divisor applied to values (e.g. RUB → bn RUB)
  "number_format": "#,##0.0",   # Excel format for labels/axis
  "unit_label": "млрд ₽",       # shown as value-axis title when axis visible
  "data_labels": true, "legend": null (auto: >1 series), "highlight_index": null,
  "value_axis": true, "gridlines": true, "y_min": 0, "y_max": null, "colors": ["0F766E", ...],
  "series_color_index": [1, 0, 2]   # optional: map series i to palette index
}
"""
from __future__ import annotations

import copy
from typing import Any

import os
import sys

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmt_utils import fmt_number  # noqa: E402
from locales import get_locale  # noqa: E402
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.util import Pt

TYPE_MAP = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "stacked_column": XL_CHART_TYPE.COLUMN_STACKED,
    "stacked_bar": XL_CHART_TYPE.BAR_STACKED,
    "stacked_column_100": XL_CHART_TYPE.COLUMN_STACKED_100,
    "line": XL_CHART_TYPE.LINE,
    "line_markers": XL_CHART_TYPE.LINE_MARKERS,
    "area": XL_CHART_TYPE.AREA,
    "pie": XL_CHART_TYPE.PIE,
    "doughnut": XL_CHART_TYPE.DOUGHNUT,
    "waterfall": XL_CHART_TYPE.COLUMN_STACKED,
    "scatter": XL_CHART_TYPE.XY_SCATTER,
}
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _rgb(hexstr: str) -> RGBColor:
    return RGBColor.from_string(hexstr.replace("#", "").upper())


def prepare(spec: dict) -> tuple[Any, Any, dict]:
    """Return (xl_chart_type, chart_data, normalized_spec)."""
    spec = copy.deepcopy(spec)
    ctype = spec.get("type", "column")
    scale = spec.get("scale") or 1
    nf = spec.get("number_format", "#,##0.0")
    if ctype == "scatter":
        cd = XyChartData(number_format=nf)
        for s in spec["series"]:
            ser = cd.add_series(s["name"])
            for x, y in s["points"]:
                ser.add_data_point(x, y / scale)
        return TYPE_MAP[ctype], cd, spec
    cats = [str(c) for c in spec["categories"]]
    cd = CategoryChartData(number_format=nf)
    cd.categories = cats
    if ctype == "waterfall":
        # first value = start bar, then deltas, optional final total (spec["total_label"])
        vals = [v / scale for v in spec["series"][0]["values"]]
        base, up, down, running = [], [], [], 0.0
        for i, v in enumerate(vals):
            is_total = i == 0 or (spec.get("total_last") and i == len(vals) - 1)
            if is_total:
                base.append(0.0); up.append(v if i == 0 else running); down.append(0.0)
                running = v if i == 0 else running
            elif v >= 0:
                base.append(running); up.append(v); down.append(0.0); running += v
            else:
                running += v
                base.append(running); up.append(0.0); down.append(-v)
        cd.add_series("_base", base)
        cd.add_series(spec["series"][0].get("name", "+"), up)
        cd.add_series(spec.get("negative_name", "−"), down)
        spec["_waterfall"] = True
    else:
        for s in spec["series"]:
            cd.add_series(str(s["name"]), [None if v is None else v / scale for v in s["values"]])
    return TYPE_MAP.get(ctype, XL_CHART_TYPE.COLUMN_CLUSTERED), cd, spec


def style_chart(chart, spec: dict, theme: dict, base_font_pt: float = 12) -> None:
    """Apply minimalist styling with python-pptx API (works for slide charts and detached XML)."""
    ctype = spec.get("type", "column")
    palette = spec.get("colors") or theme.get("palette") or ["0F766E", "94A3B8", "B91C1C", "334155"]
    if spec.get("series_color_index"):  # e.g. [1, 0, 2]: bear muted, base accent, bull third colour
        palette = [palette[j % len(palette)] for j in spec["series_color_index"]]
    text_c, muted_c, grid_c = theme.get("text", "1F2937"), theme.get("muted", "6B7280"), theme.get("grid", "E5E7EB")
    font = theme.get("font_body", "Arial")
    chart.font.size = Pt(base_font_pt)
    chart.font.name = font
    chart.font.color.rgb = _rgb(muted_c)
    n_series = len(spec.get("series", []))
    legend = spec.get("legend")
    if legend is None:
        legend = n_series > 1 and ctype not in ("waterfall",) or ctype in ("pie", "doughnut")
    chart.has_legend = bool(legend)
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(base_font_pt)
        chart.legend.font.color.rgb = _rgb(muted_c)
    if spec.get("title"):
        chart.has_title = True
        chart.chart_title.text_frame.text = spec["title"]
        p = chart.chart_title.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(base_font_pt + 1)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = _rgb(text_c)
    else:
        chart.has_title = False
    plot = chart.plots[0]
    nf = spec.get("number_format", "#,##0.0")
    if ctype in ("pie", "doughnut"):
        _no_border(chart)
        pts = plot.series[0].points
        for i in range(len(spec["categories"])):
            pts[i].format.fill.solid()
            pts[i].format.fill.fore_color.rgb = _rgb(palette[i % len(palette)])
        plot.has_data_labels = spec.get("data_labels", True)
        if plot.has_data_labels:
            dl = plot.data_labels
            dl.number_format = spec.get("number_format", "0%")
            dl.number_format_is_linked = False
            dl.font.size = Pt(base_font_pt)
            dl.font.color.rgb = _rgb("FFFFFF") if ctype == "pie" else _rgb(text_c)
            if spec.get("show_percent", True):
                dl.show_percentage = True
                dl.show_value = False
        return
    try:
        plot.gap_width = spec.get("gap_width", 60)
        if ctype.startswith("stacked") or ctype == "waterfall":
            plot.overlap = 100
    except Exception:
        pass
    hi = spec.get("highlight_index")
    for i, ser in enumerate(plot.series):
        color = palette[i % len(palette)]
        if spec.get("_waterfall"):
            color = [theme.get("bg", "FFFFFF"), theme.get("positive", palette[0]), theme.get("negative", "B91C1C")][i]
        if ctype.startswith("line"):
            ser.format.line.color.rgb = _rgb(color)
            ser.format.line.width = Pt(2.5)
            ser.smooth = False
        elif ctype == "scatter":
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = _rgb(color)
        else:
            ser.format.fill.solid()
            ser.format.fill.fore_color.rgb = _rgb(color)
            if spec.get("_waterfall") and i == 0:
                ser.format.fill.background()
                ser.format.line.fill.background()
            if hi is not None and n_series == 1:
                for j in range(len(spec["categories"])):
                    pt = ser.points[j]
                    pt.format.fill.solid()
                    pt.format.fill.fore_color.rgb = _rgb(palette[0] if j == hi else theme.get("muted_fill", "CBD5E1"))
    multi_line = ctype.startswith("line") and n_series > 1 and spec.get("label_last_only", True)
    if spec.get("data_labels", True) and multi_line:
        # label only the last point of each series (avoids overlapping labels where lines start together)
        dec = len(nf.split(".")[1].rstrip("%")) if "." in nf else 0
        lang = theme.get("lang", "ru")
        for i, ser in enumerate(plot.series):
            vals = [v for v in spec["series"][i]["values"]]
            last = len(vals) - 1
            v = vals[last] / (spec.get("scale") or 1)
            txt = fmt_number(v, dec, lang)
            dl = ser.points[last].data_label
            dl.has_text_frame = True
            dl.text_frame.text = txt
            r = dl.text_frame.paragraphs[0].runs[0]
            r.font.size = Pt(base_font_pt)
            r.font.bold = True
            r.font.color.rgb = _rgb(palette[i % len(palette)] if not spec.get("_waterfall") else text_c)
            dl.position = XL_LABEL_POSITION.RIGHT
    elif spec.get("data_labels", True) and ctype != "scatter":
        targets = plot.series[1:] if spec.get("_waterfall") else plot.series
        for ser in targets:
            dl = ser.data_labels
            dl.show_value = True
            dl.number_format = nf
            dl.number_format_is_linked = False
            dl.font.size = Pt(base_font_pt)
            dl.font.color.rgb = _rgb(text_c)
            if not (ctype.startswith("stacked") or spec.get("_waterfall") or ctype == "area"):
                try:
                    dl.position = XL_LABEL_POSITION.OUTSIDE_END if not ctype.startswith("line") else XL_LABEL_POSITION.ABOVE
                except Exception:
                    pass
            elif spec.get("_waterfall"):
                dl.position = XL_LABEL_POSITION.INSIDE_END
                dl.font.color.rgb = _rgb("FFFFFF")
    _no_border(chart)
    # axes
    try:
        va = chart.value_axis
        ca = chart.category_axis
    except Exception:
        return
    va.has_major_gridlines = spec.get("gridlines", True)
    if va.has_major_gridlines:
        va.major_gridlines.format.line.color.rgb = _rgb(grid_c)
        va.major_gridlines.format.line.width = Pt(0.5)
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(base_font_pt)
    va.tick_labels.font.color.rgb = _rgb(muted_c)
    va.tick_labels.number_format = nf
    va.tick_labels.number_format_is_linked = False
    if spec.get("y_min", 0) is not None and ctype != "scatter":
        va.minimum_scale = spec.get("y_min", 0)
    if spec.get("y_max") is not None:
        va.maximum_scale = spec["y_max"]
    va.visible = spec.get("value_axis", not spec.get("data_labels", True))
    if spec.get("unit_label") and va.visible:
        va.has_title = True
        va.axis_title.text_frame.text = spec["unit_label"]
        r = va.axis_title.text_frame.paragraphs[0].runs[0]
        r.font.size = Pt(base_font_pt)
        r.font.color.rgb = _rgb(muted_c)
        r.font.bold = False
    ca.format.line.color.rgb = _rgb(grid_c)
    ca.tick_labels.font.size = Pt(base_font_pt)
    ca.tick_labels.font.color.rgb = _rgb(text_c if ctype in ("bar", "stacked_bar") else muted_c)
    ca.has_major_gridlines = False
    try:
        from pptx.enum.chart import XL_TICK_LABEL_POSITION
        if any((v or 0) < 0 for s_ in spec.get("series", []) for v in s_.get("values", [])):
            ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    except Exception:
        pass
    try:
        from pptx.enum.chart import XL_TICK_MARK
        ca.major_tick_mark = XL_TICK_MARK.NONE
        va.major_tick_mark = XL_TICK_MARK.NONE
    except Exception:
        pass
    if ctype in ("bar", "stacked_bar"):
        # largest first from top: reverse category order
        ca.reverse_order = True


def fix_axis_ids(chart_space_el) -> None:
    """python-pptx writes negative c:axId values, which fail OOXML schema; make them positive."""
    for tag in ("axId", "crossAx"):
        for el in chart_space_el.iter(f"{{{C_NS}}}{tag}"):
            v = int(el.get("val"))
            if v < 0:
                el.set("val", str(abs(v)))


def chart_unit_suffix(spec: dict) -> str:
    return spec.get("unit_label", "")


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_RPR_TAGS = {f"{{{A_NS}}}rPr", f"{{{A_NS}}}defRPr", f"{{{A_NS}}}endParaRPr"}
_AFTER_EA = {f"{{{A_NS}}}{t}" for t in ("cs", "sym", "hlinkClick", "hlinkMouseOver", "rtl", "extLst")}


def add_ea_fonts(root, ea_font: str | None, lang_tag: str | None = None, latin: str | None = None) -> int:
    """Give every DrawingML run property an East Asian typeface (<a:ea>) and optional lang.

    Needed for CJK: PowerPoint/LibreOffice pick glyphs for Chinese characters from <a:ea>,
    not from <a:latin>. Works on slide XML and chart XML alike. Returns the number of nodes changed."""
    if not ea_font and not lang_tag:
        return 0
    n = 0
    for el in root.iter():
        if el.tag not in _RPR_TAGS:
            continue
        if lang_tag and el.tag != f"{{{A_NS}}}defRPr":
            el.set("lang", lang_tag)
            if lang_tag.startswith("zh"):
                el.set("altLang", "en-US")
        if not ea_font:
            continue
        ea = el.find(f"{{{A_NS}}}ea")
        if ea is None:
            ea = etree.Element(f"{{{A_NS}}}ea")
            lat = el.find(f"{{{A_NS}}}latin")
            if lat is None and latin:
                lat = etree.Element(f"{{{A_NS}}}latin")
                lat.set("typeface", latin)
                nxt = next((ch for ch in el if ch.tag in _AFTER_EA), None)
                if nxt is not None:
                    nxt.addprevious(lat)
                else:
                    el.append(lat)
            if lat is not None:
                lat.addnext(ea)
            else:
                nxt = next((ch for ch in el if ch.tag in _AFTER_EA), None)
                if nxt is not None:
                    nxt.addprevious(ea)
                else:
                    el.append(ea)
        ea.set("typeface", ea_font)
        n += 1
    return n


def set_chart_lang(chart_space_el, lang: str = "ru") -> None:
    """Add <c:lang> so number formats/decimal separators follow the document language."""
    code = get_locale(lang)["lang_tag"]
    el = chart_space_el.find(f"{{{C_NS}}}lang")
    if el is None:
        el = etree.SubElement(chart_space_el, f"{{{C_NS}}}lang")
        chart_space_el.remove(el)
        d = chart_space_el.find(f"{{{C_NS}}}date1904")
        if d is not None:
            d.addnext(el)
        else:
            chart_space_el.insert(0, el)
    el.set("val", code)


def _no_border(chart) -> None:
    """Remove the chart-area border/fill (minimal look, sits on slide/page background)."""
    cs = chart._chartSpace
    old = cs.find(f"{{{C_NS}}}spPr")
    if old is not None:
        cs.remove(old)
    sp = etree.fromstring(f'<c:spPr xmlns:c="{C_NS}" xmlns:a="{A_NS}"><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>')
    ch = cs.find(f"{{{C_NS}}}chart")
    ch.addnext(sp)
