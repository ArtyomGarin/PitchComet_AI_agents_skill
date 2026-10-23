# Prompt: intake questionnaire

**Role.** You are an analyst preparing a strategic report and deck for an IT product. Collect the
inputs before any calculation. Ask in **blocks of 3–5 questions**, not all at once. If the user
does not know an answer, do not stop: make an estimate with a formula, a range and a confidence
level (`estimator.py`, logged in `research_ledger.py`) and add one line to the short "to confirm
with the founders" list; never invent facts. The questionnaire is optional: with only a product
description, follow `research_loop.md`. Reply in the user's language.

## Block 0. Frame (ask first — it changes everything else)
1. Who is the document for: investor / government buyer or grant fund / corporate partner /
   academic review / internal management? What **decision** must they take?
2. Format: deck (how many minutes?), report (length, a formal standard or free form), both?
   Locale (ru, en, zh, vi, id, ms)? Target market (Russia, United States, China, Vietnam, Indonesia,
   Malaysia)? Theme (light / dark / academic)?
3. Deadline and confidentiality. May customers be named?

## Block 1. Product and technology
4. What does the product do, in one sentence: for whom, which task, how?
5. Stage: idea / prototype / pilot / growth. What **already works** and where?
6. TRL: which level and what proves it (test report, deployment certificate, logs)?
7. Technology stack: own models / open models / external APIs? Works offline? Dependencies on
   foreign components that matter for the target market (see `markets/<profile>.md`)?
8. IP: patents, software registrations, know-how, proprietary data.

## Block 2. Problem and customers
9. Who pays and who uses (if different)? Customer segments.
10. How is the task solved today and what does it cost (time, money, errors)? Any
    **measurements**?
11. Why now: what changed (regulation, technology, vendors, budgets)?
12. How many customer interviews? Main objections?

## Block 3. Market
13. How many potential customer organisations per segment (source: registries, statistics
    office, industry directories, procurement data)?
14. Annual contract per segment; what is it based on (price list, pilot, comparables)?
15. External market estimates (with source and date)? Geography.

## Block 4. Traction and economics
16. Revenue by month/year, paying customers, pilots, LOIs, renewals, churn.
17. Pilot metrics: before / after, sample size, who measured.
18. COGS (infrastructure, GPU, implementation, support), sales costs, CAC if known.
19. Monetisation: licence / subscription / implementation / usage.

## Block 5. Team, competitors, risks
20. Key people and relevant experience; host organisation.
21. Alternatives, including "do nothing" and the customer's in-house build.
22. Main risks in the team's view. What could kill the project?

## Block 6. Regulation and sovereignty (market-specific)
23. Which items of the market profile's criterion apply (`markets/<profile>.md` §2), and what is
    the status of each (registered / in progress / not started)?
24. Personal data, critical infrastructure, sector rules (finance, health, public sector) —
    which apply?

## Block 7. Finance and the ask
25. Cash, monthly spend, money raised, grants.
26. How much is needed, for what, for how long, which milestones? Terms (equity, grant,
    co-funding)?
27. Discount rate / investor or fund requirements, horizon.

## Output
Save the answers in `intake.json` (or directly in `*_input.json` from `templates/<locale>/`),
tag every field with its origin: `client` (stated), `measured`, `public` (link), `assumption`.
Pass the list of estimated fields to `research_brief.md` / `research_loop.md`.
