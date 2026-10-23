"""Text-fit heuristics shared by build_pptx.py (auto-shrink) and qa_check.py (overflow check).

No portable font metrics, so widths are estimated per character class (in em):
  * CJK ideographs, kana, hangul, full-width forms and CJK punctuation: 1.0 em (East Asian Wide/Fullwidth)
  * Latin/Cyrillic letters: ~0.53 em sans, 0.50 serif, 0.60 mono; digits 0.56; space 0.28
Line breaking follows the scripts: Latin/Cyrillic break at spaces; CJK text may break between any
two ideographs, except that closing punctuation (，。、；：？！）」』》 etc.) never starts a line and opening
punctuation never ends one (simplified kinsoku / 避头尾 rules). Confirm on a render.
"""
from __future__ import annotations

import re
import unicodedata

AVG_EM = {"sans": 0.53, "serif": 0.50, "mono": 0.60}
LINE_HEIGHT = 1.18        # multiple of font size, Latin/Cyrillic
LINE_HEIGHT_CJK = 1.30    # CJK lines need more leading
NO_LINE_START = set("，。、；：？！）》」』】〕〉…—·％%,.;:?!)]}")
NO_LINE_END = set("（《「『【〔〈([{")


def _family_kind(font_name: str | None) -> str:
    f = (font_name or "").lower()
    if any(k in f for k in ("mono", "courier", "consol")):
        return "mono"
    if any(k in f for k in ("times", "serif", "georgia", "garamond", "pt serif", "cambria", "simsun", "song", "宋")) \
            and "sans" not in f:
        return "serif"
    return "sans"


def is_wide(ch: str) -> bool:
    return unicodedata.east_asian_width(ch) in ("W", "F")


def has_cjk(text: str) -> bool:
    return any(is_wide(c) for c in text or "")


def char_em(ch: str, kind: str = "sans") -> float:
    if is_wide(ch):
        return 1.0
    if ch == " " or ch == "\u00a0":
        return 0.28
    if ch.isdigit():
        return 0.56
    if ch in "il.,;:'|!":
        return 0.28
    if ch in "mwMW@—":
        return 0.85
    return AVG_EM[kind]


def text_width_em(text: str, font_name: str | None = None) -> float:
    kind = _family_kind(font_name)
    return sum(char_em(c, kind) for c in text)


def char_width_in(font_pt: float, font_name: str | None = None, bold: bool = False) -> float:
    """Average Latin glyph width in inches (kept for backwards compatibility)."""
    w = AVG_EM[_family_kind(font_name)] * font_pt / 72.0
    return w * (1.06 if bold else 1.0)


_TOKEN = re.compile(r"\s+|[^\s\u2E80-\u9FFF\u3000-\u303F\uFF00-\uFFEF\uAC00-\uD7AF\u3040-\u30FF]+|.", re.S)


def _tokens(para: str) -> list[str]:
    """Break opportunities: whitespace runs, Latin/Cyrillic words, single CJK characters; then glue
    no-line-start punctuation to the previous token and no-line-end punctuation to the next."""
    raw = _TOKEN.findall(para)
    out: list[str] = []
    for t in raw:
        if out and len(t) == 1 and t in NO_LINE_START and not out[-1].isspace():
            out[-1] += t
        elif out and len(out[-1]) >= 1 and out[-1][-1] in NO_LINE_END and not t.isspace():
            out[-1] += t
        else:
            out.append(t)
    return out


def lines_needed(text: str, font_pt: float, box_w_in: float, font_name: str | None = None,
                 bold: bool = False, inset_in: float = 0.1) -> int:
    usable_em = max(box_w_in - 2 * inset_in, 0.2) * 72.0 / font_pt / (1.06 if bold else 1.0)
    total = 0
    for para in (text or "").split("\n"):
        if not para:
            total += 1
            continue
        lines, cur = 1, 0.0
        for tok in _tokens(para):
            w = text_width_em(tok, font_name)
            if tok.isspace():
                if cur > 0:
                    cur += w
                continue
            if cur + w <= usable_em + 1e-9:
                cur += w
                continue
            if cur == 0:  # token longer than a line: hard-wrap
                while w > usable_em:
                    lines += 1
                    w -= usable_em
                cur = w
            else:
                lines += 1
                cur = w
                while cur > usable_em:
                    lines += 1
                    cur -= usable_em
        total += lines
    return total


def text_height_in(text: str, font_pt: float, box_w_in: float, font_name: str | None = None,
                   bold: bool = False, para_space_pt: float = 0.0, inset_in: float = 0.05) -> float:
    n = lines_needed(text, font_pt, box_w_in, font_name, bold)
    paras = max(len((text or "").split("\n")), 1)
    lh = LINE_HEIGHT_CJK if has_cjk(text) else LINE_HEIGHT
    return n * font_pt * lh / 72.0 + (paras - 1) * para_space_pt / 72.0 + 2 * inset_in


def fits(text: str, font_pt: float, box_w_in: float, box_h_in: float, font_name: str | None = None,
         bold: bool = False, para_space_pt: float = 0.0) -> bool:
    return text_height_in(text, font_pt, box_w_in, font_name, bold, para_space_pt) <= box_h_in + 1e-6


def fit_font_size(text: str, box_w_in: float, box_h_in: float, max_pt: float, min_pt: float,
                  font_name: str | None = None, bold: bool = False, para_space_pt: float = 0.0,
                  step: float = 1.0) -> tuple[float, bool]:
    """Largest size in [min_pt, max_pt] that fits. Returns (size, fits_at_min)."""
    size = max_pt
    while size >= min_pt:
        if fits(text, size, box_w_in, box_h_in, font_name, bold, para_space_pt):
            return size, True
        size -= step
    return min_pt, fits(text, min_pt, box_w_in, box_h_in, font_name, bold, para_space_pt)


def text_units(text: str) -> int:
    """Length measure that works across scripts: words for Latin/Cyrillic, characters/2 for CJK
    (≈ one 'word' per two hanzi; used for title-length and density checks)."""
    cjk = sum(1 for c in text if is_wide(c) and not unicodedata.category(c).startswith("P"))
    rest = re.sub(r"[\u2E80-\u9FFF\u3000-\u303F\uFF00-\uFFEF]", " ", text)
    return len(rest.split()) + (cjk + 1) // 2
