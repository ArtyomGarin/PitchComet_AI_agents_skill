# Metrics reference

All formulas are implemented in `tools/metrics_calc.py` (function name = metric name). Every call
returns `{metric, value, unit, formula, interpretation, inputs, …}`; `interpretation` applies the
thresholds below. Examples in this file were **computed with the tool**; inputs are illustrative
and currency-neutral ("units" = any currency).

```bash
python tools/metrics_calc.py list < /dev/null
python tools/metrics_calc.py cagr --json '{"start":100,"end":200,"years":5}' < /dev/null
python tools/metrics_calc.py batch --input calcs.json        # {"calcs":[{"id","fn","args"}]}
python tools/metrics_calc.py rule_of_40 --json '{"revenue_growth":0.25,"profit_margin":0.20}' --locale vi
```

Conventions: shares as fractions (`0.18` = 18%); money in one currency and one scale inside a
calculation; the period of a metric (month / year) is explicit. Thresholds are **guides** for B2B
SaaS and IT products; see §10 for public-sector and research audiences. With `--locale` the tool
adds a `display` field formatted for that locale.

## 1. Growth and market

| Metric | Formula | Example (tool) | Thresholds / interpretation |
|---|---|---|---|
| **CAGR** `cagr` | (end / start)^(1/years) − 1 | 100 → 200 in 5 years = **14.87%** | < 5% slow; 5–15% moderate; 15–30% fast; > 30% check the base |
| CAGR projection `project_cagr` | start × (1+r)^t | 3.0 bn × 1.18^5 = **6.86 bn** | — |
| Growth rate `growth_rate` | current / previous − 1 | 130 / 100 = **30%** YoY | state the period (YoY, QoQ) |
| MoM → annual `mom_to_annual` | (1+MoM)^12 − 1 | 5% a month = **79.6%** a year | early stage: 15–20% MoM is strong |
| Market share `market_share` | revenue / market | 60 m / 3 bn = **2%** | < 1% niche; 1–5% visible; > 20% leader |
| TAM / SAM / SOM | see `market_sizing.py` | example output in `examples/` | top-down vs bottom-up gap > 2× → revisit the method |
| Logistic adoption `logistic_adoption` | K / (1+e^(−k(t−t0))) | K = 60%, t0 = 2029, k = 0.8 → 2030: **41%** | 10%→90% in 5.5 years |
| Bass diffusion `bass_diffusion` | n_t = (p + q·N/M)(M − N) | M = 1000, p = 0.03, q = 0.38 → **273** after 5 periods | typical p ≈ 0.01–0.03; q ≈ 0.3–0.5 |

**Market rules.** (1) The primary estimate is **bottom-up** (organisations × annual contract ×
shares). (2) Top-down is a check only. (3) Never use a global "AI market" as the TAM of a niche
product. (4) Every multiplier has a source in the assumptions table. `market_sizing.py` computes
both estimates and their triangulation (geometric mean) and warns at > 2× divergence.

## 2. Subscription revenue (SaaS)

| Metric | Formula | Example | Thresholds |
|---|---|---|---|
| **ARR** `arr_from_mrr` | MRR × 12 | MRR 5 m → **60 m** | recurring contracted revenue only; one-off implementation separately |
| MRR bridge `mrr_bridge` | start + new + expansion − contraction − churn | 10 + 1.5 + 0.5 − 0.2 − 0.3 = **11.5 m** | show as a waterfall |
| **NRR** `nrr` | (start + expansion − contraction − churn) / start | (100+20−5−5)/100 = **110%** | < 90% weak; 90–100% average; 100–120% good; > 120% excellent |
| **GRR** `grr` | (start − contraction − churn) / start | **90%** | ≥ 90% strong enterprise; < 80% product problem |
| Churn `churn_rate` | lost / base at start | 3 / 100 = **3% a month** | enterprise < 1% a month; SMB 2–5% a month |

## 3. Unit economics

| Metric | Formula | Example | Thresholds |
|---|---|---|---|
| **CAC** `cac` | fully loaded sales & marketing / new customers | 30 m / 12 = **2.5 m** | compare with ARPA and payback |
| **LTV** `ltv` | ARPA × gross margin / churn | 2.6 m × 0.7 / 0.15 = **12.1 m** (lifetime 6.7 years) | cap lifetime at 5 years at early stage (`financial_model.py` does) |
| **LTV/CAC** `ltv_cac` | LTV / CAC | 12.1 / 2.5 = **4.8×** | < 1 destroys value; 1–3 weak; 3–5 healthy; > 5 under-investing in growth |
| **CAC payback** `cac_payback` | CAC / (monthly ARPA × GM) | 2.5 m / (216.7 k × 0.7) = **16.5 months** | < 12 excellent; 12–18 good; 18–24 acceptable for enterprise; > 24 poor |
| **Gross margin** `gross_margin` | (revenue − COGS) / revenue | **70%** | SaaS 70–80%+; with services/hardware 40–60%; check inference cost for AI products |
| Contribution margin `contribution_margin` | (revenue − variable cost) / revenue | **55%** | > 0 per unit before scaling |
| Unit economics `unit_economics` | (price − variable) × lifetime − CAC | (2.6 − 0.8) × 4 − 2.5 = **4.7 m** per customer | > 0: the customer pays back acquisition |
| Break-even `break_even` | fixed / (price − variable) | 120 m / 1.8 m = **67 customers** | compare with SOM |

## 4. Efficiency and cash

| Metric | Formula | Example | Thresholds |
|---|---|---|---|
| Burn `burn` | (cash start − (cash end − raised)) / months | (200 − 140) / 12 = **5 m a month** | — |
| **Runway** `runway` | cash / net monthly burn | 140 / 5 = **28 months** | < 6 critical (red flag); 6–12 raise now; > 18 comfortable |
| **Burn multiple** `burn_multiple` | net burn / net new ARR | 60 / 40 = **1.5×** | < 1 excellent; 1–1.5 very good; 1.5–2 good; 2–3 suspect; > 3 bad (D. Sacks: https://www.craftventures.com/articles/the-burn-multiple) |
| **Rule of 40** `rule_of_40` | YoY revenue growth + margin (EBITDA, FCF or adjusted operating) | 25% + 20% = **45%** | ≥ 40% healthy SaaS (B. Feld: https://feld.com/archives/2015/02/rule-40-healthy-saas-company/); state which margin |
| **Magic number** `magic_number` | (rev_q − rev_q−1) × 4 / S&M_q−1 | (30 − 25) × 4 / 25 = **0.8** | < 0.5 inefficient; 0.5–0.75 improve GTM; > 0.75 accelerate (https://www.scalevp.com/blog/saas-metrics-a-history-of-the-magic-number) |

## 5. Investment and valuation

| Metric | Formula | Example | Thresholds |
|---|---|---|---|
| **NPV** `npv` | Σ CF_t / (1+r)^t | CF −200, −40, 10, 60, 120, 400 at 28% → **−35.4** | > 0 at the discount rate → accept |
| **IRR** `irr` | r such that NPV = 0 | −100, 10, 10, 110 → **10.0%** | buyout deals often target 15–25%; venture 30%+ at seed/A |
| **MOIC** `moic` | total value returned / invested | 480 / 200 = **2.4×** | buyout 2–3×; venture deal level 3–10× |
| IRR from MOIC `irr_from_moic` | MOIC^(1/years) − 1 | 2.4× over 5 years = **19.1%** | always show **both** IRR and MOIC |
| **DCF** `dcf` | Σ FCF/(1+r)^t + TV/(1+r)^N | exit at 4× revenue → **384.6**; Gordon (g = 5%) → **97.9** | TV share > 75%: value depends on the distant future; show both methods |
| CAPM `capm` | rf + β·ERP + premia | 14.5% + 1.3 × 7% + 3% = **26.6%** | see §9 and `markets/` |
| WACC `wacc` | E/V·Re + D/V·Rd·(1−t) | **25.4%** | — |
| EV multiple `ev_multiple` | EV / revenue (EBITDA) | 1.4 bn / 349 m = **4.0×** | compare only with peers of similar growth and margin |
| Valuation from multiple `valuation_from_multiple` | metric × multiple | 349 m × 4 = **1.40 bn** | — |
| EV `enterprise_value` | equity + debt − cash (+ minorities, preferred) | 1 000 + 200 − 150 = **1.05 bn** | — |
| Dilution `dilution` | investment / post-money | 200 / (600 + 200) = **25%**; with a 10% option pool founders keep **65%** | seed/A round: 15–25% |

## 6. Technology, R&D and AI products

| Metric | Formula | Example | Comment |
|---|---|---|---|
| **TRL** `trl_assess` | highest level for which all lower levels are confirmed | flags `trl1…trl6` = true → **6** | 1–3 research; 4–6 development; 7–9 deployment. Scales: NASA TRL, GOST R 58048-2017 |
| Wright's law `wright_law` | C_n = C_1 · n^log2(1−LR) | 100 → 8th unit at LR 20% = **51.2** | data: https://ourworldindata.org/learning-curve |
| Learning-rate fit `learning_rate_fit` | regression of ln C on ln N | 100, 80, 64, 51.2 → **LR = 20%**, R² = 1.0 | needs ≥ 4 points and ≥ 2 doublings |
| **Automation ROI** `automation_roi` | (savings × years − cost) / cost | 600 tasks/yr, 24 h → 4 h, 1 500/h, licence 3 m/yr, implementation 1.5 m, 3 years → ROI **414%**, payback **1.2 months**, **12 000 h/yr** saved | time savings need a **measured baseline** (time study, logs) |
| Cost per task `cost_per_task` | cost / tasks | 1.2 m / 6 000 = **200** vs 900 manual | show together with quality |
| **Accuracy vs baseline** `accuracy_vs_baseline` | acc_model − acc_base + z-test | 455/500 vs 390/500 → **+13 pp**, significant at 95% | always n and the confidence interval; difference in pp, not % |
| R&D productivity `rd_productivity` | outputs / (R&D spend / 10^6) | 12 releases on 60 m and 15 FTE → **0.2** per 1 m; 0.8 per FTE | compare with your own history |

**AI specifics.** Include inference cost (GPU hours, tokens) in COGS; for on-premise deployments
include hardware depreciation. For LLM products show quality on the customer's **held-out** task
set, not only public benchmarks; state the model version and measurement conditions.

## 7. Price

| Metric | Formula | Example | Comment |
|---|---|---|---|
| Value-based price `value_based_price` | value created × capture share | 8.2 m × 30% = **2.46 m a year** | capture 10–30%; > 50% leaves little reason to switch |
| Elasticity `price_elasticity` | %ΔQ / %ΔP (midpoint) | +10% price → −10% volume: **−1.11** | \|e\| > 1 elastic |

## 8. Sensitivity and scenarios

* `sensitivity_1d` — one variable, a set of deltas: `{"base_inputs":{…},"fn":"npv","variable":"rate","deltas":[-0.2,0,0.2]}`.
* `scenarios` — named override sets (bear / base / bull).
* `financial_model.py` builds a 2D grid (e.g. new customers × ARPA) and three scenarios with NPV,
  IRR, MOIC, break-even year and minimum cash.
* Always three scenarios with explicit assumption differences; never headline the bull case
  without the base case next to it.

## 9. Currency, inflation and discount rates

1. **Nominal or real, explicitly.** Label every forecast "nominal" or "in base-year prices".
   The tools default to nominal; `deflate` and `real_rate` compute real values.
   Example: nominal SAM growth 18% with inflation 6% → real **11.3%** (Fisher:
   (1 + 0.18) / (1 + 0.06) − 1).
2. **Discount rate in the currency of the cash flows.** Risk-free = government bond yield of a
   maturity close to the horizon, dated and linked; add equity risk premium × beta and
   size/stage premia; document the build-up in the assumptions table. Never discount local-currency
   flows at a USD rate or vice versa. Market-specific sources: `markets/<profile>.md`.
3. **Inflation.** Actual figures from the national statistics office or central bank; forecasts
   from an official, dated source. Parameter `inflation` in `market_input.json`.
4. **Price indexation.** `arpa_growth` should not be below expected inflation, otherwise real
   revenue per customer falls; state it in the assumptions.
5. **FX.** `fx_convert` with the official central-bank rate on a stated date; do not mix dates in
   one table; show the original currency in brackets.
6. **Number format.** Locale-aware formatters (`fmt_utils.py`, formats `money_mn1`, `money_bn`,
   `pct1`, `pp1`, `x1`): ru `3,0 млрд ₽`; en `$3.0B`; zh `30亿元`; vi `3,0 nghìn tỷ ₫`;
   id `Rp3,0 triliun`; ms `RM3.0 bilion`.
7. **Tax.** Use the statutory rate for the jurisdiction and any incentive regime the company
   actually qualifies for; cite the source.

## 10. Thresholds by audience

* **Investor:** thresholds as above; key metrics LTV/CAC, CAC payback, burn multiple, MOIC/IRR.
* **Government / grant:** instead of LTV/CAC — economic effect for the customer (`automation_roi`,
  `cost_per_task`), TRL, local content, budget efficiency (effect / support amount).
* **Corporate buyer:** ROI and payback for the business unit, TCO against the current solution,
  implementation time.
* **Academia:** novelty, TRL, reproducibility (`accuracy_vs_baseline` with n and CI), R&D
  productivity.
