# tools/

Python ≥ 3.10. Install: `pip install -r requirements.txt` (repository root). For previews:
LibreOffice (`soffice`) and `pdftoppm` (poppler-utils); for Chinese renders a CJK font (Noto Sans
CJK SC). Every module is both a CLI and an importable library; machine-readable descriptions of
inputs/outputs are in `tools.json` (JSON Schema). Every tool accepts `--locale ru|en|zh|vi|id|ms`.

| Tool | What it does |
|---|---|
| `auto_pitch.py` | **autonomous mode**: brief → profile → market definition → research plan (`--plan-only`) → ledger + labelled estimates → TAM/SAM/SOM (3 methods, triangulated), CAGR, price, unit economics, customer ROI/TCO, finance, valuation → pitch pattern (`--pattern`, auto from audience) → deck(s) + report → QA; `auto_summary.json` |
| `product_profiler.py` | description → category, buyer segment and industries, roles, value drivers, unit, pricing model, price points, deployment, geography, currency, AI intensity, stage, traction; each field from_text / inferred / default / to_confirm |
| `market_definer.py` | profile → classification codes (ОКВЭД 2 / NAICS / GB/T 4754 / VSIC / KBLI / MSIC ↔ ISIC), segments, ICP, research plan with fallback methods, queries (market language + English), official sources from `markets/<mk>.md` |
| `research_ledger.py` | evidence ledger: sourced facts need a link and year, estimates need method, formula, range, confidence; dedup, currency/price-year normalisation, conflict resolution, export, citations |
| `estimator.py` | labelled estimates: safe formulas over ranges, benchmarks, top-down / bottom-up / value-based sizing, triangulation verdict, CAGR from drivers, value price, unit economics, comparables |
| `pitch_story.py` | narrative per pattern (ru/en), category story packs, default speaker notes, appendix that keeps every slide figure in the report |
| `metrics_calc.py` | ~50 metrics incl. `customer_roi`, `customer_tco`, `smb_monthly_value` (growth, SaaS, unit economics, burn, Rule of 40, NPV/IRR/MOIC, DCF, CAPM/WACC, inflation, Wright, Bass, TRL, automation ROI, accuracy vs baseline); each returns value, unit, formula, interpretation (+ `display` for a locale) |
| `market_sizing.py` | TAM/SAM/SOM top-down and bottom-up, triangulation (warning at > 2× divergence), CAGR scenarios, S-curve SOM, real values |
| `financial_model.py` | 5-year P&L and cash, CAC/LTV/payback, project NPV/IRR, investor MOIC/IRR with dilution, 3 scenarios, 2D sensitivity |
| `scoring.py` | 0–100 potential score over 11 criteria, stage × audience × market profiles, range and confidence, grade, red flags, slide allocation (`--market ru|en|zh|vn|id|my`) |
| `build_docx.py` | .docx report: title page, contents, native Word charts with embedded xlsx, tables, footnotes / numeric / author-date citations, references, locale fonts and East Asian font slots |
| `build_pptx.py` | minimalist 16:9 deck: 12 layouts, native charts with embedded data, source line, notes, seven themes (light, dark, academic_light, comet, editorial, corporate, warm) with title/cover styles, one-line big numbers, East Asian fonts for zh |
| `qa_check.py` | deck and report checks: overflow (CJK-aware), sources, charts as images, fonts (incl. missing CJK fonts), label titles, banned phrases per locale, placeholders, number consistency; **completeness gate**: errors for missing TAM/SAM/SOM, CAGR, unit economics, customer ROI (customer patterns), gap placeholders in six languages, pattern mandatory terms (`--pattern`, `--no-completeness`); **glossary gate**: errors when the glossary is missing or does not cover a metric that is shown (`--no-glossary`) |
| `glossary.py` | plain-language "What the numbers mean" slide(s) and report section: detects the metrics a document shows (same text extractor as QA) and lists only those; definitions in `config/glossary.json` (6 locales); `list` / `detect` CLI |
| `agent_tools.py` | six high-level agent tools (plan, build, pipeline, qa, metric, glossary): JSON Schemas for function calling (`schemas`, `--format mcp`) and a dispatcher (`call`) |
| `mcp_server.py` | minimal Model Context Protocol server over stdio (no dependencies) exposing the `agent_tools.py` tools |
| `run_pipeline.py` | the whole chain: market → finance → scoring → `facts.json` → report + deck (light and dark) → QA → renders |
| `render_preview.py` | PDF → PNG pages + contact sheet (palette PNG, small enough for a repository); maps Microsoft YaHei / SimSun / SimHei to Noto CJK via a private fontconfig file |
| `new_project.py` | scaffold a project from `templates/<locale>/` |
| `gen_scoring_doc.py` | regenerate `scoring_model.md`, `.ru.md`, `.zh-CN.md` from `config/scoring_model.json` |
| `locales.py` | locale definitions (separators, scale words, currency style, fonts, citation style, captions, labels, dates) and market profiles |
| `fmt_utils.py` | locale-aware number/money/percent formatting, `{{path|fmt}}` placeholders |
| `citations.py` | GOST R 7.0.5-2008, APA 7, Chicago author-date and GB/T 7714-2015 references and in-text citations |
| `ooxml_clean.py` | post-save clean-up of docx/pptx (and embedded xlsx): keeps only the theme script fonts relevant to the supported locales, sets the East Asian theme language to zh-CN for Chinese and removes it otherwise |
| `textfit.py` | text-fit estimation with CJK full-width characters and line-breaking rules (no line-start punctuation) |
| `charts_common.py` | shared native-chart engine for pptx and docx (palette, highlight, waterfall, labels, East Asian fonts) |

## Quick start

```bash
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_ru.json --plan-only < /dev/null
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_ru.json --pattern smb --theme warm --render < /dev/null
python tools/research_ledger.py validate --input examples/autonomous_shiftlyra/ledger_ru.json < /dev/null
python tools/estimator.py unit_economics --json '{"segment": "smb", "arpa_month": 1400}' < /dev/null
python tools/metrics_calc.py customer_roi --json '{"annual_benefit": 120000, "annual_cost": 20000, "one_off_cost": 10000}' < /dev/null
python tools/run_pipeline.py --project examples/example_en/project.json < /dev/null
python tools/new_project.py --dir work/my_product --name "My product" --locale vi
# edit *_input.json and *_spec.json, then
python tools/run_pipeline.py --project work/my_product/project.json --no-render
```

Single steps:

```bash
python tools/metrics_calc.py list < /dev/null
python tools/metrics_calc.py ltv_cac --json '{"ltv_value": 12.1e6, "cac_value": 2.5e6}' --locale id
python tools/market_sizing.py --input market.json --out market_result.json --locale zh
python tools/financial_model.py --input finance.json --out finance_result.json --locale ms
python tools/scoring.py template < /dev/null > scores.json && python tools/scoring.py --input scores.json --market vn
python tools/scoring.py profiles < /dev/null
python tools/build_docx.py --input report_spec.json --facts facts.json --out report.docx --locale vi --citation-style apa
python tools/build_pptx.py --input deck_spec.json --facts facts.json --theme dark --out deck.pptx --locale zh
python tools/qa_check.py --pptx deck.pptx --docx report.docx --facts facts.json --locale zh --out qa.json
python tools/render_preview.py deck.pptx --outdir renders/deck
python tools/citations.py --style gbt7714 --input sources.json        # one source or a list
```

CLIs read input from `--input file.json`, `--json '{...}'` or stdin (when stdin is not a
terminal; in scripts without input pass `< /dev/null`).

## How numbers work: `facts.json`

`run_pipeline.py` collects all results into one `facts.json`; deck and report specs reference it
with placeholders, so numbers in the two documents cannot diverge.

* `{{market.sam_base|money_bn}}` → `$0.5B` (en), `38,4 млрд ₽` (ru), `33.6亿元` (zh),
  `12,0 nghìn tỷ ₫` (vi), `Rp7,7 triliun` (id), `RM2.2 bilion` (ms).
* `{{fin.irr_base|pct0}}`, `{{score.total|num0}}`, `{{fin.moic_base|x1}}`, `{{metrics.pilot_accuracy.value|pp0}}`.
* `{"$ref": "charts.tam_sam_som"}` inserts a ready object (chart, table).
* Formats: `int`, `numN`, `pctN`, `ppN`, `xN`, `money`, `money_k|_mn|_bn|_tn` + `N` decimals, `raw`, `auto`.
  Scale codes are semantic: `mn` → 万 (zh), tỷ (vi), miliar (id), juta (ms); `bn` → 亿, nghìn tỷ,
  triliun, bilion.
* `{{project.units.mn}}` / `{{project.units.bn}}` give the chart unit for captions.
* An unknown path fails the build (better than a wrong number).

Autonomous runs add the `auto.*` namespace (from `auto_facts.json`): `auto.price_month`,
`auto.ask`, `auto.breakeven_phrase`, `auto.market.*` (methods, triangulation ratio, units),
`auto.ue.*` (ARPA, gross margin, churn, CAC, LTV, LTV/CAC, payback with ranges), `auto.cust.*`
(customer ROI, payback, TCO, monthly saving), `auto.val.*`, `auto.public.*`, `auto.ledger.*`
(counts of sourced facts and estimates), `auto.tables.*`, `auto.charts.*`.

Main keys: `project.*` (incl. `locale`, `units`, `market_profile`); `market.{tam,sam,som}_{base,td,bu}`,
`market.td_bu_ratio_tam`, `market.cagr_{bear,base,bull}`, `market.{tam,sam,som}_horizon_{bear,base,bull}`,
`market.real_cagr_*`; `fin.revenue_first|last`, `fin.revenue_cagr`, `fin.ebitda_last`, `fin.ltv_cac_last`,
`fin.cac_payback_last`, `fin.npv_*`, `fin.irr_*`, `fin.moic_*`, `fin.breakeven_*`, `fin.min_cash_*`, `fin.tv_share`,
`fin.discount_rate`; `score.total|grade|grade_label|range_lo|range_hi|confidence|market|regulatory_definition`,
`score.by_audience.*`; `charts.*` (tam_sam_som, sam_scenarios, som_scenarios, revenue_ebitda, revenue_scenarios,
cash, score, segments_sam); `tables.*` (segments, market_scenarios, pnl, fin_scenarios, scorecard, by_audience,
sensitivity); `metrics.<id>.*` (from `project.metrics`).

## Tests

```bash
python -m unittest discover -s tools/tests -v < /dev/null    # from the repository root; no pytest needed
```

The suite covers reference values (CAGR 100→200 in 5 years = 14.87%; IRR [−100, 10, 10, 110] = 10%;
Rule of 40 with neutral inputs 25% + 20% = 45%), weight sums = 100 for every stage × audience ×
market combination, number/date/currency formats of all six locales, the four citation styles,
CJK text fitting, market-specific red flags, the full pipeline for every locale (QA 0 errors, native
charts, localized captions and citations, East Asian font slots), scaffolding from templates and
repository hygiene. `test_autonomous.py` covers the profiler and market definer, ledger rules
(validation, conflicts, normalisation), estimator identities (ranges, triangulation, LTV/CAC),
customer ROI/TCO/SMB metrics, the QA completeness gate (missing sizing/CAGR/unit economics and gap
placeholders in six languages fail), patterns (slide builders exist, auto-selection), every theme
(build + QA) and full `auto_pitch` runs for four patterns plus an offline run. `test_glossary.py`
covers the definitions in six locales, metric detection, the glossary slide and report section in
every locale and theme, text fit of the full glossary and the QA gate (missing or incomplete
glossary fails). `test_agent_tools.py` covers the function-calling schemas, tool calls and an MCP
session (initialize, tools/list, tools/call, errors). Tests write only to temporary directories.

## Known limitations

* Chart number formats in LibreOffice renders follow the renderer, not the document language;
  Word shows the locale's separators (charts carry `c:lang`).
* The table of contents is a field with pre-filled entries without page numbers; update fields in
  Word (Ctrl+A → F9).
* Text-fit estimation is heuristic (average glyph widths, CJK full-width); always inspect the PNGs.
* Autonomous narrative is ru/en; zh/vi/id/ms get English narrative with local formatting.
* Benchmarks are rules of thumb; estimates built on them carry `confidence: low` until research or
  pilot data replace them.
* vi/id/ms anchors of the generic criteria fall back to English (market-specific anchors are
  localized).
