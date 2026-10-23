# Development-potential scoring model

Languages: **English** · [Русский](scoring_model.ru.md) · [简体中文](scoring_model.zh-CN.md)

> Generated from `config/scoring_model.json` by `python tools/gen_scoring_doc.py`. Edit the JSON, then regenerate.

## Purpose and use

The model turns qualitative judgements about a product into a **comparable 0–100 number** with an
uncertainty range and a list of red flags. It is a discipline, not the truth: every score needs an
anchor (what exactly "3" means for the criterion) and an evidence level (A/B/C).

1. Choose the **stage** (`idea` / `prototype` / `pilot` / `growth`) from facts: idea — no working
   artefact; prototype — TRL 4–6, no paying users; pilot — at least one external pilot, first money
   or LOIs; growth — repeatable sales, ARR and retention measured monthly.
2. Choose the **audience** (`investor` / `government` / `corporate` / `academic`); it changes the
   weights (§7) and the deck structure (§9, `deck_structure.md`).
3. Choose the **market profile** (`ru`, `en`, `zh`, `vn`, `id`, `my`; default from the locale). It
   multiplies selected weights, redefines the *Regulation & sovereignty* criterion and enables
   market-specific red flags (§10, `markets/*.md`).
4. Fill `scoring_input.json` (`templates/<locale>/` or `python tools/scoring.py template`): a 0–5
   score per criterion (half points allowed), an evidence level and a one-line rationale with a fact
   and a link.
5. Run `python tools/scoring.py --input scoring_input.json --locale <loc> [--market <profile>]`.
   Output: total, range, confidence, grade, contributions, red flags, strengths and gaps, chart data
   and slide allocation. `run_pipeline.py` also computes all four audience profiles.

Formula: `Total = Σ (weight_i × score_i / 5)`, weights = stage profile × audience multiplier ×
market multiplier, normalised to 100. Range: `Σ weight_i × (score_i ± band_i) / 5`, band A = 0,
B = 0.5, C = 1.0.

## 1. Base weights (sum = 100) and rationale

| # | id | Criterion | Weight | Rationale |
|---|---|---|---:|---|
| 1 | `market` | Market size & growth | **14** | Caps the upside; every audience asks 'how big can this get'. Highest single weight because every other criterion is multiplied by the size of the prize. Absolute SAM thresholds are set per market profile (currency-specific). |
| 2 | `problem` | Problem severity & willingness to pay | **12** | Painful, budgeted problems shorten sales cycles; 'nice-to-have' kills B2B and B2G products regardless of tech quality. |
| 3 | `trl` | Product / technology maturity (TRL/УГТ) | **10** | Separates research from product. Mapped to the TRL scale (and national equivalents, e.g. ГОСТ Р 58048-2017 in Russia) so that grant committees and corporates read it the same way. |
| 4 | `moat` | Differentiation, moat & IP | **10** | Determines whether margins survive competition from big platforms and open-source models. |
| 5 | `team` | Team & execution capability | **10** | Early-stage outcomes track team quality; government and academic audiences also weigh institutional backing. |
| 6 | `traction` | Traction & evidence | **10** | Converts claims into evidence: users, revenue, pilots, LOIs, retention. |
| 7 | `unit_economics` | Business model & unit economics | **9** | Shows growth will create rather than burn value: gross margin, LTV/CAC, payback. |
| 8 | `gtm` | Go-to-market & channels | **7** | B2B/B2G sales cycles are long; a named channel (integrator, marketplace, procurement route) matters more than ads. |
| 9 | `regulatory` | Regulatory & sovereignty fit | **7** | Data-protection, security certification and supply-chain sovereignty requirements are entry tickets for public-sector, regulated and critical-infrastructure buyers. The concrete regimes differ by market and are defined in market_profiles. |
| 10 | `scalability` | Scalability & export potential | **5** | Measures the option value beyond the first market: replicability across sectors and accessible export markets (defined per market profile). |
| 11 | `risk` | Risk profile (5 = low risk) | **6** | Inverse criterion: concentration, dependency, technology, financing and regulatory risk after mitigants. |
| | | **Total** | **100** | |

## 2. Anchored 0–5 rubric

Scale: 0 = no evidence / absent; 5 = best-in-class with verified evidence. Half points allowed.

### Market size & growth (`market`, weight 14)

| Score | Anchor |
|---:|---|
| 0 | no identifiable paying market |
| 1 | very small SAM or shrinking market |
| 2 | small SAM, growth < 5%/yr |
| 3 | mid-size SAM, growth 5–15% |
| 4 | large SAM or growth 15–30%, bottom-up confirmed |
| 5 | very large SAM and growth > 20%, triangulated top-down + bottom-up |

**Red flags:** TAM quoted from a generic 'global AI market' figure; no bottom-up check; CAGR from a single press release

### Problem severity & willingness to pay (`problem`, weight 12)

| Score | Anchor |
|---:|---|
| 0 | problem not validated |
| 1 | anecdotal pain, no budget owner |
| 2 | pain confirmed in < 10 interviews, unclear budget |
| 3 | ≥ 20 interviews, named budget owner, workaround cost quantified |
| 4 | customers pay for workarounds today; quantified loss > 10x price |
| 5 | mission-critical / regulatory mandate; customers pre-pay or co-fund |

**Red flags:** problem described only in the team's words; buyer ≠ user and buyer not interviewed

### Product / technology maturity (TRL/УГТ) (`trl`, weight 10)

| Score | Anchor |
|---:|---|
| 0 | TRL 1–2: concept only |
| 1 | TRL 3: proof of concept |
| 2 | TRL 4–5: validation in a relevant environment |
| 3 | TRL 6: prototype demonstrated with real data |
| 4 | TRL 7–8: system in customer operation, qualified |
| 5 | TRL 9: proven in routine operation at several customers |

**Red flags:** demo is scripted / not on customer data; claimed TRL above evidence

### Differentiation, moat & IP (`moat`, weight 10)

| Score | Anchor |
|---:|---|
| 0 | commodity; easily replicated |
| 1 | feature-level difference only |
| 2 | better on 1–2 measured dimensions vs. alternatives |
| 3 | measured advantage + proprietary data or workflow lock-in |
| 4 | several reinforcing moats (data, integrations, certifications, registered IP) |
| 5 | structural moat: network effects / exclusive data / regulation-backed position |

**Red flags:** thin wrapper over a third-party model without a proprietary data advantage; 'no competitors' claim

### Team & execution capability (`team`, weight 10)

| Score | Anchor |
|---:|---|
| 0 | no dedicated team |
| 1 | part-time team, key skills missing |
| 2 | core technical team, no commercial lead |
| 3 | complete core team, relevant domain track record |
| 4 | team has shipped & sold similar products; advisors with access |
| 5 | repeat founders / leading research group + proven commercial executives |

**Red flags:** single point of failure (one developer); no one owns sales

### Traction & evidence (`traction`, weight 10)

| Score | Anchor |
|---:|---|
| 0 | none |
| 1 | waitlist / interest only |
| 2 | 1–2 unpaid pilots or LOIs |
| 3 | paid pilots or ≥ 3 LOIs; usage data |
| 4 | recurring revenue, ≥ 5 paying customers, retention data |
| 5 | fast-growing recurring revenue (> 2x YoY) with NRR ≥ 110% |

**Red flags:** pilots that never convert; vanity metrics (registrations, downloads) without usage

### Business model & unit economics (`unit_economics`, weight 9)

| Score | Anchor |
|---:|---|
| 0 | no model |
| 1 | pricing undefined |
| 2 | pricing defined, margins unknown |
| 3 | GM ≥ 50%, LTV/CAC estimated ≥ 2 |
| 4 | GM ≥ 70%, LTV/CAC ≥ 3, payback ≤ 18 mo (measured) |
| 5 | GM ≥ 80%, LTV/CAC ≥ 5, payback ≤ 12 mo, burn multiple < 1.5 |

**Red flags:** LTV computed with < 2% monthly churn assumption without data; inference/compute costs ignored in COGS

### Go-to-market & channels (`gtm`, weight 7)

| Score | Anchor |
|---:|---|
| 0 | no plan |
| 1 | generic plan ('marketing, partners') |
| 2 | target segment and ICP defined |
| 3 | repeatable first channel identified, sales cycle measured |
| 4 | 2+ working channels, partner/integrator agreements, procurement route clear |
| 5 | efficient scalable engine (magic number > 0.75), land-and-expand proven |

**Red flags:** relying on a single anchor customer; no understanding of public/enterprise procurement rules

### Regulatory & sovereignty fit (`regulatory`, weight 7)

| Score | Anchor |
|---:|---|
| 0 | blocked: critical dependency on a component that cannot be used in the target market, no substitute |
| 1 | major compliance gaps |
| 2 | compliance path known, not started |
| 3 | compliance in progress, controllable stack |
| 4 | meets data & security requirements of target buyers |
| 5 | full compliance + certifications + listed in sector / policy programmes |

**Red flags:** third-party cloud/LLM API in the critical path where buyers require local processing; personal data processed outside the permitted jurisdiction

### Scalability & export potential (`scalability`, weight 5)

| Score | Anchor |
|---:|---|
| 0 | custom project each time |
| 1 | heavy customization per client |
| 2 | configurable product, single sector |
| 3 | multi-sector product, marginal cost per client low |
| 4 | localized for ≥ 1 export market, partner identified |
| 5 | proven export revenue or platform/marketplace economics |

**Red flags:** export plan to markets where local compliance blocks distribution

### Risk profile (5 = low risk) (`risk`, weight 6)

| Score | Anchor |
|---:|---|
| 0 | existential risks unmitigated |
| 1 | several high risks, weak mitigants |
| 2 | high risks with plausible mitigants |
| 3 | medium residual risk, mitigants funded |
| 4 | low residual risk, diversified customers & suppliers |
| 5 | minimal residual risk, contractual protections, cash > 24 mo |

**Red flags:** runway < 6 months; > 50% revenue from one customer

## 3. Evidence levels

| Level | Meaning | Confidence | Score band |
|---|---|---:|---|
| A | verified (audited data, signed contracts, logs, peer-reviewed) | 1.00 | ±0 |
| B | credible estimate (pilot data, LOIs, reputable third-party source) | 0.75 | ±0.5 |
| C | assumption / founder claim | 0.40 | ±1.0 |

Overall confidence is the weight-averaged confidence. The range of the total comes from the bands — show it next to the score (e.g. "64/100, range 55–73").

## 4. Grade bands

| Grade | Threshold | Meaning |
|---|---:|---|
| A | ≥ 80 | strong — prioritise / invest |
| B | ≥ 65 | promising — invest with conditions |
| C | ≥ 50 | conditional — close specific gaps first |
| D | ≥ 35 | weak — rework thesis |
| E | ≥ 0 | not viable now |

## 5. Automatic red-flag rules

| id | Type | Severity | Markets | Message |
|---|---|---|---|---|
| `critical_gap` | score_below_with_weight | high | all | Critical gap: a heavily weighted criterion scores ≤ 1 |
| `trl_stage_mismatch` | stage_trl | high | all | Stage claimed (pilot/growth) inconsistent with low TRL score |
| `ltv_cac` | fact_below | high | all | LTV/CAC < 1: growth destroys value |
| `ltv_cac_soft` | fact_below | medium | all | LTV/CAC below 3 |
| `runway` | fact_below | high | all | Runway < 6 months |
| `concentration` | fact_above | medium | all | > 50% of revenue from one customer |
| `registry_gov` | fact_false_for_audience | high | ru | Not eligible for the Russian Software Register while targeting state/critical-infrastructure buyers |
| `low_confidence` | confidence_below | medium | all | Evidence confidence < 60%: most scores rest on assumptions |
| `foreign_dependency` | fact_true | high | all | Critical dependency on an external or restrictable component in the core path |
| `xinchuang_gov` | fact_false_for_audience | high | zh | Not adapted to the domestic IT stack (Xinchuang) while targeting government / SOE buyers |
| `mlps_gov` | fact_false_for_audience | medium | zh | No MLPS 2.0 (Dengbao) assessment for a system sold to government / critical buyers |
| `genai_filing` | fact_true | high | zh | Public-facing generative-AI service without the required algorithm / service filing |
| `cross_border_data` | fact_true | high | zh, ru, en, vn, id, my | Cross-border transfer of personal data without the required assessment / legal basis |
| `enterprise_security` | fact_false_for_audience | medium | en | No SOC 2 / ISO 27001 attestation (or credible plan) while selling to enterprises |
| `fedramp_gov` | fact_false_for_audience | medium | en | Targeting US federal buyers without a FedRAMP authorization path for the cloud offering |
| `ai_risk` | fact_true | medium | en | AI features sold to enterprise or federal buyers without a documented AI risk assessment (e.g. NIST AI RMF) |
| `vn_pdp_dossier` | fact_false_for_audience | medium | vn | No personal-data processing impact assessment dossier (Vietnam PDP Law 91/2025/QH15) |
| `id_pse` | fact_false_for_audience | high | id | Electronic system operator (PSE) registration missing for a service offered in Indonesia |
| `id_tkdn` | fact_false_for_audience | high | id | No TKDN (local content) certificate while targeting government / SOE procurement |
| `my_pdpa` | fact_false_for_audience | medium | my | PDPA 2010 (as amended in 2024) compliance not evidenced (e.g. DPO, breach notification, processor obligations) |

A high-severity flag does not zero the score but must appear on the risk slide and in the report's risk section with a mitigation. Two or more high flags → the recommendation is at most "conditional (C)" regardless of the number.

## 6. Stage profiles (sum = 100)

| Criterion | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Market size & growth | 16 | 14 | 13 | 12 |
| Problem severity & willingness to pay | 16 | 13 | 11 | 8 |
| Product / technology maturity (TRL/УГТ) | 6 | 12 | 11 | 6 |
| Differentiation, moat & IP | 10 | 11 | 10 | 10 |
| Team & execution capability | 16 | 13 | 9 | 8 |
| Traction & evidence | 4 | 7 | 13 | 16 |
| Business model & unit economics | 5 | 6 | 10 | 15 |
| Go-to-market & channels | 7 | 7 | 8 | 10 |
| Regulatory & sovereignty fit | 7 | 7 | 7 | 6 |
| Scalability & export potential | 6 | 5 | 4 | 6 |
| Risk profile (5 = low risk) | 7 | 5 | 4 | 3 |
| **Total** | 100 | 100 | 100 | 100 |

Logic of the shifts: at the idea stage only market, problem and team can be assessed; at pilot the weight moves to evidence (traction, unit economics); at growth to efficiency (unit economics, GTM) while technology risk is largely retired.

## 7. Audience multipliers

The multiplier scales the stage weight; weights are then renormalised to 100.

| Criterion | investor | government | corporate | academic |
|---|---:|---:|---:|---:|
| Market size & growth | 1.2 | 0.9 | 0.8 | 0.7 |
| Problem severity & willingness to pay | 1 | 1 | 1.3 | 1 |
| Product / technology maturity (TRL/УГТ) | 0.9 | 1.2 | 1.3 | 1.3 |
| Differentiation, moat & IP | 1 | 1 | 0.9 | 1.4 |
| Team & execution capability | 1 | 1.1 | 1 | 1.3 |
| Traction & evidence | 1.2 | 1 | 1 | 0.7 |
| Business model & unit economics | 1.3 | 0.6 | 0.8 | 0.5 |
| Go-to-market & channels | 1 | 1 | 1.1 | 0.6 |
| Regulatory & sovereignty fit | 0.8 | 1.6 | 1.2 | 1 |
| Scalability & export potential | 1.2 | 1.1 | 1 | 1 |
| Risk profile (5 = low risk) | 1 | 1.1 | 1 | 1 |

## 8. Effective weights: stage × audience (default market)

Generated by `scoring.py` (`weights_for`). Each column = 100.

### Audience: investor

| Criterion | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Market size & growth | 18.3 | 16.1 | 14.6 | 13.2 |
| Problem severity & willingness to pay | 15.3 | 12.5 | 10.3 | 7.3 |
| Product / technology maturity (TRL/УГТ) | 5.2 | 10.3 | 9.3 | 4.9 |
| Differentiation, moat & IP | 9.6 | 10.5 | 9.4 | 9.1 |
| Team & execution capability | 15.3 | 12.5 | 8.5 | 7.3 |
| Traction & evidence | 4.6 | 8.0 | 14.6 | 17.5 |
| Business model & unit economics | 6.2 | 7.5 | 12.2 | 17.8 |
| Go-to-market & channels | 6.7 | 6.7 | 7.5 | 9.1 |
| Regulatory & sovereignty fit | 5.3 | 5.4 | 5.3 | 4.4 |
| Scalability & export potential | 6.9 | 5.7 | 4.5 | 6.6 |
| Risk profile (5 = low risk) | 6.7 | 4.8 | 3.8 | 2.7 |
| **Total** | 100 | 100 | 100 | 100 |

### Audience: government

| Criterion | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Market size & growth | 13.8 | 12.0 | 11.4 | 10.9 |
| Problem severity & willingness to pay | 15.3 | 12.4 | 10.7 | 8.1 |
| Product / technology maturity (TRL/УГТ) | 6.9 | 13.7 | 12.8 | 7.3 |
| Differentiation, moat & IP | 9.6 | 10.5 | 9.7 | 10.1 |
| Team & execution capability | 16.8 | 13.6 | 9.6 | 8.9 |
| Traction & evidence | 3.8 | 6.7 | 12.6 | 16.1 |
| Business model & unit economics | 2.9 | 3.4 | 5.8 | 9.1 |
| Go-to-market & channels | 6.7 | 6.7 | 7.8 | 10.1 |
| Regulatory & sovereignty fit | 10.7 | 10.7 | 10.9 | 9.7 |
| Scalability & export potential | 6.3 | 5.2 | 4.3 | 6.6 |
| Risk profile (5 = low risk) | 7.4 | 5.2 | 4.3 | 3.3 |
| **Total** | 100 | 100 | 100 | 100 |

### Audience: corporate

| Criterion | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Market size & growth | 12.4 | 10.7 | 10.1 | 9.6 |
| Problem severity & willingness to pay | 20.1 | 16.2 | 13.9 | 10.4 |
| Product / technology maturity (TRL/УГТ) | 7.5 | 14.9 | 13.9 | 7.8 |
| Differentiation, moat & IP | 8.7 | 9.5 | 8.7 | 9.0 |
| Team & execution capability | 15.5 | 12.4 | 8.7 | 8.0 |
| Traction & evidence | 3.9 | 6.7 | 12.6 | 16.0 |
| Business model & unit economics | 3.9 | 4.6 | 7.8 | 12.0 |
| Go-to-market & channels | 7.4 | 7.4 | 8.5 | 11.0 |
| Regulatory & sovereignty fit | 8.1 | 8.0 | 8.1 | 7.2 |
| Scalability & export potential | 5.8 | 4.8 | 3.9 | 6.0 |
| Risk profile (5 = low risk) | 6.8 | 4.8 | 3.9 | 3.0 |
| **Total** | 100 | 100 | 100 | 100 |

### Audience: academic

| Criterion | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Market size & growth | 11.3 | 9.8 | 9.7 | 9.5 |
| Problem severity & willingness to pay | 16.1 | 13.0 | 11.7 | 9.1 |
| Product / technology maturity (TRL/УГТ) | 7.9 | 15.6 | 15.2 | 8.8 |
| Differentiation, moat & IP | 14.1 | 15.4 | 14.9 | 15.9 |
| Team & execution capability | 20.9 | 16.9 | 12.4 | 11.8 |
| Traction & evidence | 2.8 | 4.9 | 9.7 | 12.7 |
| Business model & unit economics | 2.5 | 3.0 | 5.3 | 8.5 |
| Go-to-market & channels | 4.2 | 4.2 | 5.1 | 6.8 |
| Regulatory & sovereignty fit | 7.0 | 7.0 | 7.4 | 6.8 |
| Scalability & export potential | 6.0 | 5.0 | 4.3 | 6.8 |
| Risk profile (5 = low risk) | 7.0 | 5.0 | 4.3 | 3.4 |
| **Total** | 100 | 100 | 100 | 100 |

## 9. Deck section weights by audience (sum = 100)

Used by `allocate_slides()` to allocate slides and speaking time.

| Section | investor | government | corporate | academic |
|---|---:|---:|---:|---:|
| Executive answer / thesis | 8 | 8 | 8 | 8 |
| Problem & why now | 8 | 10 | 12 | 10 |
| Solution / product & demo | 8 | 7 | 12 | 8 |
| Market sizing | 10 | 6 | 4 | 4 |
| Technology & TRL | 4 | 10 | 10 | 16 |
| Traction & evidence | 12 | 5 | 8 | 4 |
| Business model & unit economics | 10 | 3 | 6 | 2 |
| Competition & moat | 7 | 5 | 5 | 8 |
| Go-to-market | 6 | 4 | 6 | 2 |
| Financial plan & returns | 10 | 6 | 4 | 3 |
| Team | 7 | 8 | 5 | 10 |
| Regulation & sovereignty | 2 | 12 | 7 | 4 |
| Risks & mitigants | 3 | 6 | 5 | 6 |
| Roadmap & milestones | 2 | 7 | 5 | 10 |
| Ask / decision required | 3 | 3 | 3 | 5 |
| **Total** | 100 | 100 | 100 | 100 |

## 10. Market profiles

Each profile multiplies the listed weights (then renormalises), replaces the definition and anchors of the regulation criterion and lists the compliance facts read by red-flag rules. Legal status verified 2026-10-20; re-check before use.

| id | Markets | Currency | Weight multipliers | Compliance facts | Guide |
|---|---|---|---|---|---|
| `ru` | Russia | RUB | regulatory ×1.15 | `registry_eligible`, `critical_foreign_dependency`, `cross_border_data_unassessed` | [markets/ru.md](markets/ru.md) |
| `en` | United States | USD | regulatory ×0.85 | `security_attestation`, `fedramp_path`, `ai_risk_unassessed`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/en.md](markets/en.md) |
| `zh` | Mainland China | CNY | regulatory ×1.25, gtm ×1.1 | `xinchuang_adapted`, `mlps_certified`, `genai_filing_missing`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/zh.md](markets/zh.md) |
| `vn` | Vietnam | VND | regulatory ×1.15, gtm ×1.05 | `pdp_impact_assessment`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/vn.md](markets/vn.md) |
| `id` | Indonesia | IDR | regulatory ×1.15, gtm ×1.1 | `pse_registered`, `tkdn_certified`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/id.md](markets/id.md) |
| `my` | Malaysia | MYR | regulatory ×1 | `pdpa_compliant`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/my.md](markets/my.md) |

### `ru` — Regulation & technological sovereignty (RU)

**Definition of the regulation & sovereignty criterion.** Unified Register of Russian Software (Government Decree No. 1236 of 16.11.2015), personal-data law 152-FZ (incl. localisation), critical information infrastructure law 187-FZ (KII), FSTEC/FSB certification where applicable, public procurement under 44-FZ / 223-FZ.

| Score | Anchor |
|---:|---|
| 0 | blocked: dependency on unavailable/foreign components with no substitute |
| 1 | major compliance gaps |
| 2 | compliance path known, not started |
| 3 | in progress (registry application, 152-FZ compliance), domestic stack |
| 4 | in the Russian Software Register; meets data & security requirements of target buyers |
| 5 | registry + certifications + listed in import-substitution / industrial programmes |

### `en` — Regulatory, security & compliance fit (US)

**Definition of the regulation & sovereignty criterion.** State privacy laws (e.g. California CCPA as amended by the CPRA), SOC 2 / ISO/IEC 27001 attestations expected by enterprise buyers, FedRAMP for cloud services sold to US federal agencies, AI risk management (voluntary NIST AI RMF), sector rules (e.g. HIPAA).

| Score | Anchor |
|---:|---|
| 0 | blocked: product cannot meet a mandatory requirement of the target segment (e.g. sector rule) |
| 1 | major gaps (no privacy programme or service-provider terms, no security programme) |
| 2 | compliance roadmap defined, not started |
| 3 | privacy programme in place, SOC 2 Type I / ISO 27001 in progress |
| 4 | SOC 2 Type II or ISO 27001 certified; AI risk assessment documented |
| 5 | certifications + FedRAMP / sector authorizations; compliance used as a sales advantage |

### `zh` — Compliance & self-reliance (CN)

**Definition of the regulation & sovereignty criterion.** Cybersecurity Law (2016), Data Security Law (2021), Personal Information Protection Law (PIPL, 2021) incl. cross-border transfer rules; Interim Measures for Generative AI Services (2023) and algorithm filing; MLPS 2.0 (Dengbao, GB/T 22239-2019); Xinchuang adaptation to domestic chips/OS/databases for government and SOE buyers.

| Score | Anchor |
|---:|---|
| 0 | blocked: core dependency that cannot be offered in mainland China, or data must leave China without a lawful route |
| 1 | major gaps (no PIPL basis, no MLPS assessment) |
| 2 | compliance path known, not started |
| 3 | PIPL compliance in place; MLPS assessment / algorithm filing in progress; Xinchuang adaptation started |
| 4 | MLPS level met, filings completed, Xinchuang compatibility certified with major domestic stacks |
| 5 | full compliance + listed in government / industry catalogues; aligned with policy programmes |

### `vn` — Regulation & digital sovereignty (VN)

**Definition of the regulation & sovereignty criterion.** Law on Personal Data Protection No. 91/2025/QH15 (in force 1 Jan 2026; detailed by Decree 356/2025/ND-CP, which replaced Decree 13/2023/ND-CP) incl. impact-assessment dossiers for processing and cross-border transfer; Law on Cybersecurity No. 116/2025/QH15 (in force 1 Jul 2026, replacing the 2018 Cybersecurity Law and the 2015 Law on Cyberinformation Security) incl. information-system security levels; Law on Digital Technology Industry No. 71/2025/QH15 (incentives for digital-technology products and enterprises); Law on Artificial Intelligence No. 134/2025/QH15; public procurement under the Law on Bidding No. 22/2023/QH15.

| Score | Anchor |
|---:|---|
| 0 | blocked: data or core component cannot lawfully be used/processed for the target customers |
| 1 | major gaps (no PDP impact-assessment dossier, no security-level classification) |
| 2 | compliance path known, not started |
| 3 | PDP dossiers prepared; information-system security level determined; local deployment option |
| 4 | PDP and cybersecurity obligations met for target buyers; recognised as a digital-technology product/enterprise where relevant |
| 5 | full compliance + listed in national / ministry digital-transformation programmes |

### `id` — Regulation, local content & sovereignty (ID)

**Definition of the regulation & sovereignty criterion.** Personal Data Protection Law No. 27/2022 (UU PDP; two-year adjustment period ended Oct 2024); registration as an electronic system operator (PSE) under MR 5/2020 via OSS with the Ministry of Communication and Digital (Komdigi, formerly Kominfo); GR 71/2019 on electronic systems (data-placement rules for public-scope operators); local content (TKDN) certification for government and SOE procurement (Perpres 46/2025, Permenperin 35/2025).

| Score | Anchor |
|---:|---|
| 0 | blocked: cannot register as PSE or meet data-placement rules for target buyers |
| 1 | major gaps (no UU PDP programme, no PSE registration) |
| 2 | compliance path known, not started |
| 3 | PSE registered; UU PDP programme in place; TKDN assessment started |
| 4 | TKDN certified at the level required by target tenders; data and security requirements met |
| 5 | full compliance + listed in e-catalogue / government programmes |

### `my` — Regulation & digital trust (MY)

**Definition of the regulation & sovereignty criterion.** Personal Data Protection Act 2010 (Act 709) as amended by Act A1727 (2024; phased commencement 1 Jan, 1 Apr and 1 Jun 2025): data controllers and processors, DPO appointment, breach notification, data portability, cross-border transfer; Cyber Security Act 2024 (Act 854, in force 26 Aug 2024) for national critical information infrastructure (NCII) entities, overseen by NACSA; sector rules (e.g. Bank Negara Malaysia RMiT for financial institutions); Malaysia Digital (MD, formerly MSC Malaysia) status for incentives.

| Score | Anchor |
|---:|---|
| 0 | blocked: cannot meet a mandatory requirement of the target sector (e.g. NCII or RMiT obligations) |
| 1 | major gaps (no PDPA programme, no security controls) |
| 2 | compliance path known, not started |
| 3 | PDPA programme incl. DPO and breach process; security controls in progress |
| 4 | meets PDPA, sector (e.g. RMiT) and NCII-customer requirements; MD status where relevant |
| 5 | full compliance + certifications + listed in government / GLC digital programmes |

## 11. Reading and defending the score

* **Show the range, not only the point.** "64/100 (range 55–73, confidence 75%)" is more honest
  and more convincing than "64".
* **Lead with the gaps.** The scorecard slide ends with a conclusion: "main gaps are traction and
  unit economics; two contract renewals close them".
* **A score is not a decision.** The grade is a recommendation; state which facts would change it.
* **Calibration.** On first use in an organisation, score 3–5 known projects (successes and
  failures) and check the model separates them. If not, adjust anchors, not weights.
* **Two raters.** For important decisions two people score independently; a gap > 1 point on a
  criterion is a reason to discuss the evidence.

## 12. Changing the model

* New criteria go to `criteria` with a weight; then update all `stage_profiles` so each column
  sums to 100 (a test checks it).
* Audience and market multipliers express relative emphasis (0.5–1.6); do not use 0.
* After any change: `python -m unittest discover -s tools/tests` and `python tools/gen_scoring_doc.py`.
