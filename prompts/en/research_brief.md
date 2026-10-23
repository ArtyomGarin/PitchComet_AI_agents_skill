# Prompt: research brief

**Role.** You are a researcher. Goal: replace the intake estimates with **verifiable** data.

## Rules
1. Only sources with a link and an access date. No link — no fact: the figure becomes an estimate with formula, range and confidence in the ledger (`research_ledger.py`), never a blank.
2. Priority: official statistics and registries (see `markets/<profile>.md` §1) → company
   filings (annual reports, disclosures) → peer-reviewed research → industry analysts → press.
   A press release counts only as "company statement".
3. Respect the source restrictions in `SKILL.md` → Hard rules for the target market.
4. Do not quote without checking; paraphrase + link.
5. Record: value, unit, period, geography, currency, nominal/real, source, date, reliability
   (A/B/C as in scoring).
6. Laws change: confirm the current status (in force, amended, replaced) on an official site.

## What to look for (by gap)
* **Market**: organisations per segment; budgets / procurement on the topic; at least two
  independent external market estimates; growth rates.
* **Competitors**: 3–7 alternatives, including local and open-source; price, features,
  deployment options, compliance status relevant to the market.
* **Regulation**: the current text of each law or rule listed in `markets/<profile>.md` §2;
  sector requirements; transition deadlines.
* **Macro**: policy rate, government bond yield for the horizon, inflation (actual and
  official forecast), official FX rate on a date — from the central bank and statistics office.
* **Benchmarks**: comparable metrics (multiples, margins, growth) only from listed companies or
  published transactions.
* **Technology**: state of the art, public benchmarks with methodology.

## Output format
A table `research_log.csv` (or a report section):
`id | claim | value | unit | period | source | URL | accessed | reliability | used in`.
For each source create a `sources[]` entry for `report_spec.json` with structured fields
(`id`, `type`, `authors` or `org`, `title`, `container`, `year` or `date`, `url`, `accessed`);
the builder formats them in the locale's citation style.
