# Pattern: Corporate proposal (enterprise buyer / partner)

Russian label: Корпоративное предложение (крупный заказчик / партнёр)  ·  id: `corporate`  ·  kind: customer

## Who decides what
An enterprise buyer or partner decides whether to run a pilot. They care about cost, risk, time to value and whether the vendor will survive.

## Tone
customer's language: cost, risk, time to value; vendor viability in one slide

## What to emphasise
- Customer ROI and payback computed from hours saved × loaded wage (metrics_calc.customer_roi).
- 3-year TCO against the current way of working (metrics_calc.customer_tco).
- Implementation plan, data ownership and an exit plan.
- Vendor viability in one slide; no investor returns.

## Deck
- Length: 9–13 slides (target 11); QA warns outside the range.
- Theme: `corporate` (deck), `corporate` (report). Override with `--theme`.
- Slide order (ids implemented in `tools/pitch_story.py`):

  1. `title`
  2. `customer_hook`
  3. `customer_problem`
  4. `solution`
  5. `customer_roi`
  6. `tco`
  7. `competition`
  8. `implementation`
  9. `vendor_viability`
  10. `risks`
  11. `pilot_offer`

- Chart types: `customer_roi` → column, `tco` → bar

## Mandatory metrics
Computed by `auto_pitch.py`; `qa_check.py --pattern corporate` fails the deck when the terms are missing.

- `auto.cust.roi`
- `auto.cust.payback_months`
- `auto.cust.tco`
- `auto.cust.saving_3y`

Terms that must appear (regex): `\bROI\b`, `\bTCO\b`, `payback|окупаем|回本|hoàn vốn|balik modal|bayar balik`

## Cut

- investor returns (MOIC, IRR)
- fundraising ask
- valuation

## Call to action
- en: Decision: an 8-week paid pilot on 5 locations with success criteria agreed upfront
- ru: Решение: 8-недельный платный пилот на 5 точках с заранее согласованными критериями успеха

## Scoring
Audience profile `corporate` from `config/scoring_model.json`, with weight overrides (percent, renormalised): problem 16, regulatory 10, risk 9, trl 12.

## Red-team questions

1. Which hours saved are measured and which are estimated?
2. What does integration with payroll / HR systems cost us?
3. What if the vendor disappears — data export and exit plan?
4. Who owns the schedule data and where is it stored?

## Run
```bash
python tools/auto_pitch.py --brief brief.json --pattern corporate --render
```
