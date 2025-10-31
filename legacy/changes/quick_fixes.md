# Quick Fixes Included in feature/codex-audit-impl

- Enabled feature-flagged Drive integration with retry + healthcheck support (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/drive.py`, `ferum_custom_settings.json`, `ferum_custom_settings.py`).
- Added Telegram allowlists, admin gating, `/ping` command, and healthcheck endpoint (`apps/ferum_custom/ferum_custom/ferum_custom/integrations/telegram.py`, `apps/ferum_custom/ferum_custom/api/telegram_bot.py`).
  - Hardened webhook auth to accept Telegram's `X-Telegram-Bot-Api-Secret-Token` header (preferred) with query fallback; updated setup docs.
- Guarded background uploads/notifications behind settings toggles (`custom_attachment.py`, `drive_file.py`, `service_report.py`, `site_ops.py`).
- Introduced environment fallback + helpers for Ferum Custom Settings (`apps/ferum_custom/ferum_custom/ferum_custom/settings.py`).
  - Added optional env file loader for integrations: reads `config/.env.integrations` and `config/.env.local.integrations` into process env (keys `FERUM_*`).
- Delivered new integration documentation & env template (`docs/integrations/*.md`, `config/.env.example.integrations`).
- Added integration unit tests validating Drive/Telegram behaviour (`apps/ferum_custom/ferum_custom/tests/test_integrations_drive.py`, `test_integrations_telegram.py`).
