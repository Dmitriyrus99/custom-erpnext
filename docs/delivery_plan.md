# **Ferum Customizations — Delivery Plan (Этап 3)**

## 🎯 Цель

Довести систему Frappe/ERPNext + Ferum Custom до production-ready статуса с надёжной архитектурой, тестами, CI/CD и документацией.

## 📌 Основные этапы

| Этап     | Название                           | Цель                                                                                                             | Длительность           | Owner                      | Status      | Blocked by                  | Notes                                                   |
| -------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------- | -------------------------- | ----------- | --------------------------- | ------------------------------------------------------- |
| **P0-1** | Очистка и нормализация репозитория | Полностью вычищен мусор, секреты и временные файлы; структура docs/ и legacy/ оформлена                          | ✅ Выполнено           | Архитектор / DevOps        | Done        | —                           | Базовая уборка завершена (архитектура стабилизирована). |
| **P0-2** | Архитектурная консолидация         | Завершить `architecture_overview.md`, подготовить `current_diagram.drawio` и финализировать взаимосвязи сервисов | 2 дня                  | Архитектор + Backend Lead  | In Progress | Подача обновлённых диаграмм | Рабочая группа завершает схемы и зависимости.           |
| **P0-3** | Миграция и рефакторинг DocType     | Завершить миграцию кастомных DocType в стандарты ERPNext; убрать устаревшие таблицы и hooks                      | 2 недели               | Backend Team               | Planned     | P0-2, архитектурная карта   | Нужно донести миграции и data-cleanup jobs.             |
| **P0-4** | Безопасность и секреты             | Перевести все секреты в Vault/SSM, внедрить DB-уровень PQC и роле-фильтрацию на SQL                              | 1 неделя               | DevOps + Security Engineer | Planned     | P0-3, секретный менеджер    | Ротация токенов, row-level security.                    |
| **P0-5** | Тестирование и автоматизация       | Покрыть основные бизнес-флоу pytest, миграции, автоматические проверки интеграций                                | 1 неделя (параллельно) | QA Lead + Backend          | Planned     | P0-3, P0-4                  | Smoke pytest + bench тесты.                             |
| **P1-1** | CI/CD Pipeline                     | GitHub Actions: lint → pytest → bench migrate → build → deploy → notify                                          | 1 неделя               | DevOps                     | Planned     | P0-5, секреты               | Документировать и собрать workflow.                     |
| **P1-2** | Интеграции (Drive/Telegram)        | Завершить проверку Drive API и Telegram бота, внедрить Prometheus метрики и Sentry логирование                   | 1 неделя               | Integrations Engineer      | Planned     | P0-4                        | Добавить health checks и alerts.                        |

---

| **P1-3** | Документация и Runbooks | Финализировать `infrastructure_and_ci.md`, `roles_and_acl.md`, обновить README | 3 дня | Tech Writer + Architect | Planned | P0-2 | Обновить runbooks и delivery отчёты. |
| **P2-1** | Production Deployment | Развёртывание через Docker / Traefik / PostgreSQL с бэкапами и HTTPS | 1 неделя | DevOps Lead | Planned | P1-1 | Stage → prod rollout + backups. |
| **P2-2** | Мониторинг и наблюдаемость | Prometheus + Grafana + Sentry интеграция и алерты | 3 дня | DevOps + SRE | Planned | P1-2 | Настроить dash/alerts. |
| **P2-3** | Приёмочные тесты и Go-Live | Финальная валидация на stage, Smoke и UAT, подготовка отчёта об эксплуатационной готовности | 1 неделя | QA Lead + Project Owner | Planned | P2-1, P2-2 | Smoke test report и sign-off. |

---

## 📦 Шаг 2 — структура Ferum Custom

- Разбиваем функциональность на отдельные `Module Def`: Project & Contract Management, Service Request Management, Work Reporting, Invoicing, HR & Payroll, Document Management, Notifications и Analytics. Так Desk отразит бизнес-блоки вместо одного общего модуля.
- Используем стандартные DocType (Customer, Company, Employee, Project, Sales/Purchase Invoice, File) как фундамент и добавляем новые сущности (`Service Project`, `Service Request`, `Service Report`, `Service Object`, `Invoice`) с обязательным `company` и RBAC/PQC.
- `Ferum Custom Settings` — единственный singleton для JWT/secret (Google Drive/Sheets, Telegram, Sentry, rate limits). Секреты рендерятся в `.env` через `scripts/render_env*.sh` из Vault/SSM, чтобы их не было в репозитории.
- JWT-хуки (`before_request`, SLA checks), background jobs (Drive upload, cleanup) и Telegram/Drive интеграции связываются через эти модули, что обеспечивает повторную использованность и упрощает масштабирование.

## ⚙️ Подробный план по доменам

## 🧭 Роли по этапам

| Этап     | Вовлечённые роли                                   |
| -------- | -------------------------------------------------- |
| **P0-1** | Architect, DevOps                                  |
| **P0-2** | Architect, Backend Lead                            |
| **P0-3** | Backend Team, Architect                            |
| **P0-4** | Security Engineer, Architect                       |
| **P0-5** | QA Lead, Backend Team                              |
| **P1-1** | DevOps, Script Manager                             |
| **P1-2** | Integrations Engineer, Office Manager, Tech Writer |
| **P1-3** | Tech Writer, Architect                             |
| **P2-1** | DevOps Lead, SRE                                   |
| **P2-2** | DevOps, SRE, Support                               |
| **P2-3** | QA Lead, Project Owner                             |

Эта таблица отражает связь между этапами и ответственностью; роли соответствуют описанию из `docs/roles_and_acl.md` и текущим обязанностям команд.

### 🧩 Backend (ERPNext / Ferum Custom)

- Провести миграции из `apps/ferum_custom/patches.txt` → Doctype Patches.
- Внедрить data-validation и idempotent механизмы в hooks.
- Переписать `api/service.py`, `domain/service/application.py` на стандарты ERPNext.
- Добавить unit и integration тесты для модулей `service`, `finance`, `automation`.

### 🖥️ Frontend / Portal

- Унифицировать портал в `www/portal/` → новые DocType.
- JWT-аутентификация и rate-limit на API.
- Тестирование через `bench ui-test` и `pytest –k portal`.

### 🔐 Security / Compliance

- Удалить все секреты из VCS.
- Настроить Vault (или AWS SSM / KeyVault).
- Активировать DB-уровневую валидацию PQC и тесты на row-permissions.
- Настроить Sentry DSN и Prometheus endpoint с healthchecks.

### 🔄 Integrations

- Telegram Bot: webhook, метрики, аварийные уведомления.
- Google Drive / Sheets: сервисные учётки, автоподтверждение актов.
- Metrics API: Prometheus / Grafana дашборды.

### 🧠 QA / Test Automation

- Расширить `apps/ferum_custom/tests/`.
- Добавить `pytest-cov` и генерацию отчётов XML (для CI).
- Проверка миграций bench migrate ––dry-run на stage.

### 🧰 DevOps / CI / IaC

- Terraform: создание окружений (dev/stage/prod).
- Ansible playbooks для bench / postgres / traefik.
- GitHub Actions pipeline:
  - Lint → Tests → Build → Deploy → Notify.

- Резервное копирование через `site_ops.py` + S3/Vault.

### 📝 Documentation / Knowledge

- `architecture_overview.md` → обновить по результатам миграций.
- `infrastructure_and_ci.md` → описать CI/CD и бэкапы.
- `roles_and_acl.md` → обновить ACL для новых ролей.
- `legacy_notes.md` → закрыть комментарием о финальном аудите.

---

## ⏱️ Таймлайн (ориентировочно)

| Неделя | Этап        | Ключевой результат                     |
| ------ | ----------- | -------------------------------------- |
| 1–2    | P0-2, P0-3  | Архитектура и DocType модель готовы    |
| 3      | P0-4        | Секреты и PQC внедрены                 |
| 4      | P0-5 + P1-1 | CI/CD и тесты автоматизированы         |
| 5      | P1-2 + P1-3 | Интеграции и документация завершены    |
| 6      | P2-1        | Production деплой через Docker/Traefik |
| 7      | P2-2 + P2-3 | Мониторинг и Go-Live UAT успешны       |

---

## ✅ Критерии готовности к Production

1. Все DocType мигрированы и валидированы в ERPNext.
2. CI/CD pipeline успешно выполняет тесты и деплой.
3. Нет секретов в git; Vault/SSM активен.
4. Prometheus/Sentry дают метрики и алерты.
5. Тестовое восстановление из бэкапа прошло успешно.
6. Документация в `docs/` заполнена и актуальна.
7. Все UAT тесты приняты Project Owner’ом.

---

## ⚠️ Риски и меры

| Риск                                  | Влияние | Митигирующая мера                      |
| ------------------------------------- | ------- | -------------------------------------- |
| Несогласованность данных при миграции | Высокое | dry-run и авто-бэкап bench backup      |
| Ошибки CI/CD деплоя                   | Среднее | stage-окружение с ручным rollback      |
| Утечки секретов или ключей            | Высокое | Vault + регулярный secret-scan         |
| Нехватка времени QA                   | Среднее | автоматизация pytest + coverage-отчёты |
| Downtime при релизе                   | Среднее | blue-green деплой в Traefik / Docker   |

---

## 📋 Контрольные точки

- [ ] Архитектура и ERD утверждены.
- [ ] Secrets перенесены в Vault.
- [ ] CI/CD pipeline прошёл 3 циклических деплоя.
- [ ] 90 % pytest покрытия.
- [ ] Stage = Prod по конфигурации.
- [ ] Подписан UAT-протокол.

---

## 👥 Роли и ответственность

| Роль                       | Ответственность                                |
| -------------------------- | ---------------------------------------------- |
| **Архитектор / Tech Lead** | Архитектура, структура репозитория, интеграции |
| **Backend Developer**      | ERPNext миграции, hooks, тесты                 |
| **DevOps Engineer**        | CI/CD, Terraform, Vault, Traefik               |
| **QA Lead**                | Автотесты, pytest-coverage, UAT                |
| **Integrations Engineer**  | Drive/Telegram API и метрики                   |
| **Tech Writer**            | Документация, runbooks                         |
| **Project Owner**          | Финальная приёмка и Go-Live                    |

---

## 🧩 Итог

После выполнения плана Ferum Customizations станет полностью готовым к эксплуатации:

- единая архитектура, безопасность и DevOps контур;
- мигрированные данные в ERPNext;
- стабильные интеграции;
- прозрачное наблюдение и отчётность.
