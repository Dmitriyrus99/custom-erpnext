# Grafana PromQL Examples — Ferum Integrations

Use these PromQL snippets to build panels for the new integration metrics exposed at `/api/method/ferum_custom.api.metrics.prometheus`.

- Drive uploads — success vs error (5m rate)

  - `sum(rate(ferum_integration_drive_upload_total{result="success"}[5m]))`
  - `sum(rate(ferum_integration_drive_upload_total{result="error"}[5m]))`

- Drive deletes — errors by category (last 1h)

  - `sum(increase(ferum_integration_drive_delete_total{result="error"}[1h])) by (category)`

- Telegram notifications — success/error rate

  - `sum(rate(ferum_integration_telegram_send_total{result="success"}[5m]))`
  - `sum(rate(ferum_integration_telegram_send_total{result="error"}[5m]))`

- Google Sheets sync — success/error rate

  - `sum(rate(ferum_integration_sheets_sync_total{result="success"}[5m]))`
  - `sum(rate(ferum_integration_sheets_sync_total{result="error"}[5m]))`

- Business KPIs (already exposed)
  - Open service requests: `ferum_open_service_requests`
  - Invoices: sent/paid: `ferum_invoices_sent`, `ferum_invoices_paid`

Suggested alert ideas

- Drive upload error rate > 0.1/min for 10m
- Sheets sync errors detected in the last 30m
- Telegram send errors spike over baseline (> 10 in 15m)
