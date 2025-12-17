# Changelog

## 2025-12-17 — GitHub/CI hygiene pass

- Fixed missing `.gitmodules` so `apps/frappe`, `apps/erpnext`, `apps/ferum_custom` submodules work on fresh clones.
- Stopped tracking local/runtime artifacts (notably `env_ci/`, `sites/`, `build/`, `.pre-commit-cache/`).
- Standardized GitHub configuration to live in the app repo (`apps/ferum_custom/.github`) instead of the bench root.
- Added `make mcp` / `make mcp-venv` for Codex/MCP FastMCP workflow.
