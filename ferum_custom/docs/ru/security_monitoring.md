# Безопасность и мониторинг

JWT для API
- Вкл/выкл: `enable_jwt`, секрет: `jwt_secret`.
- Хук при каждом запросе: исправлен путь импорта в hooks: ferum_custom/hooks.py → `before_request` => `ferum_custom.api.auth.jwt_before_request`.

Rate Limiting (защита от брутфорса)
- Новый флаг: `enable_rate_limit_auth`.
- Порог в минуту на IP: `rate_limit_auth_per_minute` (по умолчанию 5).
- Реализация: ferum_custom/ferum_custom/api/auth.py (`_check_auth_rate_limit`).

Резервные копии
- SQL‑бэкапы по расписанию, хранение в защищенной папке Google Drive (см. общие интеграции).

Аналитика и алертинг
- Отслеживание ошибок (например, Sentry DSN) и метрик (Grafana/Prometheus) — на уровне инфраструктуры.
