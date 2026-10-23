# Market guide: Indonesia (`id`)

Default locale `id` · currency IDR (Rp … juta / miliar / triliun; dot thousands, comma decimal) ·
citations APA 7 · verified 2026-10-20.

## 1. Statistics and data sources

| Need | Source | Link |
|---|---|---|
| Official statistics (GDP, inflation, enterprises) | Badan Pusat Statistik (BPS) | https://www.bps.go.id/ |
| BI-Rate, exchange rates, payment statistics | Bank Indonesia (BI) | https://www.bi.go.id/ |
| Financial-sector supervision (banks, insurers, fintech) | Otoritas Jasa Keuangan (OJK) | https://www.ojk.go.id/ |
| Digital and telecom policy, PSE registration (Kominfo was renamed Komdigi by Perpres 174/2024, effective 5 Nov 2024) | Kementerian Komunikasi dan Digital (Komdigi) | https://www.komdigi.go.id/ |
| Legal texts | JDIH BPK | https://peraturan.bpk.go.id/ |
| Government procurement, e-catalogue | LKPP | https://www.lkpp.go.id/ |

Some Indonesian government sites block automated requests; a failed fetch is not evidence that a
page does not exist.

## 2. Regulation and sovereignty (definition of the criterion)

For this profile the criterion measures readiness to operate as a registered electronic system
provider, process Indonesian personal data and qualify for government procurement with local
content.

* **Personal data protection.** UU No. 27 Tahun 2022 (PDP Law,
  https://peraturan.bpk.go.id/Details/229798/uu-no-27-tahun-2022); the two-year adjustment period
  ended on 17 October 2024.
* **PSE registration.** Permenkominfo No. 5 Tahun 2020 on private-scope electronic system
  providers (https://jdih.komdigi.go.id/produk_hukum/unduh/id/759/t/peraturan+menteri+komunikasi+dan+informatika+nomor+5+tahun+2020);
  registration through the OSS system.
* **Data location for public scope.** PP No. 71 Tahun 2019, Article 20(2): public-scope
  electronic system providers must manage, process and store systems and data in Indonesia,
  with limited exceptions (https://jdih.komdigi.go.id/index.php/produk_hukum/view/id/695/t/peraturan+pemerintah+nomor+71+tahun+2019).
* **Local content (TKDN).** Perpres No. 46 Tahun 2025 (second amendment of the government
  procurement regulation) requires buyers to prioritise domestic products; where products with
  TKDN + BMP of at least 40% exist, products with TKDN of at least 25% must be chosen. TKDN
  certification procedures: Permenperin No. 35 Tahun 2025, in force 11 December 2025
  (https://peraturan.bpk.go.id/Details/333003/permenperin-no-35-tahun-2025).
* **Sector rules.** Banks and other financial institutions are supervised by OJK, which issues
  its own IT and outsourcing rules.

Scoring facts: `pse_registered`, `tkdn_certified`, `cross_border_data_unassessed`,
`critical_foreign_dependency`.

## 3. Discount rate, inflation, valuation

* Risk-free proxy: Indonesian government bond (SUN) yield of matching tenor; BI-Rate from Bank
  Indonesia as the policy reference. Date and link every value.
* Inflation from BPS; state nominal vs real.
* IDR figures are large: use *miliar* for company figures and *triliun* for markets; give USD in
  brackets with the BI reference rate (JISDOR) and its date.
* Rupiah cash flows require a rupiah discount rate (or a USD rate plus country risk premium and an
  explicit FX path). The example uses 22% (illustrative).

## 4. Audience and presentation culture

* **Government (kementerian/lembaga, pemda).** Bahasa Indonesia, formal register, regulation
  references by number and year (e.g. "UU 27/2022"), alignment with national programmes, local
  content and local data centres. Expect several meetings and a written proposal.
* **BUMN (state-owned enterprises).** Since 2025 SOEs are managed through Danantara (Badan
  Pengelola Investasi Daya Anagata Nusantara, established by UU No. 1 Tahun 2025,
  https://peraturan.bpk.go.id/Download/375602/UU%20Nomor%201%20Tahun%202025.pdf). Holding
  structures, procurement procedures and TKDN matter as much as the product.
* **Investors.** Regional VCs look for scale across Indonesia's large and diverse market, a
  path to profitability and governance quality.

## 5. Banned and hype phrases, pitch length

`config/banned_phrases.json` → `id`: "satu-satunya di dunia", "tanpa pesaing", "terbaik di
dunia", "revolusioner", "disruptif", "dijamin", "pasti untung", "tanpa risiko", "pasar raksasa"
and others; "pemimpin pasar", "terbesar", "pertama di Indonesia" only with a source.
Typical length: 10–15 slides for investors; government presentations are often longer and
accompanied by a written proposal.
