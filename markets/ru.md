# Market guide: Russia (`ru`)

Default locale `ru` · currency RUB · citations GOST R 7.0.5-2008 · verified 2026-10-20.

## 1. Statistics and data sources

| Need | Source | Link |
|---|---|---|
| Official statistics (prices, industries, enterprises) | Rosstat | https://rosstat.gov.ru/ |
| Key rate, inflation, OFZ yield curve, exchange rates | Bank of Russia | https://www.cbr.ru/hd_base/keyrate/ · https://www.cbr.ru/statistics/ddkp/infl/ · https://www.cbr.ru/hd_base/zcyc_params/ · https://www.cbr.ru/currency_base/daily/ |
| Registry of Russian software | Ministry of Digital Development (Mintsifry) | https://reestr.digital.gov.ru/ |
| Federal laws (current editions) | ConsultantPlus, GARANT, official publication portal | https://www.consultant.ru/ · https://base.garant.ru/ · http://publication.pravo.gov.ru/ |
| Public procurement | Unified procurement information system (EIS) | https://zakupki.gov.ru/ |

Some Russian government sites are not reachable from every network; a failed fetch is not
evidence that a page does not exist.

## 2. Regulation and sovereignty (definition of the criterion)

The *Regulation & sovereignty* criterion for this profile measures how ready the product is to be
bought by state bodies, state-owned companies and critical-infrastructure operators:

* **Registry of Russian software.** Rules: Government Decree No. 1236 of 16.11.2015
  (https://base.garant.ru/71252170/). For state and municipal buyers, registry inclusion is
  in practice a precondition for purchase.
* **Personal data.** Federal Law No. 152-FZ of 27.07.2006 "On Personal Data"
  (https://www.consultant.ru/document/cons_doc_LAW_61801/), including localisation of databases
  with personal data of Russian citizens.
* **Critical information infrastructure.** Federal Law No. 187-FZ of 26.07.2017
  (https://www.consultant.ru/document/cons_doc_LAW_220885/); the law was amended in 2023 and 2025,
  so check the current edition.
* **Procurement.** Federal Law No. 44-FZ of 05.04.2013 (state and municipal procurement,
  https://www.consultant.ru/document/cons_doc_LAW_144624/) and 223-FZ (procurement by certain
  types of legal entities, including state companies).
* **Technology readiness.** National standard GOST R 58048-2017 (TRL methodology,
  https://base.garant.ru/72237776/).
* **Dependencies.** Foreign cloud APIs, foreign OS/DBMS or unlicensed components in the core of
  the product are a red flag for public-sector buyers.

Scoring facts: `registry_eligible`, `critical_foreign_dependency`, `cross_border_data_unassessed`.

## 3. Discount rate, inflation, valuation

* Separate **nominal and real** figures explicitly ("in nominal roubles" or "in 2025 prices").
* Risk-free rate: OFZ zero-coupon yield for a maturity close to the forecast horizon (Bank of
  Russia curve, link above), with the date of the value.
* Monetary conditions benchmark: Bank of Russia key rate, **14.00%** as of 20.10.2026
  (https://www.cbr.ru/hd_base/keyrate/). Update before use.
* Venture-style discount rates for rouble cash flows are much higher than in USD; state the
  build-up (risk-free + equity risk premium × beta + size/stage premia) in the assumptions table.
  The example uses 28% as an illustrative assumption only.
* Inflation: actual — Rosstat and the Bank of Russia; the Bank of Russia inflation target is 4%.
  ARPA indexation should not be below expected inflation.
* Do not discount rouble cash flows at a dollar rate or vice versa. FX conversions use the
  official Bank of Russia rate on a stated date.
* Tax: IT companies that meet the conditions (accreditation and others) have preferential profit
  tax and social contribution rates; take the rate from the current Tax Code and cite it.

## 4. Audience and presentation culture

* **Government / state companies.** Expect evidence of registry status, import substitution,
  information security certification and measurable effect for the customer (time, cost). A
  formal tone, full official names of laws and bodies, a "passport" slide with key parameters.
* **Investors.** Unit economics, runway, a realistic rouble discount rate and exit routes that
  work in the current environment.
* **Grant committees and academia.** TRL per GOST R 58048-2017, novelty, publications and
  reproducibility.
* Reports often follow GOST R 7.32 / 7.0.5 conventions (title page, contents, numbered
  sources). Use `meta.preset: "gost"` when the customer asks for it.

## 5. Banned and hype phrases, pitch length

Locale list in `config/banned_phrases.json` → `ru`: «уникальный», «не имеет аналогов»,
«революционный», «прорывной», «гарантированно», «100% точность», «мировой лидер» and others.
«Лидер рынка», «крупнейший», «первый в России» are allowed only with a source.
Typical length: investor pitch 10–15 slides in 15–20 minutes; government briefing 8–12 slides
plus a detailed report.
