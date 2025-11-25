# Ferum Customizations — System Architecture Overview

## Core Stack

- Frappe v15 + ERPNext (Backend)
- PostgreSQL 13 (DB)
- Redis (Cache/Queue)
- Traefik (Reverse Proxy)
- Docker / Compose (Deployment)

## Integrations

- Telegram Bot (Notifications & Workflow)
- Google Drive/Sheets (Documents & Reports)
- Prometheus & Grafana (Monitoring)
- Sentry (Errors & Tracing)

## Layers

- **Application:** Custom App `ferum_custom`
- **Integration:** API Layer (FastAPI / Frappe REST)
- **Storage:** PostgreSQL, Redis
- **Security:** Vault, HTTPS (Let's Encrypt)
- **Observability:** Prometheus + Sentry

## Data Flow

Requests → ERPNext Controller → Service Logic → PostgreSQL → Drive/Telegram → Notification.

Дополнительный чек-лист миграций по каждому кастомному DocType (поля, уникальные ключи, зависимости, legacy) доступен в `docs/architecture/doctype_migration_checklist.md`.

Ежедневный job `normalize_contracts_job` нормализует номера контрактов и логирует `Data Issue` (см. `ferum_custom.data_cleanup.jobs`).

## Roles

- Admin
- Engineer
- Project Manager
- Client
- Office Manager

## Diagram

(See: docs/architecture/current_diagram.drawio)
