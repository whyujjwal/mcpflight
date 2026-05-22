"""JSONL trace storage for session events."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcpflight.models import TraceEvent
from mcpflight.parser import build_trace_event


def new_session_id() -> str:
    return str(uuid.uuid4())


def new_event_id() -> str:
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceStore:
    """Append-only JSONL store for a single recording session."""

    def __init__(self, path: Path, session_id: str | None = None) -> None:
        self.path = path
        self.session_id = session_id or new_session_id()
        self._event_counter = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        direction: str,
        raw: str,
        timestamp: str | None = None,
    ) -> TraceEvent:
        self._event_counter += 1
        event = build_trace_event(
            event_id=new_event_id(),
            session_id=self.session_id,
            timestamp=timestamp or utc_now_iso(),
            direction=direction,
            raw=raw,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json(by_alias=True) + "\n")
        return event

    @property
    def event_count(self) -> int:
        return self._event_counter


def load_events(path: Path) -> list[TraceEvent]:
    """Load all trace events from a JSONL file."""
    if not path.exists():
        return []

    events: list[TraceEvent] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            events.append(TraceEvent.model_validate_json(stripped))
    return events


def write_events(path: Path, events: list[TraceEvent]) -> None:
    """Write a list of events to a JSONL file (used by tests)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(event.model_dump_json(by_alias=True) + "\n")
