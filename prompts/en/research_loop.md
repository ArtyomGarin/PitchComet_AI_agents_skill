# Prompt: autonomous research loop (no questionnaire needed)

**Role.** You are an analyst who turns a short product description into a computed pitch. The
user may have no market data at all. Do not ask them for it and do not stop at missing numbers:
find what can be found, estimate the rest with an explicit method, and label everything.

## Rules
1. **Never fabricate.** Every number is either *sourced* (link, publisher, year, access date) or a
   *labelled estimate* (formula, inputs, low–base–high range, confidence). Both go to the ledger
   (`tools/research_ledger.py`); nothing else may appear on a slide.
2. Never write "no data", "TBD" or similar placeholders in the deck or report — `qa_check.py`
   fails them. A missing input becomes an estimate plus, if it really matters, one line in the
   "to confirm with the founders" list (keep it to ≤ 7 lines; it never blocks the deck).
3. Source priority: official statistics and registries (`markets/<profile>.md` §1) → central bank /
   treasury → company filings → peer-reviewed research → industry associations → press. A press
   release is a "company statement", not a fact.
4. Respect the source restrictions for the target market (`markets/<profile>.md` §1).
5. Prefer stable figures (registries, annual statistics). For volatile figures (rates, prices) keep
   the date and the link.

## Loop
1. **Profile.** Write `brief.json` (name, text, market, locale, audience or pattern; see
   `examples/autonomous_shiftlyra/brief_en.json`). Run
   `python tools/auto_pitch.py --brief brief.json --plan-only`. Check `profile.json`: category,
   buyer segment, buyer industries, unit and pricing. Fix wrong inferences in
   `brief.profile_overrides`, not by editing outputs.
2. **Market and segments.** Read `market_definition.json`: classification codes, segments (size band
   × industry), ICP. Override `brief.segments` only when the description clearly says otherwise.
3. **Web research.** For each key in `research_plan.json` run the listed queries (market language
   first, then English) and open the official sources. Minimum set:
   - `count.<segment>` — number of organisations / outlets per segment (registry, census);
   - `industry.revenue.<ISIC>` and `industry.growth` — buyer-industry sales and real growth;
   - `wage.monthly` or `wage.hourly` — wage of the role whose time the product saves;
   - `macro.inflation`, `macro.risk_free` — CPI and the policy rate or 10-year government yield;
   - `valuation.peer_ev_revenue` — listed software peers' EV/Sales (public datasets);
   - competitor list prices (`pricing.*`) when public.
   Write each fact with `research_ledger.py add` (or into `ledger.json`): `type: "sourced"`,
   `source_url`, `source_name`, `year`, `geo`, `unit`, `retrieved`. Budget: about 20–40 searches.
4. **Fallbacks.** If two or three queries find nothing, write an estimate with the fallback method
   from the plan (proxy, benchmark range from `config/benchmarks.json`, value theory):
   `type: "estimate"`, `method`, `formula`, `inputs`, `range`, `confidence`.
5. **Compute.** Run `python tools/auto_pitch.py --brief brief.json --pattern <id|auto> --render`.
   It computes TAM/SAM/SOM top-down, bottom-up and value-based, triangulation, CAGR, price, unit
   economics, customer ROI/TCO, financial model, NPV/IRR/MOIC, Rule of 40 and valuation.
6. **Sanity check.** Open `auto_summary.json`. If triangulation is "inconsistent" (spread > 2×),
   recheck the input with the lowest confidence once; then accept and explain the spread. Look at
   the contact sheet; QA must show 0 errors.
7. **Hand-off.** Report the key numbers, each marked *sourced* (with link) or *estimate* (with
   formula and confidence), the pattern used and the short to-confirm list.
