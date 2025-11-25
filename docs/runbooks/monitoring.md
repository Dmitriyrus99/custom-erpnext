# Monitoring & Observability

This runbook describes how to configure Prometheus, Grafana, and Sentry to keep Ferum Custom production-ready.

## Prometheus scraping

- The static config lives in `monitoring/ferum_prometheus.yml`. It scrapes:
  - `/api/method/ferum_custom.api.metrics.prometheus` for business gauges (open service requests, invoices).
  - `/api/method/ferum_custom.api.drive.health` and `/api/method/ferum_custom.api.telegram_bot.health` for integration health.
  - The blackbox exporter probes (defined in `monitoring/blackbox/example-probe.yml`) to simulate external checks against Drive/Telegram.
- Replace `${FERUM_MONITOR_TARGET}` and friends with the host+port of your ERPNext site (or use DNS aliases). Alertmanager is expected on `alertmanager:9093` by default; adjust the `alerting` section if different.

## Alert rules

- `monitoring/ferum_alerts.yml` raises alerts for:
  - High open service requests (`FerumOpenServiceRequestsHigh` >120 for 5 minutes)
  - Drive/Telegram health endpoints returning non-200 responses
  - Blackbox probe failures for Drive/Telegram (missing credentials or connectivity issues)
- Point these alerts at your Alertmanager (Slack/Telegram channels). Reuse `ferum_custom.integrations.telegram.send_message` or `ferum_custom.ferum_custom.integrations.telegram` helpers to forward critical alerts to on-call chats.

## Grafana dashboard

- Import `monitoring/grafana/ferum_dashboard.json` to Grafana. It has panels for open requests, endpoint `up` values, and the blackbox probe status.
- Hook Grafana to the same Prometheus instance (matching the scrape targets above) and place the dashboard on your operations home screen.

## Health probes

- Use the blackbox config under `monitoring/blackbox/example-probe.yml` when deploying the Prometheus blackbox exporter. The `drive_health` and `telegram_health` modules expect JSON APIs and a 200 status code.
- Trigger the probes from your external network to confirm credentials and TLS paths; they reuse the same hosts as the direct Prometheus jobs.

## Sentry & logging

- Provide `SENTRY_DSN` / `FERUM_SENTRY_DSN` / `FRAPPE_SENTRY_DSN` via the secret-rendering pipeline (`scripts/render_env.py`). The runtime no longer reads these from the DocType to avoid checked-in secrets.
- Configure Sentry to forward alerts (via integrations or webhooks) to a notification channel (Slack/Telegram). Use `docs/runbooks/secret_management.md` for secret rotation notes.
- Regularly review Sentry issues and clear the `ferum_custom.security_pqc_rules` `FALSE` PQC logs (see `docs/SECURITY.md`) to ensure no unintended blocks occur.
