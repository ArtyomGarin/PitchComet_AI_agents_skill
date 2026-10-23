# Pattern: Smaller investor (angel / pre-seed / seed)

Russian label: Небольшой инвестор (бизнес-ангел / pre-seed / seed)  ·  id: `small_investor`  ·  kind: investor

## Who decides what
An angel or a seed fund decides whether to take a second meeting. They spend minutes, not hours, and invest in a problem, a team and a path to the next round.

## Tone
clear story, one big problem, why this team now; numbers are ranges with confidence

## What to emphasise
- One clear problem slide with a number from official statistics.
- Market as TAM → SOM with CAGR; keep SAM in the report.
- LTV/CAC as a range and the cheapest channel for the first 100 customers.
- The ask with an 18-month runway and the milestones that make the next round easy.

## Deck
- Length: 10–14 slides (target 12); QA warns outside the range.
- Theme: `warm` (deck), `light` (report). Override with `--theme`.
- Slide order (ids implemented in `tools/pitch_story.py`):

  1. `title`
  2. `hook`
  3. `problem`
  4. `solution`
  5. `market_sizing`
  6. `market_growth`
  7. `competition`
  8. `business_model`
  9. `unit_economics`
  10. `gtm`
  11. `financials`
  12. `ask`
  13. `closing`

- Chart types: `market_sizing` → bar, `market_growth` → column, `financials` → column

## Mandatory metrics
Computed by `auto_pitch.py`; `qa_check.py --pattern small_investor` fails the deck when the terms are missing.

- `market.tam_base`
- `market.som_horizon_base`
- `market.cagr_base`
- `auto.ue.ltv_cac`
- `fin.moic_base`

Terms that must appear (regex): `\bTAM\b`, `\bSOM\b`, `\bCAGR\b`, `LTV\s*/\s*CAC`, `\bMOIC\b`

## Cut

- detailed sensitivity tables
- full P&L
- DCF terminal-value maths

## Call to action
- en: Join the round: {{auto.ask|money_mn1}} for 18 months to reach the milestones on the timeline
- ru: Войти в раунд: {{auto.ask|money_mn1}} на 18 месяцев до вех на дорожной карте

## Scoring
Audience profile `investor` from `config/scoring_model.json`, with weight overrides (percent, renormalised): team 15, problem 14, market 14, traction 8.

## Red-team questions

1. Why will customers switch from spreadsheets and messengers?
2. What is the cheapest channel and its CAC in the first 100 customers?
3. What milestone makes the next round easy?
4. Who on the team has sold to this buyer before?

## Run
```bash
python tools/auto_pitch.py --brief brief.json --pattern small_investor --render
```
