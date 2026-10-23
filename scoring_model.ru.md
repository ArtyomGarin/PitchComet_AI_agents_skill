# Модель оценки потенциала развития

Языки: [English](scoring_model.md) · **Русский** · [简体中文](scoring_model.zh-CN.md)

> Генерируется из `config/scoring_model.json` командой `python tools/gen_scoring_doc.py`. Правьте JSON, затем перегенерируйте.

## Зачем модель и как ей пользоваться

Модель переводит качественные суждения о продукте в **сопоставимое число 0–100** с диапазоном
неопределённости и списком красных флагов. Это дисциплина, а не «истина»: у каждого балла есть
якорь (что именно означает «3» по критерию) и уровень доказательности (A/B/C).

1. Определите **стадию** (`idea` / `prototype` / `pilot` / `growth`) по фактам: идея — нет
   работающего артефакта; прототип — УГТ 4–6, нет платящих пользователей; пилот — 1+ внешний
   пилот, первые деньги или LOI; рост — повторяемые продажи, ARR и удержание измеряются ежемесячно.
2. Определите **аудиторию** (`investor` / `government` / `corporate` / `academic`): она меняет веса
   (§7) и структуру деки (§9, `deck_structure.md`).
3. Определите **профиль рынка** (`ru`, `en`, `zh`, `vn`, `id`, `my`; по умолчанию — из локали). Он
   умножает часть весов, переопределяет критерий «Регуляторика и суверенитет» и включает
   рыночные красные флаги (§10, `markets/*.md`).
4. Заполните `scoring_input.json` (`templates/<locale>/` или `python tools/scoring.py template`):
   балл 0–5 (допустимы половинки), уровень доказательности, обоснование с фактом и ссылкой.
5. Запустите `python tools/scoring.py --input scoring_input.json --locale ru [--market ru]`.
   `run_pipeline.py` дополнительно считает все четыре профиля аудитории.

Формула: `Итог = Σ (вес_i × балл_i / 5)`, веса = профиль стадии × множитель аудитории × множитель
рынка, нормированные к 100. Диапазон: `Σ вес_i × (балл_i ± полоса_i) / 5`, полоса A = 0, B = 0,5,
C = 1,0.

## 1. Базовые веса (сумма = 100) и обоснование

| # | id | Критерий | Вес | Обоснование (EN) |
|---|---|---|---:|---|
| 1 | `market` | Размер и рост рынка | **14** | Caps the upside; every audience asks 'how big can this get'. Highest single weight because every other criterion is multiplied by the size of the prize. Absolute SAM thresholds are set per market profile (currency-specific). |
| 2 | `problem` | Острота проблемы и готовность платить | **12** | Painful, budgeted problems shorten sales cycles; 'nice-to-have' kills B2B and B2G products regardless of tech quality. |
| 3 | `trl` | Зрелость продукта и технологии (УГТ/TRL) | **10** | Separates research from product. Mapped to the TRL scale (and national equivalents, e.g. ГОСТ Р 58048-2017 in Russia) so that grant committees and corporates read it the same way. |
| 4 | `moat` | Отличие, защищённость, ИС | **10** | Determines whether margins survive competition from big platforms and open-source models. |
| 5 | `team` | Команда и способность исполнять | **10** | Early-stage outcomes track team quality; government and academic audiences also weigh institutional backing. |
| 6 | `traction` | Тракшн и доказательства | **10** | Converts claims into evidence: users, revenue, pilots, LOIs, retention. |
| 7 | `unit_economics` | Бизнес-модель и юнит-экономика | **9** | Shows growth will create rather than burn value: gross margin, LTV/CAC, payback. |
| 8 | `gtm` | Выход на рынок и каналы | **7** | B2B/B2G sales cycles are long; a named channel (integrator, marketplace, procurement route) matters more than ads. |
| 9 | `regulatory` | Регуляторика и технологический суверенитет | **7** | Data-protection, security certification and supply-chain sovereignty requirements are entry tickets for public-sector, regulated and critical-infrastructure buyers. The concrete regimes differ by market and are defined in market_profiles. |
| 10 | `scalability` | Масштабируемость и экспорт | **5** | Measures the option value beyond the first market: replicability across sectors and accessible export markets (defined per market profile). |
| 11 | `risk` | Профиль рисков (5 = низкий риск) | **6** | Inverse criterion: concentration, dependency, technology, financing and regulatory risk after mitigants. |
| | | **Итого** | **100** | |

## 2. Шкала 0–5 с якорями

Шкала: 0 — нет подтверждений / отсутствует; 5 — лучший в классе, с проверяемыми доказательствами. Допустимы половинные баллы.

### Размер и рост рынка (`market`, вес 14)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | нет платящего рынка | no identifiable paying market |
| 1 | очень малый SAM или рынок сжимается | very small SAM or shrinking market |
| 2 | малый SAM, рост < 5%/год | small SAM, growth < 5%/yr |
| 3 | средний SAM, рост 5–15% | mid-size SAM, growth 5–15% |
| 4 | крупный SAM или рост 15–30%, подтверждено снизу вверх | large SAM or growth 15–30%, bottom-up confirmed |
| 5 | очень крупный SAM и рост > 20%, триангуляция сверху и снизу | very large SAM and growth > 20%, triangulated top-down + bottom-up |

**Красные флаги:** TAM quoted from a generic 'global AI market' figure; no bottom-up check; CAGR from a single press release

### Острота проблемы и готовность платить (`problem`, вес 12)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | проблема не проверена | problem not validated |
| 1 | единичные свидетельства, нет владельца бюджета | anecdotal pain, no budget owner |
| 2 | боль подтверждена < 10 интервью, бюджет неясен | pain confirmed in < 10 interviews, unclear budget |
| 3 | ≥ 20 интервью, известен владелец бюджета, оценена стоимость обходных решений | ≥ 20 interviews, named budget owner, workaround cost quantified |
| 4 | клиенты уже платят за обходные решения; потери > 10× цены | customers pay for workarounds today; quantified loss > 10x price |
| 5 | критично для миссии / требование регулятора; клиенты предоплачивают или софинансируют | mission-critical / regulatory mandate; customers pre-pay or co-fund |

**Красные флаги:** problem described only in the team's words; buyer ≠ user and buyer not interviewed

### Зрелость продукта и технологии (УГТ/TRL) (`trl`, вес 10)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | УГТ 1–2: только концепция | TRL 1–2: concept only |
| 1 | УГТ 3: подтверждена работоспособность (PoC) | TRL 3: proof of concept |
| 2 | УГТ 4–5: проверка в условиях, близких к реальным | TRL 4–5: validation in a relevant environment |
| 3 | УГТ 6: прототип на реальных данных | TRL 6: prototype demonstrated with real data |
| 4 | УГТ 7–8: система в эксплуатации у заказчика, квалифицирована | TRL 7–8: system in customer operation, qualified |
| 5 | УГТ 9: штатная эксплуатация у нескольких заказчиков | TRL 9: proven in routine operation at several customers |

**Красные флаги:** demo is scripted / not on customer data; claimed TRL above evidence

### Отличие, защищённость, ИС (`moat`, вес 10)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | товарный продукт, легко копируется | commodity; easily replicated |
| 1 | отличия на уровне функций | feature-level difference only |
| 2 | лучше по 1–2 измеренным параметрам | better on 1–2 measured dimensions vs. alternatives |
| 3 | измеренное преимущество + собственные данные или встроенность в процессы | measured advantage + proprietary data or workflow lock-in |
| 4 | несколько взаимоусиливающих барьеров (данные, интеграции, сертификаты, зарегистрированная ИС) | several reinforcing moats (data, integrations, certifications, registered IP) |
| 5 | структурный барьер: сетевые эффекты / эксклюзивные данные / позиция, закреплённая регулированием | structural moat: network effects / exclusive data / regulation-backed position |

**Красные флаги:** thin wrapper over a third-party model without a proprietary data advantage; 'no competitors' claim

### Команда и способность исполнять (`team`, вес 10)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | нет выделенной команды | no dedicated team |
| 1 | частичная занятость, нет ключевых компетенций | part-time team, key skills missing |
| 2 | есть техническое ядро, нет коммерческого лидера | core technical team, no commercial lead |
| 3 | полное ядро команды, опыт в отрасли | complete core team, relevant domain track record |
| 4 | команда уже выводила и продавала похожие продукты | team has shipped & sold similar products; advisors with access |
| 5 | серийные основатели / ведущая исследовательская группа + доказанные коммерческие руководители | repeat founders / leading research group + proven commercial executives |

**Красные флаги:** single point of failure (one developer); no one owns sales

### Тракшн и доказательства (`traction`, вес 10)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | нет | none |
| 1 | лист ожидания / интерес | waitlist / interest only |
| 2 | 1–2 бесплатных пилота или LOI | 1–2 unpaid pilots or LOIs |
| 3 | платные пилоты или ≥ 3 LOI; данные использования | paid pilots or ≥ 3 LOIs; usage data |
| 4 | регулярная выручка, ≥ 5 платящих клиентов, данные удержания | recurring revenue, ≥ 5 paying customers, retention data |
| 5 | быстрый рост регулярной выручки (> 2× г/г) при NRR ≥ 110% | fast-growing recurring revenue (> 2x YoY) with NRR ≥ 110% |

**Красные флаги:** pilots that never convert; vanity metrics (registrations, downloads) without usage

### Бизнес-модель и юнит-экономика (`unit_economics`, вес 9)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | модели нет | no model |
| 1 | цена не определена | pricing undefined |
| 2 | цена есть, маржа неизвестна | pricing defined, margins unknown |
| 3 | ВМ ≥ 50%, оценочно LTV/CAC ≥ 2 | GM ≥ 50%, LTV/CAC estimated ≥ 2 |
| 4 | ВМ ≥ 70%, LTV/CAC ≥ 3, окупаемость ≤ 18 мес. (измерено) | GM ≥ 70%, LTV/CAC ≥ 3, payback ≤ 18 mo (measured) |
| 5 | ВМ ≥ 80%, LTV/CAC ≥ 5, окупаемость ≤ 12 мес., burn multiple < 1,5 | GM ≥ 80%, LTV/CAC ≥ 5, payback ≤ 12 mo, burn multiple < 1.5 |

**Красные флаги:** LTV computed with < 2% monthly churn assumption without data; inference/compute costs ignored in COGS

### Выход на рынок и каналы (`gtm`, вес 7)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | плана нет | no plan |
| 1 | общий план («маркетинг, партнёры») | generic plan ('marketing, partners') |
| 2 | определены сегмент и ICP | target segment and ICP defined |
| 3 | найден первый повторяемый канал, измерен цикл сделки | repeatable first channel identified, sales cycle measured |
| 4 | 2+ рабочих канала, соглашения с интеграторами, ясен путь закупки | 2+ working channels, partner/integrator agreements, procurement route clear |
| 5 | масштабируемая машина продаж (magic number > 0,75), доказан land-and-expand | efficient scalable engine (magic number > 0.75), land-and-expand proven |

**Красные флаги:** relying on a single anchor customer; no understanding of public/enterprise procurement rules

### Регуляторика и технологический суверенитет (`regulatory`, вес 7)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | заблокировано: критическая зависимость от компонента, недоступного на целевом рынке, без замены | blocked: critical dependency on a component that cannot be used in the target market, no substitute |
| 1 | серьёзные несоответствия требованиям | major compliance gaps |
| 2 | путь соответствия известен, не начат | compliance path known, not started |
| 3 | соответствие в процессе, контролируемый стек | compliance in progress, controllable stack |
| 4 | соответствует требованиям к данным и ИБ целевых заказчиков | meets data & security requirements of target buyers |
| 5 | полное соответствие + сертификаты + включено в отраслевые / государственные программы | full compliance + certifications + listed in sector / policy programmes |

**Красные флаги:** third-party cloud/LLM API in the critical path where buyers require local processing; personal data processed outside the permitted jurisdiction

### Масштабируемость и экспорт (`scalability`, вес 5)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | каждый раз заказная разработка | custom project each time |
| 1 | тяжёлая кастомизация под клиента | heavy customization per client |
| 2 | настраиваемый продукт, одна отрасль | configurable product, single sector |
| 3 | мультиотраслевой продукт, низкие предельные затраты | multi-sector product, marginal cost per client low |
| 4 | локализация для ≥ 1 экспортного рынка, есть партнёр | localized for ≥ 1 export market, partner identified |
| 5 | доказанная экспортная выручка или платформенная экономика | proven export revenue or platform/marketplace economics |

**Красные флаги:** export plan to markets where local compliance blocks distribution

### Профиль рисков (5 = низкий риск) (`risk`, вес 6)

| Балл | Якорь | Anchor (EN) |
|---:|---|---|
| 0 | экзистенциальные риски без мер | existential risks unmitigated |
| 1 | несколько высоких рисков, слабые меры | several high risks, weak mitigants |
| 2 | высокие риски с правдоподобными мерами | high risks with plausible mitigants |
| 3 | средний остаточный риск, меры профинансированы | medium residual risk, mitigants funded |
| 4 | низкий остаточный риск, диверсификация клиентов и поставщиков | low residual risk, diversified customers & suppliers |
| 5 | минимальный остаточный риск, договорная защита, денег > 24 мес. | minimal residual risk, contractual protections, cash > 24 mo |

**Красные флаги:** runway < 6 months; > 50% revenue from one customer

## 3. Уровни доказательности

| Уровень | Значение | Достоверность | Полоса балла |
|---|---|---:|---|
| A | подтверждено (аудит, договоры, логи, рецензируемые данные) | 1.00 | ±0 |
| B | обоснованная оценка (пилоты, LOI, надёжный внешний источник) | 0.75 | ±0.5 |
| C | допущение / заявление команды | 0.40 | ±1.0 |

Итоговая достоверность — средневзвешенная по весам. Диапазон итогового балла считается из полос — показывайте его рядом с баллом («64 из 100, диапазон 55–73»).

## 4. Шкала оценок

| Грейд | Порог | Значение |
|---|---:|---|
| A | ≥ 80 | сильный — приоритет / инвестировать |
| B | ≥ 65 | перспективный — поддержать с условиями |
| C | ≥ 50 | условный — сначала усилить конкретные слабые места |
| D | ≥ 35 | слабый — переработать концепцию |
| E | ≥ 0 | сейчас нежизнеспособен |

## 5. Автоматические красные флаги

| id | Тип | Серьёзность | Рынки | Сообщение |
|---|---|---|---|---|
| `critical_gap` | score_below_with_weight | high | все | Критическое слабое место: критерий с большим весом оценён ≤ 1 |
| `trl_stage_mismatch` | stage_trl | high | все | Заявленная стадия (пилот/рост) не соответствует низкой УГТ |
| `ltv_cac` | fact_below | high | все | LTV/CAC < 1: рост уничтожает стоимость |
| `ltv_cac_soft` | fact_below | medium | все | LTV/CAC ниже 3 |
| `runway` | fact_below | high | все | Запас денег < 6 месяцев |
| `concentration` | fact_above | medium | все | > 50% выручки от одного клиента |
| `registry_gov` | fact_false_for_audience | high | ru | Нет возможности включения в реестр российского ПО при ориентации на госзаказчиков / КИИ |
| `low_confidence` | confidence_below | medium | все | Достоверность оценок < 60%: большинство баллов основано на допущениях |
| `foreign_dependency` | fact_true | high | все | Критическая зависимость от внешнего или потенциально недоступного компонента в ядре решения |
| `xinchuang_gov` | fact_false_for_audience | high | zh | Нет адаптации к отечественному ИТ-стеку (синьчуан) при ориентации на госзаказчиков / госкомпании КНР |
| `mlps_gov` | fact_false_for_audience | medium | zh | Нет оценки по MLPS 2.0 (дэнбао) для системы, продаваемой госзаказчикам |
| `genai_filing` | fact_true | high | zh | Публичный сервис генеративного ИИ без обязательной регистрации алгоритма / сервиса |
| `cross_border_data` | fact_true | high | zh, ru, en, vn, id, my | Трансграничная передача персональных данных без необходимой оценки / правового основания |
| `enterprise_security` | fact_false_for_audience | medium | en | Нет аттестации SOC 2 / ISO 27001 (или реалистичного плана) при продажах корпорациям |
| `fedramp_gov` | fact_false_for_audience | medium | en | Ориентация на федеральных заказчиков США без пути авторизации FedRAMP для облачной версии |
| `ai_risk` | fact_true | medium | en | ИИ-функции продаются корпоративным или федеральным заказчикам США без документированной оценки рисков ИИ (напр. NIST AI RMF) |
| `vn_pdp_dossier` | fact_false_for_audience | medium | vn | Нет досье оценки воздействия обработки персональных данных (закон Вьетнама 91/2025/QH15) |
| `id_pse` | fact_false_for_audience | high | id | Нет регистрации оператора электронной системы (PSE) для сервиса в Индонезии |
| `id_tkdn` | fact_false_for_audience | high | id | Нет сертификата TKDN (локальное содержание) при ориентации на госзакупки / госкомпании |
| `my_pdpa` | fact_false_for_audience | medium | my | Не подтверждено соответствие PDPA 2010 (с поправками 2024 г.): DPO, уведомление об утечках, обязанности обработчика |

Флаг высокой серьёзности не обнуляет балл, но выносится на слайд рисков и в раздел «Риски» отчёта с мерой. Два и более флага high → рекомендация не выше «условный (C)» независимо от числа.

## 6. Профили по стадиям (сумма = 100)

| Критерий | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Размер и рост рынка | 16 | 14 | 13 | 12 |
| Острота проблемы и готовность платить | 16 | 13 | 11 | 8 |
| Зрелость продукта и технологии (УГТ/TRL) | 6 | 12 | 11 | 6 |
| Отличие, защищённость, ИС | 10 | 11 | 10 | 10 |
| Команда и способность исполнять | 16 | 13 | 9 | 8 |
| Тракшн и доказательства | 4 | 7 | 13 | 16 |
| Бизнес-модель и юнит-экономика | 5 | 6 | 10 | 15 |
| Выход на рынок и каналы | 7 | 7 | 8 | 10 |
| Регуляторика и технологический суверенитет | 7 | 7 | 7 | 6 |
| Масштабируемость и экспорт | 6 | 5 | 4 | 6 |
| Профиль рисков (5 = низкий риск) | 7 | 5 | 4 | 3 |
| **Итого** | 100 | 100 | 100 | 100 |

Логика сдвигов: на стадии идеи оцениваются только рынок, проблема и команда; на пилоте вес переходит к доказательствам (тракшн, юнит-экономика); на росте — к эффективности (юнит-экономика, GTM), а технологический риск почти снят.

## 7. Множители аудитории

Множитель умножает вес стадии, затем веса нормируются к 100.

| Критерий | investor | government | corporate | academic |
|---|---:|---:|---:|---:|
| Размер и рост рынка | 1.2 | 0.9 | 0.8 | 0.7 |
| Острота проблемы и готовность платить | 1 | 1 | 1.3 | 1 |
| Зрелость продукта и технологии (УГТ/TRL) | 0.9 | 1.2 | 1.3 | 1.3 |
| Отличие, защищённость, ИС | 1 | 1 | 0.9 | 1.4 |
| Команда и способность исполнять | 1 | 1.1 | 1 | 1.3 |
| Тракшн и доказательства | 1.2 | 1 | 1 | 0.7 |
| Бизнес-модель и юнит-экономика | 1.3 | 0.6 | 0.8 | 0.5 |
| Выход на рынок и каналы | 1 | 1 | 1.1 | 0.6 |
| Регуляторика и технологический суверенитет | 0.8 | 1.6 | 1.2 | 1 |
| Масштабируемость и экспорт | 1.2 | 1.1 | 1 | 1 |
| Профиль рисков (5 = низкий риск) | 1 | 1.1 | 1 | 1 |

## 8. Итоговые веса: стадия × аудитория (рынок по умолчанию)

Сгенерировано `scoring.py` (`weights_for`). Каждая колонка = 100.

### Аудитория: investor

| Критерий | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Размер и рост рынка | 18.3 | 16.1 | 14.6 | 13.2 |
| Острота проблемы и готовность платить | 15.3 | 12.5 | 10.3 | 7.3 |
| Зрелость продукта и технологии (УГТ/TRL) | 5.2 | 10.3 | 9.3 | 4.9 |
| Отличие, защищённость, ИС | 9.6 | 10.5 | 9.4 | 9.1 |
| Команда и способность исполнять | 15.3 | 12.5 | 8.5 | 7.3 |
| Тракшн и доказательства | 4.6 | 8.0 | 14.6 | 17.5 |
| Бизнес-модель и юнит-экономика | 6.2 | 7.5 | 12.2 | 17.8 |
| Выход на рынок и каналы | 6.7 | 6.7 | 7.5 | 9.1 |
| Регуляторика и технологический суверенитет | 5.3 | 5.4 | 5.3 | 4.4 |
| Масштабируемость и экспорт | 6.9 | 5.7 | 4.5 | 6.6 |
| Профиль рисков (5 = низкий риск) | 6.7 | 4.8 | 3.8 | 2.7 |
| **Итого** | 100 | 100 | 100 | 100 |

### Аудитория: government

| Критерий | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Размер и рост рынка | 13.8 | 12.0 | 11.4 | 10.9 |
| Острота проблемы и готовность платить | 15.3 | 12.4 | 10.7 | 8.1 |
| Зрелость продукта и технологии (УГТ/TRL) | 6.9 | 13.7 | 12.8 | 7.3 |
| Отличие, защищённость, ИС | 9.6 | 10.5 | 9.7 | 10.1 |
| Команда и способность исполнять | 16.8 | 13.6 | 9.6 | 8.9 |
| Тракшн и доказательства | 3.8 | 6.7 | 12.6 | 16.1 |
| Бизнес-модель и юнит-экономика | 2.9 | 3.4 | 5.8 | 9.1 |
| Выход на рынок и каналы | 6.7 | 6.7 | 7.8 | 10.1 |
| Регуляторика и технологический суверенитет | 10.7 | 10.7 | 10.9 | 9.7 |
| Масштабируемость и экспорт | 6.3 | 5.2 | 4.3 | 6.6 |
| Профиль рисков (5 = низкий риск) | 7.4 | 5.2 | 4.3 | 3.3 |
| **Итого** | 100 | 100 | 100 | 100 |

### Аудитория: corporate

| Критерий | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Размер и рост рынка | 12.4 | 10.7 | 10.1 | 9.6 |
| Острота проблемы и готовность платить | 20.1 | 16.2 | 13.9 | 10.4 |
| Зрелость продукта и технологии (УГТ/TRL) | 7.5 | 14.9 | 13.9 | 7.8 |
| Отличие, защищённость, ИС | 8.7 | 9.5 | 8.7 | 9.0 |
| Команда и способность исполнять | 15.5 | 12.4 | 8.7 | 8.0 |
| Тракшн и доказательства | 3.9 | 6.7 | 12.6 | 16.0 |
| Бизнес-модель и юнит-экономика | 3.9 | 4.6 | 7.8 | 12.0 |
| Выход на рынок и каналы | 7.4 | 7.4 | 8.5 | 11.0 |
| Регуляторика и технологический суверенитет | 8.1 | 8.0 | 8.1 | 7.2 |
| Масштабируемость и экспорт | 5.8 | 4.8 | 3.9 | 6.0 |
| Профиль рисков (5 = низкий риск) | 6.8 | 4.8 | 3.9 | 3.0 |
| **Итого** | 100 | 100 | 100 | 100 |

### Аудитория: academic

| Критерий | idea | prototype | pilot | growth |
|---|---:|---:|---:|---:|
| Размер и рост рынка | 11.3 | 9.8 | 9.7 | 9.5 |
| Острота проблемы и готовность платить | 16.1 | 13.0 | 11.7 | 9.1 |
| Зрелость продукта и технологии (УГТ/TRL) | 7.9 | 15.6 | 15.2 | 8.8 |
| Отличие, защищённость, ИС | 14.1 | 15.4 | 14.9 | 15.9 |
| Команда и способность исполнять | 20.9 | 16.9 | 12.4 | 11.8 |
| Тракшн и доказательства | 2.8 | 4.9 | 9.7 | 12.7 |
| Бизнес-модель и юнит-экономика | 2.5 | 3.0 | 5.3 | 8.5 |
| Выход на рынок и каналы | 4.2 | 4.2 | 5.1 | 6.8 |
| Регуляторика и технологический суверенитет | 7.0 | 7.0 | 7.4 | 6.8 |
| Масштабируемость и экспорт | 6.0 | 5.0 | 4.3 | 6.8 |
| Профиль рисков (5 = низкий риск) | 7.0 | 5.0 | 4.3 | 3.4 |
| **Итого** | 100 | 100 | 100 | 100 |

## 9. Веса разделов деки по аудиториям (сумма = 100)

Используются `allocate_slides()` для распределения слайдов и времени.

| Раздел | investor | government | corporate | academic |
|---|---:|---:|---:|---:|
| Главный вывод / тезис | 8 | 8 | 8 | 8 |
| Проблема и почему сейчас | 8 | 10 | 12 | 10 |
| Решение / продукт и демо | 8 | 7 | 12 | 8 |
| Рынок (TAM/SAM/SOM) | 10 | 6 | 4 | 4 |
| Технология и УГТ | 4 | 10 | 10 | 16 |
| Тракшн и доказательства | 12 | 5 | 8 | 4 |
| Бизнес-модель и юнит-экономика | 10 | 3 | 6 | 2 |
| Конкуренты и барьеры | 7 | 5 | 5 | 8 |
| Выход на рынок | 6 | 4 | 6 | 2 |
| Финплан и доходность | 10 | 6 | 4 | 3 |
| Команда | 7 | 8 | 5 | 10 |
| Регуляторика и суверенитет | 2 | 12 | 7 | 4 |
| Риски и меры | 3 | 6 | 5 | 6 |
| Дорожная карта | 2 | 7 | 5 | 10 |
| Запрос / требуемое решение | 3 | 3 | 3 | 5 |
| **Итого** | 100 | 100 | 100 | 100 |

## 10. Профили рынков

Профиль умножает указанные веса (с перенормировкой), заменяет определение и якоря критерия регуляторики и задаёт факты комплаенса для красных флагов. Правовой статус проверен 20.10.2026; перепроверяйте перед использованием.

| id | Рынки | Валюта | Множители весов | Факты комплаенса | Гайд |
|---|---|---|---|---|---|
| `ru` | Россия | RUB | regulatory ×1.15 | `registry_eligible`, `critical_foreign_dependency`, `cross_border_data_unassessed` | [markets/ru.md](markets/ru.md) |
| `en` | США | USD | regulatory ×0.85 | `security_attestation`, `fedramp_path`, `ai_risk_unassessed`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/en.md](markets/en.md) |
| `zh` | Материковый Китай | CNY | regulatory ×1.25, gtm ×1.1 | `xinchuang_adapted`, `mlps_certified`, `genai_filing_missing`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/zh.md](markets/zh.md) |
| `vn` | Вьетнам | VND | regulatory ×1.15, gtm ×1.05 | `pdp_impact_assessment`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/vn.md](markets/vn.md) |
| `id` | Индонезия | IDR | regulatory ×1.15, gtm ×1.1 | `pse_registered`, `tkdn_certified`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/id.md](markets/id.md) |
| `my` | Малайзия | MYR | regulatory ×1 | `pdpa_compliant`, `cross_border_data_unassessed`, `critical_foreign_dependency` | [markets/my.md](markets/my.md) |

### `ru` — Регуляторика и технологический суверенитет

**Определение критерия «Регуляторика и суверенитет».** Единый реестр российского ПО (ПП РФ № 1236 от 16.11.2015), 152-ФЗ «О персональных данных» (в т.ч. локализация), 187-ФЗ о безопасности КИИ, сертификация ФСТЭК/ФСБ при необходимости, закупки по 44-ФЗ / 223-ФЗ.

| Балл | Якорь |
|---:|---|
| 0 | заблокировано: критическая зависимость от иностранных компонентов без замены |
| 1 | серьёзные несоответствия требованиям |
| 2 | путь соответствия известен, не начат |
| 3 | в процессе (заявка в реестр, 152-ФЗ), отечественный стек |
| 4 | в реестре российского ПО; соответствует требованиям к данным и ИБ целевых заказчиков |
| 5 | реестр + сертификаты + включено в планы импортозамещения / отраслевые программы |

### `en` — Регуляторика, ИБ и комплаенс (США)

**Определение критерия «Регуляторика и суверенитет».** Законы штатов о персональных данных (напр. CCPA Калифорнии с поправками CPRA), аттестации SOC 2 / ISO/IEC 27001 для корпоративных заказчиков, FedRAMP для облачных сервисов федеральным ведомствам США, управление рисками ИИ (добровольная рамка NIST AI RMF), отраслевые правила (напр. HIPAA).

| Балл | Якорь |
|---:|---|
| 0 | заблокировано: продукт не может выполнить обязательное требование сегмента (напр. отраслевое правило) |
| 1 | серьёзные несоответствия (нет программы защиты данных и условий для поставщика услуг, нет программы ИБ) |
| 2 | дорожная карта комплаенса есть, не начата |
| 3 | программа защиты данных есть, SOC 2 Type I / ISO 27001 в процессе |
| 4 | SOC 2 Type II или сертификат ISO 27001; оценка рисков ИИ задокументирована |
| 5 | сертификаты + FedRAMP / отраслевые авторизации; комплаенс — преимущество в продажах |

### `zh` — Комплаенс и технологическая самостоятельность (КНР)

**Определение критерия «Регуляторика и суверенитет».** Закон о кибербезопасности (2016), Закон о безопасности данных (2021), Закон о защите персональной информации (PIPL, 2021) с правилами трансграничной передачи; Временные меры по управлению сервисами генеративного ИИ (2023) и регистрация алгоритмов; MLPS 2.0 (дэнбао, GB/T 22239-2019); адаптация к отечественному стеку «синьчуан» для госзаказчиков и госкомпаний.

| Балл | Якорь |
|---:|---|
| 0 | заблокировано: ключевая зависимость недоступна в КНР или данные должны покидать КНР без законного пути |
| 1 | серьёзные несоответствия (нет основания по PIPL, нет оценки MLPS) |
| 2 | путь соответствия известен, не начат |
| 3 | соответствие PIPL есть; оценка MLPS / регистрация алгоритма в процессе; начата адаптация «синьчуан» |
| 4 | уровень MLPS подтверждён, регистрации завершены, совместимость с основными отечественными стеками сертифицирована |
| 5 | полное соответствие + включение в государственные / отраслевые каталоги; соответствие политическим программам |

### `vn` — Регуляторика и цифровой суверенитет (Вьетнам)

**Определение критерия «Регуляторика и суверенитет».** Law on Personal Data Protection No. 91/2025/QH15 (in force 1 Jan 2026; detailed by Decree 356/2025/ND-CP, which replaced Decree 13/2023/ND-CP) incl. impact-assessment dossiers for processing and cross-border transfer; Law on Cybersecurity No. 116/2025/QH15 (in force 1 Jul 2026, replacing the 2018 Cybersecurity Law and the 2015 Law on Cyberinformation Security) incl. information-system security levels; Law on Digital Technology Industry No. 71/2025/QH15 (incentives for digital-technology products and enterprises); Law on Artificial Intelligence No. 134/2025/QH15; public procurement under the Law on Bidding No. 22/2023/QH15.

| Балл | Якорь |
|---:|---|
| 0 | blocked: data or core component cannot lawfully be used/processed for the target customers |
| 1 | major gaps (no PDP impact-assessment dossier, no security-level classification) |
| 2 | compliance path known, not started |
| 3 | PDP dossiers prepared; information-system security level determined; local deployment option |
| 4 | PDP and cybersecurity obligations met for target buyers; recognised as a digital-technology product/enterprise where relevant |
| 5 | full compliance + listed in national / ministry digital-transformation programmes |

### `id` — Регуляторика, локальное содержание и суверенитет (Индонезия)

**Определение критерия «Регуляторика и суверенитет».** Personal Data Protection Law No. 27/2022 (UU PDP; two-year adjustment period ended Oct 2024); registration as an electronic system operator (PSE) under MR 5/2020 via OSS with the Ministry of Communication and Digital (Komdigi, formerly Kominfo); GR 71/2019 on electronic systems (data-placement rules for public-scope operators); local content (TKDN) certification for government and SOE procurement (Perpres 46/2025, Permenperin 35/2025).

| Балл | Якорь |
|---:|---|
| 0 | blocked: cannot register as PSE or meet data-placement rules for target buyers |
| 1 | major gaps (no UU PDP programme, no PSE registration) |
| 2 | compliance path known, not started |
| 3 | PSE registered; UU PDP programme in place; TKDN assessment started |
| 4 | TKDN certified at the level required by target tenders; data and security requirements met |
| 5 | full compliance + listed in e-catalogue / government programmes |

### `my` — Регуляторика и цифровое доверие (Малайзия)

**Определение критерия «Регуляторика и суверенитет».** Personal Data Protection Act 2010 (Act 709) as amended by Act A1727 (2024; phased commencement 1 Jan, 1 Apr and 1 Jun 2025): data controllers and processors, DPO appointment, breach notification, data portability, cross-border transfer; Cyber Security Act 2024 (Act 854, in force 26 Aug 2024) for national critical information infrastructure (NCII) entities, overseen by NACSA; sector rules (e.g. Bank Negara Malaysia RMiT for financial institutions); Malaysia Digital (MD, formerly MSC Malaysia) status for incentives.

| Балл | Якорь |
|---:|---|
| 0 | blocked: cannot meet a mandatory requirement of the target sector (e.g. NCII or RMiT obligations) |
| 1 | major gaps (no PDPA programme, no security controls) |
| 2 | compliance path known, not started |
| 3 | PDPA programme incl. DPO and breach process; security controls in progress |
| 4 | meets PDPA, sector (e.g. RMiT) and NCII-customer requirements; MD status where relevant |
| 5 | full compliance + certifications + listed in government / GLC digital programmes |

## 11. Как читать и защищать балл

* **Показывайте диапазон, а не только точку**: «64 из 100 (диапазон 55–73, достоверность 75%)».
* **Начинайте со слабых мест**: скоркарта заканчивается выводом «главные слабые места — тракшн и
  юнит-экономика; закрываются двумя продлениями контрактов».
* **Балл ≠ решение.** Грейд — рекомендация; укажите, какие факты изменят его.
* **Калибровка.** При первом использовании оцените 3–5 известных проектов (успешных и
  провалившихся); если модель их не различает — правьте якоря, а не веса.
* **Два оценщика.** Расхождение > 1 балла по критерию — повод обсудить доказательства.

## 12. Изменение модели

* Новый критерий — в `criteria` с весом; затем обновите все `stage_profiles` (каждая колонка = 100,
  проверяет тест).
* Множители аудитории и рынка — относительный акцент (0,5–1,6); не используйте 0.
* После правки: `python -m unittest discover -s tools/tests` и `python tools/gen_scoring_doc.py`.
