# MCPFlight Agent Instructions

- Read `docs/plans/2026-05-22-mcpflight-mvp.md` before making major changes.
- Keep the MVP narrow: a transparent MCP stdio recorder/proxy with useful trace inspection.
- Prefer Python 3.11 with Typer and pytest for the first version.
- Make small, reviewable changes.
- Add or update tests for parser, trace storage, and CLI behavior.
- Prefer clear protocol handling over ambitious abstractions.
- Do not add a full web UI in the first pass unless the core recorder already works.
- Verify with the narrowest useful tests after edits.
