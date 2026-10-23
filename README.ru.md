# PitchComet

[![version](https://img.shields.io/badge/version-0.1b0-0B1530)](CHANGELOG.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-3776AB)](pyproject.toml)
[![tests](https://img.shields.io/badge/tests-unittest-brightgreen)](tools/tests)
[![MCP](https://img.shields.io/badge/MCP-stdio%20server-8A9BC9)](README.md#agent-integration)

![PitchComet](docs/social_preview.png)

Скилл для ИИ-агента и набор Python-инструментов: из **короткого описания ИТ-продукта** получаются
**рассчитанная питч-презентация (.pptx)** и **стратегический отчёт (.docx)**. Размер рынка, рост,
цену, юнит-экономику, финансовую модель и оценку компании инструменты считают сами, если у
пользователя нет данных. Нативные редактируемые диаграммы, одна база фактов для обоих документов,
строгая проверка качества, шесть локалей.

* **Автономный режим.** Профиль продукта → рынок, сегменты и ICP → план поиска в интернете →
  реестр доказательств → TAM/SAM/SOM (сверху вниз, снизу вверх, по ценности + триангуляция), CAGR,
  сценарии, цена по ценности, юнит-экономика (CAC, LTV, окупаемость по эталонным диапазонам),
  ROI/TCO клиента, финмодель на 5 лет, NPV/IRR/MOIC, Rule of 40, оценка по аналогам.
* **Ничего не выдумывается.** Каждая цифра — либо *факт из источника* (ссылка, год, дата
  обращения), либо *помеченная оценка* (формула, входы, диапазон низкий–базовый–высокий,
  уверенность). Остаётся только короткий список «уточнить у основателей» — он не блокирует презентацию.
* **QA не пропускает** питч без размера рынка, CAGR или юнит-экономики и любые заглушки
  «нет данных / TBD» на шести языках.
* **Пять паттернов питча** — крупный инвестор, небольшой инвестор, корпоративный заказчик, МСП,
  государство: порядок и число слайдов, обязательные метрики, веса скоринга, диаграммы, тон, призыв.
* **Семь тем** — `light`, `dark`, `academic_light`, `comet`, `editorial`, `corporate`, `warm`
  (все с настройками CJK-шрифтов).
* Режим «по данным» сохранён: структурированные входы → `run_pipeline.py`.
* Локали `ru`, `en`, `zh`, `vi`, `id`, `ms`; рыночные профили: Россия, США, Китай, Вьетнам,
  Индонезия, Малайзия.
* **«Что значат цифры».** Каждая презентация начинается с глоссария простыми словами: в нём ровно
  те показатели, которые есть на слайдах. В отчёте такой же раздел. QA не пропустит показатель без объяснения.
* **Готово для агентов.** `SKILL.md` для агентов со скиллами, JSON-схемы для вызова функций и MCP-сервер
  без зависимостей.

Другие языки: [English](README.md) · [简体中文](README.zh-CN.md)


## Быстрый старт за 60 секунд

```bash
git clone <адрес репозитория> pitchcomet && cd pitchcomet
pip install -r requirements.txt
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_ru.json \
       --pattern large_investor --out demo < /dev/null
ls examples/autonomous_shiftlyra/demo   # deck.pptx  report.docx  qa_comet.json  auto_summary.json ...
```

Команда за несколько секунд собирает презентацию для инвестора и отчёт по вымышленному продукту из
примера (бриф и реестр источников уже лежат в `examples/`), с проверкой качества. С `--render`
получатся PNG-превью (нужны LibreOffice и poppler-utils). Для своего продукта напишите бриф из
четырёх строк и начните с `--plan-only`.

## Галерея

![Презентация](docs/deck_large_investor_en.png)

| Пять паттернов | Семь тем |
|---|---|
| ![Паттерны](docs/patterns.png) | ![Темы](docs/themes.png) |

| Глоссарий на шести языках | Отчёт (.docx) |
|---|---|
| ![Глоссарий](docs/glossary_locales.png) | ![Отчёт](docs/report_en.png) |

Это контактные листы настоящих результатов из `examples/`; пересобрать: `python docs/make_assets.py`.

## По шагам — автономно

```bash
pip install -r requirements.txt
# 1. план исследования: профиль, определение рынка, ключи реестра, поисковые запросы
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_ru.json --plan-only < /dev/null
# 2. агент ищет данные (prompts/ru/research_loop.md) и заполняет реестр
python tools/research_ledger.py validate --input examples/autonomous_shiftlyra/ledger_ru.json < /dev/null
# 3. расчёт + сборка + QA (+ PNG-превью)
python tools/auto_pitch.py --brief examples/autonomous_shiftlyra/brief_ru.json \
       --pattern small_investor --theme warm --render < /dev/null
```

Бриф — это название, описание, рынок и аудитория:

```json
{"name": "Мой продукт", "text": "Абзац о том, что делает продукт и для кого",
 "market": "ru", "locale": "ru", "audience": "бизнес-ангелы", "ledger": "ledger.json"}
```

Без реестра запуск всё равно завершается — с помеченными офлайн-допущениями и водяным знаком
«черновик без исследования». Результат: `profile.json`, `market_definition.json`,
`research_plan.json`, `ledger_full.json`, `facts.json`, `deck*.pptx`, `report.docx`,
`qa_<тема>.json`, `auto_summary.json` (паттерн, QA, ключевые цифры, что уточнить), `renders/`.

## По шагам — по данным

```bash
python tools/run_pipeline.py --project examples/example_ru/project.json --theme light --theme editorial < /dev/null
python tools/new_project.py --dir work/my_product --name "Мой продукт" --locale ru
```

Для превью нужны LibreOffice и poppler-utils; для китайского — CJK-шрифт (например, `fonts-noto-cjk`).

```bash
python -m unittest discover -s tools/tests -v < /dev/null
```

## Паттерны питча

| id | Аудитория | Тема | Слайдов | Обязательно |
|---|---|---|---|---|
| `large_investor` | фонд роста / поздние стадии | comet | 15–20 | TAM, SAM, SOM, CAGR, LTV/CAC, Rule of 40, IRR, MOIC |
| `small_investor` | бизнес-ангел / pre-seed / seed (по умолчанию) | warm | 10–14 | TAM, SOM, CAGR, LTV/CAC, MOIC |
| `corporate` | крупный заказчик / партнёр | corporate | 9–13 | ROI клиента, TCO, окупаемость |
| `smb` | владельцы малого бизнеса | warm | 6–9 | цена в месяц, экономия, окупаемость |
| `government` | грант / госпрограмма | corporate | 11–15 | SAM, CAGR, ROI, общественный эффект |

`--pattern auto` выбирает паттерн по полю `audience`. Плейбуки: [`patterns/`](patterns/README.md).

## Локали

| Локаль | Пример суммы | Даты | Цитирование (по умолчанию) | Гид по рынку |
|---|---|---|---|---|
| `ru` | `3,0 млрд ₽` | 20.10.2026 | ГОСТ Р 7.0.5-2008, сноски | `markets/ru.md` |
| `en` | `$3.0B` | October 20, 2026 | APA 7 (есть Chicago) | `markets/en.md` |
| `zh` | `30.0亿元` | 2026年10月20日 | GB/T 7714-2015, нумерация | `markets/zh.md` |
| `vi` | `3,0 nghìn tỷ ₫` | ngày 20 tháng 10 năm 2026 | APA 7 | `markets/vn.md` |
| `id` | `Rp3,0 triliun` | 20 Oktober 2026 | APA 7 | `markets/id.md` |
| `ms` | `RM3.0 bilion` | 20 Oktober 2026 | APA 7 | `markets/my.md` |

Повествовательный текст автономного режима написан на русском и английском; остальные локали
получают английский текст с форматами своей локали (формулировки добавляются в `tools/pitch_story.py`).

## Подключение к агенту

* **Как скилл.** Агенты, которые загружают папки скиллов, читают [`SKILL.md`](SKILL.md).
* **Вызов функций.** `python tools/agent_tools.py schemas` печатает шесть инструментов с JSON-схемами
  (`--format mcp` для формата MCP). В коде: `from agent_tools import schemas, call_tool`.
* **MCP-сервер.** `python tools/mcp_server.py` работает по stdio без зависимостей:
  `{"mcpServers": {"pitchcomet": {"command": "python", "args": ["/path/to/pitchcomet/tools/mcp_server.py"]}}}`
* **CLI.** Все инструменты запускаются как обычные команды.

Подробнее с примерами: [README.md#agent-integration](README.md#agent-integration).

## Инструменты

| Инструмент | Назначение |
|---|---|
| `tools/auto_pitch.py` | автономный режим: бриф → план → реестр и оценки → паттерн → дека и отчёт → QA |
| `tools/product_profiler.py` | категория, покупатель, единица, модель цены, развёртывание, стадия по описанию |
| `tools/market_definer.py` | коды классификаторов, сегменты, ICP, план исследования, запросы, официальные источники |
| `tools/research_ledger.py` | реестр доказательств: проверка, дедупликация, валюта и год цен, разрешение конфликтов |
| `tools/estimator.py` | помеченные оценки: диапазоны, методы оценки рынка, триангуляция, CAGR, цена, юнит-экономика, аналоги |
| `tools/pitch_story.py` | текст под каждый паттерн, заметки докладчика, приложение «цифры презентации» |
| `tools/run_pipeline.py` | полный конвейер: рынок → финансы → скоринг → факты → docx + pptx → QA → превью |
| `tools/market_sizing.py` · `tools/financial_model.py` · `tools/scoring.py` | рынок, P&L/NPV/IRR/MOIC, балл потенциала |
| `tools/metrics_calc.py` | ~50 метрик, включая ROI и TCO клиента и ценность для МСП в месяц |
| `tools/build_docx.py` · `tools/build_pptx.py` | сборщики с нативными диаграммами и темами |
| `tools/qa_check.py` | QA, включая проверку полноты (`--pattern`, `--no-completeness`) |
| `tools/glossary.py` | глоссарий простыми словами: находит показатели в презентации или отчёте; определения в `config/glossary.json` |
| `tools/agent_tools.py` · `tools/mcp_server.py` | схемы для вызова функций и диспетчер; MCP-сервер по stdio |
| `tools/render_preview.py` · `tools/citations.py` · `tools/new_project.py` | превью, библиография, заготовка проекта |

Подробности: [`tools/README.md`](tools/README.md); схемы: `tools/tools.json`.

## Структура репозитория

```
pitchcomet/
├── SKILL.md                      # инструкция для агента
├── README.md · README.ru.md · README.zh-CN.md · ADAPTING.md · CHANGELOG.md
├── deck_structure.md · style_guide.md · metrics.md · scoring_model*.md
├── config/  scoring_model.json · banned_phrases.json · themes.json · benchmarks.json · market_taxonomy.json · glossary.json
├── patterns/  patterns.json + пять плейбуков
├── markets/  гиды ru · en · zh · vn · id · my
├── prompts/{ru,en,zh,vi,id,ms}/  цикл исследования, анкета, задание на исследование, сюжет, слайды, «красная команда»
├── templates/{ru,en,zh,vi,id,ms}/
├── examples/  example_{ru,en,zh,vi,id,ms}/ (по данным) · autonomous_shiftlyra/ (автономно)
├── tools/  инструменты + tools.json + tests/
└── LICENSE · CONTRIBUTING.md · pyproject.toml · requirements.txt · .github/workflows/tests.yml
```

## Принципы

* Не выдумывать реальные факты; у каждой реальной цифры — ссылка; у каждой оценки — формула.
* Эталоны в `config/benchmarks.json` — эмпирические правила, так и помечены.
* Числа берутся из инструментов, а не из текста. Одна мысль на слайд; заголовки — выводы.
* Примеры — вымышленные продукты, это указано (рыночные данные автономного примера реальные, со ссылками).

## Благодарности

PitchComet разработан с использованием личного практического опыта, а также
ИИ-ассистентов — в первую очередь **Grok** и **GigaChat**, которые активно применялись для
написания, рецензирования и доработки скилла, его промптов, инструментов и документации.

## Лицензия

MIT — см. [LICENSE](LICENSE).

## Отказ от ответственности

PitchComet формирует черновики автоматически. Результат **не является юридической консультацией
и не является инвестиционной рекомендацией**. Каждую цифру перед использованием необходимо
проверить; ответственность за то, как используются документы и за достоверность цифр, полностью
несёт пользователь.
