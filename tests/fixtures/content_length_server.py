#!/usr/bin/env python3
"""Minimal Content-Length stdio server for proxy integration tests."""

from __future__ import annotations

import json
import sys

from mcpflight.framing import FramedReader, write_message


def send(stream, mode, message: dict) -> None:
    write_message(stream, json.dumps(message).encode(), mode)


def handle(message: dict) -> dict | None:
    method = message.get("method")
    msg_id = message.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "cl-mcp", "version": "0.1.0"},
            },
        }

    if method == "tools/list":
        return {
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

    if method == "tools/call":
        params = message.get("params") or {}
        text = params.get("arguments", {}).get("text", "")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"content": [{"type": "text", "text": text}]},
        }

    if method == "notifications/initialized":
        return None

    if msg_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    return None


def main() -> None:
    reader = FramedReader(sys.stdin.buffer)
    while True:
        body = reader.read()
        if body is None:
            break
        mode = reader.mode
        assert mode is not None
        message = json.loads(body)
        if isinstance(message, dict):
            response = handle(message)
            if response is not None:
                send(sys.stdout.buffer, mode, response)


if __name__ == "__main__":
    main()
