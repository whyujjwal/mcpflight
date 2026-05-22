"""Tests for CLI commands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from mcpflight.cli import app
from mcpflight.store import write_events
from mcpflight.parser import build_trace_event

runner = CliRunner()


def _make_trace(path: Path) -> None:
    events = [
        build_trace_event(
            event_id="e1",
            session_id="s1",
            timestamp="2026-05-22T10:00:00+00:00",
            direction="client_to_server",
            raw=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        ),
        build_trace_event(
            event_id="e2",
            session_id="s1",
            timestamp="2026-05-22T10:00:01+00:00",
            direction="server_to_client",
            raw=json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}),
        ),
    ]
    write_events(path, events)


def test_cli_summarize(tmp_path: Path):
    trace = tmp_path / "session.jsonl"
    _make_trace(trace)
    result = runner.invoke(app, ["summarize", str(trace)])
    assert result.exit_code == 0
    assert "Total events:      2" in result.output
    assert "Requests:          1" in result.output


def test_cli_tail(tmp_path: Path):
    trace = tmp_path / "session.jsonl"
    _make_trace(trace)
    result = runner.invoke(app, ["tail", str(trace), "--last", "1"])
    assert result.exit_code == 0
    assert "result" in result.output


def test_cli_tail_method_filter(tmp_path: Path):
    trace = tmp_path / "session.jsonl"
    _make_trace(trace)
    result = runner.invoke(app, ["tail", str(trace), "--method", "initialize"])
    assert result.exit_code == 0
    assert "initialize" in result.output
    assert "result" not in result.output


def test_cli_tail_errors_only(tmp_path: Path):
    trace = tmp_path / "session.jsonl"
    events = [
        build_trace_event(
            event_id="e1",
            session_id="s1",
            timestamp="2026-05-22T10:00:00+00:00",
            direction="server_to_client",
            raw=json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}),
        ),
        build_trace_event(
            event_id="e2",
            session_id="s1",
            timestamp="2026-05-22T10:00:01+00:00",
            direction="server_to_client",
            raw=json.dumps(
                {"jsonrpc": "2.0", "id": 2, "error": {"code": -32601, "message": "nope"}}
            ),
        ),
    ]
    write_events(trace, events)
    result = runner.invoke(app, ["tail", str(trace), "--errors-only"])
    assert result.exit_code == 0
    assert "ERROR" in result.output
    assert "result" not in result.output


def test_cli_summarize_missing_file(tmp_path: Path):
    result = runner.invoke(app, ["summarize", str(tmp_path / "nope.jsonl")])
    assert result.exit_code == 1


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
