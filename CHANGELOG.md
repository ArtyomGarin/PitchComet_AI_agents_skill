# Changelog

All notable changes to this project are documented here. Versions follow semantic versioning.

## [0.1b0] — 2026-10-20

### Added
- AI assistants **Grok** and **GigaChat** were actively used, together with
  personal hands-on experience, to draft and refine the skill, prompts, tools and documentation.
- **Glossary "What the numbers mean"** right after the title slide of every deck (all patterns,
  locales and themes) and as a short section before the first chapter of every report. It lists
  only the metrics the document shows, one plain sentence each, and splits over two slides when
  there are more than 12. Definitions for 34 metrics in `config/glossary.json`, written natively in
  ru, en, zh, vi, id and ms. New module `tools/glossary.py` (`list`, `detect`).
- QA gate for the glossary: `glossary_missing` and `glossary_incomplete` errors for decks and
  reports, a `glossary_position` warning, `--no-glossary` flag; `qa_<theme>.json` has a `glossary`
  section (metrics shown, listed, missing, slide numbers).
- Agent integration: `tools/agent_tools.py` (six high-level tools with JSON Schemas for function
  calling, MCP-style schemas, CLI dispatcher) and `tools/mcp_server.py` (dependency-free stdio
  Model Context Protocol server).
- Tests: `test_glossary.py`, `test_agent_tools.py`.
- Repository files: `CITATION.cff`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue and pull request
  templates, `docs/` gallery (contact sheets), `docs/social_preview.png` (1280×640) and
  `docs/make_assets.py` that rebuilds them, `docs/github_settings.md` (About text, topics).

### Changed
- README: badges, gallery, "Quickstart in 60 seconds", agent integration section.
- Contact sheets are saved as palette PNGs (about a third of the size); examples keep contact
  sheets only, without page PNGs and PDFs.
- All examples rebuilt; QA 0 errors and 0 warnings in every example.
- Pattern slide counts exclude the glossary slides.

## [1.0.0] — 2026-10-20 — PitchComet

First release under the name **PitchComet**. Earlier history (below) belongs to the predecessor
skill and is kept for reference.

### Added
- **Autonomous data mode** (`tools/auto_pitch.py`): a short product description is enough. Pipeline:
  profile → market definition, segments, ICP → research plan and web-research loop → evidence
  ledger → computed TAM/SAM/SOM (top-down, bottom-up, value-based; triangulated), CAGR from drivers
  with scenarios, value-based price, unit economics from benchmark ranges, customer ROI/payback/TCO,
  5-year financial model, valuation (comparables + DCF), NPV/IRR/MOIC, Rule of 40, team plan scaled
  to the market, risks, deck + report + QA. Never stops at missing data: unknown figures become
  labelled estimates (method, formula, range, confidence, inputs); only items that cannot be
  estimated go to a short "to confirm" list. Offline runs complete and are watermarked.
- New tools with JSON Schemas in `tools/tools.json`: `product_profiler.py`, `market_definer.py`,
  `research_ledger.py`, `estimator.py`, `auto_pitch.py`, `pitch_story.py`.
- `config/market_taxonomy.json` (categories, classifications ↔ ISIC) and `config/benchmarks.json`
  (labelled rules of thumb).
- **Pitch patterns** (`patterns/`): large investor, small investor, corporate, SMB, government;
  `--pattern` flag and auto-selection from the audience; per-pattern scoring weights, slide order,
  mandatory metrics, CTA, red-team questions; playbooks per pattern.
- Customer metrics in `metrics_calc.py`: `customer_roi`, `customer_tco`, `smb_monthly_value`.
- **Themes** `comet`, `editorial`, `corporate`, `warm` (with CJK fonts), title and cover styles,
  `--theme` flag (repeatable); a test builds and checks every theme.
- `prompts/<locale>/research_loop.md` in six locales.
- Example `examples/autonomous_shiftlyra/` (fictional product, real linked market data): five
  Russian patterns, one English, renders of all seven themes.
- Tests `tools/tests/test_autonomous.py`.

### Changed
- `qa_check.py` **fails** (errors) when market sizing, CAGR or unit economics are missing, when a
  customer pattern lacks ROI/payback, or when gap placeholders such as "no data" / "нет данных" /
  "暂无数据" appear; `--pattern` checks mandatory terms; `--no-completeness` for non-pitch documents.
- Intake and research prompts: unknown figures are estimated and listed "to confirm" instead of
  being left blank.
- Templates: gap placeholders replaced by labelled assumptions.
- Big numbers on slides stay on one line (font fitted to the column).
- Number-consistency check no longer reads ranges such as "45%–82%" as negative numbers.

## Pre-rename history (predecessor skill)

### 0.2.0 — 2026-10-20


#### Added
- Locales `ru`, `en`, `zh`, `vi`, `id`, `ms` with `--locale` on every tool: number, currency and date
  formats (e.g. `3,0 млрд ₽`, `$3.0B`, `30.0亿元`, `3,0 nghìn tỷ ₫`, `Rp3,0 triliun`, `RM3.0 bilion`),
  section titles, chart labels, captions, fonts and citation styles.
- Citation engine (`tools/citations.py`): GOST R 7.0.5-2008, APA 7, Chicago author-date,
  GB/T 7714-2015; footnote, numeric and author-date modes in reports.
- Chinese typography: East Asian font slots in pptx/docx (Microsoft YaHei / SimSun / SimHei with
  Noto CJK fallback), 2-character first-line indent, CJK-aware text fitting and line breaking, QA check
  for missing CJK fonts, CJK font aliases for rendering.
- Market profiles `ru`, `en`, `zh`, `vn`, `id`, `my` in `config/scoring_model.json` (weight multipliers,
  regulation & sovereignty definitions and anchors, market-specific red flags) and guides in
  `markets/`.
- Banned/hype phrase lists per locale with "allowed only with a source" terms.
- Prompts and templates per locale; examples "Velordoc" in six locales with contact sheets.
- Scoring documentation in English, Russian and Chinese (generated).
- `research/presentation_techniques.md` — generic presentation techniques.
- `tools/ooxml_clean.py`: strips unrelated script fonts and East Asian theme languages inherited
  from library default templates.
- GitHub files: MIT licence, CI workflow, contributing guide, `pyproject.toml`.

#### Changed
- The `en` market profile covers the United States only (state privacy laws, NIST AI RMF, SOC 2,
  FedRAMP, EAR).
- English is the primary documentation language.
- Example tests use neutral illustrative numbers.

### 0.1.0

- Initial skill: market sizing, financial model, potential scoring, docx/pptx builders, QA, renders.
