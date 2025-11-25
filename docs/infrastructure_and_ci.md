# Инфраструктура и CI/CD (каркас)

## Envs: dev/stage/prod

## IaC: Terraform + Ansible/bench

## CI: lint → pytest → bench migrate (dry-run) → build → deploy → notify

## Мониторинг: Prometheus/Grafana, Sentry

- Prometheus config: `monitoring/ferum_prometheus.yml` scrapes `/api/method/ferum_custom.api.metrics.prometheus`, Drive/Telegram health endpoints, and blackbox probes.
- Alerts: defined in `monitoring/ferum_alerts.yml`, delivered via Alertmanager (Slack/Telegram/Email).  
- Grafana dashboard template: `monitoring/grafana/ferum_dashboard.json`.  
- Blackbox exporter probe config: `monitoring/blackbox/example-probe.yml`.  
- Operational guidance: see `docs/runbooks/monitoring.md`.

## Секреты: Vault/SSM, примеры .env.*.example

## DR/Backups: расписание, шифрование, test-restore
