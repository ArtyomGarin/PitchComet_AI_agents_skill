"""Tests for the agent integration layer (tools/agent_tools.py, tools/mcp_server.py).

Run from the repository root:  python -m unittest discover -s tools/tests -v
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import agent_tools as A  # noqa: E402
import mcp_server as M  # noqa: E402


class TestSchemas(unittest.TestCase):
    def test_schema_shape(self):
        names = set()
        for fmt, key in (("functions", "parameters"), ("mcp", "inputSchema")):
            for t in A.schemas(fmt):
                self.assertRegex(t["name"], r"^[a-z][a-z0-9_]{2,63}$")
                self.assertGreater(len(t["description"]), 40)
                sch = t[key]
                self.assertEqual(sch["type"], "object")
                for r in sch.get("required", []):
                    self.assertIn(r, sch["properties"])
                names.add(t["name"])
        self.assertEqual(len(names), 6)
        json.dumps(A.schemas("mcp"))  # serialisable

    def test_cli_schemas(self):
        out = subprocess.run([sys.executable, os.path.join(TOOLS, "agent_tools.py"), "schemas", "--format", "mcp"],
                             capture_output=True, text=True, stdin=subprocess.DEVNULL, check=True).stdout
        self.assertEqual(len(json.loads(out)), 6)


class TestCalls(unittest.TestCase):
    def test_metric(self):
        r = A.call_tool("pitchcomet_metric", {"metric": "cagr", "args": {"start": 100, "end": 200, "years": 2}})
        self.assertTrue(r["ok"], r["stderr"])
        self.assertAlmostEqual(r["json"]["value"], 2 ** 0.5 - 1, places=6)

    def test_glossary_definitions(self):
        r = A.call_tool("pitchcomet_glossary", {"text": "LTV/CAC 5x, CAGR 18%", "locale": "ru"})
        ids = [e["id"] for e in r["json"]]
        self.assertTrue({"cagr", "ltv_cac", "ltv", "cac"} <= set(ids))
        self.assertTrue(all(e["text"] for e in r["json"]))

    def test_bad_calls(self):
        with self.assertRaises(ValueError):
            A.call_tool("nope", {})
        with self.assertRaises(ValueError):
            A.call_tool("pitchcomet_qa", {})

    def test_plan_and_qa(self):
        tmp = tempfile.mkdtemp()
        try:
            brief = os.path.join(ROOT, "examples", "autonomous_shiftlyra", "brief_en.json")
            r = A.call_tool("pitchcomet_plan", {"brief": brief, "out": os.path.join(tmp, "plan")})
            self.assertTrue(r["ok"], r["stderr"])
            self.assertTrue(os.path.exists(os.path.join(tmp, "plan", "research_plan.json")))
            out = os.path.join(ROOT, "examples", "example_en", "output")
            r = A.call_tool("pitchcomet_qa", {"pptx": os.path.join(out, "deck.pptx"),
                                              "docx": os.path.join(out, "report.docx"), "locale": "en"})
            self.assertTrue(r["ok"], r["stdout"][-2000:])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestMcp(unittest.TestCase):
    def _session(self, msgs):
        out = io.StringIO()
        M.serve(io.StringIO("\n".join(json.dumps(m) for m in msgs) + "\n"), out)
        return [json.loads(l) for l in out.getvalue().splitlines()]

    def test_handshake_list_call(self):
        rep = self._session([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "pitchcomet_metric", "arguments": {"metric": "moic", "args": {"total_value_returned": 30, "invested": 10}}}},
            {"jsonrpc": "2.0", "id": 4, "method": "nope"},
        ])
        self.assertEqual([r["id"] for r in rep], [1, 2, 3, 4])  # the notification gets no reply
        self.assertEqual(rep[0]["result"]["serverInfo"]["name"], "pitchcomet")
        self.assertEqual(len(rep[1]["result"]["tools"]), 6)
        self.assertFalse(rep[2]["result"]["isError"])
        self.assertIn("3", rep[2]["result"]["content"][0]["text"])
        self.assertEqual(rep[3]["error"]["code"], -32601)

    def test_parse_error(self):
        out = io.StringIO()
        M.serve(io.StringIO("not json\n"), out)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"], -32700)


if __name__ == "__main__":
    unittest.main()
