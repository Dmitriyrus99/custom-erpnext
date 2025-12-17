# Integrations Status — Google Drive & Telegram

This document summarises the current implementation of the two priority integrations in the Ferum Custom app (ERPNext v15) and captures gaps against the “minimum now” checklist.

---

## Google Drive

**Entry points**

- Service Report PDF export enqueues a Drive upload (`apps/ferum_custom/ferum_custom/ferum_custom/doctype/service_report/service_report.py#L118`).
- Custom Attachment background job mirrors ERP `File` objects to Drive folders (`apps/ferum_custom/ferum_custom/ferum_custom/doctype/custom_attachment/custom_attachment.py#L8`).
- ERP File hook uploads newly attached files (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/drive_file.py#L26`).
- Daily backup job pushes SQL backups to Drive (`apps/ferum_custom/ferum_custom/ferum_custom/site_ops.py#L180`).

**Configuration**

- Drive credentials are loaded from the `Ferum Custom Settings` singleton (`apps/ferum_custom/ferum_custom/ferum_custom/settings.py#L11`).
- `google_service_account_json` is stored as an ERPNext `File`; service account info is cached with `lru_cache` (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/google.py#L19`).
- Root folder is configured via the `google_drive_root_folder_id` field (`ferum_custom_settings.json`).

**Behaviour**

- Upload routine builds folder hierarchy per customer/project and updates/creates files atomically with retry/backoff (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/drive.py#L90`).
- On failure, errors are logged and best-effort email alerts are sent to System Manager / Chief Accountant (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/drive.py#L160`).
- `delete_file` removes remote objects when `Custom Attachment` records are deleted (`drive.py#L179` and `custom_attachment.py#L20`).
- Ferum Custom Settings exposes a healthcheck button that reads `drive.healthcheck()` (`drive.py#L203`).

**Checklist status**

| Check                                          | Status | Notes                                                                                                                                       |
| ---------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Credentials kept out of repo                   | ✅     | No service-account JSON present in git; settings expect upload via ERP `File`.                                                              |
| Scopes minimal (least privilege)               | ⚠️     | Uses full `https://www.googleapis.com/auth/drive`; consider `drive.file`.                                                                   |
| Healthcheck action in settings                 | ✅     | “Check Google Drive” button runs the new healthcheck helper and surfaces folder metadata.                                                   |
| Unified mapping `fileId` ↔ ERP File/Attachment | ⚠️     | `File` has `drive_file_id` fields (patch `add_file_drive_fields.py`) and `Custom Attachment` stores IDs, but legacy rows may lack backfill. |
| 401/403/404/429/5xx retry/backoff              | ⚠️     | Retries now cover HTTP 429/5xx; 401/403/404 are surfaced as fatal errors that still require operator follow-up.                             |
| Logging & audit trail                          | ⚠️     | Relies on `frappe.log_error`; no aggregated dashboard or success metrics.                                                                   |

**Risks**

- Drive outages or credential expiry silently stop uploads (no monitoring/alerting beyond emails).
- Background jobs depend on `googleapiclient`; missing dependency disables uploads without surfacing to admins beyond a warning log.
- Root folder ID must be manually managed per site; no validation to assert folder exists or Drive access.

**Immediate opportunities**

1. Automate reconciliation/backfill for historical attachments without `drive_file_id` and report drift.
2. Emit structured logs/metrics (e.g. Prometheus/Sentry) for upload success/failure counts.
3. Review Drive scopes and move service-account secrets into a managed vault.

---

## Telegram

**Entry points**

- Central send helper with retries and allowlist enforcement (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/telegram.py#L58`).
- Business logic sends broadcasts on new service requests, SLA breaches, subcontractor invoices (`apps/ferum_custom/ferum_custom/ferum_custom/doctype/service_request/service_request.py#L149`, `apps/ferum_custom/ferum_custom/ferum_custom/doctype/invoice/invoice.py#L84`).
- Webhook endpoint handles commands `/new_request`, `/start_work`, `/ping`, and photo attachments (`apps/ferum_custom/ferum_custom/api/telegram_bot.py#L116`).

**Configuration & security**

- `Ferum Custom Settings` stores `telegram_bot_token`, `telegram_default_chat_id`, and a `telegram_webhook_secret`.
- Webhook authorisation validates Telegram's `X-Telegram-Bot-Api-Secret-Token` header when set (preferred),
  falling back to a shared `secret` query parameter for backward compatibility
  (`apps/ferum_custom/ferum_custom/api/telegram_bot.py#L316`).
- No IP allowlist or Telegram signature verification is performed.

**Behaviour**

- `send_message` retries up to 3 times with exponential delay and blocks non-allowlisted chats (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/telegram.py#L58`).
- Webhook commands now check the admin username allowlist for privileged actions (`apps/ferum_custom/ferum_custom/api/telegram_bot.py#L308`).
- Photo attachments are downloaded via Bot API and saved as ERP `File` + `Custom Attachment`, then Drive upload is triggered (`apps/ferum_custom/ferum_custom/api/telegram_bot.py#L236`).
- Healthcheck helper powers the `/ping` command and the “Check Telegram” button in settings (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/telegram.py#L110`).

**Checklist status**

| Check                                     | Status | Notes                                                                                                              |
| ----------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| Tokens & secrets in env / secret store    | ⚠️     | Stored in Single DocType; environment overrides (`FERUM_*`) available but no dedicated vault yet.                  |
| Webhook protected (signature / origin)    | ⚠️     | Secret token header supported (Telegram `secret_token`), fallback query param remains; IP allowlist still pending. |
| Centralised client wrapper + retry policy | ✅     | `send_message` centralises sending with retry/backoff and enforces chat allowlists.                                |
| Healthcheck `/ping` (admin only)          | ✅     | `/ping` command (admin) and “Check Telegram” button run the healthcheck helper.                                    |
| Documented scenarios & ACL                | ✅     | `docs/integrations/telegram_setup.md` documents commands, allowlists, and admin usernames.                         |

**Risks**

- Shared-secret-only security can be brute-forced; missing per-user authentication means any secret holder can trigger privileged actions (`/close`, `/analytics`).
- Lack of `/ping` or heartbeat complicates Ops validation; failures only appear in desk logs.
- No rate limiting or command throttling on webhook handler → exposure to spam.

**Immediate opportunities**

1. Map Telegram usernames to ERP users and enforce ERP role checks (e.g., only engineers can `/start_work`).
2. Verify Telegram webhook signatures (X-Telegram-Bot-Api-Secret-Token) or restrict via IP ranges.
3. Move secrets into a managed vault and add telemetry around send/receive rates.
