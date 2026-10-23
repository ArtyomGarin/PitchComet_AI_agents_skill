#!/usr/bin/env python3
"""agent_tools.py — PitchComet as agent tools: function-calling schemas and a CLI dispatcher.

Six high-level tools cover the whole workflow. They wrap the command-line tools, so an agent needs
nothing but Python and this folder.

  pitchcomet_plan      brief → research plan (profile, market definition, ledger keys, web queries)
  pitchcomet_build     brief (+ ledger) → computed deck.pptx + report.docx + QA (+ previews)
  pitchcomet_pipeline  project.json with structured inputs → deck + report + QA (data-driven mode)
  pitchcomet_qa        quality gate for an existing deck / report
  pitchcomet_metric    one metric from metrics_calc (CAGR, LTV/CAC, IRR, MOIC, payback ...)
  pitchcomet_glossary  plain-language definitions of the metrics found in a text

CLI:
  python tools/agent_tools.py schemas                 # [{name, description, parameters}] (function calling)
  python tools/agent_tools.py schemas --format mcp    # [{name, description, inputSchema}] (MCP tools/list)
  python tools/agent_tools.py call pitchcomet_metric --args '{"metric": "cagr", "args": {"start": 100, "end": 180, "years": 3}}'

Python:
  from agent_tools import TOOLS, call_tool
  result = call_tool("pitchcomet_build", {"brief": "examples/autonomous_shiftlyra/brief_en.json"})

Every call returns {"ok": bool, "returncode": int, "command": [...], "stdout": str, "stderr": str}
plus "json" when the tool printed JSON. Paths are resolved relative to the current directory.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS = ["auto", "large_investor", "small_investor", "corporate", "smb", "government"]
THEMES = ["light", "dark", "academic_light", "comet", "editorial", "corporate", "warm"]
LOCALES = ["ru", "en", "zh", "vi", "id", "ms"]

TOOLS = [
    {"name": "pitchcomet_plan",
     "description": "Step 1 of the autonomous mode. Reads a brief (name, one-paragraph description, market, "
                    "locale, audience) and writes research_plan.json: product profile, market definition, "
                    "ledger keys to fill and web-search queries. Research the queries, add the facts with "
                    "links to the ledger, then call pitchcomet_build.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["brief"],
                    "properties": {"brief": {"type": "string", "description": "path to brief.json"},
                                   "out": {"type": "string", "description": "output folder, relative to the brief"}}}},
    {"name": "pitchcomet_build",
     "description": "Autonomous mode: brief + evidence ledger → computed TAM/SAM/SOM, CAGR, price, unit economics, "
                    "financial model, valuation → deck.pptx + report.docx with native charts and a plain-language "
                    "glossary → QA. Missing figures become labelled estimates; nothing is invented.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["brief"],
                    "properties": {"brief": {"type": "string", "description": "path to brief.json"},
                                   "pattern": {"type": "string", "enum": PATTERNS, "default": "auto"},
                                   "themes": {"type": "array", "items": {"type": "string", "enum": THEMES}},
                                   "locale": {"type": "string", "enum": LOCALES},
                                   "out": {"type": "string", "description": "output folder, relative to the brief"},
                                   "render": {"type": "boolean", "default": False,
                                              "description": "PNG previews (needs LibreOffice and poppler-utils)"}}}},
    {"name": "pitchcomet_pipeline",
     "description": "Data-driven mode: project.json with market, finance and scoring inputs → deck + report + QA.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["project"],
                    "properties": {"project": {"type": "string", "description": "path to project.json"},
                                   "themes": {"type": "array", "items": {"type": "string", "enum": THEMES}},
                                   "pattern": {"type": "string", "enum": PATTERNS[1:]},
                                   "render": {"type": "boolean", "default": False}}}},
    {"name": "pitchcomet_qa",
     "description": "Quality gate for a deck and/or report: text fit, sources, native charts, placeholders, "
                    "banned phrases, deck/report consistency, mandatory metrics of the pattern, glossary coverage.",
     "parameters": {"type": "object", "additionalProperties": False,
                    "properties": {"pptx": {"type": "string"}, "docx": {"type": "string"},
                                   "facts": {"type": "string", "description": "facts.json for consistency checks"},
                                   "locale": {"type": "string", "enum": LOCALES},
                                   "pattern": {"type": "string", "enum": PATTERNS[1:]}}}},
    {"name": "pitchcomet_metric",
     "description": "Compute one metric with metrics_calc (value, unit, formula, interpretation). "
                    "Call with metric='list' to get every metric and its arguments.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["metric"],
                    "properties": {"metric": {"type": "string", "description": "e.g. cagr, ltv_cac, irr, moic, payback"},
                                   "args": {"type": "object", "description": "keyword arguments of the metric"},
                                   "locale": {"type": "string", "enum": LOCALES}}}},
    {"name": "pitchcomet_glossary",
     "description": "Plain-language definitions of the metrics that appear in a text, deck or report "
                    "(the same data as the 'What the numbers mean' slide).",
     "parameters": {"type": "object", "additionalProperties": False,
                    "properties": {"text": {"type": "string"}, "pptx": {"type": "string"},
                                   "docx": {"type": "string"},
                                   "locale": {"type": "string", "enum": LOCALES, "default": "en"}}}},
]
_BY_NAME = {t["name"]: t for t in TOOLS}


def schemas(fmt: str = "functions") -> list[dict]:
    if fmt == "mcp":
        return [{"name": t["name"], "description": t["description"], "inputSchema": t["parameters"]} for t in TOOLS]
    return [{"name": t["name"], "description": t["description"], "parameters": t["parameters"]} for t in TOOLS]


def _abs(p: str) -> str:
    return os.path.abspath(os.path.expanduser(p))


def build_command(name: str, a: dict) -> list[str]:
    py = [sys.executable]
    if name not in _BY_NAME:
        raise ValueError(f"unknown tool {name!r}; known: {', '.join(_BY_NAME)}")
    if name in ("pitchcomet_plan", "pitchcomet_build"):
        cmd = py + [os.path.join(HERE, "auto_pitch.py"), "--brief", _abs(a["brief"])]
        if name == "pitchcomet_plan":
            cmd.append("--plan-only")
        else:
            if a.get("pattern"):
                cmd += ["--pattern", a["pattern"]]
            for th in a.get("themes") or []:
                cmd += ["--theme", th]
            if a.get("locale"):
                cmd += ["--locale", a["locale"]]
            if a.get("render"):
                cmd.append("--render")
        if a.get("out"):
            cmd += ["--out", a["out"]]
        return cmd
    if name == "pitchcomet_pipeline":
        cmd = py + [os.path.join(HERE, "run_pipeline.py"), "--project", _abs(a["project"])]
        for th in a.get("themes") or []:
            cmd += ["--theme", th]
        if a.get("pattern"):
            cmd += ["--pattern", a["pattern"]]
        if not a.get("render"):
            cmd.append("--no-render")
        return cmd
    if name == "pitchcomet_qa":
        if not a.get("pptx") and not a.get("docx"):
            raise ValueError("pitchcomet_qa needs pptx and/or docx")
        cmd = py + [os.path.join(HERE, "qa_check.py")]
        for k in ("pptx", "docx", "facts"):
            if a.get(k):
                cmd += [f"--{k}", _abs(a[k])]
        for k in ("locale", "pattern"):
            if a.get(k):
                cmd += [f"--{k}", a[k]]
        return cmd
    if name == "pitchcomet_metric":
        cmd = py + [os.path.join(HERE, "metrics_calc.py"), a["metric"]]
        if a["metric"] != "list":
            cmd += ["--json", json.dumps(a.get("args") or {})]
        if a.get("locale"):
            cmd += ["--locale", a["locale"]]
        return cmd
    # pitchcomet_glossary
    cmd = py + [os.path.join(HERE, "glossary.py"), "detect", "--locale", a.get("locale") or "en"]
    if a.get("pptx"):
        cmd += ["--pptx", _abs(a["pptx"])]
    elif a.get("docx"):
        cmd += ["--docx", _abs(a["docx"])]
    else:
        cmd += ["--text", a.get("text") or ""]
    return cmd


def call_tool(name: str, args: dict | None = None, timeout: int = 900) -> dict:
    cmd = build_command(name, args or {})
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    res = {"ok": p.returncode == 0, "returncode": p.returncode, "command": cmd,
           "stdout": p.stdout[-20000:], "stderr": p.stderr[-4000:]}
    try:
        res["json"] = json.loads(p.stdout)
    except (ValueError, TypeError):
        pass
    if name == "pitchcomet_glossary" and isinstance(res.get("json"), list):
        sys.path.insert(0, HERE)
        import glossary  # noqa: E402
        res["json"] = glossary.entries(res["json"], (args or {}).get("locale") or "en")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["schemas", "call"])
    ap.add_argument("tool", nargs="?")
    ap.add_argument("--format", choices=["functions", "mcp"], default="functions")
    ap.add_argument("--args", default="{}", help="JSON object with the tool arguments")
    a = ap.parse_args(argv)
    if a.cmd == "schemas":
        print(json.dumps(schemas(a.format), ensure_ascii=False, indent=2))
        return 0
    if not a.tool:
        ap.error("call needs a tool name")
    res = call_tool(a.tool, json.loads(a.args))
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
