# PitchComet

[![version](https://img.shields.io/badge/version-0.1b0-0B1530)](CHANGELOG.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-3776AB)](pyproject.toml)
[![tests](https://img.shields.io/badge/tests-unittest-brightgreen)](tools/tests)
[![locales](https://img.shields.io/badge/locales-ru%20%C2%B7%20en%20%C2%B7%20zh%20%C2%B7%20vi%20%C2%B7%20id%20%C2%B7%20ms-5CC8FF)](#locales)
[![MCP](https://img.shields.io/badge/MCP-stdio%20server-8A9BC9)](#agent-integration)

![PitchComet](docs/social_preview.png)

PitchComet is a tool and a set of instructions. It takes a short description of a software product
and turns it into a finished slide deck (.pptx) and an analytical report (.docx). The tool works out
the market size, growth, price, economics of a single customer, financial model and valuation on its
own, even when the user has no data. The charts are embedded into the documents and can be edited.
Both documents take their numbers from a single source. The program supports six languages.

* **Mode without source data.** First the tool understands what the product is and who the buyer
  is. Then it builds a web search plan and a list of facts with links, and sizes the market three
  ways. After that come growth, scenarios, price, the economics of one customer, the buyer's
  benefit, a five-year financial model, returns and valuation.
* **Quality check.** The tool does not let a deck through without market size, growth and unit
  economics. It also does not let through any blank placeholder instead of data in any of the six
  languages.
* **Five deck patterns.** For a large investor, a small investor, a large corporate buyer, a small
  business and the government. Each pattern changes the slide order, length, set of required
  numbers, score, charts, tone and the final call to action.
* **Seven visual themes.** Light, dark, academic, comet, editorial, corporate and warm. All of them
  support East Asian fonts.
* **A mode with ready data exists too.** If the user already has their own figures, they fill in
  the input templates and run the main pipeline.
* **What the numbers mean.** Every deck starts with a slide that explains in plain words only the
  metrics it shows. The report has the same section. The quality check does not let a document
  through if any metric is left unexplained.
* **Ready for agents.** The instructions for assistant programs live in a separate file. There are
  function descriptions for calling and a simple server with no external dependencies.
* **Languages.** Russian, English, Chinese, Vietnamese, Indonesian and Malay. Market profiles for
  Russia, the United States, China, Vietnam, Indonesia and Malaysia.

Other languages: [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Gallery

A full English investor deck in the comet theme, built from the description above.

![Deck](docs/deck_large_investor_en.png)

The glossary slide in six languages and the report itself.

| Glossary in six languages | Report (.docx) |
|---|---|
| ![Glossary](docs/glossary_locales.png) | ![Report](docs/report_en.png) |

All the images are copies of real results from the examples folder. The command
`python docs/make_assets.py` creates them again.

## Deck patterns

| Name | For whom | Theme | Slides | Required numbers |
|---|---|---|---|---|
| `large_investor` | growth fund, late stages | comet | 15–20 | TAM, SAM, SOM, CAGR, LTV/CAC, Rule of 40, IRR, MOIC |
| `small_investor` | angel, pre-seed, seed | warm | 10–14 | TAM, SOM, CAGR, LTV/CAC, MOIC |
| `corporate` | large buyer or partner | corporate | 9–13 | customer benefit, total cost of ownership, payback |
| `smb` | small-business owners | warm | 6–9 | price per month, saving, payback |
| `government` | grant, public programme | corporate | 11–15 | SAM, CAGR, benefit, public effect |

The command `--pattern auto` picks a pattern from the audience description. Details are in the
[`patterns/`](patterns/README.md) folder.

## Languages

| Language | Money example | Dates | Source citations | Market guide |
|---|---|---|---|---|
| `ru` | `3,0 млрд ₽` | 20.10.2026 | GOST R 7.0.5 2008, footnotes | `markets/ru.md` |
| `en` | `$3.0B` | October 20, 2026 | APA 7, Chicago available | `markets/en.md` |
| `zh` | `30.0亿元` | 2026年10月20日 | GB/T 7714 2015, numeric | `markets/zh.md` |
| `vi` | `3,0 nghìn tỷ ₫` | ngày 20 tháng 10 năm 2026 | APA 7 | `markets/vn.md` |
| `id` | `Rp3,0 triliun` | 20 Oktober 2026 | APA 7 | `markets/id.md` |
| `ms` | `RM3.0 bilion` | 20 Oktober 2026 | APA 7 | `markets/my.md` |

The text in the mode without source data is written in Russian and English. The other languages get
English text with the correct number and date formats for their language.

## Connecting to agents

PitchComet is a folder that an assistant program can use in three ways. Each way runs the same
command-line programs.

**1. As a skill.** Assistant programs that can read skill folders read the [`SKILL.md`](SKILL.md)
file. Copy the folder into the skills directory of your assistant.

**2. Function calling.** There are six functions with descriptions in the JSON Schema format.

```bash
python tools/agent_tools.py schemas                # a list of name, description and parameters
python tools/agent_tools.py schemas --format mcp   # the same list in the MCP format
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

Pass this list to any language model that can call functions, and route the calls into one function.

```python
import sys; sys.path.insert(0, "tools")
from agent_tools import schemas, call_tool

tools = schemas()                       # give this to the model
result = call_tool("pitchcomet_build",  # when the model calls a function
                   {"brief": "examples/autonomous_shiftlyra/brief_en.json", "pattern": "auto"})
print(result["ok"], result["json"]["qa"])
```

Functions to call: `pitchcomet_plan`, `pitchcomet_build`, `pitchcomet_pipeline`, `pitchcomet_qa`,
`pitchcomet_metric`, `pitchcomet_glossary`. Detailed descriptions for each module live in the file
`tools/tools.json`.

**3. MCP server.** The program `tools/mcp_server.py` speaks the Model Context Protocol over standard
input and output. There are no dependencies. Add it to any MCP client.

```json
{"mcpServers": {"pitchcomet": {"command": "python", "args": ["/path/to/pitchcomet/tools/mcp_server.py"]}}}
```

**Command line.** Everything also works as plain commands. So agents that can only run commands need
nothing else.

## Tools

| Tool | What it does |
|---|---|
| `tools/auto_pitch.py` | the mode without data, from a description to a deck with a quality check |
| `tools/product_profiler.py` | understands category, buyer, unit, price and stage from a description |
| `tools/market_definer.py` | classification codes, segments, target customer, search plan and sources |
| `tools/research_ledger.py` | a list of facts with links, checking and resolving disagreements |
| `tools/estimator.py` | labelled estimates, ranges, market size, growth, price and unit economics |
| `tools/pitch_story.py` | text for each pattern, speaker notes and a figure appendix |
| `tools/run_pipeline.py` | the full pipeline from market and finance to documents and quality check |
| `tools/market_sizing.py` `tools/financial_model.py` `tools/scoring.py` | market size, money and returns, score |
| `tools/metrics_calc.py` | about fifty metrics including customer benefit and cost of ownership |
| `tools/build_docx.py` `tools/build_pptx.py` | document builders with embedded charts and themes |
| `tools/qa_check.py` | quality check including the required glossary and required numbers |
| `tools/glossary.py` | a plain-words glossary, finds the metrics shown in a document |
| `tools/agent_tools.py` `tools/mcp_server.py` | function descriptions and the MCP server |
| `tools/render_preview.py` `tools/citations.py` `tools/new_project.py` | page previews, citations, project creation |

Details are in [`tools/README.md`](tools/README.md). Schema descriptions are in `tools/tools.json`.

## Folder structure

```
pitchcomet/
├── SKILL.md                      # instructions for the agent
├── README.md · README.ru.md · README.zh-CN.md · ADAPTING.md · CHANGELOG.md
├── deck_structure.md · style_guide.md · metrics.md · scoring_model*.md
├── config/  scoring_model.json · banned_phrases.json · themes.json · benchmarks.json · market_taxonomy.json · glossary.json
├── patterns/  patterns.json and five guides
├── markets/  guides for the ru en zh vn id my markets
├── prompts/{ru,en,zh,vi,id,ms}/  search, questions, story, slide text, review
├── templates/{ru,en,zh,vi,id,ms}/
├── examples/  example_{ru,en,zh,vi,id,ms} and autonomous_shiftlyra
├── tools/  programs and tests
├── docs/  gallery images
└── LICENSE · CITATION.cff · SECURITY.md · CODE_OF_CONDUCT.md · CONTRIBUTING.md · pyproject.toml · .github/
```

## Principles

* Real facts need a link. Every estimate shows its formula.
* The values in `config/benchmarks.json` are approximate rules, and they are labelled as such.
* Numbers come from tools, not from prose. One message per slide, and the title is the conclusion.
* The examples are fictional products, and they say so. The market data in the example without
  source data is real and linked.

## PitchComet was built on personal hands-on experience together with AI agents, including GigaChat and xAI tools

## Licence

MIT, details are in the [LICENSE](LICENSE) file.

## Disclaimer

PitchComet produces machine-generated drafts. The output is **not legal advice and not an
investment recommendation**. Every figure must be verified before use, and the user bears full
responsibility for how the documents are used and for the accuracy of the numbers.