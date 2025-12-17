## FastMCP quick facts

- `.fastmcp-venv/` — persistent virtualenv with `fastmcp==2.14.1` for this bench; it lives in the repo tree for locality but is **git-ignored** to avoid noisy diffs and Codex snapshots.
- Run FastMCP in the hardened mode used by Codex: `scripts/run_fastmcp.sh`. It fails fast if the venv is missing or the version differs from 2.14.1.
- The launch flags are fixed to `--skip-env --transport stdio --no-banner` to keep startup fast and predictable.
- Do **not** recreate or upgrade the venv automatically inside scripts; rebuild it manually only when you intentionally bump FastMCP.

## Quick start

- Create the pinned venv: `make mcp-venv` (or `PYTHON_BIN=python3.12 make mcp-venv`)
- Run the MCP server: `make mcp`
