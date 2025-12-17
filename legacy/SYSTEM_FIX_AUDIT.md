1. Введение

Цель аудита — выявить и устранить технические сбои в кастомизациях Ferum (ERPNext/Frappe), влияющие на:
- Регламентное обслуживание (Service Maintenance Schedule) — ошибки открытия/сохранения, автогенерация заявок.
- Клиентские заявки (Service Request) — подача через портал, корректность прав и ограничений доступа.

Работы проводились в бенче `erpclone.ferumrus.ru` с проверкой файлов приложений и журналов.

2. Обнаруженные ошибки

- «DocType not found» при открытии «Графики обслуживания» (Service Maintenance Schedule) в Desk.
- Портальная страница «/portal/new-request» отображала пустую страницу из-за тега `<template>`; отправка формы не работала стабильно.
- У ряда ролей доступ к админ‑инструментам («Permission Manager», отчёты по доступу) был шире необходимого.
- Клиентские учётные записи могли иметь Desk‑тип (Desk User), что нарушало принцип минимально необходимого доступа.
- Планировщик (Scheduler) был отключён для `erpclone.ferumrus.ru`, из‑за чего не работала автогенерация заявок по графикам.
- В разделе «Users» некорректный перевод «Document Share Report» (отображался как «Документ Поделиться Пожаловаться»).

3. Причины

- В контроллере `Service Maintenance Schedule` отсутствовал класс Document — Frappe не мог импортировать контроллер.
- Портальные HTML были обёрнуты в `<template>`, из‑за чего браузер не отрисовывал разметку; отсутствовал явный `type: "POST"` в `frappe.call` и слабая обработка ошибок.
- Role Permission for Page and Report не ограничивали доступ к админ‑страницам/отчётам только System Manager.
- У клиентов (роль Client) не был принудительно установлен тип пользователя Website User.
- Планировщик отключён — ежедневные задачи (в т.ч. генерация заявок из графиков) не запускались.
- Ошибка перевода в ru.csv базовой локали Frappe.

4. Решения

- Service Maintenance Schedule:
  - Добавлен класс контроллера Document: `service_maintenance_schedule.py`.
  - Проверено наличие DocType и записей на сайте; создан тестовый график `SMSCH-0001`.
  - Включён планировщик (scheduler) для сайта.
- Портал заявок:
  - Исправлены страницы `/portal/new-request`, `/portal` — убран тег `<template>`, добавлен `type: "POST"`, улучшена обработка ошибок и редирект гостя на логин.
  - В API `create_service_request` добавлена подстановка компании по умолчанию.
- Ужесточение прав:
  - Добавлены `get_permission_query_conditions` и `has_permission` для `Service Request` (постраничные фильтры и доступ к документам на основе ролей и User Permissions).
  - Инструмент `site_ops.harden_permissions`: ограничение Page/Reports только для System Manager и приведение Client → Website User.
- Переводы:
  - Добавлен корректный перевод «Document Share Report» → «Отчёт по доступу к документам».

Изменённые файлы (ключевые):
- ferum_custom/ferum_custom/doctype/service_maintenance_schedule/service_maintenance_schedule.py
- ferum_custom/ferum_custom/www/portal/{index.html,new-request.html,service-request.html}
- ferum_custom/ferum_custom/api/service.py (default company)
- ferum_custom/ferum_custom/doctype/service_request/service_request.py (PQC/has_permission)
- ferum_custom/ferum_custom/site_ops.py (harden_permissions, create_test_schedule)
- ferum_custom/ferum_custom/translations/ru.csv

5. План внедрения

- Данные/права:
  - Настроить User Permissions:
    - Сотрудникам — Company (и при необходимости Project/Service Department).
    - Клиентам — Customer.
  - Ограничить доступ к админ‑страницам/отчётам только System Manager (выполнено автоматически хелпером).
- Автоматизация:
  - Убедиться, что планировщик включён (выполнено) и ежедневная задача генерации заявок активна.
  - Проверить рабочие столы (Workspaces) — «Регламентное обслуживание», «Сервисные операции».

6. Проверка и тесты (чек‑лист)

- Desk:
  - Открывается список «Service Maintenance Schedule». Видна запись `SMSCH-0001`.
  - Под PM — видны только заявки его проектов. Под инженером — только назначенные/созданные им заявки. Под клиентом — Desk недоступен.
- Портал:
  - /portal показывает список заявок пользователя.
  - /portal/new-request создаёт заявку и выводит ссылку на карточку.
- Планировщик:
  - Через день (или принудительно) проверить создание Issues по расписанию.
- Безопасность:
  - Страницы Permission Manager и отчёты «Document Share Report», «Permitted Documents For User» — доступны только System Manager.

7. Итог

Система приведена к принципам «минимально необходимого доступа» и стабилизирована:
- Исправлены ошибки открытия и сохранения сущностей регламентного обслуживания и портала.
- Усилен контроль доступа к заявкам с учётом ролей и пользовательских ограничений.
- Восстановлена корректная работа планировщика.

Дополнительно готов настроить пакетную раскладку User Permissions по вашему списку и при необходимости включить дополнительные полевые ограничения (permlevel) на чувствительные поля.
