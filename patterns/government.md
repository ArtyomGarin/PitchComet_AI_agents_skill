# Pattern: Government / grant (development institution, public programme)

Russian label: Государство / грант (институт развития, госпрограмма)  ·  id: `government`  ·  kind: public

## Who decides what
A development institution or public programme decides whether to support an application. They look for public effect, compliance and KPIs they can measure.

## Tone
public effect, compliance and measurable KPIs; no hype

## What to emphasise
- Public effect: organisations served, hours freed, economic effect per year.
- SAM and CAGR for the national market; customer ROI as the micro-level proof.
- Regulatory fit: registries, data localisation, labour-law alignment.
- A scorecard with KPIs the programme can audit; no exit multiples.

## Deck
- Length: 11–15 slides (target 13); QA warns outside the range.
- Theme: `corporate` (deck), `corporate` (report). Override with `--theme`.
- Slide order (ids implemented in `tools/pitch_story.py`):

  1. `title`
  2. `hook`
  3. `problem`
  4. `solution`
  5. `public_effect`
  6. `market_sizing`
  7. `market_growth`
  8. `customer_roi`
  9. `regulatory`
  10. `implementation`
  11. `financials`
  12. `risks`
  13. `scorecard`
  14. `closing`

- Chart types: `market_sizing` → bar, `financials` → column

## Mandatory metrics
Computed by `auto_pitch.py`; `qa_check.py --pattern government` fails the deck when the terms are missing.

- `market.sam_base`
- `market.cagr_base`
- `auto.cust.roi`
- `fin.revenue_last`

Terms that must appear (regex): `\bSAM\b`, `\bCAGR\b`, `\bROI\b|окупаем|payback`

## Cut

- exit multiples
- aggressive growth claims

## Call to action
- en: Decision: support the programme application and the KPI set on the scorecard
- ru: Решение: поддержать заявку в программу и набор KPI из скоркарты

## Scoring
Audience profile `government` from `config/scoring_model.json`, with weight overrides (percent, renormalised): regulatory 12, problem 14.

## Red-team questions

1. Which KPI will the programme measure and how?
2. Is the software in the required national registries?
3. How many jobs or hours does it free up per region?

## Run
```bash
python tools/auto_pitch.py --brief brief.json --pattern government --render
```
