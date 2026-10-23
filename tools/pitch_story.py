#!/usr/bin/env python3
"""pitch_story.py — turns computed facts + a pitch pattern into deck_spec.json and report_spec.json.

Every number is a {{placeholder}} resolved from facts.json (namespaces market.*, fin.*, score.*, auto.*),
so the deck and the report cannot drift apart. Narrative text exists in Russian and English; other
locales (zh, vi, id, ms) get the English narrative with localized number formats, chart labels and
citations — auto_pitch.py reports this as a warning so a native speaker can localize the text.

Slide ids (pattern slide_order): title, hook, customer_hook, smb_hook, problem, customer_problem,
solution, why_now, market_sizing, segments, market_growth, competition, business_model, pricing,
unit_economics, gtm, financials, fin_scenarios, valuation, risks, evidence, ask, closing,
customer_roi, tco, implementation, vendor_viability, pilot_offer, smb_value, how_to_start,
closing_smb, public_effect, regulatory, scorecard.
"""
from __future__ import annotations

import json
import re

STORY_LOCALES = ("ru", "en")

UNITS = {"location": {"ru": ("точка", "точек", "точку"), "en": ("location", "locations", "location")},
         "organisation": {"ru": ("организация", "организаций", "организацию"), "en": ("organisation", "organisations", "organisation")},
         "company": {"ru": ("компания", "компаний", "компанию"), "en": ("company", "companies", "company")},
         "employee seat": {"ru": ("рабочее место", "рабочих мест", "рабочее место"), "en": ("seat", "seats", "seat")},
         "clinic": {"ru": ("клиника", "клиник", "клинику"), "en": ("clinic", "clinics", "clinic")}}


def unit_words(unit: str, lang: str):
    u = UNITS.get(unit) or UNITS["company"]
    return u.get(lang, u["en"])


# Category-specific wording; anything missing falls back to GENERIC. Add a pack for your category.
GENERIC = {
    "role": {"ru": "сотрудника", "en": "an employee"},
    "start_title": {"ru": "Как начать: три шага от регистрации до первого результата", "en": "How to start: three steps from sign-up to the first result"},
    "smb_close_b2": {"ru": "Помесячная оплата, отмена в любой месяц", "en": "Monthly billing, cancel any month"},
    "gtm": {"ru": ["0–6 мес.|Первые 100|прямые продажи и рекомендации", "6–12 мес.|Самообслуживание|пробный период, быстрый онбординг",
                   "12–24 мес.|Партнёры|интеграторы, консультанты, маркетплейсы", "24+ мес.|Крупные клиенты|корпоративный тариф и интеграции"],
            "en": ["0–6 mo|First 100|direct sales and referrals", "6–12 mo|Self-serve|free trial, fast onboarding",
                   "12–24 mo|Partners|integrators, consultants, marketplaces", "24+ mo|Larger accounts|enterprise plan and integrations"]},
    "task": {"ru": "ручную работу", "en": "the manual work"},
    "cust_problem_title": {"ru": "Ручной процесс стоит {{auto.cust.manual_cost_month|money0}} в месяц на одну {uacc}",
                           "en": "The manual process costs {{auto.cust.manual_cost_month|money0}} a month per {u1}"},
    "cust_problem_b1": {"ru": "**{{auto.cust.hours_saved_month|num0}} ч в месяц** ручных операций (оценка)",
                        "en": "**{{auto.cust.hours_saved_month|num0}} hours a month** of manual operations (estimate)"},
    "cust_problem_b3": {"ru": "Ошибки ручного ввода — прямые потери", "en": "Manual-entry errors are direct losses"},
    "cust_problem_b4": {"ru": "Таблицы и мессенджеры не масштабируются", "en": "Spreadsheets and messengers do not scale"},
    "why_now_b4": {"ru": "Облачные и мобильные сервисы стали нормой для малого бизнеса", "en": "Cloud and mobile tools are now the norm for small businesses"},
    "x_label": {"ru": "Простота запуска", "en": "Ease of start"}, "y_label": {"ru": "Глубина автоматизации", "en": "Depth of automation"},
    "impl": {"ru": ["Настройка|импорт данных, правила", "Пилот|5 {un}, обучение", "Замер|часы, ошибки, скорость", "Решение|тиражирование"],
             "en": ["Set-up|data import, rules", "Pilot|5 {un}, training", "Measure|hours, errors, speed", "Decision|roll-out"]},
    "start": {"ru": ["Регистрация|за 2 минуты", "Данные|загрузите из таблицы", "Работа|первый результат в тот же день"],
              "en": ["Sign up|in 2 minutes", "Data|import from a spreadsheet", "Work|first result the same day"]},
    "pilot_criteria": {"ru": "Критерии успеха: −{{auto.cust.hours_saved_month|num0}} ч в месяц на {uacc}, ноль ошибок",
                       "en": "Success criteria: −{{auto.cust.hours_saved_month|num0}} hours a month per {u1}, zero errors"},
    "y_auto_note": {"ru": "", "en": ""},
}
STORY_PACKS = {
    "workforce_management": {
        "role": {"ru": "руководителя смены", "en": "a shift manager"},
        "start_title": {"ru": "Старт за 15 минут: три шага, без оборудования и договора", "en": "Start in 15 minutes: three steps, no hardware, no contract"},
        "smb_close_b2": {"ru": "Поддержка в мессенджере 7 дней в неделю", "en": "Chat support 7 days a week"},
        "gtm": {"ru": ["0–6 мес.|Первые 100|прямые продажи в 2 городах, отзывы", "6–12 мес.|Самообслуживание|пробный период, онбординг за 15 минут",
                       "12–24 мес.|Партнёры|кассовые и учётные системы, бухгалтеры", "24+ мес.|Сети|средние сети, интеграции с HR"],
                "en": ["0–6 mo|First 100|direct sales in 2 cities, referrals", "6–12 mo|Self-serve|free trial, 15-minute onboarding",
                       "12–24 mo|Partners|POS and accounting vendors, bookkeepers", "24+ mo|Chains|mid-size chains, HR integrations"]},
        "task": {"ru": "графики, замены и табель", "en": "schedules, swaps and timesheets"},
        "cust_problem_title": {"ru": "Ручное планирование смен стоит {{auto.cust.manual_cost_month|money0}} в месяц на одну {uacc}",
                               "en": "Manual shift planning costs {{auto.cust.manual_cost_month|money0}} a month per {u1}"},
        "cust_problem_b1": {"ru": "**{{auto.cust.hours_saved_month|num0}} ч в месяц** — составление графиков, замены, сверка табеля (оценка)",
                            "en": "**{{auto.cust.hours_saved_month|num0}} hours a month** — building schedules, swaps, checking timesheets (estimate)"},
        "cust_problem_b3": {"ru": "Ошибки табеля и переработки — прямые потери фонда оплаты труда", "en": "Timesheet errors and overtime leak straight out of payroll"},
        "cust_problem_b4": {"ru": "Таблицы и мессенджеры не масштабируются на несколько точек", "en": "Spreadsheets and messengers do not scale across locations"},
        "why_now_b4": {"ru": "Смартфон есть у каждого сотрудника — учёт времени без терминалов", "en": "Every employee carries a smartphone — time tracking without hardware terminals"},
        "x_label": {"ru": "Простота запуска для малого бизнеса", "en": "Ease of start for a small business"},
        "y_label": {"ru": "Автоматизация (график, учёт, расчёт)", "en": "Automation (schedule, tracking, payroll)"},
        "impl": {"ru": ["Настройка|импорт сотрудников, правила смен", "Пилот|5 {un}, обучение менеджеров", "Замер|часы на график, переработки, ошибки табеля", "Решение|тиражирование на сеть"],
                 "en": ["Set-up|import staff, shift rules", "Pilot|5 {un}, manager training", "Measure|hours on scheduling, overtime, timesheet errors", "Decision|roll out to the chain"]},
        "start": {"ru": ["Сотрудники|добавьте команду из телефона", "График|получите черновик графика на неделю", "Учёт|сотрудники отмечаются в приложении"],
                  "en": ["Staff|add your team from your phone", "Schedule|get a draft weekly schedule", "Tracking|staff clock in from the app"]},
        "pilot_criteria": {"ru": "Критерии успеха: −{{auto.cust.hours_saved_month|num0}} ч в месяц на {uacc}, ноль ошибок табеля",
                           "en": "Success criteria: −{{auto.cust.hours_saved_month|num0}} hours a month per {u1}, zero timesheet errors"},
    },
}


NOTES = {
    "market_sizing": {"ru": "Снизу вверх — основной метод: число точек из официальной статистики × цена. Сверху вниз и по ценности — проверка; расхождение больше 2× означает, что входы надо пересмотреть.",
                      "en": "Bottom-up is primary: official counts × price. Top-down and value-based are checks; a spread above 2× means the inputs need another look."},
    "market_growth": {"ru": "CAGR — оценка: номинальный рост отраслей покупателя и рост проникновения категории. Диапазон показывает неопределённость.",
                      "en": "CAGR is an estimate: nominal growth of buyer industries plus category penetration growth. The range shows the uncertainty."},
    "unit_economics": {"ru": "Эталонные диапазоны — эмпирические правила для SaaS в сегменте; их заменят когортные данные.",
                       "en": "Benchmark ranges are SaaS rules of thumb for the segment; cohort data will replace them."},
    "valuation": {"ru": "Мультипликатор — медиана публичных компаний; дисконт за непубличность и стадию — эмпирическое правило.",
                  "en": "The multiple is a listed-peer figure; the private / stage discount is a rule of thumb."},
    "customer_roi": {"ru": "Выгода считается от сэкономленных часов; до пилота это оценка, после пилота — замер.",
                     "en": "The benefit comes from hours saved; an estimate before the pilot, a measurement after it."},
    "segments": {"ru": "Каждая строка — проверяемое допущение: единицы × цена × доступная доля × достижимая доля.",
                 "en": "Each row is a testable assumption: units × price × serviceable share × obtainable share."},
}

class Story:
    def __init__(self, ctx: dict, pattern: dict, locale: str):
        self.c = ctx
        self.p = pattern
        self.loc = locale
        self.lang = locale if locale in STORY_LOCALES else "en"
        self.u1, self.un, self.uacc = unit_words(ctx.get("unit", "company"), self.lang)
        self.pack = {**GENERIC, **STORY_PACKS.get(ctx.get("category"), {})}

    def k(self, key: str):
        v = self.pack[key]
        v = v.get(self.lang, v["en"])
        fill = lambda x: x.replace("{u1}", self.u1).replace("{un}", self.un).replace("{uacc}", self.uacc)
        return [fill(x) for x in v] if isinstance(v, list) else fill(v)

    # ---------------------------------------------------------------- helpers
    def t(self, ru: str, en: str) -> str:
        """Pick the narrative language; wording written for 'location' adapts to the category's unit."""
        if self.lang == "ru":
            return (ru.replace("за точку", f"за {self.uacc}").replace("На одну точку", f"На одну {self.uacc}")
                    .replace("на точку", f"на {self.uacc}").replace(" точек", f" {self.un}"))
        return (en.replace("per location", f"per {self.u1}").replace("-location chain", f"-{self.u1} chain")
                .replace(" locations", f" {self.un}").replace("Per location", f"Per {self.u1}"))

    def src(self, kind: str) -> str:
        S = self.c.get("sources_by_kind", {}).get(kind) or []
        est = self.t("оценки и формулы — реестр допущений (research_ledger, estimator.py)",
                     "estimates and formulas — evidence ledger (research_ledger, estimator.py)")
        if S:
            return "; ".join(S[:3]) + "; " + est
        return est

    def fict(self) -> str:
        return self.c.get("fiction_note", "")

    # ---------------------------------------------------------------- slides
    def s_title(self):
        n = self.c["name"]
        return {"layout": "title", "title": f"{n}: {self.c['tagline']}",
                "subtitle": self.p.get(f"label_{self.lang}", self.p.get("label_en")) + " · " + self.c["country_label"],
                "kicker": self.c.get("kicker", ""), "author": self.c.get("author", ""), "date": self.c["date"],
                "notes": self.t("Паттерн питча: ", "Pitch pattern: ") + self.p["id"] + ". " + self.fict()}

    def s_hook(self):
        n = self.c["name"]
        return {"layout": "big_number",
                "title": self.t(f"{n}: доступный рынок {{{{market.sam_base|money1}}}} растёт на {{{{market.cagr_base|pct0}}}} в год, LTV/CAC — {{{{auto.ue.ltv_cac|x1}}}}",
                                f"{n}: a {{{{market.sam_base|money1}}}} serviceable market growing {{{{market.cagr_base|pct0}}}} a year, LTV/CAC {{{{auto.ue.ltv_cac|x1}}}}"),
                "numbers": [
                    {"value": "{{market.sam_base|money1}}", "label": self.t("Доступный рынок (SAM), {{market.base_year}}", "Serviceable market (SAM), {{market.base_year}}"),
                     "context": self.t("снизу вверх; расхождение с методом сверху вниз — {{auto.market.tam_ratio|x1}}", "bottom-up; spread vs top-down {{auto.market.tam_ratio|x1}}")},
                    {"value": "{{market.cagr_base|pct0}}", "label": self.t("CAGR рынка, базовый сценарий", "Market CAGR, base case"),
                     "context": self.t("диапазон {{market.cagr_bear|pct0}}–{{market.cagr_bull|pct0}}", "range {{market.cagr_bear|pct0}}–{{market.cagr_bull|pct0}}")},
                    {"value": "{{auto.ue.ltv_cac|x1}}", "label": "LTV/CAC", "context": self.t("окупаемость CAC {{auto.ue.payback|num0}} мес.", "CAC payback {{auto.ue.payback|num0}} months")},
                    {"value": "{{fin.revenue_last|money1}}", "label": self.t("Выручка {{fin.end_year}}", "Revenue {{fin.end_year}}"),
                     "context": "{{auto.breakeven_phrase}}"}],
                "source": self.src("market"),
                "notes": self.t("Каждая цифра — либо источник, либо оценка с формулой (см. слайд о доказательствах).",
                                "Every number is either sourced or a labelled estimate with its formula (see the evidence slide).")}

    def s_customer_hook(self):
        n = self.c["name"]
        return {"layout": "big_number",
                "title": self.t(f"{n} окупается за {{{{auto.cust.payback_months|num0}}}} мес.: ROI {{{{auto.cust.roi|pct0}}}} за 3 года на {{{{auto.cust.deal_units|num0}}}} {self.un}",
                                f"{n} pays back in {{{{auto.cust.payback_months|num0}}}} months: {{{{auto.cust.roi|pct0}}}} 3-year ROI for {{{{auto.cust.deal_units|num0}}}} {self.un}"),
                "numbers": [
                    {"value": "{{auto.cust.roi|pct0}}", "label": self.t("ROI за 3 года", "3-year ROI"), "context": self.t("выгода минус затраты, к затратам", "benefit minus cost, over cost")},
                    {"value": self.t("{{auto.cust.payback_months|num0}} мес.", "{{auto.cust.payback_months|num0}} months"), "label": self.t("Окупаемость (payback)", "Payback"),
                     "context": self.t("с учётом внедрения и разгона в 1-й год", "incl. implementation and year-1 ramp")},
                    {"value": "{{auto.cust.saving_3y_deal|money1}}", "label": self.t("Экономия за 3 года", "3-year saving"), "context": self.t("TCO против текущего процесса", "TCO versus the current process")}],
                "source": self.src("customer")}

    def s_smb_hook(self):
        return {"layout": "big_number",
                "title": self.t("Платите {{auto.price_month|money0}} в месяц за точку — возвращаете {{auto.cust.saving_month|money0}} рабочего времени",
                                "Pay {{auto.price_month|money0}} a month per location — get back {{auto.cust.saving_month|money0}} of working time"),
                "numbers": [
                    {"value": "{{auto.price_month|money0}}", "label": self.t("цена в месяц за точку", "price per location per month"), "context": self.t("без договора, отмена в любой месяц", "no contract, cancel any month")},
                    {"value": "{{auto.cust.saving_month|money0}}", "label": self.t("экономия в месяц", "saving per month"),
                     "context": self.t("{{auto.cust.hours_saved_month|num0}} ч × {{auto.cust.hourly_cost|money0}} за час", "{{auto.cust.hours_saved_month|num0}} h × {{auto.cust.hourly_cost|money0}} per hour")},
                    {"value": "{{auto.cust.value_ratio|x1}}", "label": self.t("экономия к цене", "saving to price"), "context": self.t("окупаемость (payback) — первый месяц", "payback — the first month")}],
                "source": self.src("customer")}

    def s_problem(self):
        d = self.c["drivers"]
        return {"layout": "bullets",
                "title": self.t(f"{{{{auto.market.units_total|num0}}}} {self.un} планируют смены и учёт вручную — менеджер теряет до {{{{auto.cust.hours_saved_month|num0}}}} ч в месяц",
                                f"{{{{auto.market.units_total|num0}}}} {self.un} still run scheduling by hand — a manager loses up to {{{{auto.cust.hours_saved_month|num0}}}} hours a month")
                if self.c.get("category") == "workforce_management" else
                self.t(f"{{{{auto.market.units_total|num0}}}} {self.un} решают задачу вручную — до {{{{auto.cust.hours_saved_month|num0}}}} ч в месяц на каждую",
                       f"{{{{auto.market.units_total|num0}}}} {self.un} solve this by hand — up to {{{{auto.cust.hours_saved_month|num0}}}} hours a month each"),
                "bullets": [
                    self.t(f"**{{{{auto.market.units_total|num0}}}} {self.un}** в целевых сегментах ({self.c['country_label']})",
                           f"**{{{{auto.market.units_total|num0}}}} {self.un}** in the target segments ({self.c['country_label']})"),
                    self.t(f"Час работы {self.k('role')} стоит **{{{{auto.cust.hourly_cost|money0}}}}**", f"An hour of {self.k('role')} costs **{{{{auto.cust.hourly_cost|money0}}}}**"),
                    self.t("До **{{auto.cust.hours_saved_month|num0}} ч в месяц** ручной работы можно высвободить (оценка)",
                           "Up to **{{auto.cust.hours_saved_month|num0}} hours a month** of manual work can be freed (estimate)"),
                    self.t("Где теряются деньги: ", "Where money leaks: ") + ", ".join(d[:3])],
                "source": self.src("problem")}

    def s_customer_problem(self):
        return {"layout": "bullets", "title": self.k("cust_problem_title"),
                "bullets": [self.k("cust_problem_b1"),
                            self.t(f"**{{{{auto.cust.hourly_cost|money0}}}}** — стоимость часа {self.k('role')} с учётом взносов",
                                   f"**{{{{auto.cust.hourly_cost|money0}}}}** — loaded hourly cost of {self.k('role')}"),
                            self.k("cust_problem_b3"), self.k("cust_problem_b4")],
                "source": self.src("customer")}

    def s_solution(self):
        n = self.c["name"]
        return {"layout": "two_column",
                "title": self.t(f"Решение: {n} — {self.c['tagline']}", f"Solution: {n} — {self.c['tagline']}"),
                "left": {"heading": self.t("Сегодня", "Today"), "bullets": self.c["today"][:4]},
                "right": {"heading": self.t(f"С {n}", f"With {n}"), "bullets": self.c["features"][:4]},
                "notes": self.t("Лучше всего здесь работает живая демонстрация.", "A live demo works best here.")}

    def s_why_now(self):
        return {"layout": "bullets",
                "title": self.t("Почему сейчас: отрасли покупателя растут на {{auto.market.industry_growth|pct1}} в год, а час труда дорожает",
                                "Why now: buyer industries grow {{auto.market.industry_growth|pct1}} a year and labour keeps getting dearer"),
                "bullets": [
                    self.t("Номинальный рост оборота отраслей покупателя — **{{auto.market.industry_growth|pct1}}**", "Nominal sales growth of the buyer industries — **{{auto.market.industry_growth|pct1}}**"),
                    self.t(f"Стоимость часа {self.k('role')} — **{{{{auto.cust.hourly_cost|money0}}}}**: каждый сэкономленный час заметен", f"An hour of {self.k('role')} costs **{{{{auto.cust.hourly_cost|money0}}}}**: every saved hour shows up"),
                    self.t("Проникновение категории: **{{auto.market.pen_start|pct0}} → {{auto.market.pen_end|pct0}}** к {{market.horizon_year}} (оценка)",
                           "Category penetration: **{{auto.market.pen_start|pct0}} → {{auto.market.pen_end|pct0}}** by {{market.horizon_year}} (estimate)"),
                    self.k("why_now_b4")],
                "source": self.src("growth")}

    def s_market_sizing(self):
        return {"layout": "chart",
                "title": self.t("TAM {{market.tam_base|money1}}, SAM {{market.sam_base|money1}}; SOM к {{market.horizon_year}} — {{market.som_horizon_base|money1}}",
                                "TAM {{market.tam_base|money1}}, SAM {{market.sam_base|money1}}; SOM by {{market.horizon_year}} is {{market.som_horizon_base|money1}}"),
                "chart": {"$ref": "charts.tam_sam_som"},
                "takeaway": [
                    self.t(f"Снизу вверх: {{{{auto.market.units_total|num0}}}} {self.un} × {{{{auto.price_year|money0}}}} в год", f"Bottom-up: {{{{auto.market.units_total|num0}}}} {self.un} × {{{{auto.price_year|money0}}}} a year"),
                    self.t("Сверху вниз: оборот отраслей × доля ИТ × доля категории = {{auto.market.tam_td|money1}}", "Top-down: industry sales × IT share × category share = {{auto.market.tam_td|money1}}"),
                    self.t("По ценности: {{auto.market.tam_vt|money1}}; расхождение методов {{auto.market.tam_ratio|x1}}", "Value-based: {{auto.market.tam_vt|money1}}; spread between methods {{auto.market.tam_ratio|x1}}")],
                "source": self.src("market") + "; {{project.units.bn}}"}

    def s_segments(self):
        return {"layout": "table",
                "title": self.t("Сегменты: число организаций — из официальной статистики, цена и доли — оценки с диапазонами",
                                "Segments: organisation counts from official statistics; price and shares are ranged estimates"),
                "columns": self.t("Сегмент|Единиц|Цена в год|TAM|SAM|SOM {{market.horizon_year}}", "Segment|Units|Price per year|TAM|SAM|SOM {{market.horizon_year}}").split("|"),
                "rows": {"$ref": "tables.segments"}, "col_widths": [4.4, 1.6, 1.7, 1.5, 1.5, 1.4], "source": self.src("market")}

    def s_market_growth(self):
        ch = {"$ref": "charts.sam_scenarios"}
        return {"layout": "chart",
                "title": self.t("CAGR {{market.cagr_base|pct0}} в базовом сценарии: рост отраслей плюс рост проникновения",
                                "CAGR {{market.cagr_base|pct0}} in the base case: industry growth plus rising penetration"),
                "chart": ch,
                "takeaway": [
                    self.t("CAGR = (1 + рост отраслей) × (рост проникновения)^(1/лет) − 1", "CAGR = (1 + industry growth) × (penetration growth)^(1/years) − 1"),
                    self.t("Негативный {{market.cagr_bear|pct0}} · базовый {{market.cagr_base|pct0}} · позитивный {{market.cagr_bull|pct0}}", "Bear {{market.cagr_bear|pct0}} · base {{market.cagr_base|pct0}} · bull {{market.cagr_bull|pct0}}"),
                    self.t("SAM {{market.horizon_year}}: {{market.sam_horizon_base|money1}} (база)", "SAM {{market.horizon_year}}: {{market.sam_horizon_base|money1}} (base)")],
                "source": self.src("growth") + "; {{project.units.bn}}"}

    def s_competition(self):
        n = self.c["name"]
        A = self.c["alternatives"]
        return {"layout": "matrix",
                "title": self.t(f"Против альтернатив: {n} проще корпоративных систем и надёжнее таблиц",
                                f"Versus alternatives: {n} is simpler than enterprise suites and more reliable than spreadsheets"),
                "x_label": self.k("x_label"), "y_label": self.k("y_label"),
                "quadrants": ["", self.t("Целевая позиция", "Target position"), "", ""],
                "items": [{"name": A[0], "x": 0.75, "y": 0.15}, {"name": A[1], "x": 0.6, "y": 0.35},
                          {"name": A[2], "x": 0.2, "y": 0.85}, {"name": n, "x": 0.82, "y": 0.8, "highlight": True}],
                "takeaway": [self.t("Позиции — качественная оценка команды, не измерение", "Positions are the team's qualitative view, not a measurement"),
                             self.t("Риск: крупные игроки упростят свои продукты", "Risk: large vendors may simplify their products")],
                "source": self.t("качественная оценка (команда); проверить на интервью с клиентами", "qualitative assessment (team); validate in customer interviews")}

    def s_business_model(self):
        return {"layout": "big_number",
                "title": self.t(f"Подписка {{{{auto.price_month|money0}}}} в месяц за {self.uacc}; валовая маржа {{{{auto.ue.gm|pct0}}}}",
                                f"Subscription at {{{{auto.price_month|money0}}}} per {self.u1} per month; gross margin {{{{auto.ue.gm|pct0}}}}"),
                "numbers": [
                    {"value": "{{auto.price_month|money0}}", "label": self.t("в месяц за точку", "per location per month"),
                     "context": self.t("{{auto.price_basis}}", "{{auto.price_basis}}")},
                    {"value": "{{auto.price_year|money0}}", "label": self.t("годовой чек на точку", "annual contract per location"), "context": self.t("ARPA для модели", "ARPA used in the model")},
                    {"value": "{{auto.ue.gm|pct0}}", "label": self.t("валовая маржа", "gross margin"), "context": self.t("эталонный диапазон: от {{auto.ue.gm_low|pct0}} до {{auto.ue.gm_high|pct0}}", "benchmark range: {{auto.ue.gm_low|pct0}} to {{auto.ue.gm_high|pct0}}")}],
                "source": self.src("pricing")}

    def s_pricing(self):
        return {"layout": "bullets",
                "title": self.t("Один тариф: {{auto.price_month|money0}} в месяц за точку, первые 14 дней бесплатно",
                                "One plan: {{auto.price_month|money0}} per location per month, first 14 days free"),
                "bullets": [self.t("**{{auto.price_month|money0}}** в месяц за точку — все сотрудники включены", "**{{auto.price_month|money0}}** per location per month — all staff included"),
                            self.t("Годовая оплата — **{{auto.price_year_discounted|money0}}** (скидка 2 месяца)", "Pay yearly — **{{auto.price_year_discounted|money0}}** (2 months free)"),
                            self.t("Экономия **{{auto.cust.saving_month|money0}}** в месяц — в {{auto.cust.value_ratio|x1}} больше цены", "Saving of **{{auto.cust.saving_month|money0}}** a month — {{auto.cust.value_ratio|x1}} the price"),
                            self.t("Без договора и оборудования, отмена в любой месяц", "No contract, no hardware, cancel any month")],
                "notes": self.t("Условия (14 дней бесплатно, скидка за год, отмена в любой месяц) — рекомендуемая конструкция предложения для паттерна МСП; замените фактическими условиями. Цена — {{auto.price_basis}}.",
                                "Terms (14-day trial, yearly discount, cancel any month) are the SMB pattern's recommended offer design; replace them with the actual terms. Price: {{auto.price_basis}}."),
                "source": self.src("customer")}

    def s_unit_economics(self):
        return {"layout": "table",
                "title": self.t("Юнит-экономика: LTV/CAC {{auto.ue.ltv_cac|x1}}, окупаемость CAC {{auto.ue.payback|num0}} мес. — по эталонным диапазонам",
                                "Unit economics: LTV/CAC {{auto.ue.ltv_cac|x1}}, CAC payback {{auto.ue.payback|num0}} months — from benchmark ranges"),
                "columns": self.t("Показатель|Низкий|Базовый|Высокий|Основа", "Metric|Low|Base|High|Basis").split("|"),
                "rows": {"$ref": "auto.tables.ue"}, "col_widths": [3.0, 1.5, 1.5, 1.5, 4.6],
                "source": self.src("ue"),
                "notes": self.t("Эталонные диапазоны — эмпирические правила, а не факты; заменить когортными данными после 2 кварталов продаж.",
                                "Benchmark ranges are rules of thumb, not facts; replace with cohort data after two quarters of sales.")}

    def s_gtm(self):
        return {"layout": "timeline",
                "title": self.t("Выход на рынок: самообслуживание и партнёры — CAC {{auto.ue.cac|money0}} на клиента",
                                "Go-to-market: self-serve and partners — CAC {{auto.ue.cac|money0}} per customer"),
                "steps": [dict(zip(("label", "title", "text"), x.split("|"))) for x in self.k("gtm")],
                "source": self.src("ue")}

    def s_financials(self):
        return {"layout": "chart",
                "title": self.t("Выручка {{fin.revenue_last|money1}} к {{fin.end_year}}; {{auto.breakeven_phrase}}",
                                "Revenue reaches {{fin.revenue_last|money1}} by {{fin.end_year}}; {{auto.breakeven_phrase}}"),
                "chart": {"$ref": "charts.revenue_ebitda"},
                "takeaway": [self.t("Клиенты: путь к SOM {{market.som_horizon_base|money1}}", "Customers: path to SOM {{market.som_horizon_base|money1}}"),
                             self.t("Rule of 40 в {{fin.end_year}}: {{fin.rule40_last|pct0}}", "Rule of 40 in {{fin.end_year}}: {{fin.rule40_last|pct0}}"),
                             self.t("Привлечение: {{auto.ask|money1}}; минимум денег {{fin.min_cash|money1}}", "Funding: {{auto.ask|money1}}; minimum cash {{fin.min_cash|money1}}")],
                "source": self.t("financial_model.py на оценках из реестра допущений; {{project.units.mn}}", "financial_model.py on ledger estimates; {{project.units.mn}}")}

    def s_fin_scenarios(self):
        return {"layout": "table",
                "title": self.t("Три сценария: NPV {{fin.npv_bear|money1}} … {{fin.npv_bull|money1}}, MOIC инвестора {{fin.moic_base|x1}} в базе",
                                "Three scenarios: NPV {{fin.npv_bear|money1}} … {{fin.npv_bull|money1}}, investor MOIC {{fin.moic_base|x1}} in the base case"),
                "columns": self.t("Сценарий|Выручка {{fin.end_year}}|EBITDA > 0|NPV|MOIC|IRR", "Scenario|Revenue {{fin.end_year}}|EBITDA > 0|NPV|MOIC|IRR").split("|"),
                "rows": {"$ref": "tables.fin_scenarios"}, "col_widths": [2.4, 2.0, 1.8, 1.8, 1.5, 1.5],
                "source": self.t("financial_model.py; ставка дисконтирования {{fin.discount_rate|pct0}}", "financial_model.py; discount rate {{fin.discount_rate|pct0}}")}

    def s_valuation(self):
        return {"layout": "table",
                "title": self.t("Оценка по аналогам {{auto.val.ev_low|money1}}–{{auto.val.ev_high|money1}} к {{fin.end_year}}; IRR {{fin.irr_base|pct0}}, MOIC {{fin.moic_base|x1}}",
                                "Valuation by comparables {{auto.val.ev_low|money1}}–{{auto.val.ev_high|money1}} by {{fin.end_year}}; IRR {{fin.irr_base|pct0}}, MOIC {{fin.moic_base|x1}}"),
                "columns": self.t("Метод|Низкий|Базовый|Высокий|Основа", "Method|Low|Base|High|Basis").split("|"),
                "rows": {"$ref": "auto.tables.valuation"}, "col_widths": [3.2, 1.6, 1.6, 1.6, 4.1],
                "source": self.src("valuation")}

    def s_risks(self):
        return {"layout": "table",
                "title": self.t("Главные риски — внедрение у пользователей и отток; оба измеримы в первые 2 квартала",
                                "Top risks are user adoption and churn; both are measurable within two quarters"),
                "columns": self.t("Риск|Индикатор|Ответ", "Risk|Indicator|Response").split("|"),
                "rows": {"$ref": "auto.tables.risks"}, "col_widths": [3.4, 3.6, 5.0],
                "source": self.t("анализ рисков команды; пороги — из модели", "team risk review; thresholds from the model")}

    def s_evidence(self):
        return {"layout": "two_column",
                "title": self.t("Доказательная база: фактов с источниками — {{auto.ledger.sourced|num0}}, оценок с формулами — {{auto.ledger.estimates|num0}}",
                                "Evidence: {{auto.ledger.sourced|num0}} sourced facts and {{auto.ledger.estimates|num0}} labelled estimates with formulas"),
                "left": {"heading": self.t("Как получены цифры", "How the numbers were built"), "bullets": [
                    self.t("Источники: официальная статистика, ЦБ/казначейство, отраслевые данные", "Sources: official statistics, central bank / treasury, industry datasets"),
                    self.t("Оценки: сверху вниз, снизу вверх, по ценности — сведены", "Estimates: top-down, bottom-up, value-based — triangulated"),
                    self.t("Эталоны SaaS — эмпирические правила, низкая уверенность", "SaaS benchmarks — rules of thumb, low confidence")]},
                "right": {"heading": self.t("Уточнить у основателей", "To confirm with the founders"), "bullets": self.c["to_confirm"][:4] or [
                    self.t("Фактические цены и скидки", "Actual prices and discounts")]},
                "source": self.t("реестр допущений (research_ledger.json)", "evidence ledger (research_ledger.json)")}

    def s_ask(self):
        return {"layout": "big_number",
                "title": self.t("Запрос: {{auto.ask|money1}} за {{fin.ownership_entry|pct0}} — запас денег до {{fin.end_year}}; {{auto.breakeven_phrase}}",
                                "Ask: {{auto.ask|money1}} for {{fin.ownership_entry|pct0}} — cash through {{fin.end_year}}; {{auto.breakeven_phrase}}"),
                "numbers": [{"value": "{{auto.ask|money1}}", "label": self.t("раунд", "round"), "context": self.t("покрывает минимум денег по модели + 20 %", "covers the model's cash low + 20%")},
                            {"value": "{{fin.post_money|money1}}", "label": "post-money", "context": self.t("оценка до денег — по аналогам с дисконтом", "pre-money from discounted comparables")},
                            {"value": "{{fin.moic_base|x1}}", "label": self.t("MOIC, база", "MOIC, base"), "context": "IRR {{fin.irr_base|pct0}}"}],
                "source": self.t("financial_model.py; оценка по аналогам (estimator.py)", "financial_model.py; comparables (estimator.py)")}

    def s_closing(self):
        rt = self.p.get(f"red_team_{self.lang}", self.p.get("red_team_en", []))
        return {"layout": "closing", "title": self.p.get(f"cta_{self.lang}", self.p.get("cta_en")),
                "bullets": [self.t("Проверим вместе: TAM/SAM/SOM, CAGR, LTV/CAC, окупаемость", "Let's verify together: TAM/SAM/SOM, CAGR, LTV/CAC, payback"),
                            self.t("Все исходные данные — в реестре допущений с ссылками", "All inputs are in the evidence ledger with links")],
                "contact": self.c.get("contact", ""),
                "notes": self.t("Вопросы «красной команды»:\n", "Red-team questions:\n") + "\n".join(f"- {q}" for q in rt)}

    def s_customer_roi(self):
        return {"layout": "chart",
                "title": self.t("На {{auto.cust.deal_units|num0}} точек: выгода {{auto.cust.benefit_year_deal|money1}} в год против затрат {{auto.cust.cost_year_deal|money1}}",
                                "For {{auto.cust.deal_units|num0}} locations: {{auto.cust.benefit_year_deal|money1}} benefit a year versus {{auto.cust.cost_year_deal|money1}} cost"),
                "chart": {"$ref": "auto.charts.cust_roi"},
                "takeaway": [self.t("ROI за 3 года: {{auto.cust.roi|pct0}}", "3-year ROI: {{auto.cust.roi|pct0}}"),
                             self.t("Окупаемость: {{auto.cust.payback_months|num0}} мес.", "Payback: {{auto.cust.payback_months|num0}} months"),
                             self.t("Выгода = часы × стоимость часа; 1-й год — {{auto.cust.ramp|pct0}} эффекта", "Benefit = hours × hourly cost; year 1 at {{auto.cust.ramp|pct0}} of the effect")],
                "source": self.src("customer")}

    def s_tco(self):
        return {"layout": "table",
                "title": self.t("TCO за 3 года на {{auto.cust.deal_units|num0}} точек: {{auto.cust.tco_deal|money1}} против {{auto.cust.alt_tco_deal|money1}} при ручном процессе",
                                "3-year TCO for {{auto.cust.deal_units|num0}} locations: {{auto.cust.tco_deal|money1}} versus {{auto.cust.alt_tco_deal|money1}} for the manual process"),
                "columns": self.t("Статья|Сейчас (вручную)|С продуктом", "Item|Today (manual)|With the product").split("|"),
                "rows": {"$ref": "auto.tables.tco"}, "col_widths": [5.0, 3.0, 3.0], "source": self.src("customer")}

    def s_implementation(self):
        return {"layout": "timeline",
                "title": self.t("Запуск за 8 недель: от настройки до решения по критериям успеха", "Live in 8 weeks: from set-up to a decision on agreed success criteria"),
                "steps": [{"label": lab, "title": st.split("|")[0], "text": st.split("|")[1]} for lab, st in zip(
                    self.t("Неделя 1|Недели 2–4|Недели 5–7|Неделя 8", "Week 1|Weeks 2–4|Weeks 5–7|Week 8").split("|"), self.k("impl"))],
                "source": self.t("план внедрения (типовой)", "standard implementation plan")}

    def s_vendor_viability(self):
        return {"layout": "bullets",
                "title": self.t("Поставщик устойчив: рынок SAM {{market.sam_base|money1}} растёт на {{market.cagr_base|pct0}}, юнит-экономика LTV/CAC {{auto.ue.ltv_cac|x1}}",
                                "A durable vendor: SAM {{market.sam_base|money1}} growing {{market.cagr_base|pct0}}, unit economics LTV/CAC {{auto.ue.ltv_cac|x1}}"),
                "bullets": [self.t("TAM {{market.tam_base|money1}} · SAM {{market.sam_base|money1}} · SOM {{market.som_horizon_base|money1}}", "TAM {{market.tam_base|money1}} · SAM {{market.sam_base|money1}} · SOM {{market.som_horizon_base|money1}}"),
                            self.t("CAGR рынка {{market.cagr_base|pct0}} (диапазон {{market.cagr_bear|pct0}}–{{market.cagr_bull|pct0}})", "Market CAGR {{market.cagr_base|pct0}} (range {{market.cagr_bear|pct0}}–{{market.cagr_bull|pct0}})"),
                            self.t("Выручка {{fin.revenue_last|money1}} к {{fin.end_year}}; {{auto.breakeven_phrase}}", "Revenue {{fin.revenue_last|money1}} by {{fin.end_year}}; {{auto.breakeven_phrase}}"),
                            self.t("Выгрузка всех данных в открытых форматах — план выхода", "Full data export in open formats — an exit plan")],
                "source": self.src("market")}

    def s_pilot_offer(self):
        rt = self.p.get(f"red_team_{self.lang}", self.p.get("red_team_en", []))
        return {"layout": "closing", "title": self.p.get(f"cta_{self.lang}", self.p.get("cta_en")),
                "bullets": [self.k("pilot_criteria"),
                            self.t("Цена пилота засчитывается в годовой договор", "The pilot fee is credited to the annual contract"),
                            self.t("Окупаемость (payback) {{auto.cust.payback_months|num0}} мес. — проверим на ваших данных", "Payback of {{auto.cust.payback_months|num0}} months — verified on your data")],
                "contact": self.c.get("contact", ""),
                "notes": self.t("Вопросы «красной команды»:\n", "Red-team questions:\n") + "\n".join(f"- {q}" for q in rt)}

    def s_smb_value(self):
        return {"layout": "chart",
                "title": self.t("Цена {{auto.price_month|money0}} против экономии {{auto.cust.saving_month|money0}} в месяц — выгода с первого месяца",
                                "Price {{auto.price_month|money0}} versus {{auto.cust.saving_month|money0}} saved a month — ahead from month one"),
                "chart": {"$ref": "auto.charts.smb_value"},
                "takeaway": [self.t("{{auto.cust.hours_saved_month|num0}} ч в месяц × {{auto.cust.hourly_cost|money0}} за час", "{{auto.cust.hours_saved_month|num0}} hours a month × {{auto.cust.hourly_cost|money0}} per hour"),
                             self.t("Чистая выгода {{auto.cust.net_month|money0}} в месяц", "Net gain {{auto.cust.net_month|money0}} a month"),
                             self.t("Окупаемость (payback) — первый месяц", "Payback — the first month")],
                "source": self.src("customer")}

    def s_how_to_start(self):
        return {"layout": "timeline",
                "title": self.k("start_title"),
                "steps": [{"label": str(i + 1), "title": st.split("|")[0], "text": st.split("|")[1]} for i, st in enumerate(self.k("start"))],
                "source": self.t("процесс подключения", "onboarding flow")}

    def s_closing_smb(self):
        return {"layout": "closing", "title": self.p.get(f"cta_{self.lang}", self.p.get("cta_en")),
                "bullets": [self.t("{{auto.price_month|money0}} в месяц за точку — после пробного периода", "{{auto.price_month|money0}} per location per month after the trial"),
                            self.k("smb_close_b2")],
                "contact": self.c.get("contact", "")}

    def s_public_effect(self):
        return {"layout": "big_number",
                "title": self.t("Общественный эффект: {{auto.public.hours_year|num0}} рабочих часов в год высвобождается у {{auto.public.customers|num0}} клиентов",
                                "Public effect: {{auto.public.hours_year|num0}} working hours a year freed at {{auto.public.customers|num0}} customers"),
                "numbers": [{"value": "{{auto.public.hours_year|num0}}", "label": self.t("часов в год", "hours a year"), "context": self.t("при выходе на SOM", "at SOM")},
                            {"value": "{{auto.public.value_year|money1}}", "label": self.t("стоимость времени в год", "value of time a year"), "context": self.t("часы × стоимость часа", "hours × hourly cost")}],
                "source": self.src("customer")}

    def s_regulatory(self):
        return {"layout": "bullets",
                "title": self.t("Соответствие требованиям: персональные данные сотрудников хранятся и обрабатываются по правилам рынка",
                                "Compliance: employee personal data are stored and processed under the market's rules"),
                "bullets": ["{{score.regulatory_definition}}",
                            self.t("Журнал доступа и экспорт данных по запросу", "Access log and data export on request")],
                "source": self.t("справочник рынка (markets/)", "market guide (markets/)")}

    def s_scorecard(self):
        return {"layout": "scorecard",
                "title": self.t("Потенциал {{score.total|num0}}/100 (класс {{score.grade}}): сильные стороны — {{score.top_strengths.0}}",
                                "Potential {{score.total|num0}}/100 (grade {{score.grade}}): strongest on {{score.top_strengths.0}}"),
                "criteria": {"$ref": "tables.scorecard"}, "total": {"$ref": "score.total"}, "grade": "{{score.grade}}",
                "grade_label": "{{score.grade_label}}", "range": [{"$ref": "score.range_lo"}, {"$ref": "score.range_hi"}],
                "source": "scoring.py"}

    def s_improve_deck(self):
        return {"layout": "bullets",
                "title": self.t("Как улучшить эту презентацию: сверяйте цифры, добавляйте доказательства и репетируйте",
                                "How to improve this deck: verify the numbers, add proof and rehearse"),
                "bullets": [
                    self.t("**Замените оценки фактами.** Каждая цифра со словом «оценка» в реестре должна получить источник или замер на пилоте", "**Replace estimates with facts.** Every figure marked \"estimate\" in the ledger needs a source or a pilot measurement"),
                    self.t("**Добавьте живое доказательство.** Демо продукта сильнее любых цифр — покажите реальный результат, а не описание", "**Add a live proof.** A product demo beats any number — show a real result, not a description"),
                    self.t("**Сверьте конкурентные и ценовые допущения.** Проговорите с 3–5 потенциальными клиентами, прежде чем показывать инвестору", "**Validate competitor and pricing assumptions.** Talk to 3–5 potential customers before showing an investor"),
                    self.t("**Сократите объём текста.** Один вывод на слайд; детали — в заметках и в отчёте", "**Cut the amount of text.** One conclusion per slide; details go in the notes and the report"),
                    self.t("**Отрепетируйте вердикты.** Умейте за 20 секунд объяснить каждый показатель: что считали и хорошо это или плохо", "**Rehearse the verdicts.** Be able to explain each metric in 20 seconds: what it measured and whether it is good or bad")],
                "source": self.t("рекомендации PitchComet к самопроверке", "PitchComet self-review recommendations")}

    # ---------------------------------------------------------------- deck
    def deck(self) -> dict:
        slides = []
        for sid in self.p["slide_order"]:
            fn = getattr(self, f"s_{sid}", None)
            if fn is None:
                continue
            s = fn()
            s["_id"] = sid
            verdict = self.c.get("verdicts", {}).get(sid)
            if verdict:
                s["verdict"] = verdict
            if not s.get("notes"):
                s["notes"] = NOTES.get(sid, {}).get(self.lang) or self.t(
                    "Цифры на слайде — из facts.json; источник или формула каждой — в реестре допущений (ledger_full.json).",
                    "Numbers on this slide come from facts.json; the source or formula of each is in the evidence ledger (ledger_full.json).")
            slides.append(s)
        meta = {"title": f"{self.c['name']} — {self.p.get('label_' + self.lang, self.p.get('label_en'))}",
                "author": self.c.get("author", ""), "locale": self.loc, "currency": self.c["currency"],
                "theme": self.c.get("theme", "light"), "slide_numbers": True}
        if self.c.get("watermark"):
            meta["watermark"] = self.c["watermark"]
        return {"meta": meta, "slides": slides}

    # ---------------------------------------------------------------- report
    def report(self) -> dict:
        T = self.t
        n = self.c["name"]
        B = []
        h = lambda lvl, txt: B.append({"type": "heading", "level": lvl, "text": txt})
        par = lambda txt: B.append({"type": "paragraph", "text": txt})
        B += [{"type": "title_page"}, {"type": "toc", "levels": 2}, {"type": "page_break"}]
        h(1, T("1. Краткий вывод", "1. Executive summary"))
        par(T(f"**Ответ.** {n} адресует доступный рынок (SAM) **{{{{market.sam_base|money1}}}}** в {{{{market.base_year}}}} г. при TAM **{{{{market.tam_base|money1}}}}**; рынок растёт на **{{{{market.cagr_base|pct0}}}}** в год (CAGR, диапазон {{{{market.cagr_bear|pct0}}}}–{{{{market.cagr_bull|pct0}}}}). Достижимая доля (SOM) к {{{{market.horizon_year}}}} г. — **{{{{market.som_horizon_base|money1}}}}**. Юнит-экономика по эталонным диапазонам: LTV/CAC **{{{{auto.ue.ltv_cac|x1}}}}**, окупаемость CAC **{{{{auto.ue.payback|num0}}}} мес.** Для клиента: ROI за 3 года **{{{{auto.cust.roi|pct0}}}}**, окупаемость (payback) **{{{{auto.cust.payback_months|num0}}}} мес.**",
              f"**Answer.** {n} addresses a serviceable market (SAM) of **{{{{market.sam_base|money1}}}}** in {{{{market.base_year}}}} within a TAM of **{{{{market.tam_base|money1}}}}**; the market grows **{{{{market.cagr_base|pct0}}}}** a year (CAGR, range {{{{market.cagr_bear|pct0}}}}–{{{{market.cagr_bull|pct0}}}}). The obtainable share (SOM) by {{{{market.horizon_year}}}} is **{{{{market.som_horizon_base|money1}}}}**. Unit economics from benchmark ranges: LTV/CAC **{{{{auto.ue.ltv_cac|x1}}}}**, CAC payback **{{{{auto.ue.payback|num0}}}} months**. For the customer: 3-year ROI **{{{{auto.cust.roi|pct0}}}}**, payback **{{{{auto.cust.payback_months|num0}}}} months**."))
        B.append({"type": "key_figures", "items": [
            {"value": "{{market.sam_base|money1}}", "label": "SAM {{market.base_year}}"},
            {"value": "{{market.cagr_base|pct0}}", "label": "CAGR"},
            {"value": "{{auto.ue.ltv_cac|x1}}", "label": "LTV/CAC"},
            {"value": "{{fin.revenue_last|money1}}", "label": T("выручка {{fin.end_year}}", "revenue {{fin.end_year}}")}],
            "source": self.src("market")})
        par(T("Финансовая модель: выручка **{{fin.revenue_last|money1}}** в {{fin.end_year}} г., {{auto.breakeven_phrase}}, Rule of 40 — **{{fin.rule40_last|pct0}}**. Запрос — **{{auto.ask|money1}}**; MOIC инвестора **{{fin.moic_base|x1}}**, IRR **{{fin.irr_base|pct0}}**, NPV **{{fin.npv_base|money1}}** при ставке {{fin.discount_rate|pct0}}. Оценка по аналогам к {{fin.end_year}} г. — **{{auto.val.ev_low|money1}}–{{auto.val.ev_high|money1}}**.",
              "Financial model: revenue **{{fin.revenue_last|money1}}** in {{fin.end_year}}, {{auto.breakeven_phrase}}, Rule of 40 **{{fin.rule40_last|pct0}}**. The ask is **{{auto.ask|money1}}**; investor MOIC **{{fin.moic_base|x1}}**, IRR **{{fin.irr_base|pct0}}**, NPV **{{fin.npv_base|money1}}** at {{fin.discount_rate|pct0}}. Valuation by comparables in {{fin.end_year}}: **{{auto.val.ev_low|money1}}–{{auto.val.ev_high|money1}}**."))
        B.append({"type": "callout", "title": T("Как читать цифры:", "How to read the numbers:"),
                  "text": T("каждая цифра — либо факт из источника со ссылкой, либо оценка с формулой, диапазоном и уровнем уверенности (раздел 9). Доля оценок — {{auto.ledger.estimate_share|pct0}}.",
                            "every number is either a sourced fact with a link or an estimate with its formula, range and confidence (section 9). Share of estimates: {{auto.ledger.estimate_share|pct0}}.")})
        if self.c.get("fiction_note"):
            par("*" + self.c["fiction_note"] + "*")
        if self.lang != self.loc:
            par("*Narrative text is in English (no localized narrative tables for this locale yet); numbers, units, charts and citations are localized.*")
        h(1, T("2. Профиль продукта", "2. Product profile"))
        par(T(f"{n} — {self.c['tagline']}. Профиль построен инструментом product_profiler.py из описания продукта: категория — {self.c['category_label']}; покупатель — {self.c['buyer']}; модель цены — {self.c['pricing_model']}; развёртывание — {self.c['deployment']}; рынок — {self.c['country_label']}.",
              f"{n} — {self.c['tagline']}. The profile was built by product_profiler.py from the product description: category — {self.c['category_label']}; buyer — {self.c['buyer']}; pricing model — {self.c['pricing_model']}; deployment — {self.c['deployment']}; market — {self.c['country_label']}."))
        B.append({"type": "bullets", "items": self.c["features"][:5]})
        h(1, T("3. Определение рынка и сегменты", "3. Market definition and segments"))
        par(self.c["market_sentence"])
        B.append({"type": "table", "caption": T("Сегменты и TAM / SAM / SOM, {{market.base_year}}", "Segments and TAM / SAM / SOM, {{market.base_year}}"),
                  "columns": T("Сегмент|Единиц|Цена в год|TAM|SAM|SOM {{market.horizon_year}}", "Segment|Units|Price per year|TAM|SAM|SOM {{market.horizon_year}}").split("|"),
                  "rows": {"$ref": "tables.segments"}, "col_widths_cm": [5.0, 2.0, 2.2, 2.3, 2.3, 2.2], "source": self.src("market"), "font_size": 9})
        par(T("**Идеальный клиент (ICP):** ", "**Ideal customer profile (ICP):** ") + self.c["icp_text"])
        h(1, T("4. Размер рынка: три метода", "4. Market size: three methods"))
        par(T("TAM рассчитан тремя независимыми методами и сведён (триангуляция): снизу вверх — {{auto.market.tam_bu|money1}}, сверху вниз — {{auto.market.tam_td|money1}}, по ценности для клиента — {{auto.market.tam_vt|money1}}; расхождение max/min — {{auto.market.tam_ratio|x1}} ({{auto.market.verdict}}). Для модели принят TAM снизу вверх, так как он опирается на официальные данные о числе организаций.",
              "TAM was computed with three independent methods and triangulated: bottom-up {{auto.market.tam_bu|money1}}, top-down {{auto.market.tam_td|money1}}, value-based {{auto.market.tam_vt|money1}}; spread max/min {{auto.market.tam_ratio|x1}} ({{auto.market.verdict}}). The model uses the bottom-up TAM because it rests on official counts of organisations."))
        B.append({"type": "table", "caption": T("Методы оценки TAM", "TAM methods"), "columns": T("Метод|Формула|Низкий|Базовый|Высокий", "Method|Formula|Low|Base|High").split("|"),
                  "rows": {"$ref": "auto.tables.market_methods"}, "col_widths_cm": [3.0, 6.5, 2.2, 2.2, 2.2], "source": self.src("market"), "font_size": 9})
        B.append({"type": "chart", "caption": T("TAM, SAM и SOM, {{market.base_year}}, {{project.units.bn}}", "TAM, SAM and SOM, {{market.base_year}}, {{project.units.bn}}"),
                  "chart": {"$ref": "charts.tam_sam_som"}, "height_cm": 6.0, "source": self.src("market")})
        h(1, T("5. Рост рынка (CAGR) и сценарии", "5. Market growth (CAGR) and scenarios"))
        par(T("CAGR оценён как (1 + номинальный рост отраслей покупателя {{auto.market.industry_growth|pct1}}) × рост проникновения категории ({{auto.market.pen_start|pct0}} → {{auto.market.pen_end|pct0}} к {{market.horizon_year}}) в степени 1/лет − 1. Негативный / базовый / позитивный сценарии: {{market.cagr_bear|pct0}} / {{market.cagr_base|pct0}} / {{market.cagr_bull|pct0}}.",
              "CAGR was estimated as (1 + nominal growth of buyer industries {{auto.market.industry_growth|pct1}}) × category penetration growth ({{auto.market.pen_start|pct0}} → {{auto.market.pen_end|pct0}} by {{market.horizon_year}}) to the power 1/years − 1. Bear / base / bull: {{market.cagr_bear|pct0}} / {{market.cagr_base|pct0}} / {{market.cagr_bull|pct0}}."))
        B.append({"type": "table", "caption": T("Сценарии рынка", "Market scenarios"), "columns": T("Сценарий|CAGR|TAM {{market.horizon_year}}|SAM {{market.horizon_year}}|SOM {{market.horizon_year}}", "Scenario|CAGR|TAM {{market.horizon_year}}|SAM {{market.horizon_year}}|SOM {{market.horizon_year}}").split("|"),
                  "rows": {"$ref": "tables.market_scenarios"}, "col_widths_cm": [3.0, 2.0, 3.2, 3.2, 3.2], "source": self.src("growth"), "font_size": 9})
        B.append({"type": "chart", "caption": T("SAM по сценариям, {{project.units.bn}}", "SAM by scenario, {{project.units.bn}}"), "chart": {"$ref": "charts.sam_scenarios"}, "height_cm": 6.0, "source": self.src("growth")})
        h(1, T("6. Цена и юнит-экономика", "6. Pricing and unit economics"))
        par(T("Цена: **{{auto.price_month|money0}}** в месяц за точку ({{auto.price_basis}}); годовой чек **{{auto.price_year|money0}}**. Проверка по ценности: экономия клиента {{auto.cust.saving_month|money0}} в месяц, то есть цена составляет {{auto.cust.price_share_of_value|pct0}} создаваемой ценности. Юнит-экономика (LTV/CAC, CAC, окупаемость, отток, NRR) рассчитана по эталонным диапазонам SaaS для сегмента — это эмпирические правила, а не факты; их нужно заменить данными когорт.",
              "Price: **{{auto.price_month|money0}}** per location per month ({{auto.price_basis}}); annual contract **{{auto.price_year|money0}}**. Value check: the customer saves {{auto.cust.saving_month|money0}} a month, so the price is {{auto.cust.price_share_of_value|pct0}} of the value created. Unit economics (LTV/CAC, CAC, payback, churn, NRR) use SaaS benchmark ranges for the segment — rules of thumb, not facts; replace them with cohort data."))
        B.append({"type": "table", "caption": T("Юнит-экономика: диапазоны", "Unit economics: ranges"), "columns": T("Показатель|Низкий|Базовый|Высокий|Основа", "Metric|Low|Base|High|Basis").split("|"),
                  "rows": {"$ref": "auto.tables.ue"}, "col_widths_cm": [3.5, 2.2, 2.2, 2.2, 6.0], "source": self.src("ue"), "font_size": 9})
        h(1, T("7. Ценность для клиента: ROI, окупаемость, TCO", "7. Customer value: ROI, payback, TCO"))
        par(T("На одну точку: {{auto.cust.hours_saved_month|num0}} ч в месяц × {{auto.cust.hourly_cost|money0}} = экономия {{auto.cust.saving_month|money0}} при цене {{auto.price_month|money0}} (в {{auto.cust.value_ratio|x1}} больше цены). На сеть из {{auto.cust.deal_units|num0}} точек: ROI за 3 года **{{auto.cust.roi|pct0}}**, окупаемость (payback) **{{auto.cust.payback_months|num0}} мес.**, TCO **{{auto.cust.tco_deal|money1}}** против {{auto.cust.alt_tco_deal|money1}} при ручном процессе (экономия {{auto.cust.saving_3y_deal|money1}}).",
              "Per location: {{auto.cust.hours_saved_month|num0}} hours a month × {{auto.cust.hourly_cost|money0}} = {{auto.cust.saving_month|money0}} saved against a price of {{auto.price_month|money0}} ({{auto.cust.value_ratio|x1}} the price). For a {{auto.cust.deal_units|num0}}-location chain: 3-year ROI **{{auto.cust.roi|pct0}}**, payback **{{auto.cust.payback_months|num0}} months**, TCO **{{auto.cust.tco_deal|money1}}** versus {{auto.cust.alt_tco_deal|money1}} for the manual process (saving {{auto.cust.saving_3y_deal|money1}})."))
        B.append({"type": "table", "caption": T(f"TCO за 3 года на {{{{auto.cust.deal_units|num0}}}} {self.un}", f"3-year TCO for {{{{auto.cust.deal_units|num0}}}} {self.un}"), "columns": T("Статья|Сейчас (вручную)|С продуктом", "Item|Today (manual)|With the product").split("|"),
                  "rows": {"$ref": "auto.tables.tco"}, "col_widths_cm": [7.0, 4.0, 4.0], "source": self.src("customer"), "font_size": 9})
        B.append({"type": "chart", "caption": T("Выгода и затраты клиента по годам, {{project.units.mn}}", "Customer benefit and cost by year, {{project.units.mn}}"), "chart": {"$ref": "auto.charts.cust_roi"}, "height_cm": 6.0, "source": self.src("customer")})
        h(1, T("8. Финансовая модель и оценка", "8. Financial model and valuation"))
        par(T("Модель строит путь клиентов к SOM: новые клиенты по S-кривой, отток {{auto.ue.annual_churn|pct0}} в год, расходы на продажи = новые клиенты × CAC, себестоимость = 1 − валовая маржа. Ставка дисконтирования {{fin.discount_rate|pct0}} = безрисковая ставка {{auto.val.risk_free|pct1}} + премия за риск ранней стадии (эмпирическое правило).",
              "The model builds the customer path to SOM: new customers on an S-curve, churn {{auto.ue.annual_churn|pct0}} a year, sales and marketing = new customers × CAC, cost of revenue = 1 − gross margin. Discount rate {{fin.discount_rate|pct0}} = risk-free {{auto.val.risk_free|pct1}} + an early-stage risk premium (rule of thumb)."))
        B.append({"type": "table", "caption": T("P&L и денежный поток, базовый сценарий", "P&L and cash flow, base case"), "columns": {"$ref": "tables.pnl_columns"},
                  "rows": {"$ref": "tables.pnl"}, "source": T("financial_model.py", "financial_model.py"), "font_size": 9})
        B.append({"type": "chart", "caption": T("Выручка и EBITDA, {{project.units.mn}}", "Revenue and EBITDA, {{project.units.mn}}"), "chart": {"$ref": "charts.revenue_ebitda"}, "height_cm": 6.0, "source": "financial_model.py"})
        B.append({"type": "table", "caption": T("Сценарии: NPV, MOIC, IRR", "Scenarios: NPV, MOIC, IRR"), "columns": T("Сценарий|Выручка {{fin.end_year}}|EBITDA > 0|NPV|MOIC|IRR", "Scenario|Revenue {{fin.end_year}}|EBITDA > 0|NPV|MOIC|IRR").split("|"),
                  "rows": {"$ref": "tables.fin_scenarios"}, "source": "financial_model.py", "font_size": 9})
        B.append({"type": "table", "caption": T("Оценка компании", "Valuation"), "columns": T("Метод|Низкий|Базовый|Высокий|Основа", "Method|Low|Base|High|Basis").split("|"),
                  "rows": {"$ref": "auto.tables.valuation"}, "col_widths_cm": [3.6, 2.4, 2.4, 2.4, 5.2], "source": self.src("valuation"), "font_size": 9})
        par(T("Rule of 40 в {{fin.end_year}} г.: {{fin.rule40_last|pct0}}. Запрос {{auto.ask|money1}} покрывает минимум денежных средств по модели с запасом 20 %, post-money {{fin.post_money|money1}}, доля инвестора {{fin.ownership_entry|pct0}}.",
              "Rule of 40 in {{fin.end_year}}: {{fin.rule40_last|pct0}}. The ask of {{auto.ask|money1}} covers the model's cash low with a 20% buffer; post-money {{fin.post_money|money1}}, investor stake {{fin.ownership_entry|pct0}}."))
        h(1, T("9. Реестр доказательств: источники и оценки", "9. Evidence ledger: sources and estimates"))
        par(T("Записей в реестре — {{auto.ledger.n|num0}}: фактов с источниками — {{auto.ledger.sourced|num0}}, оценок с формулой, диапазоном и уровнем уверенности — {{auto.ledger.estimates|num0}}.",
              "{{auto.ledger.n|num0}} entries: {{auto.ledger.sourced|num0}} sourced facts and {{auto.ledger.estimates|num0}} estimates with formula, range and confidence."))
        B.append({"type": "table", "caption": T("Реестр доказательств", "Evidence ledger"), "columns": T("Показатель|Значение|Тип|Уверенность|Источник или формула", "Item|Value|Type|Confidence|Source or formula").split("|"),
                  "rows": {"$ref": "auto.tables.ledger"}, "col_widths_cm": [4.4, 2.6, 1.8, 1.8, 6.4], "source": T("research_ledger.py", "research_ledger.py"), "font_size": 8})
        h(1, T("10. Скоринг потенциала", "10. Potential score"))
        par(T("Итог {{score.total|num0}}/100 (класс {{score.grade}}: {{score.grade_label}}), диапазон {{score.range_lo|num0}}–{{score.range_hi|num0}}. Веса учитывают паттерн питча.",
              "Total {{score.total|num0}}/100 (grade {{score.grade}}: {{score.grade_label}}), range {{score.range_lo|num0}}–{{score.range_hi|num0}}. Weights follow the pitch pattern."))
        B.append({"type": "scorecard", "caption": T("Скоркарта", "Scorecard"), "criteria": {"$ref": "tables.scorecard"}, "total": {"$ref": "score.total"}, "source": "scoring.py"})
        h(1, T("11. Риски и вопросы «красной команды»", "11. Risks and red-team questions"))
        B.append({"type": "table", "caption": T("Риски", "Risks"), "columns": T("Риск|Индикатор|Ответ", "Risk|Indicator|Response").split("|"),
                  "rows": {"$ref": "auto.tables.risks"}, "col_widths_cm": [4.5, 5.0, 7.0], "source": T("анализ рисков", "risk review"), "font_size": 9})
        B.append({"type": "numbered", "items": self.p.get(f"red_team_{self.lang}", self.p.get("red_team_en", []))})
        h(1, T("12. Уточнить у основателей", "12. To confirm with the founders"))
        par(T("Эти пункты не блокируют выводы: в модели для них стоят оценки, их стоит заменить фактическими данными.",
              "These items do not block the conclusions: the model uses estimates for them; replace them with actual data."))
        B.append({"type": "numbered", "items": self.c["to_confirm"] or [T("Фактические цены и скидки", "Actual prices and discounts")]})
        h(1, T("Источники", "Sources"))
        B.append({"type": "sources"})
        meta = {"title": f"{n}: " + T("оценка рынка, экономики и питч", "market, economics and pitch"),
                "subtitle": self.p.get(f"label_{self.lang}", self.p.get("label_en")) + " · " + self.c["country_label"],
                "org": self.c.get("org", ""), "author": self.c.get("author", ""), "date": self.c["date"],
                "header": f"{n} — PitchComet", "locale": self.loc, "currency": self.c["currency"], "font_size": 11,
                "preset": "report", "theme": self.c.get("report_theme", "light")}
        if self.c.get("watermark"):
            meta["watermark"] = self.c["watermark"]
        return {"meta": meta, "sources": self.c.get("sources", []), "blocks": B}


FIGURE_LABELS = {
    "auto.market.units_total": ("Целевых единиц всего", "Target units, total"),
    "market.sam_horizon_base": ("SAM на горизонте", "SAM at the horizon"),
    "fin.min_cash": ("Минимум денежных средств (без финансирования)", "Cash low point (before funding)"),
    "fin.npv_bear": ("NPV, пессимистичный сценарий", "NPV, bear case"),
    "fin.npv_bull": ("NPV, оптимистичный сценарий", "NPV, bull case"),
    "fin.rule40_last": ("Rule of 40, последний год", "Rule of 40, last year"),
    "auto.ue.gm": ("Валовая маржа, база", "Gross margin, base"),
    "auto.ue.gm_low": ("Валовая маржа, низкая", "Gross margin, low"),
    "auto.ue.gm_high": ("Валовая маржа, высокая", "Gross margin, high"),
    "auto.ue.cac": ("CAC", "CAC"),
    "auto.cust.benefit_year_deal": ("Годовая выгода клиента на сделку", "Annual customer benefit per deal"),
    "auto.cust.cost_year_deal": ("Годовая стоимость для клиента на сделку", "Annual customer cost per deal"),
    "auto.cust.manual_cost_month": ("Стоимость ручной работы в месяц", "Manual work cost per month"),
    "auto.cust.ramp": ("Доля выгоды в первый год", "First-year benefit share"),
    "auto.cust.net_month": ("Чистая выгода в месяц", "Net monthly gain"),
    "auto.price_year_discounted": ("Цена за год со скидкой", "Annual price with discount"),
    "auto.public.customers": ("Организаций-пользователей", "Adopting organisations"),
    "auto.public.hours_year": ("Сэкономленных часов в год", "Hours saved per year"),
    "auto.public.value_year": ("Экономический эффект в год", "Economic effect per year"),
}

_PH = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)\s*(?:\|\s*([A-Za-z0-9_]+))?\s*\}\}")


def _figure_appendix(deck: dict, report: dict, lang: str) -> None:
    """Every number placeholder shown on a slide also appears in the report (deck ↔ report consistency)."""
    in_report = {m.group(1) for m in _PH.finditer(json.dumps(report, ensure_ascii=False))}
    rows, seen = [], set()
    for m in _PH.finditer(json.dumps(deck, ensure_ascii=False)):
        key, fmt = m.group(1), m.group(2)
        if not fmt or key in in_report or key in seen:
            continue
        seen.add(key)
        lab = FIGURE_LABELS.get(key)
        rows.append([(lab[0] if lang == "ru" else lab[1]) if lab else key, m.group(0), key])
    if not rows:
        return
    ru = lang == "ru"
    blocks = report["blocks"]
    i = next((n for n, b in enumerate(blocks) if b.get("type") == "heading" and b.get("text") in ("Источники", "Sources")), len(blocks))
    blocks[i:i] = [
        {"type": "heading", "level": 1, "text": "Приложение: цифры презентации" if ru else "Appendix: figures used in the deck"},
        {"type": "table", "caption": "Дополнительные показатели слайдов" if ru else "Additional slide figures",
         "columns": ["Показатель", "Значение", "Ключ facts.json"] if ru else ["Metric", "Value", "facts.json key"],
         "rows": rows, "col_widths_cm": [6.5, 4.0, 6.0], "source": "facts.json", "font_size": 9}]


def build_specs(ctx: dict, pattern: dict, locale: str) -> tuple[dict, dict]:
    st = Story(ctx, pattern, locale)
    deck, report = st.deck(), st.report()
    _figure_appendix(deck, report, st.lang)
    return deck, report
