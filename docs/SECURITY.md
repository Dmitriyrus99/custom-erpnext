# Security & Row-Level Controls

This document captures the security contract for Ferum Custom — from secrets to row-level access.

## Secrets & rotation

- Secrets live outside the repo via Vault/SSM and are rendered into `.env` using `scripts/render_env_from_secrets.sh` + `scripts/render_env.py` (`docs/runbooks/secret_management.md`).
- Rotate Telegram/JWT/DB/Redis/Sentry secrets quarterly and log each change in `docs/runbooks/secret_rotation_log.md`.

## Row-Level Security (PQC)

- `hooks.py` wires `ferum_custom.security_pqc_rules` to the ERPNext permission hooks, covering `Invoice`, `Payment`, `Service Request`, `Service Report`, `Contract`, `Counterparty`, `Service Act`, `Payment Allocation`, and `Data Issue`.
- The PQC helpers enforce:
  - Company filters for finance docs (`Invoice`, `Payment`, `Counterparty`, `Contract`).
  - Engineers may query their assigned `Service Request`s; clients are restricted to their `Customer` allowed list.
  - `Data Issue` entries are only queryable by `Security Engineer` or `System Manager`; others evaluate a `FALSE` clause so the list view stays empty.
  - `default_has_permission`/`service_request_has_permission` keep form-level actions aligned with the same company/customer checks.

## Tests

- Permission rules are covered by `apps/apps/ferum_custom/ferum_custom/tests/test_permissions.py`. Run `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_permissions.py` after touching PQC logic.
- Additional QA: run `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_service_requests.py` to ensure Portal tokens + JWT also respect the same company/customer boundaries.

## Monitoring hardening

- Alert on unexpected `FALSE` PQC clauses by logging rejections and surface them in Sentry/Prometheus (see `monitoring/` for dashboards).
