# Market guide: United States (`en`)

Default locale `en` · currency USD · citations APA 7 (default) or
Chicago author-date · verified 2026-10-20.

## 1. Statistics and data sources

| Need | Source | Link |
|---|---|---|
| GDP, industry accounts (US) | Bureau of Economic Analysis | https://www.bea.gov/ |
| CPI, wages (US) | Bureau of Labor Statistics | https://www.bls.gov/cpi/ |
| Business counts by industry (US) | U.S. Census Bureau | https://www.census.gov/ |
| Policy rate, economic data (US) | Federal Reserve | https://www.federalreserve.gov/ |
| Treasury yields (risk-free rate) | U.S. Department of the Treasury | https://home.treasury.gov/ |
| Country risk premia (method and data) | NYU Stern School of Business (public datasets) | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html |
| Company filings | SEC EDGAR | https://www.sec.gov/ |

## 2. Regulation and sovereignty (definition of the criterion)

For this profile the criterion measures readiness for enterprise and public-sector procurement in
the United States:

* **Privacy**: there is no single federal data-protection statute; state laws apply, e.g. the
  California Consumer Privacy Act as amended by the CPRA (https://oag.ca.gov/privacy/ccpa,
  https://cppa.ca.gov/). Check which state laws cover the target customers and their data.
* **AI risk management**: the voluntary NIST AI Risk Management Framework, AI RMF 1.0 (NIST AI
  100-1, 2023; https://www.nist.gov/itl/ai-risk-management-framework), is a common reference for
  enterprise and federal buyers. Federal AI policy changes; cite the current document and date.
* **Security attestations** expected by enterprise buyers: SOC 2
  (https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2) and/or
  ISO/IEC 27001.
* **US federal cloud**: FedRAMP authorization (https://www.fedramp.gov/).
* **Sector rules** where relevant, e.g. HIPAA for health data (https://www.hhs.gov/hipaa/index.html).

Scoring facts: `security_attestation`, `fedramp_path`, `ai_risk_unassessed`,
`cross_border_data_unassessed`, `critical_foreign_dependency`.

## 3. Discount rate, inflation, valuation

* Risk-free rate: Treasury yield with a maturity close to the horizon,
  dated and linked. Do not hard-code it in templates.
* Venture-stage discount rates are far above the risk-free rate; document the build-up. The
  example uses 20% as an illustrative assumption.
* Inflation: CPI (BLS) or PCE price index (BEA); state whether figures are nominal or real.
* Benchmarks commonly used by investors: Rule of 40 (https://feld.com/archives/2015/02/rule-40-healthy-saas-company/),
  burn multiple (https://www.craftventures.com/articles/the-burn-multiple), LTV/CAC, CAC payback,
  NRR. Present them as benchmarks, not as laws.
* Show IRR and MOIC together and state entry valuation, dilution and exit assumptions.

## 4. Audience and presentation culture

* **Investors.** Answer-first, 10–15 slides, a clear ask; traction and unit economics carry more
  weight than technology description. A one-page memo is often read before the meeting.
* **Enterprise buyers.** Security questionnaire readiness, integration effort, total cost of
  ownership, references.
* **Public sector.** Compliance with procurement frameworks (FedRAMP, state procurement rules),
  accessibility and data residency.
* Enterprise and federal audiences expect explicit treatment of data protection and AI risk.

## 5. Banned and hype phrases, pitch length

`config/banned_phrases.json` → `en`: "unique", "revolutionary", "disruptive", "game changer",
"guaranteed", "100% accurate", "huge market", "conservative estimate" and others; "market
leader", "largest", "the first" only with a source. Typical pitch: 10–15 slides, 10–20 minutes,
plus appendix.
