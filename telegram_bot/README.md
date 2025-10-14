# Ferum Telegram Bot (Aiogram 3)

This is a separate bot service using Aiogram 3.x that integrates with Frappe/ERPNext Ferum Customizations.

Features:
- JWT-authenticated calls to Frappe custom API
- Create Service Requests, list own/assigned, change status via inline buttons
- Attach photos/documents to Service Request and Service Report (multipart upload)
- Optional Sentry error reporting and Prometheus metrics
- Webhook or polling mode (recommended: webhook behind Traefik HTTPS)

See `../../ferum_custom/docs/telegram_integration.md` for deployment.

Quick start (env)
- Preferred: use central bench file `config/.env.integrations` (see `config/.env.integrations.example`).
  - Keys supported (preferred): `FERUM_TELEGRAM_BOT_TOKEN`, `FERUM_FRAPPE_BASE_URL`, `FERUM_FRAPPE_USERNAME`, `FERUM_FRAPPE_PASSWORD`, `FERUM_BOT_TOTP_SECRET`, `FERUM_TELEGRAM_WEBHOOK_URL`, `FERUM_TELEGRAM_WEBHOOK_SECRET`, `FERUM_LOG_LEVEL`, `FERUM_PROMETHEUS_PORT`, `FERUM_SENTRY_DSN`.
  - For compatibility, classic keys in process env or local `.env` also work: `BOT_TOKEN`, `FRAPPE_BASE_URL`, `FRAPPE_USERNAME`, `FRAPPE_PASSWORD`, `BOT_TOTP_SECRET`, `WEBHOOK_URL`, `WEBHOOK_SECRET`, `LOG_LEVEL`, `PROMETHEUS_PORT`, `SENTRY_DSN`.
  - Bot now auto-loads `config/.env.local.integrations` and `config/.env.integrations` if running inside a bench.
  - Ensure in Ferum Custom Settings on the site: Enable JWT + JWT Secret (or rely on session fallback with 2FA).

JWT scoping note
- Server now issues short-lived tokens with `aud=ferum.api`, and validates JWT only for endpoints under `/api/method/ferum_custom.*`.
- Client code already targets those endpoints; no changes needed in the bot.
