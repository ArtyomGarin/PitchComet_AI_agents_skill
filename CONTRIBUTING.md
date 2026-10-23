# Contributing

Thank you for improving the skill. Please keep changes small and focused.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tools/tests -v < /dev/null
```

Optional for previews: LibreOffice, poppler-utils and a CJK font (Noto Sans CJK SC).

## Rules

1. **No invented facts.** Any real-world figure, law or statistic in docs, guides or examples needs
   an official or reliable link and a verification date. Volatile values (rates, inflation) are
   either omitted or dated.
2. **Fictional examples stay fictional** and are labelled as such in every locale.
3. **Numbers come from tools.** Specs use `{{path|fmt}}` placeholders into `facts.json`.
4. **Tests must pass** for all locales. Add a test for every new formatter, rule or locale.
5. **Regenerate generated files** after changing the model: `python tools/gen_scoring_doc.py`.
6. **No secrets, personal data or absolute paths** in commits.
7. **Neutral sources.** Do not cite organisations whose materials are restricted in a target market
   (see `SKILL.md` → Hard rules).

## Adding a locale or market

See `ADAPTING.md` §3–4: locale entry in `tools/locales.py`, banned phrases, prompts, templates,
an example, a market guide in `markets/`, a profile in `config/scoring_model.json`, tests.

## Pull requests

* Describe what changed and why; include before/after PNGs for visual changes.
* Run the example pipeline for affected locales and confirm QA reports 0 errors.
* Update `CHANGELOG.md`.
