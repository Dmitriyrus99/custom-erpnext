# Инфраструктура и CI/CD

## Envs: dev/stage/prod

## IaC: Terraform + Ansible/bench

## CI: lint → secret scan (gitleaks) → test → bench migrate → build → deploy → notify

- **Linting & Secrets:** `pre-commit` hooks run linters and `gitleaks` to ensure code quality and security.
- **Testing:** `pytest` with `pytest-cov` runs unit and e2e tests, generating XML coverage reports.
- **Migrations:** `bench migrate` is run to apply database schema changes.
- **Build:** `bench build` compiles static assets (JS/CSS) for the custom app.
- **Deployment:** Docker image build/push for main branch, manual trigger deployment to staging/prod via SSH.
- **Notifications:** Placeholder for deployment status notifications.

## Мониторинг: Prometheus/Grafana, Sentry

- Prometheus config: `monitoring/ferum_prometheus.yml` scrapes `/api/method/ferum_custom.api.metrics.prometheus`, Drive/Telegram health endpoints, and blackbox probes.
- Alerts: defined in `monitoring/ferum_alerts.yml`, delivered via Alertmanager (Slack/Telegram/Email).
- Grafana dashboard template: `monitoring/grafana/ferum_dashboard.json`.
- Blackbox exporter probe config: `monitoring/blackbox/example-probe.yml`.
- Operational guidance: see `docs/runbooks/monitoring.md`.

## Секреты: Vault/SSM, примеры .env.*.example

## DR/Backups: расписание, шифрование, test-restore

