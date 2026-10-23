# Market guide: Vietnam (`vn`)

Default locale `vi` · currency VND (triệu / tỷ / nghìn tỷ ₫; dot thousands, comma decimal) ·
citations APA 7 · verified 2026-10-20.

## 1. Statistics and data sources

| Need | Source | Link |
|---|---|---|
| Official statistics (GDP, CPI, enterprises). The former General Statistics Office (GSO) now operates as the Statistics Office (Cục Thống kê) under the Ministry of Finance | Statistics Office / NSO | https://www.nso.gov.vn/en/homepage/ |
| Policy rates, exchange rates, banking statistics | State Bank of Vietnam (SBV) | https://www.sbv.gov.vn/ |
| ICT and digital-industry policy (former MIC functions merged into MST from 01/03/2025) | Ministry of Science and Technology (MST) | https://mst.gov.vn/ |
| Fiscal data, government bonds | Ministry of Finance | https://www.mof.gov.vn/ |
| Legal texts (official gazette) | Công báo Chính phủ · Hệ thống văn bản Chính phủ | https://congbao.chinhphu.vn/ · https://vanban.chinhphu.vn/ |
| Public procurement | National e-procurement system | https://muasamcong.mpi.gov.vn/ |

## 2. Regulation and sovereignty (definition of the criterion)

For this profile the criterion measures readiness to process Vietnamese personal data, meet
cybersecurity and data-location rules and be procured by state bodies and SOEs.

* **Personal data protection.** Law on Personal Data Protection No. 91/2025/QH15, adopted
  26/06/2025, in force 01/01/2026 (https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm),
  detailed by Decree 356/2025/NĐ-CP (https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-356-2025-nd-cp-468371.htm).
  Decree 13/2023/NĐ-CP, the earlier PDP decree, was replaced from 01/01/2026. Impact-assessment
  dossiers for processing and for cross-border transfer are the key artefacts to prepare.
* **Cybersecurity.** The Cybersecurity Law 2018 (No. 24/2018/QH14) and the Law on Network
  Information Security 2015 (No. 86/2015/QH13) are replaced by the **Cybersecurity Law
  No. 116/2025/QH15**, passed 10/12/2025, in force **01/07/2026**
  (https://vanban.chinhphu.vn/?classid=1&docid=216499&pageid=27160&typegroupid=3;
  https://en.mps.gov.vn/article/national-assembly-passes-law-on-cybersecurity-1765507574).
  Under the 2018 law, Decree 53/2022/NĐ-CP set data-localisation requirements
  (https://mst.gov.vn/van-ban-phap-luat/24998.htm); check which implementing decrees apply under
  the new law. Network security functions now sit with the Ministry of Public Security.
* **Digital technology industry.** Law on Digital Technology Industry No. 71/2025/QH15, adopted
  14/06/2025, in force 01/01/2026, with some articles from 01/07/2025
  (https://mst.gov.vn/van-ban-phap-luat/25224.htm): incentives for digital technology products,
  including AI, and for domestic enterprises.
* **Artificial intelligence.** Law on Artificial Intelligence No. 134/2025/QH15, in force
  01/03/2026; check risk classification and obligations for your use case.
* **Procurement.** Law on Bidding No. 22/2023/QH15 (https://vanban.chinhphu.vn/?docid=208419&pageid=27160),
  amended since; use the consolidated text.

Scoring facts: `pdp_impact_assessment`, `cross_border_data_unassessed`,
`critical_foreign_dependency`.

## 3. Discount rate, inflation, valuation

* Risk-free proxy: Vietnamese government bond yield of matching tenor (Ministry of Finance / HNX
  data), dated and linked; policy rates from the SBV. Do not hard-code values.
* CPI from the Statistics Office; state nominal vs real; ARPA indexation should cover inflation.
* VND cash flows need a VND discount rate; a USD rate plus a country risk premium (see the
  NYU Stern public datasets, https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html)
  is an acceptable cross-check, with the FX assumption stated. The example uses 22%
  (illustrative).
* Show amounts in tỷ ₫ for company-level figures and nghìn tỷ ₫ for markets; give USD in
  brackets for foreign investors with the SBV reference rate and its date.

## 4. Audience and presentation culture

* **Government bodies.** Formal Vietnamese, official names and numbers of legal documents,
  alignment with national digital-transformation programmes, a clear statement of where data is
  stored and who operates the system. Decisions are typically consensus-based; send the report in
  advance.
* **SOEs (state-owned groups, state banks, telecoms, energy).** Compliance and security first,
  local partner and support capacity, references from comparable SOEs, phased pilots.
* **Investors.** Regional VCs and corporate investors expect a Southeast Asia expansion story,
  unit economics in USD and VND, and a realistic path to profitability.
* Bilingual decks (Vietnamese + English) are common with foreign stakeholders.

## 5. Banned and hype phrases, pitch length

`config/banned_phrases.json` → `vi`: "độc nhất vô nhị", "không có đối thủ", "tốt nhất thế
giới", "mang tính cách mạng", "chưa từng có", "đảm bảo 100%", "không rủi ro", "thị trường khổng
lồ" and others; "dẫn đầu thị trường", "lớn nhất", "đầu tiên tại Việt Nam" only with a source.
Typical length: 10–15 slides for investors; 15–20 slides plus a written report for government.
