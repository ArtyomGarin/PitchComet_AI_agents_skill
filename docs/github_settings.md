# GitHub repository settings

Settings that live outside the files. Apply them once after the first push.

## About

**Description (≤ 350 characters):**

> Agent skill + Python toolkit: a short IT product description becomes an editable pitch deck (.pptx) and strategy report (.docx) with computed TAM/SAM/SOM, CAGR, unit economics, financial model and valuation. Every number sourced or a labelled estimate. Native charts, plain-language glossary, QA gate, 6 locales, MCP server.

**Website:** leave empty or link the documentation / demo Space.

## Topics (20, lowercase, hyphens)

```
pitch-deck pptx docx python-pptx python-docx market-sizing tam-sam-som financial-model
unit-economics startup investor-pitch business-plan agent-skills ai-agents mcp mcp-server
presentation-generator report-generator localization llm-tools
```

## Social preview

Settings → General → Social preview → upload `docs/social_preview.png` (1280×640).
Rebuild it with `python docs/make_assets.py --social`.

## Other

* Enable **Discussions** (questions and ideas; the issue template links there).
* Enable **Private vulnerability reporting** (Security → Settings), used by `SECURITY.md`.
* Branch protection on `main`: require the `tests` workflow.
* Releases: tag `v0.1b0` (title "PitchComet 0.1 beta"), paste the `CHANGELOG.md` section as release notes.
