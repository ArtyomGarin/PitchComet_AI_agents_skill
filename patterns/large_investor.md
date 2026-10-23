# Pattern: Large investor (growth / late stage fund)

Russian label: Крупный инвестор (фонд роста / поздние стадии)  ·  id: `large_investor`  ·  kind: investor

## Who decides what
A growth or late-stage fund's investment committee decides whether to open due diligence. They read 15–20 slides, check every number against a source and want the downside first.

## Tone
numbers first, conservative, every claim with a source or a formula; show downside

## What to emphasise
- Lead with the market triangle (TAM/SAM/SOM by three methods) and the spread between methods.
- Unit economics as ranges (low/base/high) with the benchmark basis written next to each number.
- Bear / base / bull NPV, IRR and MOIC on one slide; Rule of 40 in the last model year.
- Valuation by comparables with the private-company discount shown explicitly.
- An evidence slide: how many figures are sourced and how many are estimates.

## Deck
- Length: 15–20 slides (target 18); QA warns outside the range.
- Theme: `comet` (deck), `light` (report). Override with `--theme`.
- Slide order (ids implemented in `tools/pitch_story.py`):

  1. `title`
  2. `hook`
  3. `problem`
  4. `solution`
  5. `why_now`
  6. `market_sizing`
  7. `segments`
  8. `market_growth`
  9. `competition`
  10. `business_model`
  11. `unit_economics`
  12. `financials`
  13. `fin_scenarios`
  14. `valuation`
  15. `risks`
  16. `evidence`
  17. `ask`
  18. `closing`

- Chart types: `market_sizing` → bar, `market_growth` → line_markers, `financials` → column, `fin_scenarios` → table

## Mandatory metrics
Computed by `auto_pitch.py`; `qa_check.py --pattern large_investor` fails the deck when the terms are missing.

- `market.tam_base`
- `market.sam_base`
- `market.som_horizon_base`
- `market.cagr_base`
- `auto.ue.ltv_cac`
- `auto.ue.payback`
- `fin.rule40_last`
- `fin.npv_base`
- `fin.irr_base`
- `fin.moic_base`
- `auto.val.ev_base`

Terms that must appear (regex): `\bTAM\b`, `\bSAM\b`, `\bSOM\b`, `\bCAGR\b`, `LTV\s*/\s*CAC`, `Rule of 40|Правило 40|правило 40|40法则|Quy tắc 40|Aturan 40|Peraturan 40`, `\bIRR\b`, `\bMOIC\b`

## Cut

- founder story
- feature lists
- logos without contracts
- vision without numbers

## Call to action
- en: Decision: term sheet for {{auto.ask|money_mn1}} and a 6-week due diligence on the five numbers above
- ru: Решение: term sheet на {{auto.ask|money_mn1}} и 6-недельная проверка пяти цифр выше

## Scoring
Audience profile `investor` from `config/scoring_model.json`, with weight overrides (percent, renormalised): traction 16, unit_economics 16, market 14, scalability 8.

## Red-team questions

1. Which of the TAM inputs is sourced and which is a rule of thumb — what happens to SOM if the adoption range is halved?
2. What is CAC payback in the bear case and is it still under 24 months?
3. Why does the exit multiple deserve the peer median after the private-company discount?
4. Which cohort data will replace the benchmark churn within two quarters?
5. What breaks if the policy rate stays at the current level for three years?

## Run
```bash
python tools/auto_pitch.py --brief brief.json --pattern large_investor --render
```
