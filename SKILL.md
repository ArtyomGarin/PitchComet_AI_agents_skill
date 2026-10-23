---
name: pitchcomet
description: Use when you need a numbers-backed pitch deck (.pptx) and/or strategic report (.docx) for an IT product, AI system or technology development — even from a one-paragraph description with no data. Autonomous mode profiles the product, defines the market and segments, researches official statistics, and computes TAM/SAM/SOM (top-down, bottom-up, value-based), CAGR, pricing, unit economics, customer ROI/TCO, financial model, NPV/IRR/MOIC, Rule of 40 and valuation, every number sourced or a labelled estimate. Pitch patterns (large investor, small investor, corporate, SMB, government) and seven themes. Locales ru, en, zh, vi, id, ms; market profiles Russia, United States, China, Vietnam, Indonesia, Malaysia.
---

# PitchComet — computed pitch decks and strategy reports

Produces two consistent documents for an IT product or technology project:
an **analytical report (.docx)** — native Word charts, tables, citations in the locale's style —
and a **strategy deck (.pptx)** — minimalist layouts, native charts with embedded data, source
lines, speaker notes, seven themes. All numbers are computed by the tools and flow into
both documents from a single `facts.json`.

**Two ways in.** (A) *Autonomous* — the user gives only a description (or nothing but a product
name and a sentence): run the research loop below; never stop at missing data. (B) *Data-driven* —
the user has market, finance and scoring inputs: use the classic recipe (steps 1–9). Both end in the
same pipeline and the same QA gate.

## Autonomous mode (default when the user has no numbers)

1. **Brief.** Write `brief.json`: `name`, `text` (the description), `market`, `locale`,
   `audience` (or `pattern`), optional `segments`, `story`, `profile_overrides`
   (example: `examples/autonomous_shiftlyra/brief_ru.json`).
2. **Plan.** `python tools/auto_pitch.py --brief brief.json --plan-only` →
   `profile.json` (category, buyer, unit, pricing; each field from_text / inferred / default /
   to_confirm), `market_definition.json` (classification codes, segments, ICP) and
   `research_plan.json` (ledger keys, queries in the market language and English, official sources).
3. **Research.** Follow `prompts/<locale>/research_loop.md`: search, open official sources, write
   every figure into `ledger.json` with `tools/research_ledger.py` — `sourced` (link, year, access
   date) or `estimate` (method, formula, range, confidence). About 20–40 searches.
4. **Compute + build.** `python tools/auto_pitch.py --brief brief.json --pattern <id|auto> [--theme …] --render`.
   Missing inputs fall back to labelled benchmark ranges (`config/benchmarks.json`, rules of thumb);
   with an empty ledger the deck is an "offline draft" with a watermark.
5. **Check.** `auto_summary.json`: QA must show 0 errors; triangulation verdict; key numbers;
   the short `to_confirm` list (≤ 7 lines, never blocks the deck). Look at the contact sheets.
6. **Hand-off.** Key numbers each marked *sourced* (link) or *estimate* (formula, confidence), the
   pattern and theme used, the to-confirm list.

**Never fabricate: every number is either sourced or a labelled estimate with its formula.**
Gap placeholders ("no data", "TBD", "нет данных", "数据缺口" …) fail QA.

### Pitch patterns (`patterns/`)

| id | Audience | Slides | Must show |
|---|---|---|---|
| `large_investor` | growth / late-stage fund | 15–20 | TAM, SAM, SOM, CAGR, LTV/CAC, Rule of 40, IRR, MOIC |
| `small_investor` | angel / pre-seed / seed (default) | 10–14 | TAM, SOM, CAGR, LTV/CAC, MOIC |
| `corporate` | enterprise buyer / partner | 9–13 | customer ROI, TCO, payback |
| `smb` | small-business owners | 6–9 | price per month, saving, payback |
| `government` | grant / public programme | 11–15 | SAM, CAGR, ROI, public effect |

Each pattern sets slide order, length, mandatory metrics (`qa_check.py --pattern`), scoring weights,
charts, tone, what to cut, the call to action and red-team questions. `--pattern auto` picks one from
the `audience` text. Playbooks: `patterns/<id>.md`.

### Glossary slide ("What the numbers mean")
Every deck gets a plain-language glossary right after the title slide, and every report gets the
same list as a short section before the first chapter. It lists only the metrics that the document
actually shows (TAM, CAGR, LTV/CAC, payback, IRR …), one everyday sentence each, split over two
slides when needed. Definitions: `config/glossary.json` (written natively in ru, en, zh, vi, id,
ms). Builders detect the metrics from the rendered text, so the list always matches the content;
QA fails a deck or report whose glossary is missing or incomplete (`glossary_missing`,
`glossary_incomplete`). Switch off with `meta.glossary: false` (QA: `--no-glossary`). Pattern
slide counts do not include the glossary slides.

### Themes (`config/themes.json`)
`light`, `dark`, `academic_light`, `comet` (navy + white, bar titles), `editorial` (serif, rule
titles), `corporate` (blue title band, split cover), `warm` (cream + coral, accent numbers). Each has
CJK font settings. `--theme` is repeatable; the first becomes `deck.pptx`, others `deck_<theme>.pptx`.

## Locales and market profiles

| Locale | Language | Numbers | Citations (default) | Default market profile |
|---|---|---|---|---|
| `ru` | Russian | `3,0 млрд ₽` | GOST R 7.0.5-2008 footnotes | `ru` Russia |
| `en` | English | `$3.0B` | APA 7 author-date (Chicago optional) | `en` United States |
| `zh` | Simplified Chinese | `30亿元`, `3,600万元` | GB/T 7714-2015 numeric | `zh` Mainland China |
| `vi` | Vietnamese | `3,0 nghìn tỷ ₫`, `36 tỷ ₫` | APA 7 | `vn` Vietnam |
| `id` | Indonesian | `Rp3,0 triliun`, `Rp36 miliar` | APA 7 | `id` Indonesia |
| `ms` | Malay | `RM3.0 bilion`, `RM36 juta` | APA 7 | `my` Malaysia |

Set `"locale"` in `project.json` (or pass `--locale` to any tool). The **locale** controls
formatting, labels, fonts and citation style; the **market profile** (`project.market_profile`,
default derived from the locale) controls scoring weights, the definition of the *Regulation &
sovereignty* criterion and red-flag rules. Guides: `markets/<profile>.md`.
Answer the user in their language; write documents in the locale they chose.

## Files

| File | Purpose |
|---|---|
| `research/presentation_techniques.md` | generic storyline, number, proof and delivery techniques and where each is built in |
| `markets/*.md` | per-market data sources, regulation & sovereignty, discount rate/inflation, presentation culture, banned phrases |
| `scoring_model.md` (+ `.ru.md`, `.zh-CN.md`) + `config/scoring_model.json` | potential score: weights, 0–5 anchors, red flags, stages, audiences, market profiles |
| `metrics.md` | formulas, examples, thresholds; currency, inflation, discount rates |
| `deck_structure.md` | 16-slide master deck, audience variants, report structure, GOST variant |
| `style_guide.md` | text and visual rules, final checklist |
| `tools/` | calculations, docx/pptx builders, QA, rendering (`tools/README.md`, `tools/tools.json`) |
| `prompts/<locale>/` | research loop (autonomous mode), intake questionnaire, research brief, storyline builder, slide writer, red-team reviewer |
| `patterns/` | five pitch patterns: `patterns.json` + playbooks |
| `config/benchmarks.json` | rules of thumb (labelled, not sourced facts) used as estimate fallbacks |
| `config/market_taxonomy.json` | national classifications ↔ ISIC, 18 product categories with keywords in six languages |
| `templates/<locale>/` | templates of all inputs and specs (working copies of the example) |
| `examples/example_<locale>/` | fictional product "Velordoc" (EXAMPLE DATA) with outputs, one per locale |
| `examples/autonomous_shiftlyra/` | autonomous run from a short description: real market data with links, fictional product; five patterns, seven themes |
| `ADAPTING.md` | adapting to another industry, organisation, locale, brand |

## Recipe (data-driven mode)

### 0. Setup
```bash
pip install -r requirements.txt
python -m unittest discover -s tools/tests
python tools/new_project.py --dir work/my_product --name "My product" --locale en
```
LibreOffice and poppler (`pdftoppm`) are needed only for PNG previews; for `zh` renders install
Noto Sans CJK (the renderer maps Microsoft YaHei / SimSun to it).

### 1. Intake
Run `prompts/<locale>/intake_questionnaire.md`. Minimum before calculating: audience and the
decision it takes · stage · what the product does · customer segments with organisation counts
and contract size · pilot metrics / traction · costs and cash · the ask.
**Never invent answers**: unknown → an estimate with formula, range and confidence (`tools/estimator.py`,
logged in the ledger) plus one line in the "to confirm" list. The questionnaire is optional.

### 2. Data checklist
| Block | Data | File |
|---|---|---|
| Market | segments: organisations, annual contract, SAM share, SOM share; external market estimate for the top-down check; CAGR per scenario; inflation | `market_input.json` |
| Finance | new customers by year, ARPA and growth, churn, COGS %, R&D, S&M, G&A, capex, cash, rounds, discount rate, exit | `finance_input.json` |
| Scoring | 0–5 scores + evidence A/B/C + rationale for 11 criteria; facts for red flags (LTV/CAC, runway, market-specific compliance facts, concentration) | `scoring_input.json` |
| Metrics | pilots (before/after, n), automation ROI, TRL, etc. | `project.json → metrics.calcs` |
| Key facts | what must match between deck and report | `project.json → key_facts` |
| Sources | every external fact: structured reference, URL, access date | `report_spec.json → sources` |

### 3. Research
`prompts/<locale>/research_brief.md` and `markets/<profile>.md`. Only verifiable sources with a
link and a date; macro inputs (risk-free rate, policy rate, inflation) from the central bank and
statistics office of the market. If web search/fetch tools are available, use them; a fact
without a link does not go into a document.

### 4. Calculations
```bash
python tools/market_sizing.py   --input market_input.json  --locale en   # TAM/SAM/SOM, scenarios
python tools/financial_model.py --input finance_input.json --locale en   # P&L, NPV/IRR/MOIC, scenarios
python tools/scoring.py         --input scoring_input.json --locale en --market en
python tools/metrics_calc.py batch --input calcs.json
```
(or go straight to step 7 — the pipeline does everything). Check warnings: market methods
diverging > 2×, terminal value share > 75%, negative cash, LTV/CAC < 3, red flags.

### 5. Scoring
Choose the stage from facts (`scoring_model.md`, "How to use"). The audience changes weights; the
market profile multiplies them and redefines the regulatory criterion. The pipeline computes all
four audience profiles — show them in the appendix. Present the score **with its range** and the
weak points; the grade is a recommendation, not a decision.

### 6. Storyline
`prompts/<locale>/storyline_builder.md`: main answer → situation/complication/question/answer →
3–4 arguments → slide titles. Structure: `deck_structure.md`. Techniques:
`research/presentation_techniques.md`.

### 7. Build
`prompts/<locale>/slide_writer.md` → `deck_spec.json`, `report_spec.json` (numbers only as
placeholders `{{path|fmt}}` and `{"$ref": …}` into `facts.json`; keys in `tools/README.md`). Then:
```bash
python tools/run_pipeline.py --project work/my_product/project.json
```
Output in `out_dir`: `report.docx`, `deck.pptx`, `deck_dark.pptx`, `facts.json`, `qa_*.json`,
`renders/` (PNG pages and contact sheets), `pipeline_summary.json`.

**DOCX**: `meta.preset` — `report` (12 pt, 1.15) or `gost` (14 pt, 1.5, 1.25 cm indent);
`meta.citation_style` — `footnotes`, `numeric` or `author_date` (default from the locale);
fonts from the locale (zh: SimSun body / SimHei headings with East Asian font slots set).
**PPTX**: themes `light` / `dark` / `academic_light` or a custom dictionary; 12 layouts; source
line and slide number on every slide; speaker notes; zh decks use Microsoft YaHei with a CJK
fallback.

### 8. QA
1. `qa_check.py` (run by the pipeline): **0 errors** required; fix or justify warnings.
2. Look at the PNGs (`renders/*/contact_sheet.png`, then single pages): overlaps, clipping,
   empty areas, chart label legibility, missing glyphs (tofu boxes) in CJK/Vietnamese text.
3. `prompts/<locale>/red_team_reviewer.md` — fix critical findings.
4. `style_guide.md` §3 — final checklist.

### Using the tools from an agent
* Agents that load skills read this file; everything else is a CLI.
* Function calling: `python tools/agent_tools.py schemas` prints six high-level tools
  (plan, build, pipeline, qa, metric, glossary) as JSON Schemas; `call_tool(name, args)` runs them.
* MCP: `python tools/mcp_server.py` is a dependency-free stdio server with the same six tools.
* Low-level schemas for every module: `tools/tools.json`.

### 9. Hand-off
Give the user the paths to `report.docx`, `deck.pptx` (and the dark version), 2–4 PNGs of key
slides, the QA result, the list of estimates and the short to-confirm list. Remind them to update fields in
Word (Ctrl+A, F9) for the table of contents.

## Hard rules
* Never invent real-world facts. Real figures only with a link; estimates labelled with formula,
  range and confidence; illustrative figures labelled.
* Never stop at missing data and never print gap placeholders — estimate and label instead.
* Fictional examples are marked "EXAMPLE DATA" in the locale's language.
* Respect source restrictions of the target market.
* Native charts, not pictures. Numbers come from `facts.json`.
* Forecasts as scenarios; nominal/real stated; currency and FX date stated.
* Legal references must be re-verified at the time of writing (laws in several markets changed in
  2025–2026; see `markets/`).
* **Disclaimer, stamped on every document:** nothing here is legal advice or an investment
  recommendation. Documents are machine-generated drafts for the user's own review; figures must be
  verified, and the user bears full responsibility for use and accuracy.
