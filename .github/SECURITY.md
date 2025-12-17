# Security Policy

## Reporting a Vulnerability

Не создавайте публичные issue для security-репортов.

Отправляйте отчёт приватно мейнтейнерам и приложите:

- компонент (app / CI / deploy scripts)
- шаги воспроизведения
- ожидаемый/фактический результат
- потенциальный импакт

## Repo hygiene

- Не коммитить секреты: `.env*`, `site_config.json`, `sites/`, `*.key`, `*.crt`.
- Не логировать секреты в CI (проверяйте `set -x`, debug вывод и артефакты).
