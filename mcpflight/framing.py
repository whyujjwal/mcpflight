"""Stdio message framing: MCP/LSP Content-Length and newline-delimited JSON."""

from __future__ import annotations

from typing import BinaryIO, Literal

FramingMode = Literal["content-length", "newline"]

_CONTENT_LENGTH_PREFIX = b"content-length:"


def format_content_length(body: bytes) -> bytes:
    """Encode a message body with Content-Length headers."""
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def format_newline(body: bytes) -> bytes:
    """Encode a message body as a single newline-terminated line."""
    return body + b"\n"


def write_message(stream: BinaryIO, body: bytes, mode: FramingMode) -> None:
    """Write one framed message to *stream*."""
    if mode == "content-length":
        stream.write(format_content_length(body))
    else:
        stream.write(format_newline(body))
    stream.flush()


class FramedReader:
    """Read JSON-RPC message bodies from a byte stream with auto-detected framing."""

    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self._buf = bytearray()
        self._mode: FramingMode | None = None

    @property
    def mode(self) -> FramingMode | None:
        """Framing mode after the first message, else None."""
        return self._mode

    def read(self) -> bytes | None:
        """Read one message body, or None at EOF with no pending data."""
        if self._mode is None:
            self._fill(1)
            if not self._buf:
                return None
            self._mode = (
                "content-length"
                if _starts_with_content_length(self._buf)
                else "newline"
            )

        if self._mode == "content-length":
            return self._read_content_length()
        return self._read_newline()

    def _fill(self, min_size: int) -> None:
        while len(self._buf) < min_size:
            chunk = self._stream.read(4096)
            if not chunk:
                return
            self._buf.extend(chunk)

    def _take(self, n: int) -> bytes:
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def _read_line(self) -> bytes | None:
        while True:
            for i, b in enumerate(self._buf):
                if b == ord(b"\n"):
                    return self._take(i + 1).rstrip(b"\r\n")
            chunk = self._stream.read(4096)
            if not chunk:
                if self._buf:
                    return self._take(len(self._buf)).rstrip(b"\r\n")
                return None
            self._buf.extend(chunk)

    def _read_content_length(self) -> bytes | None:
        while True:
            for sep in (b"\r\n\r\n", b"\n\n"):
                idx = self._buf.find(sep)
                if idx >= 0:
                    header_block = self._take(idx + len(sep))
                    length = _parse_content_length(header_block)
                    if length is None:
                        raise ValueError("Content-Length header missing or invalid")
                    self._fill(length)
                    if len(self._buf) < length:
                        extra = self._stream.read(length - len(self._buf))
                        if not extra:
                            return None
                        self._buf.extend(extra)
                    return self._take(length)

            chunk = self._stream.read(4096)
            if not chunk:
                return None
            self._buf.extend(chunk)

    def _read_newline(self) -> bytes | None:
        while True:
            line = self._read_line()
            if line is None:
                return None
            if line:
                return line


def _starts_with_content_length(buf: bytearray) -> bool:
    stripped = bytes(buf).lstrip()
    return stripped.lower().startswith(_CONTENT_LENGTH_PREFIX)


def _parse_content_length(header_block: bytes) -> int | None:
    for line in header_block.split(b"\n"):
        stripped = line.strip(b"\r")
        if stripped.lower().startswith(_CONTENT_LENGTH_PREFIX):
            _, _, value = stripped.partition(b":")
            try:
                return int(value.strip())
            except ValueError:
                return None
    return None
