#!/usr/bin/env python3
"""mcp_server.py — a minimal Model Context Protocol server for PitchComet (stdio, no dependencies).

It exposes the six tools of agent_tools.py (plan, build, pipeline, qa, metric, glossary) over
JSON-RPC 2.0, one message per line on stdin/stdout, as described in the MCP specification
(https://modelcontextprotocol.io). Methods: initialize, ping, tools/list, tools/call.

Client configuration (any MCP client that starts stdio servers):

  {"mcpServers": {"pitchcomet": {"command": "python",
                                 "args": ["/path/to/pitchcomet/tools/mcp_server.py"]}}}

The server runs the local command-line tools with the paths the client passes; it opens no
network connections itself. Run it only for clients you trust with your file system.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_tools  # noqa: E402

SUPPORTED = ["2025-06-18", "2025-03-26", "2024-11-05"]
VERSION = "0.1b0"


def handle(msg: dict) -> dict | None:
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:  # notification (e.g. notifications/initialized)
        return None

    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def err(code, text):
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": text}}

    params = msg.get("params") or {}
    if method == "initialize":
        want = params.get("protocolVersion")
        return ok({"protocolVersion": want if want in SUPPORTED else SUPPORTED[0],
                   "capabilities": {"tools": {"listChanged": False}},
                   "serverInfo": {"name": "pitchcomet", "version": VERSION}})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": agent_tools.schemas("mcp")})
    if method == "tools/call":
        name = params.get("name")
        try:
            res = agent_tools.call_tool(name, params.get("arguments") or {})
        except (ValueError, KeyError) as e:
            return err(-32602, f"invalid arguments: {e}")
        except Exception as e:  # tool crashed or timed out: report as a tool error, keep serving
            return ok({"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True})
        body = res.get("json", res["stdout"])
        text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, indent=1)
        if not res["ok"]:
            text = f"exit code {res['returncode']}\n{text}\n{res['stderr']}"
        return ok({"content": [{"type": "text", "text": text}], "isError": not res["ok"]})
    return err(-32601, f"method not found: {method}")


def serve(inp=sys.stdin, out=sys.stdout) -> None:
    for line in inp:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = handle(msg) if isinstance(msg, dict) else \
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}}
        if reply is not None:
            out.write(json.dumps(reply, ensure_ascii=False) + "\n")
            out.flush()


if __name__ == "__main__":
    serve()
