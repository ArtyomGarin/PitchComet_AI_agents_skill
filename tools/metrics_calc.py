#!/usr/bin/env python3
"""metrics_calc.py — strategic, SaaS, finance and R&D metrics with JSON in/out.

Every function returns a dict: {metric, value, unit, formula, interpretation, inputs}.
Fractions are used for rates (0.25 = 25%). Money is in any single currency unit.

CLI:
  python metrics_calc.py list
  python metrics_calc.py cagr --json '{"start": 100, "end": 250, "years": 5}'
  python metrics_calc.py batch --input calcs.json      # {"calcs":[{"id":"g","fn":"cagr","args":{...}}]}
Import:
  from metrics_calc import cagr, irr, METRICS; METRICS["cagr"](start=100, end=250, years=5)
"""
from __future__ import annotations

import math
import sys
from typing import Callable, Sequence

try:
    from fmt_utils import cli_io, dump_json
except ImportError:  # pragma: no cover
    from .fmt_utils import cli_io, dump_json  # type: ignore

METRICS: dict[str, Callable] = {}


def metric(fn: Callable) -> Callable:
    """Register a metric; the wrapper records the bound call arguments as 'inputs'."""
    import functools
    import inspect
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        out = fn(*args, **kwargs)
        if isinstance(out, dict):
            b = sig.bind(*args, **kwargs)
            b.apply_defaults()
            out["inputs"] = {k: v for k, v in b.arguments.items()}
        return out

    METRICS[fn.__name__] = wrapper
    return wrapper


def _r(metric_name, value, unit, formula, interpretation, inputs, **extra):
    out = {"metric": metric_name, "value": value, "unit": unit, "formula": formula,
           "interpretation": interpretation, "inputs": inputs}
    out.update(extra)
    return out


def _band(value, bands, default=""):
    """bands: list of (upper_exclusive, label) ascending; last may use math.inf."""
    if value is None:
        return default
    for upper, label in bands:
        if value < upper:
            return label
    return default


# ---------------------------------------------------------------- growth
@metric
def cagr(start: float, end: float, years: float) -> dict:
    """Compound annual growth rate."""
    if start <= 0 or years <= 0:
        raise ValueError("start must be > 0 and years > 0")
    v = (end / start) ** (1 / years) - 1
    interp = _band(v, [(0, "decline"), (0.05, "slow (<5%)"), (0.15, "moderate (5–15%)"),
                       (0.30, "fast (15–30%)"), (math.inf, "very fast (>30%): check base effect & source")])
    return _r("cagr", v, "fraction/yr", "(end/start)^(1/years) - 1", interp, None)


@metric
def project_cagr(start: float, rate: float, years: int, start_year: int | None = None) -> dict:
    """Project a value forward at a constant CAGR. Returns the series."""
    series = [start * (1 + rate) ** t for t in range(years + 1)]
    labels = [str(start_year + t) for t in range(years + 1)] if start_year else list(range(years + 1))
    return _r("project_cagr", series[-1], "same as start", "start*(1+rate)^t", "", None,
              series=series, labels=labels)


@metric
def growth_rate(current: float, previous: float, period: str = "YoY") -> dict:
    """Period-over-period growth (YoY, QoQ, MoM)."""
    v = current / previous - 1 if previous else None
    return _r("growth_rate", v, "fraction", "current/previous - 1", period, None)


@metric
def mom_to_annual(mom: float) -> dict:
    """Convert a monthly growth rate to an annualized rate."""
    v = (1 + mom) ** 12 - 1
    return _r("mom_to_annual", v, "fraction/yr", "(1+MoM)^12 - 1",
              "early-stage heuristic: sustained 15–20% MoM growth is strong; compare with your segment's peers",
              None)


@metric
def market_share(company_revenue: float, market_size: float) -> dict:
    """Company revenue as a share of the market."""
    v = company_revenue / market_size
    return _r("market_share", v, "fraction", "company revenue / market size",
              _band(v, [(0.01, "niche (<1%)"), (0.05, "noticeable (1–5%)"), (0.15, "significant (5–15%)"),
                        (math.inf, "leader (>15%)")]), None)


# ---------------------------------------------------------------- SaaS revenue
@metric
def arr_from_mrr(mrr: float) -> dict:
    """Annual recurring revenue from MRR."""
    return _r("arr", mrr * 12, "money/yr", "MRR × 12", "Use only recurring, contracted revenue", None)


@metric
def mrr_bridge(start_mrr: float, new: float, expansion: float, contraction: float, churned: float) -> dict:
    """MRR waterfall: start + new + expansion − contraction − churn."""
    end = start_mrr + new + expansion - contraction - churned
    net_new = end - start_mrr
    return _r("mrr_bridge", end, "money/mo", "start + new + expansion − contraction − churn",
              "", None, net_new_mrr=net_new)


@metric
def nrr(start_arr: float, expansion: float, contraction: float, churned: float) -> dict:
    """Net revenue retention of a cohort over 12 months."""
    v = (start_arr + expansion - contraction - churned) / start_arr
    interp = _band(v, [(0.9, "weak (<90%)"), (1.0, "below 100%: base shrinks"),
                       (1.2, "good (100–120%)"), (math.inf, "best-in-class (>120%)")])
    return _r("nrr", v, "fraction", "(start + expansion − contraction − churn) / start", interp, None)


@metric
def grr(start_arr: float, contraction: float, churned: float) -> dict:
    """Gross revenue retention (no expansion, capped at 100%)."""
    v = (start_arr - contraction - churned) / start_arr
    interp = _band(v, [(0.8, "weak (<80%)"), (0.9, "acceptable SMB (80–90%)"), (math.inf, "strong enterprise (≥90%)")])
    return _r("grr", v, "fraction", "(start − contraction − churn) / start", interp, None)


@metric
def churn_rate(lost: float, start: float, period: str = "month") -> dict:
    """Logo or revenue churn for a period. Annualizes if monthly."""
    v = lost / start
    annual = 1 - (1 - v) ** 12 if period == "month" else v
    return _r("churn_rate", v, f"fraction/{period}", "lost / start-of-period base",
              _band(annual, [(0.07, "enterprise-grade (<7%/yr)"), (0.2, "ok mid-market"),
                             (0.4, "SMB-typical"), (math.inf, "high: product-market fit risk")]),
              None, annualized=annual)


# ---------------------------------------------------------------- unit economics
@metric
def cac(sales_marketing_spend: float, new_customers: float) -> dict:
    """Customer acquisition cost (fully loaded S&M per new customer)."""
    v = sales_marketing_spend / new_customers
    return _r("cac", v, "money/customer", "S&M spend / new customers (same period, fully loaded)", "",
              None)


@metric
def ltv(arpa: float, gross_margin: float, churn: float, period: str = "month",
        discount_rate_annual: float = 0.0) -> dict:
    """Customer lifetime value (gross-margin based). churn per period."""
    if churn <= 0:
        raise ValueError("churn must be > 0")
    if discount_rate_annual:
        d = (1 + discount_rate_annual) ** (1 / 12) - 1 if period == "month" else discount_rate_annual
        v = arpa * gross_margin * (1 + d) / (churn + d)
        f = "ARPA × GM × (1+d) / (churn + d)"
    else:
        v = arpa * gross_margin / churn
        f = "ARPA × GM / churn"
    return _r("ltv", v, "money", f, "Cap lifetime at 5 years for early-stage claims", None,
              lifetime_periods=1 / churn)


@metric
def ltv_cac(ltv_value: float, cac_value: float) -> dict:
    """LTV to CAC ratio (benchmark ≥3)."""
    v = ltv_value / cac_value
    interp = _band(v, [(1, "value-destroying (<1)"), (3, "below benchmark (1–3)"),
                       (5, "healthy (3–5)"), (math.inf, ">5: may be under-investing in growth")])
    return _r("ltv_cac", v, "x", "LTV / CAC", interp, None)


@metric
def cac_payback(cac_value: float, arpa_monthly: float, gross_margin: float) -> dict:
    """Months to recover CAC from gross profit."""
    v = cac_value / (arpa_monthly * gross_margin)
    interp = _band(v, [(12, "excellent (<12 mo)"), (18, "good (12–18)"), (24, "acceptable (18–24)"),
                       (math.inf, "slow (>24 mo)")])
    return _r("cac_payback", v, "months", "CAC / (monthly ARPA × GM)", interp, None)


@metric
def gross_margin(revenue: float, cogs: float) -> dict:
    """Gross margin = (revenue − COGS)/revenue."""
    v = (revenue - cogs) / revenue
    interp = _band(v, [(0.5, "services-like (<50%)"), (0.7, "hybrid / AI-heavy (50–70%)"),
                       (0.8, "good SaaS (70–80%)"), (math.inf, "best-in-class software (>80%)")])
    return _r("gross_margin", v, "fraction", "(revenue − COGS) / revenue", interp, None)


@metric
def contribution_margin(revenue: float, variable_costs: float) -> dict:
    """Contribution margin after variable costs."""
    v = (revenue - variable_costs) / revenue
    return _r("contribution_margin", v, "fraction", "(revenue − variable costs) / revenue",
              "Must be > 0 per unit before scaling", None, absolute=revenue - variable_costs)


@metric
def unit_economics(price: float, variable_cost: float, cac_value: float, lifetime_units: float) -> dict:
    """Per-customer economics: contribution over lifetime minus CAC."""
    contrib = (price - variable_cost) * lifetime_units
    v = contrib - cac_value
    return _r("unit_economics", v, "money/customer", "(price − variable cost) × lifetime units − CAC",
              "positive = each customer pays back acquisition", None, lifetime_contribution=contrib)


# ---------------------------------------------------------------- burn & efficiency
@metric
def burn(cash_start: float, cash_end: float, months: float, financing_inflows: float = 0.0) -> dict:
    """Net monthly burn excluding financing inflows."""
    v = (cash_start - (cash_end - financing_inflows)) / months
    return _r("net_burn", v, "money/month", "(cash_start − (cash_end − financing)) / months", "", None)


@metric
def runway(cash: float, monthly_net_burn: float) -> dict:
    """Months of runway at current net burn."""
    v = math.inf if monthly_net_burn <= 0 else cash / monthly_net_burn
    interp = _band(v, [(6, "critical (<6 mo)"), (12, "raise now (6–12)"), (18, "ok (12–18)"),
                       (math.inf, "comfortable (>18 mo)")], "cash-flow positive")
    return _r("runway", v, "months", "cash / monthly net burn", interp, None)


@metric
def burn_multiple(net_burn: float, net_new_arr: float) -> dict:
    """Burn multiple (Craft Ventures, 2020). Same period for both inputs."""
    v = net_burn / net_new_arr if net_new_arr > 0 else math.inf
    interp = _band(v, [(1, "amazing (<1x)"), (1.5, "great (1–1.5x)"), (2, "good (1.5–2x)"),
                       (3, "suspect (2–3x)"), (math.inf, "bad (>3x)")])
    return _r("burn_multiple", v, "x", "net burn / net new ARR", interp, None)


@metric
def rule_of_40(revenue_growth: float, profit_margin: float) -> dict:
    """Growth % + margin % (EBITDA, FCF or adjusted operating margin — state which)."""
    v = revenue_growth + profit_margin
    interp = "meets Rule of 40" if v >= 0.4 else "below 40%"
    return _r("rule_of_40", v, "fraction", "YoY revenue growth + profit margin", interp, None)


@metric
def magic_number(rev_current_q: float, rev_prior_q: float, sm_prior_q: float) -> dict:
    """Scale Venture Partners definition (quarterly GAAP revenue)."""
    v = (rev_current_q - rev_prior_q) * 4 / sm_prior_q
    interp = _band(v, [(0.5, "inefficient (<0.5)"), (0.75, "watch (0.5–0.75)"), (1.0, "efficient (0.75–1)"),
                       (math.inf, "very efficient (>1): invest more in S&M")])
    return _r("magic_number", v, "x", "(Rev_q − Rev_q-1) × 4 / S&M_q-1", interp, None)


# ---------------------------------------------------------------- finance
@metric
def npv(rate: float, cashflows: Sequence[float], t0: int = 0) -> dict:
    """NPV; cashflows[0] occurs at t0 (0 = today, undiscounted)."""
    v = sum(cf / (1 + rate) ** (i + t0) for i, cf in enumerate(cashflows))
    return _r("npv", v, "money", "Σ CF_t / (1+r)^t", "accept if > 0 at the hurdle rate", None)


def _irr(cashflows: Sequence[float]) -> float | None:
    cfs = list(cashflows)
    if not (any(c < 0 for c in cfs) and any(c > 0 for c in cfs)):
        return None
    f = lambda r: sum(c / (1 + r) ** i for i, c in enumerate(cfs))
    lo, hi = -0.9999, 10.0
    flo, fhi = f(lo), f(hi)
    # expand hi if needed
    while flo * fhi > 0 and hi < 1e6:
        hi *= 10
        fhi = f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-10:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


@metric
def irr(cashflows: Sequence[float]) -> dict:
    """Internal rate of return for evenly spaced periods (bisection, robust)."""
    v = _irr(cashflows)
    interp = "" if v is None else _band(v, [(0.1, "below typical hurdle"), (0.2, "PE-buyout range 10–20%"),
                                             (0.3, "strong (20–30%)"), (math.inf, "VC-target range (>30%)")])
    return _r("irr", v, "fraction/period", "r such that Σ CF_t/(1+r)^t = 0", interp, None)


@metric
def moic(total_value_returned: float, invested: float) -> dict:
    """Multiple on invested capital."""
    v = total_value_returned / invested
    return _r("moic", v, "x", "total value (realized + unrealized) / invested capital",
              _band(v, [(1, "loss"), (2, "modest"), (3, "PE-target 2–3x"), (math.inf, "VC-class >3x")]),
              None)


@metric
def irr_from_moic(moic_value: float, years: float) -> dict:
    """Annualized IRR implied by a MOIC over N years."""
    v = moic_value ** (1 / years) - 1
    return _r("irr_from_moic", v, "fraction/yr", "MOIC^(1/years) − 1 (single in/out)", "", None)


@metric
def dcf(fcf: Sequence[float], discount_rate: float, terminal_growth: float | None = None,
        exit_multiple: float | None = None, terminal_metric: float | None = None,
        net_debt: float = 0.0) -> dict:
    """DCF: explicit FCF years 1..N + terminal value (Gordon or exit multiple)."""
    pv_fcf = sum(c / (1 + discount_rate) ** (i + 1) for i, c in enumerate(fcf))
    n = len(fcf)
    if terminal_growth is not None:
        if terminal_growth >= discount_rate:
            raise ValueError("terminal_growth must be < discount_rate")
        tv = fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        method = "Gordon growth"
    elif exit_multiple is not None:
        tv = exit_multiple * (terminal_metric if terminal_metric is not None else fcf[-1])
        method = "exit multiple"
    else:
        tv, method = 0.0, "none"
    pv_tv = tv / (1 + discount_rate) ** n
    ev = pv_fcf + pv_tv
    share_tv = pv_tv / ev if ev else None
    interp = "TV share > 75%: value rests on far-future assumptions" if share_tv and share_tv > 0.75 else ""
    return _r("dcf", ev, "money", "EV = Σ FCF_t/(1+r)^t + TV/(1+r)^N", interp, None,
              pv_fcf=pv_fcf, terminal_value=tv, pv_terminal=pv_tv, tv_share=share_tv,
              equity_value=ev - net_debt, method=method)


@metric
def capm(risk_free: float, beta: float, equity_risk_premium: float, size_premium: float = 0.0,
         country_premium: float = 0.0, venture_premium: float = 0.0) -> dict:
    """Cost of equity via (modified) CAPM. For RUB use the OFZ yield as risk-free."""
    v = risk_free + beta * equity_risk_premium + size_premium + country_premium + venture_premium
    return _r("cost_of_equity", v, "fraction/yr", "rf + β·ERP + size + country + venture premia", "",
              None)


@metric
def wacc(cost_equity: float, cost_debt: float, equity_value: float, debt_value: float, tax_rate: float) -> dict:
    """Weighted average cost of capital."""
    tot = equity_value + debt_value
    v = equity_value / tot * cost_equity + debt_value / tot * cost_debt * (1 - tax_rate)
    return _r("wacc", v, "fraction/yr", "E/V·Re + D/V·Rd·(1−t)", "", None)


@metric
def real_rate(nominal: float, inflation: float) -> dict:
    """Fisher equation; use to move between nominal RUB and real terms."""
    v = (1 + nominal) / (1 + inflation) - 1
    return _r("real_rate", v, "fraction/yr", "(1+nominal)/(1+inflation) − 1", "", None)


@metric
def deflate(values: Sequence[float], inflation: Sequence[float] | float, base_index: int = 0) -> dict:
    """Convert a nominal series to real prices of the base period."""
    infl = [inflation] * len(values) if isinstance(inflation, (int, float)) else list(inflation)
    idx = [1.0]
    for i in range(1, len(values)):
        idx.append(idx[-1] * (1 + infl[i]))
    base = idx[base_index]
    real = [v / (idx[i] / base) for i, v in enumerate(values)]
    return _r("deflate", real[-1], "money (base-period prices)", "nominal_t / Π(1+π)", "", None,
              series=real, price_index=idx)


@metric
def fx_convert(amount: float, rate: float, direction: str = "to_rub") -> dict:
    """rate = RUB per 1 unit of foreign currency. State date and source (e.g. Bank of Russia official rate)."""
    v = amount * rate if direction == "to_rub" else amount / rate
    return _r("fx_convert", v, "money", "amount × rate (to RUB) or amount / rate", "always cite the rate date",
              None)


@metric
def break_even(fixed_costs: float, price: float, variable_cost: float) -> dict:
    """Break-even volume and revenue."""
    cm = price - variable_cost
    if cm <= 0:
        return _r("break_even", None, "units", "fixed / (price − variable)", "never breaks even: negative unit margin",
                  None)
    units = fixed_costs / cm
    return _r("break_even", units, "units", "fixed costs / (price − variable cost)", "", None,
              revenue=units * price)


@metric
def value_based_price(value_created: float, capture_share: float = 0.2) -> dict:
    """Price as a share of the customer's quantified value (10–30% typical for B2B software)."""
    v = value_created * capture_share
    return _r("value_based_price", v, "money", "value created × capture share",
              "capture 10–30%; >50% leaves the buyer little reason to switch", None)


@metric
def price_elasticity(q1: float, q2: float, p1: float, p2: float) -> dict:
    """Arc (midpoint) elasticity of demand."""
    v = ((q2 - q1) / ((q1 + q2) / 2)) / ((p2 - p1) / ((p1 + p2) / 2))
    return _r("price_elasticity", v, "", "%ΔQ / %ΔP (midpoint)",
              "|e|<1 inelastic: price increase raises revenue" if abs(v) < 1 else "elastic", None)


# ---------------------------------------------------------------- technology dynamics
@metric
def wright_law(first_unit_cost: float, cumulative_units: float, learning_rate: float) -> dict:
    """Cost of the N-th unit; learning_rate = cost decline per doubling (0.2 = −20%)."""
    b = math.log2(1 - learning_rate)
    v = first_unit_cost * cumulative_units ** b
    return _r("wright_law", v, "money/unit", "C_n = C_1 · n^log2(1−LR)", "", None, exponent=b)


@metric
def learning_rate_fit(cumulative_units: Sequence[float], unit_costs: Sequence[float]) -> dict:
    """Fit Wright's-law learning rate from observed (cumulative volume, unit cost) points (log-log OLS)."""
    xs = [math.log(x) for x in cumulative_units]
    ys = [math.log(y) for y in unit_costs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    lr = 1 - 2 ** b
    ss_res = sum((y - (my + b * (x - mx))) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys) or 1e-12
    return _r("learning_rate_fit", lr, "fraction per doubling", "LR = 1 − 2^b, b = slope of ln C on ln N",
              "", {"n_points": n}, exponent=b, r2=1 - ss_res / ss_tot)


@metric
def logistic_adoption(saturation: float, midpoint_year: float, steepness: float,
                      years: Sequence[float]) -> dict:
    """S-curve: N(t) = K / (1 + e^(−k(t − t0)))."""
    series = [saturation / (1 + math.exp(-steepness * (t - midpoint_year))) for t in years]
    t10 = midpoint_year - math.log(9) / steepness
    t90 = midpoint_year + math.log(9) / steepness
    return _r("logistic_adoption", series[-1], "adopters", "K / (1 + e^(−k(t−t0)))",
              f"10%→90% takes {t90 - t10:.1f} years", None, series=series, labels=list(years))


@metric
def bass_diffusion(market_potential: float, p: float, q: float, periods: int) -> dict:
    """Bass model: p innovation (~0.01–0.03), q imitation (~0.3–0.5). Returns adopters per period."""
    cum, new = 0.0, []
    for _ in range(periods):
        n = (p + q * cum / market_potential) * (market_potential - cum)
        new.append(n)
        cum += n
    cumulative = []
    c = 0.0
    for n in new:
        c += n
        cumulative.append(c)
    peak = new.index(max(new)) + 1
    return _r("bass_diffusion", cumulative[-1], "adopters", "n_t = (p + q·N/M)(M − N)",
              f"peak adoption in period {peak}", None, new_adopters=new, cumulative=cumulative)


TRL_LEVELS = {   # (en, ru, zh)
    1: ("Basic principles observed", "Опубликованы фундаментальные принципы", "观察到基本原理"),
    2: ("Technology concept formulated", "Сформулирована концепция технологии", "形成技术概念"),
    3: ("Experimental proof of concept", "Подтверждены ключевые функции (proof of concept)", "关键功能实验验证"),
    4: ("Technology validated in a controlled environment", "Компоненты/макет проверены в контролируемых условиях", "在受控环境中验证技术"),
    5: ("Validated in relevant environment", "Проверка в условиях, близких к реальным", "在相关环境中验证"),
    6: ("Prototype demonstrated in relevant environment", "Прототип продемонстрирован в близких условиях", "在相关环境中演示原型"),
    7: ("System prototype in operational environment", "Прототип системы в реальной эксплуатации", "在实际运行环境中演示系统原型"),
    8: ("System complete and qualified", "Штатная система квалифицирована испытаниями", "系统完成并通过鉴定"),
    9: ("Actual system proven in operation", "Успешная эксплуатация реальной системы", "实际系统在运行中得到验证"),
}


@metric
def trl_assess(evidence: dict) -> dict:
    """Highest TRL whose evidence flag (trl1..trl9 booleans) is true with all lower levels true."""
    level = 0
    for i in range(1, 10):
        if evidence.get(f"trl{i}"):
            level = i
        else:
            break
    en, ru, zh = TRL_LEVELS.get(level, ("Not assessed", "Не оценено", "未评估"))
    stage = "research" if level <= 3 else "development" if level <= 6 else "deployment"
    return _r("trl", level, "level 1–9", "highest consecutive level with evidence (NASA TRL / ГОСТ Р 58048-2017 УГТ)",
              stage, {"evidence": evidence}, label_en=en, label_ru=ru, label_zh=zh)


# ---------------------------------------------------------------- R&D / AI productivity
@metric
def automation_roi(tasks_per_year: float, minutes_before: float, minutes_after: float,
                   hourly_cost: float, solution_cost_per_year: float, implementation_cost: float = 0.0,
                   adoption_rate: float = 1.0, years: int = 3, discount_rate: float = 0.0) -> dict:
    """ROI of automating a task (AI assistant, pipeline). Returns time saved, savings, ROI, payback."""
    hours_saved = tasks_per_year * adoption_rate * (minutes_before - minutes_after) / 60
    gross_savings = hours_saved * hourly_cost
    net_annual = gross_savings - solution_cost_per_year
    cfs = [-implementation_cost] + [net_annual] * years
    pv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cfs))
    total_cost = implementation_cost + solution_cost_per_year * years
    roi = (gross_savings * years - total_cost) / total_cost if total_cost else None
    payback_m = implementation_cost / (net_annual / 12) if net_annual > 0 else math.inf
    return _r("automation_roi", roi, "fraction over horizon", "(savings×years − total cost) / total cost",
              "time-saved claims need a measured baseline (stopwatch study or logs)", None,
              hours_saved_per_year=hours_saved, gross_savings_per_year=gross_savings,
              net_savings_per_year=net_annual, npv=pv, payback_months=payback_m,
              time_reduction=(minutes_before - minutes_after) / minutes_before)


@metric
def cost_per_task(total_cost: float, tasks: float, baseline_cost_per_task: float | None = None) -> dict:
    """Cost per task and reduction vs baseline."""
    v = total_cost / tasks
    extra = {}
    if baseline_cost_per_task:
        extra["reduction_vs_baseline"] = 1 - v / baseline_cost_per_task
    return _r("cost_per_task", v, "money/task", "total cost / tasks", "", None, **extra)


@metric
def accuracy_vs_baseline(model_correct: float, baseline_correct: float, n: float) -> dict:
    """Accuracy lift with a 95% CI on the difference (normal approx., independent samples)."""
    pm, pb = model_correct / n, baseline_correct / n
    diff = pm - pb
    se = math.sqrt(pm * (1 - pm) / n + pb * (1 - pb) / n)
    lo, hi = diff - 1.96 * se, diff + 1.96 * se
    err_red = (pm - pb) / (1 - pb) if pb < 1 else None
    return _r("accuracy_vs_baseline", diff, "pp (fraction)", "acc_model − acc_baseline",
              "significant at 95%" if lo > 0 else "not significant: collect more samples",
              None, accuracy_model=pm, accuracy_baseline=pb, ci95=[lo, hi],
              relative_error_reduction=err_red)


@metric
def rd_productivity(outputs: float, rd_spend: float, fte: float | None = None) -> dict:
    """Generic R&D productivity: outputs (publications, patents, releases, models) per spend and per FTE."""
    per_mn = outputs / (rd_spend / 1e6)
    return _r("rd_productivity", per_mn, "outputs per 1 mn of R&D spend", "outputs / (R&D spend / 10^6)", "",
              None, per_fte=(outputs / fte if fte else None), cost_per_output=rd_spend / outputs if outputs else None)


# ---------------------------------------------------------------- valuation & dilution
@metric
def ev_multiple(enterprise_value: float, metric_value: float, metric_name: str = "revenue") -> dict:
    """EV / metric multiple (EV/Revenue, EV/EBITDA)."""
    v = enterprise_value / metric_value
    return _r(f"ev_{metric_name}", v, "x", f"EV / {metric_name}", "compare only with peers at similar growth & margin",
              None)


@metric
def enterprise_value(equity_value: float, debt: float, cash: float, minorities: float = 0.0,
                     preferred: float = 0.0) -> dict:
    """Enterprise value from equity value and net debt."""
    v = equity_value + debt - cash + minorities + preferred
    return _r("enterprise_value", v, "money", "equity + debt − cash + minorities + preferred", "", None)


@metric
def valuation_from_multiple(metric_value: float, multiple: float, net_debt: float = 0.0) -> dict:
    """EV and equity value from a peer multiple."""
    ev = metric_value * multiple
    return _r("valuation_from_multiple", ev, "money", "metric × multiple", "", None,
              equity_value=ev - net_debt)


@metric
def dilution(pre_money: float, investment: float, founder_shares_pct: float = 1.0,
             option_pool_post: float = 0.0) -> dict:
    """Post-money, investor stake and existing-holder dilution (option pool in post-money)."""
    post = pre_money + investment
    inv_pct = investment / post
    existing_after = (1 - inv_pct - option_pool_post)
    founders_after = founder_shares_pct * existing_after
    return _r("dilution", inv_pct, "fraction", "investor % = investment / post-money", "", None,
              post_money=post, existing_holders_after=existing_after, founders_after=founders_after,
              dilution_of_existing=1 - existing_after)


@metric
def sensitivity_1d(base_inputs: dict, fn: str, variable: str, deltas: Sequence[float]) -> dict:
    """Run any metric with one input varied by relative deltas (e.g. [-0.2,0,0.2])."""
    f = METRICS[fn]
    rows = []
    for d in deltas:
        args = dict(base_inputs)
        args[variable] = base_inputs[variable] * (1 + d)
        rows.append({"delta": d, variable: args[variable], "value": f(**args)["value"]})
    return _r("sensitivity_1d", rows, "table", f"{fn} with {variable} × (1+δ)", "", None)


@metric
def scenarios(base_inputs: dict, fn: str, overrides: dict) -> dict:
    """overrides = {"bear": {...}, "base": {}, "bull": {...}} applied to base_inputs; returns value per scenario."""
    f = METRICS[fn]
    out = {name: f(**{**base_inputs, **ov})["value"] for name, ov in overrides.items()}
    return _r("scenarios", out, "by scenario", f"{fn} under scenario overrides", "", None)


@metric
def customer_roi(annual_benefit: float, annual_cost: float, one_off_cost: float = 0.0, years: int = 3,
                 discount_rate: float = 0.0, ramp_first_year: float = 1.0) -> dict:
    """Customer ROI of buying the product: payback, ROI and NPV for the buyer (corporate / SMB pitch).

    annual_benefit — measurable annual gain for the customer (saved hours × loaded cost, avoided
    losses, extra margin); annual_cost — subscription/licence + run costs; one_off_cost — implementation,
    integration, training; ramp_first_year — share of the benefit realised in year 1 (adoption ramp).
    """
    benefits = [annual_benefit * (ramp_first_year if i == 0 else 1.0) for i in range(years)]
    cfs = [-one_off_cost] + [b - annual_cost for b in benefits]
    npv_v = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cfs))
    total_cost = one_off_cost + annual_cost * years
    roi = (sum(benefits) - total_cost) / total_cost if total_cost else None
    net_annual = annual_benefit - annual_cost
    if net_annual <= 0:
        payback_m = math.inf
    else:   # month-by-month, honouring the first-year ramp
        cum, payback_m = -one_off_cost, math.inf
        for m in range(1, 12 * years + 1):
            b = annual_benefit * (ramp_first_year if m <= 12 else 1.0) / 12
            cum += b - annual_cost / 12
            if cum >= 0:
                payback_m = m
                break
    return _r("customer_roi", roi, "fraction over horizon", "(Σ benefit − (one-off + annual cost × years)) / total cost",
              "customer-side value; base the benefit on a measured baseline or a sourced proxy and show the range",
              None, payback_months=payback_m, npv=npv_v, net_annual_benefit=net_annual,
              benefit_cost_ratio=(sum(benefits) / total_cost) if total_cost else None)


@metric
def customer_tco(years: int = 3, subscription_per_year: float = 0.0, implementation: float = 0.0,
                 integration: float = 0.0, training: float = 0.0, internal_staff_per_year: float = 0.0,
                 infrastructure_per_year: float = 0.0, alternative_cost_per_year: float | None = None,
                 alternative_one_off: float = 0.0) -> dict:
    """Total cost of ownership over a horizon versus the status-quo / alternative solution."""
    one_off = implementation + integration + training
    run = subscription_per_year + internal_staff_per_year + infrastructure_per_year
    tco = one_off + run * years
    extra = {"one_off": one_off, "run_per_year": run, "tco_per_year": tco / years if years else None}
    if alternative_cost_per_year is not None:
        alt = alternative_one_off + alternative_cost_per_year * years
        extra.update(alternative_tco=alt, saving=alt - tco, saving_share=(alt - tco) / alt if alt else None)
    return _r("customer_tco", tco, "money over horizon", "one-off (implementation + integration + training) + run cost × years",
              "compare with the status quo (manual work, current tools) over the same horizon", None, **extra)


@metric
def smb_monthly_value(price_per_month: float, hours_saved_per_month: float, hourly_cost: float,
                      other_savings_per_month: float = 0.0, setup_cost: float = 0.0) -> dict:
    """SMB view: monthly saving vs monthly price, net gain and payback of the set-up (in months)."""
    saving = hours_saved_per_month * hourly_cost + other_savings_per_month
    net = saving - price_per_month
    payback = (setup_cost / net if net > 0 else math.inf) if setup_cost else (0.0 if net > 0 else math.inf)
    return _r("smb_monthly_value", saving / price_per_month if price_per_month else None, "× (saving / price)",
              "(hours saved × hourly cost + other savings) / monthly price",
              "show it as 'pay X, save Y per month'; ≥ 3× is an easy decision for a small business", None,
              monthly_saving=saving, net_monthly_gain=net, payback_months=payback)


def display_value(r: dict, locale: str) -> str | None:
    """Locale-formatted value: fractions as %, multiples with x/倍, other numbers with locale separators."""
    from fmt_utils import fmt_multiple, fmt_number, fmt_pct
    v, unit = r.get("value"), str(r.get("unit", ""))
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    if unit.startswith("fraction"):
        return fmt_pct(v, 1, locale)
    if unit in ("x", "multiple", "ratio"):
        return fmt_multiple(v, 1, locale)
    return fmt_number(v, 2 if abs(v) < 100 else 0, locale)


def run_batch(payload: dict) -> dict:
    results = {}
    for i, c in enumerate(payload.get("calcs", [])):
        key = c.get("id") or f"{c['fn']}_{i}"
        try:
            results[key] = METRICS[c["fn"]](**c.get("args", {}))
        except Exception as e:  # report, never crash the batch
            results[key] = {"metric": c.get("fn"), "error": str(e)}
    return {"results": results}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "list"):
        print(dump_json({name: (fn.__doc__ or "").strip().split("\n")[0] for name, fn in METRICS.items()}))
        return 0
    name = argv.pop(0)
    payload, out, _ = cli_io(argv)
    loc = payload.pop("locale", None) if isinstance(payload, dict) else None
    res = run_batch(payload) if name == "batch" else METRICS[name](**payload)
    if loc:
        for r in (res["results"].values() if name == "batch" else [res]):
            if isinstance(r, dict) and "value" in r:
                r["display"] = display_value(r, loc)
    print(dump_json(res, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
