# PitchComet

[![version](https://img.shields.io/badge/version-0.1b0-0B1530)](CHANGELOG.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-3776AB)](pyproject.toml)
[![tests](https://img.shields.io/badge/tests-unittest-brightgreen)](tools/tests)
[![locales](https://img.shields.io/badge/locales-ru%20%C2%B7%20en%20%C2%B7%20zh%20%C2%B7%20vi%20%C2%B7%20id%20%C2%B7%20ms-5CC8FF)](#locales)
[![MCP](https://img.shields.io/badge/MCP-stdio%20server-8A9BC9)](#agent-integration)

![PitchComet](docs/social_preview.png)

An agent skill and a Python toolkit that turn **a short description of an IT product** into a
**computed pitch deck (.pptx)** and a **strategy report (.docx)** — with market sizing, growth,
pricing, unit economics, financial model and valuation the tools work out themselves when the user
has no data. Native editable charts, one fact base for both documents, a strict QA gate, six locales.

* **Autonomous data mode.** Product profile → market, segments and ICP → web research plan →
  evidence ledger → computed TAM/SAM/SOM (top-down, bottom-up, value-based + triangulation), CAGR,
  scenarios, value-based price, unit economics (CAC, LTV, payback from benchmark ranges), customer
  ROI/TCO, 5-year financial model, NPV/IRR/MOIC, Rule of 40, valuation by comparables.
* **Never fabricated.** Every number is either *sourced* (link, year, access date) or a *labelled
  estimate* (formula, inputs, low–base–high range, confidence). Only a short "to confirm with the
  founders" list remains — it never blocks the deck.
* **QA fails** a pitch without market sizing, CAGR or unit economics, and any "no data / TBD"
  placeholder in any of the six languages.
* **Five pitch patterns** — large investor, small investor, corporate, SMB, government — change slide
  order, length, mandatory metrics, scoring weights, charts, tone and call to action.
* **Seven themes** — `light`, `dark`, `academic_light`, `comet`, `editorial`, `corporate`, `warm`
  (all with CJK font settings).
* Data-driven mode is still there: structured inputs → `run_pipeline.py`.
* **"What the numbers mean".** Every deck opens with a plain-language glossary of exactly the
  metrics it shows (and the report has the same section); QA fails if a metric is not explained.
* **Agent-ready.** `SKILL.md` for agents that load skills, JSON Schemas for function calling and a
  dependency-free MCP server.
* Locales `ru`, `en`, `zh`, `vi`, `id`, `ms`; market profiles Russia, United States, China, Vietnam,
  Indonesia, Malaysia.

Other languages: [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Quickstart in 60 seconds

```bash
git clone <this repository> pitchcomet && cd pitchcomet
pip install -r requirements.txt
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_en.json \
       --pattern large_investor --out demo < /dev/null
ls examples/autonomous_shiftlyra/demo   # deck.pptx  report.docx  qa_comet.json  auto_summary.json ...
```

That writes a 20-slide investor deck (`examples/autonomous_shiftlyra/demo/`) and a report for a fictional product from the example brief
and its research ledger, in a few seconds, with QA. Add `--render` for PNG previews (LibreOffice
and poppler-utils). To pitch your own product, write a four-line brief (below) and start with
`--plan-only`.

## Gallery

Full English investor deck (comet theme), from the brief above:

![Deck](docs/deck_large_investor_en.png)

| Five pitch patterns (first slides) | Seven themes |
|---|---|
| ![Patterns](docs/patterns.png) | ![Themes](docs/themes.png) |

The glossary slide in six languages, and the report:

| Glossary in ru · en · zh · vi · id · ms | Report (.docx) |
|---|---|
| ![Glossary](docs/glossary_locales.png) | ![Report](docs/report_en.png) |

All images are contact sheets of real outputs in `examples/`; `python docs/make_assets.py` rebuilds them.


## Step by step — autonomous

```bash
pip install -r requirements.txt
# 1. research plan: profile, market definition, ledger keys, web queries
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_en.json --plan-only < /dev/null
# 2. the agent researches (prompts/<locale>/research_loop.md) and fills the ledger
python tools/research_ledger.py validate --input examples/autonomous_shiftlyra/ledger_en.json < /dev/null
# 3. compute + build + QA (+ PNG previews)
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_en.json \
       --pattern large_investor --theme comet --render < /dev/null
```

A brief is just a name, a description, a market and an audience:

```json
{"name": "My product", "text": "One paragraph about what it does and for whom",
 "market": "en", "locale": "en", "audience": "seed funds", "ledger": "ledger.json"}
```

Without a ledger the run still completes with labelled offline assumptions and an "offline draft"
watermark. Output: `profile.json`, `market_definition.json`, `research_plan.json`,
`ledger_full.json`, `facts.json`, `deck*.pptx`, `report.docx`, `qa_<theme>.json`,
`auto_summary.json` (pattern, QA, key numbers, to-confirm list), `renders/`.

## Step by step — data-driven

```bash
python tools/run_pipeline.py --project examples/example_en/project.json --theme light --theme editorial < /dev/null
python tools/new_project.py --dir work/my_product --name "My product" --locale en
```

Previews need LibreOffice and poppler-utils; Chinese needs a CJK font (e.g. `fonts-noto-cjk`).

```bash
python -m unittest discover -s tools/tests -v < /dev/null
```

## Pitch patterns

| id | Audience | Theme | Slides | Must show |
|---|---|---|---|---|
| `large_investor` | growth / late-stage fund | comet | 15–20 | TAM, SAM, SOM, CAGR, LTV/CAC, Rule of 40, IRR, MOIC |
| `small_investor` | angel / pre-seed / seed (default) | warm | 10–14 | TAM, SOM, CAGR, LTV/CAC, MOIC |
| `corporate` | enterprise buyer / partner | corporate | 9–13 | customer ROI, TCO, payback |
| `smb` | small-business owners | warm | 6–9 | price per month, saving, payback |
| `government` | grant / public programme | corporate | 11–15 | SAM, CAGR, ROI, public effect |

`--pattern auto` picks a pattern from the brief's `audience`. Playbooks: [`patterns/`](patterns/README.md).

## Locales

| Locale | Money example | Dates | Citations (default) | Market guide |
|---|---|---|---|---|
| `ru` | `3,0 млрд ₽` | 20.10.2026 | GOST R 7.0.5-2008, footnotes | `markets/ru.md` |
| `en` | `$3.0B` | October 20, 2026 | APA 7 (Chicago available) | `markets/en.md` |
| `zh` | `30.0亿元` | 2026年10月20日 | GB/T 7714-2015, numeric | `markets/zh.md` |
| `vi` | `3,0 nghìn tỷ ₫` | ngày 20 tháng 10 năm 2026 | APA 7 | `markets/vn.md` |
| `id` | `Rp3,0 triliun` | 20 Oktober 2026 | APA 7 | `markets/id.md` |
| `ms` | `RM3.0 bilion` | 20 Oktober 2026 | APA 7 | `markets/my.md` |

Narrative text of the autonomous mode is written in Russian and English; other locales get English
narrative with locale formatting (add wording in `tools/pitch_story.py`).

## Agent integration

PitchComet is a folder an agent can use in three ways. Each wraps the same command-line tools.

**1. As a skill.** Agents that load skill folders read [`SKILL.md`](SKILL.md) (front matter with
`name` and `description`, then the recipe). Copy or link the folder into the agent's skills
directory.

**2. Function calling.** Six high-level tools with JSON Schemas:

```bash
python tools/agent_tools.py schemas                # [{name, description, parameters}]
python tools/agent_tools.py schemas --format mcp   # [{name, description, inputSchema}]
```

```json
{"name": "pitchcomet_build",
 "description": "Autonomous mode: brief + evidence ledger → computed TAM/SAM/SOM, CAGR, ... → deck.pptx + report.docx → QA.",
 "parameters": {"type": "object", "required": ["brief"],
   "properties": {"brief": {"type": "string"},
                  "pattern": {"enum": ["auto", "large_investor", "small_investor", "corporate", "smb", "government"]},
                  "themes": {"type": "array", "items": {"type": "string"}},
                  "render": {"type": "boolean"}}}}
```

Pass the list to any LLM API or agent framework that accepts JSON Schema tools, and route the
calls to one function:

```python
import sys; sys.path.insert(0, "tools")
from agent_tools import schemas, call_tool

tools = schemas()                       # give these to the model
result = call_tool("pitchcomet_build",  # when the model calls a tool
                   {"brief": "examples/autonomous_shiftlyra/brief_en.json", "pattern": "auto"})
print(result["ok"], result["json"]["qa"])
```

Tools: `pitchcomet_plan`, `pitchcomet_build`, `pitchcomet_pipeline`, `pitchcomet_qa`,
`pitchcomet_metric`, `pitchcomet_glossary`. Lower-level schemas for every module: `tools/tools.json`.

**3. MCP server.** `tools/mcp_server.py` speaks the Model Context Protocol over stdio (JSON-RPC 2.0,
no dependencies). Add it to any MCP client:

```json
{"mcpServers": {"pitchcomet": {"command": "python", "args": ["/path/to/pitchcomet/tools/mcp_server.py"]}}}
```

**CLI.** Everything is also a plain command (`auto_pitch.py`, `run_pipeline.py`, `qa_check.py`,
`metrics_calc.py`, `glossary.py` …), so shell-only agents and CI jobs need nothing else.

## Tools

| Tool | Purpose |
|---|---|
| `tools/auto_pitch.py` | autonomous mode: brief → plan → ledger + estimates → pattern → deck + report → QA |
| `tools/product_profiler.py` | infer category, buyer, unit, pricing, deployment, stage from a description |
| `tools/market_definer.py` | classification codes, segments, ICP, research plan, queries, official sources |
| `tools/research_ledger.py` | evidence ledger: validate, deduplicate, normalise currency/year, resolve conflicts |
| `tools/estimator.py` | labelled estimates: ranges, sizing methods, triangulation, CAGR, price, unit economics, comparables |
| `tools/pitch_story.py` | narrative for each pattern, speaker notes, deck ↔ report figure appendix |
| `tools/run_pipeline.py` | full pipeline: market → finance → scoring → facts → docx + pptx → QA → renders |
| `tools/market_sizing.py` · `tools/financial_model.py` · `tools/scoring.py` | sizing, P&L/NPV/IRR/MOIC, potential score |
| `tools/metrics_calc.py` | ~50 metrics incl. customer ROI, TCO, SMB monthly value |
| `tools/build_docx.py` · `tools/build_pptx.py` | builders with native charts and themes |
| `tools/qa_check.py` | QA incl. the completeness gate (`--pattern`, `--no-completeness`) and the glossary gate (`--no-glossary`) |
| `tools/glossary.py` | plain-language glossary: detects the metrics a deck or report shows; definitions in `config/glossary.json` |
| `tools/agent_tools.py` · `tools/mcp_server.py` | function-calling schemas and dispatcher; MCP stdio server |
| `tools/render_preview.py` · `tools/citations.py` · `tools/new_project.py` | previews, references, scaffolding |

Details: [`tools/README.md`](tools/README.md); schemas: `tools/tools.json`.

## Repository layout

```
pitchcomet/
├── SKILL.md                      # agent instructions
├── README.md · README.ru.md · README.zh-CN.md · ADAPTING.md · CHANGELOG.md
├── deck_structure.md · style_guide.md · metrics.md · scoring_model*.md
├── config/  scoring_model.json · banned_phrases.json · themes.json · benchmarks.json · market_taxonomy.json · glossary.json
├── patterns/  patterns.json + five playbooks
├── markets/  ru · en · zh · vn · id · my guides
├── prompts/{ru,en,zh,vi,id,ms}/  research loop, intake, research brief, storyline, slide writer, red team
├── templates/{ru,en,zh,vi,id,ms}/
├── examples/  example_{ru,en,zh,vi,id,ms}/ (data-driven) · autonomous_shiftlyra/ (autonomous)
├── tools/  Python tools + tools.json + agent_tools.py + mcp_server.py + tests/
├── docs/  gallery images, social_preview.png, make_assets.py, github_settings.md
└── LICENSE · CITATION.cff · SECURITY.md · CODE_OF_CONDUCT.md · CONTRIBUTING.md · pyproject.toml · .github/
```

## Principles

* Never invent real-world facts; every real figure needs a link; every estimate shows its formula.
* Benchmarks in `config/benchmarks.json` are rules of thumb, labelled as such.
* Numbers come from tools, not from prose. One message per slide; titles state conclusions.
* Examples are fictional products and say so (market data in the autonomous example is real and linked).

## Acknowledgements

PitchComet was developed with personal hands-on experience together with AI
assistants — in particular **Grok** and **GigaChat** — which were actively used for drafting,
reviewing and refining the skill, its prompts, tools and documentation.

## Licence

MIT — see [LICENSE](LICENSE).

## Disclaimer

PitchComet produces machine-generated drafts. The output is **not legal advice and not an
investment recommendation**. Every figure must be verified before use, and the user bears full
responsibility for how the documents are used and for the accuracy of the numbers.
