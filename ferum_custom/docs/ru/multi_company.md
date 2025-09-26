# Многофирменность и изоляция данных

- Все ключевые документы содержат ссылку на Компанию, Клиента и/или Проект.
- Доступ ограничивается через Permission Query Conditions (PQC) и has_permission.
- Роли видят только свои данные: Project Manager — по проектам, Service Engineer — по назначенным заявкам, Client — свои заявки (портал/бот).

Реализация PQC/прав:
- Service Request: ferum_custom/ferum_custom/ferum_custom/doctype/service_request/service_request.py
- Service Report: ferum_custom/ferum_custom/ferum_custom/doctype/service_report/service_report.py
- Invoice: ferum_custom/ferum_custom/ferum_custom/doctype/invoice/invoice.py

Матрица ролей: ../user_roles_permissions_matrix.md
