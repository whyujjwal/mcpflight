"""Tests for trace summarization and formatting."""

import json
from pathlib import Path

from mcpflight.models import TraceEvent
from mcpflight.store import write_events
from mcpflight.summarize import filter_events, format_event, format_tail, summarize_events, summarize_trace


def _event(direction: str, payload: dict, **extra) -> TraceEvent:
    from mcpflight.parser import build_trace_event

    raw = json.dumps(payload)
    return build_trace_event(
        event_id=extra.get("event_id", "e"),
        session_id="s",
        timestamp=extra.get("timestamp", "2026-05-22T10:00:00+00:00"),
        direction=direction,
        raw=raw,
    )


def test_summarize_events():
    events = [
        _event("client_to_server", {"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        _event("server_to_client", {"jsonrpc": "2.0", "id": 1, "result": {}}),
        _event("client_to_server", {"jsonrpc": "2.0", "method": "notifications/initialized"}),
        _event("client_to_server", {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        _event("server_to_client", {"jsonrpc": "2.0", "id": 2, "result": {"tools": []}}),
        _event(
            "server_to_client",
            {"jsonrpc": "2.0", "id": 3, "error": {"code": -32601, "message": "nope"}},
        ),
    ]
    summary = summarize_events(events)
    assert summary.total_events == 6
    assert summary.request_count == 2
    assert summary.response_count == 3
    assert summary.notification_count == 1
    assert summary.error_count == 1
    assert summary.method_counts == {"initialize": 1, "tools/list": 1, "notifications/initialized": 1}
    assert summary.distinct_methods == ["initialize", "notifications/initialized", "tools/list"]
    assert summary.first_timestamp == "2026-05-22T10:00:00+00:00"


def test_summarize_trace_file(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    events = [
        _event("client_to_server", {"jsonrpc": "2.0", "id": 1, "method": "ping"}),
        _event("server_to_client", {"jsonrpc": "2.0", "id": 1, "result": "pong"}),
    ]
    write_events(trace, events)
    summary = summarize_trace(trace)
    assert summary.total_events == 2
    assert summary.request_count == 1
    assert summary.response_count == 1


def test_format_event_and_tail():
    events = [
        _event("client_to_server", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
        _event("server_to_client", {"jsonrpc": "2.0", "id": 1, "result": {}}),
    ]
    line = format_event(events[0])
    assert "→" in line
    assert "tools/list" in line
    tail = format_tail(events, last=1)
    assert "result" in tail


def test_filter_events_by_method():
    events = [
        _event("client_to_server", {"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        _event("server_to_client", {"jsonrpc": "2.0", "id": 1, "result": {}}),
        _event("client_to_server", {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
    ]
    filtered = filter_events(events, method="tools/list")
    assert len(filtered) == 1
    assert filtered[0].method == "tools/list"


def test_filter_events_errors_only():
    events = [
        _event("server_to_client", {"jsonrpc": "2.0", "id": 1, "result": {}}),
        _event(
            "server_to_client",
            {"jsonrpc": "2.0", "id": 2, "error": {"code": -32601, "message": "nope"}},
        ),
    ]
    filtered = filter_events(events, errors_only=True)
    assert len(filtered) == 1
    assert filtered[0].has_error is True


def test_format_tail_with_filters():
    events = [
        _event("client_to_server", {"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        _event("client_to_server", {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        _event(
            "server_to_client",
            {"jsonrpc": "2.0", "id": 3, "error": {"code": -32601, "message": "nope"}},
        ),
    ]
    assert "tools/list" in format_tail(events, method="tools/list")
    assert "ERROR" in format_tail(events, errors_only=True)
    assert format_tail(events, method="missing") == "(no matching events)"
