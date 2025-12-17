# Changelog

## 2025-12-17 — GitHub/CI hygiene pass

- Fixed missing `.gitmodules` so `apps/frappe`, `apps/erpnext`, `apps/ferum_custom` submodules work on fresh clones.
- Stopped tracking local/runtime artifacts (notably `env_ci/`, `sites/`, `build/`, `.pre-commit-cache/`).
- Standardized GitHub configuration to live in the app repo (`apps/ferum_custom/.github`) instead of the bench root.
- Added `make mcp` / `make mcp-venv` for Codex/MCP FastMCP workflow.

### Added

- Service Report: strict attachment validation on validate (require at least one image and one PDF act) and automatic linking of `Custom Attachment` to the report for Drive sync.
- Data patch `v15_1.sync_service_report_attachment_links` to backfill attachment links for existing Service Reports (idempotent).
- Audit comment on Issue when a Timesheet is submitted and linked.
- Telegram: generic JWT-protected upload endpoints for attaching files to Issue/Timesheet.
- Telegram: Aiogram 3 bot scaffold with handlers, inline buttons, Frappe API client, Docker/systemd configs.
- Patch `v15_1.bootstrap_telegram_settings` to seed Telegram settings defaults (idempotent).
- Telegram: `Telegram User Link` DocType for mapping ERPNext users to Telegram chat IDs and admin flag; webhook now impersonates mapped user.

### Improved

- Google Drive consistency by ensuring all attachments referenced by Timesheet are linked and synchronized under `/Customer/Project/Reports`.
- Telegram webhook hardened with official secret header verification.
