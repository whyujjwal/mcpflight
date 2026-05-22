#!/usr/bin/env python3
"""Minimal Content-Length stdio server for proxy integration tests."""

from __future__ import annotations

import json
import sys

from mcpflight.framing import FramedReader, write_message


def main() -> None:
    reader = FramedReader(sys.stdin.buffer)
    while True:
        body = reader.read()
        if body is None:
            break
        mode = reader.mode
        assert mode is not None
        message = json.loads(body)
        method = message.get("method")
        msg_id = message.get("id")
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"protocolVersion": "2024-11-05", "capabilities": {}},
            }
            out = json.dumps(response).encode()
            write_message(sys.stdout.buffer, out, mode)


if __name__ == "__main__":
    main()
