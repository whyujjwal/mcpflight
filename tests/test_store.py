"""Tests for JSONL trace storage."""

import json
from pathlib import Path

from mcpflight.models import TraceEvent
from mcpflight.store import TraceStore, load_events, write_events


def _sample_event(**overrides) -> TraceEvent:
    data = {
        "event_id": "evt-1",
        "session_id": "sess-1",
        "timestamp": "2026-05-22T10:00:00+00:00",
        "direction": "client_to_server",
        "raw": '{"jsonrpc":"2.0","id":1,"method":"tools/list"}',
        "is_json": True,
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "has_result": False,
        "has_error": False,
    }
    data.update(overrides)
    return TraceEvent.model_validate(data)


def test_trace_store_append(tmp_path: Path):
    trace_file = tmp_path / "session.jsonl"
    store = TraceStore(trace_file, session_id="sess-test")

    event = store.append(
        direction="client_to_server",
        raw='{"jsonrpc":"2.0","id":1,"method":"initialize"}\n',
        timestamp="2026-05-22T10:00:00+00:00",
    )

    assert event.session_id == "sess-test"
    assert store.event_count == 1
    assert trace_file.exists()

    lines = trace_file.read_text().strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["method"] == "initialize"
    assert record["id"] == 1


def test_load_events_roundtrip(tmp_path: Path):
    trace_file = tmp_path / "session.jsonl"
    events = [
        _sample_event(event_id="e1"),
        _sample_event(
            event_id="e2",
            direction="server_to_client",
            raw='{"jsonrpc":"2.0","id":1,"result":{}}',
            method=None,
            has_result=True,
        ),
    ]
    write_events(trace_file, events)
    loaded = load_events(trace_file)
    assert len(loaded) == 2
    assert loaded[0].event_id == "e1"
    assert loaded[1].has_result is True


def test_load_missing_file(tmp_path: Path):
    assert load_events(tmp_path / "missing.jsonl") == []
