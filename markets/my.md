# Market guide: Malaysia (`my`)

Default locale `ms` (Bahasa Melayu; English is widely used in business and finance) · currency
MYR (RM … juta / bilion; comma thousands, dot decimal) · citations APA 7 · verified 2026-10-20.

## 1. Statistics and data sources

| Need | Source | Link |
|---|---|---|
| Official statistics (GDP, CPI, establishments) | Department of Statistics Malaysia (DOSM) | https://www.dosm.gov.my/ |
| OPR, exchange rates, financial statistics; RMiT | Bank Negara Malaysia (BNM) | https://www.bnm.gov.my/ |
| Communications and multimedia regulation | MCMC | https://www.mcmc.gov.my/ |
| Digital economy, Malaysia Digital status | MDEC | https://mdec.my/ |
| Cyber security, NCII | National Cyber Security Agency (NACSA) | https://nacsa.gov.my/ |
| Personal data protection | Jabatan Perlindungan Data Peribadi (JPDP) | https://www.pdp.gov.my/ |
| Capital markets | Securities Commission Malaysia | https://www.sc.com.my/ |
| Federal government procurement | ePerolehan (Ministry of Finance) | https://www.eperolehan.gov.my/ |

## 2. Regulation and sovereignty (definition of the criterion)

For this profile the criterion measures PDPA compliance, readiness for regulated customers
(financial institutions, NCII entities) and eligibility for government and GLC procurement.

* **Personal data.** Personal Data Protection Act 2010 (Act 709) as amended by the Personal Data
  Protection (Amendment) Act 2024 (Act A1727); provisions commenced on 1 January, 1 April and
  1 June 2025 (https://www.pdp.gov.my/ppdpv1/en/akta/personal-data-protection-amendment-act-2024/).
  Key changes include direct obligations for data processors, data breach notification, data
  protection officers and data portability.
* **Cyber security.** Cyber Security Act 2024 (Act 854), in force 26 August 2024, for national
  critical information infrastructure (NCII) entities (https://nacsa.gov.my/act854.php).
* **Financial institutions.** BNM policy document Risk Management in Technology (RMiT)
  (https://www.bnm.gov.my/-/pd-rmit-nov25): technology risk, cloud, third-party and cyber
  requirements that vendors to banks must support.
* **Malaysia Digital (MD) status.** The former MSC Malaysia status has been replaced by Malaysia
  Digital status administered by MDEC (https://www.mdec.my/malaysiadigital/tax-incentive);
  check eligibility and incentives on the MDEC site.
* **Government procurement.** Suppliers register with the Ministry of Finance through
  ePerolehan; procurement rules include preferences for Bumiputera companies at certain value
  thresholds — check the current Treasury circulars.

Scoring facts: `pdpa_compliant`, `cross_border_data_unassessed`, `critical_foreign_dependency`.

## 3. Discount rate, inflation, valuation

* Risk-free proxy: Malaysian Government Securities (MGS) yield of matching tenor; OPR from BNM
  as the policy reference. Date and link every value.
* CPI from DOSM; state nominal vs real.
* Use *juta* and *bilion* in Malay documents (RM36 juta, RM3.0 bilion); in English documents
  "RM36 million" / "RM3.0 billion". Give USD in brackets with the BNM rate and date for foreign
  investors.
* The example uses 18% (illustrative) for a venture-stage MYR discount rate.

## 4. Audience and presentation culture

* **Government agencies.** Bahasa Melayu for official submissions, English acceptable in
  technical annexes; alignment with national digital policies; local presence and support.
* **GLCs and GLICs** (government-linked companies and investment companies). Governance,
  compliance (PDPA, RMiT for financial groups, Act 854 for NCII), vendor registration and
  references from comparable groups. Expect formal procurement and committee approvals.
* **Investors.** Regional and Malaysian VCs; Bursa Malaysia listing paths (ACE / LEAP markets) are
  often discussed; show unit economics and regional expansion.

## 5. Banned and hype phrases, pitch length

`config/banned_phrases.json` → `ms`: "satu-satunya di dunia", "tiada tandingan", "tiada
pesaing", "terbaik di dunia", "revolusioner", "dijamin", "pasti untung", "tanpa risiko" and
others; "peneraju pasaran", "terbesar", "pertama di Malaysia" only with a source.
Typical length: 10–15 slides for investors; government and GLC briefings 15–20 slides plus a
written proposal.
