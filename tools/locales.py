"""locales.py — single source of locale settings:
ru (Russian), en (English, United States), zh (Simplified Chinese, mainland China),
vi (Vietnamese, Vietnam), id (Bahasa Indonesia, Indonesia), ms (Bahasa Malaysia, Malaysia).

Everything locale-dependent (number/currency/date formats, default fonts incl. East Asian fonts,
citation style, captions and labels, scenario/audience names) is read from here, so adding a
locale = adding one entry.

    from locales import get_locale, label
    loc = get_locale("zh"); label("zh", "table")  # -> "表"
"""
from __future__ import annotations

import datetime as _dt

NBSP = "\u00a0"

LOCALES: dict[str, dict] = {
    "ru": {
        "code": "ru", "lang_tag": "ru-RU", "name": "Русский", "market": "ru",
        "currency": "RUB", "decimal": ",", "thousands": NBSP,
        "na": "н/д", "pp": "п.п.", "multiple": "x",
        "scales": {"k": (1e3, "тыс."), "mn": (1e6, "млн"), "bn": (1e9, "млрд"), "tn": (1e12, "трлн")},
        "currency_style": "suffix",          # 3,0 млрд ₽
        "chart_scale_mn": 1e6, "chart_scale_bn": 1e9, "unit_mn": "млн ₽", "unit_bn": "млрд ₽",
        "fonts": {"deck_latin": "Arial", "deck_ea": None, "report_latin": "Times New Roman",
                  "report_heading": "Times New Roman", "report_ea": None, "report_heading_ea": None},
        "font_fallbacks": ["Arial", "Liberation Sans", "PT Sans"],
        "citation_style": "footnotes", "bibliography_style": "gost", "caption_sep": " — ", "caption_num_sep": " ",
        "first_line_indent_chars": 0,
        "margins_cm": (3.0, 1.5, 2.0, 2.0),  # left, right, top, bottom (ГОСТ 7.32)
        "labels": {
            "table": "Таблица", "figure": "Рисунок", "source": "Источник", "sources_inline": "Источники",
            "toc": "Содержание", "references": "Список источников", "score": "Балл", "weight": "Вес, %",
            "criterion": "Критерий", "contribution": "Вклад", "comment": "Комментарий", "total": "Итого",
            "total_score": "Итоговый балл", "of_100": "из 100", "range": "диапазон", "page": "Стр.",
            "accessed": "дата обращения", "after": "после", "revenue": "Выручка", "cash": "Денежные средства на конец года",
            "customers": "Клиенты на конец года", "gross_margin": "Валовая маржа", "fcf": "Свободный денежный поток",
            "cac_payback": "Окупаемость CAC, мес.", "metric": "Показатель", "sens_axis": "Новые клиенты \\ ARPA",
            "scn": {"bear": "Пессимистичный", "base": "Базовый", "bull": "Оптимистичный"},
            "aud": {"investor": "Инвестор", "government": "Государство / грант", "corporate": "Корпоративный партнёр",
                    "academic": "Академическая экспертиза", "neutral": "Нейтральный профиль"},
        },
    },
    "en": {
        "code": "en", "lang_tag": "en-US", "name": "English", "market": "en",
        "currency": "USD", "decimal": ".", "thousands": ",",
        "na": "n/a", "pp": "pp", "multiple": "x",
        "scales": {"k": (1e3, "K"), "mn": (1e6, "M"), "bn": (1e9, "B"), "tn": (1e12, "T")},
        "currency_style": "prefix",          # $3.0B
        "chart_scale_mn": 1e6, "chart_scale_bn": 1e9, "unit_mn": "$M", "unit_bn": "$B",
        "fonts": {"deck_latin": "Arial", "deck_ea": None, "report_latin": "Times New Roman",
                  "report_heading": "Arial", "report_ea": None, "report_heading_ea": None},
        "font_fallbacks": ["Arial", "Helvetica", "Liberation Sans"],
        "citation_style": "author_date", "bibliography_style": "apa", "caption_sep": ". ", "caption_num_sep": " ",
        "first_line_indent_chars": 0,
        "margins_cm": (2.54, 2.54, 2.54, 2.54),
        "labels": {
            "table": "Table", "figure": "Figure", "source": "Source", "sources_inline": "Sources",
            "toc": "Contents", "references": "References", "score": "Score", "weight": "Weight, %",
            "criterion": "Criterion", "contribution": "Contribution", "comment": "Comment", "total": "Total",
            "total_score": "Total score", "of_100": "of 100", "range": "range", "page": "p.",
            "accessed": "accessed", "after": "after", "revenue": "Revenue", "cash": "Year-end cash",
            "customers": "Customers, year-end", "gross_margin": "Gross margin", "fcf": "Free cash flow",
            "cac_payback": "CAC payback, months", "metric": "Metric", "sens_axis": "New customers \\ ARPA",
            "scn": {"bear": "Bear", "base": "Base", "bull": "Bull"},
            "aud": {"investor": "Investor", "government": "Government / grant", "corporate": "Corporate partner",
                    "academic": "Academic review", "neutral": "Neutral"},
        },
    },
    "zh": {
        "code": "zh", "lang_tag": "zh-CN", "name": "简体中文", "market": "zh",
        "currency": "CNY", "decimal": ".", "thousands": ",",
        "na": "无数据", "pp": "个百分点", "multiple": "倍",
        # Chinese business writing uses 万 (1e4) and 亿 (1e8); latin-style scale codes map onto them
        "scales": {"k": (1e4, "万"), "mn": (1e4, "万"), "wan": (1e4, "万"), "bn": (1e8, "亿"), "yi": (1e8, "亿"),
                   "tn": (1e12, "万亿")},
        "currency_style": "zh",              # 3.0亿元
        "chart_scale_mn": 1e4, "chart_scale_bn": 1e8, "unit_mn": "万元", "unit_bn": "亿元",
        "fonts": {"deck_latin": "Arial", "deck_ea": "Microsoft YaHei", "report_latin": "Times New Roman",
                  "report_heading": "Arial", "report_ea": "SimSun", "report_heading_ea": "SimHei"},
        # Office picks the first installed; render_preview maps these to Noto CJK SC on Linux
        "font_fallbacks": ["Microsoft YaHei", "Noto Sans CJK SC", "PingFang SC", "SimHei", "SimSun", "Noto Serif CJK SC"],
        "citation_style": "numeric", "bibliography_style": "gbt7714", "caption_sep": "  ", "caption_num_sep": "",
        "first_line_indent_chars": 2,     # 首行缩进2字符
        "numeric_superscript": True,      # GB/T 7714 顺序编码制: superscript [1]
        "margins_cm": (2.8, 2.6, 3.7, 3.5),  # GB/T 9704-2012 official-document page layout
        "labels": {
            "table": "表", "figure": "图", "source": "资料来源", "sources_inline": "资料来源",
            "toc": "目录", "references": "参考文献", "score": "评分", "weight": "权重（%）",
            "criterion": "评价维度", "contribution": "加权得分", "comment": "说明", "total": "合计",
            "total_score": "综合得分", "of_100": "满分100", "range": "区间", "page": "第",
            "accessed": "引用日期", "after": "晚于", "revenue": "营业收入", "cash": "期末现金",
            "customers": "期末客户数", "gross_margin": "毛利率", "fcf": "自由现金流",
            "cac_payback": "获客成本回收期（月）", "metric": "指标", "sens_axis": "新增客户 \\ 客单价",
            "scn": {"bear": "悲观情景", "base": "基准情景", "bull": "乐观情景"},
            "aud": {"investor": "投资机构", "government": "政府 / 项目申报", "corporate": "企业 / 国企合作方",
                    "academic": "学术评审", "neutral": "中性"},
        },
    },
    "vi": {
        "code": "vi", "lang_tag": "vi-VN", "name": "Tiếng Việt", "market": "vn",
        "currency": "VND", "decimal": ",", "thousands": ".",
        "na": "k.c.d.l.", "pp": "điểm %", "multiple": " lần",
        # VND amounts are large: the "mn"/"bn" scale codes map onto tỷ (1e9) / nghìn tỷ (1e12)
        "scales": {"k": (1e6, "triệu"), "mn": (1e9, "tỷ"), "bn": (1e12, "nghìn tỷ"), "tn": (1e12, "nghìn tỷ"),
                   "trieu": (1e6, "triệu"), "ty": (1e9, "tỷ")},
        "currency_style": "suffix",          # 3,0 tỷ ₫
        "chart_scale_mn": 1e9, "chart_scale_bn": 1e12, "unit_mn": "tỷ ₫", "unit_bn": "nghìn tỷ ₫",
        "fonts": {"deck_latin": "Arial", "deck_ea": None, "report_latin": "Times New Roman",
                  "report_heading": "Times New Roman", "report_ea": None, "report_heading_ea": None},
        "font_fallbacks": ["Arial", "Liberation Sans", "Noto Sans"],
        "citation_style": "author_date", "bibliography_style": "apa", "caption_sep": ". ", "caption_num_sep": " ",
        "first_line_indent_chars": 0,
        "margins_cm": (3.0, 2.0, 2.0, 2.0),  # left, right, top, bottom (cf. Decree 30/2020/ND-CP ranges)
        "months": ["tháng 1", "tháng 2", "tháng 3", "tháng 4", "tháng 5", "tháng 6", "tháng 7", "tháng 8",
                   "tháng 9", "tháng 10", "tháng 11", "tháng 12"],
        "labels": {
            "table": "Bảng", "figure": "Hình", "source": "Nguồn", "sources_inline": "Nguồn",
            "toc": "Mục lục", "references": "Tài liệu tham khảo", "score": "Điểm", "weight": "Trọng số, %",
            "criterion": "Tiêu chí", "contribution": "Đóng góp", "comment": "Ghi chú", "total": "Tổng",
            "total_score": "Tổng điểm", "of_100": "trên 100", "range": "khoảng", "page": "tr.",
            "accessed": "truy cập", "after": "sau", "revenue": "Doanh thu", "cash": "Tiền mặt cuối năm",
            "customers": "Khách hàng cuối năm", "gross_margin": "Biên lợi nhuận gộp", "fcf": "Dòng tiền tự do",
            "cac_payback": "Thời gian hoàn vốn CAC, tháng", "metric": "Chỉ tiêu", "sens_axis": "Khách hàng mới \\ ARPA",
            "scn": {"bear": "Bi quan", "base": "Cơ sở", "bull": "Lạc quan"},
            "aud": {"investor": "Nhà đầu tư", "government": "Cơ quan nhà nước / tài trợ", "corporate": "Doanh nghiệp / DNNN",
                    "academic": "Hội đồng khoa học", "neutral": "Trung lập"},
        },
    },
    "id": {
        "code": "id", "lang_tag": "id-ID", "name": "Bahasa Indonesia", "market": "id",
        "currency": "IDR", "decimal": ",", "thousands": ".",
        "na": "t.a.", "pp": "poin persentase", "multiple": "x",
        # IDR amounts are large: "mn"/"bn" scale codes map onto miliar (1e9) / triliun (1e12)
        "scales": {"k": (1e6, "juta"), "mn": (1e9, "miliar"), "bn": (1e12, "triliun"), "tn": (1e12, "triliun"),
                   "juta": (1e6, "juta"), "miliar": (1e9, "miliar")},
        "currency_style": "prefix_word",     # Rp3,0 miliar
        "chart_scale_mn": 1e9, "chart_scale_bn": 1e12, "unit_mn": "Rp miliar", "unit_bn": "Rp triliun",
        "fonts": {"deck_latin": "Arial", "deck_ea": None, "report_latin": "Times New Roman",
                  "report_heading": "Arial", "report_ea": None, "report_heading_ea": None},
        "font_fallbacks": ["Arial", "Liberation Sans", "Noto Sans"],
        "citation_style": "author_date", "bibliography_style": "apa", "caption_sep": ". ", "caption_num_sep": " ",
        "first_line_indent_chars": 0,
        "margins_cm": (3.0, 2.5, 2.5, 2.5),
        "months": ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September",
                   "Oktober", "November", "Desember"],
        "labels": {
            "table": "Tabel", "figure": "Gambar", "source": "Sumber", "sources_inline": "Sumber",
            "toc": "Daftar isi", "references": "Daftar pustaka", "score": "Skor", "weight": "Bobot, %",
            "criterion": "Kriteria", "contribution": "Kontribusi", "comment": "Keterangan", "total": "Total",
            "total_score": "Skor total", "of_100": "dari 100", "range": "rentang", "page": "hlm.",
            "accessed": "diakses", "after": "setelah", "revenue": "Pendapatan", "cash": "Kas akhir tahun",
            "customers": "Pelanggan akhir tahun", "gross_margin": "Margin kotor", "fcf": "Arus kas bebas",
            "cac_payback": "Payback CAC, bulan", "metric": "Indikator", "sens_axis": "Pelanggan baru \\ ARPA",
            "scn": {"bear": "Pesimis", "base": "Dasar", "bull": "Optimis"},
            "aud": {"investor": "Investor", "government": "Pemerintah / hibah", "corporate": "Korporasi / BUMN",
                    "academic": "Penilai akademik", "neutral": "Netral"},
        },
    },
    "ms": {
        "code": "ms", "lang_tag": "ms-MY", "name": "Bahasa Malaysia", "market": "my",
        "currency": "MYR", "decimal": ".", "thousands": ",",
        "na": "t/a", "pp": "mata peratusan", "multiple": "x",
        "scales": {"k": (1e3, "ribu"), "mn": (1e6, "juta"), "bn": (1e9, "bilion"), "tn": (1e12, "trilion")},
        "currency_style": "prefix_word",     # RM3.0 bilion
        "chart_scale_mn": 1e6, "chart_scale_bn": 1e9, "unit_mn": "RM juta", "unit_bn": "RM bilion",
        "fonts": {"deck_latin": "Arial", "deck_ea": None, "report_latin": "Times New Roman",
                  "report_heading": "Arial", "report_ea": None, "report_heading_ea": None},
        "font_fallbacks": ["Arial", "Liberation Sans", "Noto Sans"],
        "citation_style": "author_date", "bibliography_style": "apa", "caption_sep": ". ", "caption_num_sep": " ",
        "first_line_indent_chars": 0,
        "margins_cm": (2.54, 2.54, 2.54, 2.54),
        "months": ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai", "Ogos", "September",
                   "Oktober", "November", "Disember"],
        "labels": {
            "table": "Jadual", "figure": "Rajah", "source": "Sumber", "sources_inline": "Sumber",
            "toc": "Kandungan", "references": "Rujukan", "score": "Skor", "weight": "Wajaran, %",
            "criterion": "Kriteria", "contribution": "Sumbangan", "comment": "Catatan", "total": "Jumlah",
            "total_score": "Skor keseluruhan", "of_100": "daripada 100", "range": "julat", "page": "hlm.",
            "accessed": "diakses", "after": "selepas", "revenue": "Hasil", "cash": "Tunai akhir tahun",
            "customers": "Pelanggan akhir tahun", "gross_margin": "Margin kasar", "fcf": "Aliran tunai bebas",
            "cac_payback": "Tempoh pulangan CAC, bulan", "metric": "Penunjuk", "sens_axis": "Pelanggan baharu \\ ARPA",
            "scn": {"bear": "Pesimis", "base": "Asas", "bull": "Optimis"},
            "aud": {"investor": "Pelabur", "government": "Kerajaan / geran", "corporate": "Korporat / GLC",
                    "academic": "Penilai akademik", "neutral": "Neutral"},
        },
    },
}
ALIASES = {"ru-RU": "ru", "en-US": "en", "en-GB": "en", "zh-CN": "zh", "zh-Hans": "zh", "cn": "zh",
           "vi-VN": "vi", "vn": "vi", "id-ID": "id", "in": "id", "ms-MY": "ms", "my": "ms", "zsm": "ms"}

# Market profiles (scoring, guides in markets/<code>.md) are keyed by country/region, locales by language.
MARKETS = {"ru": "Russia", "en": "United States", "zh": "Mainland China", "vn": "Vietnam", "id": "Indonesia", "my": "Malaysia"}
MARKET_ALIASES = {"vi": "vn", "ms": "my", "us": "en", "cn": "zh"}



def norm_locale(code: str | None) -> str:
    c = (code or "ru").strip()
    c = ALIASES.get(c, c)
    c = c.split("-")[0].lower()
    return c if c in LOCALES else "en"


def norm_market(code: str | None, default_locale: str | None = None) -> str:
    """Market profile code (ru, en, zh, vn, id, my); a locale code maps to its default market."""
    c = (code or "").strip().lower()
    if c in MARKETS:
        return c
    if c in MARKET_ALIASES:
        return MARKET_ALIASES[c]
    if c:
        return LOCALES[norm_locale(c)]["market"]
    return LOCALES[norm_locale(default_locale)]["market"]


def get_locale(code: str | None) -> dict:
    return LOCALES[norm_locale(code)]


def label(code: str | None, key: str, default: str | None = None):
    return get_locale(code)["labels"].get(key, default if default is not None else key)


# Central disclaimer: not legal advice, not investment advice, draft-only, user bears responsibility.
DISCLAIMERS = {
    "ru": "Не является юридической консультацией и инвестиционной рекомендацией. Документ сформирован автоматически и предназначен только как черновик для самостоятельной доработки; все цифры требуют проверки. Ответственность за использование и за фактические цифры полностью несёт пользователь.",
    "en": "This is not legal advice and not an investment recommendation. The document is generated automatically and is intended only as a draft for the user's own review; every figure must be verified. The user bears full responsibility for its use and for the accuracy of the figures.",
    "zh": "不构成法律意见，也不构成投资建议。本文档为自动生成，仅供作为草稿供用户自行审阅；所有数字均需核实。使用者对其使用行为及各数字的准确性承担全部责任。",
    "vi": "Đây không phải là tư vấn pháp lý và không phải là khuyến nghị đầu tư. Tài liệu được tạo tự động và chỉ dùng làm bản nháp để người dùng tự xem lại; mọi con số đều cần được kiểm chứng. Người dùng chịu toàn bộ trách nhiệm về việc sử dụng và tính chính xác của các con số.",
    "id": "Ini bukan nasihat hukum dan bukan rekomendasi investasi. Dokumen dibuat secara otomatis dan hanya dimaksudkan sebagai draf untuk ditinjau sendiri oleh pengguna; setiap angka wajib diverifikasi. Pengguna bertanggung jawab penuh atas penggunaannya dan keakuratan angka-angka tersebut.",
    "ms": "Ini bukan nasihat undang-undang dan bukan cadangan pelaburan. Dokumen ini dijana secara automatik dan hanya bertujuan sebagai draf untuk semakan anda sendiri; setiap angka perlu disahkan. Pengguna bertanggungjawab sepenuhnya ke atas penggunaannya dan ketepatan angka-angka tersebut.",
}


def disclaimer(code: str | None) -> str:
    return DISCLAIMERS.get(norm_locale(code), DISCLAIMERS["en"])


DISCLAIMER_TITLES = {
    "ru": "Отказ от ответственности",
    "en": "Disclaimer",
    "zh": "免责声明",
    "vi": "Tuyên bố miễn trách nhiệm",
    "id": "Penyangkalan",
    "ms": "Penafian",
}


def disclaimer_title(code: str | None) -> str:
    return DISCLAIMER_TITLES.get(norm_locale(code), DISCLAIMER_TITLES["en"])


VERDICT_LABELS = {
    "ru": "Вердикт",
    "en": "Verdict",
    "zh": "结论",
    "vi": "Nhận định",
    "id": "Verdik",
    "ms": "Penilaian",
}


def verdict_label(code: str | None) -> str:
    return VERDICT_LABELS.get(norm_locale(code), VERDICT_LABELS["en"])


def locale_of(obj: dict | None, default: str = "ru") -> str:
    """Read the locale from a spec/meta/payload: 'locale' wins, 'language' kept for compatibility."""
    obj = obj or {}
    return norm_locale(obj.get("locale") or obj.get("language") or default)


def fmt_date(d: _dt.date | str | None = None, code: str | None = "ru") -> str:
    """ru 20.10.2026 · en October 20, 2026 · zh 2026年10月20日 · vi ngày 20 tháng 10 năm 2026 ·
    id 20 Oktober 2026 · ms 20 Oktober 2026 (ISO strings accepted)."""
    if d is None:
        d = _dt.date.today()
    if isinstance(d, str):
        d = _dt.date.fromisoformat(d[:10])
    c = norm_locale(code)
    if c == "ru":
        return d.strftime("%d.%m.%Y")
    if c == "zh":
        return f"{d.year}年{d.month}月{d.day}日"
    if c == "vi":
        return f"ngày {d.day} {LOCALES['vi']['months'][d.month - 1]} năm {d.year}"
    if c in ("id", "ms"):
        return f"{d.day} {LOCALES[c]['months'][d.month - 1]} {d.year}"
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
              "October", "November", "December"]
    return f"{months[d.month - 1]} {d.day}, {d.year}"


def fmt_date_iso(d: _dt.date | str | None = None) -> str:
    if d is None:
        d = _dt.date.today()
    if isinstance(d, str):
        return d[:10]
    return d.isoformat()


def is_cjk_locale(code: str | None) -> bool:
    return norm_locale(code) == "zh"
