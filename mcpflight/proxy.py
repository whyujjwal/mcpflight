"""Bidirectional stdio proxy with trace capture."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

from mcpflight.framing import FramedReader, write_message
from mcpflight.store import TraceStore


def run_proxy(
    command: list[str],
    trace_path: Path,
    *,
    session_id: str | None = None,
) -> int:
    """Launch *command*, proxy stdio, record events, return child exit code."""
    store = TraceStore(trace_path, session_id=session_id)

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr.buffer,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    stop = threading.Event()

    def client_to_server() -> None:
        reader = FramedReader(sys.stdin.buffer)
        try:
            while True:
                body = reader.read()
                if body is None:
                    break
                mode = reader.mode
                assert mode is not None
                store.append(direction="client_to_server", raw=body.decode("utf-8"))
                write_message(proc.stdin, body, mode)
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass
            stop.set()

    def server_to_client() -> None:
        reader = FramedReader(proc.stdout)
        try:
            while True:
                body = reader.read()
                if body is None:
                    break
                mode = reader.mode
                assert mode is not None
                store.append(direction="server_to_client", raw=body.decode("utf-8"))
                write_message(sys.stdout.buffer, body, mode)
        except (BrokenPipeError, OSError):
            pass
        finally:
            stop.set()

    t_in = threading.Thread(target=client_to_server, daemon=True)
    t_out = threading.Thread(target=server_to_client, daemon=True)
    t_in.start()
    t_out.start()

    t_in.join()
    t_out.join()
    return proc.wait()
