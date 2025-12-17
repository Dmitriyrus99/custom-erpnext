Файл: audit_inventory.md

ЭТАП 1. ПОЛНЫЙ АУДИТ РЕПОЗИТОРИЯ

Краткое резюме

- Тип проекта: Frappe/ERPNext (bench), c кастомными интеграциями (Telegram, Drive, Metrics), DevOps-артефактами и большим количеством служебной/временной документации.
- Состав: upstream-приложение ERPNext (apps/erpnext), корневые скрипты и конфигурации, вспомогательные утилиты (scripts/), конфиги инфраструктуры (config/), большое количество временных логов и lock-файлов в корне и config/.
- Риски: присутствуют секреты/учетные данные в репозитории (config/.env.integrations, redis _.acl), бинарные дампы/файлы состояния (config/pids/_.rdb), установочные логи и lock-файлы коммичены в VCS, дублирующиеся и конфликтующие документы (несколько audit/plan/architecture материалов), потенциальный конфликт npm/yarn конфигураций.
- Вывод: требуется очистка артефактов, консолидация документации, перенос секретов в менеджер секретов, выстраивание CI/CD и контроль миграций для приведения в production-ready.

1. Обнаруженные компоненты и артефакты

Примечание:

- Для каждого элемента: указан путь, назначение, статус, риск/конфликт.
- Файлам присвоены статусы: актуально / требует ревизии / устарело / дублируется.
- Элементы ERPNext (apps/erpnext/…) считаются upstream-вендорным кодом и оцениваются агрегировано (не в разрезе каждого файла).
- TODO: уточнить наличие кастомных приложений apps/ferum_custom и apps/telegram_bot (в списке файлов не отображены, но упоминаются в постановке).

А) Корень репозитория

- fix_mariadb_patches.yaml
  - Назначение: служебные фиксы последовательности/содержимого патчей MariaDB.
  - Статус: требует ревизии.
  - Риск: может конфликтовать с upstream-патчами ERPNext/Frappe; отсутствие автоматических тестов.
- frappe.sh
  - Назначение: локальный helper-скрипт для операций с bench/frappe.
  - Статус: требует ревизии.
  - Риск: неконтролируемые side-effects; нет интерактивной защиты от прод-окружения.
- pyproject.toml
  - Назначение: конфигурация Python-инструментов (lint, tooling, версии).
  - Статус: требует ревизии (согласовать со стандартом bench и pre-commit).
  - Риск: возможная рассинхронизация версий с bench/ERPNext.
- user_role_instructions_detailed.md
  - Назначение: расширенные инструкции по ролям пользователей.
  - Статус: дублируется (с user_role_instructions.md).
  - Риск: расхождение версий. Реком.: объединить в один файл.
- \_schema_reference.yaml
  - Назначение: справочник по схеме (DocType/поля/зависимости).
  - Статус: требует ревизии.
  - Риск: может противоречить текущей базе/моделям.
- schema_dependencies.md
  - Назначение: описание зависимостей схемы.
  - Статус: требует ревизии.
  - Риск: устаревание без автогенерации.
- updated_doctypes_json.zip
  - Назначение: экспорт DocType в zip.
  - Статус: устарело (бинарный артефакт).
  - Риск: хранение бинарей в git; неясное соответствие версии кода. Действие: MOVE → legacy.
- .pre-commit-config.yaml
  - Назначение: хук-линтеры/проверки.
  - Статус: актуально.
  - Риск: несогласованность с локальными скриптами в scripts/precommit.
- REBUILD_PLAN.md
  - Назначение: план перестройки/реинициализации.
  - Статус: требует ревизии/дублируется (есть SYSTEM_FIX_AUDIT.md, REBUILD_PROGRESS.md, cleanup_candidates.md).
  - Риск: расхождение с фактическим состоянием. Действие: MERGE → в единый delivery_plan.
- .prettierrc.json, .eslintrc.json
  - Назначение: форматирование/линт фронтенда.
  - Статус: требует ревизии.
  - Риск: возможный конфликт с yarn/bench Frappe toolchain (в ERPNext используется yarn + eslint). Выравнять версии.
- .gitignore
  - Назначение: исключения git.
  - Статус: требует ревизии (учесть .env, _.rdb, _.lock, logs, dumps).
  - Риск: текущие секреты/бинари уже в репозитории.
- install_frappe.log, install_erpnext.log, install_erpnext_force.log, install_erpnext_attempt.log
  - Назначение: установочные логи.
  - Статус: устарело.
  - Риск: могут содержать пути/среду; захламляют репо. Действие: MOVE → legacy.
- patches.txt (в корне)
  - Назначение: пользовательский список патчей migr.
  - Статус: требует ревизии (в ERPNext есть свой erpnext/patches.txt).
  - Риск: конфликт порядка миграций.
- schema_dependency_map.json
  - Назначение: карта зависимостей схемы.
  - Статус: требует ревизии.
  - Риск: устаревание; непонятно, как генерировалось.
- REBUILD_PROGRESS.md
  - Назначение: прогресс перестроек.
  - Статус: устарело/дублируется.
  - Риск: неоднозначность. Действие: MOVE → legacy или MERGE → delivery_plan.md как история (коротко).
- cleanup_candidates.md
  - Назначение: список кандидатов на очистку.
  - Статус: актуально как вход; после внедрения — LEGACY.
  - Риск: временный артефакт. Действие: MOVE → legacy после очистки.
- architecture_updated.drawio
  - Назначение: схема архитектуры.
  - Статус: требует ревизии (заменить на актуальную architecture_overview.md + current_diagram.drawio).
  - Риск: устаревание. Действие: REWRITE/MERGE.
- audit_report.md
  - Назначение: прежний аудит.
  - Статус: устарело/дублируется (будет новый комплект).
  - Действие: MOVE → legacy (или MERGE → новый audit_report.md сводный).
- improvement_plan.csv
  - Назначение: план улучшений.
  - Статус: требует ревизии.
  - Риск: источник для delivery_plan.md; затем MOVE → legacy.
- README.md
  - Назначение: корневой обзор.
  - Статус: требует ревизии/пересоздания под новую структуру docs/.
  - Риск: ссылки на устаревшие документы.
- package.json, package-lock.json
  - Назначение: фронтенд-зависимости на уровне корня.
  - Статус: требует ревизии.
  - Риск: конфликт с apps/erpnext/yarn.lock; рекомендуется унифицировать под yarn (стандарт Frappe/ERPNext) и удалить корневой npm, либо изолировать.
- data_model_rebuild.md
  - Назначение: заметки по перестройке модели данных.
  - Статус: требует ревизии.
  - Риск: устаревание. Действие: MERGE → architecture_overview.md (раздел “Data model”), затем MOVE → legacy.
- migration_script.sql
  - Назначение: ручные SQL-миграции.
  - Статус: требует ревизии.
  - Риск: опасно для prod; перенести в doctype patch/bench migrate pipeline с тестами.
- SYSTEM_FIX_AUDIT.md
  - Назначение: аудит фиксов.
  - Статус: дублируется/устарело.
  - Действие: MERGE → новый audit_report.md или delivery_plan.md раздел “Hotfix history”, затем MOVE → legacy.
- Procfile
  - Назначение: запуск процессов (gunicorn/redis/queue/…).
  - Статус: требует ревизии (согласовать с bench supervisor, docker/dokku).
  - Риск: рассинхрон с фактическим деплоем.
- user_role_instructions.md
  - Назначение: краткие инструкции ролей.
  - Статус: дублируется с detailed-версией.
  - Действие: MERGE → единый docs/roles_and_acl.md.
- workflow_bpmn.xml
  - Назначение: схема BPMN.
  - Статус: требует ревизии.
  - Риск: устаревание; хранить как актуальную диаграмму или перенести в legacy.

Б) Папка changes/

- changes/telegram_integration_audit.md
  - Назначение: аудит интеграции Telegram.
  - Статус: требует ревизии/консолидации.
  - Риск: дублирование с будущим architecture_overview.md и infrastructure_and_ci.md. Действие: MERGE → docs/integrations/telegram.md.
- changes/quick_fixes.md
  - Назначение: список быстрых фиксов.
  - Статус: устарело как временный артефакт.
  - Действие: MOVE → legacy после переноса в issue tracker/plan.

В) Папка scripts/

- scripts/run_audit.sh
  - Назначение: запуск внутренних проверок/аудита.
  - Статус: требует ревизии.
  - Риск: отсутствие idempotency, нет CI-интеграции.
- scripts/prompts/run_audit.py
  - Назначение: вспомогательный скрипт для аудита.
  - Статус: требует ревизии/документации.
- scripts/prompts/audit_and_cleanup.txt
  - Назначение: текстовые инструкции/промпт.
  - Статус: временный артефакт. Действие: MOVE → legacy (сохранить как legacy_notes.md выдержку).
- scripts/precommit/frappe_migrate_dry_run.py
  - Назначение: dry-run миграций в pre-commit.
  - Статус: актуально/требует интеграции в CI.
- scripts/precommit/check_forbidden_patterns.py
  - Назначение: проверка запрещённых паттернов (секреты и т.п.).
  - Статус: актуально/полезно. Развить правила.
- scripts/precommit/check_doctype_inits.py
  - Назначение: валидация **init**.py в DocType пакетах.
  - Статус: актуально.

Г) Папка config/

- config/nginx.conf
  - Назначение: конфиг Nginx.
  - Статус: требует ревизии (dev vs prod).
  - Риск: расхождение c текущим ingress/прокси.
- config/test_global.lock, config/site_config.lock, config/monitor_flush.lock, config/bench_build.lock
  - Назначение: lock-файлы.
  - Статус: устарело/REMOVE.
  - Риск: не должны храниться в репо. Действие: MOVE → legacy (затем добавить в .gitignore).
- config/redis_cache.conf, config/redis_queue.conf, config/redis_socketio.conf
  - Назначение: конфиги Redis.
  - Статус: требует ревизии (порты, security, persistence).
- config/redis_queue.acl, config/redis_cache.acl
  - Назначение: ACL Redis (секреты).
  - Статус: актуально как концепт, но СЕКРЕТЫ в git — недопустимо.
  - Риск: компрометация. Действие: REMOVE из git; хранить в Vault/SSM/Ansible vault, оставить только пример.
- config/.env.integrations
  - Назначение: переменные окружения интеграций (Google, Telegram, др.).
  - Статус: актуально как секреты, но не в VCS.
  - Риск: утечка. Действие: REMOVE из git; оставить config/.env.integrations.example и использовать secret manager.
- config/.env.integrations.example
  - Назначение: пример переменных окружения.
  - Статус: актуально.
- config/pids/temp-25696.rdb, config/pids/redis_queue.rdb
  - Назначение: дампы Redis/временные файлы.
  - Статус: устарело/недопустимо в репо.
  - Риск: случайная компрометация/раздувание репозитория. Действие: MOVE → legacy, добавить паттерны в .gitignore.
- config/scheduler_process
  - Назначение: вероятно, конфиг/скрипт планировщика.
  - Статус: требует ревизии (описать и интегрировать в supervisor/systemd/Celery bench worker).

Д) Приложения

- apps/erpnext/…
  - Назначение: upstream ERP-система ERPNext (ядро).
  - Статус: актуально (вендорный код).
  - Риск: конфликты при ручных правках. Любые изменения — через кастомные приложения/patches/hooks.
- TODO: apps/frappe/…
  - Назначение: движок Frappe (ожидается).
  - Статус: TODO: уточнить присутствие/версию.
- TODO: apps/ferum_custom/…
  - Назначение: кастомный модуль с DocType/hooks для домена.
  - Статус: TODO: уточнить наличие, миграции, фикстуры, тесты.
- TODO: apps/telegram_bot/…
  - Назначение: Telegram интеграция (webhook/polling, метрики).
  - Статус: TODO: уточнить структуру, секреты, деплой.

2. Интеграции и API (обнаруженные/упомянутые)

- Telegram
  - Источники: changes/telegram_integration_audit.md; предполагаемый apps/telegram_bot/.
  - Статус: требует ревизии; секреты в config/.env.integrations.
  - Риск: хранение токенов в git; нет Sentry/metrics указаний в коде (TODO: проверить).
- Google Drive/Sheets (Drive)
  - Источники: упоминание в задании; следы в .env.integrations.example.
  - Статус: TODO: уточнить наличие кода интеграций (api/clients/gdrive? server scripts?).
- Metrics (Prometheus)
  - Источники: упоминание api/metrics.py (в задании). В списке файлов не найден.
  - Статус: TODO: найти реальный путь и статус.
- FileSync
  - Источники: упоминание. Статус: TODO: найти реализацию.

3. Тесты, миграции, фикстуры

- Upstream ERPNext содержит обширные тесты (apps/erpnext/…/test\_\*.py, test_records.json).
  - Статус: актуально (как вендор).
- Кастомные тесты/миграции/фикстуры для нашего домена не обнаружены в видимом списке.
  - Статус: TODO: выявить в apps/ferum_custom и др.
- migration_script.sql (корень)
  - Статус: требует ревизии; перенести в управляемые патчи frappe (python patch + doctype patches) с тестами.

4. Скрипты (bootstrap, precommit, site_ops, automation)

- scripts/precommit/\* — актуально; интегрировать в CI.
- frappe.sh — требует ревизии/описания.
- scripts/run_audit.sh, scripts/prompts/\* — временные, перевести в CI/документацию.

5. DevOps-артефакты (Procfile, Docker/compose, CI/CD)

- Procfile — есть; нет Dockerfile/compose в видимом списке.
  - Статус: требует ревизии; определить целевую модель деплоя (Docker/k8s/bench supervisor).
- CI/CD конфигурации не обнаружены в корне (GitHub Actions, GitLab CI).
  - Статус: отсутствует; требуется разработать.
- config/\* — локальные конфиги сервисов; требуется нормализация для разных сред (dev/stage/prod) и IaC.

6. Документация: аудит и план очистки

Таблица артефактов документации и файлов, подлежащих очистке/консолидации

| Путь                                  | Назначение            | Статус               | Действие                              | Комментарий/Риск                              |
| ------------------------------------- | --------------------- | -------------------- | ------------------------------------- | --------------------------------------------- |
| README.md                             | Обзор проекта         | Требует ревизии      | REWRITE                               | Обновить под новую структуру docs/            |
| audit_report.md                       | Старый аудит          | Устарело/дублируется | MOVE → legacy или MERGE               | Слить ключевые выводы в новый audit_report.md |
| REBUILD_PLAN.md                       | План перестроек       | Дублируется          | MERGE → delivery_plan.md              | Затем MOVE → legacy                           |
| REBUILD_PROGRESS.md                   | Прогресс работ        | Устарело             | MOVE → legacy                         | Краткую историю перенести в delivery_plan.md  |
| SYSTEM_FIX_AUDIT.md                   | Аудит фиксов          | Дублируется/устарело | MERGE → audit_report.md               | Затем MOVE → legacy                           |
| data_model_rebuild.md                 | Перестройка модели    | Требует ревизии      | MERGE → architecture_overview.md      | Затем MOVE → legacy                           |
| architecture_updated.drawio           | Диаграмма архитектуры | Требует ревизии      | REWRITE                               | В docs/architecture/current_diagram.drawio    |
| workflow_bpmn.xml                     | BPMN диаграмма        | Требует ревизии      | REVIEW/MOVE                           | Оставить только актуальную версию в docs/     |
| schema_dependencies.md                | Зависимости схемы     | Требует ревизии      | REVIEW                                | Автогенерация/обновить и сослаться из docs    |
| \_schema_reference.yaml               | Справочник схемы      | Требует ревизии      | REVIEW                                | Синхронизировать с текущими DocType           |
| improvement_plan.csv                  | План работ            | Требует ревизии      | MERGE → delivery_plan.md              | Затем MOVE → legacy                           |
| user_role_instructions.md             | Роли (кратко)         | Дублируется          | MERGE → docs/roles_and_acl.md         | Удалить дубликаты                             |
| user_role_instructions_detailed.md    | Роли (подробно)       | Дублируется          | MERGE → docs/roles_and_acl.md         | Удалить дубликаты                             |
| changes/telegram_integration_audit.md | Аудит Telegram        | Требует ревизии      | MERGE → docs/integrations/telegram.md | Консолидировать                               |
| changes/quick_fixes.md                | Быстрые фиксы         | Устарело             | MOVE → legacy                         | Ключевое — в issue tracker/plan               |
| scripts/prompts/audit_and_cleanup.txt | Промпт/шпаргалка      | Устарело             | MOVE → legacy                         | Информацию — в legacy_notes.md                |
| install\_\*.log                       | Установочные логи     | Устарело             | MOVE → legacy                         | Не хранить логи в git                         |
| updated_doctypes_json.zip             | Экспорт DocTypes      | Устарело             | MOVE → legacy                         | Бинарники вне git; использовать миграции      |
| migration_script.sql                  | Ручные миграции       | Требует ревизии      | REWRITE                               | Перевести в патчи Frappe + тесты              |
| cleanup_candidates.md                 | Кандидаты на чистку   | Временный            | MOVE → legacy                         | После выполнения очистки                      |
| package.json / package-lock.json      | Фронтенд зависимости  | Требует ревизии      | REVIEW/MERGE                          | Принять единый менеджер (yarn)                |

Секреты и конфиденциальные данные (немедленные действия)

| Путь                                           | Тип            | Статус                       | Риск    | Рекомендация                                                         |
| ---------------------------------------------- | -------------- | ---------------------------- | ------- | -------------------------------------------------------------------- |
| config/.env.integrations                       | .env с ключами | Актуально, но хранится в git | Высокий | Удалить из git, оставить .example, перенести в Vault/SSM/K8s Secrets |
| config/redis_queue.acl, config/redis_cache.acl | ACL Redis      | Актуально, но хранится в git | Высокий | Исключить из git, хранить как секреты, зашифровать (Ansible vault)   |
| config/pids/\*.rdb                             | Дампы Redis    | Недопустимо                  | Средний | Убрать из git, добавить в .gitignore                                 |
| config/_/_.lock, \*.lock в корне               | Lock-файлы     | Устарело                     | Низкий  | Удалить/MOVE → legacy, добавить в .gitignore                         |

DevOps и окружение

- Procfile — требуется ревизия: сопоставить процессы (web, queue, scheduler, socketio) с bench или контейнерами. Если целимся в Docker/Kubernetes — заменить на docker-compose/k8s манифесты и supervisor конфиги.
- Отсутствует CI/CD — необходимо добавить GitHub Actions/другую CI: pre-commit, lint, pytest, bench migrate, build assets, deploy, notify.
- Конфиги Redis/Nginx — унифицировать по средам (dev/stage/prod), вынести параметры (порты, секреты) в переменные, описать IaC (Terraform + Ansible).

Приложения/Сервисы (логические границы — текущая оценка)

- Bench/Frappe Web (gunicorn) — управляет вебом и API.
- Background Workers (queue: default, short, long) — обработка задач.
- Scheduler — периодические задачи (cron).
- Хранилища: MariaDB/PostgreSQL (по умолчанию MariaDB для ERPNext), Redis (cache/queue/socketio).
- Интеграции: Telegram Bot (webhook), Google Drive/Sheets, Prometheus/Sentry (упомянуты, но не найдены исходники — TODO: обнаружить).

Источники бизнес-логики (ожидаемые места)

- hooks.py (в кастомных apps, TODO: найти).
- DocType и server scripts (в кастомных apps, TODO: найти).
- API endpoints (файлы под api/\*.py / whitelisted методы, TODO: найти).

Риски и конфликты (выборка)

- Секреты в репозитории (config/.env.integrations, \*.acl) — критический риск.
- Бинарные и runtime-файлы (redis \_.rdb, логи install\_\_.log, lock-файлы) — захламление и риск.
- Дублирующаяся документация (несколько audit/plan/architecture файлов) — источник противоречий.
- Несогласованность npm/yarn (root package.json vs apps/erpnext/yarn.lock) — потенциальные конфликты сборки фронтенда.
- Ручные SQL-миграции вне пайплайна Frappe — риск поломки/дрейфа схемы.

2. Таблица артефактов документации (консолидация)

См. раздел 6 таблицы — он является “таблицей артефактов документации”. Дополнительно:

- Создать:
  - docs/index.md — новый индекс.
  - docs/audit/current_audit.md — текущий аудит (консолидировать из audit_report.md, SYSTEM_FIX_AUDIT.md).
  - docs/architecture/architecture_overview.md — новая архитектура.
  - docs/architecture/current_diagram.drawio — актуальная диаграмма.
  - docs/delivery_plan.md — дорожная карта (слить REBUILD_PLAN.md, improvement_plan.csv, REBUILD_PROGRESS.md).
  - docs/infrastructure_and_ci.md — DevOps/CI/CD.
  - docs/roles_and_acl.md — объединить user_role_instructions\*.md.
  - docs/legacy_notes.md — выдержки из устаревших источников (важное, но неактуальное).

3. Список файлов, подлежащих удалению/перемещению (LEGACY/REMOVE)

LEGACY (переместить в ./legacy/ и исключить из активных ссылок):

- install_frappe.log
- install_erpnext.log
- install_erpnext_force.log
- install_erpnext_attempt.log
- updated_doctypes_json.zip
- REBUILD_PROGRESS.md
- audit_report.md (после переноса выводов в новый docs/audit/current_audit.md)
- REBUILD_PLAN.md (после слияния в docs/delivery_plan.md)
- SYSTEM_FIX_AUDIT.md (после слияния в docs/audit/current_audit.md)
- data_model_rebuild.md (после слияния в docs/architecture/architecture_overview.md)
- cleanup_candidates.md (после завершения работ)
- changes/quick_fixes.md
- scripts/prompts/audit_and_cleanup.txt
- architecture_updated.drawio (после создания актуальной диаграммы)
- workflow_bpmn.xml (если будет заменен новой актуальной схемой)

REMOVE из репозитория (и добавить в .gitignore; живут в Secret Manager/вне VCS):

- config/.env.integrations (оставить config/.env.integrations.example)
- config/redis_queue.acl
- config/redis_cache.acl
- config/pids/temp-25696.rdb
- config/pids/redis_queue.rdb
- config/test_global.lock
- config/site_config.lock
- config/monitor_flush.lock
- config/bench_build.lock

Дублирующиеся документы (MERGE → единые файлы):

- user_role_instructions.md + user_role_instructions_detailed.md → docs/roles_and_acl.md
- REBUILD_PLAN.md + REBUILD_PROGRESS.md + improvement_plan.csv → docs/delivery_plan.md
- audit_report.md + SYSTEM_FIX_AUDIT.md → docs/audit/current_audit.md
- data_model_rebuild.md + schema_dependencies.md + \_schema_reference.yaml (релевантные разделы) → docs/architecture/architecture_overview.md

4. TODO: уточнить/найти

- Наличие и структура кастомных приложений:
  - apps/ferum_custom
  - apps/telegram_bot
  - apps/frappe (если не vendored отдельно)
- Реальные пути интеграций и метрик:
  - api/metrics.py (упомянут), endpoints Telegram webhook, клиенты Google API.
- Наличие Dockerfile/docker-compose или k8s-манифестов (в списке не обнаружены).
- Наличие unit/integration тестов в кастомных apps (в ERPNext есть, в кастомных не видно).

5. Рекомендации по немедленным шагам очистки (оперативно)

- Перенести указанные LEGACY файлы в ./legacy/.
- Удалить/исключить из git файлы с секретами и runtime:
  - config/.env.integrations → заменить на .env.integrations.example.
  - config/redis\__.acl, config/pids/_.rdb, \* .lock → убрать и добавить в .gitignore.
- Обновить .gitignore:
  - .env, _.acl, _.rdb, _.log, _.lock, /legacy/, /sites/\*/private/backups/, node_modules, dist, assets, .bench, .DS_Store и т.п.
- Подготовить новые каркасные документы в docs/ (пустые разделы с TODO) для последующего заполнения:
  - docs/index.md
  - docs/audit/current_audit.md
  - docs/architecture/architecture_overview.md
  - docs/architecture/current_diagram.drawio (заглушка)
  - docs/delivery_plan.md
  - docs/infrastructure_and_ci.md
  - docs/roles_and_acl.md
  - docs/legacy_notes.md
- Переписать README.md с ссылками только на новые docs/\*.

Примечание об исполнении действий

- В рамках этого этапа сформирован список LEGACY/REMOVE. Следующий шаг: переместить/удалить перечисленные файлы согласно списку и обновить README.md и docs/index.md. Если требуется — выполню перенос и подготовлю новые каркасные документы в следующем сообщении.

Конец файла audit_inventory.md

Дальнейшие действия, которые я выполню по вашему подтверждению

- Перемещение всех помеченных LEGACY/REMOVE файлов в ./legacy/ и обновление .gitignore.
- Создание каркасов новых документов в папке docs/ и обновление README.md и docs/index.md так, чтобы они ссылались только на актуальные документы.
- Переход к ЭТАПУ 2 (консолидированная архитектурная карта) с подготовкой architecture_overview.md.
