# Роли и ACL (каркас)

Документ определяет владельцев процессов, роли и ожидания по доступам (read/write/submit/cancel). Такие соглашения необходимы для конкурентного доступа к DocType и для построения row-level security.

## Обзор ролей

| Роль               | Назначение | Ключевые зоны ответственности |
|--------------------|------------|-------------------------------|
| **Office Manager** | Ведение заявок, SLA, счета | Создание/обновление `Service Request`, `Invoice`, контроль документов |
| **Chief Accountant** | Финансовое сопровождение | Доступ к `Invoice`, `Payment`, `Payment Allocation` (по своей компании) |
| **Service Engineer** | Работа на объектах | Выполнение `Service Report`, исполнение `Service Request`, управление `Service Object` |
| **Project Manager** | Контроль проектов и контрактов | Поддержка `Project`, `Contract`, `Service Maintenance Schedule` |
| **Architect / Backend Lead** | Архитектура данных и миграции | DocType миграции, данные `Data Issue`, row-level security |
| **Security Engineer** | Секреты, ротация, observability | Secrets, Sentry, Secret Manager, row permissions |
| **DevOps / Script Manager** | CI/CD, окружения, Traefik | `docker-compose`, GitHub Actions, Vault/SSM |

## Матрица permisos по DocType

| DocType | Роли | Read | Write | Submit / Cancel | Scope | Дополнительно |
| --- | --- | --- | --- | --- | --- | --- |
| `Contract` | Architect, Project Manager | ✔️ | ✔️ (company) | Submit: Architect | Company (`company`, `project`) | `contract_no_normalized` должен быть unique |
| `Contract Stage` | Architect | ✔️ | ✔️ | N/A | Linked `contract` | Удалять вместе с контрактом |
| `Service Request` | Office Manager, Service Engineer, Client | ✔️ (assigned company/project) | ✔️ (owner/engineer) | Workflow controlled | `company`, `project`, `customer` | Клиенты видят только свои заявки |
| `Service Report` | Service Engineer, Project Manager | ✔️ (project/company) | ✔️ (linked SR) | Submit/Cancel via workflow | `service_object`, `company` | Engineers edit только свои отчёты |
| `Invoice` | Chief Accountant, Office Manager | ✔️ (company) | ✔️ (same company) | Submit/Cancel by Chief Accountant | `company` | Payment allocations проверяют `invoice.company` |
| `Payment` | Chief Accountant, Finance Ops | ✔️ (company) | ✔️ (company) | — | `company` | Доступ только к своим `payment_allocation` |
| `Payment Allocation` | Chief Accountant | ✔️ | ✔️ (linked invoice/payment) | — | `company` | Проверка сумм |
| `Service Object` | Project Manager, Service Engineer | ✔️ (project/company) | ✔️ (project) | — | `company`, `project` | Default engineer ограничен |
| `Service Maintenance Schedule` | Project Manager, Office Manager | ✔️ | ✔️ | — | `company`, `project` | Создаёт SR через scheduler |
| `Data Issue` | Architect, Security | ✔️ | ✔️ (security) | — | Global | только Security может закрывать |
| `Stg Raw` | Architect, ETL owner | ✔️ | ✔️ | — | `company` | Немедленно очищается после ETL |
| `Cashflow Article` | Chief Accountant | ✔️ | ✔️ | — | Global | Связано с `Payment.direction` |

## Row-Level Security / Permission Query Conditions

- `service_request_pqc` комбинирует company filter с привязкой к `assigned_to` для инженеров и `customer` для клиентов.
- `service_report_pqc`, `contract_pqc`, `invoice_pqc` и `payment_pqc` ограничивают доступ по `company`, а `payment_allocation_pqc` проверяет связь через счета/платежи.
- `service_request_has_permission` позволяет инженерам редактировать только свои заявки и клиентам — только свои `Service Request`/`Service Report`.
- Эти функции подключены в `hooks.py` (раздел `permission_query_conditions` и `has_permission`) и входят в миграционный и security pipeline.

## Row-permission tests

Добавьте `apps/ferum_custom/ferum_custom/tests/test_permissions.py` с кейсами:
1. Service Engineer видит и редактирует только заявки/отчёты, связанные с его `Service Object` / `Project`.
2. Chief Accountant видит все `Invoice`/`Payment` своей компании, но не может менять чужие.
3. Client (Website User) может видеть только `Service Request`/`Service Report` своего `Customer`.
4. Security Engineer может создавать/закрывать `Data Issue` любой `company`.

Тесты запускаются командой:

```bash
./env/bin/pytest apps/ferum_custom/ferum_custom/tests/test_permissions.py
```

## Row-level security implementation

- `ferum_custom.security_pqc_rules` now backs all `permission_query_conditions` in `hooks.py`, constraining `Invoice`, `Payment`, `Service Request`, `Contract`, `Counterparty`, `Service Report`, `Service Act`, and `Data Issue`.
- Engineers read assigned requests via the `assigned_to` clause (`service_request_pqc`) while `Client` / Website User roles are limited to their allowed customers; only `System Manager`/`Security Engineer` bypass their restrictions.
- `Data Issue` is visible only to `Security Engineer` or `System Manager` roles; others evaluate a `FALSE` clause, preventing accidental exposure.
- Both `service_request_has_permission` and `default_has_permission` honor company/customer scoping, so forms and actions cannot mutate rows beyond those filters.

Когда добавляете новые PQC-хуки, документируйте их логику и тест-кейсы в этом разделе.

## Секреты и ротация

В целях безопасности (`docs/SECURITY.md`) опишите регламент:
1. Секреты [Telegram бот, JWT, Sentry, DB/Redis] должны ротироваться ежеквартально.
2. Ответственные: Security Engineer созывает ревью; DevOps/Integrations участвуют в обновлении runbooks.
3. Все ротации фиксируются в `docs/runbooks/secret_rotation_log.md` (или аналогичном таблице) и задокументированы в Vault/SSM (например, `FERUM_JWT_SECRET`, `FERUM_JWT_SECRET_V2`).

Дополнительно:
- Обновите `ferum_custom/permissions.py` и `hooks.py` после тестов, чтобы row-level security стала частью приложения.
- При добавлении новых ролевых ограничений — регистрируйте их в этом документе, чтобы команды и тесты всегда имели актуальный источник правды.
