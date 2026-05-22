"""Summarize and pretty-print captured session traces."""

from __future__ import annotations

from pathlib import Path

from mcpflight.models import SessionSummary, TraceEvent
from mcpflight.parser import is_notification, is_request, is_response
from mcpflight.store import load_events


def summarize_events(events: list[TraceEvent]) -> SessionSummary:
    """Compute aggregate statistics from a list of trace events."""
    method_counts: dict[str, int] = {}
    request_count = 0
    response_count = 0
    notification_count = 0
    error_count = 0

    for event in events:
        if is_notification(event):
            notification_count += 1
            if event.method:
                method_counts[event.method] = method_counts.get(event.method, 0) + 1
        elif is_request(event):
            request_count += 1
            if event.method:
                method_counts[event.method] = method_counts.get(event.method, 0) + 1
        elif is_response(event):
            response_count += 1

        if event.has_error:
            error_count += 1

    timestamps = [event.timestamp for event in events]
    return SessionSummary(
        total_events=len(events),
        request_count=request_count,
        response_count=response_count,
        notification_count=notification_count,
        error_count=error_count,
        method_counts=method_counts,
        distinct_methods=sorted(method_counts.keys()),
        first_timestamp=timestamps[0] if timestamps else None,
        last_timestamp=timestamps[-1] if timestamps else None,
    )


def summarize_trace(path: Path) -> SessionSummary:
    """Load a trace file and return its summary."""
    return summarize_events(load_events(path))


def format_event(event: TraceEvent) -> str:
    """Return a single-line human-readable description of an event."""
    arrow = "→" if event.direction == "client_to_server" else "←"
    parts = [f"{arrow} {event.timestamp}"]

    if not event.is_json:
        preview = event.raw[:80] + ("…" if len(event.raw) > 80 else "")
        parts.append(f"raw: {preview!r}")
        return "  ".join(parts)

    if event.method:
        parts.append(f"method={event.method}")
    if event.rpc_id is not None:
        parts.append(f"id={event.rpc_id!r}")
    if event.has_result:
        parts.append("result")
    if event.has_error:
        parts.append("ERROR")

    return "  ".join(parts)


def filter_events(
    events: list[TraceEvent],
    *,
    method: str | None = None,
    errors_only: bool = False,
) -> list[TraceEvent]:
    """Return events matching optional inspection filters."""
    filtered = events
    if method is not None:
        filtered = [event for event in filtered if event.method == method]
    if errors_only:
        filtered = [event for event in filtered if event.has_error]
    return filtered


def format_tail(
    events: list[TraceEvent],
    last: int = 10,
    *,
    method: str | None = None,
    errors_only: bool = False,
) -> str:
    """Format the last N events for display."""
    filtered = filter_events(events, method=method, errors_only=errors_only)
    if not filtered:
        return "(no matching events)" if (method is not None or errors_only) else "(no events)"
    tail = filtered[-last:]
    lines = [format_event(event) for event in tail]
    return "\n".join(lines)
