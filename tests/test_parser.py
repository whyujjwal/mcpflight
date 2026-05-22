"""Tests for JSON-RPC line parsing."""

import json

from mcpflight.parser import (
    build_trace_event,
    is_notification,
    is_request,
    is_response,
    parse_jsonrpc_line,
)


def test_parse_request():
    raw = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    parsed = parse_jsonrpc_line(raw)
    assert parsed.is_json is True
    assert parsed.jsonrpc == "2.0"
    assert parsed.rpc_id == 1
    assert parsed.method == "tools/list"
    assert parsed.has_result is False
    assert parsed.has_error is False


def test_parse_response():
    raw = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": []}})
    parsed = parse_jsonrpc_line(raw)
    assert parsed.is_json is True
    assert parsed.has_result is True
    assert parsed.method is None


def test_parse_error_response():
    raw = json.dumps({"jsonrpc": "2.0", "id": 2, "error": {"code": -32601, "message": "not found"}})
    parsed = parse_jsonrpc_line(raw)
    assert parsed.has_error is True
    assert parsed.error == {"code": -32601, "message": "not found"}


def test_parse_notification():
    raw = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
    parsed = parse_jsonrpc_line(raw)
    assert parsed.method == "notifications/initialized"
    assert parsed.rpc_id is None


def test_parse_invalid_json():
    parsed = parse_jsonrpc_line("not json at all")
    assert parsed.is_json is False


def test_parse_non_object_json():
    parsed = parse_jsonrpc_line("[1, 2, 3]")
    assert parsed.is_json is False


def test_build_trace_event():
    raw = json.dumps({"jsonrpc": "2.0", "id": "abc", "method": "initialize"})
    event = build_trace_event(
        event_id="e1",
        session_id="s1",
        timestamp="2026-05-22T00:00:00+00:00",
        direction="client_to_server",
        raw=raw + "\n",
    )
    assert event.event_id == "e1"
    assert event.session_id == "s1"
    assert event.direction == "client_to_server"
    assert event.is_json is True
    assert event.method == "initialize"
    assert event.rpc_id == "abc"


def test_event_classification():
    req = build_trace_event(
        event_id="e1",
        session_id="s1",
        timestamp="t",
        direction="client_to_server",
        raw=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}),
    )
    resp = build_trace_event(
        event_id="e2",
        session_id="s1",
        timestamp="t",
        direction="server_to_client",
        raw=json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}),
    )
    notif = build_trace_event(
        event_id="e3",
        session_id="s1",
        timestamp="t",
        direction="client_to_server",
        raw=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
    )
    assert is_request(req)
    assert is_response(resp)
    assert is_notification(notif)
