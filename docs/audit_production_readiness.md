# Production Readiness Audit — Ferum Custom (ERPNext/Frappe)

Дата: 2025-12-15  
Аудитор: Автономная AI-модель (Principal Engineer / ERPNext Architect)

## 1. Назначение и структура

- Кастомное приложение `apps/ferum_custom` поверх ERPNext/Frappe.
- Ключевые области:
  - API: `apps/ferum_custom/ferum_custom/api/*` (service, telegram_bot, auth, attachments).
  - Домейн: `apps/ferum_custom/ferum_custom/domain/service/*` (Issue/Service Request логика).
  - Telegram бот: `apps/ferum_custom/telegram_bot/telegram_bot/*` (+ webhook API).
  - Патчи/миграции: `apps/ferum_custom/ferum_custom/patches/**`, реестр `patches.txt`.
  - Настройки: DocType `Ferum Custom Settings`, поля для Telegram/JWT.
  - Интеграции: Telegram Bot API, JWT API (`enable_jwt`), Drive/Telegram упоминания в tests/notifications.

## 2. Текущая зрелость

- Состояние: **Pre-Production**. Есть рабочая бизнес-логика и бот, но:
  - Секреты хранятся в репозитории.
  - Не настроены наблюдаемость/алерты.
  - Нет интеграционных e2e-тестов и секрет-скана в CI.
  - Требует плановой ротации токенов и упорядочивания миграций.

## 3. Архитектура и код

- Разделение слоёв соблюдено: API → domain → data.
- Нарушения:
  - Дубли статусов/экшенов между API и ботом (частично устранено общими константами `constants/statuses.py`).
  - Локальные try/except глушат ошибки без сигнализации (бот и API).
  - Валидация входных данных минимальна (files, payloads).

## 4. Бизнес-логика и данные

- Жизненный цикл: Issue/Service Request, смена статусов через API/бот.
- Workflow явно не описан, rely на стандартные статусы ERPNext.
- Патч `v15_5/seed_issue_priorities.py` восстанавливает Issue Priority (Low/Medium/High).
- Permissions: используют стандартные роли ERPNext + кастомные (Engineer, Telegram Admin). Не обнаружены жёсткие проверки на уровне API (только JWT/feature flags).

## 5. Безопасность

- Секреты в репо: `config/.env.integrations` содержит BOT_TOKEN, API key/secret, Proxmox token — **P0 риск**.
- JWT включён, секрет хранится в .env; audience частично проверяется.
- Webhook защищён secret header, но `telegram_ip_allowlist` может быть пуст — требуется настройка.
- Файлы: доработана проверка размера/контента для вложений (7 MB, image/pdf).
- OWASP: нет секрет-скана, нет CSP/CORS настроек на API, ограниченная валидация входа.

## 6. Отказоустойчивость

- Бот: systemd unit есть, healthz на webhook; нет внешних алертов/SLO.
- Внешние интеграции: Telegram/ERP API — нет retry/backoff в API call’ах бота (кроме max_retries в send_message).
- Логирование: есть, но без алертов; ошибки часто проглатываются.

## 7. Тестируемость

- Unit: telegram bot, telegram integration, статус-маппинг (добавлено).
- Пробелы: нет e2e webhook→DB, нет тестов миграций, нет coverage отчётов, нет secret-scan в CI.

## 8. Production Plan (приоритеты)

### P0 (срочно)

1. Ротация всех секретов, удаление из репозитория; использовать env/secret store.
2. Зафиксировать и прогнать миграции на всех сайтах (`bench migrate`), особенно `seed_issue_priorities`.

### P1 (ближайший спринт)

1. Внедрить секрет-скан/ruff/mypy в CI; публиковать coverage.
2. E2E-тесты для Telegram webhook (Happy-path: /my, /start_work, attach).
3. Настроить мониторинг: health-check оповещения, Sentry DSN, алерты по error rate.
4. Консолидировать статусы/экшены (Issue/SR) — использовать `constants/statuses.py` во всех слоях.

### P2 (улучшения)

1. Рефактор хендлеров бота: единый builder для списков/кнопок, пагинация `/my 2`.
2. Документация по боту и управлению секретами в `docs/runbooks/`.
3. Оптимизация индексов (Issue.customer/priority, Customer.name) после анализа EXPLAIN.

## 9. Вердикт

- Текущий статус: **Не готово к Production**.
- Блокеры: открытые секреты, отсутствие мониторинга/алертов, нет e2e/CI контроля, не зафиксированы миграции на проде.
- При выполнении P0/P1 список станет Production-Ready.

## 10. Быстрые чек-листы

- Запуск тестов: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests -q`
- Миграции: `bench --site <site> migrate`
- Бот: systemd `ferum-telegram-bot.service`, health: `/tg-bot/healthz`
