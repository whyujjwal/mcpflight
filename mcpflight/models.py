"""Pydantic models for trace events and summaries."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TraceEvent(BaseModel):
    """One recorded JSON-RPC message in a session trace."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: str
    session_id: str
    timestamp: str
    direction: Literal["client_to_server", "server_to_client"]
    raw: str
    is_json: bool
    jsonrpc: str | None = None
    rpc_id: str | int | None = Field(default=None, alias="id")
    method: str | None = None
    has_result: bool = False
    has_error: bool = False


class SessionSummary(BaseModel):
    """Aggregate statistics for a captured session trace."""

    total_events: int
    request_count: int
    response_count: int
    notification_count: int
    error_count: int
    method_counts: dict[str, int]
    distinct_methods: list[str]
    first_timestamp: str | None
    last_timestamp: str | None

    def to_text(self) -> str:
        lines = [
            f"Total events:      {self.total_events}",
            f"Requests:          {self.request_count}",
            f"Responses:         {self.response_count}",
            f"Notifications:     {self.notification_count}",
            f"Errors:            {self.error_count}",
            f"First timestamp:   {self.first_timestamp or '—'}",
            f"Last timestamp:    {self.last_timestamp or '—'}",
            "",
            "Methods:",
        ]
        if self.method_counts:
            for method, count in sorted(self.method_counts.items()):
                lines.append(f"  {method}: {count}")
        else:
            lines.append("  (none)")
        return "\n".join(lines)


class ParsedJsonRpc(BaseModel):
    """Structured metadata extracted from a JSON-RPC line."""

    is_json: bool
    jsonrpc: str | None = None
    rpc_id: str | int | None = Field(default=None, alias="id")
    method: str | None = None
    has_result: bool = False
    has_error: bool = False
    params: Any | None = None
    result: Any | None = None
    error: Any | None = None
