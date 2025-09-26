# Модель данных (DocTypes)

- Проекты обслуживания: Service Project — связь с Клиентом, Объектами, Заявками и Счетами.
- Заявки: Service Request — SLA, статусы, назначение инженера, связь с отчетом.
- Отчеты: Service Report — работы, документы, PDF, выгрузка в Drive.
- Счета: Invoice — статусы, синхронизация с Google Sheets, опциональное создание ERPNext Sales Invoice.

Файлы и связи:
- ER: ../entity_relationship_model.md
- Service Project: ferum_custom/ferum_custom/ferum_custom/doctype/service_project/
- Service Request: ferum_custom/ferum_custom/ferum_custom/doctype/service_request/
- Service Report: ferum_custom/ferum_custom/ferum_custom/doctype/service_report/
- Invoice: ferum_custom/ferum_custom/ferum_custom/doctype/invoice/
