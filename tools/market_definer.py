#!/usr/bin/env python3
"""market_definer.py — from a product profile to a market definition, segments, ICP and a research plan.

Output
  definition   — category, buyer, unit of sale, geography, one-sentence market definition;
  segments     — buyer industry (ISIC Rev.4 section → national classification) × company size band;
  icp          — ideal customer profile: industry, size, buyer and user roles, trigger, pains;
  research_plan— the ledger keys the pipeline needs, each with what to look for, the preferred source
                 type and the fallback estimation method (so nothing ever stays a 'gap');
  queries      — targeted web-search queries in the market language (and English), per research key;
  official_sources — the statistics / central-bank / registry sources from markets/<market>.md.

CLI:
  python market_definer.py --input profile.json [--market ru] [--year 2026] [--out market_definition.json]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    from fmt_utils import dump_json, load_json
except ImportError:  # pragma: no cover
    from .fmt_utils import dump_json, load_json  # type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
TAX_PATH = os.path.join(ROOT, "config", "market_taxonomy.json")

COUNTRY = {"ru": {"ru": "Россия", "en": "Russia"}, "en": {"en": "United States"}, "zh": {"zh": "中国", "en": "China"},
           "vn": {"vi": "Việt Nam", "en": "Vietnam"}, "id": {"id": "Indonesia", "en": "Indonesia"},
           "my": {"ms": "Malaysia", "en": "Malaysia"}}
LANG_OF = {"ru": "ru", "en": "en", "zh": "zh", "vn": "vi", "id": "id", "my": "ms"}
ISIC_RU = {"A": "сельское хозяйство", "B": "добыча полезных ископаемых", "C": "обрабатывающие производства",
           "D": "энергетика", "E": "водоснабжение и отходы", "F": "строительство", "G": "розничная и оптовая торговля",
           "H": "транспорт и логистика", "I": "общественное питание и гостиницы", "J": "информация и связь",
           "K": "финансы и страхование", "L": "недвижимость", "M": "профессиональные услуги",
           "N": "административные и вспомогательные услуги", "O": "государственное управление", "P": "образование",
           "Q": "здравоохранение", "R": "культура и спорт", "S": "прочие услуги"}
ISIC_ZH = {"A": "农业", "B": "采矿业", "C": "制造业", "D": "电力燃气", "E": "水务与废物处理", "F": "建筑业",
           "G": "批发和零售业", "H": "交通运输和仓储", "I": "住宿和餐饮业", "J": "信息传输和软件", "K": "金融业",
           "L": "房地产业", "M": "专业技术服务", "N": "租赁和商务服务", "O": "公共管理", "P": "教育",
           "Q": "卫生和社会工作", "R": "文化体育娱乐", "S": "其他服务业"}
SIZE_BANDS = {
    "smb": {"en": "micro and small businesses", "ru": "микро- и малые предприятия", "zh": "小微企业",
            "vi": "doanh nghiệp siêu nhỏ và nhỏ", "id": "usaha mikro dan kecil", "ms": "perusahaan mikro dan kecil",
            "bench": "smb"},
    "mid_market": {"en": "medium-sized companies and chains", "ru": "средние компании и сети", "zh": "中型企业与连锁",
                   "vi": "doanh nghiệp vừa và chuỗi", "id": "usaha menengah dan jaringan", "ms": "perusahaan sederhana dan rangkaian",
                   "bench": "mid_market"},
    "enterprise": {"en": "large companies", "ru": "крупные компании", "zh": "大型企业", "vi": "doanh nghiệp lớn",
                   "id": "perusahaan besar", "ms": "syarikat besar", "bench": "enterprise"},
    "consumer": {"en": "consumers", "ru": "потребители", "zh": "个人用户", "vi": "người tiêu dùng", "id": "konsumen",
                 "ms": "pengguna", "bench": "consumer"},
}
# Query templates: {ind} industry, {cat} category, {country}, {year}, {unit}, {role}
Q = {
    "en": {"count": "number of {size} {ind} establishments {country} {year} official statistics",
           "industry_revenue": "{ind} total sales revenue {country} {year} official statistics",
           "industry_growth": "{ind} sales growth year over year {country} {year}",
           "wage": "median hourly wage {role} {ind} {country} {year}",
           "competitor_pricing": "{cat} software pricing per {unit} per month",
           "adoption": "share of {size} using {cat} software survey {country}",
           "market_report": "{cat} software market size {country} {year} CAGR",
           "inflation": "consumer price inflation {country} latest official",
           "risk_free": "10-year government bond yield {country} today",
           "multiples": "EV/Sales software industry dataset {year}"},
    "ru": {"count": "количество {size} {ind} Россия {year} единый реестр МСП статистика",
           "industry_revenue": "оборот {ind} {year} Росстат млрд рублей",
           "industry_growth": "рост оборота {ind} {year} Росстат в сопоставимых ценах",
           "wage": "средняя заработная плата {role} {ind} {year} Росстат",
           "competitor_pricing": "{cat} сервис тарифы цена за {unit} в месяц",
           "adoption": "доля {size} использующих {cat} исследование",
           "market_report": "рынок {cat} Россия {year} объём рост",
           "inflation": "инфляция {year} Росстат годовая",
           "risk_free": "ключевая ставка Банк России доходность ОФЗ 10 лет",
           "multiples": "EV/Sales software industry dataset {year}"},
    "zh": {"count": "{country} {ind} {size} 数量 {year} 统计公报",
           "industry_revenue": "{country} {ind} 营业收入 {year} 国家统计局",
           "industry_growth": "{country} {ind} 增长 {year} 国家统计局",
           "wage": "{country} {ind} {role} 平均工资 {year}",
           "competitor_pricing": "{cat} 软件 价格 每{unit} 每月",
           "adoption": "{size} {cat} 软件 使用率 调查",
           "market_report": "{country} {cat} 市场规模 {year} 复合增长率",
           "inflation": "{country} CPI 同比 最新 国家统计局",
           "risk_free": "中国 10年期国债收益率 最新",
           "multiples": "EV/Sales software industry dataset {year}"},
    "vi": {"count": "số lượng {size} {ind} {country} {year} Tổng cục Thống kê",
           "industry_revenue": "doanh thu {ind} {country} {year} thống kê",
           "industry_growth": "tăng trưởng {ind} {country} {year}",
           "wage": "thu nhập bình quân {role} {ind} {country} {year}",
           "competitor_pricing": "phần mềm {cat} bảng giá mỗi {unit} mỗi tháng",
           "adoption": "tỷ lệ {size} sử dụng phần mềm {cat} khảo sát",
           "market_report": "thị trường phần mềm {cat} {country} {year}",
           "inflation": "CPI {country} mới nhất Tổng cục Thống kê",
           "risk_free": "lợi suất trái phiếu chính phủ 10 năm Việt Nam",
           "multiples": "EV/Sales software industry dataset {year}"},
    "id": {"count": "jumlah {size} {ind} {country} {year} BPS",
           "industry_revenue": "pendapatan {ind} {country} {year} BPS",
           "industry_growth": "pertumbuhan {ind} {country} {year}",
           "wage": "upah rata-rata {role} {ind} {country} {year} BPS",
           "competitor_pricing": "harga software {cat} per {unit} per bulan",
           "adoption": "persentase {size} menggunakan software {cat} survei",
           "market_report": "ukuran pasar software {cat} {country} {year}",
           "inflation": "inflasi {country} terbaru BPS",
           "risk_free": "imbal hasil SBN 10 tahun terbaru",
           "multiples": "EV/Sales software industry dataset {year}"},
    "ms": {"count": "bilangan {size} {ind} {country} {year} DOSM",
           "industry_revenue": "hasil jualan {ind} {country} {year} DOSM",
           "industry_growth": "pertumbuhan jualan {ind} {country} {year}",
           "wage": "gaji median {role} {ind} {country} {year} DOSM",
           "competitor_pricing": "harga perisian {cat} setiap {unit} sebulan",
           "adoption": "peratusan {size} menggunakan perisian {cat} tinjauan",
           "market_report": "saiz pasaran perisian {cat} {country} {year}",
           "inflation": "inflasi {country} terkini DOSM",
           "risk_free": "hasil MGS 10 tahun terkini",
           "multiples": "EV/Sales software industry dataset {year}"},
}

RESEARCH_KEYS = [
    ("count", "Number of target organisations / locations per segment (official business registers, industry statistics)",
     "official statistics", "proxy: total SMEs × industry share × size-band share (estimate)"),
    ("industry_revenue", "Total sales of the buyer industries (for the top-down cross-check)", "official statistics",
     "proxy: units × average revenue per unit (estimate)"),
    ("industry_growth", "Nominal growth of the buyer industries (base for CAGR)", "official statistics",
     "inflation + real GDP growth (estimate)"),
    ("wage", "Hourly cost of the roles whose time the product saves (value-based price, customer ROI)",
     "official wage statistics", "national average wage × role factor (estimate)"),
    ("competitor_pricing", "Price per unit of comparable products (range)", "public pricing pages",
     "value-based price = hours saved × hourly cost × 10–30 % capture (estimate)"),
    ("adoption", "Share of the segment that already uses / plans category software", "surveys, statistics on ICT use",
     "rule-of-thumb adoption range from config/benchmarks.json (estimate, low confidence)"),
    ("market_report", "Published category market size and CAGR (cross-check only — cite the publisher and year)",
     "industry reports with a public summary", "not required: triangulated TAM is used"),
    ("inflation", "Latest official inflation (nominal vs real model)", "statistics office / central bank",
     "central-bank target (estimate)"),
    ("risk_free", "Risk-free rate for the discount rate (policy rate or 10-year government bond)", "central bank / treasury",
     "last known policy rate (estimate)"),
    ("multiples", "Listed-peer EV/Revenue multiple for software", "public industry datasets of a university",
     "rule-of-thumb multiple range from config/benchmarks.json (estimate)"),
]


def official_sources(market: str) -> list[dict]:
    """Rows of the '| Need | Source | Link |' table in markets/<market>.md (section 1)."""
    path = os.path.join(ROOT, "markets", f"{market}.md")
    out = []
    if not os.path.exists(path):
        return out
    in_table = False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if re.match(r"^\|\s*Need\s*\|", line):
                in_table = True
                continue
            if in_table:
                if not line.startswith("|"):
                    break
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if set(cells[0]) <= {"-", " "}:
                    continue
                if len(cells) >= 3:
                    out.append({"need": cells[0], "source": cells[1],
                                "links": re.findall(r"https?://[^\s·|)]+", cells[2])})
    return out


def define(profile_doc: dict, market: str | None = None, year: int | None = None, taxonomy: dict | None = None,
           max_industries: int = 3) -> dict:
    import datetime as _dt
    tax = taxonomy or load_json(TAX_PATH)
    P = profile_doc.get("profile", profile_doc)
    mk = market or (P.get("geography") or ["en"])[0]
    lang = LANG_OF.get(mk, "en")
    yr = year or _dt.date.today().year
    cat = tax["categories"].get(P.get("category") or "data_analytics")
    cat_name_en = cat["label_en"].split(" (")[0]
    cat_name = cat.get(f"label_{lang}", cat_name_en).split(" (")[0] if lang == "ru" else cat_name_en
    segs_in = [s for s in (P.get("buyer_segment") or ["smb"]) if s in SIZE_BANDS]
    inds = (P.get("buyer_industries") or cat["buyer_industries"])[:max_industries]
    segments = []
    for s in segs_in[:3]:
        for ind in inds:
            ind_en = tax["isic_sections"].get(ind, ind)
            ind_l = ISIC_RU.get(ind) if lang == "ru" else (ISIC_ZH.get(ind) if lang == "zh" else ind_en)
            segments.append({"id": f"{s}_{ind}", "size_band": s, "isic": ind, "industry_en": ind_en,
                             "industry": ind_l, "name": f"{SIZE_BANDS[s].get(lang, SIZE_BANDS[s]['en'])} · {ind_l}",
                             "benchmark_segment": SIZE_BANDS[s]["bench"], "unit": cat["unit"],
                             "classification": tax["classifications"].get(mk, {}).get("name")})
    country = COUNTRY.get(mk, {}).get(lang) or COUNTRY.get(mk, {}).get("en", mk)
    role = (cat.get("user_roles") or ["manager"])[0]
    T = Q.get(lang, Q["en"])
    queries = []
    for key, what, pref, fallback in RESEARCH_KEYS:
        tpl = T[key]
        targets = segments if key in ("count", "industry_revenue", "industry_growth", "adoption") else [None]
        seen = set()
        for sg in targets:
            ind = sg["industry"] if sg else (segments[0]["industry"] if segments else "")
            size = SIZE_BANDS[sg["size_band"]].get(lang, SIZE_BANDS[sg["size_band"]]["en"]) if sg else ""
            q = tpl.format(ind=ind, size=size, cat=cat_name, country=country, year=yr - 1, unit=cat["unit"], role=role)
            q = re.sub(r"\s+", " ", q).strip()
            if q in seen:
                continue
            seen.add(q)
            queries.append({"key": key, "segment": sg["id"] if sg else None, "query": q, "lang": lang})
            if lang != "en" and key in ("competitor_pricing", "market_report"):
                qe = Q["en"][key].format(ind=sg["industry_en"] if sg else "", size="", cat=cat_name_en,
                                         country=COUNTRY.get(mk, {}).get("en", mk), year=yr - 1, unit=cat["unit"], role=role)
                queries.append({"key": key, "segment": sg["id"] if sg else None, "query": re.sub(r"\s+", " ", qe).strip(),
                                "lang": "en"})
    plan = [{"key": k, "what": w, "preferred_source": p, "fallback_estimate": f,
             "per_segment": k in ("count", "industry_revenue", "industry_growth", "adoption")}
            for k, w, p, f in RESEARCH_KEYS]
    seg_primary = segs_in[0] if segs_in else "smb"
    icp = {"size_band": seg_primary, "industries": inds[:2], "buyer_roles": cat["buyer_roles"],
           "user_roles": cat["user_roles"], "pains": cat["value_drivers"],
           "trigger": {"workforce_management": "opening a new location, high staff turnover, overtime complaints, payroll errors"}
           .get(P.get("category"), "growth that breaks the manual process; a compliance or audit requirement"),
           "deal": {"unit": cat["unit"], "price_metric": cat["price_metric"], "benchmark_segment": SIZE_BANDS[seg_primary]["bench"]}}
    definition = {"category": P.get("category"), "category_label": cat.get(f"label_{lang}", cat["label_en"]),
                  "market": mk, "locale": lang, "country": country, "unit": cat["unit"], "price_metric": cat["price_metric"],
                  "sentence_en": f"Spend of {', '.join(SIZE_BANDS[s]['en'] for s in segs_in)} in "
                                 f"{', '.join(tax['isic_sections'].get(i, i) for i in inds)} ({COUNTRY.get(mk, {}).get('en', mk)}) "
                                 f"on {cat_name_en.lower()} software, priced {cat['price_metric']}.",
                  "classification": tax["classifications"].get(mk)}
    return {"definition": definition, "segments": segments, "icp": icp, "research_plan": plan,
            "queries": queries, "official_sources": official_sources(mk), "year": yr}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", "-i", required=True, help="profile.json from product_profiler.py")
    ap.add_argument("--market", "-m", choices=["ru", "en", "zh", "vn", "id", "my"])
    ap.add_argument("--year", type=int)
    ap.add_argument("--out", "-o")
    a = ap.parse_args(argv)
    print(dump_json(define(load_json(a.input), a.market, a.year), a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
