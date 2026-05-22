"""Tests for stdio Content-Length and newline-delimited framing."""

from __future__ import annotations

import json
from io import BytesIO

from mcpflight.framing import (
    FramedReader,
    format_content_length,
    format_newline,
    write_message,
)


def _msg(**fields: object) -> bytes:
    return json.dumps(fields).encode("utf-8")


def test_format_content_length():
    body = _msg(jsonrpc="2.0", id=1, method="initialize")
    framed = format_content_length(body)
    assert framed.startswith(b"Content-Length: ")
    assert framed.endswith(body)
    assert b"\r\n\r\n" in framed


def test_format_newline():
    body = _msg(jsonrpc="2.0", id=1, method="ping")
    assert format_newline(body) == body + b"\n"


def test_read_content_length_single():
    body = _msg(jsonrpc="2.0", id=1, method="tools/list")
    stream = BytesIO(format_content_length(body))
    reader = FramedReader(stream)
    assert reader.read() == body
    assert reader.mode == "content-length"
    assert reader.read() is None


def test_read_content_length_multiple():
    a = _msg(jsonrpc="2.0", id=1, method="initialize")
    b = _msg(jsonrpc="2.0", id=1, result={})
    stream = BytesIO(format_content_length(a) + format_content_length(b))
    reader = FramedReader(stream)
    assert reader.read() == a
    assert reader.read() == b
    assert reader.read() is None


def test_read_newline_single():
    body = _msg(jsonrpc="2.0", id=1, method="ping")
    stream = BytesIO(format_newline(body))
    reader = FramedReader(stream)
    assert reader.read() == body
    assert reader.mode == "newline"
    assert reader.read() is None


def test_read_newline_skips_empty_lines():
    body = _msg(jsonrpc="2.0", method="notifications/initialized")
    stream = BytesIO(b"\n\n" + format_newline(body))
    reader = FramedReader(stream)
    assert reader.read() == body


def test_read_content_length_utf8_byte_count():
    body = '{"text":"é"}'.encode("utf-8")
    stream = BytesIO(format_content_length(body))
    reader = FramedReader(stream)
    assert reader.read() == body


def test_write_message_roundtrip():
    body = _msg(jsonrpc="2.0", id=2, method="tools/call")
    for mode in ("content-length", "newline"):
        out = BytesIO()
        write_message(out, body, mode)
        reader = FramedReader(BytesIO(out.getvalue()))
        assert reader.read() == body
