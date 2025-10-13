# Ferum Custom App Audit Report

This audit targeted the Frappe/ERPNext v15 custom app located at `apps/ferum_custom`.

- Date: $(date +%Y-%m-%d)
- Scope: Doctypes, fixtures, public assets, patches/migrations, tests, dependencies, hooks
- Result: Conservatively removed confirmed-unused items; left doubtful items in place and documented below.

## Unused Doctypes
- apps/ferum_custom/ferum_custom/ferum_custom/doctype/article — empty folder without a `.json` model (only contained `__pycache__`). Removed.

## Unused Fixtures
- Reviewed `apps/ferum_custom/ferum_custom/fixtures/*.json`.
- No duplicate names within fixture files detected.
- Types present: Workflow, Workflow State, Workflow Action Master, Role, Role Profile, Module Def, Module Profile, Print Format, Dashboard Chart, Report, Document Template, Custom Field.
- Action: Kept all — several are linked to workflows/roles or UI elements.

## Orphan Public Files
- apps/ferum_custom/ferum_custom/public/js/user.js — referenced by hooks (`doctype_js["User"]`). Kept.
- apps/ferum_custom/ferum_custom/public/logo.svg — no direct code references found. Likely used as app branding; kept (doubtful).

## Obsolete Migrations
- No `migrations/` folder in app. App uses `patches.txt` and `ferum_custom/patches/*`.
- Verified `apps/ferum_custom/ferum_custom/patches.txt` entries exist under `ferum_custom/patches/` (v1_0_0, v1_0_1, v15_0). No obsolete/empty patches found. Kept.

## Unlinked Tests
- Tests reference existing DocTypes and app APIs.
- Note: Running tests against real Frappe requires a configured site (e.g., `test_site`). No tests referencing missing DocTypes/methods were found.

## Dependency Audit
- Python (apps/ferum_custom/pyproject.toml): no runtime deps declared; dev extras include `pytest`, `pre-commit`. Code uses optional `pyjwt`, `pyotp`, and `sentry-sdk` behind feature flags/try-imports — safe without installing.
- JavaScript: the app has no `package.json`. Bench root has dev tooling (`eslint`, `prettier`) — left unchanged.

## Hooks/Handlers Audit
- doctype_js: `User -> public/js/user.js` exists.
- doctype_list_js: `Invoice -> invoice_list.js` exists.
- scheduler_events: 
  - daily: `service_maintenance_schedule.generate_service_requests_from_schedule` exists.
  - hourly: `service_request.check_all_slas` exists.
- doc_events:
  - File: `on_trash -> cleanup.on_file_trash` exists; `on_update -> integrations.drive_file.on_file_update` exists.
  - Project: `after_insert -> autodoc.on_project_created` exists.
  - Task: `on_update -> autodoc.on_task_update` exists.
- before_request: `observability.before_request`, `api.auth.jwt_before_request` exist.
- override_whitelisted_methods: `frappe.desk.query_report.run -> api.reports.run_with_defaults` exists.

## Safe to Remove
- Removed: `apps/ferum_custom/__init__.py` — stray file that shadowed the real package and broke imports/tests.
- Removed: empty Doctype folder `apps/ferum_custom/ferum_custom/ferum_custom/doctype/article`.
- Removed: unused, empty report folders under `apps/ferum_custom/ferum_custom/ferum_custom/report/`:
  - `engineer_utilization`, `open_issues_by_engineer`, `unassigned_issues`, `project_profitability_simple`.
- Removed: empty workspace dir `apps/ferum_custom/ferum_custom/ferum_custom/workspace` (fixtures provide workspace config).
- Cleaned: repo-tracked `__pycache__` dirs (if any tracked).

## Notes and Next Steps
- Test execution: to run `pytest`, ensure a test site exists. Recommended:
  - `bench new-site test_site` (with test DB creds), then run `bench --site test_site set-config developer_mode 1`.
  - Run tests with bench’s Python: `PYTHONPATH=apps/ferum_custom:apps/frappe:apps/erpnext env/bin/pytest apps/ferum_custom/ferum_custom/tests`.
- If `test_site` is not feasible, set `FRAPPE_SITE_NAME` to an existing dev site and ensure it is installed with this app.
- Consider adding `import frappe.auth` in tests’ `conftest.py` to ensure `frappe.auth` is importable for monkeypatching.
