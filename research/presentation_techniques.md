# Presentation techniques

A catalogue of generic techniques used by strong strategy, product and investment presentations.
Each entry says **what** the technique is, **when** to use it, **where** it is built into the
skill, and the **failure mode** to avoid. The techniques are common practice; no specific company
presentation is required to apply them.

## 1. Storyline

| Technique | What it is | Where in the skill | Avoid |
|---|---|---|---|
| **Answer first** | The conclusion and the ask come first; arguments and data follow. The reader can stop after slide 2 and still know the recommendation. | Slide 2 "summary" (`big_number`), report section 1 | A "journey" that saves the answer for the end |
| **Situation – Complication – Question – Answer** | A four-sentence introduction: the stable context, what changed, the question it raises, the answer. | Report executive summary (`p_scqa` in the examples), `prompts/*/storyline_builder.md` | A complication that is not a real change |
| **Mutually exclusive, collectively exhaustive arguments** | Arguments at one level do not overlap and together cover the claim. | Section structure of the report; red-team prompt checks gaps | Lists that mix causes, effects and examples |
| **Action titles** | Every slide title is a full sentence with the finding and a number. Reading titles alone gives a coherent story ("horizontal logic"). | `qa_check.py` flags label-only titles (`label_title`) and long titles | Titles like "Market" or "Team" |
| **One message per slide** | A slide supports one claim; detail moves to notes or the report. | `qa_check.py` density warnings; speaker notes on every slide | Dense slides read aloud |
| **Why now** | A dedicated argument for timing: what changed in technology, regulation or cost. | Problem slide bullet "why now"; intake questionnaire | Timing claims without a dated source |
| **Insight** | The non-obvious thing the team knows (a cost structure, a workflow, a regulatory path). | Solution / competition slides | Restating the problem |
| **Ask tied to a milestone** | The amount requested, what it buys and which verifiable milestone it reaches before the next decision. | Closing slide and roadmap (`timeline`) | An ask without a use of funds |
| **Staged plan where each step funds the next** | A roadmap in which early revenue or evidence pays for the next stage. | Roadmap slide, tranche recommendation | Distant visions without near-term checkpoints |

## 2. Numbers

| Technique | What it is | Where | Avoid |
|---|---|---|---|
| **Physical units and denominators** | State scale in units the audience can check (documents per year, minutes per task, users), then normalise (per customer, per employee, per document). | `style_guide.md` §numbers; `automation_roi`, `cost_per_task` | Percentages without a base |
| **Bottom-up first, top-down as a check** | Market = organisations × contract × reachable share × achievable share; a top-down estimate only validates it. | `market_sizing.py` (warns if the two differ by > 2×) | Using a global market as TAM for a niche product |
| **Three scenarios** | Bear / base / bull with explicit assumption differences; the bull case never stands alone in a title. | `financial_model.py`, scenario slides | "Conservative estimate" without a range |
| **Sensitivity grid** | A 2D table showing which assumptions move the result. | `financial_model.py` sensitivity, report table | Single-point valuations |
| **Returns stated two ways** | IRR and MOIC together, with entry valuation, dilution and exit assumptions. | Returns slide and report | IRR alone |
| **Cost-down waterfall** | Shows how unit cost falls step by step (automation, scale, learning curve). | `chart.type: waterfall`, `wright_law` | Learning rates without data points |
| **Benchmarks, not laws** | Rule of 40, burn multiple, LTV/CAC presented as industry rules of thumb with their source. | `metrics.md` | Benchmarks quoted without a source |
| **Evidence grading** | Each score or claim is tagged A (verified), B (credible estimate), C (assumption); ranges widen with weaker evidence. | `scoring.py`, scorecard slide | Precise scores on assumptions |

## 3. Proof

| Technique | What it is | Where | Avoid |
|---|---|---|---|
| **Outcome in the customer's metric** | Pilot results in the customer's own units (hours, error rate, cost per document) with sample size. | Pilot slide (`big_number`), `accuracy_vs_baseline` with confidence interval | "Customers love it" |
| **Us versus alternatives on one chart** | A single matrix or bar chart comparing the product to categories of alternatives on the two dimensions buyers care about. | `matrix` layout, `highlight_index` in charts | Naming competitors without evidence; feature checklists |
| **Engineering depth in one block** | A technology slide with readiness level (TRL), architecture and the measured result — not a roadmap of promises. | Technology / TRL slide | Point dates for unproven capabilities; mock-ups presented as product |
| **Customer voice** | A short, attributed (or anonymised with permission) quote tied to a metric. | Traction slide notes | Unattributed superlatives |
| **Risk register with mitigations** | Each risk has one mitigation and one control metric. | Risk slide and report table | Hiding risks in the appendix |

## 4. Delivery and language

| Technique | What it is | Where | Avoid |
|---|---|---|---|
| **Short sentences and repetition of the core claim** | The main thesis is repeated in the summary, the closing slide and the report conclusion, in the same words. | `style_guide.md` §language | Superlatives and absolute claims (`banned_phrases.json`) |
| **Audience-specific order** | Investors: traction and returns early. Government: compliance, sovereignty and public value early. Academia: novelty and TRL. | `deck_structure.md` §2 | One deck for every audience |
| **Speaker notes as the script** | Every slide has notes with the talk track and the sources. | Notes in all example decks | Reading the slide aloud |
| **Appendix for detail** | Assumption tables, sensitivity and methodology go to the appendix and the report. | Report appendix | Cutting assumptions entirely |

## 5. Investment-memo structure

A common structure for investment memoranda and investor-day material, reflected in the report
template: thesis → value-creation plan → market and competition → financials with scenarios →
returns (IRR/MOIC) → risks and mitigations → exit routes → appendix with assumptions.

## 6. Metric references used in `metrics.md`

* Rule of 40 — B. Feld, 2015: https://feld.com/archives/2015/02/rule-40-healthy-saas-company/
* Burn multiple — D. Sacks, Craft Ventures: https://www.craftventures.com/articles/the-burn-multiple
* Magic number — Scale Venture Partners: https://www.scalevp.com/blog/saas-metrics-a-history-of-the-magic-number
* Wright's law — Our World in Data: https://ourworldindata.org/learning-curve ; Nagy, Farmer, Bui,
  Trancik, PLOS ONE, 2013: https://doi.org/10.1371/journal.pone.0052669
* TRL — NASA: https://www.nasa.gov/directorates/somd/space-communications-navigation-program/technology-readiness-levels/ ;
  GOST R 58048-2017 (Russian TRL standard): https://base.garant.ru/72237776/
