# PitchComet

[![version](https://img.shields.io/badge/version-0.1b0-0B1530)](CHANGELOG.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-3776AB)](pyproject.toml)
[![tests](https://img.shields.io/badge/tests-unittest-brightgreen)](tools/tests)
[![MCP](https://img.shields.io/badge/MCP-stdio%20server-8A9BC9)](README.md#agent-integration)

![PitchComet](docs/social_preview.png)

面向 AI 智能体的技能与 Python 工具集：只需一段**简短的 IT 产品描述**，即可生成**经过计算的路演演示文稿（.pptx）**
和**战略分析报告（.docx）**。用户没有数据时，市场规模、增长、定价、单位经济、财务模型和估值都由工具自行计算。
原生可编辑图表、两份文档共用一套事实库、严格的质量检查、六种语言区域。

* **自主数据模式。** 产品画像 → 市场、细分与理想客户画像 → 网络调研计划 → 证据台账 → 计算 TAM/SAM/SOM
  （自上而下、自下而上、价值法 + 三角校验）、CAGR、情景、价值定价、单位经济（CAC、LTV、基于基准区间的回本期）、
  客户 ROI/TCO、5 年财务模型、NPV/IRR/MOIC、Rule of 40、可比公司估值。
* **绝不编造。** 每个数字要么是*有来源的事实*（链接、年份、访问日期），要么是*有标注的估计值*（公式、输入、
  低–基准–高区间、置信度）。最后只剩一份简短的“待创始人确认”清单，且从不阻塞演示文稿。
* **QA 判为不通过**：缺少市场规模、CAGR 或单位经济的路演，以及六种语言中任何“暂无数据 / 待定”之类的占位符。
* **五种路演模式**——大型投资人、小型投资人、企业客户、中小企业、政府：调整幻灯片顺序与数量、必备指标、
  评分权重、图表、语气和行动号召。
* **七套主题**——`light`、`dark`、`academic_light`、`comet`、`editorial`、`corporate`、`warm`（均含 CJK 字体设置）。
* 仍保留数据驱动模式：结构化输入 → `run_pipeline.py`。
* 语言区域 `ru`、`en`、`zh`、`vi`、`id`、`ms`；市场配置：俄罗斯、美国、中国、越南、印度尼西亚、马来西亚。
* **“这些数字是什么意思”。** 每份演示文稿在标题页后都有一页通俗易懂的术语表，只列出文稿中实际出现的指标；
  报告中也有同样的章节。若有指标未解释，QA 判为不通过。
* **面向智能体。** 提供 `SKILL.md`、函数调用用的 JSON Schema，以及无依赖的 MCP 服务器。

其他语言：[English](README.md) · [Русский](README.ru.md)


## 60 秒快速上手

```bash
git clone <仓库地址> pitchcomet && cd pitchcomet
pip install -r requirements.txt
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_en.json \
       --pattern large_investor --out demo < /dev/null
ls examples/autonomous_shiftlyra/demo   # deck.pptx  report.docx  qa_comet.json  auto_summary.json ...
```

几秒钟内即可根据示例简介和证据台账（虚构产品）生成投资人演示文稿和报告，并完成 QA。加上 `--render`
可生成 PNG 预览（需要 LibreOffice 和 poppler-utils）。为自己的产品写一份四行简介，先运行 `--plan-only`。

## 示例图

![演示文稿](docs/deck_large_investor_en.png)

| 五种路演模式 | 七套主题 |
|---|---|
| ![模式](docs/patterns.png) | ![主题](docs/themes.png) |

| 六种语言的术语表 | 报告（.docx） |
|---|---|
| ![术语表](docs/glossary_locales.png) | ![报告](docs/report_en.png) |

以上均为 `examples/` 中真实输出的缩略图；用 `python docs/make_assets.py` 重新生成。

## 分步说明——自主模式

```bash
pip install -r requirements.txt
# 1. 调研计划：画像、市场定义、台账键、搜索查询
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_en.json --plan-only < /dev/null
# 2. 智能体按 prompts/zh/research_loop.md 调研并填写台账
python tools/research_ledger.py validate --input examples/autonomous_shiftlyra/ledger_en.json < /dev/null
# 3. 计算 + 生成 + QA（+ PNG 预览）
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_en.json \
       --pattern large_investor --theme comet --render < /dev/null
```

简报只需名称、描述、市场和受众：

```json
{"name": "我的产品", "text": "一段话说明产品做什么、为谁服务",
 "market": "zh", "locale": "zh", "audience": "天使投资人", "ledger": "ledger.json"}
```

没有台账时也能跑完：使用有标注的离线假设，并加“离线草稿”水印。输出：`profile.json`、`market_definition.json`、
`research_plan.json`、`ledger_full.json`、`facts.json`、`deck*.pptx`、`report.docx`、`qa_<主题>.json`、
`auto_summary.json`（模式、QA、关键数字、待确认清单）、`renders/`。

## 分步说明——数据驱动模式

```bash
python tools/run_pipeline.py --project examples/example_zh/project.json --theme light --theme editorial < /dev/null
python tools/new_project.py --dir work/my_product --name "我的产品" --locale zh
```

预览需要 LibreOffice 和 poppler-utils；中文需要 CJK 字体（如 `fonts-noto-cjk`）。

```bash
python -m unittest discover -s tools/tests -v < /dev/null
```

## 路演模式

| id | 受众 | 主题 | 幻灯片 | 必须呈现 |
|---|---|---|---|---|
| `large_investor` | 成长期 / 后期基金 | comet | 15–20 | TAM、SAM、SOM、CAGR、LTV/CAC、Rule of 40、IRR、MOIC |
| `small_investor` | 天使 / 种子前 / 种子轮（默认） | warm | 10–14 | TAM、SOM、CAGR、LTV/CAC、MOIC |
| `corporate` | 企业客户 / 合作伙伴 | corporate | 9–13 | 客户 ROI、TCO、回本期 |
| `smb` | 中小企业主 | warm | 6–9 | 月价格、节省、回本期 |
| `government` | 补助 / 公共项目 | corporate | 11–15 | SAM、CAGR、ROI、社会效益 |

`--pattern auto` 根据简报的 `audience` 自动选择。各模式说明：[`patterns/`](patterns/README.md)。

## 语言区域

| 区域 | 金额示例 | 日期 | 默认引文格式 | 市场指南 |
|---|---|---|---|---|
| `ru` | `3,0 млрд ₽` | 20.10.2026 | GOST R 7.0.5-2008，脚注 | `markets/ru.md` |
| `en` | `$3.0B` | October 20, 2026 | APA 7（可选 Chicago） | `markets/en.md` |
| `zh` | `30.0亿元` | 2026年10月20日 | GB/T 7714-2015，顺序编码 | `markets/zh.md` |
| `vi` | `3,0 nghìn tỷ ₫` | ngày 20 tháng 10 năm 2026 | APA 7 | `markets/vn.md` |
| `id` | `Rp3,0 triliun` | 20 Oktober 2026 | APA 7 | `markets/id.md` |
| `ms` | `RM3.0 bilion` | 20 Oktober 2026 | APA 7 | `markets/my.md` |

自主模式的叙述文字目前有俄语和英语版本；其他区域使用英语叙述并采用本区域的数字格式（可在
`tools/pitch_story.py` 中补充措辞）。

## 接入智能体

* **作为技能。** 支持技能文件夹的智能体读取 [`SKILL.md`](SKILL.md)。
* **函数调用。** `python tools/agent_tools.py schemas` 输出六个带 JSON Schema 的工具（`--format mcp` 输出 MCP 格式）；
  代码中使用 `from agent_tools import schemas, call_tool`。
* **MCP 服务器。** `python tools/mcp_server.py`，基于 stdio，无依赖：
  `{"mcpServers": {"pitchcomet": {"command": "python", "args": ["/path/to/pitchcomet/tools/mcp_server.py"]}}}`
* **命令行。** 所有工具都可以直接作为命令运行。

详细示例见 [README.md#agent-integration](README.md#agent-integration)。

## 工具

| 工具 | 用途 |
|---|---|
| `tools/auto_pitch.py` | 自主模式：简报 → 计划 → 台账与估计 → 模式 → 演示文稿与报告 → QA |
| `tools/product_profiler.py` | 从描述推断品类、买方、计价单位、定价、部署方式、阶段 |
| `tools/market_definer.py` | 行业分类代码、细分、理想客户画像、调研计划、查询、官方来源 |
| `tools/research_ledger.py` | 证据台账：校验、去重、币种与价格年份归一、冲突处理 |
| `tools/estimator.py` | 有标注的估计：区间、市场规模方法、三角校验、CAGR、定价、单位经济、可比公司 |
| `tools/pitch_story.py` | 各模式的叙述、演讲者备注、演示文稿与报告数字对照附录 |
| `tools/run_pipeline.py` | 完整流水线：市场 → 财务 → 评分 → 事实 → docx + pptx → QA → 预览 |
| `tools/market_sizing.py` · `tools/financial_model.py` · `tools/scoring.py` | 市场规模、P&L/NPV/IRR/MOIC、潜力评分 |
| `tools/metrics_calc.py` | 约 50 项指标，含客户 ROI、TCO、中小企业月度价值 |
| `tools/build_docx.py` · `tools/build_pptx.py` | 带原生图表和主题的生成器 |
| `tools/qa_check.py` | QA，含完整性检查（`--pattern`、`--no-completeness`） |
| `tools/glossary.py` | 通俗术语表：识别演示文稿或报告中出现的指标；定义见 `config/glossary.json` |
| `tools/agent_tools.py` · `tools/mcp_server.py` | 函数调用 Schema 与调度器；stdio MCP 服务器 |
| `tools/render_preview.py` · `tools/citations.py` · `tools/new_project.py` | 预览、参考文献、项目脚手架 |

详见 [`tools/README.md`](tools/README.md)；接口定义：`tools/tools.json`。

## 仓库结构

```
pitchcomet/
├── SKILL.md                      # 智能体说明
├── README.md · README.ru.md · README.zh-CN.md · ADAPTING.md · CHANGELOG.md
├── deck_structure.md · style_guide.md · metrics.md · scoring_model*.md
├── config/  scoring_model.json · banned_phrases.json · themes.json · benchmarks.json · market_taxonomy.json · glossary.json
├── patterns/  patterns.json + 五份模式说明
├── markets/  ru · en · zh · vn · id · my 指南
├── prompts/{ru,en,zh,vi,id,ms}/  调研循环、访谈问卷、调研任务书、故事线、幻灯片撰写、红队审阅
├── templates/{ru,en,zh,vi,id,ms}/
├── examples/  example_{ru,en,zh,vi,id,ms}/（数据驱动） · autonomous_shiftlyra/（自主模式）
├── tools/  工具 + tools.json + tests/
└── LICENSE · CONTRIBUTING.md · pyproject.toml · requirements.txt · .github/workflows/tests.yml
```

## 原则

* 不编造真实世界的事实；每个真实数字都要有链接；每个估计值都要给出公式。
* `config/benchmarks.json` 中的基准是经验法则，并如此标注。
* 数字来自工具而非文字。每页一个观点；标题即结论。
* 示例产品均为虚构并注明（自主示例中的市场数据是真实的，附链接）。

## 致谢

PitchComet 结合个人实践经验与 AI 助手共同开发，特别是 **Grok** 和 **GigaChat**，
它们在技能、提示词、工具与文档的起草、审阅和完善过程中得到了积极使用。

## 许可证

MIT——见 [LICENSE](LICENSE)。

## 免责声明

PitchComet 自动生成草稿。输出内容**不构成法律意见，也不构成投资建议**。使用前必须核实所有数字；
用户对文档的使用方式及数字的准确性承担全部责任。
