"""Bidirectional stdio proxy with trace capture."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

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
        stderr=sys.stderr,
        text=True,
        bufsize=1,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    stop = threading.Event()

    def client_to_server() -> None:
        try:
            for line in sys.stdin:
                store.append(direction="client_to_server", raw=line)
                proc.stdin.write(line)
                proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass
            stop.set()

    def server_to_client() -> None:
        try:
            for line in proc.stdout:
                store.append(direction="server_to_client", raw=line)
                sys.stdout.write(line)
                sys.stdout.flush()
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
