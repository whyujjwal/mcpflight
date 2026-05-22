"""MCPFlight CLI — record, summarize, and tail MCP session traces."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from mcpflight import __version__
from mcpflight.proxy import run_proxy
from mcpflight.summarize import format_tail, summarize_trace
from mcpflight.store import load_events

app = typer.Typer(
    name="mcpflight",
    help="Transparent flight recorder for MCP stdio sessions.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mcpflight {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """MCPFlight records and inspects MCP stdio traffic."""


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def record(
    ctx: typer.Context,
    trace: Path = typer.Option(..., "--trace", help="Output JSONL trace file path."),
) -> None:
    """Launch a child MCP server, proxy stdio, and record every message."""
    if not ctx.args:
        typer.echo("Error: provide a command after `--`, e.g.:\n  mcpflight record --trace out.jsonl -- python server.py", err=True)
        raise typer.Exit(1)

    exit_code = run_proxy(list(ctx.args), trace)
    raise typer.Exit(code=exit_code)


@app.command()
def summarize(
    trace: Path = typer.Argument(..., help="JSONL trace file to summarize."),
) -> None:
    """Print aggregate statistics for a captured session."""
    if not trace.exists():
        typer.echo(f"Error: trace file not found: {trace}", err=True)
        raise typer.Exit(1)

    summary = summarize_trace(trace)
    typer.echo(summary.to_text())


@app.command()
def tail(
    trace: Path = typer.Argument(..., help="JSONL trace file to inspect."),
    last: int = typer.Option(10, "--last", "-n", help="Number of recent events to show."),
) -> None:
    """Pretty-print the last N events from a trace."""
    if not trace.exists():
        typer.echo(f"Error: trace file not found: {trace}", err=True)
        raise typer.Exit(1)

    events = load_events(trace)
    typer.echo(format_tail(events, last=last))


if __name__ == "__main__":
    app()
