# Finish Plan — Ferum Custom ↔ ERPNext v15

This plan captures the remaining scope to bring the Ferum Custom app in line with the target architecture. Priorities follow P0 (critical), P1 (important), P2 (nice-to-have). Effort is sized qualitatively (S/M/L).

## Dev / Product

| Task | Priority | Effort | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| Run migration patches (`migrate_service_request_to_issue`, `migrate_service_report_to_timesheet`, `migrate_service_project_to_project`, invoice migrations) on staging with snapshot + rollback plan. | P0 | L | Backend | Full data export; UAT sign-off | Validate attachments, permissions, workflows before prod rollout. |
| Refactor portal/API to use standard ERPNext DocTypes post-migration (`Issue`, `Timesheet`, `Project`, `Sales Invoice`). | P0 | M | Backend/API | Migration results | Update REST endpoints, tests, and front-end references. |
| Replace Python-driven notifications with declarative Notification DocTypes (Issue SLA, Invoice, Custom Attachment). | P1 | M | Backend | Migration done | Ensures parity with ERPNext upgrade paths. |
| Backfill Drive metadata for legacy `Custom Attachment` / `File` records (set `drive_file_id` where missing). | P1 | M | Backend | Drive access ok | Script to reconcile existing attachments; dry-run reporting required. |
| Harden Telegram commands with ERP role mapping (map Telegram usernames to ERP users, enforce role checks for `/start_work`, `/done`). | P1 | M | Backend | Admin usernames list | Uses `User` DocType mapping and permission queries. |
| Document architecture decision record (ADR) for decommissioning custom DocTypes once migrations are complete. | P2 | S | Product | Migration decisions | Helps audit & onboarding. |

## Infrastructure / Operations

| Task | Priority | Effort | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| Provision secrets storage (e.g., Ansible Vault, HashiCorp Vault) and move Telegram/Drive tokens out of desk for production. | P0 | M | DevOps | None | Update bench procfiles / systemd units to source env vars. |
| Configure monitoring for Drive/Telegram healthchecks (e.g., periodic `bench execute ...check_google_drive`). | P1 | S | DevOps | Healthcheck buttons shipped | Surface status on Ops dashboard / alert channel. |
| Lock down webhook endpoint (IP allowlist or Cloudflare rule) and enable HTTPS certificate automation. | P1 | M | DevOps | Web exposure | Combine with rate limits on reverse proxy. |
| Schedule background job to verify Drive quotas and alert on nearing limits. | P2 | M | DevOps | Drive API access | Extend healthcheck metrics to include storage consumption. |

## Data / Migration

| Task | Priority | Effort | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| Prepare data validation scripts comparing custom vs standard DocTypes (record counts, key fields, attachments). | P0 | M | Data | Migration patches | Use SQL queries + pivot tables; share with stakeholders. |
| Clean up obsolete custom DocType records post-migration (archive or export for reference). | P1 | M | Data | Migration done | Produce archive in S3/Drive, document retrieval procedure. |
| Update reporting layer (Dashboards/BI) to read from standard ERPNext tables. | P1 | M | Data | API refactor | Confirm with finance/legal regarding invoice reporting. |

## Legal / Compliance

| Task | Priority | Effort | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| Review Google Workspace & Telegram terms for data residency, ensure customer contracts allow external storage. | P0 | M | Legal | None | Document decision in compliance wiki. |
| Update data-processing agreements to mention Drive backup + Telegram alerts (if customer data flows into messages). | P1 | M | Legal | Terms review | Provide template clauses for new contracts. |
| Define retention & deletion policy for Drive archives (automatic purge after N years). | P1 | M | Legal/Ops | Drive monitoring | Feed policy into backup job (delete old backups). |

## Test & Release Checklist

- [ ] Automated test suite (`pytest`) extended with integration health tests (Drive + Telegram) — **DONE** (new tests already committed).
- [ ] Bench command for smoke deploy: `bench build && bench --site <site> migrate --skip_failing` validated on staging.
- [ ] Release notes linking to `changes/quick_fixes.md` and highlighting necessary migrations.
- [ ] On-call runbook updated with `/ping`, “Check Google Drive” button usage, escalation paths.

## Timeline (suggested)

| Milestone | Target |
| --- | --- |
| Staging migration dry-run + validation | +1 week |
| Production migration window (with rollback plan) | +3 weeks |
| Secrets management & webhook hardening | +2 weeks |
| Declarative notifications & residual clean-up | +4 weeks |
| Legal policy updates | +5 weeks |

Progress should be tracked in the project board with explicit owners. Update this checklist as tasks move to “In Progress”/“Done”.
