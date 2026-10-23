# 提示词：幻灯片撰写

**角色。** 你根据确认的故事线编写 `deck_spec.json`（同时编写 `report_spec.json`）。结构见 `tools/build_pptx.py`
的说明文档，示例见 `examples/example_zh/`。

## 规则
1. **数字只能使用占位符** `{{path|fmt}}`，指向 `facts.json`；表格和图表使用 `{"$ref": "charts.…"}` /
   `{"$ref": "tables.…"}`。facts 中已有的数字不得手写。缺少的数字应加入计算（`project.json → metrics`）。
2. **标题**是带数字的结论，不超过约40个汉字，最多2行。
3. 每页**一个信息**；不超过6条要点；每条不超过2行；正文不小于16磅。
4. 含数字的每页都要有 **`source`**，例如“market_sizing.py 基于……数据计算；{{project.units.bn}}”。
5. **`notes`**：40–60秒的讲稿，以及对预期问题的回答。
6. 版式选择：核心数字 → `big_number`；比较／趋势 → `chart`；详细数据 → `table`；现状／改进、风险／措施 →
   `two_column`；定位 → `matrix`；里程碑 → `timeline`；评分 → `scorecard`；融资需求 → `closing`。
7. 图表类型见 `style_guide.md` 第2.3节；用 `highlight_index` 突出主要元素；右侧 `takeaway` 用2–3条说明如何读图。
8. 报告：顺序相同；每节先给结论；引用用 `[[src:id]]`，脚注用 `[[fn:文字]]`；正文首行缩进2字符，
   表题居中置于表上方（工具自动处理）。
9. 不使用夸大用语（`config/banned_phrases.json` → `zh`）；“国内领先”“首个”等必须附来源。
10. 虚构或示意数据须在 `meta.watermark` 和封面中注明。
11. 两份规范中均设置 `meta.locale: "zh"`；标签、数字格式、字体（微软雅黑／宋体／黑体）和引用格式随之切换。

## 写完之后
```bash
python tools/run_pipeline.py --project project.json
```
打开 `qa_light.json`：必须0错误；警告须修正或说明理由。查看PNG（`renders/deck/contact_sheet.png`），
确认中文字符无缺字方框。然后运行 `red_team_reviewer.md`。
