#!/usr/bin/env python3
"""Minimal MCP-like stdio server for local MCPFlight testing.

Reads newline-delimited JSON-RPC from stdin and responds with stub MCP messages.
"""

from __future__ import annotations

import json
import sys


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def handle(message: dict) -> None:
    method = message.get("method")
    msg_id = message.get("id")

    if method == "initialize":
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "echo-mcp", "version": "0.1.0"},
                },
            }
        )
        return

    if method == "tools/list":
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "echo",
                            "description": "Echo text back",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"text": {"type": "string"}},
                                "required": ["text"],
                            },
                        }
                    ]
                },
            }
        )
        return

    if method == "tools/call":
        params = message.get("params") or {}
        text = params.get("arguments", {}).get("text", "")
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        )
        return

    if method == "notifications/initialized":
        return

    if msg_id is not None:
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        )


def main() -> None:
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            message = json.loads(stripped)
        except json.JSONDecodeError:
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        if isinstance(message, dict):
            handle(message)


if __name__ == "__main__":
    main()
