# MCPFlight MVP Implementation Plan

> **For Cursor/Hermes:** Build this as a sharp, timely open-source developer tool.

**Goal:** Build a transparent flight recorder for MCP servers that can sit between an MCP client and a child stdio server, log every JSON-RPC message, and produce useful local summaries for developers debugging agent tool traffic.

**Architecture:** MCPFlight is a Python CLI that launches a target MCP server as a subprocess, proxies stdio traffic bidirectionally, records every request/response/notification as structured events, and writes a session JSONL trace. A second CLI command summarizes or pretty-prints a captured session for fast debugging.

**Tech Stack:** Python 3.11, Typer, Pydantic, pytest.

---

## Why this project is interesting right now
MCP is exploding across coding agents, browser tools, and hosted runtimes. What’s still weak is **observability**: developers can connect MCP servers, but debugging live traffic is painful. A transparent recorder/proxy is timely, technically interesting, and highly relevant to the latest agent infrastructure wave.

## Product idea
### MCPFlight
A local developer tool that acts like a Wireshark/flight-recorder layer for MCP stdio sessions.

### Core value
- capture real MCP traffic without modifying the server
- inspect tool calls, resources, prompts, and errors
- generate shareable traces for debugging
- help developers understand what agents are actually sending

## MVP scope
### Required capabilities
1. Launch a child MCP server command.
2. Proxy stdin/stdout between parent/client and child process.
3. Record structured events with:
   - timestamp
   - direction (`client_to_server`, `server_to_client`)
   - raw line
   - parsed JSON-RPC fields when possible (`id`, `method`, `params`, `result`, `error`)
4. Persist each event to a session JSONL file.
5. Provide CLI commands to:
   - record a session
   - summarize a trace file
   - pretty-print the last N events
6. Include tests for JSON-RPC parsing, trace storage, and summarization.

### Explicitly out of scope for MVP
- GUI/web dashboard
- network transport (HTTP/SSE/WebSocket)
- trace diffing across sessions
- live browser viewer
- auth / cloud sync

## Suggested file layout
- `pyproject.toml`
- `README.md`
- `mcpflight/__init__.py`
- `mcpflight/models.py`
- `mcpflight/parser.py`
- `mcpflight/store.py`
- `mcpflight/proxy.py`
- `mcpflight/summarize.py`
- `mcpflight/cli.py`
- `examples/echo_mcp_server.py`
- `tests/test_parser.py`
- `tests/test_store.py`
- `tests/test_summarize.py`

## Behavior details
### Recording behavior
- support a command like:
  - `mcpflight record --trace traces/session.jsonl -- python examples/echo_mcp_server.py`
- the recorder should spawn the child process and proxy stdio
- every line should be preserved even if JSON parsing fails
- valid JSON-RPC messages should be parsed into structured fields

### Trace format
Each event line should include:
- `event_id`
- `session_id`
- `timestamp`
- `direction`
- `raw`
- `is_json`
- `jsonrpc`
- `id`
- `method`
- `has_result`
- `has_error`

### Summary behavior
A summary command should report:
- total events
- request/response counts
- method counts
- error count
- first/last timestamp
- distinct methods seen

### Pretty print behavior
A tail/show command should print a readable human summary of recent events.

## Implementation priorities
### Task 1: scaffold project
- package layout
- `pyproject.toml`
- README with concept and quickstart

### Task 2: models and parser
- Pydantic models for trace events
- parse raw lines into structured JSON-RPC event metadata
- tests for requests, responses, notifications, invalid JSON

### Task 3: store
- append JSONL trace events
- load/replay events from disk
- tests

### Task 4: summarizer
- summary stats from trace file
- human-readable formatting
- tests

### Task 5: proxy recorder
- launch child command
- bidirectional proxy with trace capture
- keep implementation simple and correct

### Task 6: CLI
- `mcpflight record --trace ... -- <command...>`
- `mcpflight summarize <trace>`
- `mcpflight tail <trace>`

### Task 7: example server
- tiny example stdio server that emits MCP-like JSON-RPC messages for local manual testing

## Verification
Use commands like:
- `python3 -m pip install -e '.[dev]'`
- `pytest -q`
- `python3 -m mcpflight.cli summarize <sample-trace>`
- manual record test using the example echo server

## Success criteria
MVP is successful if:
- a developer can record a session against a child stdio server
- events are stored as JSONL
- summaries work on saved traces
- parser behavior is tested and correct
- README makes the value obvious to GitHub readers
