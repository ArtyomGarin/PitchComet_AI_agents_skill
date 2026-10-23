# Deck and report structure

The master structure combines generic techniques from `research/presentation_techniques.md`:
answer first; problem → solution → why now → market → traction → model → team → ask; the
investment-memo sequence (thesis → value-creation plan → comparables → IRR/MOIC → risks ↔
mitigations → exit); and a composite metric with the leading segment in the title.

**Rules for every slide:** action title (a full sentence with a number, ≤ 15–18 words or
≤ 30–40 CJK characters, ≤ 2 lines) · one message per slide · a "Source: …" line on every slide
with numbers · native, editable charts with embedded data · speaker notes · ≤ 6 bullets.
"Layout" is the layout name in `build_pptx.py`. Example titles below come from the fictional
Velordoc example (`examples/example_en/`).

## 1. Master deck: 16 slides (12–18 allowed)

| # | Slide | Job of the slide | Example action title | Required numbers | Layout | Audience variants |
|---|---|---|---|---|---|---|
| 1 | **Title** | name the product and its value in one sentence | "Velordoc: on-premise AI that reads, checks and routes business documents" | — (date, organisation) | `title` | Government: programme / call name, application number. Academia: principal investigator, project code |
| 2 | **Answer first** | the whole story in 30 seconds: score + 2–3 supporting numbers + condition | "Potential 64/100: strong problem and market, sales evidence still thin" | total score; SAM; key value metric; return / effect | `big_number` (3 numbers) | Investor: MOIC/IRR. Government: effect for public customers and TRL. Corporate: ROI and payback. Academia: novelty + TRL |
| 3 | **Problem and why now** | measured pain and the window of opportunity | "Back-office staff spend 15 minutes per document on manual entry and checks" | time/money lost; size of the affected group; why-now trigger | `bullets` or `big_number` | Government: link to national programmes. Corporate: losses of a specific unit |
| 4 | **Solution** | "today → with us" | "Solution: a local classify → extract → validate → route pipeline instead of manual entry" | 1–2 product parameters (speed, accuracy) | `two_column` | Academia: method and prior work. Corporate: integration with current systems |
| 5 | **Market TAM/SAM/SOM** | size of the prize, method, check | "Serviceable market is $0.5B in 2025; achievable share by 2030 is $53M" | TAM, SAM, SOM; method; top-down vs bottom-up gap | `chart` bar funnel + takeaway | Government: market = number of public buyers and programme budgets |
| 6 | **Segments** | where the money is and where to start | "Banks and the public sector make up the largest share of SAM" | per segment: organisations, contract, SAM, SOM | `table` | Investor: + segment growth |
| 7 | **Market dynamics** | growth, drivers, scenarios | "SAM grows to $1.1B by 2030 at 18% a year (base case)" | CAGR per scenario; nominal/real | `chart` line (3 scenarios) | Government: link to programme targets |
| 8 | **Technology, TRL, evidence** | prove that it works | "Pilots: processing time −80%, field accuracy +12 pp over template OCR" | TRL; pilot metrics with n and baseline | `big_number` or before/after column chart | Academia and government: TRL in the title; publications, IP. Investor: traction (revenue, LOIs, retention) |
| 9 | **Competition and moat** | why we win and why it lasts | "More accurate than template OCR and, unlike cloud services, runs inside the customer network" | 2 comparison axes; 3–5 alternatives including "do nothing" | `matrix` 2×2 or `table` | Corporate: vs incumbent vendor and in-house build. Government: alternatives allowed in public procurement |
| 10 | **Potential score** | structured verdict and gaps | "Score 64/100 (grade C): main gaps are traction and proven unit economics" | score, range, grade, criterion contributions | `scorecard` | Audience weight profile (`scoring.py`); all 4 profiles in the appendix |
| 11 | **Business model and financial plan** | how and when we make money | "Base plan: revenue grows to $7M by 2030, EBITDA turns positive in 2030" | revenue, EBITDA, customers by year; break-even year; LTV/CAC | `table` or column+line chart | Government: budget efficiency, co-funding. Academia: short commercialisation plan |
| 12 | **Scenarios** | show the spread honestly | "Scenario spread is wide: 2030 revenue between $4M and $11M" | 3 scenarios; key drivers of differences | `chart` line | All audiences; the bear case is mandatory |
| 13 | **Returns / effect** | answer "what do I get" | "Investor return 1.3× in the base case, below the 3× venture benchmark" | NPV, IRR, MOIC by scenario; discount rate | `table` (base highlighted) | Government: economic effect / support, tax revenue, jobs. Corporate: ROI, TCO, payback |
| 14 | **Risks ↔ mitigations** | risks are known and managed | "Four key risks are manageable if first renewals happen before end-2027" | 3–5 risks; trigger/threshold each | `two_column` | Government: regulatory and sovereignty risks. Investor: concentration, runway |
| 15 | **Roadmap** | milestones that remove risk | "In 18 months: 10 contracts, compliance milestones, first export pilot" | 4–6 milestones with dates and metrics | `timeline` | Government/academia: TRL per milestone; grant reporting stages |
| 16 | **Ask and next step** | the decision we need | "Ask: $5M for 25% to prove repeatable sales" | amount, terms, tranches, use of funds, next-round milestone | `closing` | Government: grant + co-funding + performance indicators. Corporate: 3–5 day pilot workshop with a success metric. Academia: resources (data, compute, partners) |

**Optional slides (up to 18):** Team (after slide 9 for early-stage investors — `team` weighs
15% at the idea stage), Unit economics (separately at growth stage), Regulation & sovereignty
(mandatory for public-sector and regulated buyers; content from `markets/<profile>.md`),
Comparable companies and deals (late-stage investors), Use of funds (waterfall).

**Appendix (after the closing slide):** model assumptions; sensitivity table; scoring under the
4 audience profiles; market methodology; glossary; full source list.

## 2. Reordering for the audience

Slide allocation per section: `deck_weights` in `config/scoring_model.json`
(`python tools/scoring.py` returns `deck_allocation`). Weights table: `scoring_model.md`.

| Audience | Order (master-deck numbers) | Strengthen | Shorten |
|---|---|---|---|
| **Investor** | 1, 2, 3, 4, 5, 8 (traction), 6, 7, 9, team, 11, 12, 13, 14, 15, 16 | traction, unit economics, returns, market | technical detail → appendix |
| **Government / grant** | 1, 2, 3 (link to priorities), 4, 8 (TRL), regulation & sovereignty, 5, 11 (effect), 13 (effect / support), 14, 15 (stages), team, 16 | TRL, sovereignty and compliance, effect for public customers, stages and indicators | investor IRR/MOIC, company valuation |
| **Corporate** | 1, 2, 3 (unit's pain), 4, 8 (pilots), 9 (vs incumbent), 13 (ROI/TCO), 14, 15 (rollout plan), 16 (pilot) | ROI, integration, security, timeline | market size → 1 slide |
| **Academic review** | 1, 2, 3 (research problem), 4 (method), 8 (results, n, CI, TRL), 9 (vs state of the art), team / prior work, 15, 14, 16 | novelty, reproducibility, publications, IP | market and finance → 1 slide "path to application" |

**Length.** Typical norms per market are in `markets/*.md`. As a default: investor 12–16 slides
for 15–20 minutes; government committee often 7–10 minutes → 10–12 slides; corporate 10–12 plus
a demo; academia 12–15 plus a data appendix.

## 3. Analytical report (.docx)

The report is the "full version" of the deck: the same numbers (from `facts.json`), more method
and assumptions. Template: `templates/<locale>/report_spec.template.json`; example:
`examples/example_<locale>/report_spec.json`. Section titles are localized by the example specs.

| # | Section | Content | Length |
|---|---|---|---|
| — | Title page | title, organisation, author, date, classification / note | 1 p. |
| — | Contents | TOC field (update in Word with F9) | 1 p. |
| 1 | **Executive summary** | answer (situation–complication–question–answer), 3–4 key figures (`key_figures`), recommendation and conditions | 1 p. |
| 2 | Problem and context | measured pain, why now, regulatory context | 1–2 pp. |
| 3 | Market | 3.1 method; 3.2 bottom-up (segment table + funnel); 3.3 scenarios (table + line); real/nominal | 2–3 pp. |
| 4 | Product and technology | architecture, TRL, pilot results (before/after, n, significance) | 1–2 pp. |
| 5 | Competition and moat | table of alternatives, barriers, IP | 1 p. |
| 6 | Business model and unit economics | monetisation, price, CAC, LTV, payback | 1 p. |
| 7 | Financial plan and returns | P&L by year, revenue/EBITDA chart, scenarios, NPV/IRR/MOIC, sensitivity | 2 pp. |
| 8 | Potential score | scorecard table, contribution chart, range, confidence, audience profiles | 1–2 pp. |
| 9 | Regulation and sovereignty | criteria of the market profile (`markets/<profile>.md`) and the product's status | 1 p. |
| 10 | Risks and mitigation | risk, probability, impact, mitigation, trigger | 1 p. |
| 11 | Roadmap | milestones, metrics, TRL | 1 p. |
| 12 | Recommendations | decision, conditions, next steps | 0.5 p. |
| App. | Model assumptions; method; glossary | tables | as needed |
| — | **References** | all sources in the locale's citation style | 1 p. |

**Captions and sources.** Table captions above the table, figure captions below; separators
follow the locale ("Table 1. ", "Таблица 1 — ", "表1  ", "Bảng 1. ", "Tabel 1. ", "Jadual 1. ").
A "Source: …" line follows every numeric table and chart (QA checks it).

### 3.1. Citation modes (`meta.citation_style`, default from the locale)

* `footnotes` (ru default) — Word footnotes: `[[src:id]]` in text → footnote with the full
  reference from `sources`; free footnote — `[[fn:text]]`.
* `numeric` (zh default, GB/T 7714-2015) — superscript `[n]` in order of first citation and a
  numbered reference list.
* `author_date` (en, vi, id, ms default; APA 7 or Chicago author-date via
  `--citation-style chicago`) — "(Author, year)" in text and an alphabetical list with hanging
  indent.

Sources are structured (`type`, `authors`/`org`, `title`, `container`, `year`/`date`, `url`,
`accessed`); `tools/citations.py` formats them per style. A legacy `gost` string is used verbatim
for GOST output when present.

### 3.2. GOST variant (`meta.preset: "gost"`, Russian reports)

For reports to research funds and ministries in Russia. References: GOST 7.32-2017 (research
report) and GOST R 7.0.5-2008 / 7.0.100-2018 (bibliographic references). The preset sets Times
New Roman 14 pt, 1.5 spacing, 1.25 cm first-line indent, margins 30/15/20/20 mm (left/right/
top/bottom), justified text and page numbers at the bottom centre. Example footnote:

> ГОСТ Р 58048-2017. Трансфер технологий. Методические указания по оценке уровня зрелости
> технологий : утв. приказом Росстандарта от 29.12.2017 № 2128-ст // ГАРАНТ.РУ. URL:
> https://base.garant.ru/72237776/ (дата обращения: 20.10.2026).

For GOST 7.32 add the sections Abstract, Definitions, Introduction and Conclusion as `heading` +
`paragraph` blocks; the preset does not create them automatically.

## 4. Deck ↔ report mapping

| Slide | Report section |
|---|---|
| 2 | 1 Executive summary |
| 3–4 | 2, 4 |
| 5–7 | 3 |
| 8 | 4 |
| 9 | 5 |
| 10 | 8 |
| 11–13 | 6, 7 |
| 14 | 10 |
| 15 | 11 |
| 16 | 12 |

`qa_check.py` checks the key numbers (`key_facts`) in both documents and warns if a number on a
slide does not appear in the report.
