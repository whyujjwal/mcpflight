"""Parse raw JSON-RPC lines into structured metadata."""

from __future__ import annotations

import json

from mcpflight.models import ParsedJsonRpc, TraceEvent


def parse_jsonrpc_line(raw: str) -> ParsedJsonRpc:
    """Parse a single line into JSON-RPC metadata, preserving raw on failure."""
    stripped = raw.rstrip("\n\r")
    if not stripped:
        return ParsedJsonRpc(is_json=False)

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return ParsedJsonRpc(is_json=False)

    if not isinstance(payload, dict):
        return ParsedJsonRpc(is_json=False)

    return ParsedJsonRpc.model_validate(
        {
            "is_json": True,
            "jsonrpc": payload.get("jsonrpc") if isinstance(payload.get("jsonrpc"), str) else None,
            "id": payload.get("id"),
            "method": payload.get("method") if isinstance(payload.get("method"), str) else None,
            "has_result": "result" in payload,
            "has_error": "error" in payload,
            "params": payload.get("params"),
            "result": payload.get("result"),
            "error": payload.get("error"),
        }
    )


def build_trace_event(
    *,
    event_id: str,
    session_id: str,
    timestamp: str,
    direction: str,
    raw: str,
) -> TraceEvent:
    """Create a TraceEvent from a raw line and parsed JSON-RPC fields."""
    parsed = parse_jsonrpc_line(raw)
    return TraceEvent.model_validate(
        {
            "event_id": event_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "direction": direction,
            "raw": raw.rstrip("\n\r"),
            "is_json": parsed.is_json,
            "jsonrpc": parsed.jsonrpc,
            "id": parsed.rpc_id,
            "method": parsed.method,
            "has_result": parsed.has_result,
            "has_error": parsed.has_error,
        }
    )


def is_request(event: TraceEvent) -> bool:
    """Return True when the event looks like a JSON-RPC request."""
    return event.is_json and event.method is not None and not event.has_result and not event.has_error


def is_response(event: TraceEvent) -> bool:
    """Return True when the event looks like a JSON-RPC response."""
    return event.is_json and event.method is None and (event.has_result or event.has_error)


def is_notification(event: TraceEvent) -> bool:
    """Return True when the event looks like a JSON-RPC notification."""
    return (
        event.is_json
        and event.method is not None
        and event.rpc_id is None
        and not event.has_result
        and not event.has_error
    )
