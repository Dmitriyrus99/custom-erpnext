# Telegram Integration Audit — Findings & Fixes

Scope: Telegram webhook endpoint in Frappe (`ferum_custom.api.telegram_bot`), outbound helper (`integrations/telegram.py`), supporting settings, and new Aiogram 3 bot module.

## Findings

- No general-purpose upload API for external clients; only webhook path could attach photos to Service Request.
- Inline actions absent (UX friction). Users must type commands to change statuses.
- Webhook security relies on a query `?secret` in older setups only.
- Serialization/timeouts: outbound Telegram uses timeouts; inbound deserialization safe; however no clear multipart endpoints.
- Bot process missing in-repo (deployment handled externally); no standardized env/config, resilience guidance, or metrics.

## Changes Implemented

- New JWT-protected REST endpoints for uploads:
  - `ferum_custom.api.attachments.attach_to_service_request`
  - `ferum_custom.api.attachments.attach_to_service_report`
- Status update endpoint:
  - `ferum_custom.api.service.update_service_request_status`
- Webhook: strengthened secret validation using official header `X-Telegram-Bot-Api-Secret-Token` with fallback to query.
- Aiogram 3 bot module scaffold (`apps/ferum_custom/telegram_bot/`): handlers, async Frappe client, env, Docker/systemd.
- Documentation: `ferum_custom/docs/telegram_integration.md` with deployment and test checklist.

## Recommended Next Steps

- Map ERPNext users to Telegram chat IDs to enable per-role notifications and direct messages (custom Doctype or settings mapping).
- Add integration tests for upload endpoints and webhook with secret header.
- Extend bot FSM for Service Report creation flow (collect work items, PDF upload prompt) if needed by field engineers.
- Add retry/backoff for Frappe API in bot client and token refresh strategy.
