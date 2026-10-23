# Pitch patterns

One computed fact base, five ways to tell it. A pattern changes slide order, deck length,
mandatory metrics (enforced by `qa_check.py --pattern`), scoring weights, chart types, tone, what to cut,
the call to action and the red-team questions. Definitions live in `patterns.json`; slide builders in
`tools/pitch_story.py`.

| id | Audience | Kind | Theme | Slides | Mandatory terms |
|---|---|---|---|---|---|
| [`large_investor`](large_investor.md) | Large investor (growth / late stage fund) | investor | comet | 15–20 | TAM, SAM, SOM, CAGR, LTV/CAC, Rule of 40, IRR, MOIC |
| [`small_investor`](small_investor.md) | Smaller investor (angel / pre-seed / seed) | investor | warm | 10–14 | TAM, SOM, CAGR, LTV/CAC, MOIC |
| [`corporate`](corporate.md) | Corporate proposal (enterprise buyer / partner) | customer | corporate | 9–13 | ROI, TCO, payback |
| [`smb`](smb.md) | SMB customers (owners of shops, cafés, small chains) | customer | warm | 6–9 | payback, price per month |
| [`government`](government.md) | Government / grant (development institution, public programme) | public | corporate | 11–15 | SAM, CAGR, ROI |

Slide counts exclude the glossary slide(s) ("What the numbers mean") that every deck gets after
the title slide.

## Selection
- Explicit: `auto_pitch.py --pattern <id>` or `"pattern": "<id>"` in the brief.
- Automatic: `"pattern": "auto"` matches the brief's `audience` text against each pattern's
  `audience_keywords` (ru, en, zh, vi, id, ms). No match → `small_investor`.
- `auto_summary.json` records which pattern was used and why (`pattern_selected_by`).

## Adding a pattern
1. Add an entry to `patterns.json` (copy an existing one).
2. Use slide ids that exist in `tools/pitch_story.py` or add a builder method `s_<id>`.
3. Add `<id>.md` here and a test in `tools/tests/test_autonomous.py`.
