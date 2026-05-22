# MCPFlight

**A transparent flight recorder for MCP stdio sessions.**

MCPFlight sits between an MCP client and a child stdio server, proxies traffic bidirectionally, and logs every JSON-RPC message to a structured JSONL trace. Summarize or tail captured sessions to debug agent tool traffic fast.

```
  MCP Client                MCPFlight                 Child MCP Server
      │                         │                            │
      │──── JSON-RPC ──────────►│──── JSON-RPC ─────────────►│
      │◄─── JSON-RPC ───────────│◄─── JSON-RPC ──────────────│
      │                         │                            │
      │                         └──► traces/session.jsonl    │
```

## Why MCPFlight?

MCP is everywhere in coding agents, browser tools, and hosted runtimes — but **observability is still weak**. Developers can connect MCP servers, yet debugging live traffic is painful. MCPFlight is a local Wireshark-style layer: capture real traffic without modifying the server, inspect tool calls and errors, and share traces for debugging.

## Quickstart

```bash
# Install (editable, with dev deps)
python3 -m pip install -e '.[dev]'

# Record a session against the bundled example server
mcpflight record --trace traces/session.jsonl -- python examples/echo_mcp_server.py

# In another terminal, send JSON-RPC lines to the recorder's stdin:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | mcpflight record --trace traces/session.jsonl -- python examples/echo_mcp_server.py

# Summarize a trace
mcpflight summarize traces/session.jsonl

# Pretty-print the last 10 events
mcpflight tail traces/session.jsonl --last 10
```

## CLI

| Command | Description |
|---------|-------------|
| `mcpflight record --trace PATH -- COMMAND...` | Launch a child server, proxy stdio, record events |
| `mcpflight summarize TRACE` | Print session statistics |
| `mcpflight tail TRACE [--last N]` | Human-readable view of recent events |

## Trace format

Each line in a session JSONL file is one event:

```json
{
  "event_id": "…",
  "session_id": "…",
  "timestamp": "2026-05-22T12:00:00.000000+00:00",
  "direction": "client_to_server",
  "raw": "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}",
  "is_json": true,
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "has_result": false,
  "has_error": false
}
```

## Development

```bash
pytest -q
```

## License

MIT
