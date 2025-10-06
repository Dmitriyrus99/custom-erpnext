# Cleanup Changelog (Ferum Custom)

- Removed stray top-level `apps/ferum_custom/__init__.py` that shadowed the package and broke imports.
- Deleted empty DocType directory: `ferum_custom/ferum_custom/doctype/article`.
- Deleted unused empty report directories:
  - `ferum_custom/ferum_custom/report/engineer_utilization`
  - `ferum_custom/ferum_custom/report/open_issues_by_engineer`
  - `ferum_custom/ferum_custom/report/unassigned_issues`
  - `ferum_custom/ferum_custom/report/project_profitability_simple`
- Deleted empty workspace directory: `ferum_custom/ferum_custom/workspace`.
- Cleaned tracked `__pycache__` directories in repo (if any).
- Left all fixtures intact (workflows, roles, print formats, reports) — no duplicates or obvious orphans detected.
- No changes to Python/JS dependencies; optional runtime deps remain behind feature flags.
