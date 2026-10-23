# Adapting PitchComet

## 0. Autonomous mode: categories, benchmarks, patterns, wording
* **Product category.** Add a category to `config/market_taxonomy.json → categories` (keywords in
  the six languages, `buyer_industries` as ISIC sections, `unit`, `price_metric`, `value_drivers`,
  roles). `product_profiler.py` picks it by keyword hits; `profile_overrides` in a brief forces it.
* **Classifications.** `classifications.<market>` maps the national code (ОКВЭД 2, NAICS, GB/T 4754,
  VSIC, KBLI, MSIC) to ISIC Rev.4 sections; add a market here and in `market_definer.COUNTRY`.
* **Benchmarks.** `config/benchmarks.json` holds rules of thumb (segment ACV, churn, NRR, gross
  margin, CAC payback, adoption shares, valuation discounts, team ramp, R&D share cap). They are
  fallbacks, always logged as `estimate` with `confidence: low`; replace them with sourced figures in
  the ledger whenever research finds them. Keep the label "RULES OF THUMB, NOT SOURCED FACTS".
* **Ledger keys.** `auto_pitch.py` reads the keys listed in its docstring (`count.<segment>`,
  `industry.revenue.<ISIC>`, `share.size_band.<ISIC>`, `wage.*`, `macro.*`, `valuation.*`,
  `pricing.price_month`, `value.hours_saved_month`, `adoption.*`, `share.*`, `deal.units`). Facts with
  `geo` are found for the market's country automatically.
* **Narrative.** `tools/pitch_story.py`: `GENERIC` holds category-neutral wording, `STORY_PACKS`
  per-category wording (problem bullets, implementation steps, go-to-market, start steps, offer
  lines). Add a pack for your category instead of editing the slide builders. Narrative exists in
  `ru` and `en`; add another language by adding its key next to `ru`/`en`.
* **Patterns.** `patterns/patterns.json` (see `patterns/README.md`): slide order from the `s_<id>`
  builders, deck length, mandatory metrics and regex terms checked by `qa_check.py --pattern`,
  scoring `weights_override`, charts, tone, cut list, CTA, red-team questions, audience keywords for
  auto-selection.
* **QA completeness.** `qa_check.py`: `GAP_PATTERNS` (placeholders that fail), `SIZING_TERMS`,
  `CAGR_TERMS`, `UE_TERMS`, `ROI_TERMS` per language. Extend them when adding a locale.


## 1. Another industry or product type
* **Criteria and weights**: edit `config/scoring_model.json` (`criteria[].weight`,
  `stage_profiles`, `audience_multipliers`). Every `stage_profiles` column must sum to 100 (a test
  checks it). Then run `python tools/gen_scoring_doc.py` (regenerates `scoring_model*.md`) and the
  tests.
* **Anchors**: rewrite `anchors_en` / `anchors_ru` / `anchors_zh` for the industry (e.g. for
  medtech — clinical trial phase and device registration instead of a software registry; for
  hardware — production maturity and unit cost along Wright's law). Locales without their own
  anchors (vi, id, ms) fall back to English; add `anchors_<locale>` to localize them.
* **Red flags**: `red_flag_rules` — types `score_below_with_weight`, `stage_trl`, `fact_below`,
  `fact_above`, `fact_false_for_audience`; optional `markets: [...]` limits a rule to market
  profiles. Facts are passed in `scoring_input.json → facts`; messages per language
  (`message_en`, `message_ru`, `message_zh`, `message_vi`, `message_id`, `message_ms`).
* **Metrics**: a new metric is a function with the `@metric` decorator in
  `tools/metrics_calc.py` returning `_r(name, value, unit, formula, interpretation, None, **extra)`.
  It is immediately available in the CLI and in `project.json → metrics`.
* **Financial model**: non-subscription models (one-off licences, hardware) — set
  `other_revenue` by year and `cogs_pct`; for complex cases replace
  `financial_model.run_model`, keeping the `summary` keys used by `run_pipeline.build_facts`.

## 2. Another audience
* Add the audience to `audience_multipliers` and `deck_weights` (sum 100) and its labels to
  `labels.aud` of each locale in `tools/locales.py` (and `AUD_*` in `gen_scoring_doc.py`).
* Slide order: `deck_structure.md` §2 and your `deck_spec.json`.

## 3. Another market (country or region)
1. Add a profile to `market_profiles` in `config/scoring_model.json`: names, currency,
   `weight_multipliers`, `criteria.regulatory` (name, definition, anchors), the list of
   compliance `facts`, and `guide`.
2. Add market-specific red-flag rules with `"markets": ["<profile>"]`.
3. Write `markets/<profile>.md` with the five sections used by the existing guides. Every legal
   or statistical claim needs an official or reliable link and a verification date; avoid
   volatile numbers or date them.
4. Map the profile in `MARKETS` / `MARKET_ALIASES` in `tools/locales.py`.
5. Add a test in `tools/tests/test_tools.py` (profile loads, weights still sum correctly).

## 4. Another locale (language)
Add an entry to `LOCALES` in `tools/locales.py`: decimal/thousands separators, `scales`
(semantic codes `k`, `mn`, `bn`, `tn` mapped to local words), `currency`, `currency_style`,
`chart_scale_mn` / `chart_scale_bn`, `unit_mn` / `unit_bn`, fonts (`deck_latin`, `deck_ea`,
`report_latin`, `report_ea`, …), `citation_style`, caption separators, month names and all
`labels`. Then add `config/banned_phrases.json → <locale>`, `prompts/<locale>/`,
`templates/<locale>/`, an example, and tests.

### Glossary definitions
`config/glossary.json` holds one entry per metric: `abbr` (case-sensitive tokens such as `LTV/CAC`),
`words` (regular expressions per locale, matched case-insensitively), `term` and `def` per locale,
optional `implies` (showing LTV/CAC also explains LTV and CAC). Keep each definition to one
everyday sentence that a non-financial reader understands, written in the language rather than
translated word by word. A new locale needs `labels`, `term` and `def` for every entry; the tests in
`tools/tests/test_glossary.py` check coverage and that every definition fits on the slide.

## 5. Brand and design
* Themes: `config/themes.json` — seven built-in (`light`, `dark`, `academic_light`, `comet`,
  `editorial`, `corporate`, `warm`). Keys are documented in `_doc`: colours (`bg`, `text`, `muted`,
  `accent`, `accent2`, `palette`, `table_*`, `positive`, `negative`), fonts (`font_heading`,
  `font_body`, `font_numbers`, per-locale `fonts.<locale>` incl. `font_ea` for CJK), title style
  (`plain|rule|bar|band`), cover style (`plain|full|split`), big-number scale and colour. Or pass a
  dictionary in `deck_spec.meta.theme`. Select with `--theme` (repeatable) in `run_pipeline.py` /
  `auto_pitch.py`; a test builds every theme and runs QA.
* Report font: `report_spec.meta.font` or `--font`; accent: `meta.accent`.
* Logo: add a `picture` in `DeckBuilder._footer` (called on every slide), top-right, height
  ≤ 0.4 in.
* Corporate PPTX template: use `Presentation("template.pptx")` in `DeckBuilder.__init__` with a
  blank layout; grid sizes are constants at the top of `build_pptx.py`.

## 6. Formatting standards
* GOST 7.32-2017 (Russian research reports): `preset: "gost"`, add Abstract, Introduction and
  Conclusion sections. Bibliography: structured sources or a `gost` string per source.
* Funder-specific requirements (length, font, margins): `meta.font_size`, `line_spacing`,
  `first_line_indent_cm`, `gost_margins`.
* Citation style override: `meta.citation_style` and `meta.bibliography_style` or
  `build_docx.py --citation-style apa|chicago|gost|gbt7714`.

## 7. Moving to another agent or environment
* Self-contained: Python ≥ 3.10 + `requirements.txt`. LibreOffice and poppler only for previews.
* Agents without a shell can use `tools/tools.json` as function descriptions (JSON Schema
  inputs), or the six high-level tools of `tools/agent_tools.py` (`schemas`, `--format mcp`).
* MCP clients: start `python tools/mcp_server.py` as a stdio server.
* Paths in `project.json` are relative to the project file — move the folder as a whole.

## 8. Do not change without a reason
* The rule "numbers only from `facts.json`".
* QA errors (source on slides with numbers, native charts, unresolved placeholders, missing
  CJK fonts) protect against the most expensive mistakes in strategy documents.
