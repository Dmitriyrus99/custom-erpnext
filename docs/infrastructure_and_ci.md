# Инфраструктура и CI/CD (каркас)
## Envs: dev/stage/prod
## IaC: Terraform + Ansible/bench
## CI: lint → pytest → bench migrate (dry-run) → build → deploy → notify
## Мониторинг: Prometheus/Grafana, Sentry
## Секреты: Vault/SSM, примеры .env.*.example
## DR/Backups: расписание, шифрование, test-restore
