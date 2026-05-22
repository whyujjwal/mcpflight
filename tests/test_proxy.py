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
