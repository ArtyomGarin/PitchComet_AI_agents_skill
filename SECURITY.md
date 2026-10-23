# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 1.1.x | yes |
| 1.0.x | security fixes only |
| older | no |

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use the repository's private
vulnerability reporting (**Security → Report a vulnerability**) and include:

* the version or commit, operating system and Python version;
* the input files or commands that trigger the problem (minimal, with no real personal or
  company data);
* what happens and what you expected.

We aim to acknowledge a report within 7 days and to agree on a fix and disclosure date with you.
This is a volunteer project, so there is no bug bounty.

## Scope and threat model

PitchComet runs locally and processes files you give it.

* **No network access.** The tools do not download anything or call external services. Web
  research is done by the agent with its own tools; the results arrive as a JSON ledger.
* **Formulas.** Estimates use a restricted expression evaluator (`tools/estimator.py`), not
  `eval`. A way to execute code through a ledger, brief or spec file is a vulnerability.
* **Office files.** Generated `.pptx` / `.docx` files contain no macros. Rendering previews runs
  LibreOffice on those files; treat third-party Office files as untrusted input.
* **Paths.** CLI tools, `tools/agent_tools.py` and `tools/mcp_server.py` read and write the paths
  they are given, with the permissions of the user who runs them. Run the MCP server only for
  clients you trust with your file system.
* **Data.** Do not commit real customer data, credentials or personal data to briefs, ledgers or
  examples. The examples in this repository are fictional products.
