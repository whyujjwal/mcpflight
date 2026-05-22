"""Integration tests for stdio proxy framing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mcpflight.framing import format_content_length, format_newline
from mcpflight.store import load_events

_REPO_ROOT = Path(__file__).resolve().parents[1]
ECHO_SERVER = _REPO_ROOT / "examples" / "echo_mcp_server.py"
CL_SERVER = _REPO_ROOT / "tests" / "fixtures" / "content_length_server.py"


def _run_record(
    trace: Path,
    server_args: list[str],
    client_messages: list[bytes],
) -> subprocess.CompletedProcess[bytes]:
    cmd = [
        sys.executable,
        "-m",
        "mcpflight.cli",
        "record",
        "--trace",
        str(trace),
        "--",
        *server_args,
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=_REPO_ROOT,
    )
    stdout, stderr = proc.communicate(input=b"".join(client_messages), timeout=10)
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def test_record_newline_echo_server(tmp_path: Path):
    trace = tmp_path / "session.jsonl"
    init = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}
    ).encode()
    result = _run_record(
        trace,
        [sys.executable, str(ECHO_SERVER)],
        [format_newline(init)],
    )
    assert result.returncode == 0
    events = load_events(trace)
    assert len(events) >= 2
    assert events[0].direction == "client_to_server"
    assert events[0].method == "initialize"
    assert any(e.has_result for e in events)


def test_record_full_mcp_session_against_echo_server(tmp_path: Path):
    """End-to-end: record initialize → tools/list → tools/call against the example server."""
    trace = tmp_path / "session.jsonl"
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"text": "hello"}},
        },
    ]
    client_input = [format_newline(json.dumps(m).encode()) for m in messages]
    result = _run_record(
        trace,
        [sys.executable, str(ECHO_SERVER)],
        client_input,
    )

    assert result.returncode == 0
    events = load_events(trace)
    assert len(events) == 7

    client_methods = [e.method for e in events if e.direction == "client_to_server"]
    assert client_methods == [
        "initialize",
        "notifications/initialized",
        "tools/list",
        "tools/call",
    ]

    call_request = next(e for e in events if e.method == "tools/call")
    call_response = next(
        e for e in events if e.direction == "server_to_client" and e.rpc_id == call_request.rpc_id
    )
    assert call_response.has_result is True
    assert "hello" in call_response.raw

    from mcpflight.summarize import summarize_trace

    summary = summarize_trace(trace)
    assert summary.total_events == 7
    assert summary.request_count == 3
    assert summary.response_count == 3
    assert summary.notification_count == 1
    assert summary.error_count == 0
    assert summary.method_counts["tools/call"] == 1

    assert b"hello" in result.stdout


def test_record_content_length_session(tmp_path: Path):
    trace = tmp_path / "session.jsonl"
    init = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}
    ).encode()
    result = _run_record(
        trace,
        [sys.executable, str(CL_SERVER)],
        [format_content_length(init)],
    )
    assert result.returncode == 0
    events = load_events(trace)
    assert len(events) == 2
    assert events[0].method == "initialize"
    assert events[1].has_result is True
    assert events[0].raw.startswith("{")
