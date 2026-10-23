# Pattern: SMB customers (owners of shops, cafés, small chains)

Russian label: Клиенты МСП (владельцы магазинов, кафе, небольших сетей)  ·  id: `smb`  ·  kind: customer

## Who decides what
The owner of a shop, café or small chain decides whether to try the product this week. One number per slide: pay X, save Y.

## Tone
simple words, one number per slide: pay X — save Y per month

## What to emphasise
- Price per month next to the monthly saving and the value ratio (metrics_calc.smb_monthly_value).
- Payback in months or weeks, in plain words.
- How to start in three steps; no contract, no hardware.
- No jargon on slides: TAM, LTV and CAC stay in the report.

## Deck
- Length: 6–9 slides (target 8); QA warns outside the range.
- Theme: `warm` (deck), `light` (report). Override with `--theme`.
- Slide order (ids implemented in `tools/pitch_story.py`):

  1. `title`
  2. `smb_hook`
  3. `customer_problem`
  4. `solution`
  5. `smb_value`
  6. `pricing`
  7. `how_to_start`
  8. `closing_smb`

- Chart types: `smb_value` → column

## Mandatory metrics
Computed by `auto_pitch.py`; `qa_check.py --pattern smb` fails the deck when the terms are missing.

- `auto.price_month`
- `auto.cust.saving_month`
- `auto.cust.value_ratio`
- `auto.cust.payback_months`

Terms that must appear (regex): `payback|окупаем|回本|hoàn vốn|balik modal|bayar balik|\bROI\b`, `/\s?мес|per month|/month|в месяц|每月|/tháng|/bulan|sebulan`

## Cut

- market sizing
- investor metrics
- jargon (TAM, LTV, CAC)

## Call to action
- en: Start a 14-day free trial today — your first schedule in 15 minutes
- ru: Начните 14-дневный бесплатный период сегодня — первый график за 15 минут

## Scoring
Audience profile `corporate` from `config/scoring_model.json`, with weight overrides (percent, renormalised): problem 18, unit_economics 12, gtm 10.

## Red-team questions

1. Will my staff actually use the app?
2. What happens to my data if I stop paying?
3. Is there a contract or can I cancel monthly?

## Run
```bash
python tools/auto_pitch.py --brief brief.json --pattern smb --render
```
