# Telegram Integration (Ferum)

Objective: reliable two-way Telegram integration for Issues and Timesheets across ERPNext v15 / Frappe and an Aiogram 3 bot.

Contents:
- Architecture and security
- Known issues found and fixes
- REST API surface (JWT, uploads)
- Bot (Aiogram 3) structure, handlers, FSM
- Deployment: Docker/Traefik, webhook, systemd
- Observability: logging, Sentry, Prometheus
- Test checklist

## Architecture & Security

- ERPNext/Frappe app provides:
  - Webhook endpoint: `ferum_custom.api.telegram_bot.handle_update` (allow_guest, guarded by Telegram secret token via header `X-Telegram-Bot-Api-Secret-Token` or query `?secret=`).
  - Outbound helper: `ferum_custom.ferum_custom.integrations.telegram.send_message` with allowlist, retries, feature-flag.
  - JWT middleware: `before_request = ferum_custom.api.auth.jwt_before_request` enabling `Authorization: Bearer <token>` on `ferum_custom.api.*` methods.
- Aiogram 3 bot (separate service) calls Frappe over HTTPS using JWT and the new upload endpoints.
- Traefik terminates TLS and routes `/tg-bot/*` to the bot; Frappe remains under the main site host.

## Issues Found & Fixes

- Photo attach path only via Telegram webhook; no generic API for external clients.
  - Added: `ferum_custom.api.attachments.attach_to_issue` and `attach_to_timesheet` (JWT-protected, multipart upload).
- Weak inline UX in chat.
  - Added: Aiogram inline buttons for Start Work / Done with callbacks mapped to `update_issue_status`.
- Secret validation for webhook.
  - Implemented header-based secret (official Telegram) with fallback to query; returns 403 if mismatched.
- Serialization/timeouts
  - All outbound Telegram calls use JSON and explicit timeouts.
  - REST client uses `httpx` with timeouts.
- Bot resilience
  - Provided Docker + systemd configs, `Restart=always`, health endpoint, optional Sentry.

## REST API (JWT)

- Auth: POST `/api/method/ferum_custom.api.auth.login` → `{ token }` (2FA supported for TOTP).
- Create/list Issues:
  - POST `/api/method/ferum_custom.api.service.create_issue`
  - GET  `/api/method/ferum_custom.api.service.list_issues`
- Update status:
  - POST `/api/method/ferum_custom.api.service.update_issue_status` (server validations enforced).
- Uploads (multipart/form-data `file`):
  - POST `/api/method/ferum_custom.api.attachments.attach_to_issue?name=ISS-...`
  - POST `/api/method/ferum_custom.api.attachments.attach_to_timesheet?name=TS-...`

Security notes:
- Use HTTPS only; JWT feature flag `enable_jwt` and secret `jwt_secret` must be set.
- Telegram webhook secret must match `Ferum Custom Settings.telegram_webhook_secret`.
- Rate-limits: login and new request creation are rate-limited by IP (settings controlled).

## Aiogram 3 Bot

Location: `apps/ferum_custom/telegram_bot/`

- `main.py` — polling or webhook server (`MODE=polling|webhook`), `/healthz` route in webhook mode.
- `config.py` — loads `.env`.
- `frappe_client.py` — async JWT client (httpx) for Frappe API and multipart uploads.
- `handlers/issues.py` — commands:
  - `/start` — help
  - `/new <title>` — create Issue
  - `/my` — list recent issues with inline buttons [Start Work, Done]
  - Photo with caption `/attach <ISSUE-NAME>` — attaches image to Issue
- `keyboards.py` — inline keyboards.
- `.env.example`, `Dockerfile`, `docker-compose.example.yml`, `systemd/ferum-telegram-bot.service`.

FSM: kept light; caption-based attach avoids multi-step flows. Can extend with states for multi-file uploads or report creation.

## Access & Identification

- Allowlist and mapping:
  - Access is granted if a chat_id is on the allowlist (`Ferum Custom Settings.telegram_allowed_chat_ids`) or has a record in `Telegram User Link`.
  - Admins can be declared either by `Admin Telegram Usernames` (settings) or by setting `is_admin` on a `Telegram User Link` record.
- Identity mapping to ERPNext user:
  - The webhook resolves the ERPNext user from `Telegram User Link` by `chat_id` (preferred) or `telegram_username` and calls `frappe.set_user(...)` so all actions execute under that user and respect permissions/RBAC.
  - To “open access” for a person:
    1. Ask them to send `/whoami` to the bot to obtain `chat_id` and username.
    2. Create a `Telegram User Link` with fields:
       - `ERPNext User` — link to the correct User
       - `Telegram Username` — optional but recommended (e.g., `engineer123`)
       - `Telegram Chat ID` — from `/whoami`
       - `Treat as Telegram Admin` — check if this user may run admin commands
    3. Optionally add the `chat_id` to `telegram_allowed_chat_ids` in settings for a global allowlist.
  - From now on, commands run in the context of that ERPNext user, honoring PQCs and permissions.

## Deployment

- Docker + Traefik:
  - Build from `apps/ferum_custom/telegram_bot/`.
  - Expose `/tg-bot/webhook`; set Telegram webhook with `secret_token`.
- Environment (.env):
  - `BOT_TOKEN`, `WEBHOOK_URL`, `WEBHOOK_SECRET`
  - `FRAPPE_BASE_URL`, `FRAPPE_USERNAME`, `FRAPPE_PASSWORD`
  - Optional: `PROMETHEUS_PORT`, `SENTRY_DSN`
- Systemd alternative provided (polling mode).

## Observability

- Logging to stdout; Frappe logs server-side.
- Optional Sentry `SENTRY_DSN` for bot exceptions.
- Prometheus (optional) starts HTTP metrics server on `PROMETHEUS_PORT`.

## Test Checklist

- Telegram
  - `/start` replies
  - `/new` creates issue in ERPNext
  - `/my` shows list with inline buttons; buttons update statuses
  - Send photo with `/attach ISS-XXXX` → attaches to issue
- Security
  - JWT login works only over HTTPS; invalid JWT → 403
  - Webhook rejects wrong `X-Telegram-Bot-Api-Secret-Token`
- Timesheet
  - Upload PDF via `attach_to_timesheet` and ensure validation passes at submit (requires image + PDF)
- Resilience
  - Bot restarts on crash (Docker/systemd) and responds to `/healthz`

## Role-based Notifications

- Default broadcast uses `Ferum Custom Settings.telegram_default_chat_id`.
- For per-role routing, consider mapping ERPNext users to Telegram chat IDs (custom doctype or settings) and extend `integrations/telegram.py` to resolve recipients by role.
