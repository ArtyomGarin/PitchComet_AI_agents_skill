# Style guide: text, visuals, checklist

## 1. Text

### 1.1. Action titles
* A full sentence: **claim + number + implication**. "SAM grows to $1.1B by 2030 at 18% a year",
  not "Market dynamics".
* 8–18 words (≤ 30–40 characters for Chinese), at most 2 lines. QA: `label_title` (< 4 words),
  `long_title` (> 22 words; CJK measured in character units).
* Horizontal-logic test: read only the titles in order — is it a coherent story?
  (`prompts/<locale>/storyline_builder.md`).
* The title claims what the slide body proves, no more. If the chart shows 18%, the title cannot
  say "explosive growth".

### 1.2. Numbers
* Every number has a **unit, period and source**: "$0.7M revenue in 2026 (plan)".
* Round to what is meaningful: $3.0B, not $3,012,345,678; shares to whole percent when the
  difference is below the estimate's error.
* Changes in shares in **percentage points**: "accuracy +12 pp", not "+12%".
* Forecasts as **ranges or scenarios**; a single point only for facts.
* Multiples ("5× faster") only with a known baseline; state it.
* Normalise large numbers with a familiar denominator (share of budget, per employee, per
  document).
* The same number is identical everywhere: deck and report take it from `facts.json` via
  `{{path|fmt}}`. Never type numbers by hand.
* Locale formats (all produced by `fmt_utils.py`, non-breaking spaces where customary):

| Locale | Money | Percent | Points | Multiple |
|---|---|---|---|---|
| ru | `3,0 млрд ₽`, `400 млн ₽` | `18%` | `13 п.п.` | `1,6x` |
| en | `$3.0B`, `$400M` | `18%` | `13 pp` | `1.6x` |
| zh | `30亿元`, `4,000万元` | `18%` | `13个百分点` | `1.6倍` |
| vi | `3,0 nghìn tỷ ₫`, `400 tỷ ₫` | `18%` | `13 điểm %` | `1,6 lần` |
| id | `Rp3,0 triliun`, `Rp400 miliar` | `18%` | `13 poin persentase` | `1,6x` |
| ms | `RM3.0 bilion`, `RM400 juta` | `18%` | `13 mata peratusan` | `1.6x` |

### 1.3. Vocabulary
* No superlatives or advertising words — per-locale lists in `config/banned_phrases.json` (QA
  warning). Use a measured difference instead: "the only one of 5 compared products that works
  offline".
* "Leader", "largest", "first" only with a source on the same slide (`allow_if_sourced`).
* Active voice, short sentences (≤ 20 words in the report, ≤ 12 words per slide bullet).
* Call an assumption an assumption: "team estimate", "model assumption".
* Risks without euphemisms, each paired with a mitigation.
* Market-specific source rules (e.g. for Russia-facing documents) are in `SKILL.md` → Hard rules.

### 1.4. Bullets
* ≤ 6 bullets, ≤ 2 levels; 3–4 is better. Detail goes to notes and the report.
* Parallel grammar: all bullets start the same way (noun or verb).
* A bullet is at most 2 lines.

### 1.5. Report
* Each section starts with its conclusion (first paragraph = answer), then evidence.
* One idea per paragraph, 3–6 sentences.
* Method and assumptions in separate subsections / appendix; findings in the main text.
* The executive summary stands alone: 1 page, key numbers, recommendation, conditions.

## 2. Visuals

### 2.1. Grid and typography (built into `build_pptx.py`)
* 16:9 (13.333 × 7.5 in); 0.6 in margins; title at the top, body 1.75–6.6 in, source line at the
  bottom (6.88 in).
* Fonts by locale (overridable in `meta` / `config/themes.json`): Latin locales Arial (deck),
  Times New Roman (report); zh Microsoft YaHei (deck), SimSun body / SimHei headings (report),
  with Noto Sans CJK SC as the rendering fallback. East Asian font slots (`a:ea`, `w:eastAsia`)
  are always set for zh so CJK text never falls back to a Latin font.
* Sizes: title 26–28 pt; body 16–18 pt; captions 12–14 pt; source 10 pt. **Never below 10 pt**
  (QA `small_font`).
* Themes: `light` (white, accent #0F766E), `dark` (#0E1116, accent #2DD4BF), `academic_light`
  (accent #7F1D1D, Times New Roman titles). Colours in `config/themes.json`.

### 2.2. Colour
* One accent colour for the **main** element (our bar, base case, SAM); everything else neutral
  grey-blue. Chart parameter `highlight_index`.
* Red only for negative values and risks.
* At most 4 colours per chart.

### 2.3. Choosing a chart

| Message | Type | `chart.type` |
|---|---|---|
| Comparing magnitudes (TAM/SAM/SOM, segments) | horizontal bars | `bar` |
| Change over years (1–2 series) | columns | `column` |
| Change over years, scenarios (2–4 series) | line with markers | `line_markers` |
| Composition and its change | stacked columns | `stacked_column` |
| Bridge "before → after" (MRR, cost, use of funds) | waterfall | `waterfall` |
| Share of one element (≤ 4 parts) | doughnut | `doughnut` |
| Two metrics per object (positioning) | scatter / 2×2 matrix | `scatter` / layout `matrix` |

* **Native** charts with an embedded workbook only (QA: `chart_as_image`, `chart_no_data`).
* Data labels instead of an axis where possible; on multi-series lines only the last point is
  labelled (automatic, locale-formatted).
* Y axis from zero for columns. No 3D, shadows or gradients.
* Unit in the chart title or caption (`$B`, `млрд ₽`, `亿元`, `nghìn tỷ ₫`, `Rp triliun`,
  `RM bilion`), not on every value.
* Negative values: category labels at the bottom of the plot area (automatic).

### 2.4. Tables
* Numeric columns right-aligned including the header (automatic); text left-aligned.
* Highlight one row (`highlight_row`) — base case or total.
* ≤ 7 rows on a slide; longer tables go to the report / appendix.

### 2.5. Images
* Product screenshots — yes, captioned "prototype interface, October 2026".
* Renders and concepts — clearly marked "concept". No stock photos.

## 3. Final checklist

**Content**
- [ ] Slide 2 / executive summary has the answer, 3 numbers and the condition.
- [ ] Titles read in order tell the story.
- [ ] Every number has a unit, period and source; real facts have a link.
- [ ] Forecasts labelled nominal / real; three scenarios; the bear case shown.
- [ ] Market computed bottom-up and checked top-down; gap < 2× or explained.
- [ ] Scoring: range and confidence shown; red flags carried into risks.
- [ ] Regulation & sovereignty criteria of the market profile addressed (`markets/<profile>.md`).
- [ ] The ask is specific: amount, terms, use of funds, milestone.
- [ ] Fictional / illustrative data labelled as such.

**Form**
- [ ] `python tools/qa_check.py --pptx deck.pptx --docx report.docx --facts facts.json --locale <loc>` → 0 errors;
      warnings reviewed.
- [ ] Renders inspected (`render_preview.py`): no overlaps, clipped text, empty areas or missing
      glyphs.
- [ ] Font ≥ 10 pt; ≤ 6 bullets; one idea per slide.
- [ ] Speaker notes on every content slide.
- [ ] Charts native and editable in PowerPoint/Word.
- [ ] In Word: update fields (Ctrl+A, F9) — contents and page numbers.
- [ ] File metadata (author, title, language) correct; watermarks removed or intended.
