# Market guides

One guide per **market profile** (a country or region, not a language). The locale of a document
(`ru`, `en`, `zh`, `vi`, `id`, `ms`) controls formatting; the market profile (`ru`, `en`, `zh`,
`vn`, `id`, `my`) controls the scoring weights, the definition of the *Regulation & sovereignty*
criterion and the red-flag rules (`config/scoring_model.json` → `market_profiles`).

| Profile | Guide | Default locale | Currency |
|---|---|---|---|
| `ru` Russia | [ru.md](ru.md) | ru | RUB |
| `en` United States | [en.md](en.md) | en | USD |
| `zh` Mainland China | [zh.md](zh.md) | zh | CNY |
| `vn` Vietnam | [vn.md](vn.md) | vi | VND |
| `id` Indonesia | [id.md](id.md) | id | IDR |
| `my` Malaysia | [my.md](my.md) | ms (en is common in business) | MYR |

Each guide covers: statistics and data sources, regulation and sovereignty criteria, discount
rate / inflation handling and valuation norms, audience and presentation culture, banned/hype
phrases and pitch-length norms.

**Rules for these guides.** Facts must be real and stable. Volatile numbers (policy rates,
inflation, yields) are either omitted or given with a date and a source link. Laws change: each
legal reference below was checked against an official or reliable source on the date shown, and
must be re-checked before use in a real document. Nothing here is legal advice.

Last verification of links and legal status: **2026-10-20**.
